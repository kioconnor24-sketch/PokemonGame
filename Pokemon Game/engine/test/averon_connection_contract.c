#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "event_data.h"
#include "dma3.h"
#include "fieldmap.h"
#include "main.h"
#include "map_name_popup.h"
#include "task.h"
#include "overworld.h"
#include "pokemon.h"
#include "regions.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"

TEST("Averon connection contract actual reciprocal boundary preserves party and region state")
{
    struct Pokemon before;
    struct AveronRegionState region, after;
    MainCallback callback = gMain.callback2;
    const struct MapConnection *outward, *back;
    s32 x = 10, y;
    AveronRegionSave_InitNewGame();
    EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, 3, TRUE));
    EXPECT(AveronRegionSave_GetState(&region));
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    CalculatePlayerPartyCount();
    before = gParties[B_TRAINER_PLAYER][0];
    SetWarpDestination(MAP_GROUP(MAP_OLDALE_TOWN), MAP_NUM(MAP_OLDALE_TOWN), WARP_ID_NONE, x, 0);
    WarpIntoMap();
    outward = GetMapConnection(CONNECTION_SOUTH);
    EXPECT(outward != NULL);
    EXPECT_EQ(outward->mapGroup, MAP_GROUP(MAP_ROUTE101));
    EXPECT_EQ(outward->mapNum, MAP_NUM(MAP_ROUTE101));
    EXPECT_EQ(outward->offset, 0);
    y = gMapHeader.mapLayout->height - 1;
    gSaveBlock1Ptr->pos.y = y;
    InitMap();
    EXPECT(CameraMove(0, 1));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_ROUTE101));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_ROUTE101));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, x);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, 0);
    back = GetMapConnection(CONNECTION_NORTH);
    EXPECT(back != NULL);
    EXPECT_EQ(back->mapGroup, MAP_GROUP(MAP_OLDALE_TOWN));
    EXPECT_EQ(back->mapNum, MAP_NUM(MAP_OLDALE_TOWN));
    EXPECT_EQ(back->offset, -outward->offset);
    EXPECT(CameraMove(0, -1));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_OLDALE_TOWN));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_OLDALE_TOWN));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, x);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, y);
    EXPECT_EQ(memcmp(&before, &gParties[B_TRAINER_PLAYER][0], sizeof(before)), 0);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], 1);
    EXPECT(AveronRegionSave_GetState(&after));
    EXPECT_EQ(memcmp(&region, &after, sizeof(region)), 0);
    EXPECT(gMain.callback2 == callback);
    // Native CameraMove schedules the same deferred VRAM-copy/popup work as
    // gameplay. Drain it instead of suppressing the runner's leak checks.
    HideMapNamePopUpWindow();
    ProcessDma3Requests();
    RunTasks();
}

TEST("Averon connection contract Sinnoh RAM header selects only overlapping signed offset edges")
{
    u32 direction = CONNECTION_NORTH;
    s32 offset = 0;
    struct MapHeader original = gMapHeader;
    struct MapConnection edge = {0};
    struct MapConnections connections = { 1, &edge };
    s32 limit, first, last, perpendicular, inside;
    for (u32 dir = CONNECTION_SOUTH; dir <= CONNECTION_EAST; ++dir)
        for (s32 delta = -5; delta <= 5; delta += 5)
            PARAMETRIZE { direction = dir; offset = delta; }
    // This temporary RAM-only header reuses a real linked layout and target.
    // It does not register a map, choose geography, or write any map files.
    gMapHeader = *Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_OLDALE_TOWN), MAP_NUM(MAP_OLDALE_TOWN));
    gMapHeader.regionMapSectionId = MAPSEC_SANDGEM_TOWN;
    gMapHeader.connections = &connections;
    edge.direction = direction;
    edge.offset = offset;
    edge.mapGroup = MAP_GROUP(MAP_OLDALE_TOWN);
    edge.mapNum = MAP_NUM(MAP_OLDALE_TOWN);
    EXPECT_EQ(GetCurrentRegion(), REGION_SINNOH);
    EXPECT(GetMapConnection(direction) == &edge);
    limit = direction == CONNECTION_NORTH || direction == CONNECTION_SOUTH
        ? gMapHeader.mapLayout->width : gMapHeader.mapLayout->height;
    first = offset > 0 ? offset : 0;
    last = (offset < 0 ? limit + offset : limit) - 1;
    if (direction == CONNECTION_NORTH) { perpendicular = MAP_OFFSET - 1; inside = MAP_OFFSET; }
    else if (direction == CONNECTION_SOUTH) { perpendicular = gMapHeader.mapLayout->height + MAP_OFFSET; inside = perpendicular - 1; }
    else if (direction == CONNECTION_WEST) { perpendicular = MAP_OFFSET - 1; inside = MAP_OFFSET; }
    else { perpendicular = gMapHeader.mapLayout->width + MAP_OFFSET; inside = perpendicular - 1; }
    for (s32 coordinate = 0; coordinate < limit; ++coordinate)
    {
        const struct MapConnection *found, *interior;
        if (direction == CONNECTION_NORTH || direction == CONNECTION_SOUTH)
        {
            found = GetMapConnectionAtPos(coordinate + MAP_OFFSET, perpendicular);
            interior = GetMapConnectionAtPos(coordinate + MAP_OFFSET, inside);
        }
        else
        {
            found = GetMapConnectionAtPos(perpendicular, coordinate + MAP_OFFSET);
            interior = GetMapConnectionAtPos(inside, coordinate + MAP_OFFSET);
        }
        EXPECT(found == (coordinate >= first && coordinate <= last ? &edge : NULL));
        EXPECT(interior == NULL);
    }
    gMapHeader = original;
}
