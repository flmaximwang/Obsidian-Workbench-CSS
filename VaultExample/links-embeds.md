---
tags:
  - test
  - links
  - embeds
date: 2026-07-07
---

# 🔗 Links & Embeds — 链接与嵌入

> **测试目标**: 验证 Wiki 链接、外部链接、嵌入、标签、Backlinks 的渲染

---

## Wiki 链接

### 指向已有笔记

- [[index]] — 指向 vault 索引
- [[page-layout-a4]] — 指向 A4 布局测试
- [[typography]] — 指向排版测试

### 指向不存在的笔记

- [[not-yet-created]] — 未创建的笔记（显示为红色/虚线链接）
- [[missing-page-test]] — 另一个缺失链接

### 带显示文本的链接

- [[index|返回首页]]
- [[callout-grid|网格布局说明]]
- [[page-layout-wide|宽屏布局]]

## 外部链接

- [Obsidian 官网](https://obsidian.md)
- [Obsidian Workbench CSS 仓库](https://github.com/your-username/Obsidian-Workbench-CSS)
- [Style Settings 插件](https://github.com/mgmeyers/obsidian-style-settings)

其他协议链接：
- `file:///Users/maxim/Documents/note.md`
- `mailto:user@example.com`

## 嵌入

### 嵌入另一篇笔记

```markdown
![[typography]]
```

嵌入整篇笔记的内容。嵌入块应该有特殊的边框或背景样式。

### 嵌入标题区块

```markdown
![[typography#引用块]]
```

只嵌入特定标题下的内容。

### 嵌入块引用

```markdown
![[typography#^block-id]]
```

嵌入指定块 ID 的内容。

## 标签

以下标签用于测试标签渲染样式：

- `#test` 
- `#test/layout`
- `#test/callout/float`
- `#test/typography`
- `#test/table`
- `#status/in-progress`

## 标签列表

#tag1 #tag2 #tag3 #test/embedded-tags

## Backlinks

Obsidian 在面板中显示 backlinks。此页面的 backlinks 会显示哪些笔记链接到此处。

## 未解析链接

[[未创建的笔记/子路径]] — 深层路径缺失链接

> [!tip] 链接样式说明
> - **已解析链接**: 蓝色/主题色，加粗
> - **未解析链接**: 红色/灰色虚线
> - **外部链接**: 带外部链接图标
> - **嵌入内容**: 使用特殊嵌入块样式，区别于正文
