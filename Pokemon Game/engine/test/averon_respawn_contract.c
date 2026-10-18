#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "heal_location.h"
#include "overworld.h"
#include "pokemon.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"

// No Sandgem production heal ID is approved. Existing unchanged maps are
// stand-ins; these tests do not claim Sandgem nurse or graphical acceptance.
TEST("Averon respawn contract rejects invalid script healer IDs before narrowing")
{
    u32 id = HEAL_LOCATION_NONE;
    struct WarpData before;
    PARAMETRIZE { id = HEAL_LOCATION_NONE; }
    PARAMETRIZE { id = NUM_HEAL_LOCATIONS; }
    PARAMETRIZE { id = 255; }
    PARAMETRIZE { id = 256 + HEAL_LOCATION_PETALBURG_CITY; }
    PARAMETRIZE { id = 0xFF00 + HEAL_LOCATION_PETALBURG_CITY; }
    SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
    before = gSaveBlock1Ptr->lastHealLocation;
    gSpecialVar_0x8004 = id;
    RUN_OVERWORLD_SCRIPT(setrespawn VAR_0x8004;);
    EXPECT_EQ(memcmp(&gSaveBlock1Ptr->lastHealLocation, &before, sizeof(before)), 0);
}

TEST("Averon respawn contract valid script anchors preserve the regional record")
{
    u32 id = HEAL_LOCATION_ALDERFIELD;
    u32 region = AVERON_SAVE_REGION_AVERON;
    u32 destination;
    u8 record[AVERON_REGION_RECORD_SIZE];
    PARAMETRIZE { id = HEAL_LOCATION_ALDERFIELD; region = AVERON_SAVE_REGION_AVERON; }
    PARAMETRIZE { id = HEAL_LOCATION_OLDALE_TOWN; region = AVERON_SAVE_REGION_SINNOH; }
    AveronRegionSave_InitNewGame();
    EXPECT(AveronRegion_SetActive(region));
    memcpy(record, gSaveBlock3Ptr->averonRegionRecord, sizeof(record));
    gSpecialVar_0x8004 = id;
    RUN_OVERWORLD_SCRIPT(setrespawn VAR_0x8004;);
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), id);
    EXPECT_EQ(gSaveBlock1Ptr->lastHealLocation.warpId, WARP_ID_NONE);
    EXPECT_EQ(memcmp(record, gSaveBlock3Ptr->averonRegionRecord, sizeof(record)), 0);
    SetWarpDestinationToLastHealLocation();
    ApplyCurrentWarp();
    destination = id == HEAL_LOCATION_ALDERFIELD ? MAP_ALDERFIELDCLINIC : MAP_OLDALE_TOWN_POKEMON_CENTER_1F;
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(destination));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(destination));
}

TEST("Averon respawn contract healing alone preserves the previous respawn anchor")
{
    struct WarpData before;
    u32 hp = 1, poison = STATUS1_POISON;
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    CalculatePlayerPartyCount();
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &hp);
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_STATUS, &poison);
    SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
    before = gSaveBlock1Ptr->lastHealLocation;
    RUN_OVERWORLD_SCRIPT(special HealPlayerParty;);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MAX_HP));
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_STATUS), 0);
    EXPECT_EQ(memcmp(&before, &gSaveBlock1Ptr->lastHealLocation, sizeof(before)), 0);
}

TEST("Averon respawn contract unregistered arrival stays local without selecting a nurse")
{
    struct WarpData arrival = { MAP_GROUP(MAP_OLDALE_TOWN), MAP_NUM(MAP_OLDALE_TOWN), WARP_ID_NONE, 10, 10 };
    struct WarpData result;
    // This models a region arrival with no registered heal row, not a new
    // destination. No map data or production ID is changed.
    EXPECT_EQ(GetHealLocationIndexByWarpData(&arrival), HEAL_LOCATION_NONE);
    gSaveBlock1Ptr->lastHealLocation = arrival;
    gSpecialVar_LastTalked = gSpecialVar_0x800B = 0xBEEF;
    SetWhiteoutRespawnWarpAndHealerNPC(&result);
    EXPECT_EQ(memcmp(&arrival, &result, sizeof(arrival)), 0);
    EXPECT_EQ(gSpecialVar_LastTalked, 0xBEEF);
    EXPECT_EQ(gSpecialVar_0x800B, 0xBEEF);
    SetWarpDestinationToLastHealLocation();
    ApplyCurrentWarp();
    EXPECT_EQ(memcmp(&arrival, &gSaveBlock1Ptr->location, sizeof(arrival)), 0);
}
