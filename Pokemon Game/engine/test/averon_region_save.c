#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "item.h"
#include "load_save.h"
#include "malloc.h"
#include "money.h"
#include "overworld.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "constants/heal_locations.h"
#include "constants/items.h"
#include "constants/map_groups.h"

// Real flash tests for the two-region save format (averon_region_save.c):
// round trip, legacy migration, corruption, rollback, power loss and the
// newer-format refusal. Each corrupt case must load the older whole slot.

#define RECORD_OFFSET (offsetof(struct SaveSector, saveBlock3Chunk) + offsetof(struct SaveBlock3, averonRegionRecord))
#define ANCHOR_OFFSET offsetof(struct SaveBlock2, averonRegionAnchor)

static u16 (*sRealProgram)(u16, u8 *);
static u16 (*sRealErase)(u16);
static u16 (*sRealProgramByte)(u16, u32, u8);
static u32 sFlashWrites;
static u32 sProgramCalls;
static u32 sPowerLossAfter;

static u16 CountingProgram(u16 sectorNum, u8 *src)
{
    sFlashWrites++;
    return sRealProgram(sectorNum, src);
}

static u16 CountingErase(u16 sectorNum)
{
    sFlashWrites++;
    return sRealErase(sectorNum);
}

static u16 CountingProgramByte(u16 sectorNum, u32 offset, u8 data)
{
    sFlashWrites++;
    return sRealProgramByte(sectorNum, offset, data);
}

static void StartCountingWrites(void)
{
    sRealProgram = ProgramFlashSector;
    sRealErase = EraseFlashSector;
    sRealProgramByte = ProgramFlashByte;
    sFlashWrites = 0;
    ProgramFlashSector = CountingProgram;
    EraseFlashSector = CountingErase;
    ProgramFlashByte = CountingProgramByte;
}

static void StopCountingWrites(void)
{
    ProgramFlashSector = sRealProgram;
    EraseFlashSector = sRealErase;
    ProgramFlashByte = sRealProgramByte;
}

// Power is lost during sector program number sPowerLossAfter: that sector is
// left erased and nothing after it reaches flash.
static u16 PowerLossProgram(u16 sectorNum, u8 *src)
{
    u32 call = sProgramCalls++;
    if (call < sPowerLossAfter)
        return sRealProgram(sectorNum, src);
    if (call == sPowerLossAfter)
        sRealErase(sectorNum);
    return 0;
}

static u16 Checksum(const u8 *data, u16 size)
{
    u32 sum = 0;
    for (u32 i = 0; i < size / 4; i++)
        sum += ((const u32 *)data)[i];
    return (sum >> 16) + sum;
}

static s32 FindPhysical(u32 slot, u32 id)
{
    for (u32 i = 0; i < NUM_SECTORS_PER_SLOT; i++)
    {
        u16 sectorId;
        ReadFlash(slot * NUM_SECTORS_PER_SLOT + i, offsetof(struct SaveSector, id), (u8 *)&sectorId, sizeof(sectorId));
        if (sectorId == id)
            return slot * NUM_SECTORS_PER_SLOT + i;
    }
    return -1;
}

static u32 NewestSlot(void)
{
    return gSaveCounter % NUM_SAVE_SLOTS;
}

static void ReadSector(u32 physical, struct SaveSector *sector)
{
    ReadFlash(physical, 0, (u8 *)sector, sizeof(*sector));
}

static void WriteSector(u32 physical, struct SaveSector *sector)
{
    EraseFlashSector(physical);
    ProgramFlashSector(physical, (u8 *)sector);
}

static void ResealSaveBlock2(struct SaveSector *sector)
{
    sector->checksum = Checksum(sector->data, sizeof(struct SaveBlock2));
}

static void ResealRecord(u8 *record)
{
    u32 crc = AveronRegionSave_RecordCrc(record);
    record[12] = crc;
    record[13] = crc >> 8;
    record[14] = crc >> 16;
    record[15] = crc >> 24;
}

