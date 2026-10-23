# Original Victory Road core shell — source/art only

Manager6376103408 Priority B, exact claim6376396281. Started after the Sunyshore source/art/actual NORMAL chain, while its RELEASE/native tests run. Parent coast branch preserves all existing packets; no production engine install, saved IDs or donor pixel import.

Actual original GBA maps: SinnohVictoryRoad_1F52×84, 2F32×32, B1F40×52 =7,472 cells. Six reciprocal stair pairs (12 real warp events), closed borders, a connected ordinary-floor component on each floor and at least two walking approaches to every stair. Full native MB_LADDER behavior; all walkable tiles elevation3. Existing tracked General/Cave art/palettes/metadata render all three maps without new graphics banks. Original floor rooms/corridors and ceiling/side faces are explicit in shell-recipe.json, not invented donor data.

Technical reference: pret/pokeplatinum@6dc1499e3127176d4cb34f41c01ee62e1d98808a, actual res/field/events/events_victory_road_{1f,2f,b1f}.json and events_pokemon_league.json. portal-reference.json retains only technical warp facts, original file blob/SHA256 provenance, no NPC/script/encounter/DS images. All12 core event coordinates and floor return identities come from those pinned sources. Original GBA corridors approximate the physical shell; this is not faithful DS terrain reconstruction or gameplay/HM puzzle acceptance. External sources Bulbapedia/Serebii returned HTTP403 in this environment; source-pinned GitHub technical event data was available and used instead, not treated as missing geography.

Existing237 ledger target SN-L29 had no registered Sinnoh donor map. Its unregistered similarly named Hoenn/FRLG layouts were not relabeled or substituted. The existing League candidate has no actual cave warp, so this batch does not pretend an exterior already works. Two main League portal anchors(15,78),(34,5) and the side-room anchor(45,33) remain solid in1F; no external event is activated. The three side rooms/Route224 branch, water/HM puzzles, exterior source-footprint mapping and actual lower/upper League shell are next physical work, not complete or production accepted. DS exterior coordinates are recorded as reference facts only, not silently applied to the GBA map.

Focused source/art6/6 PASS: every technical stair matches source; exact candidate bytes/headers; 7,472 cells/buffer/closed edges; all floor components and multiple stair approaches; exact neutral closed external anchors/no events/origins; native ladder and complete graphics/palette/render pixels/source asset hashes; wrong map set/oversized buffer/diagonal corridor/out-of-bounds floor/nonreciprocal or external stair negatives; forbidden output. All16 outputs independently regenerated twice byte-for-byte. All three previews inspected. Native/build/mGBA/Save tests for these new floors are NOT YET RUN; the coast paired ROM does not contain these floors.

Reproduce:

```sh
python3 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/victory-road-shell/build_shell.py' --engine 'Pokemon Game/engine' --out /new/off-engine/shell
python3 -m unittest discover -s 'Pokemon Game/scripts/tests' -p 'test_sinnoh_victory_road_shell.py' -v
```

No new227+ origin, permanent registry slots, encounters, trainers, plot, item placement, boulder/Surf/Waterfall grants or global art changes. Next executable task: guarded three-floor DEV scene, paired real builds/native/stair/follower/Save→fresh Continue/old-flash checks; then a separate reviewed exact League approach adaptation before enabling natural exterior arrivals. Owner-only full namespace policy still pending; physical work need not wait.
