#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "averon_region_travel.h"
#include "event_data.h"
#include "heal_location.h"
#include "load_save.h"
#include "overworld.h"
#include "pokemon.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "test/overworld_script.h"
#include "constants/heal_locations.h"
#include "constants/map_groups.h"

// Region travel (averon_region_travel.c). No Sinnoh maps exist yet, so the
// Hoenn maps stand in: Petalburg for Averon, Oldale for Sinnoh. The tests
// check the transaction, whiteout/Teleport/Escape Rope targets after travel,
// fail-closed inputs, and that travel survives flash and power loss as one
// whole slot.

#define AVERON_HEAL HEAL_LOCATION_PETALBURG_CITY
#define SINNOH_HEAL HEAL_LOCATION_OLDALE_TOWN

struct TravelSnapshot
{
    struct AveronRegionState region;
    struct WarpData location, lastHeal, escape;
    struct Coords16 pos;
};

static u16 (*sRealProgram)(u16, u8 *);
static u16 (*sRealErase)(u16);
static u32 sProgramCalls;
static u32 sPowerLossAfter;

static u16 PowerLossProgram(u16 sectorNum, u8 *src)
{
    u32 call = sProgramCalls++;
    if (call < sPowerLossAfter)
        return sRealProgram(sectorNum, src);
    if (call == sPowerLossAfter)
        sRealErase(sectorNum);
    return 0;
}

static void Snapshot(struct TravelSnapshot *s)
{
    memset(s, 0, sizeof(*s));
    AveronRegionSave_GetState(&s->region);
    s->location = gSaveBlock1Ptr->location;
    s->lastHeal = gSaveBlock1Ptr->lastHealLocation;
    s->escape = gSaveBlock1Ptr->escapeWarp;
    s->pos = gSaveBlock1Ptr->pos;
}

static bool32 SameSnapshot(const struct TravelSnapshot *a)
{
    struct TravelSnapshot b;
    Snapshot(&b);
    return memcmp(a, &b, sizeof(b)) == 0;
}

static bool32 WarpIs(const struct WarpData *w, u32 map, s32 warpId, s32 x, s32 y)
{
    return w->mapGroup == MAP_GROUP(map) && w->mapNum == MAP_NUM(map)
        && w->warpId == warpId && w->x == x && w->y == y;
}

static void Arrive(void)
{
    ApplyCurrentWarp();
    gSaveBlock1Ptr->pos.x = gSaveBlock1Ptr->location.x;
    gSaveBlock1Ptr->pos.y = gSaveBlock1Ptr->location.y;
}

static void StandAt(u32 map, s32 x, s32 y)
{
    gSaveBlock1Ptr->location.mapGroup = MAP_GROUP(map);
    gSaveBlock1Ptr->location.mapNum = MAP_NUM(map);
    gSaveBlock1Ptr->location.warpId = WARP_ID_NONE;
    gSaveBlock1Ptr->location.x = x;
    gSaveBlock1Ptr->location.y = y;
    gSaveBlock1Ptr->pos.x = x;
    gSaveBlock1Ptr->pos.y = y;
}

static void MakeArrival(struct WarpData *w, u32 map, s32 x, s32 y)
{
    w->mapGroup = MAP_GROUP(map);
    w->mapNum = MAP_NUM(map);
    w->warpId = WARP_ID_NONE;
    w->x = x;
    w->y = y;
}

// A fresh Averon game standing in Petalburg, last healed there.
static void StartInAveron(void)
{
    AveronRegionSave_BeginLoad();
    gSaveBlock2Ptr->playerTrainerId[0] = 0x21;
    gSaveBlock2Ptr->playerTrainerId[1] = 0x43;
    gSaveBlock2Ptr->playerTrainerId[2] = 0x65;
    gSaveBlock2Ptr->playerTrainerId[3] = 0x87;
    AveronRegionSave_InitNewGame();
    for (u32 badge = FLAG_BADGE01_GET; badge <= FLAG_BADGE08_GET; badge++)
        FlagClear(badge);
    StandAt(MAP_PETALBURG_CITY, 15, 15);
    SetLastHealLocationWarp(AVERON_HEAL);
    SetEscapeWarp(MAP_GROUP(MAP_PETALBURG_CITY), MAP_NUM(MAP_PETALBURG_CITY), WARP_ID_NONE, 12, 12);
}