static bool32 StartFlash(void)
{
    CheckForFlashMemory();
    if (!gFlashMemoryPresent)
        return FALSE;
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    gSaveBlock2Ptr->playerTrainerId[0] = 0x12;
    gSaveBlock2Ptr->playerTrainerId[1] = 0x34;
    gSaveBlock2Ptr->playerTrainerId[2] = 0x56;
    gSaveBlock2Ptr->playerTrainerId[3] = 0x78;
    AveronRegionSave_InitNewGame();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    CalculatePlayerPartyCount();
    return TRUE;
}

// A distinct, valid region and game state per seed.
static void ApplyState(u32 seed)
{
    struct WarpData warp = {MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 10 + seed, 12};
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; badge++)
    {
        AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, (0x5A ^ seed) & (1 << (badge - 1)));
        AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, (0x81 + seed) & (1 << (badge - 1)));
    }
    AveronRegion_SetActive(seed & 1 ? AVERON_SAVE_REGION_SINNOH : AVERON_SAVE_REGION_AVERON);
    AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_AVERON, &warp);
    if (seed & 2)
    {
        warp = (struct WarpData){MAP_GROUP(MAP_ALDERFIELDCLINIC), MAP_NUM(MAP_ALDERFIELDCLINIC), 0, -1, -1};
        AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp);
    }
    else
    {
        AveronRegion_ClearReturnWarp(AVERON_SAVE_REGION_SINNOH);
    }
    AveronRegion_SetHealLocation(AVERON_SAVE_REGION_AVERON, HEAL_LOCATION_ALDERFIELD);
    AveronRegion_SetHealLocation(AVERON_SAVE_REGION_SINNOH, seed % NUM_HEAL_LOCATIONS);
    SetMoney(&gSaveBlock1Ptr->money, 1000 + seed);
    ClearBag();
    AddBagItem(ITEM_POTION, 1 + seed);
}

static void ScrambleRam(void)
{
    AveronRegionSave_InitNewGame();
    for (u32 badge = FLAG_BADGE01_GET; badge <= FLAG_BADGE08_GET; badge++)
        FlagClear(badge);
    SetMoney(&gSaveBlock1Ptr->money, 0);
    ClearBag();
}

static bool32 MatchesState(u32 seed)
{
    struct WarpData warp;
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; badge++)
    {
        if (AveronRegion_HasBadge(AVERON_SAVE_REGION_AVERON, badge) != (((0x5A ^ seed) >> (badge - 1)) & 1))
            return FALSE;
        if (AveronRegion_HasBadge(AVERON_SAVE_REGION_SINNOH, badge) != (((0x81 + seed) >> (badge - 1)) & 1))
            return FALSE;
    }
    if (AveronRegion_GetActive() != (seed & 1 ? AVERON_SAVE_REGION_SINNOH : AVERON_SAVE_REGION_AVERON))
        return FALSE;
    if (!AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_AVERON, &warp) || warp.x != 10 + seed || warp.y != 12)
        return FALSE;
    if (AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp) != ((seed & 2) != 0))
        return FALSE;
    if (AveronRegion_GetHealLocation(AVERON_SAVE_REGION_AVERON) != HEAL_LOCATION_ALDERFIELD
     || AveronRegion_GetHealLocation(AVERON_SAVE_REGION_SINNOH) != seed % NUM_HEAL_LOCATIONS)
        return FALSE;
    return GetMoney(&gSaveBlock1Ptr->money) == 1000 + seed
        && CountTotalItemQuantityInBag(ITEM_POTION) == 1 + seed;
}

static bool32 MatchesLegacyDefaults(void)
{
    struct WarpData warp;
    return AveronRegion_GetActive() == AVERON_SAVE_REGION_AVERON
        && AveronRegion_CountBadges(AVERON_SAVE_REGION_SINNOH) == 0
        && !AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_AVERON, &warp)
        && !AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp)
        && AveronRegion_GetHealLocation(AVERON_SAVE_REGION_SINNOH) == HEAL_LOCATION_NONE;
}

