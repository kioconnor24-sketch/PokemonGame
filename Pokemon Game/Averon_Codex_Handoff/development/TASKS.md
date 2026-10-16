# Pokémon Averon — stable prioritized task queue

**Updated for the 2026-10-15 owner-approved milestone and hard creative freeze.** This is a **queue and dependency file, not a live status log**. Confirm every claim against [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [current assignments #24](https://github.com/kioconnor24-sketch/PokemonGame/issues/24), [open PRs](https://github.com/kioconnor24-sketch/PokemonGame/pulls) and exact CI before starting. The newest owner restrictions at the top of those issues prevail over older roadmap prose.

**Already integrated:** Opening/first Gym backend and FIELD licenses ([PR #10](https://github.com/kioconnor24-sketch/PokemonGame/pull/10) **merged**). Their particular emulator scenarios are not thereby all verified. Do not reclaim or remerge FIELD just because an old progress note still says it is active.

**Current file owners:** Codex — [QUEST #14](https://github.com/kioconnor24-sketch/PokemonGame/pull/14) and narrowly allowed `codex/two-region-groundwork` *new-file-only* recovery branch. Claude — [SCRIPTED-BATTLE #25](https://github.com/kioconnor24-sketch/PokemonGame/pull/25). ChatGPT QA — [emulator runner #20](https://github.com/kioconnor24-sketch/PokemonGame/pull/20) and [QA tracker #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23). [Tooling #19](https://github.com/kioconnor24-sketch/PokemonGame/pull/19) and [Claude onboarding #18](https://github.com/kioconnor24-sketch/PokemonGame/pull/18) are separate docs/ops PRs pending independent review. **All statuses may change; check live branches first.**

| Priority | Milestone | Owner / readiness | Acceptance and dependencies |
| --- | --- | --- | --- |
| 1 | QUEST | **Codex ACTIVE; QA pending** | Fix confirmed defects and verify rendered NPC/tree/rewards, full Bag/party, whiteout and real save/reload; native 49/49 reported on #14, not a visual pass; keep draft until evidence/approved gate |
| 2 | SCRIPTED-BATTLE core | **Claude ACTIVE (parallel)** | Finish native/macro/CI tests and actual safe-win/loss/chain recovery; release-flag, script registration and save hooks require explicit handoff after QUEST merge; no finished story scenes |
| 3 | TWO-REGION abstract groundwork | **Codex ACTIVE on bounded recovery branch** | Pure region/badge resolver, synthetically identified maps, test against existing engine, no existing file or map JSON edits until integration window; 8+8 backend save/travel later |
| 4 | QUEST graphical acceptance | **ChatGPT QA ACTIVE** | Continue exact Q1–Q5 rendered interactions; Q0-C opening movement/menu demonstrated; log reproducible defects with ROM/source SHA; don't equate smoke with full acceptance |
| 5 | TOOLING ONBOARDING | **Review pending** | Canonical shared skills #19 and distinct Claude docs #18; do not re-create competing skills; no install/hooks or feature work implied |
| 6 | TWO-REGION integration | **WAITING: QUEST gate and shared-source handoff** | Region-aware flags/8+8 badges, save compatibility, healing/Fly and no invalid warps; no production map files, use synthetic IDs/existing maps |
| 7 | SCRIPTED-BATTLE integration | **WAITING: QUEST gate and Codex handoff** | Allocate audited saved flag; install registered macro and cleanup; confirm ordinary whiteout after story battle, interrupts, save/reload, no money/party/badge loss; QA case requests |
| 8 | LEGEND reusable encounter semantics | **FUTURE technical, unclaimed until ready** | Capture/defeat/flee/retry/persist mechanics using fixtures, with no final legendary species, locations or lore |
| 9 | VERIFIED GAPS | **FUTURE only if unclaimed/file-disjoint** | Repair measured issues in species/forms/evolution, follower, battle AI, field menus, save/ROM/tests; no duplicate audits or arbitrary new systems |
| 10 | LEVEL ECONOMY analysis | **LIMITED / design blocked** | Can test existing EXP/cap code with supplied symbolic values; **no final numeric Gym caps or level curve** |
| 11 | AVERON / SINNOH MAP PRODUCTION | **OWNER FROZEN** | No new maps, temporary map layouts, region drawings, routes, tiles, production warp geography or generator-driven content |
| 12 | STORY, NPC, GYM, LEGEND PLACEMENTS, POSTGAME | **OWNER FROZEN** | No new canon scenes, Gym teams/puzzles, encounter tables, level choices, art/likenesses; wait for explicit owner authorization |

**Work selection:** complete your active PR before another coding PR; otherwise choose the first ready file-disjoint technical milestone, post exact intended paths/IDs/functions in #15, and respect exclusive ownership of `flags.h`, `event_scripts.s`, trainer/save/region/battle config, generated inputs and other shared files. **The freeze and claims are hard gates.** Test and post HANDOFF on the relevant PR; update this document only for milestone/priority changes, not individual sessions. No direct main pushes or secret/ROM uploads.

See [ROADMAP.md](ROADMAP.md) for gates and [INDEX.md](INDEX.md) for navigation. Preserve historical details in [PROGRESS.md](PROGRESS.md) but don't treat old checkpoints as current.
