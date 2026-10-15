#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "event_data.h"
#include "item.h"
#include "save.h"
#include "load_save.h"
#include "gba/flash_internal.h"

static void ResetOptionalEvents(void)
{
    for (u32 flag = FLAG_AVERON_NOTES_STARTED; flag <= FLAG_AVERON_SKETCH_REWARDED; ++flag)
        FlagClear(flag);
    ClearBag();
}

static void ClaimOptionalReward(bool32 sketch)
{
    if (sketch)
        RUN_OVERWORLD_SCRIPT(call Averon_BerrySketch_TryReward;);
    else
        RUN_OVERWORLD_SCRIPT(call Averon_FieldNotes_TryReward;);
}

TEST("Averon optional event rewards require both prerequisites and cannot repeat")
{
    bool32 sketch = FALSE;
    PARAMETRIZE { sketch = FALSE; }
    PARAMETRIZE { sketch = TRUE; }
    u32 first = sketch ? FLAG_AVERON_SKETCH_STARTED : FLAG_AVERON_NOTES_STARTED;
    u32 objective = sketch ? FLAG_AVERON_SKETCH_FOUND : FLAG_AVERON_NOTES_RECORDED;
    u32 rewarded = sketch ? FLAG_AVERON_SKETCH_REWARDED : FLAG_AVERON_NOTES_REWARDED;
    enum Item item = sketch ? ITEM_ORAN_BERRY : ITEM_GREAT_BALL;
    u32 quantity = sketch ? 3 : 2;
    ResetOptionalEvents();
    ClaimOptionalReward(sketch);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    FlagSet(objective); // Interrupted or out-of-order state must not grant a gift.
    ClaimOptionalReward(sketch);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(item), 0);
    FlagClear(objective);
    FlagSet(first);
    ClaimOptionalReward(sketch);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    FlagSet(objective);
    ClaimOptionalReward(sketch);
    EXPECT_EQ(VarGet(VAR_RESULT), TRUE);
    EXPECT_EQ(FlagGet(rewarded), TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(item), quantity);
    ClaimOptionalReward(sketch);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(item), quantity);
}

TEST("Averon optional event full pocket keeps the real script reward retryable")
{
    bool32 sketch = FALSE;
    PARAMETRIZE { sketch = FALSE; }
    PARAMETRIZE { sketch = TRUE; }
    enum Item reward = sketch ? ITEM_ORAN_BERRY : ITEM_GREAT_BALL;
    enum Item removable = ITEM_NONE;
    u32 first = sketch ? FLAG_AVERON_SKETCH_STARTED : FLAG_AVERON_NOTES_STARTED;
    u32 objective = sketch ? FLAG_AVERON_SKETCH_FOUND : FLAG_AVERON_NOTES_RECORDED;
    u32 rewarded = sketch ? FLAG_AVERON_SKETCH_REWARDED : FLAG_AVERON_NOTES_REWARDED;
    ResetOptionalEvents();
    for (enum Item item = ITEM_NONE + 1; item < ITEMS_COUNT; ++item)
        if (item != reward && GetItemPocket(item) == GetItemPocket(reward) && AddBagItem(item, 1))
            removable = item;
    EXPECT(removable != ITEM_NONE);
    EXPECT_EQ(CheckBagHasSpace(reward, sketch ? 3 : 2), FALSE);
    FlagSet(first);
    FlagSet(objective);
    ClaimOptionalReward(sketch);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(FlagGet(rewarded), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(reward), 0);
    EXPECT(RemoveBagItem(removable, 1));
    ClaimOptionalReward(sketch);
    EXPECT_EQ(VarGet(VAR_RESULT), TRUE);
    EXPECT_EQ(FlagGet(rewarded), TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(reward), sketch ? 3 : 2);
}

TEST("Averon optional event stages survive native flash and transient field reset")
{
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    ResetOptionalEvents();
    FlagSet(FLAG_BADGE01_GET);
    FlagSet(FLAG_AVERON_LICENSE_CUT);
    for (u32 stage = 0; stage < 4; ++stage)
    {
        if (stage == 1)
        {
            FlagSet(FLAG_AVERON_NOTES_STARTED);
            FlagSet(FLAG_AVERON_SKETCH_STARTED);
        }
        if (stage == 2)
        {
            FlagSet(FLAG_AVERON_NOTES_RECORDED);
            FlagSet(FLAG_AVERON_SKETCH_FOUND);
        }
        if (stage == 3)
        {
            ClaimOptionalReward(FALSE);
            ClaimOptionalReward(TRUE);
        }
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        ResetOptionalEvents();
        FlagClear(FLAG_BADGE01_GET);
        FlagClear(FLAG_AVERON_LICENSE_CUT);
        EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
        // This is the native transient cleanup used by field reentry;
        // the complete rendered whiteout/return sequence is separate evidence.
        ClearTempFieldEventData();
        EXPECT_EQ(FlagGet(FLAG_AVERON_NOTES_STARTED), stage >= 1);
        EXPECT_EQ(FlagGet(FLAG_AVERON_SKETCH_STARTED), stage >= 1);
        EXPECT_EQ(FlagGet(FLAG_AVERON_NOTES_RECORDED), stage >= 2);
        EXPECT_EQ(FlagGet(FLAG_AVERON_SKETCH_FOUND), stage >= 2);
        EXPECT_EQ(FlagGet(FLAG_AVERON_NOTES_REWARDED), stage >= 3);
        EXPECT_EQ(FlagGet(FLAG_AVERON_SKETCH_REWARDED), stage >= 3);
        EXPECT_EQ(FlagGet(FLAG_BADGE01_GET), TRUE);
        EXPECT_EQ(FlagGet(FLAG_AVERON_LICENSE_CUT), TRUE);
        EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_GREAT_BALL), stage == 3 ? 2 : 0);
        EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_ORAN_BERRY), stage == 3 ? 3 : 0);
    }
}

