---
tags:
  - test
  - callout
  - timeline
date: 2026-07-07
---

# 📅 Callout Timeline — 时间线布局

> **测试目标**: 验证 `[!timeline]` 的时间线布局 —— 左侧时间轴 + 右侧内容卡片

---

## 标准时间线

> [!timeline|2024-Q1] **项目启动**
> 项目初始化阶段，完成需求调研和技术选型。
> - 团队组建
> - 需求文档 v1
> - 技术栈评审

> [!timeline|2024-Q2] **MVP 开发**
> 最小可行产品开发阶段。
>
> 后端 API 开发完成，前端初步集成。启动内部测试。
>
> ``git tag v0.1.0``

> [!timeline|2024-Q3] **Beta 测试**
> ```
> 用户数 : 500+
> 反馈  : 120条
> 修复  : 45个
> ```
> Beta 版本发布，收集用户反馈并迭代。

> [!timeline|2024-Q4] **正式发布 🚀**
> **v1.0.0** 正式版发布。
> - [x] 核心功能完成
> - [x] 文档编写
> - [x] CI/CD 上线

## 时间线 + 不同类型

> [!timeline|Day 1] `[!note]` 样式
> > [!note]
> > 时间线内的 note callout

> [!timeline|Day 2] `[!warning]` 样式
> > [!warning]
> > 时间线内的警告

> [!timeline|Day 3] `[!success]` 样式
> > [!success]
> > 成功完成里程碑

## 时间线 + 代码

> [!timeline|v0.1] **初始提交**
> ```python
> def init():
>     print("Hello Timeline!")
> ```

> [!timeline|v0.2] **功能添加**
> ```python
> def feature():
>     return "timeline feature"
> ```

## 无标题时间线

> [!timeline|阶段1]
> 不设标题，只有时间和内容。

---

> [!warning] 时间线提示
> 时间线中的每个 `[!timeline]` 代表一个时间点；多个连续的时间线 callout 按顺序串联形成完整时间轴。可通过标题参数（`|标题`）自定义时间节点标签。
