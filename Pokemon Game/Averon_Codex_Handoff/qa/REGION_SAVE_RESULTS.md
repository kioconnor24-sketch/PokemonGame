# Two-region save: implementation and evidence

Owner approval: isolated implementation and testing of the 8-byte SaveBlock2
anchor plus 64-byte SaveBlock3 record (Issue #15 comment 6209235704). This
branch implements that design from `REGION_SAVE_INTEGRITY_PROPOSAL.md`
(`codex/two-region-groundwork`). Merging it needs its own exact
`HANDOFF_APPROVED` line for the protected paths below; nothing here is
merged or registered in main yet.

Status: **TESTED ON ISOLATED BRANCH / INTEGRATION PENDING**.

## What changed

| File | Change |
| --- | --- |
| `engine/include/global.h` (protected) | `SaveBlock2.filler_90[8]` renamed `averonRegionAnchor[8]`, same offset (0x90) and size, so SaveBlock2's size and checksum length are unchanged. `SaveBlock3` gains `ALIGNED(4) u8 averonRegionRecord[64]` as its last member: offset 4, after the existing 4-byte block (dexNavChain plus ABI padding, which are kept). SaveBlock3 grows from 4 to 68 bytes. SaveBlock1 and PC storage are untouched. |
| `engine/src/save.c` (protected) | Both slot-sector writers seal the anchor and record with the footer's counter before copying logical sector 0, and refuse to write while a newer format is present. Slot validation now also requires every sector of a slot to carry one counter, and each slot to pass region classification before it can be chosen. A newer-format slot makes the load return `SAVE_STATUS_CORRUPT`, with no fallback. The #50 bounds checks are kept. |
| `engine/src/new_game.c` (protected) | `NewGameInitData` initializes the record and clears the anchor after `ClearSav3`. |
| `engine/include/averon_region_save.h`, `engine/src/averon_region_save.c` (new) | Codec, validation and the engine adapters listed below. |
| `engine/test/averon_region_save.c` (new) | 13 native flash tests, 125 parameter runs in all. |
| `scripts/test-averon-region-save.py` (new) | Source contract checks, plus `--mutations`. |
| `engine/test/save.c` | Upstream size pin `T_SAVEBLOCK3_SIZE` 4 → 68. The SaveBlock1, SaveBlock2 and PokemonStorage pins are unchanged and still pass. |

`load_save.c` is not changed. It was in the approved scope, but the load
hook fits in `LoadGameSave` in `save.c`.

## Format

The anchor and the record sit in logical sector 0, which is the first
sector written. One physical write therefore carries the anchor, which the
primary checksum covers; the record, which its own CRC covers; and the
footer counter.

Anchor (SaveBlock2 0x90..0x97): `"AVRS"`, u16 format = 1, u16 ~format.

Record (SaveBlock3 offset 4, little-endian):

| Bytes | Meaning |
| --- | --- |
| 0..3 | `"AVRR"` |
| 4..5 / 6..7 | format 1 / length 64 |
| 8..11 | save counter; must equal the sector footer and the slot counter |
| 12..15 | CRC-32/ISO-HDLC over the record with this field zeroed |
| 16 | active region: 1 Averon, 2 Sinnoh (0 or any other value is corrupt) |
| 17 | Averon badge mirror; must equal FLAG_BADGE01..08 in the same slot |
| 18 | Sinnoh badges, bit 0 = Badge 1 (canonical store) |
| 19 | zero |
| 20..27 / 28..35 | Averon / Sinnoh return warp: u8 group, u8 map, s16 warp, s16 x, s16 y; all 0xFF when unset |
| 36..37 / 38..39 | Averon / Sinnoh heal location (`HEAL_LOCATION_NONE` = unset) |
| 40..43 | playerTrainerId of the same SaveBlock2 |
| 44..63 | zero |

The tag values, format number and region codes were picked for this
isolated implementation. They become fixed only when it is merged. A return
warp is valid only if the engine's s8 warp API can take it to a real map: the
group is below `MAP_GROUPS_COUNT`, the map is below the generated
`MAP_GROUP_COUNT[group]`, and the warp is either indexed with x = y = -1 and
below the map's warp count, or a coordinate (warpId -1) inside the map's
layout.

## Load, migration, save, rollback

1. A slot is loadable only when all 14 IDs are present, the signatures and
   checksums are correct, every sector has the same counter, and region
   classification passes. Classification reads flash only. It returns:
   - CURRENT: the anchor and every record rule hold.
   - LEGACY: the anchor is all zero. Any old SaveBlock3 tail is ignored.
   - CORRUPT: a malformed anchor, or an anchor with a missing or damaged
     record.
   - UNSUPPORTED: a valid anchor with a newer format.
2. A CORRUPT newest slot makes the engine's existing logic pick the older
   whole slot. That returns `SAVE_STATUS_ERROR`, so the main menu shows its
   existing "previous save will be loaded" message. If both slots fail, the
   load is `SAVE_STATUS_CORRUPT`. Slots are never mixed.
3. LEGACY: the record defaults are derived in RAM: Averon active, no Sinnoh
   badges, no return warps or healers. Averon badges stay in their existing
   flags. Nothing is written to flash on load. The next ordinary save writes
   the anchor and the record.
4. UNSUPPORTED: nothing is loaded, and every flash write is refused, so an
   older build can never overwrite newer progress. That covers the slot
   sectors, the Hall of Fame / Trainer Hill / Recorded Battle sectors (which
   the New Game "different file" save used to erase first), and
   `TryWriteSpecialSaveSector`. The player sees the existing "save file
   erased" text. An ordinary save attempt (`TrySavingData`) returns the
   existing in-game save error, without opening the save-failed screen. If a
   link save still reaches that screen, it skips its recovery wipe and shows
   "backup memory damaged / cannot continue", because the sectors it would
   wipe are the newer save. **Owner decision pending:** a dedicated
   downgrade/unsupported-save message.

## Engine adapters (callable, registered in the ROM via save.c)

`AveronRegion_GetActive/SetActive`, `HasBadge/SetBadge/CountBadges(region, n)`
(the Averon calls read and write the existing badge flags; Sinnoh uses the
record), `Get/Set/ClearReturnWarp`, `Get/SetHealLocation`,
`IsWarpShapeValid`. Invalid regions (including values above 0xFF, which a
short enum would otherwise wrap into a valid one), badge numbers outside
1..8, warps and heal IDs are all rejected, and nothing is changed.
Not installed yet: cap and obedience selection by region (the Sinnoh cap and
obedience numbers are owner-reserved), Fly and whiteout region gating, and
the travel transaction. These come next and build on these adapters.

## Evidence (this machine, native mGBA test runner, no emulator GUI)

Run: `make check TESTS="Averon region save"`, **13/13 PASS** (125 runs):

- Layout: anchor at 0x90 (8 bytes), record at SaveBlock3 offset 4, SaveBlock3
  68 bytes, record before the footer. CRC check value 0xCBF43926.
- Round trip of both regions through flash, with **zero flash writes during
  load** (all three flash write pointers hooked).
- SaveBlock1, SaveBlock2 and PC storage are byte-exact after save and load.
- Legacy (no tail, leftover bytes, or a stale CRC-valid record left without an anchor): loads OK, keeps party, Bag,
  money and flags byte-exact, Averon badges come from the flags, Sinnoh
  starts at 0, nothing is written on load, and the next save upgrades the
  file.
- All 512 single-bit flips in the record: each rejected, older slot loaded.
- All 64 anchor bit flips with the sector checksum recomputed: each rejected.
- 20 CRC-valid semantic corruptions: counter ±1, trainer ID, badge mirror,
  region 0/3/255, both reserved areas, heal location out of range or 0xFFFF,
  warp group/map/index/coordinates/shape, length, tag, zeroed record, erased
  record. Each rejected.
- A record copied from the other slot (valid CRC, stale): rejected.
- A slot mixing two saves (footer counter changed; older sector 0 spliced
  in; spliced with a forged counter): rejected.
- Both slots corrupt: `SAVE_STATUS_CORRUPT`, and no half-loaded region state.
- Counter wrap from 0xFFFFFFFF to 0: picks the newest, and rolls back across
  the wrap.
- Newer format: load returns CORRUPT, writes are blocked, and all 28 slot
  sectors are unchanged afterwards.
- Power loss at each of the 14 sector writes (the sector is left erased and
  nothing after it is written) plus the no-loss case, at all 14 rotations,
  so both slot directions are covered: always the last whole slot, and a
  clean save afterwards loads.

GBA build: `make -j20 -O all` OK. EWRAM 226488 B (+68 vs main: +64 record,
+2 state, alignment).
Mutations: 15/15 killed. Full suite: 328 failures = the 327 expected plus the known Gimmick flake, after the SaveBlock3 size pin fix (`test/save.c`).

## Refused newer-format saves leave flash untouched (2026-10-16 follow-up)

**Defect found and fixed.** The first refusal only blocked the slot-sector
writers, and it marked each refused sector damaged. `TrySavingData` then
opened the save-failed screen, whose recovery (`CB2_WipeSave`) **programs
every damaged sector to zero**. So the first save attempt after the refusal
would have wiped the newer save it was meant to protect. Separately, the
New Game "different file" save erased sectors 28 to 31 (Hall of Fame,
Trainer Hill, Recorded Battle) before its blocked slot write, and
`TryWriteSpecialSaveSector` was not guarded. The earlier test called
`HandleSavingData` directly, so neither path was exercised.

Fix: `save.c` guards `TrySavingData` (an in-game error, no save-failed
screen), `HandleSavingData` (no erase or write for any save type; the caller
still sees a failure) and `TryWriteSpecialSaveSector`. `save_failed_screen.c`
never wipes while the refusal is in force.

New `engine/test/averon_region_save_refusal.c` (real flash, all 32 sectors
compared by CRC):
- `TrySavingData` for normal, different-file (New Game), Hall of Fame and
  link saves: returns error, sets `gSaveAttemptStatus`, opens no screen, and
  changes 0 of 32 sectors.
- `HandleSavingData` for all five save types, plus Trainer Hill and Recorded
  Battle special writes: 0 sectors changed, and the failure is still
  reported.
- The real save-failed screen driven through fade-in, wipe step and the
  "cannot continue" wait: 0 sectors changed.
- Manager audit item 3: `GetSaveBlocksPointersBaseOffset` returns the
  trainer-ID sum of the same slot the load falls back to (newest intact;
  record bit flip; anchor bit flip under a recomputed checksum; record copied
  from the older slot), independent of RAM.

Run: `make check TESTS="Averon region save"` **17/17 PASS**. Mutations
(each guard removed alone, temporary, reverted): no `TrySavingData` guard,
no `HandleSavingData` guard, no special-sector guard and no save-failed
wipe guard are each KILLED (4/4). Forcing every slot's region check to pass
fails 12 of 17 tests, including the pointer-selector test (2 of its 4
cases).
Source contract 11/11. `scripts/test-averon-region-save.py --mutations` now
also lists these four guards.
