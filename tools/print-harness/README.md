# print-harness —— Obsidian 主题「打印/PDF」测试回路

目的：能**拿到打印时真正被渲染的那份 HTML**，把它与 app 中看到的 DOM 对比，
并把打印结果转成可比较的 PDF/PNG，让 CSS 改动可以回归验证。

以下机制均来自本机源码实测（Obsidian 1.6.7 的 `obsidian.asar` 与
`better-export-pdf` 2.0.3 的 `main.js`），不是推测。

---

## 0. 先看这里：定位"导出 PDF 版式不对"的标准动作

```bash
python3 export-probe.py --file <vault 内相对路径> --out /tmp/a.pdf   # 清残留 .print + 插标尺 + 用插件同款选项真导出
python3 measure-bands.py /tmp/a.pdf --pages 1 --expect "<必须出现的文字>"
```

- 714px 标尺条印成 **482pt**（首块 h=54pt）⇒ 正常（0.675 pt/px = 0.75 × 导出 scale 0.9）。
- 印成 **321pt**（首块 h=36pt）⇒ **整页被 Chromium 的 fit-to-page 缩小**：
  去找把文档撑到页面宽的内容，**典型是 Base 视图** ⇒ 见 `FINDINGS-base-fit-shrink.md`。
- 判定小抄：**连临时插进去的标尺都等比变小 ⇒ 整页 fit-shrink（内容侧问题）；
  只有个别元素异常 ⇒ 才是主题的宽度计算问题。**

注意（都是实测踩过的）：
`printBackground:false` 时**CSS 背景不打印**，标尺只能用 `border`；
CDP 的 `Emulation.setEmulatedMedia(print)` 只能验证**布局宽度**，量不到整页缩放，必须真导出量像素；
`websocket-client` 会带 `Origin` 头被 Electron 403 拒接（本目录脚本用 `suppress_origin=True` 绕过，
或给 Obsidian 加 `--remote-allow-origins=*`）。

---

## 1. 为什么「打印的 HTML」和 app 里不一样

有两条互不相同的管线，**它们的"不一样"是两回事**：

| | 原生：`Cmd+P` / 命令 `workspace:export-pdf` | better-export-pdf：`export-current-file-to-pdf` |
|---|---|---|
| 渲染位置 | **同一个文档**：导出时 `document.body.createDiv("print")`，把笔记渲染进这个 `div.print`，导出完再 `detach()` 掉 | **独立文档**：`<webview src="app://obsidian.md/help.html" class="print-preview-container">`，把 app 的 `head.innerHTML` + `.print` 子树塞进去 ← **仅当插件 `data.json` 的 `version == "1"`**；`version == "2"`（本机现状）没有 webview，而是渲染进 app 文档再用 Obsidian 自己的 `print-to-pdf` IPC 导出，**与原生导出同管线**，详见 `FINDINGS-base-fit-shrink.md` |
| 打印媒体 | 真 `@media print` 生效（走 `printToPDF`） | 在 app 里把所有 `@media print` 规则**剥掉 media 包裹**后 `insertCSS` 进 webview（screen 媒体下也生效） |
| 主题 light/dark | 若 vault 用默认主题，导出期间给 `body` 加 `theme-light`、去 `theme-dark`，结束再还原 | 由插件自己算（含 `theme-light-auto-patch` 逻辑） |
| 其它 UI | `body > :not(.print) { display:none !important }` 把 app 全部隐藏 | 无关（webview 里本来就没有 app UI） |
| 背景 | 取决于 `printToPDF` 的 `printBackground` | 取决于插件设置；**本机 `data.json` 里是 `printBackground: false`** |

app.css（1.6.7）打印段的实际内容：

