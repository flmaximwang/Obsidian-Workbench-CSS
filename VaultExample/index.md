---
cssclasses:
  - wide
tags:
  - vault-index
  - test-suite
date: 2026-07-07
---

# 🏗️ Obsidian Workbench CSS — 测试用例仓库

> 本文档为 Obsidian-Workbench-CSS 主题的**测试索引**。每个文件中含有不同主题特性的测试场景，用于验证和调试主题的渲染效果。

---

## 目录

### 1. 页面布局 Page Layout
| 文件 | cssclasses | 测试内容 |
|------|-----------|---------|
| [[page-layout-a4]] | `a4-page` | A4 页面宽度 (714px)，分栏布局 |
| [[page-layout-a3]] | `a3-page` | A3 页面宽度 (72.8rem)，宽幅内容 |
| [[page-layout-wide]] | `wide` | 全宽布局，无内容宽度限制 |

### 2. Callout 系统 Callouts
| 文件 | 测试内容 |
|------|---------|
| [[callout-float]] | `[!float]` 浮动 + 文字环绕 |
| [[callout-grid]] | `[!grid]` 多列网格布局 |
| [[callout-card]] | `[!card]` 卡片式 callout |
| [[callout-timeline]] | `[!timeline]` 时间线布局 |
| [[callout-absolute]] | `[!absolute]` 绝对定位布局 |
| [[callout-blank]] | `[!blank]` 不可见容器 |

### 3. 排版体系 Typography
| 文件 | 测试内容 |
|------|---------|
| [[typography]] | 标题渐变下划线、列表、引用、代码块 |

### 4. 媒体 & 表格
| 文件 | 测试内容 |
|------|---------|
| [[media]] | 图片、视频嵌入响应式 |
| [[tables]] | 标准表、合并单元格、对齐方式 |

### 5. 链接 & 嵌入
| 文件 | 测试内容 |
|------|---------|
| [[links-embeds]] | Wiki 链接、嵌入、标签嵌套 |

### 6. 属性元数据
| 文件 | 测试内容 |
|------|---------|
| [[properties]] | YAML frontmatter 渲染（多类型字段） |

### 7. 打印 & 混合
| 文件 | 测试内容 |
|------|---------|
| [[print-test]] | 阅读视图 → PDF 打印渲染测试 |
| [[mixed-layout]] | 多特性混合布局（最终综合测试） |

---

## 测试说明

- **前提**: 在 Obsidian 中启用 `Workbench` 主题（本仓库根目录就是主题本体；`VaultExample/.obsidian/themes/Workbench/` 下用两个符号链接指向 `theme.css` 与 `manifest.json`）
- **推荐插件**: [Style Settings](https://github.com/mgmeyers/obsidian-style-settings) — 调整打印缩放和标尺
- **推荐插件**: [Better Export PDF](https://github.com/l1xnan/obsidian-better-export-pdf) — 调试打印 CSS
- **版本要求**: Obsidian ≥ 1.10

每个测试文件都带有明确的 `cssclasses` 和 `tags` 前注，方便筛选和分类查看。

---
*Generated: 2026-07-07*
