#!/usr/bin/env bash
# Link this repo into the test vault as a live theme install.
#
# Why a symlink and not a copy: a copy is a second source of truth, and every visual
# observation made against it can silently describe an older build. The vault only
# ever loads repo-root theme.css / manifest.json.
#
#   ./tests/VaultTest/link-theme.sh          # create/verify the links
#   ./tests/VaultTest/link-theme.sh --check  # verify only, non-zero on a stale link
set -euo pipefail

VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$VAULT/../.." && pwd)"
NAME="${THEME_NAME:-Workbench}"
DEST="$VAULT/.obsidian/themes/$NAME"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

if [ "$CHECK_ONLY" = "0" ]; then
  mkdir -p "$DEST"
  for f in theme.css manifest.json; do
    target="$(python3 -c "import os,sys;print(os.path.relpath(sys.argv[1], sys.argv[2]))" "$REPO/$f" "$DEST")"
    if [ -L "$DEST/$f" ]; then
      [ "$(readlink "$DEST/$f")" = "$target" ] && continue
      rm "$DEST/$f"
    elif [ -e "$DEST/$f" ]; then
      echo "refusing to replace the real file $DEST/$f — move it aside first" >&2
      exit 1
    fi
    ln -s "$target" "$DEST/$f"
    echo "linked $f -> $target"
  done
fi

fail=0
for f in theme.css manifest.json; do
  if [ ! -e "$DEST/$f" ]; then
    echo "MISSING  $DEST/$f" >&2
    fail=1
    continue
  fi
  a=$(md5 -q "$REPO/$f")
  b=$(md5 -q "$DEST/$f")
  if [ "$a" = "$b" ]; then
    echo "live     $f ($a)"
  else
    echo "STALE    $f — vault $b vs repo $a" >&2
    fail=1
  fi
done

# The vault's configured theme must be the folder we linked, or the app renders the
# default theme while looking set up.
configured=$(python3 -c "import json,sys;print(json.load(open('$VAULT/.obsidian/appearance.json')).get('cssTheme',''))" 2>/dev/null || echo "")
if [ "$configured" != "$NAME" ]; then
  echo "MISMATCH appearance.json cssTheme='$configured' but the linked folder is '$NAME'" >&2
  fail=1
else
  echo "matches  appearance.json cssTheme=$NAME"
fi

exit "$fail"
