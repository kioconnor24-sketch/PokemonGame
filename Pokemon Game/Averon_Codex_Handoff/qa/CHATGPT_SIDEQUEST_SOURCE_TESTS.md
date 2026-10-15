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

1. Run full coast/base authoring, then overlay installer with actual
   current layouts and flag constants; guard may intentionally stop.
2. Add new overlay step to reproducible authoring pipeline.
3. Regenerate maps, run existing map and dialogue checks, compile the GBA game.
4. Add engine-level event/save tests for both quest chains and failure states.
5. Run focused mGBA smoke test, including save/reload and rewards.
6. Test compatibility with Delta later.

Do not mark the quests built or playable until the above is actually
verified. Current status: **AUTHORED SOURCE; COMPILATION/RUNTIME PENDING**.
