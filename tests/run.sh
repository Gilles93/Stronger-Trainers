#!/usr/bin/env bash
# Load this mod through the engine's own loader, for every game version and
# every engine build the player might actually be running.
#
# The engine tree under test is the RELEASE payload unzipped out of
# gen1recomp.exe -- plus the newer .love in the save directory's updates/ if
# the updater has fetched one. A dev checkout is deliberately not used: it
# reports its version as 0.0.0-dev and is not what anyone plays.
#
# Extracted ROM data lives in .romdata/ and is gitignored; tools/gamedata.py
# documents the command that produces it.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

EXE="${GEN1RECOMP_EXE:-/c/Users/Gille/Downloads/gen1recomp-0.1.72-windows/gen1recomp-win64/gen1recomp.exe}"
UPDATES="${GEN1RECOMP_UPDATES:-$APPDATA/pokemon-love2d/updates}"
LOVEC="${LOVEC:-/c/Users/Gille/Gen1Recomp/love/lovec.exe}"
ENGINES="$REPO/.engine"
MOD_ID="stronger_trainers"

[ -x "$LOVEC" ] || { echo "no lovec.exe at $LOVEC (set LOVEC)"; exit 2; }

# --- unpack every engine build we can find. A fused LOVE binary is a zip
# with a stub in front, so unzip reads the exe directly.
mkdir -p "$ENGINES"
unpack() {  # <archive> <label>
  local archive="$1" label="$2"
  [ -f "$archive" ] || return 1
  if [ ! -f "$ENGINES/$label/src/core/GameVersion.lua" ]; then
    mkdir -p "$ENGINES/$label"
    ( cd "$ENGINES/$label" && unzip -o -q "$archive" ) 2>/dev/null
  fi
  [ -f "$ENGINES/$label/src/core/GameVersion.lua" ] || return 1
  echo "$label"
}

builds=()
if v=$(unpack "$EXE" "release-exe"); then builds+=("$v"); fi
for love in "$UPDATES"/gen1recomp-*.love; do
  [ -f "$love" ] || continue
  label="update-$(basename "$love" .love | sed 's/^gen1recomp-//')"
  if v=$(unpack "$love" "$label"); then builds+=("$v"); fi
done

if [ ${#builds[@]} -eq 0 ]; then
  echo "no engine payload could be unpacked (looked at $EXE and $UPDATES)"
  exit 2
fi

# lovec.exe is not an msys binary and does not understand /c/... paths
win() { printf '%s' "$(cd "$1" && pwd -W 2>/dev/null || echo "$1")"; }

versions=("${@:-}")
[ -z "${versions[0]:-}" ] && versions=(red blue yellow)

status=0
for build in "${builds[@]}"; do
  for version in "${versions[@]}"; do
    data="$REPO/.romdata/$version"
    if [ ! -f "$data/trainers.lua" ]; then
      echo "== $version :: $build :: SKIPPED (no .romdata/$version)"
      continue
    fi
    "$LOVEC" "$(win "$HERE")" \
      --game "$(win "$ENGINES/$build")" \
      --mod-dir "$(win "$REPO")" \
      --mod "$MOD_ID" \
      --version "$version" \
      --data "$(win "$data")"
    rc=$?
    [ $rc -ne 0 ] && status=$rc
    echo
  done
done
exit $status