```css
@media print {
  html, body { padding-top:0 !important; overflow:auto !important; height:auto !important }
  iframe, .titlebar, .app-container, .progress-bar, .popover,
  .markdown-embed-link, .suggestion-container { display:none !important }
  body > :not(.print) { display:none !important }       /* ← 关键：非 .print 全部隐藏 */
  .print .markdown-preview-view { -webkit-print-color-adjust: exact; color: initial }
  .print .markdown-preview-view .metadata-container { display:none }
  .print .markdown-preview-view .markdown-embed-content { max-height:none; overflow:visible }
  .print .markdown-preview-view .callout-content { display:inherit !important }
  .print .external-link { background:none; padding-right:0 }
  * { text-shadow:none !important }
  webview { display:none }
  ::-webkit-scrollbar { display:none }
  body { --font-text: var(--font-print) !important }    /* 打印换字体变量 */
}
```

**两个必须知道的推论（已实测）：**

1. **外部观感差异来自计算样式，不是 HTML 文本。** 同一份 `outerHTML` 在 screen 与 print
   媒体下序列化出来是一模一样的字符串；差别只在 `getComputedStyle`：
   实测同一元素 screen 下 `.print{display:none; width:auto}`，
   print 下 `.print{display:block; width:714px; margin:0 21px}`。
   → 所以"对比打印 HTML 与 app HTML"要用 **computed style 对比**，光 diff 文本会得到 0 差异。
2. **页面上没有 `.print` 元素时，打印出来是完全空白。**
   实测：无 `.print` 的页面 `printToPDF` → 该页像素全部 alpha=0；有 `.print` 的对照页 →
   不透明白底 + 内容色（`#663399`）都在。
   → 这就是为什么原生路径必须靠 `freeze-print.js` 把 `.print` 留下来才能抓，
   也是为什么 better-export-pdf 干脆自己造一份独立文档。

---

## 2. 三条抓取路径（按推荐度）

### 路径 A（推荐，最忠实、无竞态）：抓 better-export-pdf 的 print webview

导出对话框一打开，那份打印文档就已经作为一个**独立调试目标**存在了，且会一直留到你关掉对话框。

```bash
./launch-obsidian-debug.sh                     # 见下：需要 Obsidian 先完全退出
# Obsidian 里：打开一篇笔记 → 命令面板 → "Export current file to PDF"（只打开对话框，不要点导出）
python3 cdp.py targets                         # 确认能看到那个 webview 目标
python3 cdp.py --target webview dump --out captures
# → captures/*.html 就是打印时那份 HTML（独立文档，含复制过来的 head）
python3 cdp.py --target webview pdf --out captures/from-webview.pdf --pagesize A4
```

在对话框里点导出得到的 PDF，与上一步 CDP 导出的 PDF 应当一致；不一致说明插件设置
（scale / marginType / printBackground）在起作用，以对话框那份为准。

### 路径 B：原生路径 + 冻结 `.print`

```bash
# DevTools (Cmd+Opt+I) → Console 粘贴 freeze-print.js
# 然后正常触发 "Export to PDF"
```
导出结束后在 Console 里：

```js
document.querySelector('div.print').outerHTML                                  // 打印 DOM 子树
getComputedStyle(document.querySelector('div.print > .markdown-preview-view')).width
__unfreezePrint()                                                              // 收拾干净
```
再把整份文档交给 harness：

```bash
python3 cdp.py --target app dump --out captures --media print
python3 cdp.py --target app pdf --out captures/native.pdf --pagesize A4 --background
```

### 路径 C：只看计算样式（最轻，适合边改边看）

```bash
python3 cdp.py --target app styles --media screen
python3 cdp.py --target app styles --media print     # 同一批选择器在打印媒体下的值
```
关注项：`.print`、`.print > .markdown-preview-view`、`.markdown-preview-view > div`、
`table`、`.callout`，以及 `--print-zoom` / `--print-page-width` 两个自定义变量。

---

## 3. Agent 侧：怎么抓、怎么测 CSS（全部为实测过的命令）

### 3.1 抓 HTML —— 三条路，推荐 A

**A. better-export-pdf 的 print webview（无竞态，推荐）**

