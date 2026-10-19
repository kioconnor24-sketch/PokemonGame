#include "global.h"
#include "test/test.h"
#include "averon_transport.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "load_save.h"
#include "overworld.h"
#include "pokemon.h"
#include "save.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"

// Coordinates are native fixtures on existing maps, not chosen terminals.
static const struct AveronTransportPoint sAveron = {
    AVERON_SAVE_REGION_AVERON, {MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18},
};
static const struct AveronTransportPoint sSinnoh = {
    AVERON_SAVE_REGION_SINNOH, {MAP_GROUP(MAP_SANDGEM_TOWN), MAP_NUM(MAP_SANDGEM_TOWN), WARP_ID_NONE, 15, 10},
};

struct TransportSnapshot
{
    struct AveronRegionState region;
    struct WarpData location, heal, escape;
    struct Coords16 pos;
};

static void Snapshot(struct TransportSnapshot *s)
{
    memset(s, 0, sizeof(*s));
    EXPECT(AveronRegionSave_GetState(&s->region));
    s->location = gSaveBlock1Ptr->location;
    s->heal = gSaveBlock1Ptr->lastHealLocation;
    s->escape = gSaveBlock1Ptr->escapeWarp;
    s->pos = gSaveBlock1Ptr->pos;
}

static void ExpectUnchanged(const struct TransportSnapshot *before)
{
    struct TransportSnapshot after;
    Snapshot(&after);
    EXPECT_EQ(memcmp(before, &after, sizeof(after)), 0);
    // Pending warp was set to the departure by StartAt. A refused call must
    // leave it intact, including its coordinates, not just its map header.
    ApplyCurrentWarp();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, before->location.mapGroup);
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, before->location.mapNum);
    EXPECT_EQ(gSaveBlock1Ptr->location.x, before->location.x);
    EXPECT_EQ(gSaveBlock1Ptr->location.y, before->location.y);
}

static void Arrive(void)
{
    WarpIntoMap();
    gSaveBlock1Ptr->pos.x = gSaveBlock1Ptr->location.x;
    gSaveBlock1Ptr->pos.y = gSaveBlock1Ptr->location.y;
}

static void StartAt(const struct AveronTransportPoint *point)
{
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    EXPECT(AveronRegion_SetActive(point->region));
    SetWarpDestination(point->warp.mapGroup, point->warp.mapNum, WARP_ID_NONE, point->warp.x, point->warp.y);
    Arrive();
    if (point->region == AVERON_SAVE_REGION_AVERON)
        SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
    else
        gSaveBlock1Ptr->lastHealLocation = point->warp;
    gSaveBlock1Ptr->escapeWarp = point->warp;
}

TEST("Averon transport points validate physical region identity and indexed arrivals")
{
    EXPECT(AveronTransport_IsPointValid(&sAveron));
    EXPECT(AveronTransport_IsPointValid(&sSinnoh));
    EXPECT(!AveronTransport_IsPointValid(NULL));
    struct AveronTransportPoint point = sSinnoh;
    for (u32 region = 0; region <= 0x100; ++region)
    {
        point.region = region;
        EXPECT_EQ(AveronTransport_IsPointValid(&point), region == AVERON_SAVE_REGION_SINNOH);
    }
    point = sAveron;
    point.region = AVERON_SAVE_REGION_SINNOH;
    EXPECT(!AveronTransport_IsPointValid(&point));
    point = sSinnoh;
    point.warp.mapNum = 127;
    EXPECT(!AveronTransport_IsPointValid(&point));
    point = sSinnoh;
    point.warp.x = 127;
    EXPECT(!AveronTransport_IsPointValid(&point));
    point = sSinnoh;
    point.warp.warpId = 0;
    point.warp.x = point.warp.y = -1;
    EXPECT(AveronTransport_IsPointValid(&point));
    point.warp.x = 15;
    EXPECT(!AveronTransport_IsPointValid(&point));
}

TEST("Averon transport first arrival and saved return use the existing regional transaction")
{
    u32 reverse = 0;
    PARAMETRIZE { reverse = 0; }
    PARAMETRIZE { reverse = 1; }
    const struct AveronTransportPoint *from = reverse ? &sSinnoh : &sAveron;
    const struct AveronTransportPoint *to = reverse ? &sAveron : &sSinnoh;
    StartAt(from);
    EXPECT(AveronTransport_Begin(from, to, FALSE));
    Arrive();
    EXPECT_EQ(AveronRegion_GetActive(), to->region);
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, to->warp.mapGroup);
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, to->warp.x);
    EXPECT(AveronTransport_Begin(to, from, TRUE));
    Arrive();
    EXPECT_EQ(AveronRegion_GetActive(), from->region);
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, from->warp.mapNum);
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, from->warp.x);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, from->warp.y);
}

