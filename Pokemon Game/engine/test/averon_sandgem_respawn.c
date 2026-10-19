#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "averon_region_save.h"
#include "averon_region_travel.h"
#include "event_data.h"
#include "heal_location.h"
#include "load_save.h"
#include "overworld.h"
#include "save.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"

// Owner-approved Sandgem whiteout anchor (Issue #15 comment 6259265791).
// The ID is saved in the region record, so it is appended and pinned.
STATIC_ASSERT(HEAL_LOCATION_SANDGEM_TOWN == 44, sandgem_owner_approved_heal_id);
STATIC_ASSERT(HEAL_LOCATION_ALDERFIELD == 43, sandgem_preserves_existing_heal_ids);
STATIC_ASSERT(NUM_HEAL_LOCATIONS == 45, no_other_heal_allocations);

TEST("Averon Sandgem heal anchor is the tile below the Center door")
{
    const struct HealLocation *heal = GetHealLocation(HEAL_LOCATION_SANDGEM_TOWN);
    EXPECT(heal != NULL);
    EXPECT_EQ(heal->mapGroup, MAP_GROUP(MAP_SANDGEM_TOWN));
    EXPECT_EQ(heal->mapNum, MAP_NUM(MAP_SANDGEM_TOWN));
    EXPECT_EQ(heal->x, 15);
    EXPECT_EQ(heal->y, 10);
    EXPECT_EQ(GetHealLocationByMap(MAP_GROUP(MAP_SANDGEM_TOWN), MAP_NUM(MAP_SANDGEM_TOWN)), heal);
}

TEST("Averon Sandgem setrespawn whites out in front of the Sandgem nurse")
{
    struct WarpData respawn = {0};
    SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
    RUN_OVERWORLD_SCRIPT(setrespawn HEAL_LOCATION_SANDGEM_TOWN;);
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), HEAL_LOCATION_SANDGEM_TOWN);
    EXPECT_EQ(gSaveBlock1Ptr->lastHealLocation.warpId, WARP_ID_NONE);
    gSpecialVar_LastTalked = gSpecialVar_0x800B = 0;
    SetWhiteoutRespawnWarpAndHealerNPC(&respawn);
    EXPECT_EQ(respawn.mapGroup, MAP_GROUP(MAP_SANDGEM_TOWN_POKEMON_CENTER_1F));
    EXPECT_EQ(respawn.mapNum, MAP_NUM(MAP_SANDGEM_TOWN_POKEMON_CENTER_1F));
    EXPECT_EQ(respawn.warpId, WARP_ID_NONE);
    EXPECT_EQ(respawn.x, 7);
    EXPECT_EQ(respawn.y, 4);
    EXPECT_EQ(GetHealNpcLocalId(HEAL_LOCATION_SANDGEM_TOWN), 1);
    EXPECT_EQ(gSpecialVar_LastTalked, 1);
    EXPECT_EQ(gSpecialVar_0x800B, 1);
    EXPECT_EQ(IsLastHealLocationPlayerHouse(), FALSE);
}

TEST("Averon Sandgem healer survives leaving Sinnoh, a flash save and the return trip")
{
    struct WarpData sandgem = { MAP_GROUP(MAP_SANDGEM_TOWN), MAP_NUM(MAP_SANDGEM_TOWN), WARP_ID_NONE, 15, 10 };
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    memset(gSaveBlock2Ptr->playerTrainerId, 0x37, TRAINER_ID_LENGTH);
    SetWarpDestination(MAP_GROUP(MAP_PETALBURG_CITY), MAP_NUM(MAP_PETALBURG_CITY), WARP_ID_NONE, 15, 15);
    WarpIntoMap();
    SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &sandgem));
    WarpIntoMap();
    RUN_OVERWORLD_SCRIPT(setrespawn HEAL_LOCATION_SANDGEM_TOWN;);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_AVERON, NULL));
    WarpIntoMap();
    EXPECT_EQ(AveronRegion_GetHealLocation(AVERON_SAVE_REGION_SINNOH), HEAL_LOCATION_SANDGEM_TOWN);
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), HEAL_LOCATION_ALDERFIELD);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    AveronRegionSave_InitNewGame();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegion_GetHealLocation(AVERON_SAVE_REGION_SINNOH), HEAL_LOCATION_SANDGEM_TOWN);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &sandgem));
    WarpIntoMap();
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), HEAL_LOCATION_SANDGEM_TOWN);
    ClearSaveData();
}
