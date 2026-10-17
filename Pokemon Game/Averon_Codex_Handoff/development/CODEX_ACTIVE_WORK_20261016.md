# CODEX — ACTIVE SOLE ENGINE / INTEGRATION ASSIGNMENT

Issued at the owner's request on 2026-10-16. **Read newest Issue #15 claims, Issue #46 acceptance, Issue #54 last handoff, Issue #55 new reports and live GitHub heads before any write.** This document assigns work; it is not evidence of execution, an approval to bypass a gate, or an automatic agent start. Live source facts and newer owner commands supersede these pinned snapshots.

## Scope and exclusive ownership

**You are the only active production game-engine writer and final main-branch integrator.** Claude is reactivated by the owner **only** on the separate save-capacity reporting/CI lane documented in `CLAUDE_ACTIVE_WORK_20261016.md`. Playtest alone owns graphical QA #20/#23 and the independent verdict on QUEST #14. Manager owns coordination and its own open PRs #70/#71/#73.

Your active edit lane is the **existing #48 branch** (`claude/pokemon-readiness`, head at assignment `22569f23673249d11717972db99894aff09c31a1`) and later the **existing #25 branch** (`claude/scripted-battle`, head `f324e485358cf6f076418e7c223559f164c36dc1`), plus the small disjoint engine fallback specified below. Inherit the exact files actually changed by those PRs, **not** blanket write permission to every file they do not own. Claim any additional exact filenames in Issue #15 before changing them. One writer per branch.

**Do not edit:** Claude's `Pokemon Game/scripts/report-averon-save-headroom.py`, `Pokemon Game/scripts/tests/test_averon_save_headroom.py`, or `.github/workflows/averon-native-build.yml` while Claude owns that lane. Do not edit Playtest's `Pokemon Game/scripts/qa/**`, rendered-playtest workflow or QA #20 branch; do not edit manager PR #73's map registry checker/guard tests/source-check workflow, or PR #71's proposed QA changes. No new maps, layouts, events, plot, encounters, saved IDs, inventing Sinnoh badge/cap numbers or story decisions.

## P0 — finish #48 **without repeating finished fixes**

The old 198/201 failure is **resolved at the new exact head**: [GitHub native gate run 38983725807](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38983725807) completed **201/201 Averon native PASS**, with a real normal GBA build; source, release-config parity and exclusive file guards are green. Do not repeat old failed fixtures or claim that branch is still failing those three cases.

1. Inspect the latest exact #48 diff, origin/ownership lifecycle, capture/whiteout, same-ID gifts, held Berries, Pickup/full Bag behavior, PC preservation, and native tests; resolve **only evidenced** correctness regressions. Keep `LostItem` ABI and saved layouts unchanged.
2. Run the **full**, unfiltered native test suite and `Pokemon Game/scripts/check-averon-native-baseline.py` on the same exact head; report total, pass, known baseline FAIL, unexpected FAIL, timeout and why. The historical `Gimmick Form Change animations work` TIMEOUT↔FAIL flip can make the checker exit 1 despite unchanged failure count; **report it explicitly, do not silently ignore or loosen the checker**. This script and its tests are already among the #48 changed files—**Claude must not touch them**.
3. Build real normal AND `RELEASE=1` ARM ROMs from the same head; verify source/config checks, ROM/RAM/save resources, and memory limits. Do not publish copyrighted ROMs or personal save files.
4. Obtain genuine independent review and all applicable checks before normal #48 merge. **Do not self-approve**, lower required check standards or infer graphical acceptance from native tests. If a real blocker occurs, post precise test/code/run to #55; do not start unrelated grand features.

**Completion:** one reviewed, normally merged #48 with exact commit SHA, full-suite unexpected-regression count, normal/release build evidence, measured resources, honest native/GUI boundary. If the branch is ready but independent review is pending, move to the fallback below without endlessly waiting.

## P1 — keep SCRIPTED #25 ready, but serialize registration with QUEST

`#25` has successful native/source/release checks, but its exclusive-source gate conflicts with draft QUEST #14 on `Pokemon Game/engine/data/event_scripts.s`. This is **real dependency**; do not bypass, close/open to fake a clean gate, sneak changes onto main, or ask Playtest for synthetic approval.

- While QUEST Q1–Q5 genuine visual acceptance remains incomplete, limit #25 to nonoverlapping source/test review and preservation of its existing 9 source checks / 25 adverse negative controls. Do not invent scenes, new saved IDs or mythical placements.
- **After** Playtest independently verifies QUEST and a normally reviewed #14 merges, rebase/reintegrate #25 with the now-current `event_scripts.s`, claim the protected file(s) under the real guard policy, run exact-head native/normal/release/source checks, then obtain independent review and merge if genuinely eligible.
- Generic LEGEND #47 is already merged; its content-dependent *event-script registration* is **not** permission to invent placements and should remain deferred until the owner decides.

## Independent no-wait fallback — bounded PC slot-compaction defect

If #48 reaches a review/wait state and #14 is still QA-blocked, take the **existing, nonoverlapping** issue from [Problem Desk #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55): `Pokemon Game/engine/src/item.c::RemovePCItem()` currently checks `tempItem.quantity == 0` **before subtracting** `count`, so emptying a slot does not compact by itself. Current `player_pc.c` caller explicitly compacts, so this is not a demonstrated current user-flow failure.

- Claim exact `engine/src/item.c` and `engine/test/averon_pc_item_transactions.c` (existing native file) first and check current #15 for any new claim. Use a separate branch from fresh main (not stacked on unmerged #48).
- Add an adversarial **real native regression** for direct `RemovePCItem` zero-after-removal and remaining-items order. Fix only if it fails as suspected, ensure existing #60 PC/Bag paths remain correct, then run focused tests and real ARM build. Avoid modifying `engine/src/player_pc.c` unless the observed bug actually requires it; expand claim first if so.
- Independent review and normal merge only. If there is an unknown engine conflict or substantial build blocker, record it and stop this bounded patch rather than duplicate another developer.

## Review / integration discipline

Codex can separately inspect Claude's **finished** #72 source and manager's finished #73 source, comment on actual defects, and normally integrate them after required independent approval; **do not edit their source files or rewrite their branches while those writers are active**. #71 is based on Playtest's branch and must remain with Playtest for graphical acceptance/review.

Preserve already-merged #56/#61/#57/#64 and #67/#68. Do not revive #69 (closed unmerged). Do not claim `BACKEND_READY` until fresh integrated-main full-suite/native/normal+RELEASE/flash/boot/capacity evidence and honest QA status are documented.

## Reporting

At useful tested checkpoints, post **one compact message** to [Issue #54](https://github.com/kioconnor24-sketch/PokemonGame/issues/54) plus an exact file claim/release in [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). Put *actual problems* and fallback in [Issue #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55) (`AGENT_PROBLEM_REPORT` with OBSERVED, IMPACT, ATTEMPTED, NEEDS, CAN_CONTINUE_WITH, STATUS). Include branch SHA, test/run link, PASS/PARTIAL/FAIL and precise next gate; do not produce stale generic progress summaries or assume GitHub comments wake another AI.

**Priority order:** #48 verification/merge → #25 after genuine QUEST acceptance, while independently handling the small PC fix when gated. **Never wait globally:** work in your claimed lane, not Claude's or Playtest's.
