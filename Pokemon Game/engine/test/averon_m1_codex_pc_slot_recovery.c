#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "follower_npc.h"
#include "item.h"
#include "load_save.h"
#include "malloc.h"
#include "overworld.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "save.h"
#include "sprite.h"
#include "gba/flash_internal.h"
#include "constants/event_objects.h"
#include "constants/maps.h"

// Existing maps and the real Gym reward/flash/follower APIs only. This is
// a destructive native flash fixture, never a real gameplay save/Continue.
struct RecoveryState
{
    struct AveronRegionState region;
    struct WarpData location;
    u32 partyCrc, storageCrc, bagCrc, key, counter;
    u32 averonBadges, sinnohBadges, lead, boxed, boxedItem;
    bool32 claimed;
};

static u32 Crc(const void *data, u32 size)
{
    return AveronRegionSave_Crc32(data, size);
}

static void SetBadges(u32 averon, u32 sinnoh)
{
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, averon & (1 << (badge - 1))));
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, sinnoh & (1 << (badge - 1))));
    }
}

static void RebuildFollower(void)
{
    struct WarpData location = gSaveBlock1Ptr->location;
    // Loaded object events have saved sprite IDs; discard both before use.
    ResetSpriteData();
    ResetObjectEvents();
    SetWarpDestination(location.mapGroup, location.mapNum, WARP_ID_NONE, location.x, location.y);
    WarpIntoMap();
    UpdateFollowingPokemon();
}

static void MakeState(struct RecoveryState *state, bool32 newer)
{
    struct BoxPokemon boxed;
    u32 map = newer ? MAP_ALDERFIELDCLINIC : MAP_SALTMERE;
    u32 held = newer ? ITEM_SITRUS_BERRY : ITEM_ORAN_BERRY;
    state->averonBadges = newer ? 0x33 : 0x55;
    state->sinnohBadges = newer ? 0xCC : 0xAA;
    state->lead = newer ? SPECIES_BULBASAUR : SPECIES_PIKACHU;
    state->boxed = newer ? SPECIES_PIPLUP : SPECIES_WOBBUFFET;
    state->boxedItem = newer ? ITEM_LEFTOVERS : ITEM_EXP_SHARE;
    state->claimed = newer;
    RemoveFollowingPokemon();
    AveronRegionSave_InitNewGame();
    SetBadges(state->averonBadges, state->sinnohBadges);
    gSaveBlock2Ptr->encryptionKey = newer ? 0x12345678 : 0xA1B2C3D4;
    SetBagItemsPointers();
    ClearBag();
    EXPECT(AddBagItem(ITEM_POTION, newer ? 12 : 7));
    FlagClear(FLAG_AVERON_GYM1_TM);
    if (newer)
    {
        RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
        EXPECT_EQ(VarGet(VAR_RESULT), TRUE);
    }
    EXPECT(AveronRegion_SetActive(newer ? AVERON_SAVE_REGION_SINNOH : AVERON_SAVE_REGION_AVERON));
    ZeroPlayerPartyMons();
    CreateMonWithIVs(&gParties[B_TRAINER_PLAYER][0], state->lead, 12, 0x12340000 + newer, OTID_STRUCT_PLAYER_ID, 0);
    CreateMonWithIVs(&gParties[B_TRAINER_PLAYER][1], SPECIES_BUNNELBY, 8, 0x43210000 + newer, OTID_STRUCT_PLAYER_ID, 0);
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HELD_ITEM, &held);
    EXPECT_EQ(CalculatePlayerPartyCount(), 2);
    EXPECT_GT(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), 0);
    ResetPokemonStorageSystem();
    CreateBoxMon(&boxed, state->boxed, 10, 0x56780000 + newer, OTID_STRUCT_PLAYER_ID);
    SetBoxMonData(&boxed, MON_DATA_HELD_ITEM, &state->boxedItem);
    SetBoxMonAt(0, 0, &boxed);
    // Populate the last box too: both ends of the serialized PC matter.
    SetBoxMonAt(TOTAL_BOXES_COUNT - 1, IN_BOX_COUNT - 1, &boxed);
    SetWarpDestination(MAP_GROUP(map), MAP_NUM(map), WARP_ID_NONE, newer ? 7 : 18, newer ? 4 : 18);
    WarpIntoMap();
    RebuildFollower();
    EXPECT(GetFollowerObject() != NULL);
    EXPECT_EQ(OW_SPECIES(GetFollowerObject()), state->lead);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT(AveronRegionSave_GetState(&state->region));
    state->location = gSaveBlock1Ptr->location;
    state->partyCrc = Crc(gParties[B_TRAINER_PLAYER], sizeof(gParties[B_TRAINER_PLAYER]));
    state->storageCrc = Crc(gPokemonStoragePtr, sizeof(*gPokemonStoragePtr));
    state->bagCrc = Crc(&gSaveBlock1Ptr->bag, sizeof(gSaveBlock1Ptr->bag));
    state->key = gSaveBlock2Ptr->encryptionKey;
    state->counter = gSaveCounter;
}

