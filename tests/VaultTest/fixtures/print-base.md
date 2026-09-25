---
cssclasses:
  - a4-page
tags:
  - workbench-fixture
---

# Print fixture — A4 page with an embedded Base

This is the note that reproduced the **whole-page fit-shrink**: a note containing `![[x.base]]`
exported with every element (including a 714px ruler) scaled to ~2/3, because Chromium's print
fit-to-page fires on the Base's viewport-tracking table width. The fix lives in
`src/desktop/note/page/print/main.css` and must stay **outside** `@media print`.

FIXTURE-BASE-SENTINEL

![[print-base.base]]

Filler after the Base so the embed is not the last block. Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Vivamus lacinia odio vitae vestibulum vestibulum. Cras venenatis euismod malesuada.
Suspendisse potenti. Phasellus volutpat neque in augue ullamcorper, eget tristique velit aliquam.
