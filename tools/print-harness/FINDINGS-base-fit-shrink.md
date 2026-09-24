# 定位记录：含 Base 的笔记导出 PDF 时整页被缩小（"页面变宽"）

> 本文是 2026-09 一次真实排查的完整记录，目的：下次遇到"导出 PDF 版式不对"能在几分钟内收敛，
> 而不是重新花掉几十万 token。**先说结论**，再给量法与证据，最后列出走过的弯路（避免重复）。

## 1. 现象与用户可见效果

笔记 `Logs/2026/09/07/SEC-001/SEC-001.md`（末尾有 `![[%Logs2Protocols%.base]]`）用
**better-export-pdf** 导出时，A4 页面上**所有内容等比缩小到约 2/3**：文字、图片、页边距外的留白
一起变化 ⇒ 看起来就是"页面比内容宽了 1.5 倍"。同一 vault 里不含 Base 的笔记（如
`Logs/2026/09/08/Purification-005/Purification-005.md`）完全正常。

关键：**只有页码/内容密度变了，纸张尺寸没变**（始终 A4 = 595.92 × 842.88 pt）。

## 2. 结论

- **触发器：文档里的 Base 视图（`![[xxx.base]]`）**。它让 Chromium 打印管线的
  fit-to-page 对**整页**做缩放（实测系数 ≈ 0.667）。
- 删掉 Base、或给 Base 限宽，缩放立即消失；插入一根 2000px 宽的普通元素**不会**触发
  （Chromium 只把它裁切在可打印边缘）⇒ 不是"任何超宽元素都会触发"。
- 修法（已进主题，实测有效）：`src/desktop/note/page/print/main.css` 里那组
  `.print .bases-*` 规则；**必须是媒体无关规则，包进 `@media print` 就无效**（见 §5）。
- 与插件无关：better-export-pdf v2 与 `Cmd+P`/`workspace:export-pdf` **走同一条管线**
  （见 §6），两者同时中招、也同时被修好。

## 3. 量法（可复制）

### 3.1 为什么必须"真导出 + 量像素"

- CDP 的 `Emulation.setEmulatedMedia(print)` **只能验证布局宽度**（例如 `.print` 是否 = `var(--print-page-width)`）；
  它用的是**屏幕视口**，量不出 fit-to-page 的整页缩放。判整页缩放必须真导出 PDF 再量。
- `printBackground: false`（本机 better-export-pdf 默认）⇒ **CSS 背景不打印**，只有边框、图片、文字会印。
  所以标尺要用 `border`，不能用 `background`。

### 3.2 标尺

插进待打印文档顶部（`margin:0` 抵消主题的 `margin-left/right:auto`，inline `width` 胜过主题的 `width:var(--print-page-width)`）：

```html
<div style="width:714px; height:0; border-top:40px solid #000; margin:0"></div>
<div style="width:400px; height:0; border-top:20px solid #000; margin:0"></div>
<div style="width:100px; height:0; border-top:20px solid #000; margin:0"></div>
```

三根条会连成一个 **80px 高**的块；`scale 0.9` + 默认页边距下：

| 观察值 | 含义 |
|---|---|
| 首块 **h=54pt, w=482pt** | 正常（0.675 pt/px = 0.75 × 0.9） |
| 首块 **h=36pt, w=321pt** | **整页被 fit 缩小**（×0.667） |

### 3.3 命令

```bash
cd tools/print-harness
# 打开 Obsidian 调试端口（必须先完全退出 Obsidian）
./launch-obsidian-debug.sh        # 注意：本机还需要 --remote-allow-origins=*，见 §7

# 真导出（可插标尺 / 删元素 / 注入候选 CSS）
python3 export-probe.py --file Logs/2026/09/07/SEC-001/SEC-001.md --out /tmp/a.pdf
python3 export-probe.py --file <note> --drop .bases-embed          --out /tmp/b.pdf
python3 export-probe.py --file <note> --css-file /tmp/candidate.css --out /tmp/c.pdf

# 量像素（72dpi ⇒ 1px == 1pt）
python3 measure-bands.py /tmp/a.pdf --pages 1 --expect "名称,摘要"
```

## 4. 决定性数据（SEC-001，scale 0.9 + 默认页边距，标尺 714px 条）

| 导出对象 | 标尺印成 | 换算 | 页数 |
|---|---|---|---|
| 原样（含 Base） | 321pt | 0.45 pt/px ⇒ **整页 ×0.667** | 17 |
| 删 `.bases-embed` | **482pt** | 0.675 pt/px ✓ | 24 |
| 删宽表格（`div:has(> table)`） | 321pt | 仍缩放 ⇒ 不是表格 | 16 |
| 插 2000px 宽元素（Base 已删） | 482pt | ✓（超宽部分被裁在可打印边缘） | 24 |
| 给 `.bases-embed` 限宽（媒体无关） | **482pt** | ✓ | 25 |
| Purification-005（无 Base） | 482pt | ✓ | — |

