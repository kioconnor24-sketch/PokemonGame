#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "caps.h"
#include "event_data.h"
#include "item.h"

TEST("Averon Gym TM requires a badge and is granted only once")
{
    ClearBag();
    FlagClear(FLAG_BADGE01_GET);
    FlagClear(FLAG_AVERON_GYM1_TM);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT),FALSE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM),FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP),0);
    FlagSet(FLAG_BADGE01_GET);
    EXPECT_EQ(GetCurrentLevelCap(),23);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT),TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM),TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP),1);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT),FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP),1);
}

TEST("Averon full TM pocket preserves the badge and allows a reward retry")
{
    enum Item removable=ITEM_NONE;
    ClearBag();
    for (enum Item item=ITEM_NONE+1;item<ITEMS_COUNT;++item)
        if (item!=ITEM_TM_WORK_UP && GetItemPocket(item)==POCKET_TM_HM && AddBagItem(item,1))
            removable=item;
    EXPECT(removable!=ITEM_NONE);
    EXPECT_EQ(CheckBagHasSpace(ITEM_TM_WORK_UP,1),FALSE);
    FlagSet(FLAG_BADGE01_GET);
    FlagClear(FLAG_AVERON_GYM1_TM);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT),FALSE);
    EXPECT_EQ(FlagGet(FLAG_BADGE01_GET),TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM),FALSE);
    EXPECT_EQ(GetCurrentLevelCap(),23);
    EXPECT(RemoveBagItem(removable,1));
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT),TRUE);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM),TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP),1);
}
