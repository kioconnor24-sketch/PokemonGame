#ifndef GUARD_AVERON_REGION_SAVE_H
#define GUARD_AVERON_REGION_SAVE_H

// Two-region save state (owner-approved isolated implementation, Issue #15
// comment 6209235704). An 8-byte anchor in SaveBlock2 (checksummed with the
// rest of sector 0) marks a save written by this format; a 64-byte CRC-32
// record in SaveBlock3 holds the region state. Both live in logical sector 0,
// so one physical sector write carries the anchor, the record and the footer.
//
// Averon badges stay canonical in FLAG_BADGE01_GET..FLAG_BADGE08_GET; the
// record only mirrors them so a spliced or stale record is detected. Sinnoh
// badges, the active region, return warps and healers live in the record.
// Saves without an anchor load as legacy Averon-only saves, in RAM only.

#define AVERON_REGION_ANCHOR_SIZE   8
#define AVERON_REGION_RECORD_SIZE   64
#define AVERON_REGION_SAVE_FORMAT   2

// Region codes stored in the record. Not the engine's enum Region.
enum
{
    AVERON_SAVE_REGION_NONE,
    AVERON_SAVE_REGION_AVERON,
    AVERON_SAVE_REGION_SINNOH,
    AVERON_SAVE_REGION_COUNT,
};

#define AVERON_REGION_BADGES 8

// How a candidate save slot's region data was judged.
enum AveronRegionSlotClass
{
    AVERON_REGION_SLOT_CURRENT,     // anchor and record valid for this slot
    AVERON_REGION_SLOT_LEGACY,      // no anchor: written before this format
    AVERON_REGION_SLOT_CORRUPT,     // anchor or record damaged, stale or spliced
    AVERON_REGION_SLOT_UNSUPPORTED, // a newer format this build must not touch
};

// Why the last load could not use region data, if it couldn't.
enum AveronRegionLoadIssue
{
    AVERON_REGION_LOAD_OK,
    AVERON_REGION_LOAD_LEGACY_MIGRATED, // legacy save; defaults derived in RAM
    AVERON_REGION_LOAD_ROLLED_BACK,     // newest slot rejected, older slot used
    AVERON_REGION_LOAD_UNSUPPORTED,     // newer format found; load and saving refused
};

struct AveronRegionState
{
    u8 activeRegion;
    u8 sinnohBadges;          // bit 0 is Badge 1
    struct WarpData returnWarp[AVERON_SAVE_REGION_COUNT];
    u16 healLocation[AVERON_SAVE_REGION_COUNT]; // 0 is unset
};

// Engine adapters. Invalid regions or badge numbers fail closed.
u32 AveronRegion_GetActive(void);
bool32 AveronRegion_SetActive(u32 region);
bool32 AveronRegion_HasBadge(u32 region, u32 badgeNumber);
bool32 AveronRegion_SetBadge(u32 region, u32 badgeNumber, bool32 earned);
u32 AveronRegion_CountBadges(u32 region);
bool32 AveronRegion_GetReturnWarp(u32 region, struct WarpData *warp);
bool32 AveronRegion_SetReturnWarp(u32 region, const struct WarpData *warp);
void AveronRegion_ClearReturnWarp(u32 region);
u32 AveronRegion_GetHealLocation(u32 region);
bool32 AveronRegion_SetHealLocation(u32 region, u32 healLocationId);
bool32 AveronRegion_IsWarpShapeValid(const struct WarpData *warp);

// Save integration, called from new_game.c, save.c and load_save.c.
void AveronRegionSave_InitNewGame(void);
void AveronRegionSave_Seal(u32 saveCounter);
enum AveronRegionSlotClass AveronRegionSave_ClassifySlot(u32 slot, u32 saveCounter);
void AveronRegionSave_BeginLoad(void);
void AveronRegionSave_NoteRejectedSlot(enum AveronRegionSlotClass slotClass);
void AveronRegionSave_FinishLoad(u8 saveStatus);
u32 AveronRegionSave_GetLoadIssue(void);
bool32 AveronRegionSave_IsWriteBlocked(void);
// Full origins are read only after a known format has been initialized or
// every legacy Pokemon container has been normalized during load.
bool32 AveronRegionSave_UsesWideOrigins(void);

// Exposed for tests.
u32 AveronRegionSave_Crc32(const u8 *data, u32 size);
u32 AveronRegionSave_RecordCrc(const u8 *record);
bool32 AveronRegionSave_GetState(struct AveronRegionState *state);

#endif // GUARD_AVERON_REGION_SAVE_H