导出对话框一打开，打印文档就已经是**独立的调试目标**（源码里的
`<webview src="app://obsidian.md/help.html" class="print-preview-container">`），
会一直存在到关掉对话框，所以不用抢时机、也不用真的导出：

```bash
./launch-obsidian-debug.sh
# Obsidian 里执行 "Export current file to PDF" 打开对话框（不要点导出）
python3 cdp.py targets                       # 找那个 app://obsidian.md/... 的 webview 目标
python3 cdp.py --target webview dump --out captures        # outerHTML + MHTML
python3 cdp.py --target webview fixture --out tests/print-fixture   # 固化成离线可复跑目录
```

**B. 原生路径 + 冻结 `.print`**：粘 `freeze-print.js` → 导出 → `div.print` 留下来 →
`python3 cdp.py --target app dump --out captures --media print`。

**C. 只要计算样式**：`python3 cdp.py --target app styles --media print`。

### 3.2 把打印文档的 CSS 全貌摊开

```bash
python3 cdp.py --target webview sheets --out captures/sheets
```
输出 = 级联顺序表 + 每张表的字符数 + 规则数，并把原文写到 `captures/sheets/NN-*.css`。
（链接表用 `Page.getResourceContent` 读原文，绕过同源限制。）

### 3.3 诊断"为什么这条规则没生效"

```bash
python3 cdp.py --target webview matched '.print > .markdown-preview-view' --media print
```
实测输出（示例）：

```
[origin=user-agent] @media screen  div                    display:block
[origin=regular   ] @media print   .print > .markdown-preview-view
    color:rebeccapurple; font-size:15px; width:var(--print-page-width)
```
要点：**必须带 `--media print`**，否则 `@media print` 里的规则根本不算"命中"
（上面第一行就是不带 media 时的结果：只剩 UA 规则）。
`origin=injected/user` 的规则来自 `insertCSS`（better-export-pdf 就是这么注入的），
它们**不在** `document.styleSheets` 里，只能用这个命令抠原文（`--out` 存盘）。

### 3.4 CSS A/B：不碰仓库、不重构建地试

```bash
# 追加一张临时样式表（级联优先级最高）
python3 cdp.py --target webview inject --css-text '@media print { .print { width: 500px !important } }'
# 复核实际生效值
python3 cdp.py --target webview styles --media print
# 把第 N 张表的内容整体换掉（内联表直接改文本；链接表停用 + 补一张同内容的 style）
python3 cdp.py --target webview setsheet --index 2 --css /tmp/candidate.css
# 看效果
python3 cdp.py --target webview pdf --out out/ab.pdf --pagesize A4 && python3 cdp.py png out/ab.pdf
```
实测：`inject` 后 `.print` 的 width 由 800px 变 500px；`setsheet --index 2` 后
`.print > .markdown-preview-view` 由 714px 变 660px —— 改完立刻读回验证，闭环成立。
确认无误后再把它写回 `src/` 并 `npm run build`。

### 3.5 离线 fixture：一次抓取、无限次试验

`fixture` 产出的目录：

```
tests/print-fixture/
├── print.html        # 打印文档的原始序列化（保真，但依赖 app:// 资源）
├── fixture.html      # 扁平化：全部样式表按级联顺序内联，不再依赖 app://
├── sheets/NN-*.css   # 每张样式表原文（级联顺序）
└── manifest.json     # 来源 URL、body class、尺寸、样式表清单、打印参数
```
之后 CSS 试验可以在任何 Chromium/Chrome 里跑，不必开 Obsidian：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --remote-debugging-port=9337 "--remote-allow-origins=*" --user-data-dir=/tmp/ph-prof \
  file://$PWD/tests/print-fixture/fixture.html &
