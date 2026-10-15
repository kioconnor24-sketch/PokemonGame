# LIVE TASK QUEUE — ownership and next implementation

This file is the authoritative **task/owner roster**. `main` includes PR #1 and PR #9 as of October 15, 2026. Earlier contributor PRs #2–#8 are incorporated through PR #9; do not remerge their changes. Fetch latest remote refs before assuming these statements are current.

## Work in progress — exclusive scopes

| Task | Owner | PR / branch | Current state |
| --- | --- | --- | --- |
| FIELD | **Codex Cloud/local** | [PR #10](https://github.com/kioconnor24-sketch/PokemonGame/pull/10) / `codex/field-licenses` | IN PROGRESS. Existing Cut/Rock Smash/Strength/Surf/Waterfall/Dive field licenses, Field Kit, dev lab; 30 native tests + 4 save-layout tests reported passing. **Finish Fly fixture, actual menu/cancel/animation/obstacle/follower interactions, save verification**. Gameplay/Delta acceptance not yet established. |
| HYGIENE | **ChatGPT** | `chatgpt/repository-workflow-hygiene` | Separate documentation, root entry, PR template and GitHub Actions scope/cost safeguards only. No FIELD gameplay source edits; release after merge. |

## Ordered backend queue

| Priority | Task | Owner when claimed | Acceptance condition |
| --- | --- | --- | --- |
| 1 | Finish FIELD | Codex | Successful native tests and build; verified Fly/test fixtures; mark unplaytested visual behaviors honestly |
| 2 | QUEST: reusable native quest scripting | Codex after FIELD, unless disjoint source ownership explicitly agreed | Staged progress, prereqs, one-time reward, full bag/party edge, save/reload tested in dev fixture |
| 3 | LEGEND: reusable unique legendary encounters | Codex after QUEST | Capture/defeat/flee/retry, prerequisites and save persistence; no final locations |
| 4 | BATTLES: scripted loss / gauntlet / heal / no-heal ambush | Codex | Test Renn loss without penalties; carry party health/status across battles; heal; save/recovery |
| 5 | REGIONS: two-region save and transport fixture | Codex; consider Sol High for save architecture | Separate badges, flags, Fly and whiteout, stable save/reload between test regions; no final Sinnoh maps |
| 6 | DATA: modern rules/species/followers/evolution gaps | ChatGPT only when explicitly claimed | Reproduce concrete gap, modify disjoint files, add native tests, document what was not emulator tested |
| 7 | BALANCE: source-driven two-region progression math | ChatGPT after user supplies needed topology | Compare growth/economy for multiple party sizes without guessing cap values |
| 8 | WORLD MAP, location-specific encounters, final trainer teams | **PAUSED — user owns geography** | User-approved map and progression before world content implementation |

**Rule:** One active programming PR per agent + at most one integration PR. Do not simultaneously edit shared event scripts, flags, save schema, global species tables or FIELD-specific files. To claim, record owner, branch, paths and acceptance here in a PR and notify existing owners through GitHub PR comments. If a task is blocked, specify why and take the next independent READY assignment rather than inventing geography.

A task is not DONE until remote PR/commit and actual evidence are linked. Source, build, native test, emulator and Delta are **different** statuses. Preserve history and never delete unmerged branches as a tidying shortcut.
