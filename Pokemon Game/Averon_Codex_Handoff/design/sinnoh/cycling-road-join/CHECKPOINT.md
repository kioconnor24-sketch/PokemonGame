# W25 current-baseline DEV — tested checkpoint, 2026-10-27

Branch `codex/w25-current-runtime-20261027`, implementation source `195298e89cd9b8e8cfa21a704a6121e2ee731598`. Base main `eec3efd4b9e053583fff97855ab1aaf13a4df7cb`, engine tree `63d0c037e0da9a93b5e1a968c078d9622b56c691`; temporary 63-file engine tree `f77daade08932db37b617f1226575006072eaf0a`. Main subsequently appended only the #338 planning document. No production installer or engine change in this PR.

The read-only adapter preserves the accepted 30-map prefix, Gate B1F ladder/warp 1 and every existing layout, appending nine DEV maps. Temporary Gate east exit is warp 2 and City return matches it. Nine original donor seam pairs and source collision/elevation are retained. The old immutable recipes/native source are untouched.

## Actual evidence

- **187/187 host PASS** across 21 dependent modules, 100.375 seconds.
- **330/330 Averon-prefix native PASS**, no failures. This is not the full upstream/M1 suite. Initial run was 329 PASS / 1 FAIL: the generated Eterna test still expected legacy prefix 19 instead of 30. Correcting that generated expectation changed only test source; both linked ROM hashes remained identical.
- **NORMAL: 134/134 rendered controller checks + 3/3 fresh-process Continue PASS. RELEASE: 134/134 + 3/3 PASS.** Includes Gate B1F preservation, mine/City warps, directed seam traversal, followers, menus and genuine flash Save. A new process restored the game-written Mine B2F save at (15,2). Private input flash hash: `e00518cc30cf056813cc482f82d3c55c8a19ab5c9a2eecdd5d1641b6657a1963`; DEV entry Route207 slot 36 at (15,2).
- Source-aware muddy-slope observation: **4/4 additional NORMAL checks PASS**, three separate UP trials actually entered (18,15), then slid back to (18,16) after release. This resolves collision-vs-animation ambiguity; the earlier generic “blocked” label meant endpoint unchanged. Stock `ForcedMovement_MuddySlope` forces south below fastest northward speed. No bike acquisition or reciprocal uphill foot route is claimed.
- **Retained static finding:** Route207 has 54 directed south-to-north on-foot unreachable pairs. The earlier zero-finding result used the incomplete pre-mud planner and is superseded, not accepted. No collision was flattened and no portal checks were removed. The traversal order handles north ports before descending.
- Actual GCC 14.2.1 20241119, GNU Make 4.4.1, rendered mGBA SDL 0.10.5. CRIES=off both profiles; original cry sources, music and SFX remain untouched. Four earlier ARM syntax checks and real map-group generation passed; healing JSON stayed byte-identical.

| Profile | Linked ROM | EWRAM | IWRAM | ROM SHA256 |
| --- | ---: | ---: | ---: | --- |
| NORMAL | 17,493,976 B | 226,480 B | 28,392 B | `0a5ed3426b2dbfea6b6a1f65688a873e062dd207be22ee9f68cb619e923e21a3` |
| RELEASE | 17,613,096 B | 226,482 B | 28,336 B | `043d772e78e4f6c337ff58a691614235ddd2ba54f834193092459512b2ae95ad` |

Both padded ROMs are 33,554,432 B. Linked free ROM: NORMAL 16,060,456 B; RELEASE 15,941,336 B. No incremental growth claim against a matched 30-map baseline build.

Full native identities, check arrays, retained failures, source/ROM/flash hashes, memory measurements and reproducible mud observation are in `BUILD_AND_RUNTIME.json` at repository root `issues/evidence/w25-current-20261027/`. Two selected rendered screenshots accompany it. No ROM, ELF or private save is published.

## Failures and limitations

Original #317 traversal 32/34 was not accepted. Initial current-scene attempts failed on mud-uphill planning (6 PASS / 4 FAIL) and unsettled Route206 arrow approach (2 PASS / 1 FAIL). The shared on-foot mud rule, settled warp approach and stable traversal permutation fixed these demonstrated harness defects. Failed result hashes and checks remain in the evidence. A sparse-source dependency installation failure also caused an unintended baseline make; it was stopped, dependencies restored and subsequent installation made fail-fast. That interrupted baseline is not build evidence.

This is a **temporary 39-map DEV scene**, not production integration. Temporary section 217 names are aliases (including the Mine popup), not approved new identities. Controller traversal samples first/middle/last seam lanes, not every lane. No story, natural whiteout, ordinary bike acquisition, human audio or Delta acceptance. Old 44-map DEV flash was not reused.

## Next executable work

Finish source/evidence review and applicable checks for #317/#336; do not merge production geography from this proof. Keep #339's seven-map Stark recovery separate for independent asset/source review. Correct #337's section-227 native expectation on a separate Codex branch while preserving Claude's branch and claimed files. Production packet C still needs genuine exact-path owner handoffs and final-head acceptance; no IDs 228+ or save migration is approved. Then address coherent Frontier terrain findings without hiding the retained 32 findings.
