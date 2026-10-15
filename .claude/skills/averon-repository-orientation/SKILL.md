---
name: averon-repository-orientation
description: Orient in the Pokémon Averon repository at the start of a session - where things live, what is authoritative, who owns what, and what to read first. Use before any planning, review or coding work in this repo.
---

# Averon repository orientation

## Session start (in order)
1. `git fetch origin main`; list open PRs and issue #15 comments (`gh api repos/kioconnor24-sketch/PokemonGame/pulls?state=open`, `.../issues/15/comments`). Live GitHub beats any note or cached summary.
2. Read root `AGENTS.md`, then `Pokemon Game/Averon_Codex_Handoff/development/AGENT_ROLES.md`, `WORKFLOW.md`, `TASKS.md`. `TASKS.md` and the top of `PROGRESS.md` can lag the owner's newer decisions in issue #15; treat contradictions as stale.
3. Read the latest `HANDOFF` comment on any PR you might touch.

## Layout (under `Pokemon Game/`)
- `engine/` - Pokémon Emerald Expansion-derived game source (C, event scripts `data/`, maps, `src/data/`, `test/`). Build and native tests run here.
- `scripts/` - Python authoring generators (`build-averon-*.py`), audits (`audit-averon-*.py`) and tests (`test-*.py`, `tests/`).
- `Averon_Codex_Handoff/` - design (`design/`), process (`development/`), QA instructions/results (`qa/`). Design docs may hold provisional names and numbers; owner decisions in issue #15 win.
- `evidence/`, `tools/` - recorded evidence and local tooling.
- `.github/workflows/` (repo root) - CI: native build, source checks, readiness, hygiene (`file-guard`).

## Ownership rules that matter
- Owner decides geography, story, final level caps. Never invent them.
- Claim in issue #15 before editing shared files: `flags.h`, `vars.h`, `save.c`, `global.h`, event script registries (`event_scripts.s`), region/badge/heal code, shared species tables, generated data.
- One coding PR per lead. Do not edit another agent's claimed files.

## Do not
- Commit ROMs/saves/keys (`*.gba`, `*.sav`, `.env`, `.pem` fail `file-guard`).
- Treat a code graph, memory note or old doc as more authoritative than current source.
