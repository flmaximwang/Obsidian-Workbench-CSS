#!/usr/bin/env python3
"""Guard against re-introducing copies of Obsidian's own app.css defaults.

Rule enforced (see AGENTS.md "Don't mirror app.css"):
`src/global/design/setting.css` and `color.css` may only define a custom property whose
value DIFFERS from the app.css default at the same selector context.  Byte-identical
copies are dead weight: they freeze an old app version and bloat theme.css.

Two traps are encoded here, each of which cost a real rendering regression:

1. **Context matters.**  A theme `body { --x: v }` is only a copy when the app defines
   `--x: v` at `body` too.  A definition inside an at-rule is not "the default at that
   context": `app.css` sets `--code-normal` under
   `@media screen and (forced-colors: active)`, so treating that as the body default
   made a genuine override look like a deletable copy.
2. **Use the stylesheet the app serves, not the asar copy.**  `obsidian.asar`'s
   `app.css` is truncated and stale (426 KB vs 655 KB live), and holds different values.
   Fetch the real one:
       python3 tools/css-audit/fetch-app-css.py      # -> /tmp/app-live.css

Usage:
    python3 tools/css-audit/check-tokens.py                       # report only
    python3 tools/css-audit/check-tokens.py --strict              # exit 1 on any mirror
    python3 tools/css-audit/check-tokens.py --app-css /tmp/app-live.css

Exit codes: 0 = clean (or report-only), 1 = mirrors found under --strict, 2 = file missing.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGETS = {
    "src/global/design/setting.css": "body",
    "src/global/design/color.css": None,  # compare per-selector (.theme-light/.theme-dark)
}
DECL_RE = re.compile(r"^\s*(--[\w-]+)\s*:\s*(.+?)\s*$", re.S)


def collect(css: str) -> dict[str, dict[str, str]]:
    """{var: {context: value}} with context = "[at-rule >> ]selector".

    A brace-stack walker over comment-stripped text.  The earlier regex version ignored
    at-rule nesting entirely, which is exactly how the `--code-normal` regression
    slipped through: the app's declaration sits inside a `@media`, the theme's sat at
    `body`, and the two were compared as if they were the same context.
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out: dict[str, dict[str, str]] = collections.defaultdict(dict)
    stack: list[str] = []
    buf: list[str] = []
    for ch in css:
        if ch == "{":
            stack.append(re.sub(r"\s+", " ", "".join(buf)).strip())
            buf = []
        elif ch == "}":
            buf = []
            if stack:
                stack.pop()
        elif ch == ";":
            decl = "".join(buf)
            buf = []
            m = DECL_RE.match(decl)
            if m and stack and not stack[-1].startswith("@"):
                ats = [s for s in stack[:-1] if s.startswith("@")]
                key = (" ".join(ats) + " >> " if ats else "") + stack[-1]
                out[m.group(1)][key] = re.sub(r"\s+", " ", m.group(2)).strip()
        else:
            buf.append(ch)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Flag custom properties in src/global/design/ that re-declare an app.css default.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--app-css", default="/tmp/app-live.css",
                    help="app.css fetched from the RUNNING app (see fetch-app-css.py)")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any mirror is found")
    ap.add_argument("--json", dest="json_out", help="also write the findings as JSON")
    args = ap.parse_args(argv)

    app_path = Path(args.app_css)
    if not app_path.exists():
        print(f"app.css not found: {app_path}\n"
              "  run: python3 tools/css-audit/fetch-app-css.py\n"
              "  (needs Obsidian started with --remote-debugging-port; the obsidian.asar\n"
              "   copy is truncated and stale — do not audit against it)",
              file=sys.stderr)
        return 2

    app = collect(app_path.read_text(encoding="utf-8", errors="ignore"))
    findings, kept = [], []
    for rel, fixed_sel in TARGETS.items():
        f = REPO / rel
        if not f.exists():
            print(f"skip (missing): {rel}", file=sys.stderr)
            continue
        for var, ctxmap in collect(f.read_text(encoding="utf-8")).items():
            for ctx, value in ctxmap.items():
                target = fixed_sel or ctx
                app_value = app.get(var, {}).get(target)
                rec = {"file": rel, "selector": ctx, "var": var, "value": value, "app_selector": target}
                (findings if app_value is not None and app_value == value else kept).append(rec)

    for rec in findings:
        print(f"MIRROR  {rec['file']}  {rec['var']}: {rec['value'][:60]}  == app.css[{rec['app_selector']}]")
    print(f"\nmirrors of app.css defaults: {len(findings)}   real overrides / theme-only: {len(kept)}")
    for rec in kept:
        print(f"  keep  {rec['var']}: {rec['value'][:60]}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps({"mirrors": findings, "kept": kept}, indent=1))

    if findings and args.strict:
        print("\nFAIL: theme must not mirror app.css defaults.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
