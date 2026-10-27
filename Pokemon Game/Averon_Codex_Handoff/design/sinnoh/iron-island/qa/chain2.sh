#!/bin/bash
# After chain1: W12 Veilstone civic on the eastern-loop scene (wt-static4), tooling ba533bed.
L=/root/claude-dev/cries-scratch/gate
while [ ! -f "$L/chain1.done" ] || pgrep -x mgba >/dev/null; do sleep 30; done
source <(sed -n '/^gate() {/,/^}/p' /root/claude-dev/qa-tools/chain1.sh)
gate w12-normal wt-static4 w12-scratch MAP_VEILSTONE_CITY MAP_VEILSTONE_CITY_DEPARTMENT_STORE_1F MAP_VEILSTONE_CITY_DEPARTMENT_STORE_2F \
  MAP_VEILSTONE_CITY_DEPARTMENT_STORE_3F MAP_VEILSTONE_CITY_DEPARTMENT_STORE_4F MAP_VEILSTONE_CITY_DEPARTMENT_STORE_5F \
  MAP_VEILSTONE_CITY_DEPARTMENT_STORE_ROOFTOP MAP_VEILSTONE_CITY_POKEMON_CENTER_1F MAP_VEILSTONE_CITY_WAREHOUSE_1F MAP_VEILSTONE_CITY_WAREHOUSE_2F
touch "$L/chain2.done"