其它旁证：

- `pdfimages -list` 显示图片放置尺寸随缩放一起变（x-ppi 652 → 569 等），说明是**整页等比缩放**而非局部。
- 同机 **Google Chrome headless** 打印同一段标尺 HTML：714px → 535pt（0.75 pt/px，标准）；
  加 `--force-device-scale-factor=2` 结果不变 ⇒ 不是显示器/系统层面的问题。
- Base 的表格在**屏幕视口**下的宽度跟着视口走（2560px 视口 → `.bases-table` 2559px），
  其 `width:min-content` 克隆 ≈ 792px；`.bases-table-container` 自带 `overflow-x:auto`。

## 5. 修法与"必须媒体无关"这个坑

`src/desktop/note/page/print/main.css`：

```css
.print .bases-embed,
.print .bases-view { max-width: var(--print-page-width); overflow: hidden; }
.print .bases-table-container { overflow-x: hidden; }
.print .bases-td,
.print .bases-table-header { min-width: 0; white-space: normal; overflow-wrap: anywhere; }
```

**这组规则不能包进 `@media print`** —— 实测对比（同一文档、同一导出选项、同一会话）：

| 变体 | 规则位置 | 结果 |
|---|---|---|
| fixA | `@media print { max-width + overflow:hidden }` | 仍缩放（321pt / 17 页）✗ |
| fixB | `@media print { 表格/行/格 width:100%、min-width:0、换行 }` | 仍缩放 ✗ |
| fixD | `@media print { … !important }` | 仍缩放 ✗ |
| fixE | `@media print { .bases-embed{display:none!important} }` | 正常（但 Base 不进 PDF） |
| **fixC** | **媒体无关**（同一组 max-width + overflow） | **482pt / 25 页 ✓** |
| **fixF** | **媒体无关** + 表格/单元格收缩换行 | **482pt / 25 页 ✓，且 Base 列头在文本层齐全（无裁列）** |

⇒ fit-to-page 的判定发生在**非打印媒体**的布局里；只在 print 媒体里改尺寸可能完全不生效。
最终采用 fixF 的规则集（更保险：显式允许单元格换行，不依赖裁切）。

## 6. 与插件的关系（顺带纠正两处旧认识）

- better-export-pdf `data.json` 里 `version: "2"` 时**没有 webview**：文档渲染进 app 文档
  （`document.body.createDiv('print theme-light')` + 弹窗 `.print-preview-item` 里一份），
  导出走 Obsidian 自己的 `ipcRenderer.send('print-to-pdf')` ⇒ 主进程 `sender.printToPDF(options)`。
  `insertCSS` + `@media print` 剥壳重放那套（`AGENTS.md` 旧描述）只在 `version: "1"` 时生效。
- 因此**插件导出与原生导出逐页一致**（实测 17 页 A4、逐页墨迹框相同）。判断"是不是插件搞的鬼"
  时不要用"插件 vs 原生"二分，要用像素对照。
- 插件每次开弹窗都会在 body 下多留一份 `.print` 副本（屏幕 `display:none`，无感），
  排查时会干扰"给打印文档插标尺"，先清掉它们最省事（`export-probe.py` 已内置清理）。

## 7. 环境坑

- `launch-obsidian-debug.sh` 未带 `--remote-allow-origins=*`，新版 `websocket-client` 会带 `Origin` 头，
  WebSocket 握手直接 403。规避：建连接时 `suppress_origin=True`（`cdp.py`/`export-probe.py` 已做），
  或给 Obsidian 加该启动参数。
- 插标尺前先确认"哪一份 `.print` 会被打印"：body 级、有 `.markdown-preview-view`、`offsetHeight` 较大的那份；
  插到别的副本上量不到任何东西。
- `pdftoppm -gray` 输出的 PGM 可以用纯 Python 解析（`measure-bands.py` 就是这么做的，免 PIL）。

## 8. 走过的弯路（别再重复）

- ❌ 先入为主地把它当成"这台机器打印管线的 px→pt 常数是 0.5"（= 144 px/inch）。这个"常数"
  其实是**整页 ×0.667 缩放**的表象：0.75 × 0.9 × 0.667 ≈ 0.45。判据：**连插进去的标尺都等比变小** ⇒
  去查整页 fit-shrink（超宽内容/Base），而不是去改主题的宽度计算。
- ❌ 只看对话框预览就下结论：预览在 **screen 媒体**下渲染，既不走 fit-shrink，
  也不套 `@media print` 宽度规则，所以"预览里的页面宽度"和导出的 PDF 可以差 1.5 倍。
- ❌ 用 CDP 媒体仿真替代真导出：仿真给的布局宽度可以是对的，但仍然量不到整页缩放。
