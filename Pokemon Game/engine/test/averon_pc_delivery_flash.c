#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "item.h"
#include "load_save.h"
#include "move.h"
#include "overworld.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "save.h"
#include "constants/characters.h"
#include "constants/maps.h"

// Direct production delivery/storage API fixture, not a real capture, gift
// caller or the Gen VII full-party swap menu. Normal saves include Pokemon
// storage; SAVE_LINK intentionally does not and is not used for this proof.
#define AVERON_BADGES 0x49
#define SINNOH_BADGES 0xB2
#define PLAYER_OT_ID 0x78563412
#define FILLER_PERSONALITY 0x10203040
#define DELIVERY_PERSONALITY 0x1234FEDC

static void SetBadgeBanks(u32 averon, u32 sinnoh)
{
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, averon & (1 << (badge - 1))));
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, sinnoh & (1 << (badge - 1))));
    }
}

static u32 PartyCrc(void)
{
    return AveronRegionSave_Crc32((const u8 *)gParties[B_TRAINER_PLAYER],
                                 sizeof(gParties[B_TRAINER_PLAYER]));
}

static u32 StorageCrc(void)
{
    return AveronRegionSave_Crc32((const u8 *)gPokemonStoragePtr, sizeof(*gPokemonStoragePtr));
}

static u32 BagCrc(void)
{
    return AveronRegionSave_Crc32((const u8 *)&gSaveBlock1Ptr->bag, sizeof(gSaveBlock1Ptr->bag));
}

static u32 StorageAfterFirstSlotCrc(void)
{
    const u8 *tail = (const u8 *)(GetBoxedMonPtr(0, 0) + 1);
    const u8 *end = (const u8 *)gPokemonStoragePtr + sizeof(*gPokemonStoragePtr);
    return AveronRegionSave_Crc32(tail, end - tail);
}

static void ExpectDeliveredState(void)
{
    u32 delivered = 0, shares = 0;
    EXPECT_EQ(CalculatePlayerPartyCount(), PARTY_SIZE);
    EXPECT_EQ(CheckFreePokemonStorageSpace(), FALSE);
    EXPECT_EQ(CountStorageNonEggMons(), TOTAL_BOXES_COUNT * IN_BOX_COUNT);
    EXPECT_EQ(StorageGetCurrentBox(), TOTAL_BOXES_COUNT - 1);
    EXPECT_EQ(VarGet(VAR_PC_BOX_TO_SEND_MON), 0);
    EXPECT_EQ(GetBoxMonDataAt(0, 0, MON_DATA_SPECIES), SPECIES_PIPLUP);
    EXPECT_EQ(GetBoxMonDataAt(0, 0, MON_DATA_PERSONALITY), DELIVERY_PERSONALITY);
    EXPECT_EQ(GetBoxMonDataAt(0, 0, MON_DATA_OT_ID), PLAYER_OT_ID);
    EXPECT_EQ(GetBoxMonDataAt(0, 0, MON_DATA_HELD_ITEM), ITEM_EXP_SHARE);
    EXPECT_EQ(GetBoxMonDataAt(0, 0, MON_DATA_MOVE1), MOVE_TACKLE);
    EXPECT_EQ(GetBoxMonDataAt(0, 0, MON_DATA_PP1), GetMovePP(MOVE_TACKLE));
    EXPECT_EQ(GetLevelFromBoxMonExp(GetBoxedMonPtr(0, 0)), 12);
    EXPECT_EQ(CheckBoxMonSanityAt(0, 0), TRUE);
    for (u32 box = 0; box < TOTAL_BOXES_COUNT; ++box)
        for (u32 slot = 0; slot < IN_BOX_COUNT; ++slot)
        {
            delivered += GetBoxMonDataAt(box, slot, MON_DATA_SPECIES) == SPECIES_PIPLUP;
            shares += GetBoxMonDataAt(box, slot, MON_DATA_HELD_ITEM) == ITEM_EXP_SHARE;
        }
    EXPECT_EQ(delivered, 1);
    EXPECT_EQ(shares, 1);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_EXP_SHARE), 0);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), 7);
}

