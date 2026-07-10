---
tags:
  - test
  - callout
  - absolute
date: 2026-07-07
---

# 📌 Callout Absolute — 绝对定位

> **测试目标**: 验证 `[!absolute]` 的定位能力 —— 通过元数据 `position: top-left|top-right|bottom-left|bottom-right|center` 控制绝对位置

---

## 绝对定位注意事项

> [!warning] **重要说明**
> `[!absolute]` 将其父容器作为定位参考。在默认布局中，父容器是整个内容区域。如果需要精确定位到某个段落或元素附近，请用 `<div>` 包裹作为定位上下文。
>
> 此测试文件仅包含**概念性说明** —— 绝对定位的最佳测试方式是在实际页面中拖拽侧边栏和调整窗口大小，观察定位元素是否固定于视口中的指定位置。

## 定位类型

| 定位值 | 位置 | 典型用途 |
|:-------|:----|:---------|
| `position: top-right` | 右上角 | 导航浮窗、操作按钮 |
| `position: top-left` | 左上角 | 返回顶部 |
| `position: bottom-right` | 右下角 | 回到顶部、联系浮窗 |
| `position: bottom-left` | 左下角 | 版本信息 |
| `position: center` | 居中 | 模态对话框替代 |

## 具体定位示例

```yaml
> [!absolute]
> position: top-right
> **右上角固定**
> 滚动页面时此内容固定在右上角
```

> [!note] 定位机制说明
> `[!absolute]` 使用 CSS `position: fixed`（相对于视口）或 `position: absolute`（相对于定位父容器）。多用于**页面向导**、**关键指标看板**、**快速操作入口**等。建议避免在移动端使用。

## 定位上下文示例

```html
<div style="position: relative; min-height: 200px; border: 1px dashed var(--text-muted); padding: 1em;">
  <!-- 此 div 是定位父容器 -->
  
  > [!absolute]
  > position: top-right
  > **浮动按钮**
  > 固定在此框右上角
  
  <p>父容器内的普通内容。</p>
  <p>绝对定位元素不会影响周围内容的布局。</p>
</div>
```

> [!tip] 调试建议
> 使用浏览器的 DevTools（`Cmd+Opt+I`）检查 `[!absolute]` 元素的 `position` 和 `top`/`right`/`bottom`/`left` 属性值。
