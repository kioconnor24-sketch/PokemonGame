# Twinleaf Town: production acceptance (exterior-only)

Tested branch head `7089c15a` (engine tree `9d23369e`). This tree is #150 (Route 201) plus Twinleaf plus main through #161.

**Scope:**
- the Twinleaf Town exterior, 32 × 36, from the merged #156 candidate;
- section **218**, approved in Issue #15 comment 6271044156;
- the connection Route 201 `down` 0 ↔ Twinleaf `up` 0.

The four houses are **closed shells**: no warps, interiors, NPCs or story, as that decision records. The door tiles are solid (collision 1, the same as Sandgem's reserved buildings), so pressing into one only bumps. An interior proposal is preserved separately on `claude/twinleaf-interiors` for a future owner scope decision.

| Build | ROM SHA-256 | Linked size | mGBA run | Fresh Continue |
|---|---|---|---|---|
| NORMAL | `dc79c2e0…` | 17,329,424 B | **PASS 17/17** | **PASS 3/3** |
| RELEASE | `57d6a8a5…` | 17,448,560 B | **PASS 17/17** | **PASS 3/3** |

- **Compiler warnings:** 0 on both builds.
- **Native Averon:** **292/292**, including both new `averon_twinleaf_location.c` tests and the section-218 pins in `averon_sandgem_location.c` and `averon_location_compatibility.c`.

**mGBA checks (both builds):**
- Twinleaf `up` seam at columns 15, 16 and 17 → Route 201 (x, 21) and back.
- Route 201 `down` seam at columns 15–17 → Twinleaf (x, 0) and back.
- Route 201 ↔ Sandgem seams at rows 6, 8 and 9, still exact.
- Route 201's closed Lake Verity edges.
- The follower.
- The Start menu, then SAVE, then a fresh mGBA process CONTINUEs on the saved tile.

**Entry and evidence:** entry is a disclosed DEV continue-warp onto Twinleaf (16, 10). No ROMs or saves are committed.

**Negative tests:**
- `negative-twinleaf-wrong-offset` (TEST-ONLY, throwaway tree) shifts Twinleaf's `up` offset to 2 while Route 201 keeps `down` 0. That must fail the seam check. Result: **FAIL as required**: static audit `seam-mismatch`, and the real run fails `MAP_TWINLEAF_TOWN up seam (17, 0) -> MAP_ROUTE201 (15, 21) and back` (1/1 fixtures behaved as expected).
- Section identity is protected by native `STATIC_ASSERT`s (218, `MAPSEC_COUNT` 219) and by the Python namespace tests: 218 can't be moved, duplicated or widened, and 219 and above are rejected.

**Static checks:**
- map registry PASS, 955 pinned IDs, 12/12 mutations caught;
- preflight on 4 Sinnoh maps, 0 errors and 0 warnings;
- section pins exit 0;
- Python suites 18/18 and 60/60;
- orphan tree quarters: 0 (`sinnoh-tree-repair.py`).