// Two complete saves: the older holds state `older`, the newest `newer`.
static u32 SaveTwo(u32 older, u32 newer)
{
    ApplyState(older);
    TrySavingData(SAVE_NORMAL);
    ApplyState(newer);
    TrySavingData(SAVE_NORMAL);
    return gSaveCounter;
}

// Rewrite one slot's sector 0 as the pre-Averon writer left it: no anchor,
// and nothing in the SaveBlock3 chunk past the original 4-byte prefix
// unless `tail` asks for leftover bytes there.
static void MakeSlotLegacy(u32 slot, bool32 tail)
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    s32 physical = FindPhysical(slot, SECTOR_ID_SAVEBLOCK2);
    ReadSector(physical, sector);
    memset(&sector->data[ANCHOR_OFFSET], 0, AVERON_REGION_ANCHOR_SIZE);
    for (u32 i = 4; i < SAVE_BLOCK_3_CHUNK_SIZE; i++)
        sector->saveBlock3Chunk[i] = tail ? (u8)(i * 37 + 5) : 0;
    ResealSaveBlock2(sector);
    WriteSector(physical, sector);
    Free(sector);
}

TEST("Averon region save layout: anchor replaces filler_90 and the record fits sector 0")
{
    EXPECT_EQ(offsetof(struct SaveBlock2, averonRegionAnchor), 0x90);
    EXPECT_EQ(sizeof(gSaveBlock2Ptr->averonRegionAnchor), 8);
    EXPECT_EQ(offsetof(struct SaveBlock3, averonRegionRecord), 4); // after the old 4-byte block
    EXPECT_EQ(sizeof(struct SaveBlock3), 68);
    EXPECT_LE(RECORD_OFFSET + AVERON_REGION_RECORD_SIZE, offsetof(struct SaveSector, id));
    // CRC-32/ISO-HDLC check value.
    EXPECT_EQ(AveronRegionSave_Crc32((const u8 *)"123456789", 9), 0xCBF43926);
}

TEST("Averon region save round-trips both regions through flash without writing on load")
{
    u8 anchor[AVERON_REGION_ANCHOR_SIZE];
    u8 status;
    EXPECT(StartFlash());
    ApplyState(7);
    EXPECT(MatchesState(7));
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ReadFlash(FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2), ANCHOR_OFFSET, anchor, sizeof(anchor));
    EXPECT_EQ(memcmp(anchor, "AVRS", 4), 0);
    EXPECT_EQ(anchor[4] | (anchor[5] << 8), AVERON_REGION_SAVE_FORMAT);
    ScrambleRam();
    EXPECT(!MatchesState(7));
    StartCountingWrites();
    status = LoadGameSave(SAVE_NORMAL);
    StopCountingWrites();
    EXPECT_EQ(status, SAVE_STATUS_OK);
    EXPECT_EQ(sFlashWrites, 0);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
    EXPECT(MatchesState(7));
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_PIPLUP);
}

TEST("Averon region save keeps SaveBlock1, SaveBlock2 and the PC byte-exact through flash")
{
    struct SaveBlock1 *sb1 = Alloc(sizeof(struct SaveBlock1));
    struct SaveBlock2 *sb2 = Alloc(sizeof(struct SaveBlock2));
    u32 storageCrc;
    EXPECT(StartFlash());
    ApplyState(3);
    gPokemonStoragePtr->currentBox = 5;
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    memcpy(sb1, gSaveBlock1Ptr, sizeof(*sb1));
    memcpy(sb2, gSaveBlock2Ptr, sizeof(*sb2));
    storageCrc = AveronRegionSave_Crc32((const u8 *)gPokemonStoragePtr, sizeof(struct PokemonStorage));
    ScrambleRam();
    gPokemonStoragePtr->currentBox = 0;
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(memcmp(sb1, gSaveBlock1Ptr, sizeof(*sb1)), 0);
    EXPECT_EQ(memcmp(sb2, gSaveBlock2Ptr, sizeof(*sb2)), 0);
    EXPECT_EQ(AveronRegionSave_Crc32((const u8 *)gPokemonStoragePtr, sizeof(struct PokemonStorage)), storageCrc);
    Free(sb1);
    Free(sb2);
}

