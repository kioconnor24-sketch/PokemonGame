# Independent ChatGPT sidequest source QA — October 15, 2026

Scope: early optional quest source and full region *design* progression audit.
Source branch: chatgpt/early-quests-and-world-progression.
Associated pull request: #3.

## Verified locally (isolated fixtures)

- Installer integrity: 7 tests passed. Checks installation of four NPCs,
  reserved flag slot handling, idempotence, blocked tiles, event collisions,
  missing map rejection and reward retry order.
- Planned route graph: 9 tests passed. Checks badge order, required Gym
  reachability, optional unlocks, malformed gates and disconnected regions.
- Restricted native-script interpreter: 6 tests passed. Checks that all
  referenced branch/message labels exist, both quest state transitions,
  decline, full-Bag retry, exactly-once item grants and independent flags.
- Total: 22 executed local tests passed.

The native script interpreter is a *mock*, not the game engine. It does not
prove that the compiled Emerald virtual machine behaves identically.

## Checked against actual GitHub project data

- Design route CSV: 36 planned routes, 24 named locations, 8 Gyms.
- Invalid route endpoints: zero.
- Each expected next Gym/League destination is reachable in the
  *design-only* badge graph (0 through 8 badges). This independently
  checked graph is not the runtime map graph.
- Native font width: parsed actual engine font widths and charmap and measured
  all newly authored event text. Widest line 181px, below the project's
  normal message-window bound of 208px. No unmapped glyphs found.

## Not verified and required before game merge

1. Add new overlay step to reproducible authoring pipeline after coast generation.
2. Regenerate maps, run existing map and dialogue checks, compile the GBA game.
3. Add engine-level event/save tests for both quest chains and failure states.
4. Run focused mGBA smoke test, including save/reload and rewards.
5. Test compatibility with Delta later.

Do not mark the quests built or playable until the above is actually
verified. Current status: **AUTHORED SOURCE; COMPILATION/RUNTIME PENDING**.

## Verified on GitHub Actions

Workflow: https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38681796403

GitHub Actions passed Python syntax and fixture tests, the actual route design
audit, **and** a focused cross-branch integration check: it fetched the current
Codex `codex/first-gym-verification` engine map JSON, native layout binaries,
layout registry, constants/flags.h and event_scripts.s. It then successfully
ran the proposed sidequest installer against those real source assets in a
temporary, isolated checkout.

This confirms (for that Codex branch snapshot) the four NPC placement tiles
were accepted as walkable and unoccupied; all six proposed saved flag slots
were available; and adding the quest script included no source-preflight
conflict. The check did **not** compile the modified project, execute native
event scripts, test actual character interaction, or modify the Codex branch.
This is source integration evidence only.

The GitHub Actions quality gate is defined in
`.github/workflows/averon-source-checks.yml` on this development branch.
It will not automatically protect all work until the workflow is merged
into the base branch and branch protection is configured if desired.
