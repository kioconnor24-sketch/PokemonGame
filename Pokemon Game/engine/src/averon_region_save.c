#include "global.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "fieldmap.h"
#include "overworld.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "constants/heal_locations.h"
#include "constants/map_groups.h"
#include "data/map_group_count.h"

extern const struct MapHeader *const *const gMapGroups[];

// See averon_region_save.h for the format. Record layout (little-endian):
//   0..3   tag            4..5 format        6..7 length (64)
//   8..11  save counter, equal to the containing sector footer's
//   12..15 CRC-32/ISO-HDLC over the record with this field zeroed
//   16 active region  17 Averon badge mirror  18 Sinnoh badges  19 zero
//   20..27 Averon return warp  28..35 Sinnoh return warp
//          (u8 group, u8 map, s16 warp, s16 x, s16 y; all 0xFF when unset)
//   36..37 Averon healer  38..39 Sinnoh healer (0 when unset)
//   40..43 playerTrainerId of the same SaveBlock2
//   44..63 zero
// Anchor (SaveBlock2 0x90..0x97): tag, format, ~format.

#define REC_TAG          0
#define REC_FORMAT       4
#define REC_LENGTH       6
#define REC_COUNTER      8
#define REC_CRC         12
#define REC_ACTIVE      16
#define REC_AVERON_MASK 17
#define REC_SINNOH_MASK 18
#define REC_RESERVED_19 19
#define REC_RETURN      20 // + 8 * (region - 1)
#define REC_HEAL        36 // + 2 * (region - 1)
#define REC_TRAINER_ID  40
#define REC_RESERVED    44
#define RETURN_SIZE      8

#define ANCHOR_TAG        0
#define ANCHOR_FORMAT     4
#define ANCHOR_COMPLEMENT 6

static const u8 sRecordTag[4] = {'A', 'V', 'R', 'R'};
static const u8 sAnchorTag[4] = {'A', 'V', 'R', 'S'};

STATIC_ASSERT(sizeof(((struct SaveBlock2 *)0)->averonRegionAnchor) == AVERON_REGION_ANCHOR_SIZE, AveronRegionAnchorSize);
STATIC_ASSERT(offsetof(struct SaveBlock2, averonRegionAnchor) == 0x90, AveronRegionAnchorOffset);
STATIC_ASSERT(sizeof(((struct SaveBlock3 *)0)->averonRegionRecord) == AVERON_REGION_RECORD_SIZE, AveronRegionRecordSize);
// The record must sit wholly in logical sector 0's SaveBlock3 chunk.
STATIC_ASSERT(offsetof(struct SaveBlock3, averonRegionRecord) + AVERON_REGION_RECORD_SIZE <= SAVE_BLOCK_3_CHUNK_SIZE, AveronRegionRecordInSector0);
STATIC_ASSERT(TRAINER_ID_LENGTH == 4, AveronRegionTrainerIdLength);
STATIC_ASSERT(NUM_BADGES == AVERON_REGION_BADGES, AveronRegionBadgeCount);

static EWRAM_DATA u8 sLoadIssue = AVERON_REGION_LOAD_OK;
static EWRAM_DATA bool8 sWriteBlocked = FALSE;
static EWRAM_DATA bool8 sWideOriginsReady = FALSE;
static EWRAM_DATA bool8 sOriginsNeedFullSave = FALSE;

static u16 ReadU16(const u8 *p)
{
    return p[0] | (p[1] << 8);
}

static u32 ReadU32(const u8 *p)
{
    return p[0] | (p[1] << 8) | (p[2] << 16) | ((u32)p[3] << 24);
}

static void WriteU16(u8 *p, u16 value)
{
    p[0] = value;
    p[1] = value >> 8;
}

static void WriteU32(u8 *p, u32 value)
{
    p[0] = value;
    p[1] = value >> 8;
    p[2] = value >> 16;
    p[3] = value >> 24;
}

u32 AveronRegionSave_Crc32(const u8 *data, u32 size)
{
    u32 crc = 0xFFFFFFFF;
    for (u32 i = 0; i < size; i++)
    {
        crc ^= data[i];
        for (u32 bit = 0; bit < 8; bit++)
            crc = (crc >> 1) ^ (0xEDB88320 & -(crc & 1));
    }
    return ~crc;
}

