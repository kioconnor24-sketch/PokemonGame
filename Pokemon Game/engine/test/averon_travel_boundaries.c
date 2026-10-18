#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "averon_region_travel.h"
#include "event_data.h"
#include "heal_location.h"
#include "load_save.h"
#include "overworld.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "save.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"

// Existing unchanged Oldale is a stand-in for an approved future Sinnoh
// transport endpoint. No route/transport or production Sinnoh map is added.
static struct WarpData Arrival(void)
{
    struct WarpData result = { MAP_GROUP(MAP_OLDALE_TOWN), MAP_NUM(MAP_OLDALE_TOWN), WARP_ID_NONE, 10, 10 };
    return result;
}

static void Start(void)
{
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    memset(gSaveBlock2Ptr->playerTrainerId, 0x37, TRAINER_ID_LENGTH);
    SetWarpDestination(MAP_GROUP(MAP_PETALBURG_CITY), MAP_NUM(MAP_PETALBURG_CITY), WARP_ID_NONE, 15, 15);
    WarpIntoMap();
    SetLastHealLocationWarp(HEAL_LOCATION_PETALBURG_CITY);
    for (u32 badge = 1; badge <= 8; ++badge)
    {
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, badge & 1));
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, !(badge & 1)));
    }
}

TEST("Averon travel boundaries refusal preserves an already armed destination")
{
    u32 kind = 0;
    u8 record[AVERON_REGION_RECORD_SIZE];
    struct WarpData request, heal, escape;
    struct Coords16 pos;
    for (u32 i = 0; i < 5; ++i)
        PARAMETRIZE { kind = i; }
    Start();
    request = Arrival();
    if (kind == 0) request.x = -1; // neither coordinate nor indexed warp
    if (kind == 1) { request.warpId = 0; request.x = -1; } // mixed shapes
    if (kind == 2) request.mapGroup = -1;
    if (kind == 3) request.warpId = -2;
    if (kind == 4) gSaveBlock1Ptr->pos.x = -1; // invalid departure
    heal = gSaveBlock1Ptr->lastHealLocation;
    escape = gSaveBlock1Ptr->escapeWarp;
    pos = gSaveBlock1Ptr->pos;
    memcpy(record, gSaveBlock3Ptr->averonRegionRecord, sizeof(record));
    // Existing tests snapshot saved fields but not the pending warp. Verify
    // a refusal cannot silently overwrite a previous caller's destination.
    SetWarpDestination(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18);
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &request));
    EXPECT_EQ(memcmp(record, gSaveBlock3Ptr->averonRegionRecord, sizeof(record)), 0);
    EXPECT_EQ(memcmp(&heal, &gSaveBlock1Ptr->lastHealLocation, sizeof(heal)), 0);
    EXPECT_EQ(memcmp(&escape, &gSaveBlock1Ptr->escapeWarp, sizeof(escape)), 0);
    EXPECT_EQ(memcmp(&pos, &gSaveBlock1Ptr->pos, sizeof(pos)), 0);
    ApplyCurrentWarp();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_SALTMERE));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(gSaveBlock1Ptr->location.x, 18);
    EXPECT_EQ(gSaveBlock1Ptr->location.y, 18);
}

TEST("Averon travel boundaries indexed arrivals resolve the real map warp for Teleport and respawn")
{
    struct WarpData request = { MAP_GROUP(MAP_OLDALE_TOWN_POKEMON_CENTER_1F), MAP_NUM(MAP_OLDALE_TOWN_POKEMON_CENTER_1F), 0, -1, -1 };
    struct Coords16 arrived;
    Start();
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &request));
    WarpIntoMap();
    arrived = gSaveBlock1Ptr->pos;
    EXPECT_EQ(arrived.x, gMapHeader.events->warps[0].x);
    EXPECT_EQ(arrived.y, gMapHeader.events->warps[0].y);
    EXPECT_EQ(gSaveBlock1Ptr->location.warpId, 0);
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), HEAL_LOCATION_NONE);
    SetWarpDestinationForTeleport();
    WarpIntoMap();
    EXPECT_EQ(memcmp(&arrived, &gSaveBlock1Ptr->pos, sizeof(arrived)), 0);
    SetWarpDestinationToLastHealLocation();
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, request.mapGroup);
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, request.mapNum);
    EXPECT_EQ(memcmp(&arrived, &gSaveBlock1Ptr->pos, sizeof(arrived)), 0);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
}

TEST("Averon travel boundaries flash Continue preserves Sandgem origins PC and both badge banks")
{
    struct WarpData request;
    struct BoxPokemon boxed;
    struct Pokemon party;
    u32 section = MAPSEC_SANDGEM_TOWN;
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    ClearSaveData();
    Save_ResetSaveCounters();
    Start();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    CalculatePlayerPartyCount();
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION, &section);
    party = gParties[B_TRAINER_PLAYER][0];
    boxed = party.box;
    gPokemonStoragePtr->boxes[0][0] = boxed;
    request = Arrival();
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &request));
    WarpIntoMap();
    // Simulates a separately approved healer being registered in the target
    // region, using only an unchanged real Oldale healer as the stand-in.
    SetLastHealLocationWarp(HEAL_LOCATION_OLDALE_TOWN);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    AveronRegionSave_InitNewGame();
    SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
    ZeroPlayerPartyMons();
    memset(&gPokemonStoragePtr->boxes[0][0], 0, sizeof(boxed));
    for (u32 badge = 1; badge <= 8; ++badge)
        AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, FALSE);
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
    EXPECT_EQ(memcmp(&gParties[B_TRAINER_PLAYER][0], &party, sizeof(party)), 0);
    EXPECT_EQ(memcmp(&gPokemonStoragePtr->boxes[0][0], &boxed, sizeof(boxed)), 0);
    EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[0][0], MON_DATA_MET_LOCATION), MAPSEC_SANDGEM_TOWN);
    EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[0][0], MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    for (u32 badge = 1; badge <= 8; ++badge)
    {
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_AVERON, badge), badge & 1);
        EXPECT_EQ(AveronRegion_HasBadge(AVERON_SAVE_REGION_SINNOH, badge), !(badge & 1));
    }
    SetWarpDestinationToLastHealLocation();
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_OLDALE_TOWN_POKEMON_CENTER_1F));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_OLDALE_TOWN_POKEMON_CENTER_1F));
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_AVERON, NULL));
    EXPECT_EQ(AveronRegion_GetHealLocation(AVERON_SAVE_REGION_SINNOH), HEAL_LOCATION_OLDALE_TOWN);
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_PETALBURG_CITY));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_PETALBURG_CITY));
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), HEAL_LOCATION_PETALBURG_CITY);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
}
