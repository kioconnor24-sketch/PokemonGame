# Opening runtime results — in progress

Emulator: mGBA 0.10.5. First custom ROM hash:
6f66b71ff51aea4e7d8a7af20be6bf9885ae730b4edc758c3df43150ab5af787.
Screenshots and controller-action logs: evidence/m1/ from workspace root.

| Check | Result | Evidence / limit |
|---|---|---|
| Compiles native opening | PASS | build.log, exit 0 |
| New game reaches Saltmere | PASS | proto-arrive.png, welcome-complete.png |
| Greenhouse interior enter/exit | PASS | greenhouse-enter.png, greenhouse-return.png |
| Greenhouse task accepted and completed | PASS | tray-complete.png |
| Greenhouse awards Snivy | PASS | snivy-offer.png, snivy-party.png |
| Decline starter then return | PASS | starter-declined.png, starter-retry.png |
| Native save/reset/Continue | PASS | native-save.png, continue-menu3.png, save-reloaded.png |
| Snivy follows after save load/movement | PASS | follower-after-load.png |
| Follower appears immediately after award | FIX BUILT; RETEST PENDING | added registered UpdateFollowingPokemon special |
| Renn uses assigned counter starter | PASS after fix | v4-counter-starter.png shows Fennekin vs Snivy; first ROM failed |
| Route/Windrow/capture | PASS for main traversal and Bunnelby capture | meadow-entry.png, capture-result.png, windrow-arrival.png |
| Windrow Berry activity | PASS for award path | windrow-berry-prompt.png, windrow-berries-given.png |
| Workshop/harbor starter branches | NOT RUN | next tests |
| All visit orders, party/bag full, loss recovery | NOT RUN | do not infer passes from script inspection |
| Delta iPhone test | NOT RUN | separate user device test |

Renn defect (P1): RIVAL_BATTLE_HEAL_AFTER=1, RIVAL_BATTLE_TUTORIAL=3.
Upstream battle_setup.c tested any shared bit with 3, so heal-only battles
entered tutorial handling. Fix requires all tutorial bits to be present.
The normal tutorial flag value 3 retains its behavior; flag 1 preserves
safe early-rival loss healing while using the actual trainer team.
Renn's completed-battle script also heals the party after victory.

Corrected ROM: evidence/m1/averon-saltmere-v4.gba,
SHA256 81796b63d347fb86a9fc3c22b4ca6d5f446da724dda87e594549364547bee10a.
It loaded the pre-battle native save and executed the counter-starter battle.
Source checkpoint 5cc22201bd contains the follower and battle-flag fixes.

Walkable catch-grass correction built in v5:
847ee8cc94e260e148c9ee97334c2dcc4a3d7d1f62cc27ca1abb61b10d1fac55.
The first authoring source sampled a colliding tree cell; MB_TALL_GRASS was
verified from the real metatile attributes and added to static map checks.
Saved viewport tiles can preserve old graphics after a layout change; fresh
saves are required for clean visual reviews. Existing save resumed for the
capture/traversal tests, and old cached vegetation remains a known update issue.

M0 untouched base battle/save sequence was deferred on explicit user steering.
These custom-ROM passes do not retroactively complete that baseline test.
