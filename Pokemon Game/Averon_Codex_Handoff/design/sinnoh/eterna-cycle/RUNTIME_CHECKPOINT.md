# Connected Eterna/Cycling/211 DEV runtime — tested current-main candidate

Production baseline **c6ac2f967b02473741791eb24b5cc9b11bda3904**. Reuses completed #213/#219/#220 geography/art; no reconversion. Exactly **five maps** are installed: EternaCity60×55, Route206_North9×11, Route20628×120, Route206_South9×11, Route211_West36×28. All current Sinnoh slots0–18, including northern13–18, remain unchanged; only this marked disposable checkout appends19–23. All source headers remain MAPSEC_PENDING_OWNER. Existing217 is a DEV-only surrogate, never a production met-origin allocation. No production source, save format, permanent origin, NPC/story/encounter/service or global General edit is submitted.

## Exact source and paired builds

The deterministic recipe verifies nine current tracked baseline files, refuses a moved base/dirty or unmarked checkout/occupied target, and installs36 controlled files. Actual repository tree **beeb31fddc575b70a0cfab727304cc0d41f6843f**, engine subtree **077938717b95b6b8aefad5f319579bc020b77ce1**. Every installed file was reverified against runtime-recipe.json before GUI testing and preservation. All three outdoors share the same General/Rustboro82-record family; both gates use existing Building/Shop295. Source collision/elevation, complete attributes, all original warp arrays and reciprocal offsets are unchanged. Source271+19 elevation15 cells remain intact.

| Actual linked build | Used bytes | Delta vs actual c6ac build | Free under32MiB | ROM SHA256 |
| --- | ---: | ---: | ---: | --- |
| NORMAL | 17425948 | +32604 | 16128484 | 8e14c7150d1a3e8aa29c35155b8280ae3bb2cd4ca4649db2a0e6dc9f51090057 |
| RELEASE | 17545076 | +32612 | 16009356 | f00e37527b27c55c5cd20f5377d5b426a869d874deb715e7b7dc9ea337f2ad4c |

Both ROM files are padded33554432B; used bytes come from their matching ELF/link map, not padding. ARM GCC14.2.1, MODERN=1, default criesOFF; existing generated assets reused, not a clean-build claim. NORMAL EWRAM226480/IWRAM28392B; RELEASE226482/28336B, zero delta from paired main baselines. Existing toolchain/newlib warnings remain in raw logs. Baseline ROM identities/capacity are published with #217: NORMAL5bf7e16f41bf2e6e1e55538f45412699ab20493e62566e2b26db9c9c6577c259; RELEASE64c4ab1d5052804612092080ce08066a72e502571d76c64f03f78adb1e088130. No ROM/ELF/private save is uploaded.

## Executed checks

- Focused host **19/19**, complete Sinnoh source **236/236**, zero skips. Includes real QA World parsing, pinned family/header/registry preservation, unsafe installation refusal, malformed warps/offsets/banks and native-rule elevation/arrow routing negatives.
- Additional broad source discover **504 outcomes,503 executed PASS,1SKIP**: test_averon_mapjson_inclusion.MapjsonInclusionTests.test_arm_link_preserves_slots_and_requires_layout_events_and_scripts requires ARM binutils/built preproc in that source checkout. This optional broader run is explicitly not all504PASS and not the M1 strict native baseline.
- Actual compiled native **29/29**: two new compiled-header/shared-family cases plus existing numeric registry, location/encryption/PC/flash/regional/northern fixtures. Separate save-layout goldens **4/4**: PokemonStorage and SaveBlocks1/2/3. Raw logs retain exact identities. Full M1 strict baseline was not rerun or relabelled.
- Existing static audit **0 findings**. City↔Route211 has3 reciprocal sampled walking spans per side. City↔Route206 connection±1 exists for streaming but has **zero direct walking span** because original roofs block it; actual movement uses NorthGate. Do not claim a foot seam across that boundary.
- Genuine graphical mGBA0.10.5 with controller input: **EACH NORMAL and RELEASE** final traversal **55/55**, fresh-process Continue **3/3**, and unmodified original legacy flash load **3/3**. All five maps, constructed walking seam/gateway warp pairs, followers, menu and game-written SAVE exercised. Continue endpoint Ridge(0,20); this is not proof of saving at every bridge square.
- Dedicated actual upper bridge probe **150/150 EACH profile**, including140 individually checked steps down/up Route206(10,15)↔(10,85); player/follower retain elevation4.
- Dedicated lower underpass probe **42/42 EACH profile**, including32 individually checked steps left/right(20,70)↔(4,70), crossing source elevation15 columns9/10/15/16; player/follower retain elevation3. Actual layer screenshots inspected and published.

