@AGENTS.md

# Claude Code — Pokémon Averon current role
**Current owner-approved phase:** Read [CURRENT_PHASE_AND_HANDOFF.md](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md) and current [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) before any previous M1 instructions. M1 is accepted, Codex is **not** paused, and audio listening is deferred to later human QA. Old sole-Claude/PR #14/QUEST re-entry instructions are historical only.

## Working rules
- Own **specifically approved, nonoverlapping** implementation or testing in a `claude/*` branch/worktree. Codex may work simultaneously on disjoint technical infrastructure; verify live claims and PR diffs first.
- Prioritize small **owner-approved** playable-region slices and actual graphical mGBA checks, after the necessary geography/story/ID contracts are approved. Before detailed owner approval, work on scoped QA/tooling/review instead of inventing maps, Gym teams, story or asset IDs.
- For graphics/gameplay provide authentic controller input, screenshots, source/ROM SHA, true Save→Continue and precise PASS/PARTIAL/FAIL; clearly mark `DEV_FIXTURE`. Developer-operated QA and AI subagent review are *not* third-party human Playtest. Human audio listening remains pending on #23.
- For engine changes, use actual available toolchain, production build and focused regression on changed source; do not rerun already complete M1 suite for unchanged source. Reserve stable dirty worktrees. One `make` per build tree. Do not assume host paths/toolchain version from historical logs; verify.
- Honor normal PR review, GitHub protected-path handoffs, CI and no direct main pushes. If a prior guard still freezes maps, propose a safe separate reviewed policy change rather than bypassing it. No copyrighted ROMs, unlicensed assets or private saves committed.
- Current roles and tasks are on #15; [WORKFLOW](Pokemon%20Game/Averon_Codex_Handoff/development/WORKFLOW.md) governs changes. Prior `CLAUDE_SOLE_M1_EXECUTION_20261017.md` is an archived task plan, not an executable queue.

## Native test pitfalls (found 2026-10-16)

- `SINGLE_BATTLE_TEST` / `DOUBLE_BATTLE_TEST` are recorded **link** battles (`TRAINER_LINK_OPPONENT`): no whiteout money, no in-game trainer behaviour. Use `AI_SINGLE_BATTLE_TEST` / `AI_DOUBLE_BATTLE_TEST` for real trainer battles (opponent moves come from the AI; give it one move and use `EXPECT_MOVE`).
- The runner plays every battle as `BATTLE_TYPE_RECORDED`, and `GetAttackerObedienceForAction` returns `OBEYS` for recorded battles. To test obedience, clear that flag around a direct call in `THEN` and restore it.
- `THEN` sees the post-battle party only if the battle actually ended (a win, loss, run or capture). A battle left running skips end-of-battle code such as `TryRestoreHeldItems`.
- Post-battle Pickup and Honey Gather never fire in the native runner. A full-party capture opens the Gen 7 "party or box" prompt, which the runner cannot answer (it hangs): that case is Playtest's.
- In plain `TEST()`, `PARAMETRIZE` needs a variable named `i`. In battle tests, extra test parameters are fields of `results[i]`, not locals.
- `EXPECT_EQ(f(), x)` evaluates `f()` again when it prints a failure, so a call with side effects shows a misleading value. Store the result first.
- `CreateMon` gives no moveset and leaves HP at 0: set moves and call `CalculateMonStats`.
- A host CI script (`scripts/verify-averon-native-caps.py`) compiles the real `GetCurrentLevelCap` with stubs; a new call in `caps.c` needs a stub there too.
- Prove a new test with a temporary mutation of the code it guards, then revert and confirm `git diff` is clean before committing.

