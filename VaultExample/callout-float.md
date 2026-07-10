---
tags:
  - test
  - callout
  - float
date: 2026-07-07
---

# 🧭 Callout Float — 浮动与文字环绕

> **测试目标**: 验证 `[!float|left]` 和 `[!float|right]` 的浮动定位与文字环绕效果

---

## 左浮动

> [!float|left]
> #### 左浮动卡片
> **位置**: 左侧浮动
> **宽度**: 自适应
> 这是 `float left` 的测试内容。

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus lacinia odio vitae vestibulum vestibulum. Cras venenatis euismod malesuada. Suspendisse potenti. Phasellus volutpat neque in augue ullamcorper, eget tristique velit aliquam. Maecenas sed diam eget risus varius blandit sit amet non magna.

Donec ullamcorper nulla non metus auctor fringilla. Nullam quis risus eget urna mollis ornare vel eu leo. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec sed odio dui. Vivamus sagittis lacus vel augue laoreet rutrum faucibus dolor auctor.

## 右浮动

> [!float|right]
> #### 右浮动卡片
> **位置**: 右侧浮动
> 文字环绕在左侧。用于侧边注释、配图说明、关键数据等。

Maecenas faucibus mollis interdum. Cras mattis consectetur purus sit amet fermentum. Donec id elit non mi porta gravida at eget metus. Nullam id dolor id nibh ultricies vehicula ut id elit. Aenean lacinia bibendum nulla sed consectetur. Etiam porta sem malesuada magna mollis euismod.

Praesent commodo cursus magna, vel scelerisque nisl consectetur et. Sed posuere consectetur est at lobortis. Vestibulum id ligula porta felis euismod semper. Nullam quis risus eget urna mollis ornare vel eu leo.

## 多浮动混合

> [!float|left]
> **左 A** — 第一个浮动元素

> [!float|left]
> **左 B** — 第二个浮动元素

> [!float|right]
> **右 A** — 右侧浮动

Floats 可以多个共存。这段文字应当环绕在以上三个浮动元素之间。浮动元素不占据文档流高度，后续段落正常排列。

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## 浮动中的富内容

> [!float|right]
> ```python
> # 浮动内容的代码块
> def float_test():
>     return "floating right"
> ```
> *代码块在浮动 callout 内*

A float callout can contain code blocks, lists, images, and even nested callouts. Heavy content inside a float will affect the float's height and positioning.

- Float 内的列表项 A
- Float 内的列表项 B

## 浮动中的 callout 嵌套

> [!float|left]
> > [!note] 嵌套 Callout
> > 浮动内部再嵌套一个标准 callout
>
> 浮动 callout 支持嵌套，用于创建复杂的布局结构。

这段文字环绕在包含嵌套 callout 的浮动元素周围。Obsidian-Workbench-CSS 的浮动系统支持多级嵌套。

> [!warning] 浮动注意事项
> - 浮动 callout **不**影响兄弟元素宽度，仅内容环绕
> - 多个浮动可能堆叠（取决于可用宽度）
> - 浮动内部不建议放非常大的内容块
> - `[!float]` 不支持 `[!grid]` 的组合（两者互斥）