// CRC over the record with its CRC field taken as zero.
u32 AveronRegionSave_RecordCrc(const u8 *record)
{
    u8 copy[AVERON_REGION_RECORD_SIZE];
    memcpy(copy, record, sizeof(copy));
    WriteU32(&copy[REC_CRC], 0);
    return AveronRegionSave_Crc32(copy, sizeof(copy));
}

static bool32 IsValidRegion(u32 region)
{
    return region == AVERON_SAVE_REGION_AVERON || region == AVERON_SAVE_REGION_SINNOH;
}

static u8 *Record(void)
{
    return gSaveBlock3Ptr->averonRegionRecord;
}

static void EncodeUnsetWarp(u8 *p)
{
    memset(p, 0xFF, RETURN_SIZE);
}

static bool32 IsUnsetWarp(const u8 *p)
{
    for (u32 i = 0; i < RETURN_SIZE; i++)
    {
        if (p[i] != 0xFF)
            return FALSE;
    }
    return TRUE;
}

// A warp the engine's s8 SetWarpDestination can take to a real map: an
// indexed warp (x = y = -1) below the map's warp count, or a coordinate
// inside the map's layout with warpId -1.
static bool32 IsWarpValid(s32 group, s32 num, s32 warpId, s32 x, s32 y)
{
    const struct MapHeader *header;
    if (group < 0 || group >= MAP_GROUPS_COUNT || group > 127)
        return FALSE;
    // Disabled regions retain numeric map IDs and counts, but have no
    // linked group. The overworld lookup dereferences the group pointer.
    if (gMapGroups[group] == NULL)
        return FALSE;
    if (num < 0 || num >= MAP_GROUP_COUNT[group] || num > 127)
        return FALSE;
    header = Overworld_GetMapHeaderByGroupAndId(group, num);
    if (header == NULL || header->mapLayout == NULL || header->events == NULL)
        return FALSE;
    if (warpId >= 0)
        return warpId <= 127 && x == -1 && y == -1 && warpId < header->events->warpCount;
    if (warpId != WARP_ID_NONE)
        return FALSE;
    return x >= 0 && y >= 0 && x <= 127 && y <= 127
        && x < header->mapLayout->width && y < header->mapLayout->height;
}

bool32 AveronRegion_IsWarpShapeValid(const struct WarpData *warp)
{
    return warp != NULL && IsWarpValid(warp->mapGroup, warp->mapNum, warp->warpId, warp->x, warp->y);
}

static bool32 IsEncodedWarpValid(const u8 *p)
{
    if (IsUnsetWarp(p))
        return TRUE;
    return IsWarpValid(p[0], p[1], (s16)ReadU16(&p[2]), (s16)ReadU16(&p[4]), (s16)ReadU16(&p[6]));
}

static bool32 IsHealLocationValid(u32 healLocationId)
{
    return healLocationId < NUM_HEAL_LOCATIONS; // HEAL_LOCATION_NONE is unset
}

static u8 CurrentAveronBadgeMask(void)
{
    u8 mask = 0;
    for (u32 i = 0; i < AVERON_REGION_BADGES; i++)
    {
        if (FlagGet(FLAG_BADGE01_GET + i))
            mask |= 1 << i;
    }
    return mask;
}

static bool32 IsRecordInitialized(const u8 *record)
{
    return memcmp(&record[REC_TAG], sRecordTag, sizeof(sRecordTag)) == 0
        && ReadU16(&record[REC_FORMAT]) >= 1
        && ReadU16(&record[REC_FORMAT]) <= AVERON_REGION_SAVE_FORMAT
        && ReadU16(&record[REC_LENGTH]) == AVERON_REGION_RECORD_SIZE;
}

// Defaults for a new game or a legacy save: in Averon, no Sinnoh badges,
// no return warps or healers.
static void InitRecordDefaults(void)
{
    u8 *record = Record();
    memset(record, 0, AVERON_REGION_RECORD_SIZE);
    memcpy(&record[REC_TAG], sRecordTag, sizeof(sRecordTag));
    WriteU16(&record[REC_FORMAT], AVERON_REGION_SAVE_FORMAT);
    WriteU16(&record[REC_LENGTH], AVERON_REGION_RECORD_SIZE);
    record[REC_ACTIVE] = AVERON_SAVE_REGION_AVERON;
    EncodeUnsetWarp(&record[REC_RETURN]);
    EncodeUnsetWarp(&record[REC_RETURN + RETURN_SIZE]);
}

