#!/bin/bash
# gbuild TREE LOG ROM [make args]: guarded build. heal_locations.json restored first and must equal HEAD after
# (mapjson groups can run twice under -j and truncate it; map_data_rules.mk:32).
tree="$1" log="$2" rom="$3"; shift 3
cd "$tree/Pokemon Game/engine" || exit 9
git checkout -q -- src/data/heal_locations.json && rm -f "$rom"
make -j6 CRIES=off "$@" > "$log" 2>&1; rc=$?
git diff --quiet -- src/data/heal_locations.json; hl=$?
echo "build exit $rc heal_locations_unchanged $((hl==0))" >> "$log"
sha256sum "$rom" >> "$log" 2>&1
[ $rc -eq 0 ] && [ $hl -eq 0 ]
