#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "averon_region_travel.h"
#include "event_data.h"
#include "fieldmap.h"
#include "follower_npc.h"
#include "heal_location.h"
#include "load_save.h"
#include "main.h"
#include "money.h"
#include "overworld.h"
#include "party_menu.h"
#include "pokenav.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "region_map.h"
#include "regions.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"
#include "../src/data/map_group_count.h"

// Native/flash fixtures, not a transport script or graphical Continue proof.
// Newly linked approved Sinnoh maps/healers join this matrix automatically.
#define SINNOH_GROUP MAP_GROUP(MAP_SANDGEM_TOWN)
#define LAST_BOX (TOTAL_BOXES_COUNT - 1)
#define LAST_SLOT (IN_BOX_COUNT - 1)

struct ResumeSnapshot
{
    struct AveronRegionState region;
    struct WarpData location, heal, escape;
    struct Coords16 pos;
    struct Pokemon party;
    struct BoxPokemon boxed;
    u32 money;
    u8 averonBadges;
};

static u16 (*sRealProgram)(u16, u8 *);
static u16 (*sRealErase)(u16);
static u32 sProgramCalls, sLostAt;

static u16 InterruptedProgram(u16 sector, u8 *src)
{
    u32 call = sProgramCalls++;
    if (call < sLostAt)
        return sRealProgram(sector, src);
    if (call == sLostAt)
        sRealErase(sector);
    return 0; // power absent for every subsequent attempted write
}

static void Snapshot(struct ResumeSnapshot *s)
{
    memset(s, 0, sizeof(*s));
    EXPECT(AveronRegionSave_GetState(&s->region));
    s->location = gSaveBlock1Ptr->location;
    s->heal = gSaveBlock1Ptr->lastHealLocation;
    s->escape = gSaveBlock1Ptr->escapeWarp;
    s->pos = gSaveBlock1Ptr->pos;
    s->party = gParties[B_TRAINER_PLAYER][0];
    s->boxed = gPokemonStoragePtr->boxes[LAST_BOX][LAST_SLOT];
    s->money = GetMoney(&gSaveBlock1Ptr->money);
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
        s->averonBadges |= AveronRegion_HasBadge(AVERON_SAVE_REGION_AVERON, badge) << (badge - 1);
}

static void ExpectSnapshot(const struct ResumeSnapshot *expected)
{
    struct ResumeSnapshot actual;
    Snapshot(&actual);
    EXPECT_EQ(memcmp(&actual, expected, sizeof(actual)), 0);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], 1);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[LAST_BOX][LAST_SLOT], MON_DATA_SANITY_IS_BAD_EGG), FALSE);
}

static void ExpectWarp(const struct WarpData *actual, const struct WarpData *expected)
{
    // WarpData has an unused padding byte. Decoding a return warp need not
    // reproduce that byte; only its five defined fields are semantic data.
    EXPECT_EQ(actual->mapGroup, expected->mapGroup);
    EXPECT_EQ(actual->mapNum, expected->mapNum);
    EXPECT_EQ(actual->warpId, expected->warpId);
    EXPECT_EQ(actual->x, expected->x);
    EXPECT_EQ(actual->y, expected->y);
}

static struct WarpData Endpoint(u32 map)
{
    const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(SINNOH_GROUP, map);
    // In-bounds native coordinates; midpoint walkability is not asserted.
    struct WarpData result = {SINNOH_GROUP, map, WARP_ID_NONE,
        header->mapLayout->width / 2, header->mapLayout->height / 2};
    EXPECT_EQ(GetRegionForSectionId(header->regionMapSectionId), REGION_SINNOH);
    EXPECT(AveronRegion_IsWarpShapeValid(&result));
    return result;
}

static void StartFlash(void)
{
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    memset(gSaveBlock2Ptr->playerTrainerId, 0x37, TRAINER_ID_LENGTH);
    ResetPokemonStorageSystem();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    u32 origin = MAPSEC_COASTAL_BLUFFS;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION, &origin);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    CalculatePlayerPartyCount();
    gPokemonStoragePtr->boxes[LAST_BOX][LAST_SLOT] = gParties[B_TRAINER_PLAYER][0].box;
    origin = METLOC_SPECIAL_EGG;
    SetBoxMonData(&gPokemonStoragePtr->boxes[LAST_BOX][LAST_SLOT], MON_DATA_MET_LOCATION, &origin);
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
    {
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, badge & 1));
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, !(badge & 1)));
    }
    SetMoney(&gSaveBlock1Ptr->money, 9876);
    SetWarpDestination(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18);
    WarpIntoMap();
    SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
}