static void PoisonRam(bool32 expectedClaimed)
{
    RemoveFollowingPokemon();
    ResetSpriteData();
    ResetObjectEvents();
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    ResetPokemonStorageSystem();
    AveronRegionSave_InitNewGame();
    SetBadges(0, 0);
    gSaveBlock2Ptr->encryptionKey = 0x5A5AA5A5;
    ClearBag();
    EXPECT(AddBagItem(ITEM_POTION, 99));
    if (expectedClaimed)
        FlagClear(FLAG_AVERON_GYM1_TM);
    else
        FlagSet(FLAG_AVERON_GYM1_TM);
    SetWarpDestination(MAP_GROUP(MAP_SALTMEREHOME), MAP_NUM(MAP_SALTMEREHOME), WARP_ID_NONE, 6, 5);
    WarpIntoMap();
}

static void ExpectState(const struct RecoveryState *state)
{
    struct AveronRegionState region;
    EXPECT_EQ(gSaveCounter, state->counter);
    EXPECT_EQ(gSaveBlock2Ptr->encryptionKey, state->key);
    EXPECT_EQ(Crc(gParties[B_TRAINER_PLAYER], sizeof(gParties[B_TRAINER_PLAYER])), state->partyCrc);
    EXPECT_EQ(Crc(gPokemonStoragePtr, sizeof(*gPokemonStoragePtr)), state->storageCrc);
    EXPECT_EQ(Crc(&gSaveBlock1Ptr->bag, sizeof(gSaveBlock1Ptr->bag)), state->bagCrc);
    EXPECT_EQ(CalculatePlayerPartyCount(), 2);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), state->lead);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    EXPECT_EQ(GetBoxMonDataAt(0, 0, MON_DATA_SPECIES), state->boxed);
    EXPECT_EQ(GetBoxMonDataAt(0, 0, MON_DATA_HELD_ITEM), state->boxedItem);
    EXPECT_EQ(GetBoxMonDataAt(TOTAL_BOXES_COUNT - 1, IN_BOX_COUNT - 1, MON_DATA_SPECIES), state->boxed);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), state->claimed);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), state->claimed ? 1 : 0);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), state->claimed ? 12 : 7);
    EXPECT(AveronRegionSave_GetState(&region));
    EXPECT_EQ(memcmp(&region, &state->region, sizeof(region)), 0);
    EXPECT_EQ(memcmp(&gSaveBlock1Ptr->location, &state->location, sizeof(state->location)), 0);
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_AVERON, badge), (state->averonBadges >> (badge - 1)) & 1);
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_SINNOH, badge), (state->sinnohBadges >> (badge - 1)) & 1);
    }
    RebuildFollower();
    EXPECT(GetFollowerObject() != NULL);
    EXPECT_EQ(OW_SPECIES(GetFollowerObject()), state->lead);
}

TEST("Averon M1 torn PC sectors restore one coherent quest Bag party region and follower state")
{
    struct RecoveryState older, newer;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 sectorId = SECTOR_ID_PKMN_STORAGE_START;
    bool32 found = FALSE;
    PARAMETRIZE { sectorId = SECTOR_ID_PKMN_STORAGE_START; }
    PARAMETRIZE { sectorId = SECTOR_ID_PKMN_STORAGE_END; }
    EXPECT(sector != NULL);
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    ClearFollowerNPCData();
    FlagClear(FLAG_TEMP_HIDE_FOLLOWER);
    MakeState(&older, FALSE);
    MakeState(&newer, TRUE);

    // Positive control: the complete newest state really loads first.
    PoisonRam(TRUE);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    ExpectState(&newer);
    for (u32 i = 0; i < NUM_SECTORS_PER_SLOT; ++i)
    {
        u32 physical = newer.counter % NUM_SAVE_SLOTS * NUM_SECTORS_PER_SLOT + i;
        ReadFlash(physical, 0, (u8 *)sector, sizeof(*sector));
        if (sector->id == sectorId)
        {
            EXPECT_EQ(EraseFlashSector(physical), 0);
            found = TRUE;
            break;
        }
    }
    Free(sector);
    EXPECT(found);
    PoisonRam(FALSE);
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_ERROR);
    EXPECT_EQ(AveronRegionSave_IsWriteBlocked(), FALSE);
    ExpectState(&older);

    // The rejected newer reward cannot leak into the recovered save. Claim
    // once again through the real script, save, then load poisoned RAM.
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT), TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 1);
    RUN_OVERWORLD_SCRIPT(call Alderfield_ClaimGymTM;);
    EXPECT_EQ(VarGet(VAR_RESULT), FALSE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 1);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    PoisonRam(TRUE);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(FlagGet(FLAG_AVERON_GYM1_TM), TRUE);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_TM_WORK_UP), 1);
    EXPECT_EQ(Crc(gPokemonStoragePtr, sizeof(*gPokemonStoragePtr)), older.storageCrc);
    EXPECT_EQ(Crc(gParties[B_TRAINER_PLAYER], sizeof(gParties[B_TRAINER_PLAYER])), older.partyCrc);
    RebuildFollower();
    EXPECT(GetFollowerObject() != NULL);
    EXPECT_EQ(OW_SPECIES(GetFollowerObject()), older.lead);
    RemoveFollowingPokemon();
    ResetSpriteData();
    ResetObjectEvents();
    ClearFollowerNPCData();
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    ResetPokemonStorageSystem();
    ClearBag();
    FlagClear(FLAG_AVERON_GYM1_TM);
    SetBadges(0, 0);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
}
