> **ARCHIVED PROCESS / SNAPSHOT — superseded 2026-10-18.** Use the [single operating contract](CURRENT_PHASE_AND_HANDOFF.md), [integration queue](INTEGRATION_QUEUE.md) and [#15 live claims](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). All prior “current”, “authoritative”, pause, freeze, manager-only and resume commands below are historical. Retained evidence and approved product constraints are preserved; this file grants no new work or content approval.

---

# CLAUDE — ACTIVE INDEPENDENT CAPACITY / CI ASSIGNMENT

Issued at the owner's request on 2026-10-16. **The owner is reactivating Claude for this narrowly disjoint work lane, not the historical co-lead engine development or any autonomous schedule.** First read newest [Issue #15 claims](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [Issue #55 problem reports](https://github.com/kioconnor24-sketch/PokemonGame/issues/55), current PR list and this file. Snapshot SHAs are not guaranteed current; do not act on old role assignments from #31/#53/legacy documents.

## Exact ownership — no overlap with Codex or Playtest

You are the **single active writer for the existing informational save-headroom reporting lane**, [draft PR #72](https://github.com/kioconnor24-sketch/PokemonGame/pull/72), branch `claude/save-headroom-report`, head at assignment `c9580b442014784f406629de53cb6f8c937c731e`.

Allowed existing files:
- `Pokemon Game/scripts/report-averon-save-headroom.py` (report from actual linked ARM ELF).
- `Pokemon Game/scripts/tests/test_averon_save_headroom.py` (independent source-only regression tests).
- **One optional exact-file extension after posting a new Issue #15 claim and verifying no intervening claim:** `.github/workflows/averon-native-build.yml` (run report/tests in existing native CI; narrow workflow change only).

These files are **reserved to Claude** until a verified handoff. Build evidence may be read from engine outputs, but **do not edit any `Pokemon Game/engine/**` production or native-test file**, `scripts/check-averon-native-baseline.py`, `scripts/test-check-averon-native-baseline.py`, `scripts/averon-native-test-baseline.txt`, `event_scripts.s`, `config/battle.h`, main build/config, or any #48/#25 source. Codex owns them. No edits to manager PR #73's map registry files/source checks, to manager PR #71 or Playtest #20 QA files, or to new maps.

**Ownership is by filename, not by topic:** analyzing save/test/battle source read-only is fine; adding production save fields, changing save sector semantics, revising battle mechanics or making Sinnoh cap choices is **not assigned**. Do not revive Claude's previous scheduled background writer or assume a GitHub comment can launch agents.

## P0 — close the real save-space evidence gap, efficiently

`#72` adds a safe offline script reading `arm-none-eabi-nm -S` output and compiler/header-defined capacities, accounting for the `SAVEBLOCK_MOVE_RANGE` padding. Existing pure-Python tests reportedly **3/3 PASS** and the informational script has real main-branch ELF evidence. Independently inspect and reproduce on current files, do not claim game/save acceptance merely from parsing.

1. Verify script and tests on the **exact branch head**. Confirm missing symbols, invalid sizes, malformed input and bounds are rejected, rather than returning fabricated free space. If existing tests already cover these, don't repeat implementation.
2. Claim `.github/workflows/averon-native-build.yml` explicitly in newest #15 before changing it. Add **only** required path triggers for `report-averon-save-headroom.py` and `tests/test_averon_save_headroom.py`, a short source-only `unittest` invocation, and a post-normal-ROM-build step invoking the report on the **actual freshly linked** `pokeemerald.elf`. Include small textual/JSON capacity evidence in existing CI artifact paths if useful; never upload ROM, ELF, original saves or copyrighted assets. **Keep the existing standard GBA compile/native gate and resource-budget checks intact**.
3. Check that the changed workflow's shell/YAML contract is sane, existing source/guard/hygiene CI passes and a genuine exact-head native build runs successfully with the new capacity step. Do not call CI `success` until logs confirm that the report ran.
4. Report exact linked normal/release measurements separately when available. Current reported main `9d32324580ea` figures: SaveBlock1 **304 B free**, SaveBlock2 **84 B**, SaveBlock3 **1,556 B**, Pokémon Storage **1,568 B**, normal ROM approximately **6.82 MB free**. Use newly measured values if different; do not infer space for an entire Sinnoh region or add new save fields. Save design beyond this is Codex/owner territory.
5. Keep #72 **draft until tests/CI and independent review**; notify Codex/Manager with exact commit SHA, run, actual sizes and recommendation. Codex remains sole integrator/merger. Don't keep rewriting the same branch after final handoff.

**Completion:** one small tested #72 adding measurement report and CI registration, truthful bytes for all four blocks at a specific real ELF SHA, zero game-source changes, and a normal independent review/merge path.

## Read-only independent follow-up — valuable work without duplicated code

After #72 is stable, do **not** start a second overlapping engineering PR to look busy.

- Read-only review [manager #73](https://github.com/kioconnor24-sketch/PokemonGame/pull/73): engine object array has 64 slots; checker previously allowed 255. Verify its 64/65 positive/negative tests, actual map-registry CI, and lack of map/engine changes. Post **specific** review findings only if real; no self-merge or edits to manager branch. This can be an independent review because Claude reported the original problem, but never substitute a cursory glance for a real code review.
- Read-only analyze new [Codex #48](https://github.com/kioconnor24-sketch/PokemonGame/pull/48) at current pushed head, especially SaveBlock/Bag interactions and its **full native vs old 201/201 targeted** distinction. You authored predecessor code in this PR: your review is **not automatically an independent approval**. Provide reproducible findings to Codex without editing files or running redundant full builds just to copy evidence.
- If the full-suite `Gimmick Form Change animations work` TIMEOUT↔FAIL flake still causes a baseline false failure, write a concise reproduction/expected safe narrow rule in [Problem Desk #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55). **Do not modify baseline checker, entries or tests** while Codex owns them. The remedy must reject other statuses, count changes, NEW tests and incomplete runs.
- No task requires actual map production, legendary placements, story scripts, graphic acceptance, or decisions about Sinnoh badges/obedience. If capacity shows genuine hard exhaustion, report the exact data and remain on unrelated read-only review, not a speculative save rewrite.

## Cross-agent rules

**Codex writes engine code and merges eligible PRs. Claude writes the three explicitly assigned tooling/CI files only. Playtest alone writes QA and signs off rendered Q1–Q5. Manager coordinates and owns #70/#71/#73.** A file needs one named writer at a time, verified by the latest #15 comments and head before every write. Never force-push over others' work, relax branch protection, bypass protected-source approval, falsify screenshots/CI, conflate configured flags with gameplay evidence, or generate new Averon/Sinnoh maps.

If a claimed file becomes occupied or a new defect would require another lane, **do not take it**: document the exact reproduction and pass it to that lane while continuing available independent work. Do not create process gates that unnecessarily stop Codex's #48 verification or Playtest's graphical QA.

## Reporting

At a material tested checkpoint: update PR #72, post a short `CLAUDE_CHECKPOINT` in [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) (exact files, head, tests, CI, ready/blocked, next step), and post an `AGENT_PROBLEM_REPORT` to [Issue #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55) **only for genuine unresolved problems**, distinguishing verified problems from suspicions. No auto-start promise, no automatic model scheduling. If complete, **stop with a clean saved handoff** rather than inventing extra work.

**Priority order:** finish the #72 save-headroom/CI integration first → review #73 read-only → report actual #48/baseline concerns without source edits. Do not wait for Codex or Playtest to do your first task.
