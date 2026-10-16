# Region travel: implementation and evidence

Status: **TESTED ON ISOLATED BRANCH / INTEGRATION PENDING**. This branch builds on
PR #56 (the region save). It adds no maps, flags, vars or save fields, and it
doesn't touch event scripts. No Sinnoh map exists yet, so the tests use Hoenn
maps as stand-ins: Petalburg for Averon and Oldale for Sinnoh.

## Code
- `engine/src/averon_region_travel.c` / `include/averon_region_travel.h`.
- `AveronRegion_BeginTravel(target, arrival)`: validates everything first. On
  failure nothing changes. On success it:
  - stores the departing region's return point and its last heal location;
  - makes the target region active;
  - aims whiteout and Teleport at the target's stored healer, or at the arrival
    point if the player hasn't healed in that region yet;
  - aims Escape Rope and Dig at the arrival point;
  - sets the warp destination. The caller then performs the warp.
  `arrival == NULL` returns the player to where they left the target region.
- `AveronRegion_BeginTravelSpecial`: script entry (`callnative`). Reads
  VAR_0x8004..0x8009 and rejects values that would wrap when narrowed to s8.

## Evidence (native mGBA test runner, this machine; no emulator GUI, no Delta)
`make check TESTS="Averon region travel"`: **6/6 PASS**.
- The departure is stored. Whiteout, Teleport and Escape Rope stay in the new
  region before the player heals there.
- Whiteout goes to the Pokémon Center of the region the player is in, both
  before and after the trip home. Each region keeps its own healer, and a
  return trip lands where the player left.
- 11 invalid requests (bad region or region values above 0xFF, same region,
  never visited, bad group, map, warp or coordinates, player standing off the
  map) each fail, and the region record, location, heal warp and escape warp
  are left byte-identical.
- Script entry: group, map or warp values that would wrap are rejected; a valid
  call succeeds.
- Travel, then save to flash and load: the state is identical, and the loaded
  game can travel home.
- Power loss at each of the 14 sector writes, plus the no-loss case, while
  saving right after travel: always the whole pre-travel or the whole
  post-travel state. The region record (sector 0) is never paired with the
  location from the other save (sectors 1..4).

The tests caught all 4 deliberate breaks of the travel code (no heal swap, no
escape warp, departing healer not stored, state changed before the last
validation check).

## Not done yet
- No in-game caller. That needs a map or an NPC script, which waits on owner
  map approval.
- Fly menu region gating, and cap and obedience selection by region (the
  Sinnoh numbers are owner-reserved).