TEST("Averon region save loads a legacy save as Averon-only, in RAM, then upgrades on the next save")
{
    u32 tail = FALSE;
    u8 status;
    u8 anchor[AVERON_REGION_ANCHOR_SIZE];
    struct SaveBlock1 *sb1 = Alloc(sizeof(struct SaveBlock1));
    PARAMETRIZE { tail = FALSE; }
    PARAMETRIZE { tail = TRUE; } // leftover bytes past the old SaveBlock3
    EXPECT(StartFlash());
    ApplyState(5); // Averon badges 0x5F; Sinnoh state will be dropped
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    MakeSlotLegacy(NewestSlot(), tail);
    memcpy(sb1, gSaveBlock1Ptr, sizeof(*sb1));
    ScrambleRam();
    StartCountingWrites();
    status = LoadGameSave(SAVE_NORMAL);
    StopCountingWrites();
    EXPECT_EQ(status, SAVE_STATUS_OK);
    EXPECT_EQ(sFlashWrites, 0);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_LEGACY_MIGRATED);
    EXPECT_EQ(memcmp(sb1, gSaveBlock1Ptr, sizeof(*sb1)), 0); // party, Bag, money, flags
    EXPECT(MatchesLegacyDefaults());
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; badge++)
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_AVERON, badge), ((0x5A ^ 5) >> (badge - 1)) & 1);
    EXPECT_EQ(gSaveBlock2Ptr->averonRegionAnchor[0], 0); // not upgraded until saved
    // The next ordinary save writes the anchor and record.
    AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, 2, TRUE);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ReadFlash(FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2), ANCHOR_OFFSET, anchor, sizeof(anchor));
    EXPECT_EQ(memcmp(anchor, "AVRS", 4), 0);
    ScrambleRam();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
    EXPECT_EQ(AveronRegion_CountBadges(AVERON_SAVE_REGION_SINNOH), 1);
    EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_SINNOH, 2), TRUE);
    Free(sb1);
}

TEST("Averon region save rejects every single-bit flip in the record and loads the older slot")
{
    u32 byte = 0;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 olderCounter, physical;
    for (u32 i = 0; i < AVERON_REGION_RECORD_SIZE; i += 4)
        PARAMETRIZE { byte = i; }
    EXPECT(StartFlash());
    SaveTwo(1, 2);
    olderCounter = gSaveCounter - 1;
    physical = FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2);
    for (u32 b = byte; b < byte + 4; b++)
    {
        for (u32 bit = 0; bit < 8; bit++)
        {
            ReadSector(physical, sector);
            sector->saveBlock3Chunk[offsetof(struct SaveBlock3, averonRegionRecord) + b] ^= 1 << bit;
            WriteSector(physical, sector);
            ScrambleRam();
            Save_ResetSaveCounters();
            EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_ERROR);
            EXPECT_EQ(gSaveCounter, olderCounter);
            EXPECT(MatchesState(1));
            EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_ROLLED_BACK);
            sector->saveBlock3Chunk[offsetof(struct SaveBlock3, averonRegionRecord) + b] ^= 1 << bit;
            WriteSector(physical, sector);
        }
    }
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT(MatchesState(2));
    Free(sector);
}

TEST("Averon region save rejects every anchor bit flip even under a recomputed sector checksum")
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 olderCounter, physical;
    EXPECT(StartFlash());
    SaveTwo(1, 2);
    olderCounter = gSaveCounter - 1;
    physical = FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2);
    for (u32 b = 0; b < AVERON_REGION_ANCHOR_SIZE; b++)
    {
        for (u32 bit = 0; bit < 8; bit++)
        {
            ReadSector(physical, sector);
            sector->data[ANCHOR_OFFSET + b] ^= 1 << bit;
            ResealSaveBlock2(sector);
            WriteSector(physical, sector);
            ScrambleRam();
            Save_ResetSaveCounters();
            EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_ERROR);
            EXPECT_EQ(gSaveCounter, olderCounter);
            EXPECT(MatchesState(1));
            sector->data[ANCHOR_OFFSET + b] ^= 1 << bit;
            ResealSaveBlock2(sector);
            WriteSector(physical, sector);
        }
    }
    Free(sector);
}