static u8 *EnsureRecord(void)
{
    if (!IsRecordInitialized(Record()))
        InitRecordDefaults();
    return Record();
}

u32 AveronRegion_GetActive(void)
{
    u32 region = EnsureRecord()[REC_ACTIVE];
    return IsValidRegion(region) ? region : AVERON_SAVE_REGION_NONE;
}

bool32 AveronRegion_SetActive(u32 region)
{
    if (!IsValidRegion(region))
        return FALSE;
    EnsureRecord()[REC_ACTIVE] = region;
    return TRUE;
}

bool32 AveronRegion_HasBadge(u32 region, u32 badgeNumber)
{
    if (badgeNumber == 0 || badgeNumber > AVERON_REGION_BADGES)
        return FALSE;
    switch (region)
    {
    case AVERON_SAVE_REGION_AVERON:
        return FlagGet(FLAG_BADGE01_GET + badgeNumber - 1) != FALSE;
    case AVERON_SAVE_REGION_SINNOH:
        return (EnsureRecord()[REC_SINNOH_MASK] >> (badgeNumber - 1)) & 1;
    default:
        return FALSE;
    }
}

bool32 AveronRegion_SetBadge(u32 region, u32 badgeNumber, bool32 earned)
{
    u8 *record;
    if (badgeNumber == 0 || badgeNumber > AVERON_REGION_BADGES)
        return FALSE;
    switch (region)
    {
    case AVERON_SAVE_REGION_AVERON:
        if (earned)
            FlagSet(FLAG_BADGE01_GET + badgeNumber - 1);
        else
            FlagClear(FLAG_BADGE01_GET + badgeNumber - 1);
        return TRUE;
    case AVERON_SAVE_REGION_SINNOH:
        record = EnsureRecord();
        if (earned)
            record[REC_SINNOH_MASK] |= 1 << (badgeNumber - 1);
        else
            record[REC_SINNOH_MASK] &= ~(1 << (badgeNumber - 1));
        return TRUE;
    default:
        return FALSE;
    }
}

u32 AveronRegion_CountBadges(u32 region)
{
    u32 count = 0;
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; badge++)
        count += AveronRegion_HasBadge(region, badge);
    return count;
}

bool32 AveronRegion_GetReturnWarp(u32 region, struct WarpData *warp)
{
    const u8 *p;
    if (!IsValidRegion(region) || warp == NULL)
        return FALSE;
    p = &EnsureRecord()[REC_RETURN + RETURN_SIZE * (region - 1)];
    if (IsUnsetWarp(p) || !IsEncodedWarpValid(p))
        return FALSE;
    warp->mapGroup = p[0];
    warp->mapNum = p[1];
    warp->warpId = (s16)ReadU16(&p[2]);
    warp->x = (s16)ReadU16(&p[4]);
    warp->y = (s16)ReadU16(&p[6]);
    return TRUE;
}

bool32 AveronRegion_SetReturnWarp(u32 region, const struct WarpData *warp)
{
    u8 *p;
    if (!IsValidRegion(region) || !AveronRegion_IsWarpShapeValid(warp))
        return FALSE;
    p = &EnsureRecord()[REC_RETURN + RETURN_SIZE * (region - 1)];
    p[0] = warp->mapGroup;
    p[1] = warp->mapNum;
    WriteU16(&p[2], warp->warpId);
    WriteU16(&p[4], warp->x);
    WriteU16(&p[6], warp->y);
    return TRUE;
}

void AveronRegion_ClearReturnWarp(u32 region)
{
    if (IsValidRegion(region))
        EncodeUnsetWarp(&EnsureRecord()[REC_RETURN + RETURN_SIZE * (region - 1)]);
}

u32 AveronRegion_GetHealLocation(u32 region)
{
    u32 id;
    if (!IsValidRegion(region))
        return HEAL_LOCATION_NONE;
    id = ReadU16(&EnsureRecord()[REC_HEAL + 2 * (region - 1)]);
    return IsHealLocationValid(id) ? id : HEAL_LOCATION_NONE;
}

