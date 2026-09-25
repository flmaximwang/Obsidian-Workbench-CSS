#!/usr/bin/env bash
# Symlink the one plugin the live print checks need into the test vault.
#
#   ./tests/VaultTest/link-plugins.sh                       # source: the first vault found
#   ./tests/VaultTest/link-plugins.sh /path/to/vault        # source: that vault's .obsidian/plugins
#
# Symlinks, never copies: the plugin binaries stay in the vault that already has them,
# nothing large lands in this repo, and the test vault is reproducible from a clone.
# `tests/vault.test.js` fails if any plugin file turns out to be a real copy.
set -euo pipefail

VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN="better-export-pdf"   # the id better-export-pdf ships with
DEST="$VAULT/.obsidian/plugins/$PLUGIN"

find_source() {
  if [ "${1:-}" != "" ]; then echo "$1/.obsidian/plugins/$PLUGIN"; return; fi
  for base in /Users/org_zsqlab/Obsidian /Users/maxim/Documents/Obsidian; do
    [ -d "$base" ] || continue
    found=$(find "$base" -maxdepth 4 -type d -name "$PLUGIN" 2>/dev/null | head -1 || true)
    if [ -n "$found" ]; then echo "$found"; return; fi
  done
}

SRC="$(find_source "${1:-}")"
if [ -z "${SRC:-}" ] || [ ! -d "$SRC" ]; then
  echo "no existing $PLUGIN install found — pass the vault that has it: $0 <vault-path>" >&2
  exit 1
fi
echo "source: $SRC"

mkdir -p "$DEST"
# Binaries only: symlinking data.json would let the test vault write into the source
# vault's plugin settings. With no data.json the plugin runs on its defaults, which is
# exactly the state the checks assume (ruler uses borders because backgrounds do not print).
for name in main.js manifest.json styles.css; do
  [ -e "$SRC/$name" ] || continue
  [ -e "$DEST/$name" ] && continue
  ln -s "$SRC/$name" "$DEST/$name"
done
ls -l "$DEST" | sed '1d' | awk '{print "  linked " $9 " -> " $11}'

python3 - "$VAULT" "$PLUGIN" <<'PY'
import json, sys
vault, plugin = sys.argv[1], sys.argv[2]
p = f"{vault}/.obsidian/community-plugins.json"
ids = json.load(open(p, encoding="utf-8"))
if plugin not in ids:
    ids.append(plugin)
    json.dump(ids, open(p, "w", encoding="utf-8"), indent=2)
    open(p, "a", encoding="utf-8").write("\n")
print("community-plugins.json ->", ids)
PY
