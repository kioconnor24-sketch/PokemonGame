# Route 201: production acceptance (PR #150 head `0476a5ce`)

Real mGBA 0.10.5 play through the `claude_play` GDB driver, using `map_qa run` on the production ROMs built from this PR's head (no test edits in the tree).

| Build | ROM SHA-256 | Linked size | Run | Fresh Continue |
|---|---|---|---|---|
| NORMAL (`make`, cries OFF) | `a93de284…8266d` | 17,326,920 B (+3,072 B over main `b0219d88`) | **PASS 35/35** | **PASS 3/3** |
| RELEASE (`make RELEASE=1`) | `4e085926…7827` | 17,446,088 B (+3,072 B) | **PASS 35/35** | **PASS 3/3** |

Batch: `MAP_ROUTE201`, `MAP_SANDGEM_TOWN`, `MAP_SANDGEM_TOWN_POKEMON_CENTER_1F`.

**What each run checks (both builds identical):**
- **Seams both ways**, on rows 6, 8 and 9 of the open span:
  - Route 201 (63, y) → Sandgem (0, y + 4) and back;
  - Sandgem (0, y) → Route 201 (63, y − 4) and back.
  - The screenshots show whole 2×2 trees across the boundary, and the "SANDGEM TOWN" / "ROUTE 201" popups.
- **Closed edges block:**
  - Route 201 south at (16, 21), toward Twinleaf;
  - Route 201 west at (0, 10) and (0, 14), toward Lake Verity;
  - Sandgem north and south;
  - the Center's walls.
- **Warps:** the Center door both ways and both Center mats. The follower stays visible and an exit is reachable after every warp.
- **Save/reload:** the Start menu, then SAVE, then a fresh mGBA process on CONTINUE restores map, position, flags and party (`*-continue/continue-check.json`). This batch ends, and saves, in the Sandgem Center. **`route201-save/` saves on Route 201 itself:** PASS 11/11 and Continue 3/3 on both builds, restored at Route 201 (63, 9).

**Entry is a disclosed DEV-only fixture.** `map_qa fixture-save` sets the engine's own CONTINUE_GAME_WARP to Sandgem (15, 10) on a copy of a real save. There is still no ordinary Averon → Sinnoh entrance. No ROMs, ELFs, saves or savestates are committed. The `state-*.json` files are decoded field summaries.

**Region UI on Route 201:** PokéNav MAP, the Town Map and Fly are all refused, and each returns to a working field. See `region-ui/`, which also covers the harness timing flake found and fixed on the way.

**Final head `633ddcab`:** a clean rebuild reproduces both ROMs byte-for-byte (`a93de284…` / `4e085926…`, 0 compiler warnings), so every run above applies to it.

Native: Averon suite **286/286**, including `averon_route201_location.c` (2 tests).