enum
{
    BAD_COUNTER_PLUS,
    BAD_COUNTER_MINUS,
    BAD_TRAINER_ID,
    BAD_AVERON_MIRROR,
    BAD_REGION_NONE,
    BAD_REGION_THREE,
    BAD_REGION_MAX,
    BAD_RESERVED_19,
    BAD_RESERVED_TAIL,
    BAD_HEAL_RANGE,
    BAD_HEAL_MAX,
    BAD_WARP_GROUP,
    BAD_WARP_MAP,
    BAD_WARP_INDEX,
    BAD_WARP_COORDS,
    BAD_WARP_SHAPE,
    BAD_LENGTH,
    BAD_TAG,
    BAD_RECORD_ZEROED,
    BAD_RECORD_ERASED,
    BAD_COUNT,
};

TEST("Averon region save rejects CRC-valid semantic corruption and loads the older slot")
{
    u32 kind = 0;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u8 *record;
    u32 olderCounter, physical;
    for (u32 i = 0; i < BAD_COUNT; i++)
        PARAMETRIZE { kind = i; }
    EXPECT(StartFlash());
    SaveTwo(1, 2); // newest has an Averon return warp at Saltmere (11, 12)
    olderCounter = gSaveCounter - 1;
    physical = FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2);
    ReadSector(physical, sector);
    record = &sector->saveBlock3Chunk[offsetof(struct SaveBlock3, averonRegionRecord)];
    switch (kind)
    {
    case BAD_COUNTER_PLUS:   record[8]++; break;
    case BAD_COUNTER_MINUS:  record[8]--; break;
    case BAD_TRAINER_ID:     record[40] ^= 0x01; break;
    case BAD_AVERON_MIRROR:  record[17] ^= 0x80; break;
    case BAD_REGION_NONE:    record[16] = AVERON_SAVE_REGION_NONE; break;
    case BAD_REGION_THREE:   record[16] = 3; break;
    case BAD_REGION_MAX:     record[16] = 0xFF; break;
    case BAD_RESERVED_19:    record[19] = 1; break;
    case BAD_RESERVED_TAIL:  record[63] = 1; break;
    case BAD_HEAL_RANGE:     record[36] = NUM_HEAL_LOCATIONS; record[37] = 0; break;
    case BAD_HEAL_MAX:       record[38] = 0xFF; record[39] = 0xFF; break;
    case BAD_WARP_GROUP:     record[20] = MAP_GROUPS_COUNT; break;
    case BAD_WARP_MAP:       record[21] = 0x7F; break;
    case BAD_WARP_INDEX:     record[22] = 0x7F; record[23] = 0; record[24] = 0xFF; record[25] = 0xFF; record[26] = 0xFF; record[27] = 0xFF; break;
    case BAD_WARP_COORDS:    record[24] = 0x7F; break; // x = 127, outside Saltmere
    case BAD_WARP_SHAPE:     record[22] = 0xFE; record[23] = 0xFF; break; // warpId -2
    case BAD_LENGTH:         record[6] = 63; break;
    case BAD_TAG:            record[0] = 'a'; break;
    case BAD_RECORD_ZEROED:  memset(record, 0, AVERON_REGION_RECORD_SIZE); break;
    case BAD_RECORD_ERASED:  memset(record, 0xFF, AVERON_REGION_RECORD_SIZE); break;
    }
    if (kind < BAD_RECORD_ZEROED)
        ResealRecord(record);
    WriteSector(physical, sector);
    ScrambleRam();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_ERROR);
    EXPECT_EQ(gSaveCounter, olderCounter);
    EXPECT(MatchesState(1));
    Free(sector);
}

