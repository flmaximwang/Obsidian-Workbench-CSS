#!/usr/bin/env bash
# 以远程调试模式启动 Obsidian（必须在 Obsidian 完全退出后执行）
#
#   ./launch-obsidian-debug.sh            # 默认端口 9222
#   PORT=9333 ./launch-obsidian-debug.sh
#
# 验证：curl -s http://127.0.0.1:9222/json/version
#   预期输出含 "Browser": "Chrome/xxx"（Electron 的内核标识可能不同，但必须有 webSocketDebuggerUrl）
set -euo pipefail

PORT="${PORT:-9222}"
APP="${OBSIDIAN_APP:-/Applications/Obsidian.app}"

if pgrep -f "$APP/Contents/MacOS/Obsidian" >/dev/null 2>&1; then
  echo "Obsidian 正在运行。调试端口只在启动时生效，需要先退出："
  echo "  osascript -e 'quit app \"Obsidian\"'"
  echo "然后重新执行本脚本。"
  exit 1
fi

echo "启动 Obsidian，调试端口 $PORT ..."
open -na "$APP" --args "--remote-debugging-port=$PORT"

for i in $(seq 1 20); do
  sleep 1
  if curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "OK：调试端口已就绪"
    curl -s "http://127.0.0.1:$PORT/json/version"
    exit 0
  fi
done
echo "超时：端口没起来。检查是否有另一个 Obsidian 实例占用了单实例锁。" >&2
exit 1
