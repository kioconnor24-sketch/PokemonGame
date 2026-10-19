# Route 201 region UI: PokéNav MAP, Town Map and Fly are refused

Built by `map_qa selftest --only route201` from this PR's head, with the TEST-ONLY fixture `positive-route201-region-ui-refused.json`. The fixture adds a Route 201 on-transition grant: the PokéNav flag, the Fly licence and a Town Map. It is a throwaway tree, never this branch. Test ROM `6ddf0e53…`.

In every run, all three entry points are refused on Route 201 (section 217). Each one returns to a normal, non-black field where the player can move. See `run-fix1/0019-0021-region-ui-*.png`.

| Run | Harness | Verdict |
|---|---|---|
| `selftest-timed-hold` | main's map_qa | FAIL 21/24: all 7 region-UI checks PASS. Sandgem→Route 201 seam leg overshot to (62, 6). |
| `rerun1` | main's map_qa | PASS 23/23 |
| `rerun2` | main's map_qa | FAIL 21/23: all 7 region-UI checks PASS. Route 201→Sandgem leg overshot to (1, 12). |
| `run-fix1`, `fix2`, `fix3` | map_qa from `claude/map-qa-seam-step` `06772c62` | **PASS 23/23 each** |

**The failures were the harness, not the map.** Main's seam check holds the direction for 0.3 s of wall-clock time, and that can start a second step. On the same ROM the overshoot came and went, and hit different seams in each direction, including a crossing with no test script involved. The fix takes one real step, released when the tile changes. It is a separate tooling PR.

The production acceptance in `../` used the old harness and passed 35/35 on both builds. An overshoot can only cause a *false failure*, because every seam leg asserts the exact landing tile. So those passes stand.
