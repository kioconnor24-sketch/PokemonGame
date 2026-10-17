#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "item.h"
#include "load_save.h"
#include "pokemon.h"
#include "save.h"

// Native fixtures for the existing Gym reward script, not evidence of a
// rendered Gym victory. No new quest, map, saved ID or Sinnoh profile is used.
// The Bag/reward flag and regional record must survive the same save. A
// refused reward must remain retryable after loading; an accepted one must
// remain claimed even when its only copy has subsequently left the Bag.
#define AVERON_BADGES 0x25
#define SINNOH_BADGES 0x9A

static void SetBadgeBanks(u32 averon, u32 sinnoh)
{
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, averon & (1 << (badge - 1))));
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, sinnoh & (1 << (badge - 1))));
    }
}

static void ExpectBadgeBanks(void)
{
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_AVERON);
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_AVERON, badge), (AVERON_BADGES >> (badge - 1)) & 1);
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_SINNOH, badge), (SINNOH_BADGES >> (badge - 1)) & 1);
    }
}

static u32 TmPocketCrc(void)
{
    const struct BagPocket *pocket = &gBagPockets[POCKET_TM_HM];
    return AveronRegionSave_Crc32((const u8 *)pocket->itemSlots,
                                 pocket->capacity * sizeof(struct ItemSlot));
}

static void SaveAndReload(u32 saveType, bool32 claimed, u32 rewardCount)
{
    u32 counter = gSaveCounter;
    u32 key = gSaveBlock2Ptr->encryptionKey;
    u32 pocketCrc = TmPocketCrc();
    EXPECT_EQ(TrySavingData(saveType), SAVE_STATUS_OK);
    EXPECT_EQ(gSaveCounter, counter + (saveType == SAVE_NORMAL));
    counter = gSaveCounter;

    // Poison every asserted state instead of accidentally passing on live
    // RAM. A different encryption key also requires the load to restore the
    // matching SaveBlock2 key and the encrypted Bag in SaveBlock1 together.
    AveronRegionSave_InitNewGame();
    SetBadgeBanks(0, 0xFF);
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    if (claimed)
        FlagClear(FLAG_AVERON_GYM1_TM);
    else
        FlagSet(FLAG_AVERON_GYM1_TM);
    gSaveBlock2Ptr->encryptionKey ^= 0x5A5A5A5A;
    ClearBag();
    EXPECT(AddBagItem(ITEM_TM_WORK_UP, rewardCount + 2));
    EXPECT(AddBagItem(ITEM_POTION, 99));
    memset(gSaveBlock1Ptr->pcItems, 0, sizeof(gSaveBlock1Ptr->pcItems));

    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
    EXPECT_EQ(gSaveCounter, counter);
    EXPECT_EQ(gSaveBlock2Ptr->encryptionKey, key);
    EXPECT_EQ(TmPocketCrc(), pocketCrc);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), claimed);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), rewardCount);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), 7);
    // PC item storage also lives in SaveBlock1 and must not be collateral
    // damage from either full-slot or in-place SaveBlock1/2 writes.
    EXPECT_EQ(CountUsedPCItemSlots(), 1);
    EXPECT(CheckPCHasItem(ITEM_SUPER_POTION, 3));
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[0].quantity, 3);
    ExpectBadgeBanks();
}

static void ExerciseRewardFlash(u32 saveType)
{
    enum Item removable = ITEM_NONE;
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    SetBadgeBanks(AVERON_BADGES, SINNOH_BADGES);
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_AVERON));
    FlagClear(FLAG_AVERON_GYM1_TM);
    SetBagItemsPointers();
    ClearBag();
    EXPECT(AddBagItem(ITEM_POTION, 7));
    memset(gSaveBlock1Ptr->pcItems, 0, sizeof(gSaveBlock1Ptr->pcItems));
    EXPECT(AddPCItem(ITEM_SUPER_POTION, 3));
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculatePlayerPartyCount();

    for (enum Item item = ITEM_NONE + 1; item < ITEMS_COUNT; ++item)
        if (item != ITEM_TM_WORK_UP && GetItemPocket(item) == POCKET_TM_HM && AddBagItem(item, 1))
            removable = item;
    EXPECT_NE(removable, ITEM_NONE);
    EXPECT_EQ(CheckBagHasSpace(ITEM_TM_WORK_UP, 1), FALSE);

    // Establish a full slot before the in-place link-save variant. This also
    // provides a valid older state so loading the wrong slot is detectable.
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 0);
    SaveAndReload(saveType, FALSE, 0);
    EXPECT_EQ(CheckBagHasSpace(ITEM_TM_WORK_UP, 1), FALSE);

    // A later retry after loading succeeds only when capacity really exists.
    EXPECT(RemoveBagItem(removable, 1));
    EXPECT_EQ(CheckBagHasSpace(ITEM_TM_WORK_UP, 1), TRUE);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT), TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 1);
    SaveAndReload(saveType, TRUE, 1);

    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 1);

    // Removing the item must not make the persistent reward available again.
    EXPECT(RemoveBagItem(ITEM_TM_WORK_UP, 1));
    SaveAndReload(saveType, TRUE, 0);
    EXPECT_EQ(CheckBagHasSpace(ITEM_TM_WORK_UP, 1), TRUE);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 0);
    ExpectBadgeBanks();

    ClearBag();
    memset(gSaveBlock1Ptr->pcItems, 0, sizeof(gSaveBlock1Ptr->pcItems));
    FlagClear(FLAG_AVERON_GYM1_TM);
    SetBadgeBanks(0, 0);
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
}

TEST("Averon Gym reward normal flash preserves full-Bag retry and nonduplication with regional badges")
{
    ExerciseRewardFlash(SAVE_NORMAL);
}

TEST("Averon Gym reward link flash preserves full-Bag retry and nonduplication with regional badges")
{
    ExerciseRewardFlash(SAVE_LINK);
}