TEST("Averon region save rejects a record copied from the other slot")
{
    struct SaveSector *newest = Alloc(sizeof(*newest));
    struct SaveSector *older = Alloc(sizeof(*older));
    u32 olderCounter, physical, recordStart = offsetof(struct SaveBlock3, averonRegionRecord);
    EXPECT(StartFlash());
    SaveTwo(1, 2);
    olderCounter = gSaveCounter - 1;
    physical = FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2);
    ReadSector(physical, newest);
    ReadSector(FindPhysical(1 - NewestSlot(), SECTOR_ID_SAVEBLOCK2), older);
    // The older record is internally valid (its own CRC) but stale here.
    memcpy(&newest->saveBlock3Chunk[recordStart], &older->saveBlock3Chunk[recordStart], AVERON_REGION_RECORD_SIZE);
    WriteSector(physical, newest);
    ScrambleRam();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_ERROR);
    EXPECT_EQ(gSaveCounter, olderCounter);
    EXPECT(MatchesState(1));
    Free(newest);
    Free(older);
}

TEST("Averon region save rejects a slot whose sectors come from two different saves")
{
    u32 variant = 0, extraSave = 0;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    struct SaveSector *other = Alloc(sizeof(*other));
    u32 olderCounter, physical;
    // Each damage kind, with the newest save in either physical slot.
    for (u32 i = 0; i < 2; i++)
    {
        PARAMETRIZE { variant = 0; extraSave = i; } // one sector's footer counter differs
        PARAMETRIZE { variant = 1; extraSave = i; } // older slot's whole sector 0 spliced in
        PARAMETRIZE { variant = 2; extraSave = i; } // older sector 0 spliced in, footer counter forged
    }
    EXPECT(StartFlash());
    if (extraSave)
        TrySavingData(SAVE_NORMAL);
    SaveTwo(1, 2);
    olderCounter = gSaveCounter - 1;
    if (variant == 0)
    {
        physical = FindPhysical(NewestSlot(), SECTOR_ID_PKMN_STORAGE_START);
        ReadSector(physical, sector);
        sector->counter += 2; // checksum covers data only, so it still passes
        WriteSector(physical, sector);
    }
    else
    {
        physical = FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2);
        ReadSector(physical, sector);
        ReadSector(FindPhysical(1 - NewestSlot(), SECTOR_ID_SAVEBLOCK2), other);
        if (variant == 2)
            other->counter = sector->counter;
        WriteSector(physical, other);
    }
    ScrambleRam();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_ERROR);
    EXPECT_EQ(gSaveCounter, olderCounter);
    EXPECT(MatchesState(1));
    Free(sector);
    Free(other);
}

TEST("Averon region save reports both slots corrupt instead of mixing them")
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    EXPECT(StartFlash());
    SaveTwo(1, 2);
    for (u32 slot = 0; slot < NUM_SAVE_SLOTS; slot++)
    {
        u32 physical = FindPhysical(slot, SECTOR_ID_SAVEBLOCK2);
        ReadSector(physical, sector);
        sector->saveBlock3Chunk[offsetof(struct SaveBlock3, averonRegionRecord) + 18] ^= 0x10;
        WriteSector(physical, sector);
    }
    ScrambleRam();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_CORRUPT);
    EXPECT(MatchesLegacyDefaults()); // nothing half-loaded is presented as region state
    Free(sector);
}

TEST("Averon region save rolls back across save counter wrap")
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 physical;
    EXPECT(StartFlash());
    gSaveCounter = 0xFFFFFFFE;
    SaveTwo(1, 2); // counters 0xFFFFFFFF then 0
    EXPECT_EQ(gSaveCounter, 0);
    ScrambleRam();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(gSaveCounter, 0);
    EXPECT(MatchesState(2));
    physical = FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2);
    ReadSector(physical, sector);
    sector->saveBlock3Chunk[offsetof(struct SaveBlock3, averonRegionRecord) + 30] ^= 0x01;
    WriteSector(physical, sector);
    ScrambleRam();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_ERROR);
    EXPECT_EQ(gSaveCounter, 0xFFFFFFFF);
    EXPECT(MatchesState(1));
    Free(sector);
}

