#!/usr/bin/env python3
"""export-probe —— 在运行中的 Obsidian 里，用「插件同款选项」导出一篇笔记，并可
   · 往待打印文档里插一根已知尺寸的边框标尺（printBackground=false 时只有边框会印）
   · 临时删掉文档里的某些元素（找出是谁在把页面撑宽）

用途：定位「导出 PDF 版式不对」——尤其是**整页被等比缩小**这类问题。
判据：标尺 714px 条若印成 482pt（scale 0.9 / 默认页边距）就是正常；
      印成 321pt 说明整页被 Chromium 的 fit-to-page 缩小了（去查超宽内容，典型是 Base 视图）。

示例：
  python3 export-probe.py --file Logs/2026/09/07/SEC-001/SEC-001.md --out /tmp/sec001/a.pdf
  python3 export-probe.py --file <note> --drop .bases-embed --out /tmp/sec001/b.pdf
  python3 export-probe.py --file <note> --css-file /tmp/candidate.css --out /tmp/sec001/c.pdf
  python3 measure-bands.py /tmp/sec001/a.pdf --pages 1

依赖：websocket-client（`suppress_origin` 绕过 Electron 的 Origin 403）、Obsidian 需带
      --remote-debugging-port 启动。参数默认值见 --help（本文件不重复维护参数说明）。
"""
from __future__ import annotations

import argparse
import json
import sys

import websocket as _ws

_orig_create_connection = _ws.create_connection


def _create_connection(url, *a, **kw):  # Electron 拒绝带 Origin 头的 WebSocket
    kw.setdefault("suppress_origin", True)
    return _orig_create_connection(url, *a, **kw)


_ws.create_connection = _create_connection

from cdp import CDP, list_targets  # noqa: E402  (同目录)

RULER = (
    '<div class="harness-ruler">'
    '<div style="width:714px; height:0; border-top:40px solid #000; margin:0"></div>'
    '<div style="width:400px; height:0; border-top:20px solid #000; margin:0"></div>'
    '<div style="width:100px; height:0; border-top:20px solid #000; margin:0"></div>'
    "</div>"
)

MARGINS = {
    "default": "{marginType: 'default'}",
    "none": "{top: 0, left: 0, bottom: 0, right: 0}",
    "small": "{top: 2.54, left: 2.54, bottom: 2.54, right: 2.54}",
}

