#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "follower_npc.h"
#include "heal_location.h"
#include "item.h"
#include "load_save.h"
#include "move.h"
#include "overworld.h"
#include "pokemon.h"
#include "save.h"
#include "sprite.h"
#include "constants/event_objects.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"

// Native fixtures: DoWhiteOut really heals and warps, and the production
// follower code really creates its object. No graphical nurse/cutscene,
// controller recovery, natural loss or Playtest Q3 acceptance is asserted.
// Both healers and coordinates already exist in heal_locations.json.
#define AVERON_BADGES 0x55
#define SINNOH_BADGES 0xAA

static const enum Species sPartySpecies[] = {SPECIES_PIKACHU, SPECIES_BULBASAUR};
static const enum Item sHeldItems[] = {ITEM_ORAN_BERRY, ITEM_SITRUS_BERRY};

static void SetBadgeBanks(u32 averon, u32 sinnoh)
{
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, averon & (1 << (badge - 1))));
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, sinnoh & (1 << (badge - 1))));
    }
}

static void ExpectRegion(const struct AveronRegionState *expected)
{
    struct AveronRegionState actual;
    EXPECT(AveronRegionSave_GetState(&actual));
    EXPECT_EQ(memcmp(&actual, expected, sizeof(actual)), 0);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_AVERON);
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_AVERON, badge), (AVERON_BADGES >> (badge - 1)) & 1);
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_SINNOH, badge), (SINNOH_BADGES >> (badge - 1)) & 1);
    }
}

static void ResetFieldObjects(void)
{
    RemoveFollowingPokemon();
    ResetSpriteData();
    ResetObjectEvents();
}

static void EnterSaltmere(void)
{
    SetWarpDestination(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18);
    WarpIntoMap();
    ResetFieldObjects();
}

static u32 FollowerSpecies(void)
{
    struct ObjectEvent *follower;
    UpdateFollowingPokemon();
    follower = GetFollowerObject();
    return follower == NULL ? SPECIES_NONE : OW_SPECIES(follower);
}

static void ExpectDestination(u32 map, s32 x, s32 y)
{
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(map));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(map));
    EXPECT_EQ(gSaveBlock1Ptr->location.warpId, WARP_ID_NONE);
    EXPECT_EQ(gSaveBlock1Ptr->location.x, x);
    EXPECT_EQ(gSaveBlock1Ptr->location.y, y);
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, x);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, y);
}

static void ExpectHealedParty(void)
{
    EXPECT_EQ(CalculatePlayerPartyCount(), ARRAY_COUNT(sPartySpecies));
    for (u32 slot = 0; slot < ARRAY_COUNT(sPartySpecies); ++slot)
    {
        struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][slot];
        EXPECT_EQ(GetMonData(mon, MON_DATA_SPECIES), sPartySpecies[slot]);
        EXPECT_GT(GetMonData(mon, MON_DATA_MAX_HP), 0);
        EXPECT_EQ(GetMonData(mon, MON_DATA_HP), GetMonData(mon, MON_DATA_MAX_HP));
        EXPECT_EQ(GetMonData(mon, MON_DATA_STATUS), 0);
        EXPECT_EQ(GetMonData(mon, MON_DATA_MOVE1), MOVE_TACKLE);
        EXPECT_EQ(GetMonData(mon, MON_DATA_PP1), GetMovePP(MOVE_TACKLE));
        EXPECT_EQ(GetMonData(mon, MON_DATA_HELD_ITEM), sHeldItems[slot]);
    }
    EXPECT(GetFirstLiveMon() == &gParties[B_TRAINER_PLAYER][0]);
}

