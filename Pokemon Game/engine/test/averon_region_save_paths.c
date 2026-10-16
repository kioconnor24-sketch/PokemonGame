#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "item.h"
#include "load_save.h"
#include "money.h"
#include "overworld.h"
#include "pokemon.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "constants/heal_locations.h"
#include "constants/items.h"
#include "constants/map_groups.h"

// The save entry points other than SAVE_NORMAL (Hall of Fame, overwriting a
// different file, and the partial in-place link save) with the two-region
// record. #53 P0-A3 / Manager audit 6209836444. A load must always give one
// whole saved state: region record (SaveBlock2 sector) and money and Bag
// (SaveBlock1) from the same save, never a mix.

static u16 (*sRealProgramByte)(u16, u32, u8);
static u16 (*sRealProgram)(u16, u8 *);
static u16 (*sRealErase)(u16);
static u32 sByteWrites;
static u32 sPowerLossAt;

// Counts byte programs; from call sPowerLossAt on, nothing reaches flash.
static u16 LossyProgramByte(u16 sectorNum, u32 offset, u8 data)
{
    if (sByteWrites++ < sPowerLossAt)
        return sRealProgramByte(sectorNum, offset, data);
    return 0;
}

static u16 LossyProgram(u16 sectorNum, u8 *src)
{
    if (sByteWrites < sPowerLossAt)
        return sRealProgram(sectorNum, src);
    return 0;
}

static u16 LossyErase(u16 sectorNum)
{
    if (sByteWrites < sPowerLossAt)
        return sRealErase(sectorNum);
    return 0;
}

static void StartPowerLossAt(u32 call)
{
    sRealProgramByte = ProgramFlashByte;
    sRealProgram = ProgramFlashSector;
    sRealErase = EraseFlashSector;
    sByteWrites = 0;
    sPowerLossAt = call;
    ProgramFlashByte = LossyProgramByte;
    ProgramFlashSector = LossyProgram;
    EraseFlashSector = LossyErase;
}

static void RestorePower(void)
{
    ProgramFlashByte = sRealProgramByte;
    ProgramFlashSector = sRealProgram;
    EraseFlashSector = sRealErase;
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

// A distinct state per seed, split across both blocks: region record in the
// SaveBlock2 sector, Averon badges, money and Bag in SaveBlock1.
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

static bool32 MatchesRegion(u32 seed)
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
    if (!AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_AVERON, &warp) || warp.x != 10 + seed)
        return FALSE;
    return AveronRegion_GetHealLocation(AVERON_SAVE_REGION_SINNOH) == seed % NUM_HEAL_LOCATIONS;
}

static bool32 MatchesBlock1(u32 seed)
{
    return GetMoney(&gSaveBlock1Ptr->money) == 1000 + seed
        && CountTotalItemQuantityInBag(ITEM_POTION) == 1 + seed;
}

static bool32 MatchesState(u32 seed)
{
    return MatchesRegion(seed) && MatchesBlock1(seed);
}

static void ExpectLoadsState(u32 seed)
{
    ScrambleRam();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT(MatchesState(seed));
}

TEST("Averon region save paths: a Hall of Fame save seals and reloads the region state")
{
    EXPECT(StartFlash());
    ApplyState(4);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ApplyState(9);
    EXPECT_EQ(TrySavingData(SAVE_HALL_OF_FAME), SAVE_STATUS_OK);
    ExpectLoadsState(9);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
}

TEST("Averon region save paths: overwriting a different file seals and reloads the region state")
{
    EXPECT(StartFlash());
    ApplyState(2);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ApplyState(5);
    EXPECT_EQ(TrySavingData(SAVE_OVERWRITE_DIFFERENT_FILE), SAVE_STATUS_OK);
    ExpectLoadsState(5);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
}

TEST("Averon region save paths: a link save rewrites the newest slot in place and reloads it")
{
    EXPECT(StartFlash());
    ApplyState(1);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ApplyState(6);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    u32 counter = gSaveCounter;
    ApplyState(11);
    EXPECT_EQ(TrySavingData(SAVE_LINK), SAVE_STATUS_OK);
    EXPECT_EQ(gSaveCounter, counter); // in place: no new slot
    ExpectLoadsState(11);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
}

// Power is lost at sampled byte writes across the whole link save: points
// through the five rewritten sectors, exactly on each boundary between two
// sectors, and every write of the final signature pass. The load must be one
// whole saved state. The link state 262 has the same badges as state 6 and
// differs only in money, Bag, return warp and healer, so the badge mirror in
// the region record cannot be what catches a mixed slot.
#define LINK_STATE 262
TEST("Averon region save paths: power loss during a link save never mixes two saves")
{
    u32 point = 0;
    for (u32 j = 0; j < 24; j++)
        PARAMETRIZE { point = j; }

    // Measure the link save's byte writes on a scratch run.
    EXPECT(StartFlash());
    ApplyState(1);
    TrySavingData(SAVE_NORMAL);
    ApplyState(6);
    TrySavingData(SAVE_NORMAL);
    ApplyState(LINK_STATE);
    StartPowerLossAt(0xFFFFFFFF);
    HandleSavingData(SAVE_LINK);
    RestorePower();
    u32 total = sByteWrites;
    u32 linkSectors = SECTOR_ID_SAVEBLOCK1_END - SECTOR_ID_SAVEBLOCK2 + 1;
    u32 perSector = (total - linkSectors) / linkSectors;
    EXPECT_EQ(total, linkSectors * perSector + linkSectors);

    // 0..13 spread through the data, 14..17 on sector boundaries,
    // 18..23 the last six writes (the signature pass).
    u32 lossAt;
    if (point < 14)
        lossAt = (total * point) / 14;
    else if (point < 18)
        lossAt = perSector * (point - 13);
    else
        lossAt = total - (24 - point);

    EXPECT(StartFlash());
    ApplyState(1);
    TrySavingData(SAVE_NORMAL);
    ApplyState(6);
    TrySavingData(SAVE_NORMAL);
    ApplyState(LINK_STATE);
    StartPowerLossAt(lossAt);
    HandleSavingData(SAVE_LINK);
    RestorePower();

    // SAVE_STATUS_ERROR is the engine's "newest slot rejected, older whole
    // slot loaded" result; anything else (empty, corrupt) would lose the save.
    ScrambleRam();
    u8 status = LoadGameSave(SAVE_NORMAL);
    EXPECT(status == SAVE_STATUS_OK || status == SAVE_STATUS_ERROR);
    if (status == SAVE_STATUS_ERROR)
        EXPECT(MatchesState(1));
    bool32 whole = MatchesState(1) || MatchesState(6) || MatchesState(LINK_STATE);
    if (!whole)
        DebugPrintf("loss at %d of %d: region 6/%d = %d/%d, block1 6/%d = %d/%d", lossAt, total, LINK_STATE,
                    MatchesRegion(6), MatchesRegion(LINK_STATE), LINK_STATE, MatchesBlock1(6), MatchesBlock1(LINK_STATE));
    EXPECT(whole);
}
