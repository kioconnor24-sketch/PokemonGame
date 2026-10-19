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

### Issues found by the self-test, and fixes (committed in `efebc88e`, verified by run 2)

1. **The pocket probe ran in the wrong map.**
   - **Cause.** After the Center warp checks, the player was still inside the Center. The probe's `go()` to Sandgem (4, 14) silently did nothing, and `can_leave` then measured the Center (`at: CENTER_1F (6, 8)`).
   - **Fix.**
     - `pocket()` now travels to the map, and fails under separate setup names if it cannot reach the entry tile or does not land in the pocket.
     - It then really tries to walk out: it routes to every exit, then presses each direction.
     - The check passes only if the player leaves the pocket tiles.
2. **An unreachable seam crashed the run instead of failing the seam check.**
   - **Cause.** `walk_path` raised `Stuck`, which aborted the run as "driver got stuck". The negative fixture must fail on its named seam check, so a crash doesn't count.
   - **Fix.** `go()` turns `Stuck` into "could not reach the tile", which fails the `… up seam …` check itself.

Run 1 is kept unchanged as the record of what the self-test caught.

## Fixture self-test run 2 (`selftest-run2-20261018/`): **6/6 as expected**

- **Tool:** `map_qa.py` at `38b11f8c` (the two fixes above), on the same throwaway worktree at `a91d7096`.
- **Builds:** each fixture was rebuilt for real. The no-edit `positive-sandgem` build reproduces #133's NORMAL ROM exactly (`f1d212fe913c…`), so the fixture tree adds nothing of its own.

| Fixture | Expect | Static | Run | Fails on (negatives) |
| --- | --- | --- | --- | --- |
| positive-sandgem | PASS | clean | PASS + fresh CONTINUE PASS | — |
| positive-loop-connection | PASS | clean | PASS + fresh CONTINUE PASS | — |
| negative-one-way-connection | FAIL | clean | FAIL | `up seam … and back`: the back leg is blocked at (x, 27) |
| negative-warp-return | FAIL | clean | FAIL | `warp 1 (25, 9) … and back`: it returned to (15, 10) |
| negative-ledge-pocket | FAIL | `one-way-pocket` | FAIL | `has no one-way pocket`. The probe stood at (4, 14), really jumped to (4, 16), tried routing and every direction, and ended trapped at (4, 17) |
| negative-unreachable-seam | FAIL | `exit-unreachable` | FAIL | `up seam …` with `could not reach the seam tile`, with no driver crash |

## Region-map UI fixtures, run 5 (`selftest-run5-region-ui-20261019/`): **8/8 as expected**

- **Tool:** `map_qa.py` at `20fecce8`.
- **Throwaway tree:** main `0c9ec0c3` (after #136/#138/#146; cries OFF by default).
- **Scope:** all eight fixtures, the six earlier ones as a regression run plus the two new ones.

| New fixture | Expect | Run | Detail |
| --- | --- | --- | --- |
| positive-sinnoh-region-ui-refused | PASS | PASS + fresh CONTINUE PASS | In Sinnoh Sandgem, PokéNav MAP, the Town Map item and Field Kit FLY are all refused. Each returns to a non-black field where the player can move. FLY shows "Can't use that here." |
| negative-region-ui-legacy-section | FAIL | FAIL on `region UI: … refused` ×3 | Sandgem relabelled `MAPSEC_LITTLEROOT_TOWN`. All three open the Hoenn map ("FLY to where?" at Littleroot). The back-to-field checks still pass, so the detector separates "opened" from "stuck" |

The six earlier fixtures all behaved as in run 2.

**Bug caught on the way: run 3** ([`run3-selftest-keyerror.json`](selftest-run5-region-ui-20261019/run3-selftest-keyerror.json)), at `8626c3ad`.
- **Symptom:** the six old fixtures passed, but both new ones stopped with `KeyError('ITEM_TOWN_MAP')`.
- **Cause:** `map_qa run` imports the driver modules (`emu`, `game`) from the **engine tree under test**, which predated the new probe constants.
- **Fix** (`20fecce8`): register them on the imported `emu` at run time.
- Run 4 then confirmed both region fixtures before this full run 5.

## Limitations

- The fixture entry uses the DEV continue-warp save, so there is no ordinary story entrance.
- Fixtures are TEST-ONLY placements in a throwaway tree.
- The fixtures cover the NORMAL cries-OFF build only. RELEASE was not run through `map_qa`, although #133's own acceptance covers RELEASE.
- No human play and no Delta.
- `static` models walking and ledges only. Surf, Cut and other HM moves are not modelled.