TEST("Averon region save refuses a newer format: loads nothing and never overwrites it")
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 before[2 * NUM_SECTORS_PER_SLOT];
    u32 physical, damaged, issue;
    bool32 blocked;
    u8 status;
    EXPECT(StartFlash());
    SaveTwo(1, 2);
    physical = FindPhysical(NewestSlot(), SECTOR_ID_SAVEBLOCK2);
    ReadSector(physical, sector);
    sector->data[ANCHOR_OFFSET + 4] = AVERON_REGION_SAVE_FORMAT + 1;
    sector->data[ANCHOR_OFFSET + 5] = 0;
    sector->data[ANCHOR_OFFSET + 6] = ~(AVERON_REGION_SAVE_FORMAT + 1);
    sector->data[ANCHOR_OFFSET + 7] = 0xFF;
    ResealSaveBlock2(sector);
    WriteSector(physical, sector);
    for (u32 i = 0; i < 2 * NUM_SECTORS_PER_SLOT; i++)
    {
        ReadSector(i, sector);
        before[i] = AveronRegionSave_Crc32((const u8 *)sector, sizeof(*sector));
    }
    ScrambleRam();
    Save_ResetSaveCounters();
    status = LoadGameSave(SAVE_NORMAL);
    issue = AveronRegionSave_GetLoadIssue();
    blocked = AveronRegionSave_IsWriteBlocked();
    ApplyState(9);
    HandleSavingData(SAVE_NORMAL); // what the player's next save would do
    damaged = gDamagedSaveSectors;
    AveronRegionSave_BeginLoad(); // unblock before any check can end the test
    Save_ResetSaveCounters();
    EXPECT_EQ(status, SAVE_STATUS_CORRUPT); // the older slot is not loaded either
    EXPECT_EQ(issue, AVERON_REGION_LOAD_UNSUPPORTED);
    EXPECT_EQ(blocked, TRUE);
    EXPECT_NE(damaged, 0);
    for (u32 i = 0; i < 2 * NUM_SECTORS_PER_SLOT; i++)
    {
        ReadSector(i, sector);
        EXPECT_EQ(AveronRegionSave_Crc32((const u8 *)sector, sizeof(*sector)), before[i]);
    }
    Free(sector);
}

TEST("Averon region save power loss at any sector write keeps the last whole slot")
{
    u32 rotation = 0;
    for (u32 i = 0; i < NUM_SECTORS_PER_SLOT; i++)
        PARAMETRIZE { rotation = i; }
    EXPECT(StartFlash());
    for (u32 lostAt = 0; lostAt <= NUM_SECTORS_PER_SLOT; lostAt++)
    {
        u32 newerCounter;
        u8 status;
        ClearSaveData();
        Save_ResetSaveCounters();
        // Earlier saves leave both the rotation and the newest slot varied.
        gLastWrittenSector = rotation;
        gSaveCounter = rotation;
        newerCounter = SaveTwo(1, 2);
        ApplyState(3);
        sRealProgram = ProgramFlashSector;
        sRealErase = EraseFlashSector;
        sProgramCalls = 0;
        sPowerLossAfter = lostAt;
        ProgramFlashSector = PowerLossProgram;
        HandleSavingData(SAVE_NORMAL);
        ProgramFlashSector = sRealProgram;
        // Power back on.
        ScrambleRam();
        Save_ResetSaveCounters();
        status = LoadGameSave(SAVE_NORMAL);
        if (lostAt == NUM_SECTORS_PER_SLOT)
        {
            EXPECT_EQ(status, SAVE_STATUS_OK);
            EXPECT_EQ(gSaveCounter, newerCounter + 1);
            EXPECT(MatchesState(3));
        }
        else
        {
            EXPECT_EQ(status, SAVE_STATUS_ERROR);
            EXPECT_EQ(gSaveCounter, newerCounter);
            EXPECT(MatchesState(2));
            // A clean save afterwards is complete and loads.
            if (lostAt == rotation)
            {
                ApplyState(4);
                EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
                ScrambleRam();
                Save_ResetSaveCounters();
                EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
                EXPECT(MatchesState(4));
            }
        }
    }
}