static void ExerciseDeliveryFlash(bool32 foreignOt)
{
    struct Pokemon delivery;
    struct BoxPokemon filler;
    struct AveronRegionState region, loadedRegion;
    u32 partyCrc, storageCrc, bagCrc, untouchedStorageCrc, key;
    u32 heldItem = ITEM_EXP_SHARE, zero = 0;

    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    gSaveBlock2Ptr->playerTrainerId[0] = 0x12;
    gSaveBlock2Ptr->playerTrainerId[1] = 0x34;
    gSaveBlock2Ptr->playerTrainerId[2] = 0x56;
    gSaveBlock2Ptr->playerTrainerId[3] = 0x78;
    memset(gSaveBlock2Ptr->playerName, EOS, sizeof(gSaveBlock2Ptr->playerName));
    gSaveBlock2Ptr->playerName[0] = CHAR_A;
    AveronRegionSave_InitNewGame();
    SetBadgeBanks(AVERON_BADGES, SINNOH_BADGES);
    EXPECT(AveronRegionSave_GetState(&region));
    SetWarpDestination(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18);
    WarpIntoMap();
    SetBagItemsPointers();
    ClearBag();
    EXPECT(AddBagItem(ITEM_POTION, 7));

    ZeroPlayerPartyMons();
    for (u32 slot = 0; slot < PARTY_SIZE; ++slot)
        CreateMonWithIVs(&gParties[B_TRAINER_PLAYER][slot], SPECIES_WOBBUFFET,
                         10, FILLER_PERSONALITY + slot, OTID_STRUCT_PLAYER_ID, 0);
    EXPECT_EQ(CalculatePlayerPartyCount(), PARTY_SIZE);
    ResetPokemonStorageSystem();
    CreateBoxMon(&filler, SPECIES_WOBBUFFET, 10, FILLER_PERSONALITY, OTID_STRUCT_PLAYER_ID);
    for (u32 box = 0; box < TOTAL_BOXES_COUNT; ++box)
        for (u32 slot = 0; slot < IN_BOX_COUNT; ++slot)
            SetBoxMonAt(box, slot, &filler);
    gPokemonStoragePtr->currentBox = TOTAL_BOXES_COUNT - 1;
    VarSet(VAR_PC_BOX_TO_SEND_MON, TOTAL_BOXES_COUNT - 1);
    FlagSet(FLAG_SHOWN_BOX_WAS_FULL_MESSAGE);
    CreateMonWithIVs(&delivery, SPECIES_PIPLUP, 12, DELIVERY_PERSONALITY,
                     foreignOt ? OTID_STRUCT_PRESET(0xA1B2C3D4) : OTID_STRUCT_PLAYER_ID, 0);
    SetMonData(&delivery, MON_DATA_HELD_ITEM, &heldItem);
    SetMonMoveSlot(&delivery, MOVE_TACKLE, 0);
    SetMonData(&delivery, MON_DATA_PP1, &zero);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_HELD_ITEM), ITEM_EXP_SHARE);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_PP1), 0);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_OT_ID), foreignOt ? 0xA1B2C3D4 : PLAYER_OT_ID);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_SPECIES), SPECIES_PIPLUP);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    partyCrc = PartyCrc();
    storageCrc = StorageCrc();
    bagCrc = BagCrc();

    EXPECT_EQ(CheckFreePokemonStorageSpace(), FALSE);
    EXPECT_EQ(GiveCapturedMonToPlayer(&delivery), MON_CANT_GIVE);
    EXPECT_EQ(CalculatePlayerPartyCount(), PARTY_SIZE);
    EXPECT_EQ(PartyCrc(), partyCrc);
    EXPECT_EQ(StorageCrc(), storageCrc);
    EXPECT_EQ(BagCrc(), bagCrc);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_HELD_ITEM), ITEM_EXP_SHARE);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_PP1), 0);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_SPECIES), SPECIES_PIPLUP);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    // The API intentionally assigns the player's OT even on refusal. Its
    // input is not claimed byte-immutable; party and storage must be.
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_OT_ID), PLAYER_OT_ID);

    ZeroBoxMonAt(0, 0);
    EXPECT_EQ(CheckFreePokemonStorageSpace(), TRUE);
    untouchedStorageCrc = StorageAfterFirstSlotCrc();
    EXPECT_EQ(GiveCapturedMonToPlayer(&delivery), MON_GIVEN_TO_PC);
    EXPECT_EQ(gSpecialVar_MonBoxId, 0);
    EXPECT_EQ(gSpecialVar_MonBoxPos, 0);
    EXPECT_EQ(FlagGet(FLAG_SHOWN_BOX_WAS_FULL_MESSAGE), FALSE);
    EXPECT_EQ(StorageAfterFirstSlotCrc(), untouchedStorageCrc);
    EXPECT_EQ(PartyCrc(), partyCrc);
    EXPECT_EQ(BagCrc(), bagCrc);
    ExpectDeliveredState();
    storageCrc = StorageCrc();
    key = gSaveBlock2Ptr->encryptionKey;
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);

    // Poison each persisted component. A skipped/no-op load cannot pass on
    // the delivery still being present in the runtime storage or party.
    ResetPokemonStorageSystem();
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    AveronRegionSave_InitNewGame();
    SetBadgeBanks(0, 0);
    VarSet(VAR_PC_BOX_TO_SEND_MON, TOTAL_BOXES_COUNT - 1);
    gSaveBlock2Ptr->encryptionKey ^= 0x5A5A5A5A;
    ClearBag();
    EXPECT(AddBagItem(ITEM_EXP_SHARE, 2));
    EXPECT(AddBagItem(ITEM_POTION, 99));
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
    EXPECT_EQ(gSaveBlock2Ptr->encryptionKey, key);
    EXPECT_EQ(PartyCrc(), partyCrc);
    EXPECT_EQ(StorageCrc(), storageCrc);
    EXPECT_EQ(BagCrc(), bagCrc);
    EXPECT(AveronRegionSave_GetState(&loadedRegion));
    EXPECT_EQ(memcmp(&region, &loadedRegion, sizeof(region)), 0);
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_AVERON, badge), (AVERON_BADGES >> (badge - 1)) & 1);
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_SINNOH, badge), (SINNOH_BADGES >> (badge - 1)) & 1);
    }
    ExpectDeliveredState();

    // Refusal after loading a full PC cannot append another copy or move its
    // held item into the Bag. General delivery is not an idempotent gift API.
    EXPECT_EQ(GiveCapturedMonToPlayer(&delivery), MON_CANT_GIVE);
    EXPECT_EQ(PartyCrc(), partyCrc);
    EXPECT_EQ(StorageCrc(), storageCrc);
    EXPECT_EQ(BagCrc(), bagCrc);

    ResetPokemonStorageSystem();
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    ClearBag();
    SetBadgeBanks(0, 0);
    VarSet(VAR_PC_BOX_TO_SEND_MON, 0);
    FlagClear(FLAG_SHOWN_BOX_WAS_FULL_MESSAGE);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
}