python3 cdp.py --port 9337 --target app styles --media print
```

**保真度实测（同一页面：线上文档 vs 离线 fixture）**
- computed style：`.print` 与 `.print > .markdown-preview-view` 的 width/margin/padding
  **逐字段相同**（500px / 660px / margin 0 128px）。
- PDF 文本层：`pdftotext` 输出**完全一致**。
- 像素：全页 911×1287，差异像素 5672（0.48%），全部落在文字块包围盒
  `201x138+187+52` 内，且只是字形抗锯齿（核心色 `#663399` 1459 vs 1436 px）；
  布局、背景、颜色无差异。
- 结论：**fixture 可用于级联/布局/结构的断言；像素回归要把阈值设成容忍抗锯齿噪声**
  （建议按内容区域比，或 `RMSE_norm < 0.05` 视为"无变化"）。最终定稿的观感判断仍用真实
  Obsidian 导出的 PDF。

## 4. 视觉回归（让"能不能看"这件事可自动化）

```bash
python3 cdp.py --target app pdf --out out/baseline.pdf --pagesize A4   # 改 CSS 前
npm run build && python3 cdp.py --target app pdf --out out/after.pdf   # 改 CSS 后
python3 cdp.py png out/baseline.pdf --dpi 110                          # → out/baseline.pages/page-1.png
python3 cdp.py png out/after.pdf    --dpi 110
python3 cdp.py pxdiff out/baseline.pages/page-1.png out/after.pages/page-1.png --out out/diff.png
# RMSE 0 表示像素级无变化；非 0 时打开 diff.png 看红区在哪
```
PNG 也是给"能看图的 agent"用的输入——把 page-*.png 丢进对话，让 agent 判断分页、
页边距、callout 背景是否是对的，而不是靠 CSS 逻辑猜。

---

## 4. 命令与预期输出

```bash
curl -s http://127.0.0.1:9222/json/version
```
预期：JSON，含 `"webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/..."`。
拿不到就是调试端口没生效（必须先退出 Obsidian 再带参数启动）。

```bash
python3 cdp.py targets
```
预期：逐行列出 `page / webview / iframe` 目标及其 ws 地址；
主界面是 `app://obsidian.md/index.html`，导出对话框的打印文档是另一个 `app://obsidian.md/...`。

```bash
python3 cdp.py --target app dump --out captures --media print
```
预期：
```
[html] captures/<title>.printmedia.html  (N chars)  <- app://obsidian.md/index.html
[meta] {"body":"theme-dark ...","html":"","print":true,"media_print":true,"inner":[1512,966]}
[mhtml] captures/<title>.printmedia.mhtml
```
`"print":true` 表示 `.print` 元素在 DOM 里；`media_print` 是媒体仿真的回读校验。

```bash
python3 cdp.py --target app pdf --out out/after.pdf --pagesize A4
```
预期：`[pdf] out/after.pdf <- app://obsidian.md/index.html  (NNNN bytes)`；
再用 `pdfinfo` 核对 `Page size: 595.92 x 841.92 pts (A4)`（= 210×297mm）。

---

## 5. 依赖

- Python 3 + `websocket-client`（`pip install websocket-client`）
- `poppler`（`pdftoppm` / `pdfinfo`）、`imagemagick`（`magick`）
- Obsidian 必须带 `--remote-debugging-port=<PORT>` 启动

## 7. 已知坑

- **`Origin` 头导致 403**：新版 `websocket-client` 会带 `Origin`，Electron 直接拒接
  （`Rejected an incoming WebSocket connection … --remote-allow-origins`）。
  本节脚本 `suppress_origin=True` 绕过；也可以给 Obsidian 加 `--remote-allow-origins=*` 启动。
- **插件 v2 没有 webview**：`data.json` 的 `version == "2"` 时，`insertCSS`/剥壳重放那条路不跑，
  文档渲染在 app 文档里，导出走 Obsidian 自己的 `print-to-pdf` IPC ⇒ 与原生导出同管线、逐页一致。
- **插件会累积多份 `.print` 副本**（屏幕 `display:none`，无感）：挑错副本会导致"插进去的标尺根本没印出来"。
  先 `document.querySelectorAll('.print').forEach(e => e.remove())` 再开弹窗（`export-probe.py` 已内置）。
