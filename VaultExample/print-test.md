---
cssclasses:
  - a4-page
tags:
  - test
  - print
  - export
date: 2026-07-07
---

# 🖨️ Print Test — 打印/PDF 导出测试

> **测试目标**: 验证打印媒体样式 —— A4 页边距、页面尺寸、标尺覆盖线、阅读视图→PDF 导出效果
>
> **使用方法**: 切换至**阅读视图** → `Cmd+P` 打印（或使用 Better Export PDF 插件）

---

## 打印设置

| 设置项 | 推荐值 | 说明 |
|:-------|:------|:-----|
| 页面大小 | A4 | 通过 `a4-page` cssclass |
| 页边距 | 默认 | 由 print CSS 控制 |
| 打印缩放 | 100% | 可通过 Style Settings 调整 |
| 背景图形 | 开启 | 确保 callout 背景色可见 |
| PDF 导出 | 横向/纵向均可 | 内容宽度 714px 适配 A4 |

## A4 打印分页测试

> [!note] 第 1 页内容
> 此内容位于文档前半部分，应当出现在打印输出的第一页。

---

此处插入手动分页标记（`<hr>` 通常被 print CSS 处理为分页点）。

> [!warning] 第 2 页内容
> 此内容应当出现在打印输出的第二页。

---

更多内容用于触发更多分页。

## 长文本填充以触发分页

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus lacinia odio vitae vestibulum vestibulum. Cras venenatis euismod malesuada. Suspendisse potenti. Phasellus volutpat neque in augue ullamcorper, eget tristique velit aliquam.

Maecenas sed diam eget risus varius blandit sit amet non magna. Donec ullamcorper nulla non metus auctor fringilla. Nullam quis risus eget urna mollis ornare vel eu leo.

Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec sed odio dui. Vivamus sagittis lacus vel augue laoreet rutrum faucibus dolor auctor. Maecenas faucibus mollis interdum.

Cras mattis consectetur purus sit amet fermentum. Donec id elit non mi porta gravida at eget metus. Nullam id dolor id nibh ultricies vehicula ut id elit. Aenean lacinia bibendum nulla sed consectetur.

## 打印中的 Callout

> [!note] Print Note
> Callout 在打印时应当保留背景色和边框（需开启"背景图形"）

> [!warning] Print Warning
> 警告 callout 颜色在打印时应保持可辨识度

> [!success] Print Success
> 成功 callout 用于确认打印样式

## 打印中的代码块

```python
# 此代码块在打印时应当保留语法高亮
def print_test():
    print("Testing PDF export from Obsidian")
```

## 打印中的表格

| 打印元素 | 预期行为 | 当前状态 |
|:---------|:---------|:--------:|
| 文本     | 黑色，可缩放 | ✅ |
| Callout  | 保留颜色与边框 | 待验证 |
| 代码块   | 保留高亮 | 待验证 |
| 表格     | 保留边框 | 待验证 |
| 图片     | 保留比例 | 待验证 |
| 链接     | 保留文字+URL (可选) | 待验证 |

## 打印标尺（调试模式）

启用 Style Settings 中的"Print Ruler Overlays"后，PDF 预览中应看到：
- **红色** — 纸张边缘
- **绿色** — 打印区域（margin box）
- **蓝色** — 内容区域（content box）

> [!tip] 调试步骤
> 1. 安装 [Better Export PDF](https://github.com/l1xnan/obsidian-better-export-pdf)
> 2. 打开导出对话框（不导出，仅预览）
> 3. 打开 DevTools (`Cmd+Opt+I`)
> 4. Rendering 面板 → Emulate CSS media type: `print`
> 5. 检查 `.print` 元素的 `display: none` 并移除

---

> [!info] 打印完成检查清单
> - [ ] 页面尺寸为 A4 (210mm × 297mm)
> - [ ] 页边距均匀
> - [ ] Callout 颜色保留
> - [ ] 代码块语法高亮保留
> - [ ] 表格边框正确
> - [ ] 分页位置合理（无孤行）
> - [ ] 链接可读
> - [ ] 标题渐变下划线在打印中是否可见
