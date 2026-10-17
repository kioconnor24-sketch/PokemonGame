# POKÉMON AVERON — EXHAUSTIVE REMAINING PRE-SINNOH M1 WORK
**Last GitHub inspection:** 2026-10-17, baseline main \`27f91919d4872faa4cc719309e8beb22ad80ea34\`. **Sole assigned active executor: Claude Code.** This document is the prioritized, executable acceptance checklist. Check current GitHub first: PRs, source commits, CI and developer evidence may advance while it is being read. Mark tasks completed only when evidence actually supports completion. **The owner has not yet accepted M1 as finished.**

## Rules of interpretation: protect time and accuracy

- **This is the remaining M1 map-independent/backend plus existing-approved-map testing gate, not the complete game.** Averon and Sinnoh map production, real Sinnoh destinations/Gyms/wild ecology, new canon/rosters/dialogue, final Pokédex encounter placement, custom graphics/music, Sinnoh gameplay, full campaign, Cynthia/Red and full Delta iOS release are reserved for approved content later. These are **POST-CONTENT**, not M1 failures. Sinnoh remains second in story even though its maps may be produced first after M1.
- **Already merged and NOT tasks:** QUEST #14 / Gate A (merge \`bcfeb28d\`); scripted+legend macro registration #25 (merge \`0a3a3552\`); whiteout/follower native #95 (merge \`7b194ac8\`); Pokémon delivery original-trainer key fix #96 (merge \`9e410fed\`). Likewise #48, #77, #81, #89, #90–#94 and older regional/save/Fly work need **verification**, not recreation. A registered macro is not a playable story scene.
- Claude has owner-delegated coding, QA verdict, separate read-only review, issue/PR handling and *eligible ordinary merges*, via merged PR #98. **Not** permission to waive source protections, force-push shared history, turn expected failures into passes or bypass Auto-mode command denials. GitHub's actual permissions must permit each write. A blocked command does not block independent development.
- Never upload private ROM/ELF/\`.sav\`, proprietary assets, tokens or personal files. Source code, test scripts and appropriately sanitized PNG/JSON/audio/trace **evidence** are permitted with provenance. Do not mutate memory, badges, Pokémon, inventory or save bytes to pass a claimed **natural** playthrough; developer-only fixture paths must be disclosed.
- Do not create a new generalized framework/test merely because a feature has a historical unchecked checkbox. First locate the *actual current* production caller, matching merged tests and existing successful proof. Classify each checklist item as **VERIFIED CURRENT MAIN**, **REPRODUCED DEFECT / FIX OPEN**, **REAL GRAPHICAL QA OPEN**, **SOURCE/TEST PROOF MISSING**, **POST-CONTENT**, or **OWNER DECISION**. A passed configuration or isolated branch is not itself installed-playable proof.
- **No extra gate from a paused agent:** Codex, former separate Playtest and ChatGPT Manager are paused. For each graphical case Claude can record a truthful verdict **after an explicitly distinct read-only adversarial review**, preferably a clean reviewer subprocess/subagent. Do not imply independent third-party approval.

## Snapshot: what is truly outstanding right now

| Area | Verified status on inspection | Exact remaining work |
| --- | --- | --- |
| Repo integration #14/#25/#95/#96 | **DONE and merged** | Source-pinned final combined regression only, no redo |
| [#97](https://github.com/kioconnor24-sketch/PokemonGame/pull/97) local real-mGBA driver | Open **draft**; latest inspected head \`eef446bb420848500dd69f9fdfad655a0b44f263\`. New commit says debug-PC deposit navigation helper is implemented; GitHub file/source checks green | Run actual deposit/gift scenario, finalize source/offline tests, independent review, normal merge; close **tooling** separately from gameplay evidence |
| Gym1/Badge01 | Claude reports natural Elio win **run17** on older ROM, with trainer-card/save badge screenshots | Preserve source/picture/provenance; validate save compatibility on current ROM; distinct QA review, not automatic replay |
| Q1 researcher→Hiker | Claude reports real \`0→2\` Great Balls, repeat \`2\`, Save→fresh Continue (**runs18–19**) on #14 merged ROM | Evidence bundle/reviewer; **full Balls pocket refusal→space→retry** still to test |
| Q2 sketch→Oran | Claude reports normal **walking** (not warp) to boy/tree/artist, \`0→3\` Oran, nonduplication, Save (**run20**). Older warp-transport CI positive Save→Continue is already accepted only for Gate A | Evidence bundle/reviewer; confirm natural-run Continue if required; **full Berries pocket refusal→space→retry** still to test |
| Q3 whiteout | Previous real emulator CI [run 38996685926](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38996685926) supports Elio loss→whiteout→nurse→clinic SAVE→fresh CONTINUE; party HP probe absent. Claude's newer deliberate-loss phase exists in driver | Execute current-source loss/clinic/HP/PP/status/follower/in-game SAVE/fresh Continue; exact screenshots and separate review |
| Q4 full party gift | Claude reports six legitimately captured team and **dev-only lab** party-full refusal (**run21**, copy of save) | Actually execute working debug-PC deposit helper through ordinary controls; one-time Wobbuffet gift + negative repeat, party/PC/BAG/flag, Save/Continue; label **DEV FIXTURE** |
| Q5 usable overworld | No complete case; title-music WAV alone is not gameplay-audio acceptance | Live movement/collision, NPC/dialogue, menus/controls, follower and game audio with no softlock |
| [#20](https://github.com/kioconnor24-sketch/PokemonGame/pull/20) + [#71](https://github.com/kioconnor24-sketch/PokemonGame/pull/71) | Both still open on very old stacked bases; ~114/118 commits ahead and 278 behind main at earlier comparison | Carefully transplant only needed QA source to fresh main-based Claude-owned branch, fix GDB title interrupt error, test and close/supersede stack accurately |
| [#100](https://github.com/kioconnor24-sketch/PokemonGame/issues/100) egg/battle OT integrity | **Source-level hazard, NOT demonstrated Bad Egg**; #96 fixed delivery only | Real foreign-OT egg native RED/control, narrow fix only if reproduced, battle caller risk investigation |
| Final complete M1 native / release / resources | Claude reports earlier local composite \`5,330 pass / 327 expected-fail\`, normal and RELEASE built; that result was **before final merged current-main verification** | Re-run once on final integrated main, compare exact baseline identities, rebuild normal/RELEASE, flash+asset+memory budgets and final evidence/report |

**Claude's precise latest file claims** ([Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15)): \`claude/local-playthrough\` owns \`Pokemon Game/scripts/claude_play/**\`; proposed \`claude/qa-evidence-m1\` stores sanitized evidence only; proposed \`claude/qa-stack-on-main\` owns old #20/#71 QA scripts and workflow; \`claude/egg-hatch-ot\` owns new egg test and \`src/egg_hatch.c\` **only if real RED**. These are **claims**, not proof the branches have already been pushed. Avoid overlapping those files.

---

## P0 — Finish and substantiate Q1–Q5 Gate B gameplay in real mGBA

Use the **same backed-up legitimate save chain**, current approved existing maps, ordinary controller keys, read-only game-state probes and a consistent source→ELF→ROM provenance manifest. Game-state observations need visual/UI corroboration; don't derive PASS from a label or workflow completion alone. Keep a separate copy for dev fixture Q4; don't contaminate natural-run save.

### B0 — Evidence infrastructure, without redoing already-played positives

- [ ] Preserve exact run17–run21 inputs, readable post-text screenshots, game-state traces, flash save hashes and source/ROM/tool versions. Post sanitized evidence bundle as designed under the evidence branch or Actions artifacts; **do not commit ROM/ELF/.sav**.
- [ ] Validate a real saved checkpoint from older \`66b58c3a…\` ROM loads on current source, and Q1/Q2 \`e6870c30ece40c6d180e9077b79c47ebae8b0d241ff02bdec645d3422a7f34e1\` case provenance. **Do not state these ROMs are byte-identical.**
- [ ] Run \`scripts/coordination/qa_evidence_report.py\` on each available sanitized package. \`READY_FOR_INDEPENDENT_REVIEW\` is not QA PASS; fail closed on missing screenshots, ROM SHA mismatch, dirty/unaccounted engine, invalid read-only probe, mislabeled Continue/menu frame or debug action.
- [ ] Conduct a distinct read-only adversarial review of **each** case (may be one reviewer over immutable groups): inspect actual screenshots, inputs, saved-slot state and event ordering; publish exact **PASS/PARTIAL/FAIL/NOT_TESTED** with precise observed gaps. Explicitly identify Claude self-operated testing as **not third-party independent Playtest**. Record review and verdict in Issue #23.

### B1 — Q1 Gym Badge01, first field notes, Hiker +2 Great Balls

- [ ] Review actual Elio victory, filled Badge01 trainer card and/or Save menu badge 1 screen, game flags and no direct memory mutation; allow old-ROM run17 proof only where code-equivalence relevant to badge entry is established.
- [ ] Review natural researcher field-notes registration and badge gate, Hiker NOTES_RECORDED, return to researcher, exact Great Ball quantity **0→2** and quest completion, repeated interaction **stays 2**, field and party unchanged. Existing Claude run18 may cover the positive path.
- [ ] Confirm real Start→SAVE success and **fresh emulator process** title→CONTINUE→field, badge, rewarded flag and Bag Great Ball ×2 (run19); screenshot must actually display the restored field/Bag, not a highlighted Continue option.
- [ ] **Missing negative**: prepare **full Balls pocket** using normal gameplay or a documented safe developer fixture, then interact with the real claim NPC. Verify reward refusal (NO delivered balls, NO reward/completion flag), release pocket capacity through real bag actions, retry to receive **exactly 2**, repeat does not duplicate, and in-game SAVE/CONTINUE preserves final state. If fixture-only, label fixture; never assert naturally collected inventory.
- [ ] Check genuinely blocked-route/early badge attempt stays blocked where relevant, and controls/menu remain responsive after rejection.

### B2 — Q2 boy→tree→artist +3 Oran Berries

- [ ] Inspect run20 genuine walk (no debug warp) and boy *hint only*, tree at local coordinate (12,27) marks FOUND once, repeat tree doesn't reward, artist gives **exactly 3 Oran** and repeat doesn't duplicate; screenshots should show messages after text is fully rendered.
- [ ] Confirm stage flags are consistent with the player dialogue and that Save/Continue restores Oran Berry ×3 after the **natural run** where feasible; reuse earlier accepted warp-assisted Gate A Save/Continue only as narrowly version-equivalent support and disclose transport difference.
- [ ] **Missing negative**: **full Berries pocket** refusal before accepting reward: no item delivered, reward not consumed/flag not set, quest remains retryable; free legal bag capacity, claim exactly +3, refuse duplicate, Save/Continue. No memory/flag/item injection can masquerade as ordinary play.
- [ ] Verify unstarted quest and premature artist/tree interactions don't accidentally set paid/rewarded states; reuse native positive/negative evidence if it proves the same source at current SHA.

### B3 — Q3 legitimate whiteout → clinic nurse → full recovery and fresh Continue

- [ ] From playable actual saved game, lose a permitted battle on purpose through normal combat. No forced flag, direct whiteout call, debug warp or raw save editing in a claimed real battle loss.
- [ ] Record the authentic defeat, whiteout/fade text, post-loss clinic actual map and tile, after-whiteout nurse dialogue and regained overworld control. Distinguish \`lastHealLocation\` (saved healing choice) from \`gSaveBlock1Ptr->location\` (actual clinic map); avoid historical false negative fixed by #71.
- [ ] Measure **each surviving/restored party member** HP vs MAX_HP, status ailments cleared and appropriate move PP; verify follower correctly despawns/respawns according to actual lead and field, rather than assuming the nurse script is sufficient proof. Test region badge/quest flags unaffected.
- [ ] In clinic use actual Start→SAVE, capture success and persisted flash slot, quit emulator, relaunch a separate process **without debugger for Continue if reproducible**, select CONTINUE and verify **the clinic field appears**, with recovered party and quest state. Reuse [prior CI run 38996685926](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38996685926) for real nurse/clinic Save→Continue where exact source behavior equivalence is proven; it lacks post-heal HP validation.
- [ ] Separate read-only evidence review; document actual PASS/PARTIAL rather than treating old CI green as full acceptance.

### B4 — Q4 six-party gift refusal → deposit → exactly one Wobbuffet

- [ ] Preserve a copy of six naturally captured Pokémon, inspect their real party slots and compare before/after; use **clearly disclosed developer-only lab access** on that copy because natural access is not approved.
- [ ] Re-run current PR #97 \`pc_deposit\` helper (latest code head \`eef446bb\` reports actual cursor reading) against real PC UI **MOVE, DEPOSIT, WITHDRAW** ordering. The helper is code, not a verified successful test until it actually navigates and deposits a Pokémon with normal inputs.
- [ ] With party 6/6, interact with test scientist, show "Your party is full" refusal, no gift flag or unexpected PC delivery. Then deposit one by actual menu button presses (not memory writes), demonstrate **5/6**, retry event and verify a single intended Wobbuffet, correct one-time flag and expected species/party count.
- [ ] Re-talk after successful gift, confirm no second Wobbuffet in party or storage; run Save→fresh Continue on dev copy and confirm party/gift flag/PC consistency.
- [ ] Specify whether the gift is developer-only and not currently natural-story reachable; if so accept **DEV_FIXTURE_NATIVE+RENDERED** scope for backend M1, and defer natural lab accessibility to later owner map/story content instead of inventing a route.

### B5 — Q5 field playability, text, following and sound

- [ ] Genuine player movement/turning and collision: walk to blocked and open terrain/door/warps, NPC collision, no boundary clipping or softlock; screen coordinates/inputs correctly match actual collision data. Document chosen **existing approved locations**.
- [ ] Dialogue fully renders, progresses and closes; Start/Bag/party/Field Kit/options/menu selection/cancel return to player with responsive controls, and restarting/resetting does not strand them in menus.
- [ ] Following Pokémon lead/party switch lifecycle, doors and warps, field→battle→field or whiteout; verify visually correct object state and save/Continue persistence where applicable. Note future art missing only when actually absent.
- [ ] Capture actual **overworld/battle audio** (not only title BGM) with game/ROM provenance; verify audible/non-silent signal and expected state transitions to the extent reproducible. No invented copyright/track attribution or altered audio files.
- [ ] Exercise opening/starter branch variants or existing verified source/native controls where achievable **without** restarting the whole existing save and without inventing owner-approved starter selection rules. Check player control, first Gym state, field menu, PC and Save/Continue as applicable.
- [ ] Report blocked/unreachable cases separately with exact source/map restriction; only mark **POST-CONTENT** if genuinely dependent on a not-yet-approved map/story caller.

---

## P1 — Close outstanding QA integration PRs correctly

### T1 — Local graphical playthrough driver [PR #97](https://github.com/kioconnor24-sketch/PokemonGame/pull/97)

- [ ] On live PR #97 head (last seen \`eef446bb420848500dd69f9fdfad655a0b44f263\`), review all eight \`scripts/claude_play/\` files, CLI, destructive/unsafe operations, symbol extraction, menu-cursor logic and read-only GDB contract. Guard against accidentally writing debugger memory, copying or committing save/ROM, falsely treating title as gameplay, and parsing encrypted BoxPokemon data without proper XOR.
- [ ] Run offline unit/negative tests and review current \`python-source-checks\`, \`file-guard\`, \`exclusive-files\`, \`route\`; add only necessary regressions for new \`pc_deposit\`, Q3 and evidence manifest. Capture actual version/commit and test command/outcome.
- [ ] Finalize the driver as reusable QA tooling, mark ready and normally merge **once eligible**, regardless of whether all Gate B cases have been accepted; a successful tool merge does not automatically pass gameplay QA. Keep private save/evidence branch separate.

### T2 — Old graphical observer [PR #20](https://github.com/kioconnor24-sketch/PokemonGame/pull/20) and clinic fix [PR #71](https://github.com/kioconnor24-sketch/PokemonGame/pull/71)

- [ ] Compare exact live source files/diffs of both PR heads to latest main; note #20 old parent \`codex/quest-event-framework\`, #71 base \`chatgpt/emulator-smoke-playtest\`. Old branches have **heavily diverged history**. Never blindly merge hundreds of old commits or force-push shared branches.
- [ ] Audit the old QA-only material: \`.github/workflows/averon-rendered-playtest.yml\`, \`Pokemon Game/scripts/qa/quest_state_controller.py\`, its unit tests, QA handoff, plus #71 \`.github/workflows/averon-qa-observer-unit.yml\` and clinic-specific amendments. Carry forward verified useful behavior only.
- [ ] **Source-grounded #20 bug:** \`title_state\` on its current old head calls \`sendall(b"\\x03")\` (four literal characters) rather than the **actual** GDB 0x03 byte used by \`position\`. Demonstrate failure with an isolated unit test before fixing the observer on fresh latest-main branch; verify title→Continue is no longer stuck.
- [ ] Preserve #71's distinction between respawn **clinic** map 75/11 and stored Alderfield heal location 75/9; avoid observer false negatives, overbroad acceptance from a screenshot, broken tests or changed game flags. Refresh CI workflow/test artifacts and actual Q3 screenshot evidence.
- [ ] Prefer a **fresh main-based Claude QA transplant PR** with only intentional files/diffs; review test semantics/protections, run unit and mGBA smoke checks, normal-merge it when eligible. Then link replacement in old #20/#71, close old PRs only after their needed work/evidence is really included and document why they were superseded. If instead retargeting either legacy PR, verify it displays only intended changes, no hidden history and all required checks pass.
- [ ] Confirm no overlap/concurrency between QA observer stack and Claude's separate #97 driver source. Don't delete old evidence or mislabel a report as PASS.

---

## P2 — One targeted source risk to resolve, without broad speculative refactoring

### R1 — Foreign-OT egg hatch and battle OT/personality hazard [Issue #100](https://github.com/kioconnor24-sketch/PokemonGame/issues/100)

- [ ] Inspect current \`engine/src/egg_hatch.c:345–348\`, \`ScriptHatchMon\`, secure BoxPokemon XOR key mechanics in \`pokemon.c\` and the exact merged #96 repair scope. Test a valid **foreign-OT egg** through **real \`ScriptHatchMon\`**, plus matching OT control, with item/move/PP/species/checksum/bad-egg/HP/saved party assertions. No invalid manufactured egg as the only supposed proof.
- [ ] Capture a **real native RED** on current main and pass/fail identity; only if reproduced, implement the narrowest **decrypt with old key → set OT → re-encrypt with new key** repair at the proper boundary, review behavior for early-return/errors, repeat GREEN including Save→Load, normal+RELEASE and relevant CI. Do not globally modify the raw setter required by constructors.
- [ ] Inspect reachable \`battle_controllers.c\` OT_ID and personality writes. The personality ID can select substructure order, so simple key XOR may be insufficient; validate source call paths and add an actual failing native test before touching production code. If only theoretical, mark **SOURCE-REVIEWED / RUNTIME NOT DEMONSTRATED** with exact rationale.
- [ ] Normal-merge any verified fix with source review and exact-head checks. If no actual defect, close #100 with a reproducible negative/control explanation. **Any confirmed save/Pokémon corruption cannot be waved away as POST-CONTENT at final M1.**
- [ ] Revisit speculative legacy save-callback / Berry Blender claims only if a reachable caller and genuine native reproduction are demonstrated after already merged #92. Do not expand a bounded investigation into an indefinite general audit.

---

## P3 — Full map-independent backend evidence and cross-feature completeness

For each matrix row below **first** inspect current main compiled production implementation, actual native tests, source SHA and linked call sites. Then mark **VERIFIED CURRENT MAIN** with a specific test command/log; where a non-map bug is reproduced, open smallest issue/PR with actual RED/GREEN. **Do not reimplement existing two-region/save/mechanics modules or create entirely new systems merely to satisfy a list.**

### C1 — TWO-REGION, save and world-platform invariants

- [ ] Two-region **Averon/Sinnoh active identity**, independent **8+8** badge banks, clean return cycles using symbolic fixtures, region-selected level cap/obedience, badge permissions/visited Fly/field licenses, heal/whiteout/region switches; reject invalid region/map/heal/warp IDs before narrowing. Show actual linked production adapter calls; don't demand real Sinnoh terrain.
- [ ] Full save: valid old-format migration without destructive writes, normal new-format roundtrip and state preservation (party, PC, Bag, quest flags, Trainer ID and badges), slot counters/rotation/CRC/version, torn newest slot fallback to whole coherent older slot, missing/truncated/semantic-invalid blocks, erased headers, disallowed future versions, no partial mixing across slots, corruption after failed save, alternative save paths and graceful error routing.
- [ ] Old and current game save compatibility; normal Save/Continue; full SaveBlock/sector/resource headroom; at least one negative proof for blocked incremental/trade save callback after merged #92. No silent item/Pokémon transfer on refused save.
- [ ] Map registry/group/event ID and object limits, route/warp/heal and generator determinism, source flags/vars reserved-range collisions and stable saved IDs; use existing compiled map data/synthetic descriptors only. No new maps/real Sinnoh destination.
- [ ] Available Field Kit and field action license/cancel interfaces: Cut, Rock Smash, Strength, Surf, Waterfall, Dive, Flash, Fly; correct badge permission, visited status and safe wrong-terrain responses by native or existing-area executable path. Document any action truly requiring future geometry as POST-CONTENT.

### C2 — Pokémon, battle and progression invariants

- [ ] Species/form/ability/move/item/learnset/Pokédex and breeding registry across currently supported generations with source-backed **configured vs actually encounterable** distinction. Existing valid Mega, regional form and evolution interfaces, trade substitutes, stone/item/time/move/party/location evolutions under symbolic native fixtures. Track missing later sprite graphics and location-dependent evolutions without requiring new final content or blanket "all species obtainable" claim.
- [ ] Forced **Set** battle style/no free-switch prompt; physical/special split; smarter existing battle AI and ordinary/special trainer-forfeit rules. Correct no-running for scripted battles, safe loss/win and no standard scripted loss penalty; never install owner-unapproved rival/trainer scene.
- [ ] Traditional **held-item** Generation V EXP Share rather than party-wide EXP, 6-party double/switch/fainted participants, cap and level-100 behavior; restoration, item transfer, persistence. Regression from #48/#94 should be reused if source-identical.
- [ ] Mega access requiring proper enablement item/key, valid transformation and post-battle reversion, end-of-battle/reset/whiteout; Z-Moves, Dynamax, Terastallization, Primal and other unapproved battle-only systems absent/disabled in intended production configuration.
- [ ] NPC trainer/wild/double battle, party/box full capacity, capture/gifts, item and storage safety, trade/menu/TM/tutor/item actions, status/held items, exp/rewards, old/new Save→Load. Cross-confirm #96 OT delivery fix and #100 outcome; no invented encounter design.
- [ ] Follower eligibility, lead slot changes, sprite/form/shiny identity where supported, map/battle/warp/door, surf/whiteout and loaded save lifecycle; if missing graphics require owner-provided future assets, classify precisely.
- [ ] LEGEND generic capture/defeat/flee/forced escape/full-party/retry/persistent state, SCRIPTED gauntlet/no-penalty loss/ally heal flags, Quest + Bag/full inventory and Save; compiled native actual registered interfaces but **no user-unapproved static legendary encounter or dramatic scene**.
- [ ] Basic weather/day-night, audio hook, existing area collision and overworld menu/PC/party interfaces; only fix actual defects with source + run proof.

### C3 — Cross-feature boundary smoke

- [ ] QUEST Q1/Q2 **reward→Bag full→retry→Save→reload** and region badge independence.
- [ ] PARTY/PC **full/refusal→space→gift/capture→Save→reload**, including foreign-OT integrity.
- [ ] NORMAL vs SCRIPTED battle forfeit/loss, no-whiteout state, HP/status/money/reset, follower reappearance, flash.
- [ ] LEGEND outcome/escape/capture/full party/PC/flash, native fixtures without reserved content.
- [ ] Two regions' 8+8 badges + cap/obedience + Fly/field license + whiteout/return + saved load.
- [ ] Six-party held EXP, level cap and level100, Mega/reversion with battle exit, evolution/breeding form/pokedex storage, resource check.
- [ ] Old/new/corrupted regional save combined with quest/PC/Bag/follower/region-state persistence, no duplicate item/reward or mixed-slot state.
- [ ] Use provenance from actual merged tests rather than manufacturing a new 6000-test suite. Any true compile/native/glitch gap gets a targeted new test+fix, then a final complete sweep.

---

## P4 — Final integrated-main build, full regression and owner-ready verdict (do LAST)

**A local composite or another PR's green CI is not final integrated-main proof.**

- [ ] Ensure #97 tooling and approved QA stack are merged/superseded, reproduced source defects fixed or disproven, and appropriate Gate B evidence passed or legitimately scoped with evidence. Refresh actual exact **final main SHA** and clean full-source tree. Confirm all required source/protection/CI checks and no open relevant backend PR for M1 (historical closed/obsolete branches explicitly resolved).
- [ ] From clean toolchain, record exact \`arm-none-eabi-gcc\`, native compiler, mGBA, Python, build commands and elapsed results for **NORMAL** and **RELEASE** ROM. Capture source commit, ROM SHA-256, ELF SHA-256, no new compiler/linker warnings/regressions and boot into real mGBA through field/menu without softlock. Don't promise untested iOS Delta.
- [ ] Run focused Averon integration native/save suites on final main, then **one full unfiltered native suite** with immutable strict expected-failure file. Earlier composite result was **5,330 pass / 327 expected failures**; compare **test identity and category**, not just total count, and distinguish unexpected failures/flakes/missing cases. Do not remove tests/edit allowlists to make green. Log commands/results/artifacts; investigate any divergence.
- [ ] Verify actual **GBA ROM <= 32 MiB**, linker/asset headroom, EWRAM and IWRAM budget, measured vs unmeasured stack, SaveBlock/sector layout and persistence, number of sprites/palettes/objects/event tables, build/asset-generator reproducibility and future capacity risk. Unknown margin is **unknown**, not PASS. Report risk of additional future Sinnoh art/maps without guessing sizes.
- [ ] Test old/new/corrupt/unsupported save handling and actual in-game SAVE→power/reset→CONTINUE from current-game ROM; compare full Bag, party, PC, badge, quest, follower and region data, no state mix/duplication. Back up local personal save before destructive tests.
- [ ] Run all feasible existing-approved-map Gate B cases with exact source/ROM inputs/screenshots/reviewer verdict, resolve any reproduced critical errors and retest fixes. Explicitly mark developer-fixture-only events vs normal gameplay, true owner-map-dependent POST-CONTENT and unrelated future features.
- [ ] Create a final **M1_ACCEPTANCE_REPORT** (e.g. under \`Averon_Codex_Handoff/development/\`) with a per-requirement matrix: **PASS**, **VERIFIED_EXISTING**, **FIXED_AND_RETESTED**, **PARTIAL/UNVERIFIED**, **POST-CONTENT**, **OWNER_DECISION**; link code commit/test runs/real screenshot evidence, source checks, hashes and known defects. For every PARTIAL say **what exact fact is missing**, why and which phase legitimately owns it.
- [ ] Publish final report and concise truthful owner decision summary to Issues #15/#23/#46/#55 as relevant; mark issue checkboxes **[x] only on actual supported evidence**, update stale instructions. Do not prematurely create another story/canon map backlog as if it were M1.
- [ ] Present owner with **BACKEND_READY: YES / NO / CONDITIONAL**, material risks and explicit map/content deferred list. **Do not begin Sinnoh maps or unfreeze creative scope until the human owner approves.** If true non-map functionality is not verified, M1 is not finished, regardless of how many PRs merged.

## Execution policy — keep Claude working, minimize usage waste

1. Refresh live main, relevant PR heads, changed filenames and Issue #15 claims **before** modifying or merging; this file's heads are snapshot facts. Prefer **#97 gameplay + evidence** first (already almost implemented), then #20/#71 transplant, #100 targeted test, stable combined matrix/final regression.
2. One emulator/save chain at a time; use separate copied save for developer fixtures and preserve genuine run17–run21. Read-only observation; no memory writes. Don't replay long known-positive introductions merely to change a status label.
3. One code owner per exact path. QA stack files and egg files are disjoint from #97. Claim, commit, run targeted tests and push to appropriate Claude-owned branch. Merge the next reviewed eligible PR normally when real CI passes.
4. If a task is truly inaccessible because of host/Auto GitHub permissions, **do not reattempt via a covert alternative or disable a guard**. Leave a precise merge-ready SHA+required-action note and implement the next independent item. Owner-approved interactive permission or separately authorized GitHub management can resolve the action.
5. Close out tasks by evidence, not by elapsed effort. Avoid endless unspecific audits, repeat building full native after every doc/test-only change or demanding maps/canon. **No arbitrary status inflation.**
6. Each session checkpoint: current main SHA, pushed branch heads, PRs merged/open, Q1–Q5 fact-by-fact PASS/PARTIAL, strict test delta, real blockers and next runnable step. This markdown checklist is the one to update, not another competing queue.

## Canonical references

- [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15): current owner delegation, claims, handoffs and merges.
- [Issue #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23): genuine graphical playtest and case-specific verdicts.
- [Issue #46](https://github.com/kioconnor24-sketch/PokemonGame/issues/46): owner-scoped 26 M1 acceptance items, previously containing stale unmerged-PR tasks.
- [Issue #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55): source risks and engineering friction.
- [Issue #100](https://github.com/kioconnor24-sketch/PokemonGame/issues/100): hatch/battle OT investigation.
- [PR #97](https://github.com/kioconnor24-sketch/PokemonGame/pull/97), [PR #20](https://github.com/kioconnor24-sketch/PokemonGame/pull/20), [PR #71](https://github.com/kioconnor24-sketch/PokemonGame/pull/71): only open PRs at original snapshot.
- [Latest short owner runbook](CLAUDE_SOLE_M1_EXECUTION_20261017.md) and [prior exact case checkpoint](M1_POST_INTEGRATION_CHECKPOINT_20261017.md) support this list. **If an older instruction conflicts, prefer the newest actual owner directive and verified GitHub facts.**
