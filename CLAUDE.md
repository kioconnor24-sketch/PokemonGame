@AGENTS.md

# Claude entry point
Use the [operating contract](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md) and [integration queue](Pokemon%20Game/Averon_Codex_Handoff/development/INTEGRATION_QUEUE.md). Review Codex's high-risk production work when needed; Claude may self-merge only low-risk docs/trackers/design proposals or isolated test/QA tooling under the owner-approved tiered option-2 exact-head evidence/check rules. Own approved content/mGBA evidence under exact claims. The organizational reset does not resume a paused session.
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