static void WhiteOut(void)
{
    SetWarpDestinationToLastHealLocation();
    Arrive();
}

TEST("Averon region travel stores the departure and arms the target region's warps")
{
    struct WarpData arrival, stored;
    StartInAveron();
    MakeArrival(&arrival, MAP_OLDALE_TOWN, 10, 10);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &arrival));
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
    EXPECT(AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_AVERON, &stored));
    EXPECT(WarpIs(&stored, MAP_PETALBURG_CITY, WARP_ID_NONE, 15, 15));
    EXPECT_EQ(AveronRegion_GetHealLocation(AVERON_SAVE_REGION_AVERON), AVERON_HEAL);
    EXPECT(!AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &stored));
    // Not healed in Sinnoh yet: whiteout, Teleport and Escape Rope all stay
    // in Sinnoh at the arrival point instead of returning to Averon.
    EXPECT(WarpIs(&gSaveBlock1Ptr->lastHealLocation, MAP_OLDALE_TOWN, WARP_ID_NONE, 10, 10));
    EXPECT(WarpIs(&gSaveBlock1Ptr->escapeWarp, MAP_OLDALE_TOWN, WARP_ID_NONE, 10, 10));
    Arrive();
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_OLDALE_TOWN, WARP_ID_NONE, 10, 10));
    SetWarpDestinationForTeleport();
    Arrive();
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_OLDALE_TOWN, WARP_ID_NONE, 10, 10));
    SetWarpDestinationToEscapeWarp();
    Arrive();
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_OLDALE_TOWN, WARP_ID_NONE, 10, 10));
}

TEST("Averon region travel whiteout uses the healer of the region the player is in")
{
    struct WarpData arrival;
    StartInAveron();
    MakeArrival(&arrival, MAP_OLDALE_TOWN, 10, 10);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &arrival));
    Arrive();
    WhiteOut(); // before healing in Sinnoh: the arrival point
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_OLDALE_TOWN, WARP_ID_NONE, 10, 10));

    SetLastHealLocationWarp(SINNOH_HEAL); // healed in Sinnoh
    StandAt(MAP_OLDALE_TOWN, 8, 9);
    WhiteOut();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_OLDALE_TOWN_POKEMON_CENTER_1F));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_OLDALE_TOWN_POKEMON_CENTER_1F));

    // Home again: the Averon healer is back, and Sinnoh's is remembered.
    StandAt(MAP_OLDALE_TOWN, 8, 9);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_AVERON, NULL));
    EXPECT_EQ(AveronRegion_GetHealLocation(AVERON_SAVE_REGION_SINNOH), SINNOH_HEAL);
    Arrive();
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_PETALBURG_CITY, WARP_ID_NONE, 15, 15));
    WhiteOut();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_PETALBURG_CITY_POKEMON_CENTER_1F));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_PETALBURG_CITY_POKEMON_CENTER_1F));

    // And back to Sinnoh where the player left it, with its healer.
    StandAt(MAP_PETALBURG_CITY, 16, 15);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, NULL));
    Arrive();
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_OLDALE_TOWN, WARP_ID_NONE, 8, 9));
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), SINNOH_HEAL);
}

TEST("Averon region travel rejects invalid requests and changes nothing")
{
    struct TravelSnapshot before;
    struct WarpData bad;
    StartInAveron();
    Snapshot(&before);

    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_NONE, NULL));
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_COUNT, NULL));
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH | 0x100, NULL));
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_AVERON, NULL)); // already there
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, NULL)); // never visited
    MakeArrival(&bad, MAP_OLDALE_TOWN, 10, 10);
    bad.mapGroup = MAP_GROUPS_COUNT;
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &bad));
    MakeArrival(&bad, MAP_OLDALE_TOWN, 10, 10);
    bad.mapNum = 127;
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &bad));
    MakeArrival(&bad, MAP_OLDALE_TOWN, 10, 10);
    bad.warpId = 100; // indexed warp beyond the map's warp count
    bad.x = bad.y = -1;
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &bad));
    MakeArrival(&bad, MAP_OLDALE_TOWN, 120, 10); // outside the layout
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &bad));
    MakeArrival(&bad, MAP_OLDALE_TOWN, -2, 10);
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &bad));
    EXPECT(SameSnapshot(&before));

    // The player standing somewhere unencodable cannot leave either.
    MakeArrival(&bad, MAP_OLDALE_TOWN, 10, 10);
    gSaveBlock1Ptr->pos.x = 200;
    Snapshot(&before);
    EXPECT(!AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &bad));
    EXPECT(SameSnapshot(&before));
}

