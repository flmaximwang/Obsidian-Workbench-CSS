#!/usr/bin/env python3
"""DOM-level regression probe against the **test vault** instance of Obsidian.

Reads computed styles in the running app for two things that have silently changed before and
cannot be caught by reading CSS:

  * `--code-normal` resolution — when the theme's override was lost, printed inline-code colour
    fell back to the body text colour (`#5a5a5a` -> `#222222` in one release).
  * print geometry constants — `--print-page-width` must still be the 714px A4 content width
    (the value the PDF ruler measurement independently confirms).

It also **places the fixture as the active document** and proves it, before any caller exports it:
`getLeaf(false).openFile()` can land on a leaf that never renders the file, and a measurement
taken from the wrong document is worse than no measurement.

Prints `{"info": {...}, "checks": [{"name","ok","detail"}]}` and exits 1 if any check failed.
Needs Obsidian on `--remote-debugging-port` with the test vault open
(`tests/VaultTest/run-test-vault.sh`); never touches a real vault.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import websocket as _ws

_orig_create_connection = _ws.create_connection


def _create_connection(url, *a, **kw):  # Electron rejects a WebSocket carrying an Origin header
    kw.setdefault("suppress_origin", True)
    return _orig_create_connection(url, *a, **kw)


_ws.create_connection = _create_connection

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "print-harness"))

from cdp import CDP, list_targets  # noqa: E402

JS = r"""
(async () => {
  const FILE = FILE_JSON;
  const out = {info: {}, checks: [], values: {}};
  const add = (name, ok, detail) => out.checks.push({name, ok: !!ok, detail});

  out.info.vault = app.vault.getName();
  // `app.appVersion` is the instance's own version; the window title carries it too.
  out.info.appVersion = app.appVersion || ((document.title.match(/Obsidian v([\d.]+)/) || [])[1] || null);
  out.info.theme = (app.customCss && app.customCss.theme) || null;

  const file = app.vault.getAbstractFileByPath(FILE);
  if (!file) { add('fixture present', false, FILE + ' not found in the vault'); return JSON.stringify(out); }

  // Close the fixture tabs a previous run left behind: they accumulate (one per probe) and a
  // crowded workspace defers rendering of background leaves, which then look like a failed check.
  const stale = [];
  app.workspace.iterateAllLeaves(l => {
    if (l.view && l.view.file && /^fixtures\//.test(l.view.file.path)) stale.push(l);
  });
  stale.forEach(l => l.detach());
  if (stale.length) await new Promise(r => setTimeout(r, 500));

  const leaf = app.workspace.getLeaf('tab');
  await leaf.openFile(file);
  let active = null;
  for (let i = 0; i < 25; i++) {
    active = app.workspace.getActiveFile();
    if (active && active.path === FILE) break;
    await new Promise(r => setTimeout(r, 400));
  }
  out.info.activeFile = active ? active.path : null;
  add('the fixture is the active document', !!active && active.path === FILE,
      `active file = ${JSON.stringify(out.info.activeFile)}, expected ${JSON.stringify(FILE)}`);

  // Same leaf we opened in — reading the state off a different leaf silently misses the note.
  for (let i = 0; i < 5; i++) {
    const st = leaf.getViewState();
    if (st.state && st.state.mode === 'preview') break;
    st.state = Object.assign({}, st.state, {mode: 'preview'});
    await leaf.setViewState(st);
    await new Promise(r => setTimeout(r, 800));
  }
  await new Promise(r => setTimeout(r, 600));
  // Identity mode stops here: the export's text-layer sentinel check is the authoritative proof of
  // which document was printed, and rendering checks stay noisy while tabs are being recycled.
  if (IDENTITY_ONLY) return JSON.stringify(out);

  const mode = leaf.view && leaf.view.getMode ? leaf.view.getMode() : 'unknown';
  // Read the ACTIVE LEAF's own container: several tabs hold a `.markdown-reading-view`,
  // and document.querySelector picks the first — often a different pane than the fixture's.
  const container = (leaf.view && leaf.view.containerEl) || document.querySelector('.markdown-reading-view');
  const code = container ? container.querySelector('code') : null;
  const readingViews = document.querySelectorAll('.markdown-reading-view').length;
  out.info.mode = mode;
  out.info.readingViews = readingViews;
  add('the fixture renders in reading view (in its own leaf)', !!code,
      `leaf mode = ${mode}, ${readingViews} .markdown-reading-view(s) on screen, inline <code> in this leaf ${code ? 'found' : 'missing'}`);

  const bodyStyle = getComputedStyle(document.body);
  const codeColor = code ? getComputedStyle(code).color : null;
  const bodyColor = bodyStyle.color;
  out.values['--code-normal'] = bodyStyle.getPropertyValue('--code-normal').trim();
  out.values.inlineCodeColor = codeColor;
  out.values.bodyColor = bodyColor;

  add('theme is the linked Workbench build',
      out.info.theme === 'Workbench',
      `app.customCss.theme = ${JSON.stringify(out.info.theme)}`);
  add('inline code has its own colour',
      !!code && codeColor && codeColor !== bodyColor,
      `inline code ${codeColor} vs body ${bodyColor} (the theme's --code-normal override must not collapse into --text-normal)`);

  const pageWidth = bodyStyle.getPropertyValue('--print-page-width').trim();
  const a4 = bodyStyle.getPropertyValue('--a4-page-print-width-original').trim();
  out.values['--print-page-width'] = pageWidth;
  out.values['--a4-page-print-width-original'] = a4;
  add('A4 content width constant is 714px', a4 === '714px',
      `--a4-page-print-width-original = ${JSON.stringify(a4)}`);
  // getPropertyValue substitutes the var() chain but does not evaluate the calc(),
  // so accept either form: the token name or the resolved 714px.
  add('--print-page-width is driven by the A4 constant',
      /--a4-page-print-width-zoomed|714px/.test(pageWidth),
      `--print-page-width = ${JSON.stringify(pageWidth)}`);
  return JSON.stringify(out);
})()
"""


def pick_target(port: int, vault_prefix: str):
    for cand in list_targets(port):
        if cand.get("type") != "page" or "index.html" not in (cand.get("url") or ""):
            continue
        try:
            c = CDP(cand["webSocketDebuggerUrl"])
            try:
                name = c.eval("app.vault.getName()")
            finally:
                c.close()
        except Exception:
            continue
        if name and name.startswith(vault_prefix):
            return cand
    return None


def main() -> None:
    ap = argparse.ArgumentParser(
        description="测试库实例里读计算样式并置顶 fixture（--code-normal、打印几何常量、文档身份）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--port", type=int, default=9222, help="Obsidian 远程调试端口")
    ap.add_argument("--vault-prefix", default="VaultTest", help="用于挑选目标窗口的 vault 名前缀")
    ap.add_argument("--open", default="fixtures/print-a4.md", help="置顶并校验的 vault 内相对路径")
    ap.add_argument("--checks", choices=["all", "identity"], default="all",
                    help="all = 文档身份 + 计算样式检查；identity = 只置顶并校验文档身份（导出前用）")
    args = ap.parse_args()

    target = pick_target(args.port, args.vault_prefix)
    if target is None:
        sys.exit(f"没有找到 vault 前缀为 {args.vault_prefix!r} 的 Obsidian 窗口（先跑 tests/VaultTest/run-test-vault.sh）")

    c = CDP(target["webSocketDebuggerUrl"])
    try:
        r = c.call("Runtime.evaluate",
                   expression=JS.replace("FILE_JSON", json.dumps(args.open))
                               .replace("IDENTITY_ONLY", "true" if args.checks == "identity" else "false"),
                   returnByValue=True, awaitPromise=True, timeout=120000)
        if r.get("exceptionDetails"):
            sys.exit(f"JS 异常：{json.dumps(r['exceptionDetails'], ensure_ascii=False)[:800]}")
        out = json.loads(r["result"]["value"])
    finally:
        c.close()

    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(1 if [c["name"] for c in out["checks"] if not c["ok"]] else 0)


if __name__ == "__main__":
    main()
