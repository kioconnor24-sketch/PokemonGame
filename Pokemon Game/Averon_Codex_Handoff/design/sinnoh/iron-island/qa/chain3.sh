#!/bin/bash
# After chain2: W8 again with tooling 68c27967 (one-way holes + go() returns to the map).
L=/root/claude-dev/cries-scratch/gate
while [ ! -f "$L/chain2.done" ] || pgrep -x mgba >/dev/null; do sleep 30; done
cp "/root/claude-dev/wt-mapqa-batch/Pokemon Game/scripts/claude_play/"*.py "/root/claude-dev/wt-static2/Pokemon Game/scripts/claude_play/"
git -C /root/claude-dev/wt-mapqa-batch rev-parse HEAD > "$L/chain3.tooling"
source <(sed -n '/^gate() {/,/^}/p' /root/claude-dev/qa-tools/chain1.sh)
gate w8c-normal wt-static2 w8-scratch MAP_ROUTE209 MAP_SOLACEON_RUINS_A MAP_SOLACEON_RUINS_B MAP_SOLACEON_RUINS_C \
  MAP_LOST_TOWER_1F MAP_LOST_TOWER_2F MAP_LOST_TOWER_3F MAP_LOST_TOWER_4F MAP_LOST_TOWER_5F MAP_LOST_TOWER_6F
touch "$L/chain3.done"
