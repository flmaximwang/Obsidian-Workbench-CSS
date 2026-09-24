#!/usr/bin/env python3
"""Read live state from the running Obsidian (debug port) — Wave 2 checks.

Reports, from the real app:
  1. vault + active file
  2. the theme's own tokens as the browser computes them (--file-line-width etc.)
  3. which CodeMirror generation the DOM actually contains (.cm-editor vs .CodeMirror)
  4. whether the freshly built theme.css is the one loaded (marker text + length)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cdp as harness  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))

JS = r"""
(() => {
  const cs = getComputedStyle(document.body);
  const varOf = n => cs.getPropertyValue(n).trim();
  const q = s => document.querySelectorAll(s).length;
  // find the theme stylesheet: the one that carries our print tokens
  let themeLen = null, themeIdx = -1;
  const sheets = [...document.styleSheets];
  sheets.forEach((s, i) => {
    let txt = "";
    try { txt = [...s.cssRules].map(r => r.cssText).join("\n"); } catch (e) { return; }
    if (txt.includes("--a4-page-print-width-original")) { themeLen = txt.length; themeIdx = i; }
  });
  return {
    vaultBase: (() => { try { return app.vault.adapter.basePath || app.vault.adapter.getBasePath?.() || null; } catch (e) { return null; } })(),
    activeFile: (() => { try { return app.workspace.getActiveFile()?.path ?? null; } catch (e) { return null; } })(),
    viewMode: (() => { try { return app.workspace.activeLeaf?.view?.getMode?.() ?? null; } catch (e) { return null; } })(),
    fileLineWidth: varOf("--file-line-width"),
    wordsPerLine: varOf("--words-per-line"),
    documentWidth: varOf("--document-width"),
    documentBackground: varOf("--document-background"),
    printPageWidth: varOf("--print-page-width"),
    pSpacing: varOf("--p-spacing"),
    counts: {
      cmEditor: q(".cm-editor"),
      cmSObsidian: q(".cm-s-obsidian"),
      cmTab: q(".cm-tab"),
      cmSearching: q(".cm-searching"),
      codeMirror: q(".CodeMirror"),
      codeMirrorAny: q('[class*="CodeMirror"]'),
      miscCalloutSwitches: q('[data-callout-metadata*="banner"]'),
    },
    themeSheetIndex: themeIdx,
    themeSheetChars: themeLen,
    sheetCount: sheets.length,
  };
})()
"""


def main() -> int:
    port = int(os.environ.get("PORT", "9222"))
    targets = harness.pick_targets(harness.list_targets(port), "app")
    if not targets:
        print("no app target", file=sys.stderr)
        return 1
    c = harness.CDP(targets[0]["webSocketDebuggerUrl"])
    try:
        info = c.eval(JS)
    finally:
        c.close()

    local = os.path.join(REPO, "theme.css")
    local_chars = len(open(local, encoding="utf-8").read()) if os.path.exists(local) else -1

    print(json.dumps(info, indent=1, ensure_ascii=False))
    print(f"\ntheme.css on disk: {local_chars} chars")
    if info.get("themeSheetChars"):
        print(f"loaded theme sheet: {info['themeSheetChars']} chars  "
              f"{'(matches disk -> new build is live)' if info['themeSheetChars'] == local_chars else '(DIFFERS from disk!)'}")
    print("\n-- 判读 --")
    print(f"  阅读行宽: --file-line-width = {info['fileLineWidth']!r}"
          f"   --words-per-line = {info['wordsPerLine']!r}")
    print(f"  DOM 里的 CodeMirror 代次: .cm-editor={info['counts']['cmEditor']}  "
          f".cm-s-obsidian={info['counts']['cmSObsidian']}  .CodeMirror={info['counts']['codeMirror']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
