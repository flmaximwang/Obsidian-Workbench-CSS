#!/usr/bin/env python3
"""Fetch the AUTHORITATIVE app.css from the running Obsidian (needs the debug port).

Why this exists: `obsidian.asar` ships a **truncated / stale** `app.css` (426 KB there
vs 655 KB served at runtime).  Auditing token mirrors against the asar copy produced a
wrong keep/delete decision — it reported `body { --code-normal: var(--text-muted) }`
while the running app actually has `--code-normal: var(--text-normal)`, so the theme's
real override was deleted and inline-code colour changed in print output.  Always audit
against the file the app itself serves.

Usage:
    python3 tools/css-audit/fetch-app-css.py                    # -> /tmp/app-live.css
    python3 tools/css-audit/fetch-app-css.py --out /tmp/app.css --port 9222
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HARNESS = REPO / "tools" / "print-harness"
sys.path.insert(0, str(HARNESS))

try:
    import cdp as harness  # noqa: E402  (reuses the harness CDP client)
except ImportError as e:  # pragma: no cover
    sys.exit(f"cannot import tools/print-harness/cdp.py: {e}")

JS = "fetch('app://obsidian.md/app.css').then(r => r.text())"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Fetch app.css from the running Obsidian (authoritative reference).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--port", type=int, default=9222, help="Obsidian remote debugging port")
    ap.add_argument("--out", default="/tmp/app-live.css", help="output path")
    args = ap.parse_args(argv)

    try:
        targets = harness.pick_targets(harness.list_targets(args.port), "app")
    except SystemExit as e:  # harness exits when the port is closed
        print(e, file=sys.stderr)
        return 2
    if not targets:
        print("no app target; start Obsidian with --remote-debugging-port", file=sys.stderr)
        return 2

    c = harness.CDP(targets[0]["webSocketDebuggerUrl"])
    try:
        text = c.eval(JS, await_promise=True)
    finally:
        c.close()
    if not isinstance(text, str) or len(text) < 100_000:
        print(f"unexpected payload ({type(text).__name__}, {len(text) if text else 0} chars)", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.write_text(text, encoding="utf-8")
    asar = Path("/Applications/Obsidian.app/Contents/Resources/obsidian.asar")
    extra = f"  (asar copy is {asar.stat().st_size} bytes — stale, do not use)" if asar.exists() else ""
    print(f"app.css: {len(text)} chars -> {out}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