static void TravelToSinnoh(u32 map)
{
    struct WarpData endpoint = Endpoint(map);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &endpoint));
    WarpIntoMap();
    u32 healer = GetHealLocationIndexByMap(SINNOH_GROUP, MAP_NUM(MAP_SANDGEM_TOWN));
    if (healer != HEAL_LOCATION_NONE)
        SetLastHealLocationWarp(healer);
}

static void DestroyLiveRam(void)
{
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    SetWarpDestination(MAP_GROUP(MAP_PETALBURG_CITY), MAP_NUM(MAP_PETALBURG_CITY), WARP_ID_NONE, 15, 15);
    WarpIntoMap(); // replace the live Sinnoh header too
    SetLastHealLocationWarp(HEAL_LOCATION_PETALBURG_CITY);
    SetMoney(&gSaveBlock1Ptr->money, 0);
    ZeroPlayerPartyMons();
    memset(&gPokemonStoragePtr->boxes[LAST_BOX][LAST_SLOT], 0, sizeof(struct BoxPokemon));
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
        EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, FALSE));
}

static void ReloadMapHeader(void)
{
    // Rebuild through the warp loader after flash load, not through the
    // graphical CB2_ContinueSavedGame callback that replaces the runner.
    struct WarpData location = gSaveBlock1Ptr->location;
    struct Coords16 pos = gSaveBlock1Ptr->pos;
    SetWarpDestination(location.mapGroup, location.mapNum, WARP_ID_NONE, pos.x, pos.y);
    WarpIntoMap();
}

static void ReturnFromMap(void) {}

static void ExpectMapUIRefused(void)
{
    MainCallback previous = gMain.callback2;
    IntrCallback vblank = gMain.vblankCallback;
    bool32 unchanged = FALSE;
    ClearFollowerNPCData();
    EXPECT_EQ(IsRegionMapAvailableForSection(gMapHeader.regionMapSectionId), FALSE);
    EXPECT_EQ(SetUpFieldMove_Fly(), FALSE);
    FieldInitRegionMap(ReturnFromMap);
    MainCallback actual = gMain.callback2;
    SetMainCallback2(previous); // restore runner before assertions
    EXPECT(actual == ReturnFromMap);
    EXPECT(gMain.vblankCallback == vblank);
    EXPECT_EQ(TestPokenavMainMenuMapInput(&unchanged), POKENAV_MENU_FUNC_NONE);
    EXPECT(unchanged);
}

TEST("Averon Sinnoh resume validates each linked layout boundary and indexed warp limit")
{
    u32 map = 0;
    for (u32 i = 0; i < MAP_GROUP_COUNT[SINNOH_GROUP]; ++i)
        PARAMETRIZE { map = i; }
    struct WarpData warp = Endpoint(map);
    const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(SINNOH_GROUP, map);
    warp.x = warp.y = 0;
    EXPECT(AveronRegion_IsWarpShapeValid(&warp));
    warp.x = header->mapLayout->width - 1;
    warp.y = header->mapLayout->height - 1;
    EXPECT(AveronRegion_IsWarpShapeValid(&warp));
    warp.x++;
    EXPECT(!AveronRegion_IsWarpShapeValid(&warp));
    warp.x = 0;
    warp.y++;
    EXPECT(!AveronRegion_IsWarpShapeValid(&warp));
    warp.x = -1;
    warp.y = 0;
    EXPECT(!AveronRegion_IsWarpShapeValid(&warp));
    warp.x = warp.y = -1;
    warp.warpId = header->events->warpCount;
    EXPECT(!AveronRegion_IsWarpShapeValid(&warp));
    if (header->events->warpCount)
    {
        warp.warpId--;
        EXPECT(AveronRegion_IsWarpShapeValid(&warp));
        warp.x = 0; // indexed and coordinate forms must not be mixed
        EXPECT(!AveronRegion_IsWarpShapeValid(&warp));
    }
}