The genuine legacy source remains SHA256 **44cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d**, unchanged before/after both runs. DEV entry flash copies are labelled as fixtures and never replace that legacy baseline. GUI used X11/software rendering with dummy audio; no human listening/Delta acceptance.

## Real failed trials and repairs retained

The63 files in runtime-evidence contain raw builds/native/save/static/source identity, final ten successful result/event pairs,20 actual screenshots and five failed result/event pairs. Old successful and failed private trial directories are preserved too.

1. Initial static parser could not recognize generated `.metatileAttributes=g...`; existing World requires `.metatileAttributes = symbol`. Owned first build was explicitly terminated before correcting generator formatting. Real parser regression added; parser not weakened.
2. Initial NORMAL compile failed guessed Building graphics/palette aliases. Existing engine uses InsideBuilding names and InitTilesetAnim_Building. Recipe now reads all actual pinned header bindings; no guessed aliases/NULL callbacks. Failed compile log retained.
3. Initial genuine2D traversal **46/49 FAIL**: naive upper→lower path and global tile blockers prevented two lower exits; one follower observation failed. Same ROM/source retained. Height-aware `(x,y,elevation)` navigation now follows existing native0/15 semantics and selects a reachable gateway for another layer.
4. First height retry **40/43 FAIL**: ordinary follower step pressed NORTH on a current NORTH_ARROW_WARP, legitimately warping. Planner now excludes the current arrow direction from ordinary walking and verifies exact neighbour/return before observing follower; source behavior unchanged.
5. First upper probe **3/4 FAIL**, setup only: follower placement left actor one tile away. Explicitly walk to/settle at entry and verify before probing.
6. First exact upper probe **4/5 FAIL**, false assertion despite correct coordinate/elevation: real Driver.step returns game.State, an empty dict with live attributes, hence falsey. Launcher checks `is None` rather than truthiness; real State host regression added. No game memory or terrain patch.
7. First full stricter NORMAL replay **51/52 FAIL** at lower arrow4: navigation returned a tile before its movement settled. Launcher now settles ordinary walking and rechecks exact destination. Final paired replays pass55/55 with strict follower return checks; that failed receipt remains separate. Previous clean55/55 trials were not silently relabelled as final-helper trials.

`run_runtime_qa.py` reuses the existing controller/QA checks; all36 source hashes/DEV marker are validated before launch. Player/follower elevations are read only using matching-build compiler-derived object offsets. No GDB game-state writes, entity spawning, teleportation, baseline relaxation or source physics changes are used.

## Reproduction and remaining gates

Run prepare_runtime.py --repo SOURCE_REPO to inspect; only --install into a clean exact-c6ac codex/eterna-runtime-scratch-* checkout with engine/.map_qa_throwaway can write. Run test_sinnoh_eterna_runtime.py and all test_sinnoh_*.py. Build MODERN=1 normal and RELEASE=1 profiles, run native fixture with registry/corridor/location/region_save/northern/save test sources, then existing map_qa fixtures and this guarded launcher for normal/--bridge-probe upper/lower/--expect saved state. Exact source inputs and all tested map files are hashed in the recipe/identity; raw result/event identities bind actual ROMs. Private accepted ROM/ELF/map pairs are preserved at /workspace/scratch/eterna-current-accepted-20261022 before scratch reuse.

This is a reproducible **DEV runtime**, not merged production gameplay. Natural arrival, story/bicycle progression, services, whiteout, human audio listening and Delta remain unaccepted. Permanent origins227+ and protected production path handoffs still require legitimate owner/manager action. Manager owns reviews/merges in this session; do not self-merge. Next independently executable runtime is the already-adapted six-map Forest/Chateau cluster with #222's coordinate-aware15 self-map warp QA; keep all31 cluster events and previous accepted evidence intact.

Tested launcher identity: dedicated150/42 probes used commit8bc07ce810617ca29256ecccf9ef606df73d3dc8, fileSHA256 fddee9d13dc704f3ab4fdb3a9a8bf525efb1dd58b7d814d5376ed5c21b720135. Final paired55/Continue3/legacy3 used settled-navigation fileSHA256 a06d07ea066236698dd3dd62d3c3410b16b183856c9e162e4592760e8413efab. The later evidence-only commit does not change the engine/ROMs. Published log files normalize semantically empty EOF lines only; private raw stdout remains preserved.
