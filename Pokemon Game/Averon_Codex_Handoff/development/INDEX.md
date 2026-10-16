# Pokémon Averon — repository and documentation index

This is the **navigation page**, not an independent source of gameplay requirements. Keep historical source and design artifacts in place so old links and reproducible builds continue to work.

**Current default task and no-wait policy:** [BACKEND_TO_SINNOH_EXECUTION.md](BACKEND_TO_SINNOH_EXECUTION.md) and [backend completion issue #46](https://github.com/kioconnor24-sketch/PokemonGame/issues/46). These supersede older dated instructions below. No new Sinnoh or Averon maps until complete and separately authorized.

## Read in this order

| Purpose | Where | Authority |
| --- | --- | --- |
| Owner instructions and creative freeze | [Team hub #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [active assignments #24](https://github.com/kioconnor24-sketch/PokemonGame/issues/24) | Current owner instructions override historical plans |
| **Complete pre-Sinnoh engineering + blocked-task fallbacks** | [BACKEND_TO_SINNOH_EXECUTION.md](BACKEND_TO_SINNOH_EXECUTION.md), [backend #46](https://github.com/kioconnor24-sketch/PokemonGame/issues/46) | **Current authoritative execution contract** |
| Agent responsibilities | [AGENT_ROLES.md](AGENT_ROLES.md), [root AGENTS.md](../../../AGENTS.md) | Standing operating rules |
| Collaboration, commits and acceptance | [WORKFLOW.md](WORKFLOW.md) | Process |
| Current working code | [main and open pull requests](https://github.com/kioconnor24-sketch/PokemonGame/pulls) | Actual source and head-specific tests |
| **Automated coordination (new)** | [COORDINATION_AUTOMATION.md](COORDINATION_AUTOMATION.md), [live board #31](https://github.com/kioconnor24-sketch/PokemonGame/issues/31) | Advisory GitHub inboxes, QA gates and protected-file workflow, not automatic agent execution |
| **Agent-specific next actions** | [NEXT_AGENT_COMMANDS.md](NEXT_AGENT_COMMANDS.md) | Dated, source-checked commands for Codex, Claude and Playtest; recheck current claims before use |
| Next unblocked work | [TASKS.md](TASKS.md), latest claims in [#15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) | Stable priorities; newest PR claim wins when files overlap |
| Milestones and dependency gates | [ROADMAP.md](ROADMAP.md), [conditional future backlog #26](https://github.com/kioconnor24-sketch/PokemonGame/issues/26) | Backlog **not** permission to start frozen content |
| Independent player-facing testing | [QA tracker #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23), [QA_MATRIX.md](../qa/QA_MATRIX.md) | Only specifically executed cases are emulator-tested |
| Previously integrated evidence | [PROGRESS.md](PROGRESS.md) | Historical integration log; not live PR status |

## Repository layout (do not move these while active branches depend on them)

| Path | Contents | Maintenance |
| --- | --- | --- |
| [engine/](../../engine/) | Emerald Expansion source, graphics, event data, native tests | Codex/Claude file claims; no mass renames or unreviewed refactors |
| [scripts/](../../scripts/) | Build/install tools, audits, authoring utilities, host tests | Some paths are hard-coded by builds and workflows; preserve names |
| [scripts/tests/](../../scripts/tests/) | Host unit tests | Independent from engine-native test harness |
| [Averon_Codex_Handoff/development/](./) | Coordination, historical findings, technical decisions | Update stable queue only at real milestones |
| [Averon_Codex_Handoff/qa/](../qa/) | Regression procedures and evidence reports | Do not confuse source assertions with graphical acceptance |
| [Averon_Codex_Handoff/design/](../design/) | Earlier creative drafts and possible future references | **Not approved production instructions** |
| [Averon_Codex_Handoff/data/](../data/) | Historical planning CSVs and asset ledger | Do **not** use provisional geography/rosters as final data |
| [Averon_Codex_Handoff/reference_maps/](../reference_maps/) | Old conceptual designs | Frozen; no generation or implementation |
| [.github/workflows/](../../../.github/workflows/) | Build, source and hygiene CI | No full ROM/save uploads |
| [evidence/](../../evidence/) | Recorded source/test evidence where available | Verify exact source SHA; never assume older evidence validates a new head |

## Historical material — preserve, do not silently execute

- [START_HERE.md](../START_HERE.md), [CODEX_START_PROMPT.txt](../CODEX_START_PROMPT.txt), [CODEX_WORK_ORDER.md](../CODEX_WORK_ORDER.md): earlier bootstrap instructions; **not** current session/role/project status.
- [AUTHORITATIVE_BACKEND_FIRST_ROADMAP.md](AUTHORITATIVE_BACKEND_FIRST_ROADMAP.md), [OPENING_IMPLEMENTATION.md](OPENING_IMPLEMENTATION.md), [FIRST_GYM_IMPLEMENTATION.md](FIRST_GYM_IMPLEMENTATION.md), [COASTAL_ROUTE_IMPLEMENTATION.md](COASTAL_ROUTE_IMPLEMENTATION.md): design/implementation history; actual source and current accepted owner decisions govern.
- [ENGINE_FINDINGS.md](ENGINE_FINDINGS.md), [ENGINE_RESEARCH.md](ENGINE_RESEARCH.md), [READING_LOG.md](READING_LOG.md), [ENVIRONMENT.md](ENVIRONMENT.md): investigation and environment snapshots, not necessarily current.
- [DECISIONS.md](DECISIONS.md) and [CREATIVE_LOCKS_AND_OPEN_CHOICES.md](../design/CREATIVE_LOCKS_AND_OPEN_CHOICES.md): useful context, but explicit recent owner freezes/decisions take priority.
- [CHATGPT_QUESTS_AND_PROGRESSION.md](CHATGPT_QUESTS_AND_PROGRESSION.md), [LEVEL_CURVE_RESEARCH.md](LEVEL_CURVE_RESEARCH.md): speculative/working research; not a green light to choose story or final numeric levels.

## What is intentionally *not* cleaned up yet

No engine file moves, generated-source rewrites, script deletions, map development, authoritative story rewrites, build-tool renames, historic evidence purges, or merges of active coding PRs. Such changes can break reproducible builds or collide with active branches. Propose them as separately reviewed, tested changes only when a specific benefit is demonstrated.

## Where to put new information

- Individual session evidence → latest HANDOFF on the same PR.
- Current file ownership and handoff → [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15).
- Real independent gameplay/visual evidence → [Issue #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23).
- Approved task reorder → [TASKS.md](TASKS.md) once at milestone, not on every test.
- Accepted merged milestone → new top checkpoint in [PROGRESS.md](PROGRESS.md).
- New design choices → only when explicitly approved by owner; do not rewrite provisional drafts as final.
