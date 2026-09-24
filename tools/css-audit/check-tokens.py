#!/usr/bin/env python3
"""Guard against re-introducing copies of Obsidian's own app.css defaults.

Rule enforced (see AGENTS.md "Don't mirror app.css"):
`src/global/design/setting.css` and `src/global/design/color.css` may only define a
custom property when its value DIFFERS from the app.css default at the same selector
context.  Byte-identical copies are dead weight: they freeze an old app version and
add ~430 lines of noise to theme.css.

Usage:
    python3 check-tokens.py                       # report only
    python3 check-tokens.py --strict              # exit 1 on any mirror
    python3 check-tokens.py --app-css /tmp/app.css

Exit codes: 0 = clean (or report-only), 1 = mirrors found under --strict, 2 = app.css missing.
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


def collect(css: str) -> dict[str, dict[str, list[str]]]:
    """{var: {normalized_selector: [values]}} — last value wins, all kept for reporting."""
    out: dict[str, dict[str, list[str]]] = collections.defaultdict(dict)
    for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        sel = re.sub(r"/\*.*?\*/", "", block.group(1), flags=re.S)
        sel = re.sub(r"\s+", " ", sel).strip()
        for decl in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", block.group(2)):
            out[decl.group(1)].setdefault(sel, []).append(re.sub(r"\s+", " ", decl.group(2)).strip())
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Flag custom properties in src/global/design/ that just re-declare an app.css default.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--app-css", default="/tmp/app.css", help="extracted Obsidian app.css")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any mirror is found")
    ap.add_argument("--json", dest="json_out", help="also write the findings as JSON")
    args = ap.parse_args(argv)

    app_path = Path(args.app_css)
    if not app_path.exists():
        print(f"app.css not found: {app_path}\n  run: python3 tools/css-audit/extract-app-css.py", file=sys.stderr)
        return 2

    app = collect(app_path.read_text(encoding="utf-8", errors="ignore"))
    findings, kept = [], []
    for rel, fixed_sel in TARGETS.items():
        f = REPO / rel
        if not f.exists():
            print(f"skip (missing): {rel}", file=sys.stderr)
            continue
        for var, selmap in collect(f.read_text(encoding="utf-8")).items():
            for sel, values in selmap.items():
                target = fixed_sel or sel
                app_values = app.get(var, {}).get(target)
                rec = {"file": rel, "selector": sel, "var": var, "value": values[-1], "app_selector": target}
                if app_values and values[-1] in app_values:
                    findings.append(rec)
                else:
                    kept.append(rec)

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
