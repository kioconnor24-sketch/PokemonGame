# Four-floor DEV room verification — 2026-10-23

Source/art from #237/#238; real Twinleaf main and rival house1F/2F, no reconstructed geometry. Both stair pairs tested separately from copied-save DEV entries; exterior town doors remain closed. Neutral stock art/mats are test proxies, not final donor appearance or services/story acceptance. Only these four floors, not all42 art candidates or91 source maps, have new compiled/runtime evidence.

Exact production base d855ff86785a744264788ff39815cc70581e4c94. Exact combined engine **tree**8ca8bfc246ce6d39f3c40da4e7d0445d4ea38b97, reconstructed from26 installed recipe files. This is a disposable test tree, not a production commit. Original19 slots retained, temporary19–22 and existing217 surrogate; saved structs/encoding/identities unchanged. Native Building pointer reused after byte-equal metadata verification; one isolated331-record Shop secondary, unchanged source graphics/palettes/callbacks. Guarded installer and source-verified generic height-aware QA are reused.

## Actual results

| Check | NORMAL | RELEASE |
| --- | --- | --- |
| Main house live stair round trips/follower/menu/Save |14/14|14/14|
| Main house fresh-process Continue |3/3|3/3|
| Rival house live stair round trips/follower/menu/Save |14/14|14/14|
| Rival house fresh-process Continue |3/3|3/3|
| Genuine unchanged original-flash load |3/3|3/3|
| Linked ROM bytes |17,400,448|17,519,568|
| Increment vs matching measured baseline |+7,104|+7,104|
| EWRAM / IWRAM bytes |226480 /28392|226482 /28336|

**74/74 genuine GUI checks; native29/29; strict unchanged SaveBlock1/2/3/PC goldens4/4; host installation/negative5/5.** Full source host461/461, zero skips, independently fetched Actions120635247505 on93f4c5ddb0ac0f26432ae76e86abfe80515f2c76; final evidence-head checks remain separately required. The native run is a curated regression, not an unfiltered M1 rerun. GCC14.2.1/MODERN1/criesOFF, mGBA0.10.5. Both builds exited0; matching ELF/ROM load segments and linked extent verified. RELEASE16,034,864B free under32MiB; RAM unchanged.

NORMAL ROM SHA25696e70bd975c101d7f47b6a0f46b5332391dbcd8bc60a102ab9dcd038fe22a60b.
RELEASE ROM SHA256dcd6a543117edede8671a6af6f9c886bca52f9ce20de2627112334c628cb3660.
`room-runtime-evidence/` has49 actual source/recipe/resource/log/result/event/screenshot/manifest files. No ROM/ELF/private save or expected-save snapshot is published. Original private save remains44cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d.

## Reproduction and failures retained

Use the exact-base marked `codex/rooms-runtime-scratch-*` installer, then NORMAL `make -j4 all MODERN=1` and RELEASE `make -j4 all MODERN=1 RELEASE=1`. Run each pair with `run_room_runtime_qa.py --pair main|rival` against the matching profile/ROM/recipe. Start persistent `Xvfb :77 -screen 0 800x600x24 -nolisten tcp -ac -noreset` before sequential cases: the existing Emulator defaults to77. Native source list: test_runner.c,test_runner_args.c,test_runner_battle.c,test_test_runner.c,averon_map_registry_contract.c,averon_corridor_location.c,averon_location_compatibility.c,averon_region_save.c,averon_northern_location.c,save.c,averon_remaining_room_runtime.c under test/. Run `make -j4 check MODERN=1 TESTS=Averon TEST_SRCS=... ROMTEST=/workspace/.onboarding/mgba-rom-test`, then the same with `TESTS=*backwards compatible`. Fixture-save and source/ROM checks precede ordinary controller input; do not copy a DEV save into production.

Initial private caller used persistent display78 while Emulator uses77. Two subsequent launches failed before gameplay (`x11 not available`); both retained in launch-blocks. Correcting the caller to persistent77 made fresh Continue and the independent rival pair pass; no engine/helper/memory change or hidden gameplay failure. Initial art asset-hash test compared working CRLF palettes with canonical LF; corrected to the established verified-file API without changing any asset/hash baseline.

## Recovery / next executable task

All scene/build/native jobs ended. Scratch tracked source restored clean after preserving overlay stash **5d5886cec9ead3e255e61965a5b1df2c10ecea0e** and private paired artifact bundle `/workspace/scratch/remaining-rooms-built-20261023`. Restore once via stash OR installer against exact baseline, never over a different overlay. Existing snow/eastern/Coronet archives and private saves preserved.

Refresh main/claims, then prepare the already completed four-map Canalave/Route218 DEV cluster from #234/#236 (ordinary water/portals; separate entries as needed, no fake Surf/story unlock). Reuse the guarded installer/QA patterns, actual paired builds and original-save checks. Continue broader source-family art construction from the now complete159 registered source inventory; remaining47 targets are physical gaps, not completed gameplay. #237 still requires genuine owner-reserved handoff for its three development inventory files at e3663c8b86999f23442d366eb2379e22291d7332. #235 remains DRAFT for the unresolved snow bridge visual. No failing/protected merge is authorized.
