---
tags:
  - test
  - media
  - image
  - video
date: 2026-07-07
---

# 🖼️ Media — 媒体元素

> **测试目标**: 验证图片、视频嵌入的响应式渲染

---

## 单张图片

`![Description](https://picsum.photos/seed/example/800/400)`

标准 markdown 图片语法。图片应当自动适应内容宽度，不溢出。

## 限定宽度图片

`![400](https://picsum.photos/seed/medium/800/400)`

使用 `![400]` 语法将图片宽度限制为 400px。

## 小图和大图

`![150](https://picsum.photos/seed/small/200/200)`

小图（150px宽度）应当保持原有比例。

`![600](https://picsum.photos/seed/large/1200/600)`

大图（600px宽度）。

## 多图并排

```
![200|inline](https://picsum.photos/seed/m1/200/200)
![200|inline](https://picsum.photos/seed/m2/200/200)
![200|inline](https://picsum.photos/seed/m3/200/200)
```

- `inline` 标志使多张图片在同一行并排显示
- 适用于图库、对比图等场景

## 图片对齐

左对齐：
`![100|left](https://picsum.photos/seed/left/100/100)`

右对齐：
`![100|right](https://picsum.photos/seed/right/100/100)`

居中（默认）：
`![100](https://picsum.photos/seed/center/100/100)`

## 视频嵌入

```markdown
![[video.mp4]]
```

或使用 HTML 标签：

```html
<video controls>
  <source src="https://www.w3schools.com/html/mov_bbb.mp4" type="video/mp4">
</video>
```

视频元素应当自适应宽度，保持宽高比，且不超出内容区域。

## 音频嵌入

```markdown
![[audio.mp3]]
```

音频播放器应显示为内联播放控件，宽度自适应。

## iframe / 嵌入

```markdown
<iframe src="https://example.com" width="100%" height="400"></iframe>
```

> [!warning] 媒体注意事项
> - Obsidian 默认禁用远程图片加载；如果需要测试外部图片，需在设置中开启
> - 视频和音频文件需在 vault 内才能渲染
> - iframe 在阅读视图中可能被安全策略限制