TEST("Averon region adapters keep both badge banks independent and fail closed")
{
    struct WarpData warp;
    AveronRegionSave_InitNewGame();
    for (u32 badge = FLAG_BADGE01_GET; badge <= FLAG_BADGE08_GET; badge++)
        FlagClear(badge);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_AVERON);
    EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, 8, TRUE));
    EXPECT_EQ(FlagGet(FLAG_BADGE08_GET), FALSE); // Sinnoh never touches Averon flags
    EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, 1, TRUE));
    EXPECT_EQ(FlagGet(FLAG_BADGE01_GET), TRUE);
    EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_SINNOH, 1), FALSE);
    EXPECT_EQ(AveronRegion_CountBadges(AVERON_SAVE_REGION_AVERON), 1);
    EXPECT_EQ(AveronRegion_CountBadges(AVERON_SAVE_REGION_SINNOH), 1);
    // Invalid regions and badge numbers, including values a short enum would truncate.
    EXPECT(!AveronRegion_SetBadge(AVERON_SAVE_REGION_NONE, 1, TRUE));
    EXPECT(!AveronRegion_SetBadge(AVERON_SAVE_REGION_COUNT, 1, TRUE));
    EXPECT(!AveronRegion_SetBadge(0x101, 1, TRUE));
    EXPECT(!AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, 0, TRUE));
    EXPECT(!AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, 9, TRUE));
    EXPECT(!AveronRegion_HasBadge(0x102, 8));
    EXPECT_EQ(AveronRegion_CountBadges(0x102), 0);
    EXPECT(!AveronRegion_SetActive(AVERON_SAVE_REGION_NONE));
    EXPECT(!AveronRegion_SetActive(0x101));
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_AVERON);
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
    // Return warps must be real map positions the s8 warp API can take.
    EXPECT(!AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    warp = (struct WarpData){MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18};
    EXPECT(AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    warp = (struct WarpData){MAP_GROUPS_COUNT, 0, WARP_ID_NONE, 1, 1};
    EXPECT(!AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    warp = (struct WarpData){MAP_GROUP(MAP_SALTMERE), 120, WARP_ID_NONE, 1, 1};
    EXPECT(!AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    warp = (struct WarpData){MAP_GROUP(MAP_ALDERFIELDCLINIC), MAP_NUM(MAP_ALDERFIELDCLINIC), 100, -1, -1};
    EXPECT(!AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    warp = (struct WarpData){MAP_GROUP(MAP_ALDERFIELDCLINIC), MAP_NUM(MAP_ALDERFIELDCLINIC), 0, 3, 3};
    EXPECT(!AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    warp = (struct WarpData){MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 127, 127};
    EXPECT(!AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    EXPECT(!AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_NONE, &warp));
    EXPECT(AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    EXPECT_EQ(warp.x, 18); // the failed calls changed nothing
    AveronRegion_ClearReturnWarp(AVERON_SAVE_REGION_SINNOH);
    EXPECT(!AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    EXPECT(!AveronRegion_SetHealLocation(AVERON_SAVE_REGION_SINNOH, NUM_HEAL_LOCATIONS));
    EXPECT(!AveronRegion_SetHealLocation(0x101, HEAL_LOCATION_ALDERFIELD));
    EXPECT(AveronRegion_SetHealLocation(AVERON_SAVE_REGION_SINNOH, HEAL_LOCATION_ALDERFIELD));
    EXPECT_EQ(AveronRegion_GetHealLocation(AVERON_SAVE_REGION_SINNOH), HEAL_LOCATION_ALDERFIELD);
    EXPECT_EQ(AveronRegion_GetHealLocation(AVERON_SAVE_REGION_AVERON), HEAL_LOCATION_NONE);
    AveronRegionSave_InitNewGame();
    FlagClear(FLAG_BADGE01_GET);
}
