---
tags:
  - test
  - callout
  - grid
date: 2026-07-07
---

# 🔲 Callout Grid — 多列网格

> **测试目标**: 验证 `[!grid]` 系列网格布局 —— `[!grid|2]`, `[!grid|3]`, `[!grid|4]`, 以及嵌套网格

---

## 2 列网格

> [!grid|2]
>> [!note] 列 1-A
>> 标准 note callout
>>
>> 内容第二行
>
>> [!tip] 列 1-B
>> Tip callout in grid

## 3 列网格

> [!grid|3]
>> [!note] **卡片 #1**
>> 第一列内容
>
>> [!warning] **卡片 #2**
>> 第二列含警告信息
>
>> [!important] **卡片 #3**
>> 第三列重要提示

## 4 列网格

> [!grid|4]
>> [!note] Cell 1
>> 内容
>
>> [!note] Cell 2
>> 内容
>
>> [!note] Cell 3
>> 内容
>
>> [!note] Cell 4
>> 内容

## 不同类型混合网格

> [!grid|3]
>> [!tip] **Tips**
>> - 使用 `[!tip]` 提示技巧
>> - 支持列表
>
>> [!warning] **警告**
>> > 内嵌引用
>> 注意事项文本
>
>> [!danger] **危险**
>> ```python
>> danger = True
>> ```
>
>> [!success] **成功**
>> ✅ 任务完成
>
>> [!info] **信息**
>> 附加信息说明
>
>> [!question] **疑问**
>> 这是一个问题吗？

## 嵌套网格

> [!grid|2]
>> [!grid|2] **内层 2 列**
>>> 子 A
>>>
>>> 子 B
>
>> [!note] **右侧**
>> 普通 callout 右侧对齐

## 网格 + 媒体占位

> [!grid|3]
>> **图 A**
>> `![400](https://picsum.photos/seed/g1/400/300)`
>
>> **图 B**
>> `![400](https://picsum.photos/seed/g2/400/300)`
>
>> **图 C**
>> `![400](https://picsum.photos/seed/g3/400/300)`

## 网格内容拉伸测试

> [!grid|2]
>> **短内容**
>>
>> 简短
>
>> **长内容**
>>
>> 这是一段比较长的内容，用来测试网格中的弹性伸缩。在 grid 布局中，同一行各列高度应当保持一致（等高布局）。如果一列内容较短、另一列内容更长，短列会被拉伸以匹配长列的高度。
>> 
>> Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus lacinia odio vitae vestibulum vestibulum. Cras venenatis euismod malesuada. Suspendisse potenti.

> [!grid|3]
>> [!check] ✅ 无样式
>> 纯净内容
>
>> [!check] ✅ 无样式
>> 同样纯净
>
>> [!check] ✅ 无样式
>> 第三列

> [!warning] 网格限制
> 网格只能包含 **作为子项的 callout**。裸文本或段落不能直接放在网格中，必须用至少一个 `[!blank]` 包裹（如果不需要可见边框）。
