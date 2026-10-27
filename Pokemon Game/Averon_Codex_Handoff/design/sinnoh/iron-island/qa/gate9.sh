#!/bin/bash
# W13 (Spring Path, Sendoff Spring, Turnback Cave, Maniac Tunnel) on the eastern-loop scene.
L=/root/claude-dev/cries-scratch/gate
while [ ! -f "$L/gate8.done" ] || pgrep -x mgba >/dev/null; do sleep 30; done
T="/root/claude-dev/wt-static/Pokemon Game"; cd "$T/scripts/claude_play" || exit 1
O="$L/w13-normal"; rm -rf "$O"; mkdir -p "$O"; cp -r "$L/w13-scratch" "$O/scratch"
M=(--map MAP_SPRING_PATH --map MAP_SENDOFF_SPRING --map MAP_MANIAC_TUNNEL --map MAP_TURNBACK_CAVE_1F
   --map MAP_TURNBACK_CAVE_B1F --map MAP_TURNBACK_CAVE_B2F)
timeout 5400 python3 -B map_qa.py run --engine "$T/engine" --rom "$T/engine/pokeemerald-cries-off.gba" --build normal --scratch "$O/scratch" --out "$O/run" "${M[@]}" --save qa > "$O/run.log" 2>&1; echo "run exit $?" >> "$O/run.log"
timeout 900 python3 -B map_qa.py run --engine "$T/engine" --rom "$T/engine/pokeemerald-cries-off.gba" --build normal --scratch "$O/scratch" --out "$O/continue" "${M[@]}" --expect "$O/run/saved-qa.json" > "$O/continue.log" 2>&1; echo "continue exit $?" >> "$O/continue.log"
touch "$L/gate9.done"
