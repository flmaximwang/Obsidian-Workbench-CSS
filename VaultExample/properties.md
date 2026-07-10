---
title: "Properties Test"
aliases:
  - "属性测试"
  - "Frontmatter 测试"
tags:
  - test
  - properties
  - frontmatter
date: 2026-07-07
cssclasses:
  - wide
number: 42
rating: 4.5
status: active
coordinates:
  lat: 31.2304
  lng: 121.4737
references:
  - "Obsidian CSS Variables"
  - "Theme Design Guide"
favorite: true
empty_field:
---

# 🏷️ Properties — YAML 前注渲染

> **测试目标**: 验证 YAML frontmatter（属性面板）的渲染样式 —— 不同类型字段的显示

---

## 本页属性字段一览

| 字段名 | 类型 | 值 |
|:-------|:----|:---|
| `title` | 文本 | "Properties Test" |
| `aliases` | 列表 | 属性测试, Frontmatter 测试 |
| `tags` | 列表 | test, properties, frontmatter |
| `date` | 日期 | 2026-07-07 |
| `cssclasses` | 列表 | wide |
| `number` | 数字 | 42 |
| `rating` | 浮点数 | 4.5 |
| `status` | 文本 | active |
| `coordinates` | 对象 | lat: 31.23, lng: 121.47 |
| `references` | 列表 | "Obsidian CSS Variables", "Theme Design Guide" |
| `favorite` | 布尔 | true |
| `empty_field` | 空 | (无值) |

## 属性面板渲染检查项

- [x] 文本字段正确展示
- [ ] 标签/列表以 chip 形式展示
- [ ] 日期格式正确
- [ ] 数字/浮点数对齐
- [ ] 布尔值以开关形式展示
- [ ] 空字段占位
- [ ] 嵌套对象展开

> [!note] 属性面板位置
> 在 Obsidian 1.10+ 中，YAML frontmatter 默认在编辑模式下显示为属性面板（properties view），而非原始 YAML。Workbench CSS 主题对属性面板有专门的样式覆盖，其 CSS 位于 `src/desktop/note/property.css`。