bool32 AveronRegion_SetHealLocation(u32 region, u32 healLocationId)
{
    if (!IsValidRegion(region) || !IsHealLocationValid(healLocationId))
        return FALSE;
    WriteU16(&EnsureRecord()[REC_HEAL + 2 * (region - 1)], healLocationId);
    return TRUE;
}

bool32 AveronRegionSave_GetState(struct AveronRegionState *state)
{
    if (state == NULL)
        return FALSE;
    memset(state, 0, sizeof(*state));
    state->activeRegion = AveronRegion_GetActive();
    state->sinnohBadges = EnsureRecord()[REC_SINNOH_MASK];
    for (u32 region = AVERON_SAVE_REGION_AVERON; region < AVERON_SAVE_REGION_COUNT; region++)
    {
        if (!AveronRegion_GetReturnWarp(region, &state->returnWarp[region]))
        {
            state->returnWarp[region].mapGroup = MAP_GROUP(MAP_UNDEFINED);
            state->returnWarp[region].mapNum = MAP_NUM(MAP_UNDEFINED);
            state->returnWarp[region].warpId = WARP_ID_NONE;
            state->returnWarp[region].x = -1;
            state->returnWarp[region].y = -1;
        }
        state->healLocation[region] = AveronRegion_GetHealLocation(region);
    }
    return TRUE;
}

void AveronRegionSave_InitNewGame(void)
{
    InitRecordDefaults();
    memset(gSaveBlock2Ptr->averonRegionAnchor, 0, AVERON_REGION_ANCHOR_SIZE);
    sWideOriginsReady = TRUE;
    sOriginsNeedFullSave = FALSE;
}

// Called by save.c just before logical sector 0 is copied for writing, with
// the counter that sector's footer will carry.
void AveronRegionSave_Seal(u32 saveCounter)
{
    u8 *record = EnsureRecord();
    u8 *anchor = gSaveBlock2Ptr->averonRegionAnchor;
    WriteU32(&record[REC_COUNTER], saveCounter);
    record[REC_AVERON_MASK] = CurrentAveronBadgeMask();
    record[REC_RESERVED_19] = 0;
    memcpy(&record[REC_TRAINER_ID], gSaveBlock2Ptr->playerTrainerId, TRAINER_ID_LENGTH);
    memset(&record[REC_RESERVED], 0, AVERON_REGION_RECORD_SIZE - REC_RESERVED);
    WriteU32(&record[REC_CRC], AveronRegionSave_RecordCrc(record));
    memcpy(&anchor[ANCHOR_TAG], sAnchorTag, sizeof(sAnchorTag));
    WriteU16(&anchor[ANCHOR_FORMAT], AVERON_REGION_SAVE_FORMAT);
    WriteU16(&anchor[ANCHOR_COMPLEMENT], (u16)~AVERON_REGION_SAVE_FORMAT);
}

// Physical sector holding logical sector `id` in a slot, or -1. The caller
// has already checked that the slot holds each of the 14 IDs exactly once.
static s32 FindSlotSector(u32 slot, u32 id)
{
    for (u32 i = 0; i < NUM_SECTORS_PER_SLOT; i++)
    {
        u16 sectorId;
        u16 physical = slot * NUM_SECTORS_PER_SLOT + i;
        ReadFlash(physical, offsetof(struct SaveSector, id), (u8 *)&sectorId, sizeof(sectorId));
        if (sectorId == id)
            return physical;
    }
    return -1;
}

static bool32 ReadSlotSaveBlock1Byte(u32 slot, u32 offset, u8 *value)
{
    u32 id = SECTOR_ID_SAVEBLOCK1_START + offset / SECTOR_DATA_SIZE;
    s32 physical;
    if (id > SECTOR_ID_SAVEBLOCK1_END)
        return FALSE;
    physical = FindSlotSector(slot, id);
    if (physical < 0)
        return FALSE;
    ReadFlash(physical, offset % SECTOR_DATA_SIZE, value, 1);
    return TRUE;
}

static bool32 ReadSlotAveronBadgeMask(u32 slot, u8 *mask)
{
    *mask = 0;
    for (u32 i = 0; i < AVERON_REGION_BADGES; i++)
    {
        u32 flag = FLAG_BADGE01_GET + i;
        u8 byte;
        if (!ReadSlotSaveBlock1Byte(slot, offsetof(struct SaveBlock1, flags) + flag / 8, &byte))
            return FALSE;
        if (byte & (1 << (flag % 8)))
            *mask |= 1 << i;
    }
    return TRUE;
}

