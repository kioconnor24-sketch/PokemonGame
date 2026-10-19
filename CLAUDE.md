@AGENTS.md

# Claude entry point
Read [live Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), the [operating contract](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md), [Sinnoh master roadmap](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_MASTER_PRODUCTION_ROADMAP.md) and [developer work packages](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_DEVELOPER_WORK_PACKAGES.md), then current PR heads/changed paths and your active handoffs. Under explicit owner delegation, design and construct ordinary Sinnoh geography for later owner revision while preserving story/encounter/level/saved-identity restrictions. You may personally merge **all eligible Fast Lane A and strictly bounded Fast Lane B** work after genuine applicable evidence/checks; broader high-risk changes still need an attributed independent Codex review before normal author-driven merge. Avoid duplicated reviews and manager bottlenecks. Native testing tips below remain relevant. GitHub comments cannot restart paused sessions.
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


