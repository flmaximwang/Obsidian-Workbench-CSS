// freeze-print.js —— 在 Obsidian 的 DevTools Console 里粘一次，然后正常「导出为 PDF」。
//
// 为什么需要它：
//   Obsidian 原生打印路径在导出结束后立即调用 `.print` 元素的 detach() 把它移除
//   （obsidian.asar 里 `r=function(){n.detach(), ...}`，n 就是那个 div.print）。
//   所以导出完再看 DOM 就什么都抓不到了。把 detach 变成"请留下来"，就能在导出
//   完成后从容检查／序列化打印时的真实 DOM。
//
// 用法：
//   1) DevTools (Cmd+Opt+I) → Console → 粘贴执行
//   2) 正常触发导出：命令面板执行 "Export to PDF"（或 Cmd+P）
//   3) 保持 DevTools 打开，导出结束后在 Console 里：
//        document.querySelector('div.print').outerHTML      // 打印用的 DOM 子树
//        copy(document.documentElement.outerHTML)           // 整份文档（含 .print）
//        getComputedStyle(document.querySelector('div.print > .markdown-preview-view')).width
//   4) 想恢复原状：__unfreezePrint()
//
// 注意：冻结后每次导出都会残留一个 .print，屏幕上看不出来（被
//   `body > :not(.print){display:none}` 挡在打印媒体之外），但会占内存。

(() => {
  if (window.__unfreezePrint) {
    console.warn("已经 freeze 过了。如需恢复请先执行 __unfreezePrint()");
    return;
  }
  const origDetach = Node.prototype.detach;      // Obsidian 给 Node 加的扩展方法
  const kept = [];
  Node.prototype.detach = function () {
    if (this.classList && this.classList.contains("print")) {
      kept.push(this);
      console.log("[freeze-print] 拦下 detach()，保留", this);
      return this;                                // 不真的移除
    }
    return origDetach.apply(this, arguments);
  };
  window.__unfreezePrint = () => {
    Node.prototype.detach = origDetach;
    kept.forEach((el) => el.remove());
    kept.length = 0;
    delete window.__unfreezePrint;
    console.log("[freeze-print] 已恢复，残留的 .print 已清除");
  };
  console.log("[freeze-print] 已就绪：下一次导出会保留 .print 元素，导出后用 "
    + "document.querySelector('div.print').outerHTML 取出打印 DOM。");
})();
