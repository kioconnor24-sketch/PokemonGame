#include "global.h"
#include "test/test.h"
#include "item.h"
#include "load_save.h"

static void PrepareInventory(void)
{
    SetBagItemsPointers();
    ClearBag();
    memset(gSaveBlock1Ptr->pcItems, 0, sizeof(gSaveBlock1Ptr->pcItems));
    EXPECT(AddBagItem(ITEM_POTION, 7));
}

static u32 CountPCQuantity(enum Item item)
{
    u32 total = 0;
    for (u32 i = 0; i < PC_ITEMS_COUNT; ++i)
        if (gSaveBlock1Ptr->pcItems[i].itemId == item)
            total += gSaveBlock1Ptr->pcItems[i].quantity;
    return total;
}

TEST("Averon PC items split a large deposit across bounded stacks without changing the Bag")
{
    PrepareInventory();
    EXPECT(AddPCItem(ITEM_POTION, MAX_PC_ITEM_CAPACITY + 1));
    EXPECT_EQ(CountUsedPCItemSlots(), 2);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[0].itemId, ITEM_POTION);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[0].quantity, MAX_PC_ITEM_CAPACITY);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[1].itemId, ITEM_POTION);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[1].quantity, 1);
    EXPECT(CheckPCHasItem(ITEM_POTION, MAX_PC_ITEM_CAPACITY));
    EXPECT(AddPCItem(ITEM_POTION, MAX_PC_ITEM_CAPACITY - 1));
    EXPECT_EQ(CountPCQuantity(ITEM_POTION), 2 * MAX_PC_ITEM_CAPACITY);
    EXPECT_EQ(CountUsedPCItemSlots(), 2);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), 7);
}

TEST("Averon PC items reject a partly fitting deposit atomically and allow retry after space is freed")
{
    struct ItemSlot before[PC_ITEMS_COUNT]; // 200 bytes; no large IWRAM fixture.
    PrepareInventory();
    for (u32 i = 0; i < PC_ITEMS_COUNT; ++i)
    {
        gSaveBlock1Ptr->pcItems[i].itemId = ITEM_POTION;
        gSaveBlock1Ptr->pcItems[i].quantity = MAX_PC_ITEM_CAPACITY;
    }
    --gSaveBlock1Ptr->pcItems[0].quantity;
    memcpy(before, gSaveBlock1Ptr->pcItems, sizeof(before));
    EXPECT_EQ(AddPCItem(ITEM_POTION, 2), FALSE);
    EXPECT_EQ(memcmp(before, gSaveBlock1Ptr->pcItems, sizeof(before)), 0);
    EXPECT_EQ(CountUsedPCItemSlots(), PC_ITEMS_COUNT);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), 7);

    RemovePCItem(1, MAX_PC_ITEM_CAPACITY);
    // This is the same explicit compaction used by player_pc.c after removal.
    CompactPCItems();
    EXPECT_EQ(CountUsedPCItemSlots(), PC_ITEMS_COUNT - 1);
    EXPECT(AddPCItem(ITEM_POTION, 2));
    EXPECT_EQ(CountUsedPCItemSlots(), PC_ITEMS_COUNT);
    EXPECT_EQ(CountPCQuantity(ITEM_POTION), (PC_ITEMS_COUNT - 1) * MAX_PC_ITEM_CAPACITY + 1);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[PC_ITEMS_COUNT - 1].quantity, 1);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), 7);
}

TEST("Averon PC items preserve adjacent entries through partial removal and exhausted-slot compaction")
{
    PrepareInventory();
    EXPECT(AddPCItem(ITEM_POTION, 2));
    EXPECT(AddPCItem(ITEM_SUPER_POTION, 3));
    EXPECT(AddPCItem(ITEM_ANTIDOTE, 4));
    RemovePCItem(1, 1);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[1].itemId, ITEM_SUPER_POTION);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[1].quantity, 2);
    EXPECT_EQ(CountUsedPCItemSlots(), 3);
    RemovePCItem(1, 2);
    CompactPCItems();
    EXPECT_EQ(CountUsedPCItemSlots(), 2);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[0].itemId, ITEM_POTION);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[0].quantity, 2);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[1].itemId, ITEM_ANTIDOTE);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[1].quantity, 4);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[2].itemId, ITEM_NONE);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[2].quantity, 0);
    EXPECT(AddPCItem(ITEM_SUPER_POTION, 1));
    EXPECT_EQ(CountUsedPCItemSlots(), 3);
    EXPECT_EQ(CountPCQuantity(ITEM_SUPER_POTION), 1);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), 7);
}

TEST("Averon PC direct removal compacts an exhausted first middle or last slot in order")
{
    static const enum Item items[] = { ITEM_POTION, ITEM_SUPER_POTION, ITEM_ANTIDOTE };
    u32 removed = 0;
    PARAMETRIZE { removed = 0; }
    PARAMETRIZE { removed = 1; }
    PARAMETRIZE { removed = 2; }

    PrepareInventory();
    for (u32 i = 0; i < ARRAY_COUNT(items); ++i)
        EXPECT(AddPCItem(items[i], i + 2));

    // Direct API call: no caller-side CompactPCItems to hide a stale hole.
    RemovePCItem(removed, removed + 2);
    EXPECT_EQ(CountUsedPCItemSlots(), ARRAY_COUNT(items) - 1);
    for (u32 source = 0, slot = 0; source < ARRAY_COUNT(items); ++source)
    {
        if (source == removed)
            continue;
        EXPECT_EQ(gSaveBlock1Ptr->pcItems[slot].itemId, items[source]);
        EXPECT_EQ(gSaveBlock1Ptr->pcItems[slot].quantity, source + 2);
        ++slot;
    }
    for (u32 slot = ARRAY_COUNT(items) - 1; slot < PC_ITEMS_COUNT; ++slot)
    {
        EXPECT_EQ(gSaveBlock1Ptr->pcItems[slot].itemId, ITEM_NONE);
        EXPECT_EQ(gSaveBlock1Ptr->pcItems[slot].quantity, 0);
    }
    // The existing player's explicit second compaction remains harmless.
    CompactPCItems();
    EXPECT(AddPCItem(items[removed], 1));
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[2].itemId, items[removed]);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[2].quantity, 1);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), 7);
}

TEST("Averon PC items remain plaintext and unchanged when the Bag encryption key rotates")
{
    u32 oldKey = 0x11112222;
    u32 newKey = 0xAABBCCDD;
    PARAMETRIZE { oldKey = 0x11112222; newKey = 0xAABBCCDD; }
    PARAMETRIZE { oldKey = 0; newKey = 0xFFFFFFFF; }
    PARAMETRIZE { oldKey = 0xFFFFFFFF; newKey = 0; }
    gSaveBlock2Ptr->encryptionKey = oldKey;
    PrepareInventory();
    EXPECT(AddPCItem(ITEM_POTION, 5));
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[0].quantity, 5);
    EXPECT_EQ(gBagPockets[POCKET_ITEMS].itemSlots[0].quantity, 7 ^ (u16)oldKey);
    ApplyNewEncryptionKeyToBagItems(newKey);
    gSaveBlock2Ptr->encryptionKey = newKey;
    EXPECT_EQ(gBagPockets[POCKET_ITEMS].itemSlots[0].quantity, 7 ^ (u16)newKey);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), 7);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[0].itemId, ITEM_POTION);
    EXPECT_EQ(gSaveBlock1Ptr->pcItems[0].quantity, 5);
    EXPECT_EQ(CountUsedPCItemSlots(), 1);
    EXPECT(CheckPCHasItem(ITEM_POTION, 5));
}
