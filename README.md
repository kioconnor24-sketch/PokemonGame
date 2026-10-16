# Pokémon Averon — Game Boy Advance project

The source project for a Pokémon Emerald Expansion game with the original Averon region and Sinnoh planned as a full second region. The source is actively developed; a complete playable game and independent Delta iOS verification are **not** claimed.

## Start here — one reliable path

1. [Repository operating instructions](AGENTS.md) and [four-agent roles](Pokemon%20Game/Averon_Codex_Handoff/development/AGENT_ROLES.md)
2. [Development index / file organization](Pokemon%20Game/Averon_Codex_Handoff/development/INDEX.md) — what each folder contains; which documents are historical
3. [Current work queue](Pokemon%20Game/Averon_Codex_Handoff/development/TASKS.md) and [dependency roadmap](Pokemon%20Game/Averon_Codex_Handoff/development/ROADMAP.md)
4. [Team claims and owner restrictions — Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15); [active assignments #24](https://github.com/kioconnor24-sketch/PokemonGame/issues/24)
5. [Current source branches and PR handoffs](https://github.com/kioconnor24-sketch/PokemonGame/pulls); [QA observations #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23)
6. [GitHub workflow handbook](Pokemon%20Game/Averon_Codex_Handoff/development/WORKFLOW.md) and [build/test checks](https://github.com/kioconnor24-sketch/PokemonGame/actions)

## Repository layout

| Path | Purpose |
| --- | --- |
| [Pokemon Game/engine/](Pokemon%20Game/engine/) | Game engine, data, sprites, native tests |
| [Pokemon Game/scripts/](Pokemon%20Game/scripts/) | Build, audits, authoring, host tests; keep existing paths stable |
| [Pokemon Game/Averon_Codex_Handoff/development/](Pokemon%20Game/Averon_Codex_Handoff/development/) | Collaboration rules, roadmap, active task queue, historical progress |
| [Pokemon Game/Averon_Codex_Handoff/qa/](Pokemon%20Game/Averon_Codex_Handoff/qa/) | Test plans and evidence, not equivalent to a complete emulator pass |
| [Pokemon Game/Averon_Codex_Handoff/design/](Pokemon%20Game/Averon_Codex_Handoff/design/) | **Historical/provisional** creative drafts, not authorization to implement |
| [Pokemon Game/Averon_Codex_Handoff/data/](Pokemon%20Game/Averon_Codex_Handoff/data/) | Planning CSVs and asset information; do not treat provisional data as final |
| [.github/workflows/](.github/workflows/) | Source checks, native builds, safety checks |

## Current constraints

Codex and Claude are **equal peer developers in separate checkouts**, with exclusive claims for shared files; ChatGPT QA owns independent emulator acceptance, and ChatGPT management handles reviews. Read the latest [coordination hub](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) before touching a claimed path.

**Owner hard freeze:** no new production *or temporary* map/layout/route/geography files, no final Sinnoh maps, unapproved story scenes, Gym teams or level curves, Pokémon placement, legendary locations, custom friend likenesses or unapproved sprites/music. Synthetic in-memory region/badge fixtures and unrelated verified technical work are permitted. The [conditional future backlog](https://github.com/kioconnor24-sketch/PokemonGame/issues/26) does not lift this freeze.

`main` is the integrated baseline. Open PRs are **not merged achievements**. Source/compile/native tests are not graphical gameplay verification; owner-run Delta testing remains separate. Do not publish copyrighted complete ROMs, private save data, secrets, or unlicensed media.

## Developer workflow

Read the [working procedure](Pokemon%20Game/Averon_Codex_Handoff/development/WORKFLOW.md), claim exact files in #15, code on an independent branch, run targeted checks, then build/test the actual GBA engine when appropriate. Record the exact head SHA, actual results and the next action in that PR's **HANDOFF** rather than rewriting shared documents every session.

Past creative packets and Codex bootstrap instructions remain available for provenance but should **not** override this entry point or current owner approvals.