- **CDP 媒体仿真量不到整页缩放**：`Emulation.setEmulatedMedia(print)` 只能验证布局宽度；
  判 fit-shrink 必须真导出 PDF 量像素（`measure-bands.py`）。
- **整页 fit-shrink 的触发判定发生在非打印媒体的布局里**：同一组限宽规则写在 `@media print` 内**无效**，
  媒体无关才有效（见 `FINDINGS-base-fit-shrink.md` §5）。
- **`printBackground: false` 时 CSS 背景不打印**：标尺/色块要用 `border` 或图片。
- **调试端口只在启动时生效**：必须完全退出 Obsidian 再 `open -na ... --args --remote-debugging-port=9222`。
- **`Emulation.setEmulatedMedia` 是 per-session 的**：设完媒体仿真后必须在**同一个连接**里抓取，
  断开连接就失效。所以 `dump` / `styles` / `matched` 都有 `--media` 参数在同连接内完成。
- **原生 `.print` 是短命的**（导出后立刻 `detach()`），不冻结就抓不到。
- **CDP 不推 `CSS.styleSheetAdded`**（Chromium 153 实测 0 条事件）：样式表枚举改用
  JS 读 `document.styleSheets`；链接表原文用 `Page.getResourceContent`，不要指望 `sheet.cssRules`
  （`file://` 下是 `SecurityError`；Obsidian 的 `app://` 同源才可读）。
- **`insertCSS` / 浏览器注入的样式表不在 `document.styleSheets` 里**，只能从
  `matched --media print` 的 `origin=injected/user` 规则反查。
- **`@media print` 里的规则在 screen 媒体下"不命中"**：诊断时必须 `--media print`，
  否则会得到"规则不存在"的错误结论。
- **`printBackground: false`**（本机 better-export-pdf 的 `data.json`）会让 callout 背景色不出现，
  与主题预期不符时先查这一项。
- **`scale` 设置会改变 PDF 几何**：本机 `data.json` 的 `prevConfig.scale` 是 90，
  用对话框导出时以对话框里的值为准；CDP 直接 `pdf` 默认是 100。
- **打印时字体变量被改写**：`body { --font-text: var(--font-print) !important }`，
  若主题改了 `--font-print` 或依赖 `--font-text`，打印结果会与屏幕不同。


## 8. 命令速查

| 目的 | 命令 |
|---|---|
| 真导出 + 插标尺（定位版式问题首选） | `python3 export-probe.py --file <note> --out /tmp/a.pdf` |
| 量 PDF 页面条带（判整页缩放/裁切） | `python3 measure-bands.py /tmp/a.pdf --pages 1 --expect "<文字>"` |
| 列出调试目标 | `python3 cdp.py targets` |
| 抓打印 HTML（推荐） | `python3 cdp.py --target webview dump --out captures` |
| 抓 app HTML | `python3 cdp.py --target app dump --out captures` |
| 摊开全部样式表 | `python3 cdp.py --target webview sheets --out captures/sheets` |
| 诊断规则命中 | `python3 cdp.py --target webview matched '<选择器>' --media print` |
| 临时注入 CSS | `python3 cdp.py --target webview inject --css-text '<css>'` |
| 替换第 N 张表 | `python3 cdp.py --target webview setsheet --index N --css candidate.css` |
| 固化离线 fixture | `python3 cdp.py --target webview fixture --out tests/print-fixture` |
| 导出 PDF | `python3 cdp.py --target webview pdf --out out.pdf --pagesize A4 --background` |
| PDF→PNG | `python3 cdp.py png out.pdf --dpi 110` |
| 像素对比 | `python3 cdp.py pxdiff a.png b.png --out diff.png` |
| 结构对比 | `python3 cdp.py diff print.html app.html` |
| 计算样式对比 | `python3 cdp.py styles --media screen` / `--media print` |
