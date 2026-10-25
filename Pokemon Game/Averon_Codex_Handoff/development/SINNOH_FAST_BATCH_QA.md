# Sinnoh fast geographic development QA — opt-in, not a new acceptance gate

Effective for **new development work** after the owning agent finishes any frozen active ROM/emulator acceptance. Read root AGENTS.md, the current operating contract, Issue #15, and the original MAP-QA/ENGINE-QA requirements first. This document changes neither protected files nor final integration/merge requirements. Source-only is never equivalent to a playable map.

## Why / measured baseline

The accepted [#249 combined DEV scene](https://github.com/kioconnor24-sketch/PokemonGame/pull/249) has 18 actual emulator scenarios, 606 assertions, and ~2,476 seconds of execution **within recorded scenarios** (excluding builds, launch gaps and setup). ~2,220 seconds were full-map traversals. 354 assertions checked follower visibility or avatar foot/Surf state; many repeat after transitions. This does not prove those checks are useless or measure developer-hours.

The original Route222 two-ledges FAIL, Route221 duplicate seam, and invalid donor borders demonstrate that static/negative tests catch real defects. Conversely, Route216 snow bridge screenshots still show a white gap despite passing movement checks. Keep a separate *visual* status and preserve known-failure cases.

## Three explicit modes

1. **QUICK — during editing**: generate/reuse source packet and preview, run deterministic source/attribute/collision/warp/reachability/ledge checks, compare frozen dependencies. No ROM or runtime acceptance claim. `scripts/sinnoh_fast_batch_qa.py --mode quick static --engine E --map MAP_A [--map ...]` (from `Pokemon Game/`).
2. **BATCH — finished geographic batch, still DEV**: use the same guarded exact-source disposable ROM and existing native/build/save tests, then optionally invoke `scripts/sinnoh_fast_batch_qa.py --mode batch run ...` instead of the ordinary `map_qa.py run`. It performs one actual round trip per **unambiguous, unique reciprocal warp pair** (thus testing both directions), and samples follower state once per encountered map and static elevation. **Ambiguous/shared-return/unmatched/external warps remain individually tested**; distinct mechanics such as bike/Surf/ice, cliff, elevational transitions still need focused probes. Never substitute batch results for final acceptance.
3. **FINAL — before eligible permanent production integration**: use `scripts/sinnoh_fast_batch_qa.py --mode final run ...` or the original `scripts/claude_play/map_qa.py run ...` for unchanged full map QA. Complete source/negative/static checks, required native/legacy saves, NORMAL+RELEASE real linked builds, mGBA two-way traversal/followers, Save→fresh-process Continue, natural entry/whiteout where applicable, visual review, exact current-head CI, and all existing owner/protected-ID/review gates. A DEV fixture is not natural arrival or permanent production. **Neither QUICK nor BATCH changes the final contract.**

This opt-in helper does **not** automatically optimize bespoke `design/sinnoh/*/run_runtime_qa.py` wrappers, which may override `Runner`, add bespoke game mechanics and/or use custom mGBA launchers. Those paths remain unchanged until separately inspected and tested. If uncertain, use the full original runner.

## Work-reuse rule (development only)

If map payload, headers, banks, engine, dependent registry and ROM/ELF identities genuinely match previously finished proof, re-use that specific earlier result during **construction** and test only new/affected joins with explicit source hashes and known gaps. If any gameplay input changed, rebuild and run focused batch checks. No re-labeling an old result as acceptance for a different compiled scene; final acceptance is from the actual final source and both profiles. Run high-risk native/save/identity regressions regardless of perceived map-only scope.

## Visual and defect policy

- Source/quick checks must exercise all available static ledge landing, seam reciprocity, invalid metatile/border and one-way pocket checks. Keep the real Route222 corrected negative probes when Route222 is affected. Source tests include deliberately malformed fixtures.
- At least one inspectable in-game screenshot per **new** area/visual family and changed layering/elevation condition before calling graphics accepted. Preserve screenshots from every genuine failure; routine duplicate observation captures can be reduced on construction runs, but not by losing final visual evidence. White bridge gap in #235 remains FAIL/OPEN.
- A BATCH failure or unexpected setup outcome is logged honestly. Separate game/source failures from simulator socket, controller timing, source fixture and space/inode failures. Never change expected results or old goldens to manufacture green.
- When a bug is caught late: stop the affected lane, reproduce and fix the candidate on its owner branch, add a targeted fast static/native regression where possible, then rerun relevant final integration proof. Unaffected developers continue separate geographic files.

## Batch throughput and agent ownership

- Both Claude and Codex independently **build + source-test + finish their own connected physical-map batches**. Prefer approximately 5–10 maps when useful, not mandatory. Each picks new area from existing gap ledger; never reconstruct staged donor geography unless a verified need exists.
- Separate branches and literal path claims. No concurrent changes to shared `scripts/claude_play/map_qa.py`, `driver.py`, common registry, protected fields or another developer's in-flight ROM. One owner for shared engine-scratch/global registrar edits at a time.
- Before handing off, record each batch's map names, real geographic connections, source hashes, status by stage (SOURCE/STAGED/BUILT/BATCH-TESTED/FINAL-TESTED/PRODUCTION-INTEGRATED), gameplay gaps, visual status, and next ready batch. Use one concise final evidence summary, not repeated comment threads for individual assertions.
- Do not run legacy full M1 suite for routine geography absent demonstrated regression. Source/build preflight and existing exact required gates remain.
- Recheck whether QA optimizations are useful after 3 completed new batches: record Quick/Batch/Final wall times, launch/setup errors, unique physical defects detected, and escaped issues; revoke any optimization that misses a previously detectable consequential defect.

## Current ownership exceptions

Claude's active shared `scripts/claude_play/{map_qa,mapdata,driver,test_map_qa}.py` elevation fix stays his until merged/handed off. Codex's #248 frozen nine-map scene, `scripts/sinnoh-runtime-preflight.py`, and its source hashes remain undisturbed. The new root `scripts/sinnoh_fast_batch_qa.py` and focused test file are disjoint; the original runner and its tests are not edited here. This is not permission to invalidate an ongoing QA run or to rebase it during acceptance.
