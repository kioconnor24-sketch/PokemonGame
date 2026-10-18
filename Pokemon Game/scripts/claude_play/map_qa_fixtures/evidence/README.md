# map_qa evidence (2026-10-18)

These files are real mGBA runs, observed read-only through GDB with controller input. They contain JSON results, event logs and selected screenshots. No ROM, ELF, save or savestate is committed.

## Smoke run on the #133 final head (`smoke-sandgem-final-head/`)

- **ROM:** NORMAL `f1d212fe913c…` (#133 head `f3570d73`). The batch is `MAP_SANDGEM_TOWN` plus `MAP_SANDGEM_TOWN_POKEMON_CENTER_1F`.
- **Entry:** the DEV continue-warp save fixture.
- **`run/`: PASS, 26/26 checks.**
  - Closed edges, 3 in town and 5 in the Center.
  - Warp round trips: the town door, and both Center mats. Both mats return through the one door.
  - Follower visible after each arrival; an exit is reachable after each warp.
  - The Start menu opens and closes; SAVE.
- **`continue/`: PASS.** A fresh process restores the save through CONTINUE.

## Fixture self-test run 1 (`selftest-run1-20261018/`): 4/6 as expected

This run used the throwaway worktree at `a91d7096`, with each TEST-ONLY placement applied, rebuilt with `CRIES=off` and played. `selftest.json` has the table.

| Fixture | Expect | Static | Run | As expected? |
| --- | --- | --- | --- | --- |
| positive-sandgem | PASS | clean | PASS + fresh CONTINUE PASS | yes |
| positive-loop-connection | PASS | clean | PASS + fresh CONTINUE PASS; real seam crossings both ways | yes |
| negative-one-way-connection | FAIL | clean (reciprocity is #125's job) | FAIL: up seam lands at (x, 27), down is blocked | yes |
| negative-warp-return | FAIL | clean | FAIL: the Mart door (25, 9) enters the Center, and its mat returns to the Center door (15, 10), not (25, 10) | yes |
| negative-ledge-pocket | FAIL | `one-way-pocket` found | **PASS: runtime bug** | **no** |
| negative-unreachable-seam | FAIL | `exit-unreachable` found | FAIL, **but for the wrong reason** (driver `Stuck`) | **no** |

### Issues found by the self-test, and fixes (committed, not yet re-run in mGBA)

1. **The pocket probe ran in the wrong map.**
   - **Cause.** After the Center warp checks, the player was still inside the Center. The probe's `go()` to Sandgem (4, 14) silently did nothing, and `can_leave` then measured the Center (`at: CENTER_1F (6, 8)`).
   - **Fix.**
     - `pocket()` now travels to the map, and fails under separate setup names if it cannot reach the entry tile or does not land in the pocket.
     - It then really tries to walk out: it routes to every exit, then presses each direction.
     - The check passes only if the player leaves the pocket tiles.
2. **An unreachable seam crashed the run instead of failing the seam check.**
   - **Cause.** `walk_path` raised `Stuck`, which aborted the run as "driver got stuck". The negative fixture must fail on its named seam check, so a crash doesn't count.
   - **Fix.** `go()` turns `Stuck` into "could not reach the tile", which fails the `… up seam …` check itself.

**Next step:** re-run `selftest` (about 50 minutes) and commit `selftest-run2`. Expected result: 6/6.