TEST("Averon region travel special validates script values before narrowing")
{
    struct TravelSnapshot before;
    StartInAveron();
    Snapshot(&before);
    gSpecialVar_0x8004 = AVERON_SAVE_REGION_SINNOH;
    gSpecialVar_0x8005 = MAP_GROUP(MAP_OLDALE_TOWN) + 256; // would wrap to Oldale's group
    gSpecialVar_0x8006 = MAP_NUM(MAP_OLDALE_TOWN);
    gSpecialVar_0x8007 = WARP_ID_NONE;
    gSpecialVar_0x8008 = 10;
    gSpecialVar_0x8009 = 10;
    gSpecialVar_Result = 0xBEEF;
    AveronRegion_BeginTravelSpecial();
    EXPECT_EQ(gSpecialVar_Result, FALSE);
    gSpecialVar_0x8005 = MAP_GROUP(MAP_OLDALE_TOWN);
    gSpecialVar_0x8006 = MAP_NUM(MAP_OLDALE_TOWN) + 256;
    AveronRegion_BeginTravelSpecial();
    EXPECT_EQ(gSpecialVar_Result, FALSE);
    gSpecialVar_0x8006 = MAP_NUM(MAP_OLDALE_TOWN);
    gSpecialVar_0x8007 = 200;
    AveronRegion_BeginTravelSpecial();
    EXPECT_EQ(gSpecialVar_Result, FALSE);
    gSpecialVar_0x8005 = 0xFFFF; // "return": never visited
    AveronRegion_BeginTravelSpecial();
    EXPECT_EQ(gSpecialVar_Result, FALSE);
    EXPECT(SameSnapshot(&before));

    gSpecialVar_0x8005 = MAP_GROUP(MAP_OLDALE_TOWN);
    gSpecialVar_0x8007 = (u16)WARP_ID_NONE;
    AveronRegion_BeginTravelSpecial();
    EXPECT_EQ(gSpecialVar_Result, TRUE);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
    EXPECT(WarpIs(&gSaveBlock1Ptr->escapeWarp, MAP_OLDALE_TOWN, WARP_ID_NONE, 10, 10));
}

static bool32 StartFlash(void)
{
    CheckForFlashMemory();
    if (!gFlashMemoryPresent)
        return FALSE;
    ClearSaveData();
    Save_ResetSaveCounters();
    StartInAveron();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    CalculatePlayerPartyCount();
    return TRUE;
}

static void Scramble(void)
{
    AveronRegionSave_BeginLoad();
    StandAt(MAP_LITTLEROOT_TOWN, 3, 3);
    memset(&gSaveBlock1Ptr->lastHealLocation, 0x5A, sizeof(struct WarpData));
    memset(&gSaveBlock1Ptr->escapeWarp, 0x5A, sizeof(struct WarpData));
}

TEST("Averon region travel survives a save and load through flash")
{
    struct TravelSnapshot afterTravel;
    struct WarpData arrival;
    EXPECT(StartFlash());
    MakeArrival(&arrival, MAP_OLDALE_TOWN, 10, 10);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &arrival));
    Arrive();
    SetLastHealLocationWarp(SINNOH_HEAL);
    Snapshot(&afterTravel);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    Scramble();
    EXPECT(!SameSnapshot(&afterTravel));
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT(SameSnapshot(&afterTravel));
    // The loaded game can travel home.
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_AVERON, NULL));
    Arrive();
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_PETALBURG_CITY, WARP_ID_NONE, 15, 15));
}

