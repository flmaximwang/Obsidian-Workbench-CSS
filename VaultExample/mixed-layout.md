---
cssclasses:
  - wide
tags:
  - test
  - mixed
  - comprehensive
date: 2026-07-07
---

# 🧩 Mixed Layout — 混合布局综合测试

> **测试目标**: 综合验证多种主题特性在同一篇笔记中的配合 —— float + grid + card + timeline + blank + typography 混合使用

---

## 1. 概述 + 浮动摘要

> [!float|right]
> ### 快速导航
> 1. [[#1 概述 + 浮动摘要]]
> 2. [[#2 卡片网格仪表盘]]
> 3. [[#3 时间线集成]]
> 4. [[#4 宽表格 + 浮动]]
> 5. [[#5 复杂嵌套]]

这是一篇综合测试笔记，用于验证多种布局元素在同一页面中的共存与配合情况。右侧的浮动导航提供了快速跳转功能。

页面采用 `wide` 布局以获得最大灵活性，适合展示复杂布局。

## 2. 卡片网格仪表盘

> [!grid|3]
>> [!card] 📈 **指标 A**
>> ```
>> 完成率: 87%
>> 趋势: ↑
>> ```
>
>> [!card] 📊 **指标 B**
>> ```
>> 覆盖率: 92%
>> 趋势: →
>> ```
>
>> [!card] ⚡ **指标 C**
>> ```
>> 响应时间: 1.2s
>> 趋势: ↓
>> ```
>
>> [!card] 🎯 **指标 D**
>> ```
>> 准确率: 95%
>> 趋势: ↑
>> ```
>
>> [!card] 🔒 **指标 E**
>> ```
>> 安全性: A+
>> 趋势: →
>> ```
>
>> [!card] 📋 **指标 F**
>> ```
>> 活跃用户: 1.2K
>> 趋势: ↑
>> ```

## 3. 时间线集成

> [!timeline|Phase 1] **需求分析**
> > [!grid|2]
> >> [!blank]
> >> - 用户访谈
> >> - 竞品分析
> >
> >> [!blank]
> >> ```
> >> 周期: 2周
> >> 状态: ✅
> >> ```

> [!timeline|Phase 2] **原型设计**
> > [!grid|2]
> >> [!card] **低保真**
> >> 线框图阶段
> >
> >> [!card] **高保真**
> >> Figma 原型
>
> ```python
> # 时间线内的代码块
> def phase2():
>     print("Prototyping complete")
> ```

> [!timeline|Phase 3] **开发迭代**
> - 后端 API
> - 前端集成
> - 自动化测试

## 4. 宽表格 + 浮动注释

> [!float|left]
> **表格说明**
> 
> 左侧的浮动说明框解释右侧表格中各字段的含义。这种设计常用于**带注释的数据报告**。
> - 浮动元素不打断表格流
> - 文字环绕维持可读性

| 组件 | 版本 | 状态 | 覆盖率 | 备注 |
|:----|:----:|:----:|:------:|:-----|
| Auth Service | v2.1 | ✅ | 94% | JWT + OAuth |
| API Gateway | v3.0 | ✅ | 89% | Rate limiting |
| Frontend | v4.2 | ⚠️ | 76% | 需补充 E2E |
| Database | v5.0 | ✅ | 91% | Migrations OK |
| Cache Layer | v1.8 | ✅ | 85% | Redis cluster |
| Queue System | v2.3 | ⚠️ | 72% | 需故障转移测试 |

*注: ⚠️ 表示需关注的项目*

## 5. 复杂嵌套

> [!grid|2]
>> [!blank]
>> ### 左区：嵌套展示
>> 
>> > [!note] **左侧主容器**
>> > 内部包含多行数据
>> > 
>> > ```
>> > ID: LX-001
>> > Type: Mixed
>> > ```
>> 
>> 次级内容填充。
>
>> [!blank]
>> ### 右区：代码与数据
>> 
>> ```json
>> {
>>   "layout": "mixed",
>>   "components": ["float", "grid", "card", "timeline"],
>>   "width": "wide"
>> }
>> ```
>> 
>> > [!tip] **提示**
>> > `wide` + `[!grid]` 是最强组合。

## 6. 嵌入与引用

> [!quote] **引文**
> "Good design is as little design as possible."
> — Dieter Rams

本文也通过嵌入引用其他测试笔记中的内容：

```markdown
![[page-layout-a4#水平线]]
```

> [!success] ✅ 综合测试通过标准
> - [x] Float 与其他元素共存
> - [x] Grid 内部多种类型
> - [x] Timeline 内嵌 Grid + Card + Blank
> - [x] Wide 内容宽度完整
> - [x] 复杂嵌套无布局崩溃
