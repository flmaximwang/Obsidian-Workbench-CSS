#!/usr/bin/env python3
"""A/B the theme's broken `--file-line-width` in the running app.

`src/desktop/note/page/main.css` declares
    --file-line-width: calc(var(--font-text-size) * var(--words-per-line));
with `--words-per-line` defined nowhere, so the value is guaranteed-invalid and the
theme silently overrides the app's own `body { --file-line-width: 700px }` — which
app.css consumes in 8 `max-width: var(--file-line-width)` rules.

This script measures whether restoring the app's 700px changes any rendered width.
  * no measured change  -> the theme's two lines are inert; deleting them is neutral
  * a change            -> the neutralisation is load-bearing; keep it, but write it
                           explicitly (`--file-line-width: initial`)

Usage: python3 ab-file-line-width.py [--port 9222]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cdp as harness  # noqa: E402

METRICS = r"""
(() => {
  const leaf = app.workspace.activeLeaf;
  const el = leaf && leaf.view && leaf.view.containerEl;
  if (!el) return {error: "no active leaf"};
  const box = s => {
    const n = el.querySelector(s);
    if (!n) return null;
    const cs = getComputedStyle(n);
    return {width: cs.width, maxWidth: cs.maxWidth, padding: cs.paddingLeft + " " + cs.paddingRight};
  };
  const csb = getComputedStyle(document.body);
  return {
    mode: leaf.view.getMode ? leaf.view.getMode() : null,
    readable: !!el.querySelector(".is-readable-line-width"),
    fileLineWidth: csb.getPropertyValue("--file-line-width").trim(),
    themeWidth: csb.getPropertyValue("--width-is-readable-line-width").trim(),
    sizer: box(".cm-sizer") || box(".markdown-preview-sizer"),
    content: box(".cm-content"),
    line: box(".cm-line"),
    previewSizer: box(".markdown-preview-sizer"),
    viewContent: box(".view-content"),
  };
})()
"""

INJECT = """(() => {
  let s = document.getElementById("hermes-ab");
  if (!s) { s = document.createElement("style"); s.id = "hermes-ab"; document.head.appendChild(s); }
  s.textContent = "body { --file-line-width: 700px !important; }";
  return s.textContent;
})()"""

UNINJECT = """(() => { const s = document.getElementById("hermes-ab"); if (s) s.remove(); return !!s; })()"""

MARKER = """(() => {
  const sheets = [...document.styleSheets];
  const hit = sheets.find(s => { try { return [...s.cssRules].some(r => r.cssText.includes("--document-background: transparent")); } catch (e) { return false; } });
  const cmSearch = sheets.find(s => { try { return [...s.cssRules].some(r => r.cssText.includes(".cm-searching")); } catch (e) { return false; } });
  return {newBuildLive: !!hit, cmSearchingRuleLive: !!cmSearch, sheets: sheets.length};
})()"""


def _ab(c) -> None:
    before = c.eval(METRICS)
    c.eval(INJECT)
    time.sleep(0.3)
    after = c.eval(METRICS)
    c.eval(UNINJECT)
    print(f"mode={before.get('mode')} readable={before.get('readable')} "
          f"--file-line-width={before.get('fileLineWidth')!r} -> {after.get('fileLineWidth')!r}")
    for k in ["sizer", "content", "line", "previewSizer", "viewContent"]:
        b, a = before.get(k), after.get(k)
        flag = "   " if b == a else "  <<< CHANGED"
        print(f"  {k:14s} before={b}  after={a}{flag}")


def main() -> int:
    ap = argparse.ArgumentParser(description="A/B the theme broken --file-line-width against the app default")
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--mode", choices=["current", "source", "preview", "both"], default="both",
                    help="view mode to measure (default: both)")
    args = ap.parse_args()

    SET_MODE = """(mode => {
      const leaf = app.workspace.activeLeaf;
      const st = leaf.getViewState();
      st.state = Object.assign({}, st.state, {mode});
      return leaf.setViewState(st, {focus: false}).then(() => mode);
    })(%s)"""

    targets = harness.pick_targets(harness.list_targets(args.port), "app")
    c = harness.CDP(targets[0]["webSocketDebuggerUrl"])
    try:
        try:
            c.eval("app.customCss.loadThemes().then(() => 'ok')", await_promise=True)
        except Exception as e:  # noqa: BLE001
            print(f"(loadThemes failed: {e})", file=sys.stderr)
        time.sleep(0.6)
        print("markers:", json.dumps(c.eval(MARKER)))

        modes = (["source", "preview"] if args.mode == "both"
                 else ([args.mode] if args.mode != "current" else [None]))
        for mode in modes:
            if mode:
                c.eval(SET_MODE % json.dumps(mode), await_promise=True)
                time.sleep(0.5)
            print(f"\n================ mode = {mode or 'as-is'} ================")
            _ab(c)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