static bool32 IsZero(const u8 *p, u32 size)
{
    for (u32 i = 0; i < size; i++)
    {
        if (p[i] != 0)
            return FALSE;
    }
    return TRUE;
}

// Judges one slot whose 14 sectors already passed the signature, ID,
// checksum and counter checks. Reads flash only; publishes nothing.
enum AveronRegionSlotClass AveronRegionSave_ClassifySlot(u32 slot, u32 saveCounter)
{
    u8 anchor[AVERON_REGION_ANCHOR_SIZE];
    u8 record[AVERON_REGION_RECORD_SIZE];
    u8 trainerId[TRAINER_ID_LENGTH];
    u8 averonMask;
    u32 format, sectorCounter;
    s32 physical;

    if (slot >= NUM_SAVE_SLOTS)
        return AVERON_REGION_SLOT_CORRUPT;
    physical = FindSlotSector(slot, SECTOR_ID_SAVEBLOCK2);
    if (physical < 0)
        return AVERON_REGION_SLOT_CORRUPT;
    ReadFlash(physical, offsetof(struct SaveBlock2, averonRegionAnchor), anchor, sizeof(anchor));
    if (IsZero(anchor, sizeof(anchor)))
        return AVERON_REGION_SLOT_LEGACY; // any old SaveBlock3 tail is ignored
    format = ReadU16(&anchor[ANCHOR_FORMAT]);
    if (memcmp(&anchor[ANCHOR_TAG], sAnchorTag, sizeof(sAnchorTag)) != 0
     || ReadU16(&anchor[ANCHOR_COMPLEMENT]) != (u16)~format
     || format == 0)
        return AVERON_REGION_SLOT_CORRUPT;
    if (format > AVERON_REGION_SAVE_FORMAT)
        return AVERON_REGION_SLOT_UNSUPPORTED;

    ReadFlash(physical, offsetof(struct SaveSector, saveBlock3Chunk) + offsetof(struct SaveBlock3, averonRegionRecord),
              record, sizeof(record));
    ReadFlash(physical, offsetof(struct SaveSector, counter), (u8 *)&sectorCounter, sizeof(sectorCounter));
    ReadFlash(physical, offsetof(struct SaveBlock2, playerTrainerId), trainerId, sizeof(trainerId));

    // With an anchor, a missing or damaged record is corrupt, never legacy.
    if (!IsRecordInitialized(record)
     || ReadU16(&record[REC_FORMAT]) != format
     || ReadU32(&record[REC_CRC]) != AveronRegionSave_RecordCrc(record)
     || ReadU32(&record[REC_COUNTER]) != sectorCounter
     || sectorCounter != saveCounter
     || !IsValidRegion(record[REC_ACTIVE])
     || record[REC_RESERVED_19] != 0
     || !IsZero(&record[REC_RESERVED], AVERON_REGION_RECORD_SIZE - REC_RESERVED)
     || memcmp(&record[REC_TRAINER_ID], trainerId, sizeof(trainerId)) != 0
     || !IsEncodedWarpValid(&record[REC_RETURN])
     || !IsEncodedWarpValid(&record[REC_RETURN + RETURN_SIZE])
     || !IsHealLocationValid(ReadU16(&record[REC_HEAL]))
     || !IsHealLocationValid(ReadU16(&record[REC_HEAL + 2])))
        return AVERON_REGION_SLOT_CORRUPT;
    if (!ReadSlotAveronBadgeMask(slot, &averonMask) || averonMask != record[REC_AVERON_MASK])
        return AVERON_REGION_SLOT_CORRUPT;
    return AVERON_REGION_SLOT_CURRENT;
}

void AveronRegionSave_BeginLoad(void)
{
    sLoadIssue = AVERON_REGION_LOAD_OK;
    sWriteBlocked = FALSE;
    sWideOriginsReady = FALSE;
    sOriginsNeedFullSave = FALSE;
}

