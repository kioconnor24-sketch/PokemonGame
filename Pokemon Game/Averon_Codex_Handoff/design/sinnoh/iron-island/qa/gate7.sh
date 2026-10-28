#!/bin/bash
# W8 (Lost Tower + Solaceon Ruins with the derived Route 209 step fix) on the hearthome-solaceon scene.
L=/root/claude-dev/cries-scratch/gate
while [ ! -f "$L/gate6.done" ] || pgrep -x mgba >/dev/null; do sleep 30; done
T="/root/claude-dev/wt-static2/Pokemon Game"; cd "$T/scripts/claude_play" || exit 1
O="$L/w8-normal"; rm -rf "$O"; mkdir -p "$O"; cp -r "$L/w8-scratch" "$O/scratch"
M=(--map MAP_ROUTE209 --map MAP_SOLACEON_RUINS_A --map MAP_SOLACEON_RUINS_B --map MAP_SOLACEON_RUINS_C
   --map MAP_LOST_TOWER_1F --map MAP_LOST_TOWER_2F --map MAP_LOST_TOWER_3F --map MAP_LOST_TOWER_4F
   --map MAP_LOST_TOWER_5F --map MAP_LOST_TOWER_6F)
timeout 5400 python3 -B map_qa.py run --engine "$T/engine" --rom "$T/engine/pokeemerald-cries-off.gba" --build normal --scratch "$O/scratch" --out "$O/run" "${M[@]}" --save qa > "$O/run.log" 2>&1; echo "run exit $?" >> "$O/run.log"
timeout 900 python3 -B map_qa.py run --engine "$T/engine" --rom "$T/engine/pokeemerald-cries-off.gba" --build normal --scratch "$O/scratch" --out "$O/continue" "${M[@]}" --expect "$O/run/saved-qa.json" > "$O/continue.log" 2>&1; echo "continue exit $?" >> "$O/continue.log"
touch "$L/gate7.done"
