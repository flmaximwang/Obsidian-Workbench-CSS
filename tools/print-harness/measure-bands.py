#!/usr/bin/env python3
"""measure-bands —— 把 PDF 页面转成灰度位图后，量出「黑色条带」的位置/尺寸。

配合 export-probe.py 的标尺使用：72 dpi 下 1 px == 1 pt，于是一根 714px 宽的边框条
在正常导出里应量到 482pt（scale 0.9 + 默认页边距），被整页 fit 缩小时只有 321pt。

输出：每页墨迹外框 + 每条带（y 区间、高度 pt、x 区间、宽度 pt/mm）；可选 --expect 检查
文本层里必须出现的字串（找「内容被裁掉」这类问题）。

依赖：poppler（pdftoppm / pdftotext）。不需要 PIL：直接解析 pdftoppm 输出的 PGM。
参数默认值见 --help。
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile


def load_pgm(path: str) -> tuple[int, int, list[bytes]]:
    """读 P5 二值/灰度 PGM，返回 (width, height, rows)。"""
    with open(path, "rb") as fh:
        data = fh.read()
    if not data.startswith(b"P5"):
        raise ValueError(f"{path}: 不是 P5 PGM")
    # header: P5 <w> <h> <maxval>\n
    m = re.match(rb"P5\s+(\d+)\s+(\d+)\s+(\d+)\s", data)
    if not m:
        raise ValueError(f"{path}: PGM 头解析失败")
    w, h = int(m.group(1)), int(m.group(2))
    offset = m.end()
    return w, h, [data[offset + y * w: offset + (y + 1) * w] for y in range(h)]


def bands(rows: list[bytes], threshold: int) -> list[tuple[int, int, int, int]]:
    """把连续有墨的行合并成条带：(y0, y1, x0, x1)。"""
    out: list[tuple[int, int, int, int]] = []
    for y, row in enumerate(rows):
        xs = [x for x, v in enumerate(row) if v < threshold]
        if not xs:
            continue
        x0, x1 = xs[0], xs[-1]
        if out and out[-1][1] >= y - 3:
            p = out[-1]
            out[-1] = (p[0], y, min(p[2], x0), max(p[3], x1))
        else:
            out.append((y, y, x0, x1))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description="量 PDF 页面里的黑色条带（配合 export-probe.py 的标尺做版式判定）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("pdf")
    ap.add_argument("--pages", type=int, default=1, help="只看前 N 页")
    ap.add_argument("--dpi", type=int, default=72, help="渲染 DPI（72 时 1px = 1pt）")
    ap.add_argument("--threshold", type=int, default=128, help="灰度阈值（小于即算墨）")
    ap.add_argument("--expect", default="", help="逗号分隔的字串，检查是否出现在 PDF 文本层")
    ap.add_argument("--keep", action="store_true", help="保留渲染出的 PGM/PNG 以便肉眼复核")
    args = ap.parse_args()

    if not shutil.which("pdftoppm"):
        sys.exit("需要 poppler（pdftoppm）")
    info = subprocess.run(["pdfinfo", args.pdf], capture_output=True, text=True).stdout
    total = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    m = re.search(r"Page size:\s+([\d.]+ x [\d.]+)", info)
    size = m.group(1) if m else "?"
    print(f"# {args.pdf}: {total} 页, 页面 {size} pt")

    tmp = tempfile.mkdtemp(prefix="measure-bands-")
    last = min(args.pages, total)
    subprocess.run(["pdftoppm", "-gray", "-r", str(args.dpi), "-f", "1", "-l", str(last),
                    args.pdf, os.path.join(tmp, "p")], check=True)
    for i in range(1, last + 1):
        pgm = os.path.join(tmp, f"p-{i:02d}.pgm")
        if not os.path.exists(pgm):
            pgm = os.path.join(tmp, f"p-{i}.pgm")
        w, h, rows = load_pgm(pgm)
        bs = bands(rows, args.threshold)
        ink = (min(b[0] for b in bs), max(b[1] for b in bs), min(b[2] for b in bs), max(b[3] for b in bs)) if bs else None
        print(f"  p{i}: {w}x{h}px  墨迹外框={ink}  条带数={len(bs)}")
        for y0, y1, x0, x1 in bs[:6]:
            wpt, hpt = (x1 - x0 + 1) * 72.0 / args.dpi, (y1 - y0 + 1) * 72.0 / args.dpi
            print(f"      y {y0}..{y1} ({hpt:.0f}pt)  x {x0}..{x1}  w={wpt:.0f}pt "
                  f"= {wpt / 72 * 25.4:.1f}mm   -> 若标尺 714px 条: {wpt / 714:.3f} pt/px")
        if i == 1:
            print("      (正常 scale 0.9: 714px 条 = 482pt；整页被 fit 缩小 = 321pt)")

    if args.expect:
        text = subprocess.run(["pdftotext", args.pdf, "-"], capture_output=True, text=True).stdout
        for needle in [s.strip() for s in args.expect.split(",") if s.strip()]:
            print(f"  文本层包含 {needle!r}: {needle in text}")

    if args.keep:
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", "1", "-l", str(last),
                        args.pdf, os.path.join(tmp, "view")], check=True)
        print(f"  PNG 保留在 {tmp}/view-*.png")
    else:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