TEST("Averon full PC delivery refuses atomically then wraps into one free slot and survives regional flash")
{
    ExerciseDeliveryFlash(FALSE);
}

// Ordinary wild constructors already use the player's OT. This is the
// production API's foreign-OT boundary, not evidence of a live capture bug.
TEST("Averon foreign OT PC delivery preserves encrypted data on refusal retry and regional flash")
{
    ExerciseDeliveryFlash(TRUE);
}

TEST("Averon foreign OT delivery preserves encrypted data when the party has space")
{
    struct Pokemon delivery;
    u32 heldItem = ITEM_EXP_SHARE, zero = 0;

    gSaveBlock2Ptr->playerTrainerId[0] = 0x12;
    gSaveBlock2Ptr->playerTrainerId[1] = 0x34;
    gSaveBlock2Ptr->playerTrainerId[2] = 0x56;
    gSaveBlock2Ptr->playerTrainerId[3] = 0x78;
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    CreateMonWithIVs(&delivery, SPECIES_PIPLUP, 12, DELIVERY_PERSONALITY,
                     OTID_STRUCT_PRESET(0xA1B2C3D4), 0);
    SetMonData(&delivery, MON_DATA_HELD_ITEM, &heldItem);
    SetMonMoveSlot(&delivery, MOVE_TACKLE, 0);
    SetMonData(&delivery, MON_DATA_PP1, &zero);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_HELD_ITEM), ITEM_EXP_SHARE);
    EXPECT_EQ(GetMonData(&delivery, MON_DATA_SPECIES), SPECIES_PIPLUP);
    EXPECT_EQ(GiveCapturedMonToPlayer(&delivery), MON_GIVEN_TO_PARTY);
    EXPECT_EQ(CalculatePlayerPartyCount(), 1);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HELD_ITEM), ITEM_EXP_SHARE);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_PIPLUP);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_PERSONALITY), DELIVERY_PERSONALITY);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_OT_ID), PLAYER_OT_ID);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MOVE1), MOVE_TACKLE);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_PP1), 0);
    EXPECT_EQ(memcmp(&delivery, &gParties[B_TRAINER_PLAYER][0], sizeof(delivery)), 0);
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
}
