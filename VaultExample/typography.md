---
tags:
  - test
  - typography
  - headings
date: 2026-07-07
---

# ✒️ Typography — 排版体系

> **测试目标**: 验证 H1–H6 标题渐变下划线、正文排版、引用、代码块、列表的视觉渲染

---

# H1 — 一级标题（带渐变下划线）

一段跟随在一级标题之后的正文。H1 应当有显眼的渐变下划线（从左到右渐变为透明）。

## H2 — 二级标题

### H3 — 三级标题

#### H4 — 四级标题

##### H5 — 五级标题

###### H6 — 六级标题

---

## 引用块

> 单层引用块 — 这是一段示例文本，用于验证引用块的左边框样式。
> 
> 引用续行。

> 多段引用
> 
> > 嵌套引用 — 外层引用内部再嵌套一层。
> > 
> > > 三层嵌套引用测试。

## 代码块

### 无语法高亮

```
这是纯文本代码块（无语法高亮）。
```

### Python

```python
from typing import Optional


class TypographyTest:
    """测试排版系统的代码块样式"""

    def __init__(self, name: str, level: int = 1):
        self.name = name
        self.level = level

    def render(self) -> str:
        return f"<h{self.level}>{self.name}</h{self.level}>"


# 实例化并调用
test = TypographyTest("Heading Test", 2)
output = test.render()
print(output)
```

### JavaScript

```javascript
/**
 * 排版测试 - JavaScript 版本
 */
const typography = {
  headingLevels: [1, 2, 3, 4, 5, 6],
  hasGradientUnderline: true,
  fontFamily: "'iA Writer Quattro', 'Source Han Serif SC', serif"
};

for (const level of typography.headingLevels) {
  console.log(`Testing H${level}`);
}
```

### CSS

```css
/* 标题渐变下划线 */
h1, h2 {
  border-bottom: 2px solid;
  border-image: linear-gradient(
    to right,
    var(--color-accent),
    transparent
  ) 1;
}
```

### 行内代码

使用 `print()` 函数输出。变量 `$name` 应当被渲染为行内代码样式。路径 `/etc/config/obsidian.css` 也是行内代码。快捷键 `Ctrl+P`。

## 数学公式（LaTeX）

行内公式: $E = mc^2$

块级公式:

$$
\int_{-\infty}^{\infty} e^{-x^2} \, dx = \sqrt{\pi}
$$

$$
\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}
$$

## 水平分割线

---

以上应有一条跨度的分割线。

多段文字之间

***

带星号的

---

和短横线分割线。

## 注释 / 脚注

这是一段带脚注的文字[^1]。

[^1]: 这是脚注内容——通常出现在页面底部。

## 高亮与标记

==高亮文本== 用于强调。

混合使用 **粗体**、*斜体*、***粗斜体***、~~删除线~~、<u>下划线</u> 和 `行内代码`。

## Emoji

🎯 🚀 ✅ ❌ ⚠️ 🔧 📝 📋 🧪 🎨 🔥 💡

## 对齐测试

左对齐是默认方式。

> 右对齐引用块（测试引用对齐）。

## 清单

- [x] 排版测试用例完成
- [ ] 添加更多内联样式测试
- [ ] 验证中文排版效果