// The region record (sector 0) and the location and heal warps (SaveBlock1,
// sectors 1..4) are in different sectors: a lost write must never pair a
// Sinnoh record with an Averon location or the reverse.
TEST("Averon region travel power loss while saving keeps region and location together")
{
    u32 lostAt = 0;
    struct TravelSnapshot beforeTravel, afterTravel;
    struct WarpData arrival;
    u8 status;
    for (u32 i = 0; i <= NUM_SECTORS_PER_SLOT; i++)
        PARAMETRIZE { lostAt = i; }
    EXPECT(StartFlash());
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK); // both slots valid
    Snapshot(&beforeTravel);
    MakeArrival(&arrival, MAP_OLDALE_TOWN, 10, 10);
    EXPECT(AveronRegion_BeginTravel(AVERON_SAVE_REGION_SINNOH, &arrival));
    Arrive();
    Snapshot(&afterTravel);
    sRealProgram = ProgramFlashSector;
    sRealErase = EraseFlashSector;
    sProgramCalls = 0;
    sPowerLossAfter = lostAt;
    ProgramFlashSector = PowerLossProgram;
    HandleSavingData(SAVE_NORMAL);
    ProgramFlashSector = sRealProgram;
    Scramble();
    Save_ResetSaveCounters();
    status = LoadGameSave(SAVE_NORMAL);
    if (lostAt == NUM_SECTORS_PER_SLOT)
    {
        EXPECT_EQ(status, SAVE_STATUS_OK);
        EXPECT(SameSnapshot(&afterTravel));
    }
    else
    {
        EXPECT_EQ(status, SAVE_STATUS_ERROR);
        EXPECT(SameSnapshot(&beforeTravel));
    }
}

// The special is registered in data/specials.inc, which also keeps the
// transaction in the GBA ROM: without a gSpecials entry nothing references
// it and the linker drops it. This goes through the real `special` command.
TEST("Averon region travel runs from an overworld script through the registered special")
{
    struct TravelSnapshot before;
    struct WarpData warp;
    StartInAveron();

    gSpecialVar_0x8004 = AVERON_SAVE_REGION_AVERON; // already there
    gSpecialVar_0x8005 = 0xFFFF;
    gSpecialVar_Result = 0xBEEF;
    Snapshot(&before);
    RUN_OVERWORLD_SCRIPT(special AveronRegion_BeginTravelSpecial;);
    EXPECT_EQ(gSpecialVar_Result, FALSE);
    EXPECT(SameSnapshot(&before));

    gSpecialVar_0x8004 = AVERON_SAVE_REGION_SINNOH;
    gSpecialVar_0x8005 = MAP_GROUP(MAP_OLDALE_TOWN);
    gSpecialVar_0x8006 = MAP_NUM(MAP_OLDALE_TOWN);
    gSpecialVar_0x8007 = (u16)WARP_ID_NONE;
    gSpecialVar_0x8008 = 10;
    gSpecialVar_0x8009 = 9;
    RUN_OVERWORLD_SCRIPT(special AveronRegion_BeginTravelSpecial;);
    EXPECT_EQ(gSpecialVar_Result, TRUE);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
    EXPECT(AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_AVERON, &warp));
    EXPECT(WarpIs(&warp, MAP_PETALBURG_CITY, WARP_ID_NONE, 15, 15));
    Arrive();
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_OLDALE_TOWN, WARP_ID_NONE, 10, 9));

    // Back the way the player came, by the "return" form of the special.
    gSpecialVar_0x8004 = AVERON_SAVE_REGION_AVERON;
    gSpecialVar_0x8005 = 0xFFFF;
    RUN_OVERWORLD_SCRIPT(special AveronRegion_BeginTravelSpecial;);
    EXPECT_EQ(gSpecialVar_Result, TRUE);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_AVERON);
    Arrive();
    EXPECT(WarpIs(&gSaveBlock1Ptr->location, MAP_PETALBURG_CITY, WARP_ID_NONE, 15, 15));
    WhiteOut(); // the Averon healer is armed again
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_PETALBURG_CITY_POKEMON_CENTER_1F));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_PETALBURG_CITY_POKEMON_CENTER_1F));
}