static void ExerciseWhiteoutFlash(u32 healer, u32 map, s32 x, s32 y)
{
    struct AveronRegionState region;
    struct WarpData lastHeal;
    struct Pokemon healedParty[ARRAY_COUNT(sPartySpecies)];
    u32 zero = 0, poison = STATUS1_POISON, move = MOVE_TACKLE;

    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    SetBadgeBanks(AVERON_BADGES, SINNOH_BADGES);
    EXPECT(AveronRegion_SetHealLocation(AVERON_SAVE_REGION_AVERON, healer));
    SetLastHealLocationWarp(healer);
    lastHeal = gSaveBlock1Ptr->lastHealLocation;
    EXPECT(AveronRegionSave_GetState(&region));
    ClearFollowerNPCData();
    FlagClear(FLAG_TEMP_HIDE_FOLLOWER);
    VarSet(VAR_BRINEY_LOCATION, 0);
    VarSet(VAR_SHOULD_END_ABNORMAL_WEATHER, 0);
    SetBagItemsPointers();
    ClearBag();
    ZeroPlayerPartyMons();
    for (u32 slot = 0; slot < ARRAY_COUNT(sPartySpecies); ++slot)
    {
        struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][slot];
        CreateMon(mon, sPartySpecies[slot], 10, slot, OTID_STRUCT_PLAYER_ID);
        CalculateMonStats(mon);
        EXPECT_GT(GetMonData(mon, MON_DATA_HP), 0);
        SetMonData(mon, MON_DATA_MOVE1, &move);
        SetMonData(mon, MON_DATA_HELD_ITEM, &sHeldItems[slot]);
    }
    CalculatePlayerPartyCount();
    EnterSaltmere();
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    for (u32 slot = 0; slot < ARRAY_COUNT(sPartySpecies); ++slot)
    {
        struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][slot];
        SetMonData(mon, MON_DATA_HP, &zero);
        SetMonData(mon, MON_DATA_STATUS, &poison);
        SetMonData(mon, MON_DATA_PP1, &zero);
    }
    EXPECT(GetFirstLiveMon() == NULL);
    EXPECT_EQ(FollowerSpecies(), SPECIES_NONE);

    // Full production entry point, not just selecting a respawn warp or
    // calling HealPlayerParty independently of the whiteout transition.
    DoWhiteOut();
    ExpectDestination(map, x, y);
    EXPECT_EQ(gSpecialVar_LastTalked, GetHealNpcLocalId(healer));
    EXPECT_EQ(gSpecialVar_0x800B, GetHealNpcLocalId(healer));
    EXPECT_EQ(memcmp(&gSaveBlock1Ptr->lastHealLocation, &lastHeal, sizeof(lastHeal)), 0);
    ExpectRegion(&region);
    ExpectHealedParty();
    ResetFieldObjects();
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    memcpy(healedParty, gParties[B_TRAINER_PLAYER], sizeof(healedParty));
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);

    // A different live lead, map, healer and regional state prevent the
    // load assertions from passing on the already-healed runtime state.
    EnterSaltmere();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_BULBASAUR, 5, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    EXPECT_GT(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), 0);
    CalculatePlayerPartyCount();
    EXPECT_EQ(FollowerSpecies(), SPECIES_BULBASAUR);
    AveronRegionSave_InitNewGame();
    SetBadgeBanks(0, 0);
    SetLastHealLocationWarp(healer == HEAL_LOCATION_ALDERFIELD
                            ? HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F
                            : HEAL_LOCATION_ALDERFIELD);

    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
    ExpectDestination(map, x, y);
    EXPECT_EQ(memcmp(&gSaveBlock1Ptr->lastHealLocation, &lastHeal, sizeof(lastHeal)), 0);
    EXPECT_EQ(memcmp(healedParty, gParties[B_TRAINER_PLAYER], sizeof(healedParty)), 0);
    ExpectRegion(&region);
    ExpectHealedParty();

    // Rebuild the loaded map/header and object state, as the existing native
    // follower fixtures do. This is not a rendered Continue/menu test.
    SetWarpDestination(MAP_GROUP(map), MAP_NUM(map), WARP_ID_NONE, x, y);
    WarpIntoMap();
    // Loaded object events refer to saved sprites, not the poisoned live
    // sprites. Discard both before trying to spawn the loaded party's lead.
    ResetSpriteData();
    ResetObjectEvents();
    EXPECT(GetFollowerObject() == NULL);
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    ExpectDestination(map, x, y);
    ExpectRegion(&region);

    ResetFieldObjects();
    ClearFollowerNPCData();
    FlagClear(FLAG_TEMP_HIDE_FOLLOWER);
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    SetBadgeBanks(0, 0);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
}

TEST("Averon native whiteout heals and restores the home follower through flash with regional badges")
{
    ExerciseWhiteoutFlash(HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F, MAP_SALTMEREHOME, 6, 5);
}

TEST("Averon native whiteout heals and restores the clinic follower through flash with regional badges")
{
    ExerciseWhiteoutFlash(HEAL_LOCATION_ALDERFIELD, MAP_ALDERFIELDCLINIC, 7, 4);
}
