#!/usr/bin/env python3
"""
print-harness — 抓取 Obsidian / Electron 应用「打印时」的 HTML，并与 app 中看到的 HTML 做对比。

背景（源码验证结论，Obsidian 1.6.7）：
  * 原生打印/导出 PDF：在主文档 body 里临时 append 一个 <div class="print">，
    渲染完笔记后调用 ipcRenderer.send('print-to-pdf')，主进程用**同一个 webContents**
    调 printToPDF()。打印媒体下 app.css 有 `body > :not(.print) { display:none !important }`，
    所以「打印 HTML = 同一文档 + .print 子树 + 其余兄弟节点被隐藏 + @media print 生效」。
  * better-export-pdf：把 app 的 head + `.print` 子树复制进一个独立的
    <webview src="app://obsidian.md/help.html" class="print-preview-container">，
    并把 app 里所有 @media print 规则「剥掉 media 包裹」后 insertCSS 进去（screen 媒体下也生效）。

用法：
  python3 cdp.py targets                       # 列出可连接的调试目标
  python3 cdp.py dump  --out DIR               # 抓 outerHTML + MHTML 快照
  python3 cdp.py media print                   # 切换 print/screen 媒体仿真
  python3 cdp.py pdf   --out x.pdf             # 用 print 媒体导出 PDF（确定性）
  python3 cdp.py styles --selectors sel.json   # 导出指定选择器的 computed style
  python3 cdp.py diff  A.html B.html           # 对比「打印 HTML」与「app HTML」
  python3 cdp.py png   x.pdf --outdir DIR      # PDF -> PNG（给能看图的 agent）
  python3 cdp.py pxdiff a.png b.png            # 像素级差异（ImageMagick）

依赖：websocket-client（pip install websocket-client）；png/pxdiff 需要 poppler 与 imagemagick。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser

try:
    import websocket  # websocket-client
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖：pip install websocket-client")

DEFAULT_PORT = 9222


# --------------------------------------------------------------------------- #
# CDP
# --------------------------------------------------------------------------- #
def list_targets(port: int) -> list[dict]:
    url = f"http://127.0.0.1:{port}/json/list"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.load(r)
    except urllib.error.URLError as e:
        sys.exit(f"连不上 {url}：{e}\n→ 应用必须先带 --remote-debugging-port={port} 启动。")


class CDP:
    def __init__(self, ws_url: str, timeout: float = 30.0):
        # suppress_origin: Electron 拒绝带 Origin 头的 devtools 连接（403），
        # 见 README §0 的注记。websocket-client 默认会带，必须显式关掉。
        self.ws = websocket.create_connection(
            ws_url, timeout=timeout, max_size=512 * 1024 * 1024, suppress_origin=True
        )
        self._id = 0

    def call(self, method: str, **params):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        deadline = time.time() + 60
        while time.time() < deadline:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(method)

    def eval(self, expr: str, await_promise: bool = False):
        r = self.call(
            "Runtime.evaluate",
            expression=expr,
            returnByValue=True,
            awaitPromise=await_promise,
            userGesture=True,
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(f"JS 异常：{r['exceptionDetails'].get('text')}")
        return r["result"].get("value")

    def drain(self, wait: float = 1.0):
        """收集 wait 秒内推送的事件（无 id 的消息），例如 CSS.styleSheetAdded。"""
        evs = []
        self.ws.settimeout(wait)
        try:
            while True:
                msg = json.loads(self.ws.recv())
                if "method" in msg:
                    evs.append(msg)
        except Exception:  # 超时即结束
            pass
        finally:
            self.ws.settimeout(30)
        return evs

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def pick_targets(targets: list[dict], which: str) -> list[dict]:
    """which: all | app | webview | print"""
    pages = [t for t in targets if t.get("type") in ("page", "webview", "iframe")]
    pages = [t for t in pages if t.get("webSocketDebuggerUrl")]
    if which == "all":
        return pages
    if which == "app":  # 主界面（Obsidian: app://obsidian.md/index.html）
        return [t for t in pages if t.get("url", "").startswith("app://") and "index.html" in t["url"]] or pages[:1]
    if which == "webview":  # better-export-pdf 的打印预览文档
        return [t for t in pages if t.get("url", "").startswith("app://") and "index.html" not in t["url"]]
    if which == "print":
        return [t for t in pages if t.get("title", "").startswith("print")] or [
            t for t in pages if t.get("url", "").startswith("app://") and "index.html" not in t["url"]
        ]
    raise ValueError(which)


def slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:80] or "target"


# --------------------------------------------------------------------------- #
# 子命令
# --------------------------------------------------------------------------- #
def cmd_targets(args):
    for t in list_targets(args.port):
        print(f"{t['type']:8} {t.get('title','')[:40]:42} {t.get('url','')[:90]}")
        print(f"         ws: {t.get('webSocketDebuggerUrl','')}")


def cmd_dump(args):
    os.makedirs(args.out, exist_ok=True)
    targets = pick_targets(list_targets(args.port), args.target)
    if not targets:
        sys.exit("没有匹配的调试目标。")
    for t in targets:
        name = slug(t.get("title") or t.get("url") or t["id"])
        if args.media:
            name = f"{name}.{args.media}media"
        c = CDP(t["webSocketDebuggerUrl"])
        try:
            if args.media:  # 媒体仿真只在本连接内有效，必须同连接抓取
                c.call("Emulation.setEmulatedMedia", media=args.media)
            html = c.eval("document.documentElement.outerHTML")
            p_html = os.path.join(args.out, f"{name}.html")
            with open(p_html, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[html] {p_html}  ({len(html)} chars)  <- {t.get('url')}")
            body_classes = c.eval("JSON.stringify({body:document.body.className, html:document.documentElement.className,"
                                  "print:!!document.querySelector('.print'),"
                                  "media_print:matchMedia('print').matches,"
                                  "inner:[innerWidth,innerHeight]})")
            print(f"[meta] {body_classes}")
            try:  # MHTML：单文件快照，带样式与图片
                snap = c.call("Page.captureSnapshot", format="mhtml")
                p_mht = os.path.join(args.out, f"{name}.mhtml")
                with open(p_mht, "w", encoding="utf-8") as f:
                    f.write(snap.get("data", ""))
                print(f"[mhtml] {p_mht}")
            except Exception as e:  # noqa: BLE001
                print(f"[mhtml] 跳过：{e}")
        finally:
            c.close()


def cmd_media(args):
    targets = pick_targets(list_targets(args.port), args.target)
    for t in targets:
        c = CDP(t["webSocketDebuggerUrl"])
        try:
            c.call("Emulation.setEmulatedMedia", media=args.media)
            is_print = c.eval('matchMedia("print").matches')
            print(f"media={args.media}  matchMedia('print')={is_print}  <- {t.get('url')}")
        finally:
            c.close()


def cmd_pdf(args):
    targets = pick_targets(list_targets(args.port), args.target)
    t = targets[0]
    c = CDP(t["webSocketDebuggerUrl"])
    try:
        c.call("Emulation.setEmulatedMedia", media="print")
        opts = dict(
            printBackground=args.background,
            landscape=args.landscape,
            scale=args.scale / 100.0,
            preferCSSPageSize=args.css_page_size,
            transferMode="ReturnAsBase64",
        )
        if args.pagesize:
            w, h = {"A4": (8.27, 11.69), "A3": (11.69, 16.54), "Letter": (8.5, 11.0)}[args.pagesize]
            opts["paperWidth"], opts["paperHeight"] = w, h
        r = c.call("Page.printToPDF", **opts)
        with open(args.out, "wb") as f:
            f.write(__import__("base64").b64decode(r["data"]))
        print(f"[pdf] {args.out} <- {t.get('url')}  ({os.path.getsize(args.out)} bytes)")
    finally:
        c.close()


DEFAULT_SELECTORS = [
    "body", ".print", ".print > .markdown-preview-view", ".markdown-preview-view",
    ".markdown-preview-sizer", ".markdown-preview-view > div", "table", ".callout",
    ".markdown-rendered > *:first-child",
]


def cmd_styles(args):
    sels = DEFAULT_SELECTORS
    if args.selectors:
        with open(args.selectors, encoding="utf-8") as f:
            sels = json.load(f)
    expr = """
