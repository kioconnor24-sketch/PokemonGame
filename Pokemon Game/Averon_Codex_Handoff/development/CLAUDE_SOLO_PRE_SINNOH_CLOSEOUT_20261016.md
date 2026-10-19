> **ARCHIVED PROCESS / SNAPSHOT — superseded 2026-10-18.** Use the [single operating contract](CURRENT_PHASE_AND_HANDOFF.md), [integration queue](INTEGRATION_QUEUE.md) and [#15 live claims](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). All prior “current”, “authoritative”, pause, freeze, manager-only and resume commands below are historical. Retained evidence and approved product constraints are preserved; this file grants no new work or content approval.

---

# POKÉMON AVERON — CLAUDE SOLO PRE-SINNOH CLOSEOUT / INTEGRATION RUNBOOK
**Owner-directed working handoff, October 16, 2026.** **Start implementing and integrating immediately.** This is a new coordination note on a separate documentation PR, not proof that any software feature is merged. **Fresh GitHub Issue #15 exact claims, the current main SHA, current changed-file lists/reviews/checks and #46 acceptance outrank every snapshot in this file.**

## 0. The deliverable and what “done” means

**Objective:** Finish the entire *safe, reasonably map-independent* pre-Sinnoh engineering backlog, integrate verified functionality into main, and deliver a real, tested GBA build that is safe to begin producing the playable Averon pre-Sinnoh story/region on. Do not prolong this milestone with indefinite speculative audits. After it, remaining new geography, canon teams, placement, story and graphical post-map tests become part of actual world production rather than excuses to delay it. Finishing this engineering milestone is **not** the same as finishing a playable Averon or Sinnoh campaign, nor permission to generate new maps.

Source of truth: [#15 active ownership/dashboard](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [#46 completion gates](https://github.com/kioconnor24-sketch/PokemonGame/issues/46), [#53 implementation backlog](https://github.com/kioconnor24-sketch/PokemonGame/issues/53), [#54 prior Codex handoffs](https://github.com/kioconnor24-sketch/PokemonGame/issues/54), [#55 actual agent blockers](https://github.com/kioconnor24-sketch/PokemonGame/issues/55), [#23 independent graphical QA](https://github.com/kioconnor24-sketch/PokemonGame/issues/23), and [#62 manager integration routing](https://github.com/kioconnor24-sketch/PokemonGame/pull/62).

### Owner-delegated operational authority — with real safety boundaries

The owner explicitly authorizes **Claude to take primary responsibility for all remaining pre-Sinnoh implementation and normal integration**, including claiming newly released file scopes, creating branches/PRs, reviewing evidence, repairing legitimate merge conflicts, refreshing stacked branches, running native/ARM/release tests, and merging PRs **when actual repository permissions, required independent review, protected-file authorization, source ownership, accepted graphical QA, and exact-head checks permit**. Routine implementation and normal eligible merges **do not require repeated conversational approval**. Do not mistake a GitHub comment from ChatGPT for the human owner's identity or a valid protected-path handoff. Do not self-review to imitate a required independent approver, disable checks, forge reviewer/Playtest signoff, force a broken main merge or resolve collision by hiding source conflicts. GitHub permission/rules cannot be overridden by prose.

**Claude is accountable for finishing the technical backlog even if Codex/Manager are inactive.** Playtest #20/#23 remains the authoritative independent graphical verifier; Claude may assist, reproduce or add honest screenshot artifacts in unclaimed paths, but must not certify its own unresolved graphical gates as independently accepted. If another Claude scheduled/manual session still owns a branch, coordinate through current remote head/claim and **never simultaneously overwrite that branch**. If a branch/file is occupied, claim a genuinely disjoint task immediately.

**Project invariants remain in force:** no new production or temporary maps/map fixtures, unapproved Sinnoh maps, plot or dialogue, art/music, trainer teams, canonical legendary placements, saved ID allocations, numerical final Sinnoh cap curve, or automatic lifting of the world-production freeze. Use symbolic values, existing unchanged maps, parameterized tests and original source. Keep original Gen 5 **held-item** EXP Share (not party-wide); mandatory Set-style/no free switch, level 100 maximum, allowed Mega Evolution, no Z-Moves/Dynamax/Terastallization/Primal gameplay.

## 1. Current verified baseline — refresh before running

At writing, main is **7f4ecc44270e98b2363fc49cb708aa4d9a3527fa**. **None** of the following open development PRs is merged into main. The owner wants results, not another plan.

| PR | Snapshot head | Disposition/remaining action |
| --- | --- | --- |
| [#50](https://github.com/kioconnor24-sketch/PokemonGame/pull/50) save-sector bounds | 3c9d43de89 | Reviewed-safe candidate; no independent submitted review at snapshot. Merge first through existing protected gate. |
| [#51](https://github.com/kioconnor24-sketch/PokemonGame/pull/51) off-stack Fly fixture | 1ba7bf9cf2 | Verified test-only repair; merge second. |
| [#52](https://github.com/kioconnor24-sketch/PokemonGame/pull/52) Fly destination bounds | 476ba941c6 | Verified bounds repair; protected path; merge third. |
| [#56](https://github.com/kioconnor24-sketch/PokemonGame/pull/56) two-region flash/save | 2f4dba7bf3 | Tested, **DRAFT, failed exclusive-files due to overlapping earlier safety PRs**; needs branch integration, real owner-specific protected approval, peer review. |
| [#61](https://github.com/kioconnor24-sketch/PokemonGame/pull/61) save-entry pathways | 78b5ed44df | DRAFT, stacked on #56; real HoF/link/overwrite and power-cut tests; integrate after base. |
| [#57](https://github.com/kioconnor24-sketch/PokemonGame/pull/57) reversible region travel | 5ce9301e93 | DRAFT, stacked on #56; linked script special; merge after #56. |
| [#64](https://github.com/kioconnor24-sketch/PokemonGame/pull/64) region caps/obedience/badge rules | 10de349770 | DRAFT, stacked on #57; parameterized regional selection and genuine battle tests; owner-specific policy remains unset. |
| [#48](https://github.com/kioconnor24-sketch/PokemonGame/pull/48) Pokémon readiness and held-item repair | 7f2446009c | Review-ready, no longer draft; includes real held-item fix and broad Gen 1–9 tests. |
| [#47](https://github.com/kioconnor24-sketch/PokemonGame/pull/47) unique LEGEND state | cf2a1aaf35 | Review-ready core, not event-registered; macro registration must respect #14/#25 event_scripts overlap. |
| [#14](https://github.com/kioconnor24-sketch/PokemonGame/pull/14) QUEST | db6baaea45 | DRAFT: genuine independent [#20/#23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23) Q1–Q5 gameplay QA incomplete. |
| [#25](https://github.com/kioconnor24-sketch/PokemonGame/pull/25) SCRIPTED BATTLE | 456bd035a2 | DRAFT: finish real config/registry/no-whiteout/no-Run cleanup **after #14 owns and lands shared event_scripts.s**; no canon trainer content. |
| [#58](https://github.com/kioconnor24-sketch/PokemonGame/pull/58) production config parity | 4331c99007 | Review-ready: 432 host assertions, 23 deliberate mutations; verify current CI, merge independently. |
| [#60](https://github.com/kioconnor24-sketch/PokemonGame/pull/60) PC/Bag transactions | 5ead8c826e | Review-ready: four new actual PC tests, head evidence +51/51 Averon native; merge independently. |
| [#63](https://github.com/kioconnor24-sketch/PokemonGame/pull/63) map registry/capacity | 2e3a5c1305 | Review-ready: signed map slots, 951 fixed IDs/76 groups/534 linked maps, native/GBA/source mutations; merge independently. |
| [#18](https://github.com/kioconnor24-sketch/PokemonGame/pull/18) tools | f6a45b732d | Review-ready documentation/tooling; verify diff and merge if compatible. |
| [#59](https://github.com/kioconnor24-sketch/PokemonGame/pull/59) auto-board authority | 13b4251075 | Review-ready, makes generated #31 historical; normal review then merge. |
| [#62](https://github.com/kioconnor24-sketch/PokemonGame/pull/62) integration routing | a80e392a40 | Advisory docs; merge if reviewed and still current, refresh old SHA labels before reuse. |
| [#20](https://github.com/kioconnor24-sketch/PokemonGame/pull/20) graphical QA | e46beacf00 | DRAFT on #14 branch, not production code; its isolated evidence must be judged per case before #14 can merge. |

**Test anchor, NOT a real merge:** Claude combined rehearsal [#15 checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6221013804) built #14+#25+#47+#48+#61+#64 together with **200/200 Averon checks and 6,065 full tests (327 recognized baseline failures)**, real GBA build with no C warnings, zero source conflicts. It excluded later modifications and does not imply main integration, release gameplay, Delta, or QA acceptance. Never cite a stale aggregate as latest exact-head green. The baseline 327 failures are acceptable **only if the baseline checker verifies they are the same known failures; any novel fail is blocking**.

## 2. First critical path: actually integrate the safety and two-region stacks

**P0.1 — land #50 -> #51 -> #52 on main by normal reviewed merges.**
- Refresh each open PR's exact head, changed-file list, approvals, source guard, ARM/native tests, and compare accepted patches against the same commits already stacked on #56. Source paths: #50 engine/src/save.c plus separate test/script; #51 test-only Fly fixture; #52 engine/src/region_map.c plus test/script.
- Their patches are already present (unchanged cherry-picks) on the #56 parent stack. **No duplication.** Historical approved protected handoffs for #50 and #52 are [#15 owner comment 6209610910](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6209610910).
- The exclusive file gate currently flags #50/#52 against open #56 even when existing handoffs exist. **Fix the sequencing as a legitimate review/branch-ownership transition, not by disabling/dodging the guard.** Reproduce actual current gate behavior and obtain a reviewable nonoverlapping serial diff or explicit supersession of byte-identical commits consistent with repo policy. Have the integrator coordinate a short quiet window on shared save/map files; no conflicting Claude branch writers.
- For each merge: source/diff review by permitted reviewer, all required checks green at exact head, human/protected authorization as applicable, merge normally through GitHub, re-read main SHA. If GitHub refuses a guarded merge, post **one exact blocker and a workable non-bypass next step**, then continue disjoint work; don't wait idle.

**P0.2 — bring #56 region save onto updated main.**
- After the accepted #50/#51/#52 changes really enter main, merge main into the #56 branch (no force push). [Rehearsal](https://github.com/kioconnor24-sketch/PokemonGame/pull/56#issuecomment-6221166981) found an identical resulting tree and a reduced diff (not proof it will remain so); verify live heads, source hash, and re-run checks.
- Guarantee exactly one source implementation of sector guards; the refreshed feature PR must not pretend to introduce #50/#52 independently. Review new region-save fields/layout, old-game SaveBlock1/2 compatibility, anchor/CRC/counter validation, correct slot selection, never mixed slot copies, old save migration, bad signatures, newer-format refusal without ANY destructive write including special sectors/save-failed wipe, SaveBlock3/test pin, and resource footprint.
- Re-run focused save suite incl. flash save/load, 512+64 single bit flips with valid physical checksums, semantics, stale tail, each 14-sector write/rotation, interruptions and 15+ additional mutations. #56 later reported 17/17 save tests, 15/15 original mutations + 4/4 newer-save refusal guards killed; check actual latest branch results and run full baseline. Confirm no hidden C warnings and real ARM build.
- **Authorization:** owner has delegated normal merges here, but the guard may require a distinct GitHub comment from the **real owner account** in Issue #15, not a manager impersonation. **Required requested line (exact scope, subject to changed-file verification):**
  HANDOFF_APPROVED PR=#56 PATHS=Pokemon Game/engine/include/global.h, Pokemon Game/engine/src/save.c, Pokemon Game/engine/src/new_game.c, Pokemon Game/engine/test/save.c
  Verify exact guard path list after #50–#52; ask owner for this one GitHub posting if unfulfilled. Never forge it or weaken the check. After green checks and real review, merge #56 normally.

**P0.3 — merge #61 without losing its real test coverage.**
- Its existing four native cases test SAVE_HALL_OF_FAME, SAVE_OVERWRITE_DIFFERENT_FILE, SAVE_LINK in-place slot revision, and interruptions at 24 boundaries. It reported 18/18 focused and 80/80 Averon at the branch; mutation showed deferred signature ordering prevents mixed state.
- Refresh #61's base to merged #56; keep its unique test file once; verify parent commits are not replayed as duplicates, re-run branch tests and normal PR review, then merge. State deliberate one-save rollback on power loss; do not falsely promise last-written data always survives.

**P0.4 — merge #57, preserving linked callable travel.**
- Validate script registration in data/specials.inc so the real GBA executable retains the travel native and its script entry, not just a host test. Existing 7/7 focused covers return, invalid inputs, heal/whiteout/Teleport/Escape Rope, full flash roundtrip, every-sector power interruption and real native script execution.
- Use symbolic stand-in coordinates on unchanged maps. No actual Sinnoh NPC/warps/landings may be created until map approval. After refreshing the parent, merge normally and recheck ELF linkage.

**P0.5 — merge #64 region progression, then resolve policy separately.**
- Has independently stored Averon and Sinnoh badge banks from #56, and cap/obedience selector integrated into real caps.c/battle_util.c; later changes route actual whiteout money, missing-badge catch penalty, and Flash via a three-way badge policy. Confirm latest 11/11 focused, 98/98 Averon, mutation kills and full native baseline, real GBA and resource headroom after merge from #57.
- Do not invent final 0–8 Sinnoh gym cap/obedience values. A missing numerical profile stays explicit **OWNER-DESIGN PENDING** with conservative unchanged behavior, and cannot stop testing/merging the reusable parameterized engine if otherwise safe.
- **Proposed policy for later owner approval, not silently canonical:** ACTIVE_REGION for badge-dependent money/catch/Flash is geographically coherent. Other possibilities AVERON or EITHER are already tested. Do not change default without a clear owner decision. Badge UI/menu/shop/rematches must be inventoried as verified existing, intentionally global, needs fix, or post-map; no hiding those edge cases.
- Do not allocate new badge flags; the existing regional save record controls the second bank.

## 3. Independent ready-to-integrate PRs — get them out of the queue now

**P0.6:** In parallel to the protected save sequence, properly review/merge clean, released, disjoint #58 (release config parity), #60 (PC transactions), #63 (map registry capacity), #59 (stale generated board), #18 (tools) and #62 (routing docs), **only after exact-head CI and required review**. They do not need to wait for new maps or Sinnoh cap numbers. Check whether #18 tooling PR touches live workflow/guidance and whether its stale instructions conflict with Issue #15 before merge. Update superseded docs on a later claimed diff, not by rewriting other branches mid-review.

**P0.7:** #48 Pokémon readiness is review-ready and contains an actual battle held-item restoration source repair. Make sure its change to battle_util.c does not overwrite the #64 obedience selector; the combined rehearsal auto-merged at its historical heads but verify newer heads. Enforce original held Gen 5 EXP Share and no party-wide effect, Set style, Mega eligibility/reversion, national dex persistence, breed/evolution/forms/growth to 100, trainer item return/no theft duplication, follower lifecycle, release/debug parity, wild/whiteout/TM interfaces, RAM budget. Existing #48 latest notes report 110/110 Averon tests at its head. Merge the verified core without waiting for the future placement of a Mega Ring or 13 ecological evolution acquisition methods, which are **owner-content or post-map** unless generic engine bug is proven.

**P0.8:** #47 LEGEND is review-ready as generic encounter-state library (15/15 focused tests; real capture/flash/follower outcome test). Its captured/defeated/flee/Teleport/Whirlwind/retry semantics can be merged without naming a legendary, new flags, or an encounter. A separate production event registration in data/event_scripts.s is needed before game scripts can call macros, and **must be serialized with #14 then #25**. The later #47 protected-path approval must be provided by the real owner if required:
  HANDOFF_APPROVED PR=#47 PATHS=Pokemon Game/engine/data/event_scripts.s
  Only request/apply this to an actually scoped registration PR/change after current #14 and #25 event-script diffs are resolved; do not add fake events to make this pass. Full-party captured-Pokémon swap menu is graphical, not a headless PASS.

## 4. QUEST: finish actual player-facing Q1–Q5 rather than wait forever

**P0.9 — #14 game source + Playtest #20/#23 independent evidence.** #14 native/source checks had 49/49 Averon, 4/4 save layout and a genuine ARM build. The first scope of original Q1 researcher, Q2 artist/berry tree, Q4 Wobbuffet gift, Q5 field input has substantial GUI proof. **This does NOT equal complete Q1–Q5.**

Required outstanding real/gameplay cases:
1. **Q1 researcher/Hiker/first badge:** already proved NO Badge01 gate rejects and backs player off. Legally earn Badge01 in the original Gym, traverse existing route, accept/deny/reoffer the Hiker branch, give reward exactly once, persist state across honest save/load, including full Bag retry. No debug-set badge/inventory as supposed visual acceptance.
2. **Q2 artist/tree/three Oran:** original observation/claim/no-duplicate already observed; genuine SAVE -> exit -> fresh emulator -> CONTINUE showed the berries and DONE text, and raw flash item/state reported independently. Still verify full BERRIES pocket rejected then recover legitimately, status flags and no accidental duplication.
3. **Q3 gym/whiteout:** actual ordinary Elio trainer loss from a genuine lv5 Wobbuffet, the 40-money loss, no Badge01, unchanged quest flags and home whiteout was already independently observed in [run 38932180353](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38932180353). **Clinic setrespawn, healing, subsequent control and full battle return remain unverified**, next QA run noted in [#23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23). Check its current result; do not repeat completed Gym loss solely to accumulate logs.
4. **Q4 lab gift:** actual refusal -> YES -> one real Wobbuffet -> duplicate denied and following Pokémon on original maps observed. Still needs legitimate party-six/full-party retry, real save/Continue gift persistence and menu behavior.
5. **Q5:** ordinary controls after quest/gift, follower lifecycle across battle/warp/surf/entrance, sound if the runner can genuinely observe it, restart recovery, no stuck movement/text; don't mark audio PASS from screenshots or synthetic files.
6. **Failure handling:** distinguish automation input/GDB/emulator debugger limitations from actual production-game defects. Do not weaken QA or mutate gameplay state to construct convenient screenshots.

If Playtest continues running, **Claude must not overwrite #20 files**. If Playtest is inactive, Claude may develop on new, exclusively claimed QA-support paths and gather evidence, but **independent graphical acceptance is still needed** before declaring Q1–Q5 accepted or merging protected QUEST gameplay through a mandatory QA gate. Owner's delegation to Claude does not magically constitute Playtest signoff. If full rewards genuinely require world content not available, label that exact case POST-MAP with evidence and request the owner for a scope decision; do not invent a location.

**P0.10 — merge #14 when, and only when, the required independent case-specific QA and normal gates pass.** After merging #14, re-evaluate all #25 event_scripts.s changes against the merged file; no concurrent edits from two PRs.

## 5. SCRIPTED-BATTLE core #25 — finish code only, never invent scripted story events

**P0.11:** #25 has safe-loss helpers and tests but still needs the real runtime configuration and script registry integration. Specifically:
- Finish the engine-approved temporary B_FLAG_NO_WHITEOUT special RAM flag in include/config/battle.h (FLAG_SPECIAL_FLAG_UNUSED_0x4003), and test ordinary trainer Run remains restricted appropriately while scripted special fights can enforce no Run as designed.
- Register data/scripts/averon_scripted_battle.inc in event_scripts.s **after #14** is merged; ensure exactly one registration and no missing symbols. Existing owner handoff covers two protected files on original #25 at [#15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6209610910), but review current path names and latest guard.
- Test scripted victory, scripted safe defeat, interrupted battle/draw, repeated battles/cleanup, save/reset preserving normal rules, HP/status/currency/badges/party and ally heal boundary. No accidental saved no-whiteout leak. Validate real in-game fallbacks using original unchanged maps when reachable.
- **Do not implement Renn, corrupt gym leaders, operatives, ambush scenes or trainer.party teams now**: their identities/scenes/teams are owner-approved story/map production work, not a requirement to finish the generic scripted-battle API.
- Actual graphical acceptance of an accessible generic scripted battle is desirable; do not invent that it happened if no approved in-game caller yet.

## 6. Remaining platform, item/field, interfaces and safety

**P1.1 — item/storage:** merge #60 and cross-check PC deposit overflow/retry, partial removal/compaction, Bag encryption rotation and field gift/full bag/party responses with #14 and region save. A native interface pass cannot stand in for actual GUI PC/full-party swap gameplay. Audit menu bugs **only when reproduced**.

**P1.2 — map registry and scalability:** merge #63. Validate stable existing map IDs, group and signed-byte limits, generator/ELF alignment and future two-region capacity. It reports 951 pinned IDs, 76 groups and 534 linked maps, 10/10 mutations, 50/50 Averon native and real GBA build. This is **not permission to create maps** and not a claim every future region layout fits; record actual map-only constraints for later.

**P1.3 — field moves:** existing Fly section bounds fixed by #52; audit active-region badge/field license/Flash, warp/respawn, Dig/Escape Rope, Surf, weather/time, map transitions and whiteout fallback. Do not manufacture Sinnoh Fly locations. Mark actual region-map UI and physical landing verification POST-MAP; ensure code can accept them without corrupting saved warps.

**P1.4 — Pokémon species/evolution:** preserve all existing Gen 1–9 species/form/learnset/follower/dex persistence checks and actual Mega restrictions. #48 documents **174 fallback follower sprites out of 3,142 lookups** and **13 species/form evolutions with unavailable Averon trigger routes**, plus graphical follower gaps. These are asset/world-placement design gates, **not a reason to invent 174 sprites or 13 placement rules in backend closeout**. Confirm mechanically supported routes; report honest coverage and post-map plan.

**P1.5 — release config/battle rules:** enforce no debug release, test vs production differences, Gen 5 held EXP Share, hard level 100, EXP caps, Set mode, Mega yes, excluded gimmicks no. #58 catches 23/23 deliberate production probe faults. Gen 5 EXP details **not specified by just “held-item EXP Share”** need owner decision: trainer 1.5×, unevolved 1.2×, EXP on capture; keep documented current behavior or a clearly reversible config instead of guessing if not blocking the game.

**P1.6 — audio/assets/capacity:** verify real linked and padded ROM <=32 MiB, actual IWRAM/EWRAM/flash headroom and save sector packing under merged code. Prior snapshot showed roughly 80% ROM and mid-80% IWRAM/EWRAM usage, not unlimited second-region art budget. Check practical compression/import pipeline and document risks without importing unapproved copyrighted assets. Build clean owner-local GBA + test manifest; actual iOS Delta gameplay remains separate verification.

**P1.7 — final cross-feature test combinations:** after main advances, fresh main (not local draft stack) must pass:
- #14 quest rewards + #25 script recovery + #47 legend capture/retry + #48 held item/EXP/Mega/follower/party;
- #56 regional save with #61 link/HoF/overwrite + #57 travel + #64 badge/cap/field + #60 PC transaction, including old-save and repeated interrupted flash cycles;
- #63 map identity + #52 Fly bounds + region-return/warp compatibility;
- native FULL suite with exact known-failure baseline, normal and release ARM builds, real emulator boot and independently evidenced reachable-world controls/save/Continue. No silent skipped tests or phantom zero tests.
- Keep test binary/ROM/save private; never upload copyrighted ROM or user save files.

## 7. Owner-only game-design choices — DO NOT turn these into broad work stoppages

These choices are genuine remaining *decisions*, not permission to invent canon. The owner has approved routine engineering/merging, **not specific values/placements or bypass of branch protections**.

1. #64: **nine numeric Sinnoh level caps and nine obedience values** indexed by 0–8 Sinnoh badges, each 1–100. Leave an empty validated profile with a documented safe fallback until owner decides; the generic selector must still be integrated/tested.
2. #64: badge counting for whiteout money, catch penalty and Flash: AVERON (existing default) vs ACTIVE_REGION (geographically intuitive recommendation) vs EITHER. All three tested. Do not silently choose a canon rule; leave safe default until owner picks. UI/rematch/shop badge logic must be documented, not falsely claimed switched.
3. #48: trainer EXP 1.5× on/off; unevolved 1.2× on/off; EXP on capture on/off. The locked requirement is the **held Gen 5 EXP Share**, not necessarily every other Gen 5 EXP feature. Preserve existing options pending decision.
4. Mega Ring acquisition: where the player obtains it, required by release code. POST-MAP/OWNER-CONTENT placement; battle behavior can be verified with a legal test item.
5. 13 region- or map-dependent evolution routes need eventual gift/wild/trade/region rules, not arbitrary backend placements.
6. Unsupported/newer-format save UX (currently error/erased wording) must be documented as a player-facing concern; engine must prioritize **never damaging** the newer save. Request wording/UX if needed; do not weaken safety to improve aesthetics.
7. Exact GitHub owner-authored protected approvals for #56 and, later, #47 event registry may remain required even though owner delegated routine merges in chat. **Do not forge owner's issue authorship or disable guards**. Ask the owner to post the exact scoped approvals only once when all paths are verified.
8. **Lifting map freeze** is a separate explicit owner decision after a gameplay-ready checkpoint. Generic backend completion cannot authorize a new map automatically.

## 8. No-wait solo execution loop and stop criteria

For EACH work session (including scheduled Claude cloud sessions):
1. Fetch current main SHA, newest Issue #15 claims, open PR list with changed paths/base/head, required review/CI state, and the immediately relevant handoff. Only then select the **single next executable item** from P0.1 through P1.7; do not restart from the top on every run.
2. Check another Claude/manual/scheduled session's recent commits and its exact branch/file claims. If active, stay off its paths. If there's a verified handoff/released claim, explicitly claim before changing. No concurrent writes to shared branches or mutable test files.
3. Do real work now: smallest source fix, rebase/merge-once diff, honest independent review, new negative test, actual ARM/native/flash check, or run real graphical test if available. Work on a meaningful unblocked P0/P1 item even while waiting on a different required merge.
4. Push a recoverable commit/PR; check the remote head/CI. Never claim tests passed merely because a script printed counts from a stale branch. Preserve owner-approved design, fixed flags, save compatibility, and source ownership.
5. When exact-head checks, legitimate required independent review, human protected authorization and genuine QA are satisfied, **Claude may perform the normal GitHub merge without asking the user again**, then record merged SHA/main SHA. A read-only test report never substitutes for merge. For ineligible PRs, keep them open/draft and route ONE exact request with a safe concurrent fallback.
6. Publish a *short actual checkpoint* to the owning PR and #15 only when meaningful: [merged PR/main SHA or new source branch SHA] + [tested exact command, positive/failed/skipped counts] + [remaining real gate] + [next test/PR]. Do not add endless tasks/coordination commentary.
7. Stop work only for actual exhaustion of all currently legal, feasible technical tasks, lack of tools, or a genuine required human/independent QA decision with no disjoint alternatives. Then leave a concise reproducible handoff. **GitHub comments do not launch Claude; the user must start its session/scheduled cloud runner.**

### Completion certificate — honest exit to playable Averon production

Claude must deliver a source-backed matrix with one row for each #46 category: **INTEGRATED+TESTED / VERIFIED EXISTING / OWNER-CONTENT LATER / STRICT POST-MAP TEST / STILL OPEN DEFECT**, with merged SHA and actual passing tests. Deliver:
- main on new integrated SHA(s), no critical save/switch/whiteout/level/EXP/held-item regressions;
- reproducible real ARM normal/release game build <=32 MiB + native expected-failure baseline + flash save/power-cut safety + mGBA boot;
- independently corroborated Q1–Q5 gameplay acceptance for existing reachable cases, or an explicit unsatisfied gate requiring continued work—**do not declare full QA accepted if not**;
- player-facing pre-Sinnoh readiness status; honest owner-only pending profile/locations/map UX and strictly post-map validation list;
- all critical PRs either merged/accepted or precisely explained as owner-blocked, never simply forgotten.

**The next phase is playable Averon development**, not magically completed Sinnoh. Do not include generation of new region maps, trainers, full campaign, final balancing, Delta full release or final story in this “closeout” job. The owner may decide that sufficiently tested gameplay-ready backend (rather than absolute #46 coverage) is enough to authorize map production, but Claude cannot silently redefine that threshold or lift the freeze.