JS = r"""
(async () => {
  const FILE = FILE_JSON, OUT = OUT_JSON, DROP = DROP_LIST, CSS = CSS_JSON,
        SCALE = SCALE_NUM, PAGESIZE = PAGESIZE_JSON, MARGINS = MARGINS_JS, RULER = RULER_JSON;
  const out = {};
  document.querySelectorAll('.harness-ruler, #harness-probe-css').forEach(e => e.remove());
  document.querySelector('.modal-container .modal-header-button')?.click();
  await new Promise(r => setTimeout(r, 400));
  document.querySelectorAll('.print').forEach(e => e.remove());   // 清掉插件残留副本

  const f = app.vault.getAbstractFileByPath(FILE);
  if (!f) return JSON.stringify({error: 'file not found: ' + FILE});
  await app.workspace.getLeaf(false).openFile(f);
  await new Promise(r => setTimeout(r, 900));

  if (CSS) {
    const st = document.createElement('style');
    st.id = 'harness-probe-css';
    st.textContent = CSS;
    document.head.appendChild(st);
  }
  app.commands.executeCommandById('better-export-pdf:export-current-file-to-pdf');
  await new Promise(r => setTimeout(r, 4500));

  const docs = Array.from(document.querySelectorAll('.print'))
      .filter(d => d.querySelector('.markdown-preview-view') && d.offsetHeight > 300);
  out.docs = docs.map(d => [d.className, d.offsetHeight]);
  out.rulersIn = [];
  docs.forEach((d, i) => {
    const view = d.querySelector('.markdown-preview-view');
    DROP.forEach(sel => view.querySelectorAll(sel).forEach(e => e.remove()));
    if (RULER) {
      const holder = document.createElement('div');
      holder.innerHTML = RULER;
      view.prepend(holder.firstElementChild);
      out.rulersIn.push(i);
    }
  });

  const { ipcRenderer } = require('electron');
  await new Promise(res => { ipcRenderer.once('print-to-pdf', res);
    ipcRenderer.send('print-to-pdf', {pageSize: PAGESIZE, landscape: false, open: false,
      printBackground: false, generateTaggedPDF: false, scale: SCALE, margins: MARGINS,
      displayHeaderFooter: false, headerTemplate: '<span></span>', footerTemplate: '<span></span>',
      filepath: OUT}); });
  out.exported = OUT;

  document.querySelectorAll('.harness-ruler, #harness-probe-css').forEach(e => e.remove());
  document.querySelector('.modal-container .modal-header-button')?.click();
  await new Promise(r => setTimeout(r, 300));
  out.cleanup = {modals: document.querySelectorAll('.modal-container').length,
                 rulers: document.querySelectorAll('.harness-ruler').length};
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
    sys.exit(f"没找到 vault 前缀为 {vault_prefix!r} 的 Obsidian 窗口（先用 cdp.py targets 看看）")


def main() -> None:
    p = argparse.ArgumentParser(
        description="在运行中的 Obsidian 里用插件同款选项导出笔记（可插标尺 / 删元素 / 注入 CSS）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--port", type=int, default=9222, help="Obsidian 远程调试端口")
    p.add_argument("--vault-prefix", default="zsqlab08", help="用来挑选目标窗口的 vault 名前缀")
    p.add_argument("--file", required=True, help="vault 内相对路径，如 Logs/2026/09/07/SEC-001/SEC-001.md")
    p.add_argument("--out", required=True, help="输出 PDF 路径")
    p.add_argument("--drop", action="append", default=[], help="导出前从打印文档里删掉的 CSS 选择器（可重复）")
    p.add_argument("--css", default=None, help="注入到 app 的 CSS 文本（用于 A/B 候选规则）")
    p.add_argument("--css-file", default=None, help="从文件读取要注入的 CSS")
    p.add_argument("--no-ruler", action="store_true", help="不插标尺（只看版式时用）")
    p.add_argument("--scale", type=int, default=90, help="打印缩放百分比（插件对话框里的 scale）")
    p.add_argument("--pagesize", default="A4", help="纸张尺寸，如 A4 / A3 / Letter / Custom")
    p.add_argument("--margins", choices=sorted(MARGINS), default="default", help="页边距档位")
    args = p.parse_args()

    css = args.css
    if args.css_file:
        with open(args.css_file, encoding="utf-8") as fh:
            css = fh.read()

    t = pick_target(args.port, args.vault_prefix)
    c = CDP(t["webSocketDebuggerUrl"])
    try:
        js = (JS.replace("FILE_JSON", json.dumps(args.file))
                .replace("OUT_JSON", json.dumps(args.out))
                .replace("DROP_LIST", json.dumps(args.drop))
                .replace("CSS_JSON", json.dumps(css))
                .replace("SCALE_NUM", str(args.scale / 100.0))
                .replace("PAGESIZE_JSON", json.dumps(args.pagesize))
                .replace("MARGINS_JS", MARGINS[args.margins])
                .replace("RULER_JSON", json.dumps("" if args.no_ruler else RULER)))
        r = c.call("Runtime.evaluate", expression=js, returnByValue=True, awaitPromise=True,
                   userGesture=True, timeout=180000)
        if r.get("exceptionDetails"):
            sys.exit(f"JS 异常：{json.dumps(r['exceptionDetails'], ensure_ascii=False)[:800]}")
        print(json.dumps(json.loads(r["result"]["value"]), indent=2, ensure_ascii=False))
    finally:
        c.close()


if __name__ == "__main__":
    main()
