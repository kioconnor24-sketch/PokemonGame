# Averon — stable prioritized task queue

**This file is for order and dependencies, not daily status updates.** Actual ownership/current progress live in OPEN pull requests and their latest HANDOFF comment. Check current GitHub before taking a task; update this file only when a new task is approved, priorities/dependencies change, a block becomes permanent, or a milestone merges.

**CURRENT RESERVED WORK:** Codex owns [PR #10 — field licenses and Field Kit](https://github.com/kioconnor24-sketch/PokemonGame/pull/10), `codex/field-licenses`, while the PR remains open. Do not touch its source, flags, map fixture, field menu or related code unless Codex transfers the claim. It has partial native verification; emulator and Delta coverage are not automatically established. `main` already integrates the opening/Gym 1 and contributor backend via PRs #1/#9 and repository hygiene PR #11. Never remerge old contributor PRs.

| Priority | ID | Readiness | Acceptance goal |
| --- | --- | --- | --- |
| 1 | FIELD | ACTIVE Codex | Finish existing Fly destination, menu/cancel, field effects, follower/obstacle and persistence checks; clean compilation, native test counts; record emulator gaps |
| 2 | QUEST | READY after FIELD | Reusable multi-stage native event scripts with one-time reward, prerequisites, full inventory and save/reload developer fixture |
| 3 | LEGEND | READY after QUEST | Unique encounter prereqs, capture/flee/defeat/retry state and saved quest progression on fixture |
| 4 | SCRIPTED-BATTLE | READY after QUEST | Safe forced Renn loss, sequential ten-operative battles with party carryover, allied heal, corrupt Gym no-heal rematch tests |
| 5 | TWO-REGION | READY after core events | Separate badge/transport/Fly/whiteout and save compatibility on two **temporary** region maps; no production Sinnoh map |
| 6 | DATA-GAPS | READY if file-disjoint | ChatGPT/guest: verify actual Gen I–IX species/form, evolution, battle rule or follower defect and fix with regression tests |
| 7 | LEVEL-ECONOMY | PARTIALLY READY | Source-driven EXP modeling without choosing final numerical Gym caps; final curves wait on geography/trainer density |
| 8 | AVERON-MAPS | PAUSED user | Author-approved geography, routes, Gym placements, encounters, level progression |
| 9 | SINNOH-CONTENT | PAUSED | Complete second region after two-region proof + established world production |
| 10 | POSTGAME | PAUSED | Legendary quests, Champions' Circuit, Cynthia, Red final, long-form QA and Delta |

**Priority algorithm:** Continue your open PR; otherwise take the first READY nonoverlapping item with prerequisites. If all coding tasks are claimed/blocked, report rather than inventing world design. One coding PR per agent, one integration/ops PR at most. Changes to `TASKS.md` and `PROGRESS.md` belong to integration milestones, not each cloud session.
