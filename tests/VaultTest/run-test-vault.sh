#!/usr/bin/env bash
# Launch a THROWAWAY Obsidian profile that opens only tests/VaultTest, with the debug port.
#
#   ./tests/VaultTest/run-test-vault.sh          # port 9222
#   PORT=9333 ./tests/VaultTest/run-test-vault.sh
#
# Why a separate profile: the single-instance lock is per `--user-data-dir`, so this never
# touches a running Obsidian window, its vault list or its open tabs. Kill it with
#   pkill -f "user-data-dir=$PROFILE_DIR"
set -euo pipefail

VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-9222}"
PROFILE_DIR="${PROFILE_DIR:-/tmp/obs-workbench-test}"
APP="${OBSIDIAN_APP:-/Applications/Obsidian.app}"

"$VAULT/link-theme.sh"

mkdir -p "$PROFILE_DIR"
python3 - "$PROFILE_DIR" "$VAULT" <<'PY'
import json, sys
profile, vault = sys.argv[1], sys.argv[2]
data = {"vaults": {"7e57c0de00000001": {"path": vault, "ts": 1, "open": True}}, "cli": False}
with open(f"{profile}/obsidian.json", "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=2)
PY

echo "profile : $PROFILE_DIR"
echo "vault   : $VAULT"
echo "port    : $PORT"
open -na "$APP" --args "--remote-debugging-port=$PORT" "--user-data-dir=$PROFILE_DIR" "--remote-allow-origins=*"

for i in $(seq 1 30); do
  sleep 1
  if curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "OK: debug port is up"
    echo "next: cd $VAULT/../.. && npm run test:live"
    exit 0
  fi
done
echo "timeout waiting for the debug port — check that no other profile holds port $PORT" >&2
exit 1