(() => {
  const props = %s;
  const out = {};
  for (const sel of props) {
    const el = document.querySelector(sel);
    if (!el) { out[sel] = null; continue; }
    const cs = getComputedStyle(el);
    const box = el.getBoundingClientRect();
    out[sel] = {
      width: cs.width, maxWidth: cs.maxWidth, minWidth: cs.minWidth,
      margin: cs.margin, padding: cs.padding, display: cs.display,
      fontSize: cs.fontSize, lineHeight: cs.lineHeight, color: cs.color,
      fontFamily: cs.fontFamily.slice(0, 60),
      breakInside: cs.breakInside, pageBreakAfter: cs.pageBreakAfter,
      rect: [Math.round(box.width), Math.round(box.height)],
      varPrintZoom: cs.getPropertyValue('--print-zoom'),
      varPrintPageWidth: cs.getPropertyValue('--print-page-width'),
    };
  }
  return JSON.stringify(out, null, 2);
})()
""" % json.dumps(sels)
    targets = pick_targets(list_targets(args.port), args.target)
    for t in targets:
        c = CDP(t["webSocketDebuggerUrl"])
        try:
            if args.media:
                c.call("Emulation.setEmulatedMedia", media=args.media)
            res = json.loads(c.eval(expr))
            media_print = c.eval('matchMedia("print").matches')
            print(f"# {t.get('url')}  media_print={media_print}  (emulated={args.media or 'none'})")
            for k, v in res.items():
                print(f"  {k}: {json.dumps(v, ensure_ascii=False)}")
            if args.out:
                os.makedirs(args.out, exist_ok=True)
                with open(os.path.join(args.out, "styles-%s.json" % slug(t.get("title") or t["id"])), "w", encoding="utf-8") as f:
                    json.dump({t.get("url"): res}, f, ensure_ascii=False, indent=2)
        finally:
            c.close()


# --------------------------------------------------------------------------- #
# CSS 侧：样式表枚举 / 命中规则诊断 / 在线改写 / 离线 fixture
# --------------------------------------------------------------------------- #
ENUM_JS = """(() => {
  const sheets = Array.from(document.styleSheets).map((s, i) => {
    let rules = null, err = null;
    try { rules = s.cssRules.length; } catch (e) { err = e.name; }
    const o = s.ownerNode;
    return {i, href: s.href, ownerTag: o ? o.tagName : null,
            ownerId: o ? (o.id || null) : null, disabled: !!s.disabled,
            isInline: !s.href, rules, err};
  });
  return JSON.stringify(sheets);
})()"""


def _enum_sheets(c):
    """用 JS 枚举 document.styleSheets（顺序 = 级联顺序）。
    链接表通过 Page.getResourceContent 读原文（不受跨源限制）。
    注意：用 insertCSS/浏览器注入的样式表**不在** document.styleSheets 里，
    需要靠 `matched` 从命中规则里反查（origin=injected/user）。"""
    c.call("Page.enable")
    c.call("DOM.enable")
    info = json.loads(c.eval(ENUM_JS))
    frame = c.call("Page.getFrameTree")["frameTree"]["frame"]["id"]
    out = []
    for s in info:
        text, err = None, s.get("err")
        if s["isInline"]:
            text = c.eval(
                "(() => { const s = Array.from(document.styleSheets)[%d];"
                " return s && s.ownerNode ? s.ownerNode.textContent : null; })()" % s["i"]
            )
        else:
            try:
                text = c.call("Page.getResourceContent", frameId=frame, url=s["href"]).get("content")
            except Exception as e:  # noqa: BLE001
                err = f"getResourceContent: {e}"
        out.append({**s, "text": text,
                    "source": s["href"] or f"inline:{s.get('ownerId') or 'style'}", "err2": err})
    return out


def _dump_sheet(out_dir, i, sheet):
    if sheet["text"] is None:
        return None
    base = os.path.basename(sheet["source"]) or "inline"
    if not base.endswith(".css"):
        base += ".css"
    name = f"{i:02d}-{slug(base)[:-4]}.css"
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        f.write(sheet["text"])
    return name


def cmd_sheets(args):
    targets = pick_targets(list_targets(args.port), args.target)
    for t in targets:
        c = CDP(t["webSocketDebuggerUrl"])
        try:
            sheets = _enum_sheets(c)
            print(f"# {t.get('url')}  sheets={len(sheets)}  （按级联顺序，后面的覆盖前面的）")
            if args.out:
                os.makedirs(args.out, exist_ok=True)
            for s in sheets:
                flag = " (disabled)" if s["disabled"] else ""
                rules = f"{s['rules']} rules" if s["rules"] is not None else f"读不到规则: {s['err']}"
                size = f"{len(s['text'])} chars" if s["text"] is not None else "原文不可读"
                kind = "inline" if s["isInline"] else "link  "
                print(f"  [{s['i']:02d}] {kind} {size:>13}  {rules:>22}  {s['source'][:64]}{flag}")
                if args.out:
                    _dump_sheet(args.out, s["i"], s)
            if args.out:
                print(f"[sheets] 已写入 {args.out}")
        finally:
            c.close()


def cmd_matched(args):
    targets = pick_targets(list_targets(args.port), args.target)
    for t in targets:
        c = CDP(t["webSocketDebuggerUrl"])
        try:
            c.call("DOM.enable")
            c.call("CSS.enable")
            if args.media:  # 关键：@media print 里的规则只在 print 媒体下才"命中"
                c.call("Emulation.setEmulatedMedia", media=args.media)
            root = c.call("DOM.getDocument", depth=0)["root"]["nodeId"]
            nid = c.call("DOM.querySelector", nodeId=root, selector=args.selector).get("nodeId")
            if not nid:
                print(f"# {t.get('url')} 选择器未命中任何元素：{args.selector}")
                continue
            media_print = c.eval('matchMedia("print").matches')
            print(f"# {t.get('url')}  选择器 {args.selector}  节点 {nid}  media_print={media_print}")
            ms = c.call("CSS.getMatchedStylesForNode", nodeId=nid)
            if not ms.get("matchedCSSRules"):
                print("  （没有任何规则命中这个元素——选择器没写对，或该元素只在别的媒体下存在）")
            for e in ms.get("matchedCSSRules", []):
                r = e["rule"]
                sid = r.get("styleSheetId")
                origin = r.get("origin", "?")
                media = " ".join(m["text"] for m in r.get("media") or []) or "screen"
                decl = "; ".join(
                    f"{p['name']}:{p.get('value')}"
                    for p in r["style"].get("cssProperties", [])
                    if p.get("value") is not None and not p.get("disabled")
                )
                print(f"  [origin={origin:9}] @media {media:20} {r['selectorList']['text'][:64]}")
                print(f"      {decl[:280]}")
                if sid and origin in ("injected", "user") and args.out:
                    # 注入类样式表不在 document.styleSheets 里，只能这样把原文抠出来
                    try:
                        text = c.call("CSS.getStyleSheetText", styleSheetId=sid)["text"]
                        os.makedirs(args.out, exist_ok=True)
                        name = f"injected-{slug(sid)}.css"
                        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
                            f.write(text)
                        print(f"      → 注入表原文 {len(text)} chars 已存 {args.out}/{name}")
                    except Exception as e:  # noqa: BLE001
                        print(f"      → 注入表原文读取失败：{e}")
            if ms.get("inlineStyle"):
                print("  [inline style]", ms["inlineStyle"]["cssText"][:200])
        finally:
            c.close()


def cmd_inject(args):
    css = args.css_text
    if args.css:
        with open(args.css, encoding="utf-8") as f:
            css = f.read()
    if not css:
        sys.exit("需要 --css <文件> 或 --css-text '<css>'")
    targets = pick_targets(list_targets(args.port), args.target)
    for t in targets:
        c = CDP(t["webSocketDebuggerUrl"])
        try:
            expr = (
                "(() => {"
                "  const el = document.createElement('style');"
                "  el.id = 'harness-injected-' + document.querySelectorAll('[id^=harness-injected]').length;"
                f"  el.textContent = {json.dumps(css)};"
                "  document.head.appendChild(el);"
                "  return JSON.stringify({id: el.id, len: el.textContent.length,"
                "    stylesheets: document.styleSheets.length,"
                "    sheetText: Array.from(document.styleSheets).pop().ownerNode.id});"
                "})()"
            )
            info = json.loads(c.eval(expr))
            print(f"[inject] {info['len']} chars 注入到 {t.get('url')}（{info['id']}）；"
                  f"该文档现有 {info['stylesheets']} 张样式表（新表在最后 = 级联优先级最高）")
        finally:
            c.close()


def cmd_setsheet(args):
    """把第 N 张样式表的**内容**换成给定 CSS：
    内联表 → 直接改 ownerNode.textContent；链接表 → 停用它并补一张同内容的 <style>（位置在最后）。
    这是"如果我这样改主题的 print 规则，会怎样"的最快验证方式，全程不碰仓库。"""
    with open(args.css, encoding="utf-8") as f:
        text = f.read()
    targets = pick_targets(list_targets(args.port), args.target)
    for t in targets:
        c = CDP(t["webSocketDebuggerUrl"])
        try:
            sheets = _enum_sheets(c)
            if not 0 <= args.index < len(sheets):
                sys.exit(f"--index 越界：该文档只有 {len(sheets)} 张样式表")
            s = sheets[args.index]
            expr = """(() => {
              const i = %d, text = %s;
              const sheet = Array.from(document.styleSheets)[i];
              if (!sheet) return JSON.stringify({ok: false, why: 'no sheet'});
              if (!sheet.href) {
                const el = sheet.ownerNode;
                if (!el) return JSON.stringify({ok: false, why: 'inline without ownerNode'});
                el.textContent = text;
                return JSON.stringify({ok: true, mode: 'inline-replaced', owner: el.id || 'style'});
              }
              sheet.disabled = true;
              const el = document.createElement('style');
              el.id = 'harness-replaced-%d';
              el.textContent = text;
              document.head.appendChild(el);
              return JSON.stringify({ok: true, mode: 'link-disabled+new-style', href: sheet.href});
            })()""" % (args.index, json.dumps(text), args.index)
            info = json.loads(c.eval(expr))
            print(f"[setsheet] [{args.index:02d}] {s['source'][:60]} -> {info}")
            print("           复核：cdp.py styles --media print …（看目标选择器的实际值）")
        finally:
            c.close()


LINK_RE = re.compile(r"<link\b[^>]*rel=[\"']?stylesheet[\"']?[^>]*>", re.I)
STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.I | re.S)
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)


def cmd_fixture(args):
    """把打印文档固化成可离线复跑的目录：html + 各样式表 + manifest。"""
    targets = pick_targets(list_targets(args.port), args.target)
    t = targets[0]
    c = CDP(t["webSocketDebuggerUrl"])
    out = args.out
    try:
        html = c.eval("document.documentElement.outerHTML")
        meta = json.loads(c.eval(
            'JSON.stringify({url:location.href,title:document.title,'
            'bodyClass:document.body.className,htmlClass:document.documentElement.className,'
            'printEl:!!document.querySelector(".print"),'
            'inner:[window.innerWidth,window.innerHeight],'
            'ua:navigator.userAgent})'
        ))
        enumerated = _enum_sheets(c)
        sheets = []
        os.makedirs(os.path.join(out, "sheets"), exist_ok=True)
        concat = []
        for s in enumerated:
            if s["text"] is None:
                continue
            base = os.path.basename(s["source"]) or "inline"
            if not base.endswith(".css"):
                base += ".css"
            name = f"{s['i']:02d}-{slug(base)[:-4]}.css"
            with open(os.path.join(out, "sheets", name), "w", encoding="utf-8") as f:
                f.write(s["text"])
            sheets.append({"index": s["i"], "file": f"sheets/{name}", "source": s["source"],
                           "isInline": s["isInline"], "bytes": len(s["text"])})
            concat.append(f"/* ==== [{s['i']:02d}] {s['source']} ==== */\n{s['text']}\n")
        with open(os.path.join(out, "print.html"), "w", encoding="utf-8") as f:
            f.write(html)
        # 扁平化版本：去掉 link/style/script，把全部样式按级联顺序塞进 head 末尾
        flat = SCRIPT_RE.sub("", LINK_RE.sub("", STYLE_RE.sub("", html)))
        style_block = "<style id=\"fixture-flattened\">\n" + "\n".join(concat) + "\n</style>"
        flat = flat.replace("</head>", style_block + "\n</head>", 1)
        with open(os.path.join(out, "fixture.html"), "w", encoding="utf-8") as f:
            f.write(flat)
        with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump({"source": meta, "sheets": sheets,
                       "note": "fixture.html 是扁平化版本（样式表按级联顺序内联），"
                               "print.html 是原始序列化；两者都不再依赖 app:// 协议。",
                       "print_options": {"pageSize": args.pagesize, "scale": args.scale,
                                         "margins": "default", "printBackground": args.background}},
                      f, ensure_ascii=False, indent=2)
        print(f"[fixture] {out}/print.html  ({len(html)} chars)")
        print(f"[fixture] {out}/fixture.html  ({len(flat)} chars, {len(sheets)} stylesheets 内联)")
        print(f"[fixture] {out}/manifest.json")
        print(f"[fixture] source: {meta['url']}  body='{meta['bodyClass']}'  .print={meta['printEl']}")
    finally:
        c.close()


# --------------------------------------------------------------------------- #
# HTML 结构对比
# --------------------------------------------------------------------------- #
class Census(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: dict[str, int] = {}
        self.classes: dict[str, int] = {}
        self.ids: dict[str, int] = {}

    def handle_starttag(self, tag, attrs):
        self.tags[tag] = self.tags.get(tag, 0) + 1
        d = dict(attrs)
        for c in (d.get("class") or "").split():
            self.classes[c] = self.classes.get(c, 0) + 1
        if d.get("id"):
            self.ids[d["id"]] = self.ids.get(d["id"], 0) + 1


def census(path):
    c = Census()
    with open(path, encoding="utf-8") as f:
        c.feed(f.read())
    return c


def cmd_diff(args):
    a, b = census(args.a), census(args.b)
    def table(title, ka, kb):
        keys = sorted(set(ka) | set(kb), key=lambda k: -(abs(ka.get(k, 0) - kb.get(k, 0))))
        rows = [(k, ka.get(k, 0), kb.get(k, 0)) for k in keys if ka.get(k, 0) != kb.get(k, 0)]
        print(f"\n## {title}（只列不同的，按差值排序，最多 40 行）")
        print(f"   {'':38} {'A(print)':>9} {'B(app)':>8}")
        for k, x, y in rows[:40]:
            print(f"   {k[:38]:38} {x:>9} {y:>8}")
        print(f"   — 共 {len(rows)} 项不同")
    print(f"A = {args.a}\nB = {args.b}")
    table("元素计数 tags", a.tags, b.tags)
    table("class 计数", a.classes, b.classes)
    print("\n## 只在 A 中出现的 class")
    print("   ", sorted(set(a.classes) - set(b.classes))[:60])
    print("## 只在 B 中出现的 class")
    print("   ", sorted(set(b.classes) - set(a.classes))[:60])


def cmd_png(args):
    outdir = args.outdir or os.path.splitext(args.pdf)[0] + ".pages"
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(
        [shutil.which("pdftoppm") or "pdftoppm", "-png", "-r", str(args.dpi), args.pdf,
         os.path.join(outdir, "page")],
        check=True,
    )
    files = sorted(os.listdir(outdir))
    for f in files:
        print(os.path.join(outdir, f))
    print(f"[{len(files)} page(s)] PDF 页数：", end=" ")
    subprocess.run(["pdfinfo", args.pdf], check=False)


def cmd_pxdiff(args):
    if not shutil.which("magick"):
        sys.exit("需要 ImageMagick（magick）。")
    r = subprocess.run(["magick", "compare", "-metric", "RMSE", args.a, args.b, args.out],
                       capture_output=True, text=True)
    print(f"RMSE: {r.stderr.strip()}")
    print(f"diff image: {args.out}")


# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(
        description="抓取 Electron(Obsidian) 打印时的 HTML/PDF 并与 app HTML 对比",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help="远程调试端口")
    p.add_argument("--target", default="app", choices=["app", "webview", "print", "all"],
                   help="要操作的调试目标")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("targets", help="列出调试目标").set_defaults(func=cmd_targets)

    d = sub.add_parser("dump", help="抓 outerHTML + MHTML")
    d.add_argument("--out", default="captures", help="输出目录")
    d.add_argument("--media", choices=["print", "screen"], help="抓取前临时仿真该媒体类型（同一连接内生效）")
    d.set_defaults(func=cmd_dump)

    m = sub.add_parser("media", help="切换媒体仿真")
    m.add_argument("media", choices=["print", "screen"], help="媒体类型")
    m.set_defaults(func=cmd_media)

    q = sub.add_parser("pdf", help="用 print 媒体导出 PDF")
    q.add_argument("--out", default="out.pdf")
    q.add_argument("--pagesize", default="A4", choices=["A4", "A3", "Letter"])
    q.add_argument("--scale", type=int, default=100, help="缩放百分比")
    q.add_argument("--background", action="store_true", help="打印背景色/图")
    q.add_argument("--landscape", action="store_true")
    q.add_argument("--css-page-size", action="store_true", help="尊重 CSS @page size")
    q.set_defaults(func=cmd_pdf)

    s = sub.add_parser("styles", help="导出关键选择器的 computed style")
    s.add_argument("--selectors", help="JSON 文件，内容为选择器数组")
    s.add_argument("--out", help="把结果存到该目录")
    s.add_argument("--media", choices=["print", "screen"], help="抓取前临时仿真该媒体类型")
    s.set_defaults(func=cmd_styles)

    df = sub.add_parser("diff", help="对比两个 HTML 的结构差异")
    df.add_argument("a", help="打印时抓到的 HTML")
    df.add_argument("b", help="app 中抓到的 HTML")
    df.set_defaults(func=cmd_diff)

    sh = sub.add_parser("sheets", help="按级联顺序列出/导出全部样式表")
    sh.add_argument("--out", help="把每张样式表导出到该目录")
    sh.set_defaults(func=cmd_sheets)

    mt = sub.add_parser("matched", help="诊断某选择器命中了哪些规则（含来源与 @media）")
    mt.add_argument("selector", help="CSS 选择器，如 '.print > .markdown-preview-view'")
    mt.add_argument("--media", choices=["print", "screen"], help="在该媒体下诊断（@media print 规则必须选 print）")
    mt.add_argument("--out", help="把遇到的注入表原文存到该目录")
    mt.set_defaults(func=cmd_matched)

    ij = sub.add_parser("inject", help="向当前文档追加一张样式表（不改仓库，用于 A/B）")
    ij.add_argument("--css", help="CSS 文件")
    ij.add_argument("--css-text", help="直接给一段 CSS", dest="css_text")
    ij.set_defaults(func=cmd_inject)

    ss = sub.add_parser("setsheet", help="整体替换第 N 张样式表的文本")
    ss.add_argument("--index", type=int, required=True)
    ss.add_argument("--css", required=True)
    ss.set_defaults(func=cmd_setsheet)

    fx = sub.add_parser("fixture", help="把打印文档固化成离线可复跑的目录")
    fx.add_argument("--out", required=True)
    fx.add_argument("--pagesize", default="A4", choices=["A4", "A3", "Letter"])
    fx.add_argument("--scale", type=int, default=100)
    fx.add_argument("--background", action="store_true")
    fx.set_defaults(func=cmd_fixture)

    pn = sub.add_parser("png", help="PDF -> 每页 PNG")
    pn.add_argument("pdf")
    pn.add_argument("--dpi", type=int, default=110)
    pn.add_argument("--outdir")
    pn.set_defaults(func=cmd_png)

    px = sub.add_parser("pxdiff", help="两张图的像素差异")
    px.add_argument("a")
    px.add_argument("b")
    px.add_argument("--out", default="pxdiff.png")
    px.set_defaults(func=cmd_pxdiff)
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
