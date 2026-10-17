# Pokémon Averon — Pokémon Emerald Expansion game project

The source project for an original **Averon** region followed by a full **Sinnoh** second region. This is actively developed source, **not** a complete playable game or verified Delta iOS release.

## Start here — CURRENT source of truth

1. **[Owner-approved current phase, readiness and developer handoff](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md)** — the single canonical status. **Pre-Sinnoh Milestone 1 is accepted; the next phase is authorized.** Human audio listening is deferred; detailed map/story/ID design still requires approval.
2. [Repository-wide agent rules](AGENTS.md) and [Claude-specific rules](CLAUDE.md), then [documentation index](Pokemon%20Game/Averon_Codex_Handoff/development/INDEX.md).
3. [Current Phase 2 task queue](Pokemon%20Game/Averon_Codex_Handoff/development/TASKS.md), [milestone roadmap](Pokemon%20Game/Averon_Codex_Handoff/development/ROADMAP.md) and [Sinnoh technical readiness](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_TECHNICAL_READINESS_20261017.md).
4. [Developer ownership hub — Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) · [future design backlog #26](https://github.com/kioconnor24-sketch/PokemonGame/issues/26) · [QA / deferred human audio #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23) · [problem desk #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55).
5. [Pull requests](https://github.com/kioconnor24-sketch/PokemonGame/pulls) · [GitHub Actions](https://github.com/kioconnor24-sketch/PokemonGame/actions) · [workflow rules](Pokemon%20Game/Averon_Codex_Handoff/development/WORKFLOW.md).

## Milestone 1 evidence (finished; do not reimplement)
- [Consolidated acceptance, merged #112](Pokemon%20Game/Averon_Codex_Handoff/development/M1_ACCEPTANCE_REPORT_20261017.md): all assigned map-independent engineering complete, no known blocking defects, Q1–Q5 scoped graphical evidence, Gym 1 victory/badge preserved; remaining human **audio quality check is DEFERRED, NOT PASS**.
- [Native/full regression closeout, merged #109](Pokemon%20Game/Averon_Codex_Handoff/development/CODEX_M1_NATIVE_CLOSEOUT_20261017.md): 6,107 native test outcomes, 5,332 PASS and an **unchanged strict expected-failure baseline**; normal/RELEASE builds and save-integrity evidence.
- [Current new-phase technical planning, merged #111](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_TECHNICAL_READINESS_20261017.md): RELEASE ROM ~6.39 MiB headroom, SaveBlock2 84 B free, and pending section/met-location/region integration contracts. This does **not** prove a full region fits.

## Repository

| Path | Purpose |
| --- | --- |
| [Pokemon Game/engine/](Pokemon%20Game/engine/) | Buildable GBA engine, game data and native tests |
| [Pokemon Game/scripts/](Pokemon%20Game/scripts/) | Build, QA and coordination tools |
| [Pokemon Game/Averon_Codex_Handoff/development/](Pokemon%20Game/Averon_Codex_Handoff/development/) | Current phase, signed-off M1 evidence, historical handoffs |
| [Pokemon Game/Averon_Codex_Handoff/qa/](Pokemon%20Game/Averon_Codex_Handoff/qa/) | Case-specific visual testing and evidence |
| [Pokemon Game/Averon_Codex_Handoff/design/](Pokemon%20Game/Averon_Codex_Handoff/design/) | Provisional creative drafts, not automatically accepted canon |
| [.github/workflows/](.github/workflows/) | Required CI, guard and reproducible validation |

**Working rule:** Codex and Claude may work independently on nonoverlapping, approved scopes. No direct unreviewed `main` pushes or guard bypasses, and no unapproved creative decisions or ROM/private-save uploads. Historical documents/issues stay accessible for provenance but do not override the [current-phase handoff](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md).
