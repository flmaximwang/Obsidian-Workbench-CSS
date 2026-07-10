---
cssclasses:
  - wide
tags:
  - test
  - layout
  - wide
date: 2026-07-07
---

# 🌐 Wide Page Layout

> **测试目标**: 验证 `wide` cssclass — 内容扩展至视口全宽，无宽度限制

---

## 全宽渲染

`wide` 布局禁用内容宽度约束，内容区域填满可用视口。适合仪表盘、宽表格、大图画廊等场景。

### 宽网格

在 `wide` 布局下，callout 网格可以容纳更多列：

> [!grid|4]
>> [!note] 卡片 A
>> `wide` 布局中网格列数增多
>
>> [!tip] 卡片 B
>> 利用全宽展示更多信息
>
>> [!warning] 卡片 C
>> 适合大屏显示器
>
>> [!important] 卡片 D
>> 4 列以上轻松排布

### 宽表格

| # | 特性 | A4 | A3 | wide | 备注 |
|:-|:-----|:--:|:--:|:----:|:-----|
| 1 | 内容宽度 | 714px | 72.8rem | 100% | wide = 无限制 |
| 2 | 代码块 | 换行 | 正常 | 正常 | wide 最佳 |
| 3 | 大表格 | 滚动 | 显示 | 最大空间 | wide 最佳 |
| 4 | 多栏 | 2-3列 | 3-4列 | 4-8列 | 随宽度自适应 |
| 5 | 阅读长文 | 最佳 | 可接受 | 过宽 | 注意行长度 |
| 6 | 仪表盘 | ❌ | ⚠️ | ✅ | wide 适用场景 |
| 7 | 宽幅图片 | 居中 | 完整 | 完整 | wide 最佳 |
| 8 | 并排图表 | 2幅 | 2-3幅 | 3-4幅 | 视口宽度相关 |

## 多列文本

> [!grid|2]
>> **左列**
>> 
>> 这是 `wide` 布局下的左列内容。利用 grid 2 列显示并排文本。
>> 
>> - 列表项 1
>> - 列表项 2
>> - 列表项 3
>
>> **右列**
>> 
>> 右列内容，与左列并列展示。
>> 
>> ```python
>> # 代码块在 wide 下宽度充足
>> for i in range(10):
>>     print(f"wide item {i}")
>> ```

## 宽代码块

```typescript
// Wide 布局下代码块完全无需换行或滚动
interface WideLayoutConfig {
  name: string;
  contentWidth: '100%' | 'auto' | 'unset';
  maxColumns: number;
  supportedScenarios: Array<'dashboard' | 'gallery' | 'datatable' | 'diagram'>;
  breakpoints: Record<string, { minWidth: number; columns: number }>;
}

const wideConfig: WideLayoutConfig = {
  name: 'Wide Layout',
  contentWidth: '100%',
  maxColumns: 8,
  supportedScenarios: ['dashboard', 'gallery', 'datatable', 'diagram'],
  breakpoints: {
    desktop: { minWidth: 1440, columns: 6 },
    ultrawide: { minWidth: 1920, columns: 8 }
  }
};
```

## 图片并排（占位符）

在 `wide` 下，多张图片可以并排显示而不会被宽度限制挤压：

> [!grid|3]
>> `![Placeholder 1](https://picsum.photos/seed/p1/400/300)`
>
>> `![Placeholder 2](https://picsum.photos/seed/p2/400/300)`
>
>> `![Placeholder 3](https://picsum.photos/seed/p3/400/300)`

## 宽布局注意事项

> [!warning] 行长警告
> 纯文本内容在 `wide` 布局下可能超过 75 字符/行的可读性上限。对于长篇文章，建议使用默认布局或 `a4-page`。`wide` 适用于结构化的：仪表盘、宽表格、代码比对、多栏布局。

> [!tip] 最佳实践
> 将 `wide` 与 `[!grid]` 或 `[!card]` 搭配使用，充分发挥宽屏优势。
