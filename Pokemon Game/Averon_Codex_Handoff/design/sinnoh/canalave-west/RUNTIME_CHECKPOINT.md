# Canalave/Route218 four-map DEV verification — 2026-10-23

Reuses completed #234/#236 source/art; no map reconstruction. Source branch codex/canalave-dev-runtime-20261023, PR239 retargeted to main after #236 merged. Normal main merge reconciles current056d881158aa87b48ef71fdd67c110d7015dbaa6. Actual compiled based855ff86785a744264788ff39815cc70581e4c94 and all five engine/QA source files are byte-identical to current main (see runtime-evidence/baseline-equivalence.json); unchanged source/code does not need a redundant rebuild. Exact test engine tree **417bde2f93ff9c0d52358593a51c392bb20d4c2f** is reconstructed from28 installed recipe files, not a production commit.

Existing19 slots/pinned identities untouched; temporary19–22/217 surrogate only. Native General/Building metadata prefixes and pointers/callbacks retained; only isolated Rustboro/Shop secondary banks. All source geometry/warps/full attributes/water preserved, no gameplay objects/flags/items/moves added. Guarded exact-base marker/branch/input/path/dirty checks, source-driver identity verification and ordinary controller-only QA retained. Original private save unchanged.

## Actual results

| Check | NORMAL | RELEASE |
| --- | --- | --- |
| Four-map retained warp round trips/follower/on-foot/menu/Save |45/45|45/45|
| Fresh-process Continue and on-foot flags |4/4|4/4|
| Genuine unchanged original flash |3/3|3/3|
| Linked ROM bytes |17,409,504|17,528,632|
| Increment vs matching measured baseline |+16,160|+16,168|
| EWRAM / IWRAM |226480 /28392|226482 /28336|

**104/104 real GUI checks, curated native29/29 and unchanged strict save goldens4/4.** Host6/6; original-base full442/442; reconciled current-main full477/477, zero skips. Not an unfiltered M1 rerun. GCC14.2.1/MODERN1/criesOFF, mGBA0.10.5. Matching ELF/ROM segments and linked extent verified; RELEASE16,025,800B free under32MiB; RAM unchanged. Final-head CI must pass separately.

NORMAL ROM SHA256d5aa56c5961939f8dfc24b6235a561fefbfd406a61874a074f24f699b18b7487.
RELEASE ROM SHA25642371dcaced522fb6cebcf5f35878d42f6432721f1ada4cd9f492d3affdd522f.
40 public evidence files under runtime-evidence: actual recipe/source identity, byte-equivalence, source/static/build/resource/native/golden/GUI logs, JSON/events/screenshots and manifest. No ROM/ELF/linker dump/private save/expected-save snapshot published. Neutral art, sampled paths and retained warps are tested; city-wide bridge/water interactions, final aesthetics, Delta and production/story access are not exhaustively accepted.

## Correcting the earlier foot-route assumption

The old art handoff conservatively assumed water blocked a whole foot route. Actual source graph has a59-step **dry** path from(59,24) to(4,20) and zero static findings across all four maps. Both real profiles completed all retained portal pairs and the route. Every recorded follower/warp arrival has actual avatar_flags1, onFoot mask1 and Surf mask8 absent. Water/collision/attrs/callbacks/saved flags were never changed to obtain this. This does not mean water itself is foot-traversable; no Surf grant/unlock or gameplay acceptance is fabricated.

## Failure, reproduction and recovery

First wrapper attempt aborted BEFORE GAMEPLAY because resolving _wrapper before importing the expected driver violated the existing strict identity guard. Corrected import order to match merged runner; guard unchanged. The actual failure log is retained and a fresh-process test covers identity plus positive/negative live-flag observations and method restoration. A transient environment-unavailable signal occurred during builds; workspace/jobs returned intact and all results were verified afterward, not assumed.

Start persistent Xvfb77 with -noreset for sequential GUI cases. Use prepare_runtime.py on marked codex/canalave-runtime-scratch-* at exact based855ff, then `make -j4 all MODERN=1` and `make -j4 all MODERN=1 RELEASE=1`. CLI run_runtime_qa.py uses the actual matching profile/ROM/recipe. Native source list is the preceding room package list with averon_canalave_runtime.c replacing averon_remaining_room_runtime.c; run TESTS=Averon and then TESTS=*backwards compatible. Source/ROM/recipe/marker are checked before input. Future baselines must be intentionally repinned, not silently relabeled.

All jobs ended; scratch source restored clean after archiving the overlay and matching paired artifacts. Private bundle /workspace/scratch/canalave-built-20261023; source stash5b67feb05846645133e9139d23b3d32ba9fa9763. Verified duplicate per-case game.gba copies were removed ONLY after identical canonical archived ROM hashes were checked; every private save, unique binary, source, log and history remains intact. Room/snow/eastern/Coronet archives preserved. Original save SHA25644cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d unchanged.

NEXT per manager6374512946: preserved stacked SunyshoreCity + Route222 + Route223 + literal PokmonLeague, and Route222_Access only if source portals support it. Read immutable #237 stages, new design/sinnoh/sunyshore-coast outputs, existing permitted art/packer, explicit closure/Surf limits, then guarded current-main runtime. Claim exact files, no permanent227+ IDs, donor graphics, original story or production install. #237 still needs genuine owner-reserved handoff for three development inventory paths; #235 snow visual gap remains DRAFT. No failing merge or self-authored authorization.
