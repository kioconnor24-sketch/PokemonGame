#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "event_data.h"
#include "item.h"

TEST("Averon harvest fair reward requires delivery and cannot be duplicated")
{
    ClearBag();
    VarSet(VAR_AVERON_HARVEST_FAIR, 0);
    RUN_OVERWORLD_SCRIPT(call Alderfield_CollectFairCrate;);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 0);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimFairReward;);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_SUPER_POTION), 0);
    RUN_OVERWORLD_SCRIPT(call Alderfield_AcceptFair;);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 1);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimFairReward;);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_SUPER_POTION), 0);
    RUN_OVERWORLD_SCRIPT(call Alderfield_CollectFairCrate;);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 2);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimFairReward;);
    EXPECT_EQ(VarGet(VAR_RESULT), TRUE);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 3);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_SUPER_POTION), 1);
    RUN_OVERWORLD_SCRIPT(call Alderfield_AcceptFair; call Alderfield_CollectFairCrate; call Alderfield_ClaimFairReward;);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 3);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_SUPER_POTION), 1);
}

TEST("Averon harvest fair reward survives a full pocket and can be reclaimed")
{
    enum Item removable = ITEM_NONE;
    enum Pocket pocket = GetItemPocket(ITEM_SUPER_POTION);
    ClearBag();
    for (enum Item item=ITEM_NONE+1; item<ITEMS_COUNT; ++item)
        if (item != ITEM_SUPER_POTION && GetItemPocket(item)==pocket && AddBagItem(item,1))
            removable=item;
    EXPECT(removable != ITEM_NONE);
    EXPECT_EQ(CheckBagHasSpace(ITEM_SUPER_POTION,1), FALSE);
    VarSet(VAR_AVERON_HARVEST_FAIR, 2);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimFairReward;);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 2);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_SUPER_POTION), 0);
    EXPECT(RemoveBagItem(removable,1));
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimFairReward;);
    EXPECT_EQ(VarGet(VAR_RESULT), TRUE);
    EXPECT_EQ(VarGet(VAR_AVERON_HARVEST_FAIR), 3);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_SUPER_POTION), 1);
}
