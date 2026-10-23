# Pokémon Averon — Pokémon Emerald Expansion game project

The source project for an original **Averon** region followed by a full **Sinnoh** second region. This is actively developed source, **not** a complete playable game or verified Delta iOS release.

## Fast developer startup (live work)

For **Codex or Claude**, avoid reconstructing the project from dated handoffs or hundreds of old comments. This is a navigation guide, not a replacement for the protected operating contract.

1. Read root [AGENTS.md](AGENTS.md) (Claude also [CLAUDE.md](CLAUDE.md)) and the [current operating contract](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md). These control authorization and preservation, not old handoff files.
2. Open [the live work router (Issue #15)](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [current open PRs](https://github.com/kioconnor24-sketch/PokemonGame/pulls?q=is%3Apr+is%3Aopen) and [latest main](https://github.com/kioconnor24-sketch/PokemonGame/commits/main/). Check **your active branch/PR head, file claims, final checkpoint and required CI**, not a historic manager summary.
3. For Sinnoh donor availability, use the **159-map reuse ledger in [PR #237](https://github.com/kioconnor24-sketch/PokemonGame/pull/237)** until accepted onto `main`; [PR #238](https://github.com/kioconnor24-sketch/PokemonGame/pull/238) depends on it. Use the existing [87-site geography scope](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_FULL_AREA_COVERAGE.md) to find genuinely missing places, not to count individual maps.
4. Work on substantive connected map/art/DEV test batches; use existing source converters, art packers and QA. Separate **source-staged**, **DEV emulator-tested** and **production-installed** status. Keep story and new permanent saved origins out of this phase.
5. If blocked, record the **one exact blocker** on the owning PR/Issue #15 and continue independent work. Issue comments do not launch sessions. Do not read all historical branches, repeat earlier proofs without changed inputs, delete shared refs or upload ROMs/private saves.

**October 23, 2026 snapshot (check live links):** #239 Canalave DEV merged; #237 bulk 91-map stage is awaiting genuine owner handoff for three reserved documentation paths, #238 is stacked on #237, and draft #235 has unresolved Snowpoint bridge visuals. Codex's Sunyshore coast branch is active. Older manager handoffs, branch inventories and the development index can be useful history, but are not current assignment authority.

## Start here — current operating contract

1. **[Owner-approved current phase, readiness and developer handoff](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md)** — the single process authority. **Milestone 1 is accepted.** Developers may design and construct ordinary Sinnoh physical geography for later owner revision; story, encounters, levels, saved-ID policy, protected paths, and release are separately controlled. Human-audio and Delta acceptance remain unverified.
2. [Repository-wide agent rules](AGENTS.md) and [Claude-specific rules](CLAUDE.md), then [documentation index](Pokemon%20Game/Averon_Codex_Handoff/development/INDEX.md).
3. **Current Sinnoh production:** [Master roadmap](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_MASTER_PRODUCTION_ROADMAP.md), [Claude/Codex work packages](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_DEVELOPER_WORK_PACKAGES.md), [87-place coverage](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_FULL_AREA_COVERAGE.md) and [area register](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_AREA_REGISTER.csv). [Earlier integration queue](Pokemon%20Game/Averon_Codex_Handoff/development/INTEGRATION_QUEUE.md), [roadmap](Pokemon%20Game/Averon_Codex_Handoff/development/ROADMAP.md) and [reset audit](Pokemon%20Game/Averon_Codex_Handoff/development/ORGANIZATIONAL_RESET_20261018.md) are dated checkpoints; refresh live GitHub.
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

**Working rule:** Claude/Codex independently claim disjoint files and construct ordinary Sinnoh geography under the owner's delegation. Author-merge only within the current evidence-backed risk tiers; preserve high-risk peer review and protected GitHub rules. Do not invent story/encounter/level decisions or upload ROMs/private saves. Historical documents/issues stay accessible for provenance but do not override the [current-phase handoff](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md).
