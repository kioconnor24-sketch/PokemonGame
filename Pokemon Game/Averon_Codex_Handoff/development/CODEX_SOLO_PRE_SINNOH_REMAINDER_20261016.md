> **ARCHIVED PROCESS / SNAPSHOT — superseded 2026-10-18.** Use the [single operating contract](CURRENT_PHASE_AND_HANDOFF.md), [integration queue](INTEGRATION_QUEUE.md) and [#15 live claims](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). All prior “current”, “authoritative”, pause, freeze, manager-only and resume commands below are historical. Retained evidence and approved product constraints are preserved; this file grants no new work or content approval.

---

# CODEX — SOLO PRE-SINNOH BACKEND AND INTEGRATION TAKEOVER
**Owner-directed, 2026-10-16.** Claude's current manual session has finished per owner. **Codex is assigned all remaining feasible backend implementation and integration**, not merely small test tasks. This file is a handoff on a new documentation branch, **not completed or merged game code**. First re-read fresh main, open PR changed paths/reviews/checks/heads, live Issue #15, full completion contract #46, Codex handoff #54, Playtest QA #23 and problem desk #55. Newer source wins over this snapshot.

## Actual snapshot and major blockers

At inspection, main is **7f4ecc44270e98b2363fc49cb708aa4d9a3527fa**. No major backend feature PR has merged. Claude's local combination of QUEST #14, SCRIPTED #25, LEGEND #47, readiness #48, save #56+#61, travel #57 and progression #64 reported real GBA build/no C warnings, **200/200 focused Averon natives** and 6,065 full-suite tests with 327 expected baseline failures, at [Issue #15 comment 6221013804](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6221013804). This is a **local rehearsal only**; neither new main code nor graphical acceptance.

Current branch snapshot—re-query before acting:

| PR | Head | Work remaining |
| --- | --- | --- |
| [#50](https://github.com/kioconnor24-sketch/PokemonGame/pull/50) | 3c9d43de89 | Save sector bounds; protected-file collision with #56 |
| [#51](https://github.com/kioconnor24-sketch/PokemonGame/pull/51) | 1ba7bf9cf2 | Fly test stack repair; normal review/merge |
| [#52](https://github.com/kioconnor24-sketch/PokemonGame/pull/52) | 476ba941c6 | Fly destination bounds; protected-file collision with #56 |
| [#56](https://github.com/kioconnor24-sketch/PokemonGame/pull/56) | 2f4dba7bf3 | Regional save/flash/old-save migration; draft, exclusive-files FAIL due #50/#52 |
| [#61](https://github.com/kioconnor24-sketch/PokemonGame/pull/61) | 78b5ed44df | HoF, link, overwrite save tests, stacked on #56; integrate |
| [#57](https://github.com/kioconnor24-sketch/PokemonGame/pull/57) | 5ce9301e93 | Real-ROM registered bidirectional region travel; stacked on #56 |
| [#64](https://github.com/kioconnor24-sketch/PokemonGame/pull/64) | 10de349770 | Region badges, EXP caps, obedience, whiteout money/catch and Flash; stacked on #57, owner policy pending |
| [#48](https://github.com/kioconnor24-sketch/PokemonGame/pull/48) | 7f2446009c | Pokémon mechanics, forms/EXP Share/follower tests, actual held-item repair; review-ready |
| [#47](https://github.com/kioconnor24-sketch/PokemonGame/pull/47) | cf2a1aaf35 | Generic legendary-state library; review-ready, event registration later |
| [#14](https://github.com/kioconnor24-sketch/PokemonGame/pull/14) | db6baaea45 | QUEST events, draft and still missing independent full Q1–Q5 graphical acceptance |
| [#25](https://github.com/kioconnor24-sketch/PokemonGame/pull/25) | 456bd035a2 | Scripted-battle true no-whiteout config/Run/cleanup, event_scripts.s shared with #14 |
| [#58](https://github.com/kioconnor24-sketch/PokemonGame/pull/58) | 4331c99007 | Release parity, 432 host assertions/23 mutation detections, review/merge |
| [#60](https://github.com/kioconnor24-sketch/PokemonGame/pull/60) | 5ead8c826e | PC/Bag transaction tests, GBA+51/51 Averon, review/merge |
| [#63](https://github.com/kioconnor24-sketch/PokemonGame/pull/63) | 2e3a5c1305 | Saved map-ID registry/capacity checks, 951 IDs/76 groups/534 maps, review/merge |
| [#18](https://github.com/kioconnor24-sketch/PokemonGame/pull/18), [#59](https://github.com/kioconnor24-sketch/PokemonGame/pull/59), [#62](https://github.com/kioconnor24-sketch/PokemonGame/pull/62), [#65](https://github.com/kioconnor24-sketch/PokemonGame/pull/65) | open | Docs/agent workflow fixes; merge only after normal independent review, don't block engine |
| [#20](https://github.com/kioconnor24-sketch/PokemonGame/pull/20) / [QA #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23) | draft | Independent rendered gameplay QA remains partial |

## Owner transfer and permissions

The owner has designated **Codex as the active developer and integrator for the unfinished Claude work**. Codex may claim/reuse Claude branches/code, fix remaining source defects, run tests, refresh dependencies, propose consolidation, open pull requests, and perform **normal eligible merges without repeatedly requesting user confirmation**. Claude's separate scheduled cloud routine was reportedly paused during integration: verify it stays paused, and never overwrite an actually active writer or perform simultaneous writes to the same branch. GitHub comments do not themselves launch agents.

**Do NOT waive** any actual GitHub required checks, protected-file authorization, the independent review process, or genuine Playtest acceptance. Do not force push, temporarily close and reopen #56 merely to fool an overlap guard, or use an old green check that predates new conflicting PRs. No new Averon/Sinnoh maps, map fixtures, saved IDs, story, canonical trainer roster, legendary location or unapproved artwork.

The genuine repository-owner Issue #15 [comment 6221771797](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6221771797) authorizes #56's four specified protected paths (global.h, save.c, new_game.c, test/save.c). Other scoped protected approvals for #50/#52/#25 are in [comment 6209610910](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6209610910). Neither approval makes a still-colliding PR pass. **Any new successor PR or newly protected path needs genuine approval if the unchanged guard requires it**, not a fabricated comment.

## Priority A — FIX protected-file collision, then actually merge regional system

**A1. Structural collision reproduction.** The trusted main-exclusive workflow compares file lists from *all* open PRs, including drafts. #50 vs #56 both change engine/src/save.c; #52 vs #56 both change engine/src/region_map.c. Under current guard check_protected_files.py, both fail if evaluated anew. Claude demonstrated #56 contains byte-identical cherry-pick equivalents to #50/#51/#52 and that locally merging accepted safety commits into #56 is clean ([#56 rehearsal](https://github.com/kioconnor24-sketch/PokemonGame/pull/56#issuecomment-6221166981)); independently verify latest heads, tests, patch IDs and actual file tree.

**A2. Permanent legitimate resolution:** propose one reviewable, **permanently owned** integration series or consolidated successor that preserves *all* verified unique safety + save code and tests, records explicit supersession/transfer of redundant PRs, gets genuine approval for all protected paths (including region_map.c if moved to a successor), and passes the unchanged exclusive guard on the final actual open-PR state. Never temporarily hide #56 just to pass stale checks. Another valid route is source/branch restructuring that honestly removes filename overlap with no lost code. If needed, ask owner for **one** narrowly scoped approval/decision, then work immediately on other merge-ready work, not more planning.

**A3. Merge reviewed and green actual source.** Recheck all applicable exact-head file-guard/exclusive/native/release/ARM/flash checks after restructuring; require true independent review. Execute normal GitHub merge only if all real gates succeed, confirm main SHA and ensure #50/#51/#52 identical commits aren't applied twice. If the collision remains, do not claim an integrated save system.

**A4. #56 comprehensive persistence.** Old saves remain valid; SaveBlock1/2/3 and PC/party/Bag coherent; 14-sector full-slot selection; anchor/CRC/counter validation; no mixed-slot writes; corrupt or duplicate-sector recovery; sector power cuts and rotation; upgrade new saves only on next proper save; refusal of newer version must never invoke destructive failed-save wipe or erase special HoF/link/overwrite sectors. Claude reports 17/17 native region save tests, 15/15 original and 4/4 refusal-related mutations killed; rerun as needed against merged source. Don't break reserved flash layout or allocate new saved IDs.

**A5. #61** link/HoF/overwrite and sampled interruption tests. Integrate after real region-save base. Recognize that aborted link save can legally roll back an entire prior slot.

**A6. #57** bidirectional travel and exact return/whiteout/heal/Teleport/Escape Rope; reject invalid map IDs atomically; flash power loss. Confirm the compiled ARM game actually retains the registered AveronRegion_BeginTravelSpecial. No real Sinnoh destinations yet.

**A7. #64** independently stored Averon/Sinnoh badge banks, active-region level caps/obedience, Rare Candy/EXP limit, party/save/travel/whiteout; whiteout money, missing-badge catch penalty, Flash rule selector. Its empty Sinnoh cap profile and default Averon badge rule should remain explicit until owner chooses nine cap+obedience values and AVERON / ACTIVE_REGION / EITHER rule. Do NOT quietly invent final numbers. Evaluate shop/menu/card/rematches separately and label map/owner-dependent behavior honestly.

## Priority B — integrate independently completed PRs NOW, even when A is blocked

After live checks, independent review and actual eligible merge, advance #58 release configuration safety (432 assertions and 23 mutants); #60 PC item integrity (4 transaction tests and GBA); #63 stable map slots and ROM/warp identifiers; #48 Pokémon readiness/held-item restoration; #47 generic LEGEND library; and #18/#59/#62/#65 as useful docs. These tasks do not need the protected save stack. Verify #48's battle_util.c edit safely combines with #64's obedience hook when region stack later lands. Keep the original Gen 5 **held-item** EXP Share, forced Set/no free-switch, level 100 maximum, Mega Evolution yes, Z/Dynamax/Tera/Primal no. Test the actual real RELEASE config, not just native-test TESTING overrides. Treat #47's event registration separately: it requires later protected event_scripts.s ownership, after QUEST #14 and SCRIPTED #25; don't invent actual legendary event placement. **No reviewable successful pull request should be left idle solely because a different one needs owner input.**

## Priority C — implement remaining unfinished battle/quest interfaces

**#14 QUEST:** native/source test success is not enough. Playtest already visually proved (scoped) Q1 no-badge refusal; Q2 artist/Oran x3 Save, fresh mGBA Continue and restored item; Q4 real single-Wobbuffet gift/no duplicate and on-map following; Q3 real Elio battle defeat, $40 loss and whiteout to home ([run 38932180353](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38932180353)). Still unverified: legitimately winning first badge and Hiker/Q1 reward, full Bag Q1/Q2 retry, six-Pokémon full party Q4 retry, clinic heal/respawn after authentic visit, Q5 input/follower/audio and any genuinely needed persistence case. **Playtest #20/#23 owns acceptance; Codex fixes proved production bugs, never impersonates independent acceptance.** Don't merge #14 as complete until required gate passes or owner formally narrows an unreachable scope.

**#25 SCRIPTED BATTLE:** the current draft still needs the real B_FLAG_NO_WHITEOUT RAM special flag in config/battle.h, actual source script inclusion only after #14 owns and merges event_scripts.s, no-Run rule, safe forced loss with HP/status/money/party preserved, cleanup across win/loss/draw/cancel/save/reload and repeated gauntlet battles, ally heal boundary and normal battle regressions. Existing #25 protected authorization exists but overlapping event_scripts.s still blocks simultaneous merge. Don't create canonical villain, Renn, operative or Gym teams/scenes in the map-independent phase.

**#47 LEGEND:** test capture (including capture with a full party when GUI reachable), defeat, forced exit/Teleport/Whirlwind, once-only caught state, retry and flash persistence, party/follower integration. Generic library #47 may merge without a placed event; the production script macro registration is a *later separately protected edit* needing genuine scoped approval after #14/#25 event script consolidation. Don't invent legendary species/placements.

## Priority D — remaining engine readiness and final verification

- Source/compiled checks: all supported existing species/evolutions/regions, forms, Pokédex persistence, friend/stone/trade item/party/time/region evolutions, follower lifecycle and palettes, Mega Ring requirements and Mega restoration after battle; status, type, items, AI, escape and capture; no excluded gimmicks in release. Only patch actual source defects. #48 reports **174 substitute follower sprite lookups**, and 13 region-dependent evolution targets not locally reachable; actual art and acquisition belong to later approved content, not a reason to make unapproved maps/assets.
- Saved progress interaction: QUEST rewards/full Bag, full-party gifts, box storage/PC operations, LEGEND captures, alternate save routes, active-region badges, Fly/field licenses, heal/whiteout, levels/EXP/obedience/party/follower. Run actual combined negative native tests and no destructive corruption; do not repeat completed audits without identifying a new gap.
- ROM and platform: clean real normal/release ARM build, linked/padded ROM <=32 MiB, flash saves and RAM resource headroom; source map registry stability and connection/warp bounds; actual emulator boot and independent reachable gameplay Save->Continue. Historical mid-80% RAM and ~80% ROM is **not proof of enough capacity** for an entire second region; report projected capacity risk honestly.
- Final **fresh integrated main** native full suite with expected failure baseline checker. Prior 327 failures were recognized in the historical 6,065 suite; any new failing case is a blocker. Exact nonzero test PASS/FAIL/SKIP and actual GitHub run IDs; don't assert 200/200 on new commits until rerun.
- Final #46 matrix: VERIFIED EXISTING / INTEGRATED+TESTED / UNVERIFIED / OWNER-DESIGN LATER / STRICT POST-MAP. Explicit decisions deferred: nine Sinnoh cap values and nine obedience values; badge rule; optional trainer 1.5x / unevolved 1.2x / EXP capture; Mega Ring placement; 13 regional evolutions; unsupported-save UI copy; Sinnoh real Fly sections/warps, area content/art and late-story encounters. The owner can choose a **gameplay-ready milestone** short of 100% peripheral backend, but Codex must not lift the no-new-maps freeze itself.

## No-wait Codex execution cycle

1. Post a short first-person Codex TAKEOVER claim in #15: user says Claude manual work is finished; verify scheduled Claude routine is not still writing; state precise existing branch you inherit or a new branch/file claim. No double writer.
2. Start with the single highest-value legal task and **actually execute** reviews, code edits, scoped PR corrections, real CI/ARM/native/flash checks, and eligible merges. Do not only summarize this document, request ordinary ACKs, or rebuild completed source.
3. If protected save collision requires owner permission, report one concise exact request and continue merging disjoint green, reviewed #58/#60/#63/#48/#47 core or other unclaimed engineering instead of waiting.
4. After every merge, verify new remote main SHA and source tree. Push recoverable work + exact test results and brief HANDOFF; repeat until all feasible approved map-independent tasks are exhausted or every remaining legal action genuinely blocked.
5. Never bypass independent review, required status checks, Playtest acceptance or owner's content freeze. Never claim GitHub comments awaken an inactive agent. Do not force-push others' work.
6. Stop only with a factual evidence matrix, merged SHAs, remaining owner-only choices, Playtest unmet cases and a clear recommendation on when playable Averon map construction can begin. No blanket 100%-complete claim without proof.

**Reference full prior Claude closeout:** [PR #65](https://github.com/kioconnor24-sketch/PokemonGame/pull/65). This narrower handoff supersedes its stale CLAUDE ownership, not its underlying safety/test requirements.