TEST("Averon transport rejects invalid activation descriptors and leaves all travel state unchanged")
{
    u32 which = 0;
    for (u32 i = 0; i < 9; ++i)
        PARAMETRIZE { which = i; }
    StartAt(&sAveron);
    struct AveronTransportPoint departure = sAveron, arrival = sSinnoh;
    if (which == 0) departure.warp.x++;
    if (which == 1) departure.warp.mapNum++;
    if (which == 2) EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    if (which == 3) arrival.region = AVERON_SAVE_REGION_AVERON;
    if (which == 4) arrival.warp.x = -1;
    if (which == 5) departure.region = AVERON_SAVE_REGION_COUNT;
    if (which == 6) arrival = sAveron;
    if (which == 7) { departure = sSinnoh; departure.warp.warpId = 0; departure.warp.x = departure.warp.y = -1; }
    struct TransportSnapshot before;
    Snapshot(&before);
    EXPECT(!AveronTransport_Begin(which == 8 ? NULL : &departure, &arrival, FALSE));
    ExpectUnchanged(&before);
    EXPECT(!AveronTransport_Begin(&departure, NULL, FALSE));
    ExpectUnchanged(&before);
}

TEST("Averon transport refuses missing or physically wrong region saved returns before mutation")
{
    u32 reverse = 0;
    PARAMETRIZE { reverse = 0; }
    PARAMETRIZE { reverse = 1; }
    const struct AveronTransportPoint *from = reverse ? &sSinnoh : &sAveron;
    const struct AveronTransportPoint *to = reverse ? &sAveron : &sSinnoh;
    StartAt(from);
    struct TransportSnapshot before;
    Snapshot(&before);
    EXPECT(!AveronTransport_Begin(from, to, TRUE));
    ExpectUnchanged(&before);
    // Low-level record setters intentionally accept arbitrary valid warps.
    // The configured transport adapter supplies the stronger region contract.
    EXPECT(AveronRegion_SetReturnWarp(to->region, &from->warp));
    Snapshot(&before);
    EXPECT(!AveronTransport_Begin(from, to, TRUE));
    ExpectUnchanged(&before);
}

TEST("Averon transport saved return selects the recorded point instead of the configured first arrival")
{
    u32 reverse = 0;
    PARAMETRIZE { reverse = 0; }
    PARAMETRIZE { reverse = 1; }
    const struct AveronTransportPoint *from = reverse ? &sSinnoh : &sAveron;
    const struct AveronTransportPoint *to = reverse ? &sAveron : &sSinnoh;
    StartAt(from);
    struct WarpData recorded = to->warp;
    recorded.x++;
    EXPECT(AveronRegion_SetReturnWarp(to->region, &recorded));
    EXPECT(AveronTransport_Begin(from, to, TRUE));
    Arrive();
    EXPECT_EQ(AveronRegion_GetActive(), to->region);
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, recorded.x);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, recorded.y);
    EXPECT(gSaveBlock1Ptr->pos.x != to->warp.x);
}

TEST("Averon transport accepts an indexed first arrival without substituting coordinates")
{
    StartAt(&sAveron);
    struct AveronTransportPoint indexed = sSinnoh;
    indexed.warp.warpId = 0;
    indexed.warp.x = indexed.warp.y = -1;
    EXPECT(AveronTransport_Begin(&sAveron, &indexed, FALSE));
    EXPECT(GetDestinationWarpMapHeader() == Overworld_GetMapHeaderByGroupAndId(indexed.warp.mapGroup, indexed.warp.mapNum));
    EXPECT_EQ(gSaveBlock1Ptr->escapeWarp.warpId, 0);
    EXPECT_EQ(gSaveBlock1Ptr->escapeWarp.x, -1);
    EXPECT_EQ(gSaveBlock1Ptr->escapeWarp.y, -1);
    // Normal field initialization resolves indexed coordinates; this fixture
    // deliberately does not claim to execute that graphical arrival path.
}

TEST("Averon transport refuses a wrong region cached healer without changing the transaction")
{
    StartAt(&sAveron);
    EXPECT(AveronRegion_SetHealLocation(AVERON_SAVE_REGION_SINNOH, HEAL_LOCATION_ALDERFIELD));
    struct TransportSnapshot before;
    Snapshot(&before);
    EXPECT(!AveronTransport_Begin(&sAveron, &sSinnoh, FALSE));
    ExpectUnchanged(&before);
    EXPECT(AveronRegion_SetHealLocation(AVERON_SAVE_REGION_SINNOH, HEAL_LOCATION_NONE));
    EXPECT(AveronTransport_Begin(&sAveron, &sSinnoh, FALSE));
}

TEST("Averon transport saved return validation remains usable after an actual flash reload")
{
    u32 reverse = 0;
    PARAMETRIZE { reverse = 0; }
    PARAMETRIZE { reverse = 1; }
    const struct AveronTransportPoint *from = reverse ? &sSinnoh : &sAveron;
    const struct AveronTransportPoint *to = reverse ? &sAveron : &sSinnoh;
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    ClearSaveData();
    Save_ResetSaveCounters();
    StartAt(from);
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculatePlayerPartyCount();
    EXPECT(AveronTransport_Begin(from, to, FALSE));
    Arrive();
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    AveronRegionSave_InitNewGame();
    memset(&gSaveBlock1Ptr->location, 0x5A, sizeof(struct WarpData));
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegion_GetActive(), to->region);
    EXPECT(AveronTransport_Begin(to, from, TRUE));
    Arrive();
    EXPECT_EQ(AveronRegion_GetActive(), from->region);
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, from->warp.x);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, from->warp.y);
}
