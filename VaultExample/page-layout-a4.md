---
cssclasses:
  - a4-page
tags:
  - test
  - layout
  - a4
date: 2026-07-07
---

# 📐 A4 Page Layout

> **测试目标**: 验证 `a4-page` cssclass — 内容宽度限制为 714px（A4 兼容宽度）

---

## 正常段落流

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla facilisi. Vivamus lacinia odio vitae vestibulum vestibulum. Cras venenatis euismod malesuada. Suspendisse potenti. Phasellus volutpat neque in augue ullamcorper, eget tristique velit aliquam.

Maecenas sed diam eget risus varius blandit sit amet non magna. Donec ullamcorper nulla non metus auctor fringilla. Nullam quis risus eget urna mollis ornare vel eu leo. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.

## 多级标题结构

### H3 — 第三级

Vestibulum id ligula porta felis euismod semper. Aenean eu leo quam. Pellentesque ornare sem lacinia quam venenatis vestibulum. Donec sed odio dui.

#### H4 — 第四级

Praesent commodo cursus magna, vel scelerisque nisl consectetur et. Etiam porta sem malesuada magna mollis euismod.

##### H5 — 第五级

Morbi leo risus, porta ac consectetur ac, vestibulum at eros. Nullam id dolor id nibh ultricies vehicula ut id elit.

## 长段落（验证换行）

Donec sed odio dui. Cras mattis consectetur purus sit amet fermentum. Donec id elit non mi porta gravida at eget metus. Nullam id dolor id nibh ultricies vehicula ut id elit. Maecenas faucibus mollis interdum. Donec ullamcorper nulla non metus auctor fringilla. Nullam quis risus eget urna mollis ornare vel eu leo. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed posuere consectetur est at lobortis. Vivamus sagittis lacus vel augue laoreet rutrum faucibus dolor auctor. Aenean lacinia bibendum nulla sed consectetur. Nullam id dolor id nibh ultricies vehicula ut id elit. Curabitur blandit tempus porttitor. Cras justo odio, dapibus ut facilisis in, egestas eget quam.

## 水平线

---

## 内联元素

这是 **粗体**、*斜体*、***粗斜体***、~~删除线~~、`行内代码`、<u>下划线</u>、^上标^、~下标~ 和 ==高亮==。

>  这是一个普通引用块，用于验证在 A4 宽度下的引用渲染效果。引用块应当有左侧竖线标识。

## 无序列表

- 列表项一 — 短文本
- 列表项二 — 中等长度的文本，用来测试列表项的换行和缩进对齐效果
- 列表项三
  - 嵌套子项 A
  - 嵌套子项 B
    - 深层嵌套 i
    - 深层嵌套 ii
- 列表项四 — 长文本。Donec sed odio dui. Cras mattis consectetur purus sit amet fermentum. Donec id elit non mi porta gravida at eget metus.

## 有序列表

1. 第一步
2. 第二步
3. 第三步
   1. 子步骤 a
   2. 子步骤 b
4. 第四步 — 长文本。Vestibulum id ligula porta felis euismod semper. Aenean eu leo quam.

## 任务列表

- [x] 已完成任务
- [ ] 未完成任务
- [ ] 待处理任务
  - [x] 子任务已完
  - [ ] 子任务待做

## 代码块

```python
def hello_world():
    """A4 页面中的代码块渲染测试"""
    name = "Obsidian Workbench"
    print(f"Hello, {name}!")
    return [i ** 2 for i in range(10)]


class A4Test:
    pass
```

## 表格

| 左对齐 | 居中对齐 | 右对齐 |
|:-------|:--------:|-------:|
| A4 测试 | 714px   | 有效 |
| 短文本  | 中文本   | 长文本实验 |
| 再一行  | 居中对   | 齐测试 |

---

## 分页测试（打印用）

### 第一页内容

A4 打印时应当在此处分页。在此之前的内容应位于第一页。

---

### 第二页内容

此段文字应当在打印时出现在第二页。注意阅读视图中的滚动连续性。
