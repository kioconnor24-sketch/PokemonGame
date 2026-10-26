#!/bin/bash
# Serial DEV gates (one emulator at a time), tooling ba533bed: W8 re-run, W13, W14. Each: NORMAL run + fresh Continue.
L=/root/claude-dev/cries-scratch/gate
gate() {  # name tree scratch maps...
  local name=$1 T="/root/claude-dev/$2/Pokemon Game" S=$3; shift 3
  while pgrep -x mgba >/dev/null; do sleep 30; done
  local O="$L/$name"; rm -rf "$O"; mkdir -p "$O"; cp -r "$L/$S" "$O/scratch"
  local M=(); for m in "$@"; do M+=(--map "$m"); done
  cd "$T/scripts/claude_play" || return 1
  timeout 5400 python3 -B map_qa.py run --engine "$T/engine" --rom "$T/engine/pokeemerald-cries-off.gba" --build normal --scratch "$O/scratch" --out "$O/run" "${M[@]}" --save qa > "$O/run.log" 2>&1; echo "run exit $?" >> "$O/run.log"
  timeout 900 python3 -B map_qa.py run --engine "$T/engine" --rom "$T/engine/pokeemerald-cries-off.gba" --build normal --scratch "$O/scratch" --out "$O/continue" "${M[@]}" --expect "$O/run/saved-qa.json" > "$O/continue.log" 2>&1; echo "continue exit $?" >> "$O/continue.log"
}
gate w8b-normal wt-static2 w8-scratch MAP_ROUTE209 MAP_SOLACEON_RUINS_A MAP_SOLACEON_RUINS_B MAP_SOLACEON_RUINS_C \
  MAP_LOST_TOWER_1F MAP_LOST_TOWER_2F MAP_LOST_TOWER_3F MAP_LOST_TOWER_4F MAP_LOST_TOWER_5F MAP_LOST_TOWER_6F
gate w13b-normal wt-static w13-scratch MAP_SPRING_PATH MAP_SENDOFF_SPRING MAP_MANIAC_TUNNEL MAP_TURNBACK_CAVE_1F \
  MAP_TURNBACK_CAVE_B1F MAP_TURNBACK_CAVE_B2F
gate w14-normal wt-prodthrow w14-scratch MAP_JUBILIFE_CITY MAP_JUBILIFE_CITY_GLOBAL_TERMINAL_1F MAP_JUBILIFE_CITY_GLOBAL_TERMINAL_2F \
  MAP_JUBILIFE_CITY_TV_1F MAP_JUBILIFE_CITY_TV_2F MAP_JUBILIFE_CITY_POKETCH_COMPANY_1F MAP_JUBILIFE_CITY_POKETCH_COMPANY_2F \
  MAP_JUBILIFE_CITY_POKETCH_COMPANY_3F MAP_JUBILIFE_CITY_CONDO1 MAP_JUBILIFE_CITY_CONDO2
touch "$L/chain1.done"
