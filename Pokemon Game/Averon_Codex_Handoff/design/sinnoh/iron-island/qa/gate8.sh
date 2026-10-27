#!/bin/bash
# W1 harbor (three-plank gangway) + Newmoon, Fullmoon and Iron Island, tooling 37d52157.
L=/root/claude-dev/cries-scratch/gate
while [ ! -f "$L/gate7.done" ] || pgrep -x mgba >/dev/null; do sleep 30; done
T="/root/claude-dev/wt-iron2throw/Pokemon Game"; cd "$T/scripts/claude_play" || exit 1
O="$L/nm-normal"; rm -rf "$O"; mkdir -p "$O"; cp -r "$L/nm-scratch" "$O/scratch"
M=(--map MAP_CANALAVE_CITY_HARBOR --map MAP_NEWMOON_ISLAND --map MAP_FULLMOON_ISLAND --map MAP_IRON_ISLAND)
timeout 5400 python3 -B map_qa.py run --engine "$T/engine" --rom "$T/engine/pokeemerald-cries-off.gba" --build normal --scratch "$O/scratch" --out "$O/run" "${M[@]}" --save qa > "$O/run.log" 2>&1; echo "run exit $?" >> "$O/run.log"
timeout 900 python3 -B map_qa.py run --engine "$T/engine" --rom "$T/engine/pokeemerald-cries-off.gba" --build normal --scratch "$O/scratch" --out "$O/continue" "${M[@]}" --expect "$O/run/saved-qa.json" > "$O/continue.log" 2>&1; echo "continue exit $?" >> "$O/continue.log"
touch "$L/gate8.done"
