#!/usr/bin/env bash
# Run AFTER installing the exact central DEV recipe and building both ROMs.
# Requires the owner's original flash + its private saved-state expectation;
# neither private file is redistributed. One X11 mGBA session at a time.
set -euo pipefail
if [ "$#" -ne 6 ]; then
  echo 'usage: reproduce.sh ENGINE INSTALLED_RECIPE LEGACY_FLASH LEGACY_EXPECT OUTPUT_ROOT normal|release' >&2
  exit 2
fi
engine=$(realpath "$1")
recipe=$(realpath "$2")
legacy=$(realpath "$3")
expected=$(realpath "$4")
root=$(realpath -m "$5")
profile=$6
case "$profile" in normal) rom="$engine/pokeemerald.gba";; release) rom="$engine/pokeemerald-release.gba";; *) exit 2;; esac
here=$(cd -- "$(dirname -- "$0")/.." && pwd)
qa="$here/../../../../scripts/claude_play/map_qa.py"
launcher="$here/run_runtime_qa.py"
export PYTHONDONTWRITEBYTECODE=1 SDL_AUDIODRIVER=dummy SDL_VIDEODRIVER=x11
export LIBGL_ALWAYS_SOFTWARE=1 SDL_RENDER_DRIVER=software
: "${DISPLAY:?Run an isolated X11 display first; do not reuse an active gameplay session}"
xdotool getdisplaygeometry >/dev/null
test ! -e "$root/$profile" || { echo "Refusing an existing profile output" >&2; exit 2; }
original_hash=$(sha256sum "$legacy")
mkdir -p "$root/$profile/entry" "$root/$profile/continue" "$root/$profile/legacy"
python3 "$qa" fixture-save --engine "$engine" "$legacy" "$root/$profile/entry/game.sav" MAP_HEARTHOME_CITY 30 25
python3 "$launcher" --engine "$engine" --recipe "$recipe" --rom "$rom" --profile "$profile" \
  --scratch "$root/$profile/entry" --out "$root/$profile/traversal"
cp "$root/$profile/entry/game.sav" "$root/$profile/continue/game.sav"
python3 "$launcher" --engine "$engine" --recipe "$recipe" --rom "$rom" --profile "$profile" \
  --scratch "$root/$profile/continue" --out "$root/$profile/continued" --expect "$root/$profile/traversal/saved-central-seven.json"
cp "$legacy" "$root/$profile/legacy/game.sav"
python3 "$qa" run --engine "$engine" --rom "$rom" --build "$profile" --map MAP_SALTMERE \
  --scratch "$root/$profile/legacy" --out "$root/$profile/legacy-result" --expect "$expected"
for probe in upper lower; do
  x=22; y=12
  if [ "$probe" = lower ]; then x=14; y=16; fi
  mkdir -p "$root/$profile/$probe-entry"
  python3 "$qa" fixture-save --engine "$engine" "$legacy" "$root/$profile/$probe-entry/game.sav" MAP_ROUTE208 "$x" "$y"
  python3 "$launcher" --engine "$engine" --recipe "$recipe" --rom "$rom" --profile "$profile" \
    --scratch "$root/$profile/$probe-entry" --out "$root/$profile/$probe-result" --bridge-probe "$probe"
done
test "$(sha256sum "$legacy")" = "$original_hash"
