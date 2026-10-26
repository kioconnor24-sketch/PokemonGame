#!/bin/bash
# Integration-gate runs for the completed W1 (19 maps) and south-west W2+W6 batches.
# NORMAL then RELEASE, each followed by a fresh-process Continue. One emulator at a time. Tooling 8027173f.
L=/root/claude-dev/cries-scratch/gate
mkdir -p "$L"
run() {
  local tree="$1" out="$2" src="$3" build="$4" rom="$5"; shift 5
  local M=(); for m in "$@"; do M+=(--map "$m"); done
  while pgrep -x mgba >/dev/null; do sleep 20; done
  cd "$tree/Pokemon Game/scripts/claude_play" || return
  local E="$tree/Pokemon Game/engine"
  rm -rf "$out"; mkdir -p "$out"; cp -r "$src" "$out/scratch"
  timeout 7200 python3 -B map_qa.py run --engine "$E" --rom "$E/$rom" --build "$build" --scratch "$out/scratch" --out "$out/run" "${M[@]}" --save qa > "$out/run.log" 2>&1
  echo "run exit $?" >> "$out/run.log"
  timeout 900 python3 -B map_qa.py run --engine "$E" --rom "$E/$rom" --build "$build" --scratch "$out/scratch" --out "$out/continue" "${M[@]}" --expect "$out/run/saved-qa.json" > "$out/continue.log" 2>&1
  echo "continue exit $?" >> "$out/continue.log"
}
W1=(MAP_ROUTE218_EAST MAP_ROUTE218 MAP_ROUTE218_WEST MAP_CANALAVE_CITY MAP_CANALAVE_CITY_HARBOR MAP_CANALAVE_CITY_POKEMON_CENTER_1F
    MAP_CANALAVE_CITY_LIBRARY_1F MAP_CANALAVE_CITY_LIBRARY_2F MAP_CANALAVE_CITY_HOUSE2 MAP_CANALAVE_CITY_HOUSE3 MAP_CANALAVE_CITY_HOUSE4
    MAP_CANALAVE_CITY_HOUSE5 MAP_CANALAVE_CITY_HOUSE6 MAP_IRON_ISLAND MAP_IRON_ISLAND_HOUSE MAP_IRON_ISLAND_1F MAP_IRON_ISLAND_B1F
    MAP_IRON_ISLAND_B2F MAP_IRON_ISLAND_B3F)
SW_A=(MAP_SANDGEM_TOWN MAP_SANDGEM_TOWN_POKEMON_CENTER_1F MAP_ROUTE219)
SW_B=(MAP_ROUTE221 MAP_PAL_PARK_GATE MAP_PAL_PARK)
T1=/root/claude-dev/wt-iron2throw; T6=/root/claude-dev/wt-palthrow
N=pokeemerald-cries-off.gba; R=pokeemerald-cries-off-release.gba
for b in normal release; do r=$N; [ $b = release ] && r=$R
  run $T1 "$L/w1-$b" "$L/w1-scratch" $b $r "${W1[@]}"
  run $T6 "$L/swa-$b" "$L/swa-scratch" $b $r "${SW_A[@]}"
  run $T6 "$L/swb-$b" "$L/swb-scratch" $b $r "${SW_B[@]}"
done
touch "$L/gate.done"
