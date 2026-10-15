#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "battle.h"
#include "event_data.h"
#include "item.h"
#include "load_save.h"
#include "pokemon.h"
#include "save.h"

TEST("Averon opening and Gym progression survive two native flash save and load cycles")
{
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    ClearBag();
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][0], SPECIES_SNIVY, 15, 0);
    CalculatePlayerPartyCount();
    u16 heldItem = ITEM_EXP_SHARE;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HELD_ITEM, &heldItem);
    VarSet(VAR_AVERON_FIRST_HOUSE, 1);
    VarSet(VAR_AVERON_GREENHOUSE, 2);
    VarSet(VAR_AVERON_HARVEST_FAIR, 2);
    FlagSet(FLAG_AVERON_STARTER);
    FlagSet(FLAG_AVERON_WEST_SLUICE);
    FlagClear(FLAG_AVERON_EAST_SLUICE);
    FlagClear(FLAG_BADGE01_GET);
    FlagClear(FLAG_AVERON_GYM1_TM);
    FlagClear(FLAG_AVERON_COAST_ITEM);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);

    ZeroPlayerPartyMons();
    VarSet(VAR_AVERON_FIRST_HOUSE, 3);
    VarSet(VAR_AVERON_GREENHOUSE, 0);
    VarSet(VAR_AVERON_HARVEST_FAIR, 0);
    FlagClear(FLAG_AVERON_STARTER);
    FlagClear(FLAG_AVERON_WEST_SLUICE);
    FlagSet(FLAG_AVERON_EAST_SLUICE);
    FlagSet(FLAG_BADGE01_GET);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_SNIVY);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_LEVEL), 15);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HELD_ITEM), ITEM_EXP_SHARE);
    EXPECT_EQ(VarGet(VAR_AVERON_FIRST_HOUSE), 1);
    EXPECT_EQ(VarGet(VAR_AVERON_GREENHOUSE), 2);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 2);
    EXPECT_EQ(FlagGet(FLAG_AVERON_STARTER), TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_WEST_SLUICE), TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_EAST_SLUICE), FALSE);
    EXPECT_EQ(FlagGet(FLAG_BADGE01_GET), FALSE);

    FlagSet(FLAG_AVERON_EAST_SLUICE);
    FlagSet(FLAG_BADGE01_GET);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 1);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), TRUE);
    FlagSet(FLAG_AVERON_COAST_ITEM);
    VarSet(VAR_AVERON_HARVEST_FAIR, 3);
    // Ordinary bag pockets point directly into SaveBlock1. The similarly
    // named SavePlayerBag restores a link-room backup and is not used here.
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ClearBag();
    FlagClear(FLAG_AVERON_EAST_SLUICE);
    FlagClear(FLAG_BADGE01_GET);
    FlagClear(FLAG_AVERON_GYM1_TM);
    FlagClear(FLAG_AVERON_COAST_ITEM);
    VarSet(VAR_AVERON_HARVEST_FAIR, 0);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(FlagGet(FLAG_AVERON_EAST_SLUICE), TRUE);
    EXPECT_EQ(FlagGet(FLAG_BADGE01_GET), TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_COAST_ITEM), TRUE);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 3);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 1);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 1);
}

TEST("Averon unclaimed rewards survive saving with a full pocket and remain retryable")
{
    bool32 gym = TRUE;
    PARAMETRIZE { gym=TRUE; }
    PARAMETRIZE { gym=FALSE; }
    enum Item reward = gym ? ITEM_TM_WORK_UP : ITEM_SUPER_POTION;
    enum Item removable = ITEM_NONE;
    enum Pocket pocket = GetItemPocket(reward);
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    ClearBag();
    for (enum Item item=ITEM_NONE+1; item<ITEMS_COUNT; ++item)
        if (item != reward && GetItemPocket(item)==pocket && AddBagItem(item, 1))
            removable=item;
    EXPECT(removable != ITEM_NONE);
    EXPECT_EQ(CheckBagHasSpace(reward, 1), FALSE);
    FlagSet(FLAG_BADGE01_GET);
    FlagClear(FLAG_AVERON_GYM1_TM);
    VarSet(VAR_AVERON_HARVEST_FAIR, 2);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ClearBag();
    FlagSet(FLAG_AVERON_GYM1_TM);
    VarSet(VAR_AVERON_HARVEST_FAIR, 3);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(CheckBagHasSpace(reward, 1), FALSE);
    EXPECT_EQ(FlagGet(FLAG_BADGE01_GET), TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), FALSE);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 2);
    if (gym)
        RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    else
        RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimFairReward;);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(reward), 0);
    EXPECT(RemoveBagItem(removable, 1));
    if (gym)
        RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    else
        RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimFairReward;);
    EXPECT_EQ(VarGet(VAR_RESULT), TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(reward), 1);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ClearBag();
    FlagClear(FLAG_AVERON_GYM1_TM);
    VarSet(VAR_AVERON_HARVEST_FAIR, 0);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    if (gym)
        RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    else
        RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimFairReward;);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(reward), 1);
}
