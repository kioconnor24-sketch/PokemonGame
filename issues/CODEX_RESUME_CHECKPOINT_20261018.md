# CODEX_RESUME_CHECKPOINT — October 18, 2026

## Scope and integration status

Execution follows [Issue #15 comment6255884529](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6255884529), tasks X1–X7. M1 remains accepted; this work does not reopen its gameplay verdict. Main at the start of final verification: `8967b05b951c63dca9ffa39325ac53f240e3d9ba` (merged #132). No Codex PR was self-merged and no direct main push occurred.

All source work is committed and pushed in separate reviewable PRs. No Claude maps, art, graphical QA or acceptance files were edited. No protected engine paths, new maps, permanent identifiers, save structures, migrations or production origin encodings were changed. Existing 0–214 / NONE 215 / Sandgem 216 / special FD–FF remain intact; 217–252 remain unallocated.

## Exact submitted heads

| Task | PR / branch | Remote source SHA | Actual focused native identities |
|---|---|---|---|
| X1 | [#134](https://github.com/kioconnor24-sketch/PokemonGame/pull/134), `codex/extended-location-tests-20261018` | `b6dd5dabdb1592ad7d533252dd26a2ed78fa8372` | 3/3 PASS |
| X2 | [#136](https://github.com/kioconnor24-sketch/PokemonGame/pull/136), `codex/healer-table-contract-20261018` | `86356d3d7679ef1de5269d6604b8a9461e85abf2` | 4 new identities / 9 parameter cases, included in 35/35 focused PASS |
| X3 | [#137](https://github.com/kioconnor24-sketch/PokemonGame/pull/137), `codex/travel-boundaries-20261018` | `b35e3f222328bb02d375713f5fc2c26934cebc3f` | 3/3 PASS |
| X4 | [#138](https://github.com/kioconnor24-sketch/PokemonGame/pull/138), `codex/unsupported-region-map-access-20261018` | `f309adf3f4479984b1befce98ae75d097318f7e1` | 6/6 PASS |
| X5 | [#140](https://github.com/kioconnor24-sketch/PokemonGame/pull/140), `codex/connection-contract-20261018` | `32c9f98047cbff455ab043946419dba10a6adad7` | 2/2 PASS |
| X6 | [#141](https://github.com/kioconnor24-sketch/PokemonGame/pull/141), `codex/grouped-origin-experiment-20261018` | `17449dfc61e929ac09f47912622735bf5de52ace` | 2/2 PASS |

These are 20 distinct new TEST identities, not 284 newly written tests. Most use parameter loops internally. Main's existing Averon suite contains 264 identities.

## Changes and reproduced failures

**X1:** reconciled the original one-file research PR with merged #132 using an ordinary main merge and retargeted the base to main. No duplicate production section integration. Actual encrypted Pokémon permutations/PC/OT rekey, checksum-valid legacy ambiguity, and actual egg hatching remain TEST-only experiments.

**X2:** a script's 16-bit healer variable was narrowed to 8 bits before validation. A native RED showed `256 + HEAL_LOCATION_PETALBURG_CITY` selecting that unrelated valid healer. Validate before narrowing. The generated optional nurse tables also inferred their length from the last nurse entry: appending a valid healer without a nurse produced a host sanitizer out-of-bounds RED at index 43. Explicit parallel table dimensions preserve today's 43 rows and safely zero-fill the optional 44th row. No actual healer was allocated. Existing raw-anchor fallback remains unchanged. Current/append-without-nurse/append-with-nurse sanitizer fixtures PASS.

**X3:** no production defect found. New cases verify rejected travel preserves an already-armed warp, indexed arrivals resolve an actual registered warp, and real flash save/load retains encrypted party+PC Sandgem origins, regional badges and the returning healer. Existing Petalburg/Oldale endpoints are stand-ins, not approved Sinnoh transport.

**X4:** actual Sinnoh 216 Fly setup returned TRUE despite absent Sinnoh map assets/grid/destinations. Generic normal-entry guards now refuse unsupported regions while preserving legacy Hoenn/Kanto behavior. PokeNav checks in the actual menu input handler before changing/freeing its menu. The earlier proposed initializer guard was removed after source review exposed an unsafe cleanup path; `pokenav_region_map.c` is unchanged from main. New actual-handler RED scheduled the unsupported feature; GREEN preserves the menu. Earlier 5-test/`6d07d071` evidence and review HOLD are superseded by 6-test/`f309adf3` evidence. The existing Fly host audit had a stale pre-#128 oracle expecting empty rows to warp to Petalburg; corrected only the audit and reviewed mutation patterns. ASan/UBSan 9/9 cases, 1,544 combinations/boundaries, relocated high special and 7/7 harmful mutants PASS/detected.

**X5:** actual Oldale↔Route101 CameraMove/re-entry preserves coordinates, party, region state and callback. RAM-only section 216 headers exercise actual connection lookup in four directions with offsets −5/0/+5 and overlapping/nonoverlapping/interior coordinates. Fixture cleanup uses ordinary DMA/task cleanup; no leak exemptions. No production geometry or follower implementation changed.

**X6:** actual encrypted records preserve all 256 legacy met bytes; unsupported synthetic details reject without a default. Two different synthetic wide origins assigned the same TEST-only byte become identical through actual PC→flash→load→party→summary consumers. Grouping therefore preserves the byte format but permanently loses exact location detail. No codebook was adopted. #134's 13-bit tests separately prove that checksum-valid old unused bits cannot identify a version and actual hatching leaves candidate high bits stale. A future scheme needs explicit owner-approved version/import/egg/trade/consumer policy. Current 36 spare ordinary bytes are not enough to guarantee 87 distinct additional origins; if 87 were required, at least 50 distinctions would need a broader scheme or grouping. This is conditional capacity arithmetic, not a content allocation.

## Exact-head GitHub native evidence

All counts below refer to the **Averon-filtered** native suite, not the accepted 6,107-result unfiltered M1 regression. The strict M1 expected-failure baseline and workflows were not changed.

| PR | Run / native job | Actual result | Textual evidence artifact / zip SHA256 |
|---|---|---|---|
| #134 |39172261690 /117807613859|267/267 PASS|12152842735 / `c25dd5ef2e20de400b883c4a8547900d0da0fcdea3f96ac1b9179b1cb16ceb23`|
| #136 |39172953393 /117809653809|268/268 PASS|12153536978 / `031724a934bd7286754529d7cb41b42c64dcc684e22eec5b5aab7941beb47c4b`|
| #137 |39173146898 /117810232596|267/267 PASS|12153109920 / `1cd111ab3d7ba57a746bd22df0eaaade8c6a97ed5f8b03fb0b1ab200058d2c45`|
| #138 |39174097324 /117813202565|270/270 PASS|12153981555 / `966161841515293524cee3855797fefe51ef9c2d7cb612a08b323baed3d5495f`|
| #140 |39173667840 /117811803485|266/266 PASS|12153756215 / `403ff8506ca39cd02d234e1459be9a543a5e97f4d760fc56447cd8212ce838d5`|
| #141 |39173797907 /117812198389|266/266 PASS|12153751862 / `55fffe8c8390a14f1a302f8f12c34042221d53d9869fb5784edceda508029d61`|

CI uses its pinned workflow's Ubuntu GCC 13 / newlib 4.4, while local measurements below use GCC 14.2.1 / binutils 2.44 / newlib 4.5. Different ROM hashes across those toolchains are recorded, not treated as identical artifacts. All CI artifacts contain textual evidence only; no ROM or user save is published.

## Actual local builds and resources

Default cries ON; no audio source/QA changes. Byte counts are **linked used ROM**, not the padded 32 MiB output size. Baseline main #132 measured with the same local toolchain: NORMAL 26,736,564 B; RELEASE 26,855,760 B.

| Source | NORMAL used / delta | RELEASE used / delta | RELEASE ROM free |
|---|---|---|---|
| #136 `86356d3d` |26,736,572 /+8 B|26,855,776 /+16 B|6,698,656 B|
| #138 `f309adf3` |26,736,764 /+200 B|26,856,484 /+724 B|6,697,948 B|

NORMAL/RELEASE ROM SHA256:

- #136 NORMAL `345fc0efe125a98efb74d896455c8b7db39486d76847773a3d396c728fc7be3f`; RELEASE `5c046cb066c4b34372b888c1e7b880a5da853e030f0667818f5db0b8856aa126`.
- #138 NORMAL `7bf92a3c7a866f3a7fb05cf026d7937885201fc218b9d0c0ae8f167e49574b40`; RELEASE `2fe09aab6ef1cd000567bb8f5e6464dcaf8d1642dfdeac1f0947c4974bd2d186`.

NORMAL static EWRAM 226,480 B / IWRAM 28,392 B. #136 RELEASE 226,486 / 28,336 B; #138 RELEASE 226,482 / 28,336 B. Save free bytes unchanged: SaveBlock1 **304**, SaveBlock2 **84**, SaveBlock3 **1,556**, PC **1,568**. Pokémon/Box sizes and save layout unchanged. NORMAL 0 compiler/linker warnings; RELEASE 4 existing newlib syscall warnings. Static linked headroom is not proof of peak runtime stack, object, palette or VRAM occupancy.

## Combined verification tree

Branch `codex/validation-only-x1-x6-20261018` is an isolated combination of the six submitted heads on main8967b05b. It is **not an integration PR or authorization to merge itself**. Manager must review the individual PRs normally.

- Combined source SHA `026c598e7c3bbc185601290de281cc9d737b510d`.
- Engine tree `782e0ab53fa5f9d339d549358cda4dd95b5aeaaf`.
- Local native result: **284/284 PASS**, no failing/skipped identities; all264 existing +20 new identities executed together. Full local build/test log SHA256 `e74eb41a4052b640835a0f722fefd7251f00cfe2ee6740d306d4dfe1fb8126aa`.
- Repeated host checks: healer current 43 / append 44 optional / append 44 nurse PASS under ASan/UBSan; Fly 9/9 and 7/7 mutations killed. `detect_leaks=0` is solely the host environment's LeakSanitizer/ptrace limitation; address/undefined checks remain enabled and native leak checks remain enabled.
- Dispatched existing authorized workflow without edits: [run39174616265](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/39174616265), native job117814638822. **IN_PROGRESS at the owner's wrap-up**; do not claim remote284/284 until its actual job log completes. Resume with `gh run view 39174616265 --json status,conclusion,jobs`, then inspect actual logs/artifact. All six individual source PRs already have the completed exact-head CI evidence above.
- The separate source PRs' actual NORMAL/RELEASE builds are recorded above. The combined CI workflow also builds NORMAL; an additional local combined retail build pair was not started before the owner's wrap-up instruction. Do not attribute either individual PR's ROM hash to the combined tree.

## Real blockers and next executable actions

1. **Independent review and normal integration:** manager reviews #134/#136/#137/#138/#140/#141 at the heads above, source changes, claims, native CI and protected gates. No self-merge. Integrating them changes the expected Averon count from 264 to 284, not a failure-baseline change. Rebase/merge refreshed main ordinarily if another PR lands; revalidate changed sources and resulting head.
2. **Sandgem healing/whiteout remains POST-CONTENT and owner-gated:** #133 is ready/open at `a91d7096efe7a857a74ca5fdfc6d96669e1f69ed`, not merged at the latest check. Its nurse's common heal does not itself register a respawn anchor; actual `HealPlayerParty` preservation is native-tested. Need owner-approved healer allocation and exact exterior anchor/interior nurse coordinates, then scoped protected-path handoff if required. Claude owns its map/scripts and must wire approved `setrespawn` from the ordinary center hook. Do not silently select the next healer ID, alter maps, or claim natural Sandgem whiteout PASS. Generic #136 guards can integrate independently. [Exact blocker in Issue #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55#issuecomment-6256277307).
3. **X7 starts after actual #133 main merge:** refresh main; read exact merged map/layout/script tree and latest claims. Run existing actual NORMAL/RELEASE resource+save-headroom tooling on merged content, then relevant cries ON/OFF parity using existing configuration tooling. Compare linked growth against a same-toolchain parent and retain actual hashes. No merged-Sandgem stress claim yet. Existing audio listening remains deferred; Delta UNTESTED.
4. **Town Map/Fly future interface:** real Sinnoh grid/art/cursor bounds and approved destination/heal rows are still missing. #138 intentionally refuses normal unsupported entry. Low-level protected `region_map.c`/debug/Pokédex area APIs remain outside these normal-entry guards; any deeper defense needs signed exact-path approval before editing. Claude should validate refusal/return paths graphically. Do not add synthetic art or destination IDs.
5. **No long-term save-format adoption:** grouped or 13-bit origins require a separate owner decision. #134/#141 are regression experiments only, not accepted format specifications.
6. **Claude-only next content:** #135 Route201 and #139 future junction/Route202 work are design proposals, not permission for section217, maps, encounters or story. Preserve Claude's C5 graphical QA files and original #133 nine-path approval scope.

Owner requested wrap-up during combined verification. Local verification completed successfully and all meaningful source work is pushed. No new assignment or extra retail build pair was started afterward. Latest #134 check history includes canceled superseded runs; its subsequent same-head native267/267 and applicable gates succeeded as recorded above. Do not mistake those earlier canceled jobs for a current source failure.

## Exact new native identities

- Averon extended location experiment preserves candidate bits across all 24 permutations PC and OT rekey
- Averon extended location experiment cannot infer a version from checksum-valid legacy unused bits
- Averon extended location experiment actual egg hatch replaces only the byte and retains stale candidate high bits
- Averon respawn contract rejects invalid script healer IDs before narrowing
- Averon respawn contract valid script anchors preserve the regional record
- Averon respawn contract healing alone preserves the previous respawn anchor
- Averon respawn contract unregistered arrival stays local without selecting a nurse
- Averon travel boundaries refusal preserves an already armed destination
- Averon travel boundaries indexed arrivals resolve the real map warp for Teleport and respawn
- Averon travel boundaries flash Continue preserves Sandgem origins PC and both badge banks
- Averon region map access refuses Fly from Sinnoh without an approved grid
- Averon region map access retains every legacy section and rejects explicit Sinnoh
- Averon region map access preserves legacy Fly map type restrictions
- Averon region map access wall map returns without replacing VBlank or allocating
- Averon region map access PokeNav refuses before changing or freeing the main menu
- Averon region map access PokeNav still schedules the legacy map feature
- Averon connection contract actual reciprocal boundary preserves party and region state
- Averon connection contract Sinnoh RAM header selects only overlapping signed offset edges
- Averon grouped origin experiment preserves all legacy bytes without modifying encryption
- Averon grouped origin experiment loses distinct runtime detail across real PC flash and summary

## Reproduction commands

From repository root, activate the configured ARM toolchain first (`. /workspace/.onboarding/activate.sh` in this workspace). For any submitted branch or the validation-only tree:

```sh
make -j4 -O -C 'Pokemon Game/engine' all > /tmp/averon-normal.log 2>&1
python3 'Pokemon Game/scripts/check-averon-resource-budget.py' --log /tmp/averon-normal.log --rom 'Pokemon Game/engine/pokeemerald.gba' --json /tmp/averon-normal-budget.json
make -j4 -O -C 'Pokemon Game/engine' RELEASE=1 all > /tmp/averon-release.log 2>&1
python3 'Pokemon Game/scripts/check-averon-resource-budget.py' --log /tmp/averon-release.log --rom 'Pokemon Game/engine/pokeemerald-release.gba' --json /tmp/averon-release-budget.json
python3 'Pokemon Game/scripts/report-averon-save-headroom.py' --elf 'Pokemon Game/engine/pokeemerald-release.elf' --json /tmp/averon-save-headroom.json
make -j4 -O -C 'Pokemon Game/engine' check TESTS=Averon ROMTEST=/workspace/.onboarding/mgba-rom-test > /tmp/averon-native.log 2>&1
ASAN_OPTIONS=detect_leaks=0 python3 'Pokemon Game/scripts/test-averon-healer-table-contract.py'
ASAN_OPTIONS=detect_leaks=0 python3 'Pokemon Game/scripts/test-averon-fly-destination-bounds.py' --include-dir 'Pokemon Game/engine/include' --mutations
```

The last two scripts require generated headers from a completed build. CI uses its bundled native runner rather than this workspace-specific absolute path. Use `gh workflow run averon-native-build.yml --ref <exact-pushed-branch>` when the local toolchain is unavailable. Inspect actual completed job logs/counts and attach textual evidence; a dispatched or green non-native gate alone is not native PASS.