void AveronRegionSave_NoteRejectedSlot(enum AveronRegionSlotClass slotClass)
{
    if (slotClass == AVERON_REGION_SLOT_UNSUPPORTED)
    {
        // Never let this build overwrite progress written by a newer one.
        sLoadIssue = AVERON_REGION_LOAD_UNSUPPORTED;
        sWriteBlocked = TRUE;
    }
    else if (sLoadIssue == AVERON_REGION_LOAD_OK)
    {
        sLoadIssue = AVERON_REGION_LOAD_ROLLED_BACK;
    }
}

static void NormalizeLegacyPokemonContainers(void)
{
    // FinishLoad precedes CopyPartyAndObjectsFromSave: normalize the saved
    // party, not the stale global party. All these containers were loaded
    // from the same validated full save slot. Do not touch flash here.
    for (u32 i = 0; i < PARTY_SIZE; i++)
        NormalizeMonLegacyOrigin(&gSaveBlock1Ptr->playerParty[i]);
    for (u32 box = 0; box < TOTAL_BOXES_COUNT; box++)
        for (u32 slot = 0; slot < IN_BOX_COUNT; slot++)
            NormalizeBoxMonLegacyOrigin(&gPokemonStoragePtr->boxes[box][slot]);
    for (u32 i = 0; i < DAYCARE_MON_COUNT; i++)
        NormalizeBoxMonLegacyOrigin(&gSaveBlock1Ptr->daycare.mons[i].mon);
#if IS_FRLG
    NormalizeBoxMonLegacyOrigin(&gSaveBlock1Ptr->route5DayCareMon.mon);
#endif
    for (u32 i = 0; i < MAX_FUSION_STORAGE; i++)
        NormalizeMonLegacyOrigin(&gPokemonStoragePtr->fusions[i]);
}

// Called after a complete validated slot has been copied to RAM. Format 2
// changes no structure sizes. Its anchor and record seal atomically in sector
// 0 on the next ordinary save; older binaries refuse that unsupported format.
void AveronRegionSave_FinishLoad(u8 saveStatus)
{
    if (saveStatus != SAVE_STATUS_OK && saveStatus != SAVE_STATUS_ERROR)
    {
        InitRecordDefaults(); // nothing usable was loaded
        sWideOriginsReady = FALSE;
        return;
    }
    if (IsZero(gSaveBlock2Ptr->averonRegionAnchor, AVERON_REGION_ANCHOR_SIZE))
    {
        // Legacy save: derive the defaults in RAM. Flash is untouched until
        // the player's next ordinary save writes the anchor and record.
        InitRecordDefaults();
        NormalizeLegacyPokemonContainers();
        sOriginsNeedFullSave = TRUE;
        if (sLoadIssue == AVERON_REGION_LOAD_OK)
            sLoadIssue = AVERON_REGION_LOAD_LEGACY_MIGRATED;
    }
    else if (ReadU16(&Record()[REC_FORMAT]) == 1)
    {
        NormalizeLegacyPokemonContainers();
        sOriginsNeedFullSave = TRUE;
        WriteU16(&Record()[REC_FORMAT], AVERON_REGION_SAVE_FORMAT);
        // Keep the loaded anchor unchanged in RAM until the normal writer
        // seals both fields together. No pre-upgrade flash bytes are changed.
        if (sLoadIssue == AVERON_REGION_LOAD_OK)
            sLoadIssue = AVERON_REGION_LOAD_LEGACY_MIGRATED;
    }
    sWideOriginsReady = !sWriteBlocked
        && ReadU16(&Record()[REC_FORMAT]) == AVERON_REGION_SAVE_FORMAT;
}

bool32 AveronRegionSave_UsesWideOrigins(void)
{
    return sWideOriginsReady
        && ReadU16(&Record()[REC_FORMAT]) == AVERON_REGION_SAVE_FORMAT;
}

bool32 AveronRegionSave_RequiresFullOriginSave(void)
{
    return sOriginsNeedFullSave;
}

void AveronRegionSave_FullOriginSaveComplete(void)
{
    // Called only after all fourteen sectors of a complete slot, including
    // the normalized PC/fusion containers, have committed successfully.
    sOriginsNeedFullSave = FALSE;
}

u32 AveronRegionSave_GetLoadIssue(void)
{
    return sLoadIssue;
}

bool32 AveronRegionSave_IsWriteBlocked(void)
{
    return sWriteBlocked;
}
