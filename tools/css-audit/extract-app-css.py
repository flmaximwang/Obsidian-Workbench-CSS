#!/usr/bin/env python3
"""Extract app.css (and any other file) from Obsidian's packed obsidian.asar.

The asar format: 16-byte header (u32 magic=4, u32 pickle size, u32 json size, u32 json size),
then the JSON directory, padded to a 4-byte boundary, then the file payloads.

Usage:
    python3 extract-app-css.py                 # -> /tmp/app.css
    python3 extract-app-css.py --out /tmp/x.css
    python3 extract-app-css.py --asar /Applications/Obsidian.app/Contents/Resources/obsidian.asar
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

DEFAULT_ASAR = "/Applications/Obsidian.app/Contents/Resources/obsidian.asar"


def find_asar() -> Path:
    p = Path(DEFAULT_ASAR)
    if p.exists():
        return p
    # fall back to the app.asar of a non-standard install
    raise SystemExit(f"obsidian.asar not found at {DEFAULT_ASAR}")


def extract(asar: Path, member: str, out: Path) -> Path:
    blob = asar.read_bytes()
    _, _pickle_size, json_size, _json_size_dup = struct.unpack("<IIII", blob[:16])
    header, _end = json.JSONDecoder().raw_decode(blob[16 : 16 + json_size].decode("utf-8", "ignore"))
    base = 16 + json_size
    base += (4 - base % 4) % 4  # header block is padded to a 4-byte boundary

    node = header
    for part in member.split("/"):
        node = node["files"][part]
    start = base + int(node["offset"])
    out.write_bytes(blob[start : start + int(node["size"])])
    return out


def main(argv: list[str] | None = None) -> int:
    print("WARNING: the app.css inside obsidian.asar is TRUNCATED and STALE "
          "(426 KB vs 655 KB served at runtime, with different values).\n"
          "         Do not audit theme tokens against it — use: "
          "python3 tools/css-audit/fetch-app-css.py\n", file=sys.stderr)
    ap = argparse.ArgumentParser(
        description="Extract app.css (or any member) from Obsidian's packed obsidian.asar.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--asar", default=str(find_asar()), help="path to obsidian.asar")
    ap.add_argument("--member", default="app.css", help="file inside the asar (slash separated)")
    ap.add_argument("--out", default="/tmp/app.css", help="output path")
    args = ap.parse_args(argv)

    out = extract(Path(args.asar), args.member, Path(args.out))
    n = out.stat().st_size
    print(f"{args.member}: {n} bytes -> {out}")
    if n == 0:
        print("WARNING: extracted 0 bytes — check --member", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