TEST("Averon Sinnoh resume reloads real endpoints and refuses all three map interfaces")
{
    u32 map = 0;
    for (u32 i = 0; i < MAP_GROUP_COUNT[SINNOH_GROUP]; ++i)
        PARAMETRIZE { map = i; }
    struct ResumeSnapshot expected;
    StartFlash();
    TravelToSinnoh(map);
    u32 origin = gMapHeader.regionMapSectionId;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION, &origin);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    Snapshot(&expected);
    DestroyLiveRam();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    ExpectSnapshot(&expected);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION), origin);
    ReloadMapHeader();
    EXPECT_EQ(gMapHeader.regionMapSectionId, origin);
    ExpectMapUIRefused();
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_AVERON, NULL));
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_SALTMERE));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, 18);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, 18);
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), HEAL_LOCATION_ALDERFIELD);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, NULL));
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, map);
    EXPECT_EQ(gMapHeader.regionMapSectionId, origin);
    ExpectWarp(&gSaveBlock1Ptr->lastHealLocation, &expected.heal);
    struct WarpData respawn;
    SetWhiteoutRespawnWarpAndHealerNPC(&respawn);
    u32 healer = GetHealLocationIndexByMap(SINNOH_GROUP, MAP_NUM(MAP_SANDGEM_TOWN));
    if (healer != HEAL_LOCATION_NONE)
    {
        EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), healer);
        EXPECT_EQ(respawn.mapGroup, SINNOH_GROUP);
        EXPECT_EQ(respawn.mapNum, MAP_NUM(MAP_SANDGEM_TOWN_POKEMON_CENTER_1F));
        EXPECT_EQ(gSpecialVar_LastTalked, GetHealNpcLocalId(healer));
    }
    else
        ExpectWarp(&respawn, &expected.heal);
    ClearSaveData();
    AveronRegionSave_BeginLoad();
}

TEST("Averon Sinnoh resume interrupted return never mixes real region healer party and PC slots")
{
    u32 map = 0, parity = 0, lostAt = 0;
    for (u32 i = 0; i < MAP_GROUP_COUNT[SINNOH_GROUP]; ++i)
    for (u32 p = 0; p < 2; ++p)
    for (u32 cut = 0; cut <= NUM_SECTORS_PER_SLOT; ++cut)
        PARAMETRIZE { map = i; parity = p; lostAt = cut; }
    struct ResumeSnapshot before, after;
    StartFlash();
    TravelToSinnoh(map);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    if (parity)
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    Snapshot(&before);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_AVERON, NULL));
    WarpIntoMap();
    EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, 1, TRUE));
    u32 origin = MAPSEC_SALTMERE, special = METLOC_IN_GAME_TRADE;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION, &origin);
    SetBoxMonData(&gPokemonStoragePtr->boxes[LAST_BOX][LAST_SLOT], MON_DATA_MET_LOCATION, &special);
    SetMoney(&gSaveBlock1Ptr->money, 54321);
    Snapshot(&after);
    sRealProgram = ProgramFlashSector;
    sRealErase = EraseFlashSector;
    sProgramCalls = 0;
    sLostAt = lostAt;
    ProgramFlashSector = InterruptedProgram;
    HandleSavingData(SAVE_NORMAL);
    ProgramFlashSector = sRealProgram;
    EXPECT(sProgramCalls >= NUM_SECTORS_PER_SLOT);
    DestroyLiveRam();
    Save_ResetSaveCounters();
    u32 status = LoadGameSave(SAVE_NORMAL);
    if (lostAt < NUM_SECTORS_PER_SLOT)
    {
        EXPECT_EQ(status, SAVE_STATUS_ERROR);
        ExpectSnapshot(&before);
    }
    else
    {
        EXPECT_EQ(status, SAVE_STATUS_OK);
        ExpectSnapshot(&after);
    }
    ReloadMapHeader();
    if (lostAt < NUM_SECTORS_PER_SLOT)
    {
        EXPECT_EQ(GetRegionForSectionId(gMapHeader.regionMapSectionId), REGION_SINNOH);
        ExpectMapUIRefused();
    }
    else
    {
        EXPECT_EQ(gMapHeader.regionMapSectionId, MAPSEC_SALTMERE);
        EXPECT(IsRegionMapAvailableForSection(gMapHeader.regionMapSectionId));
    }
    ClearSaveData();
    AveronRegionSave_BeginLoad();
}

TEST("Averon Sinnoh resume refuses unallocated sections NONE and special met aliases")
{
    u32 section = MAPSEC_NONE;
    PARAMETRIZE { section = MAPSEC_NONE; }
    for (u32 i = MAPSEC_COUNT; i <= 255; ++i)
        PARAMETRIZE { section = i; }
    gMapHeader = *Overworld_GetMapHeaderByGroupAndId(SINNOH_GROUP, MAP_NUM(MAP_SANDGEM_TOWN));
    gMapHeader.regionMapSectionId = section;
    EXPECT_EQ(IsRegionMapAvailableForSection(section), FALSE);
    // The raw API also accepts u32, unlike MapHeader's 8-bit section field.
    EXPECT_EQ(IsRegionMapAvailableForSection(256), FALSE);
    EXPECT_EQ(IsRegionMapAvailableForSection(0xFFFFFFFF), FALSE);
    ExpectMapUIRefused();
}
