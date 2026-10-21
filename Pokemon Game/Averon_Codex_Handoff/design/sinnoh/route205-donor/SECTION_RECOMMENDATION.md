# Owner decision: saved sections for the Route 204 → Floaroma → Route 205 corridor

**Status:** a recommendation only. Nothing is allocated; every staged header says `MAPSEC_PENDING_OWNER`, and the
Route 204 installer refuses sections that don't exist.

**Context:**
- Approved so far: 219 Route 202, 220 Lake Verity (shared by both Verity maps), 221 Jubilife (+ interiors),
  222 Route 203, 223 Oreburgh Gate.
- Ordinary met-origin codes are limited: roughly 29 remain after 223, against far more Sinnoh place names. Sharing a
  code where the original games already treat an area as part of a larger place saves codes for genuinely distinct
  places.
- A section sets two things players see: the **map-name popup** on entry, and the **met location** on a caught
  Pokémon's summary. Sharing a section means both show the shared name.

## Recommendation: 3 codes for 6 maps

| Proposed | Name shown | Maps | What players see |
| --- | --- | --- | --- |
| next free (224) | ROUTE 204 | Route 204, **Ravaged Path** | Inside the cave, the popup and met location say ROUTE 204 instead of RAVAGED PATH. |
| next free (225) | FLOAROMA TOWN | Floaroma Town, **Floaroma Meadow** | The meadow shows FLOAROMA TOWN (same pattern as Lake Verity's two maps). |
| next free (226) | ROUTE 205 | Route 205 South and North | Both halves show ROUTE 205, as in the original games. |

**Alternative: 5 codes.** Give Ravaged Path and Floaroma Meadow their own names. That is more faithful to the
original games (both had distinct names), but it spends 2 more of the scarce codes on side areas.

**Unchanged either way:** existing IDs, save encoding and old-save meaning. The values are append-only and
contiguous after 223. Choosing the numbers and names is the owner's decision; this note only frames it.
