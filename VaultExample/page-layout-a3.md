---
cssclasses:
  - a3-page
tags:
  - test
  - layout
  - a3
date: 2026-07-07
---

# 📏 A3 Page Layout

> **测试目标**: 验证 `a3-page` cssclass — 内容宽度扩展至 72.8rem（A3 宽幅）

---

## 宽幅内容测试

A3 页面布局适合需要更宽内容区域的场景，比如大表格、宽代码块、并排展示等。

下面是一个宽段落的渲染测试：

Vestibulum id ligula porta felis euismod semper. Aenean eu leo quam. Pellentesque ornare sem lacinia quam venenatis vestibulum. Donec sed odio dui. Maecenas faucibus mollis interdum. Donec ullamcorper nulla non metus auctor fringilla. Nullam quis risus eget urna mollis ornare vel eu leo. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Vivamus sagittis lacus vel augue laoreet rutrum faucibus dolor auctor. Cras justo odio, dapibus ut facilisis in, egestas eget quam.

## 宽表格（A3 优势场景）

下表列数较多，在 A4 宽度下会溢出，在 A3 宽度下应当正常显示：

| 特性               | A4 (714px) | A3 (72.8rem) | wide (100%) | 描述                           |
|:------------------|:----------:|:------------:|:-----------:|:-------------------------------|
| 内容宽度           | 714px      | 72.8rem      | 视口全宽    | 可用宽度                     |
| 适合打印           | ✅         | ✅           | ❌          | 标准纸张兼容性               |
| 宽代码块           | ⚠️ 溢出    | ✅           | ✅          | 无需水平滚动                 |
| 多栏 callout 网格  | 2-3 列     | 3-4 列       | 4-6 列      | 列数随宽度增加               |
| 大表格             | ⚠️ 滚动    | ✅           | ✅          | 宽列数表格展示               |
| 并排双图           | 两图并排   | 图可更大     | 最大        | 图片宽度自由度               |
| 阅读长行文本       | 良好       | 较宽（需注意）| 过宽        | 行长 (measure) 对可读性影响  |

## 宽代码块

```javascript
// A3 宽度下，长代码行无需换行或水平滚动
const features = {
  a4:  { width: '714px',  columns: '2-3', scroll: true  },
  a3:  { width: '72.8rem', columns: '3-4', scroll: false },
  wide: { width: '100%',   columns: '4-6', scroll: false }
};

function getLayout(type) {
  if (features[type]) {
    return `Current layout: ${type}, width=${features[type].width}`;
  }
  throw new Error(`Unknown layout type: ${type}`);
}

console.log(getLayout('a3'));
// 这一行很长，用于测试代码块在宽幅布局下是否水平溢出
// "A3 page layout provides 72.8rem content width — enough for most technical content without horizontal scrolling"
```

## 并排引用

> A3 布局受益者：技术文档作者，需要同时展示代码和说明。

> 适合场景：宽语言示例、架构图说明、API 文档对照表。

## 大段文本可读性测试

虽然 A3 提供了更多空间，但过宽的行长（measure）可能降低阅读性。理想行长约为 50-75 字符。下面这段文字用于检查 A3 下是否过宽：

在设计响应式宽度时，需要在"容纳更多内容"和"保持可读性"之间取得平衡。根据排版学（Typography）的传统法则，单列文本的最佳行长为 45-75 个字符（包括空格）。过短的行导致眼球频繁换行，过长则使读者难以定位到下一行的起始位置。A3 页面布局虽然提供了更宽的内容区域，但如果文本内容占满全部宽度，对于大段正文来说可能会降低阅读体验。因此 A3 更适合包含大量表格、代码、图表等非纯文本内容的文档，而非长文阅读。

---

## 多语言内容

**English**: The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.

**中文**: 用 Obsidian Workbench CSS 主题在 A3 页面布局下测试中文排版效果。自适应宽度对于中英文混排的场景尤为重要。

**日本語**: 日本語のテキストが A3 ページレイアウトでどのように表示されるかをテストします。

**混合**: A3 布局适用于含大量 `代码`、**粗体**、*斜体*、以及 ==高亮== 的混合内容。
