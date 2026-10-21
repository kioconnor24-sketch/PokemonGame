# Final corridor scratch evidence — 2026-10-21

SCRATCH-ROM-TESTED. NOT PRODUCTION-MERGED. This directory supersedes earlier
44945713 records for final candidate acceptance. No ROM, ELF or flash save is included.

Source `1f21747e60b139d275ab4196f957dc854d618f53` is a local scratch commit;
engine tree `9f0183e88fd2153c69f078573e6d6b31289848e7`. Public reproduction is
`apply_scratch_overlay.py` plus `engine-overlay/`. All38 changed files were
reproduced byte-for-byte from base `a80f871ba156e062401ac49d785d0b49b2d80146`;
see `corridor-v2-source-manifest.json`.

Inputs: main `9fa2f1d366b7c386910b9173967faeba86b51396`, Route202
`b4c1d39f0476b004f772506abd1b378e055ad03e`, existing section220 from Verity
`4ed99916f0aeb6bee81e9aedf51f40fb6d66730e`. No Verity production maps are in
this scratch tree. Latest observed main `ca5b47ecf34e85ab75be9501dfe1d79f4fab5a10`
adds management documentation only; its engine source matches the tested base.

## Actual results

| Check | Result |
| --- | --- |
| Corridor host regression |28/28 PASS, no failures/skips|
| Existing map-QA host tests |20/20 PASS; tester code unchanged|
| Seven-map static audit |0 findings|
| Source negatives |2/2 rejected: wrong offset and blocked seam cell|
| Relevant native |37/37 PASS; exact test names in corridor-v2-native.txt|
| Save-layout goldens |4/4 PASS|
| Graphical NORMAL |66/66 PASS; Save then fresh-process Continue3/3|
| Graphical RELEASE |66/66 PASS; Save then fresh-process Continue3/3|
| Pre-corridor save in final NORMAL |3/3 Continue checks PASS|
| Same pre-corridor save in final RELEASE |3/3 Continue checks PASS|

Both corridor runs traverse all six maps, sample reciprocal seams, use both
interior exit mats, check follower/Start menu, walk repaired Center/Gate areas,
press against closed walls and perform actual in-game SAVE. Static checks cover
all eight Route202/City seam cells; runtime samples endpoints/middle. GDB is
read-only; movement, warps, menus and SAVE use ordinary graphical-controller input.

Initial corridor entry used a disclosed test-only continue-warp save fixture.
It does not prove ordinary narrative access. Subsequent Continue tests load
saves written by the game in a separate emulator process. The legacy save was
generated through ordinary NEW GAME/opening/SAVE on the pre-corridor ROM, source
`0e52bb6da5169188ee1fd4f0de6f0f8c8273be41`. No transport fixture was applied to
that save. Map/position, party, selected flags, money, balls/berries and follower
restore in both final profiles. This is a generated compatibility fixture, not
a supplied historical private save. Native additionally tests encrypted/PC/flash
persistence of all256 origin bytes and region state.

Legacy Continue results retain one raw-source Saltmere north-seam warning at
(7,0) facing CoastalMeadow(7,31). It is identical on production engine base,
pre-corridor baseline and candidate; see `saltmere-preexisting-static-warning.json`.
Those three-check cases test Continue only, not acceptance of the Saltmere seam.
No new runtime defect was demonstrated; no unrelated M1 map was changed.

## Build and reproduction

ARM GCC14.2.1 (20241119), apcs-gnu; graphical mGBA0.10.5. NORMAL and RELEASE
use unchanged default cries-OFF policy. All cry sources remain intact.
Source `/workspace/.onboarding/activate.sh`; allow local X/GDB sockets and use
writable XDG cache/runtime paths. Final RELEASE/Continue runs use
`LIBGL_ALWAYS_SOFTWARE=1 SDL_RENDER_DRIVER=software`. Earlier intermittent
no-window attempts are recorded environment failures, not PASSes or proven game
defects. No speculative tester/engine fix was introduced.

Reproduce this frozen evidence, not future production registration:

1. Fetch exact inputs; create a disposable branch `codex/corridor-scratch-...`
   at base a80f871b (main9fa2f1d3 merged with exact181).
2. Touch `Pokemon Game/engine/.map_qa_throwaway`; run committed
   `apply_scratch_overlay.py --repo SCRATCH_REPO --overlay ENGINE_OVERLAY`.
3. Build in scratch engine: `make -j3`, then `make -j3 RELEASE=1`.
4. Native: `make -j2 -O check TESTS=Averon ROMTEST=/workspace/.onboarding/mgba-rom-test`
   with the following `TEST_SRCS` (then repeat with `TESTS=test/save.c`):

```
test/test_runner.c test/test_test_runner.c test/test_runner_args.c test/test_runner_battle.c test/averon_corridor_location.c test/averon_location_compatibility.c test/averon_sandgem_location.c test/averon_route202_location.c test/averon_map_registry_contract.c test/averon_region_save.c test/averon_region_travel.c test/save.c
```

5. Use merged `scripts/claude_play/map_qa.py static/run`. Batch:
   MAP_JUBILIFE_CITY, MAP_ROUTE203, MAP_OREBURGH_GATE_1F,
   MAP_JUBILIFE_CITY_POKEMON_CENTER_1F, MAP_JUBILIFE_CITY_MART,
   MAP_JUBILIFE_CITY_POKEMON_SCHOOL. Additional `--blocked` probes:
   `MAP_JUBILIFE_CITY_POKEMON_CENTER_1F,1,6,left`,
   `MAP_OREBURGH_GATE_1F,19,4,up`, `MAP_OREBURGH_GATE_1F,25,20,down`.
   Use `--save corridor-v2`, close emulator, then a separate process with
   `--expect PREVIOUS_OUT/saved-corridor-v2.json`.

This is a focused native subset, not an unfiltered M1/battle rerun. Legacy
identity goldens, save structures and strict failure baseline were not weakened.

## Resources and production boundary

`resource-comparison.json` gives all four ROM hashes and actual linked sizes:
NORMAL+22,540B; RELEASE+22,532B; linked EWRAM/IWRAM growth0.
Final NORMAL SHA256:
`6b5db1684efbaf80e52d3cd5a38fa7c0f15412722d934b671efaa8ebcc35d1f2`.
Final RELEASE SHA256:
`a3f1003a39d1b62d26fbca9fd5a9c73852b468a4177c898adee6518d103561d9`.

Route202 #181 still needs genuine owner protected-path authorization, described
in Issue15 comment6298723295. This evidence is not authorization. After its
eligible merge, serialize held Verity, then corridor, each with its own actual
path handoff. Verity appends change the new corridor's temporary map slots:
regenerate registry goldens and rerun exact-production-head evidence. Existing
public slots, sections0–214, NONE215 and specials253–255 must stay unchanged.
No sections>=224, healer, story, encounters or donor art are introduced here.
No Delta, human audio listening or ordinary narrative travel acceptance is claimed.
