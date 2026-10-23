// DEV-only runtime fixture. Installed only by the marked scratch recipe.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"

extern const struct MapHeader *const *const gMapGroups[];
#define HEADER(map) (gMapGroups[MAP_GROUP(map)][MAP_NUM(map)])
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, oreburgh_box_format_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, oreburgh_party_format_unchanged);
STATIC_ASSERT(MAPSEC_NONE == 215, oreburgh_none_unchanged);

TEST("Averon DEV Oreburgh preserves all six individual mine B1 events")
{
    static const u8 xs[] = {11,12,11,12,10,13};
    static const u8 ys[] = {1,1,21,21,21,21};
    static const u8 ids[] = {1,4,0,0,0,0};
    const struct MapEvents *events = HEADER(MAP_OREBURGH_MINE_B1F)->events;
    EXPECT_EQ(events->warpCount, 6);
    for (u32 i = 0; i < 6; i++)
    {
        u32 dest = i < 2 ? MAP_OREBURGH_CITY : MAP_OREBURGH_MINE_B2F;
        EXPECT_EQ(events->warps[i].x, xs[i]); EXPECT_EQ(events->warps[i].y, ys[i]);
        EXPECT_EQ(events->warps[i].elevation, 0); EXPECT_EQ(events->warps[i].warpId, ids[i]);
        EXPECT_EQ(events->warps[i].mapGroup, MAP_GROUP(dest));
        EXPECT_EQ(events->warps[i].mapNum, MAP_NUM(dest));
    }
}

TEST("Averon DEV Oreburgh B2 returns to the canonical B1 downstairs event")
{
    const struct MapEvents *events = HEADER(MAP_OREBURGH_MINE_B2F)->events;
    EXPECT_EQ(events->warpCount, 1);
    EXPECT_EQ(events->warps[0].x, 15); EXPECT_EQ(events->warps[0].y, 1);
    EXPECT_EQ(events->warps[0].warpId, 2);
    EXPECT_EQ(events->warps[0].mapNum, MAP_NUM(MAP_OREBURGH_MINE_B1F));
    EXPECT_EQ(events->warps[0].mapGroup, MAP_GROUP(MAP_OREBURGH_MINE_B1F));
}

TEST("Averon DEV Oreburgh City and Gate use coupled compact return indices")
{
    const struct MapEvents *city = HEADER(MAP_OREBURGH_CITY)->events;
    const struct MapEvents *gate = HEADER(MAP_OREBURGH_GATE_1F)->events;
    EXPECT_EQ(city->warpCount, 5); EXPECT_EQ(gate->warpCount, 2);
    EXPECT_EQ(gate->warps[1].warpId, 0); EXPECT_EQ(gate->warps[1].mapNum, MAP_NUM(MAP_OREBURGH_CITY));
    EXPECT_EQ(city->warps[0].warpId, 1); EXPECT_EQ(city->warps[0].mapNum, MAP_NUM(MAP_OREBURGH_GATE_1F));
    for (u32 i = 1; i < 5; i++)
    {
        EXPECT_EQ(city->warps[i].x, 49+i); EXPECT_EQ(city->warps[i].y, 57);
        EXPECT_EQ(city->warps[i].warpId, i < 3 ? 0 : 1);
    }
}

TEST("Averon DEV Oreburgh City and Route207 preserve reciprocal offsets")
{
    const struct MapConnections *city = HEADER(MAP_OREBURGH_CITY)->connections;
    const struct MapConnections *route = HEADER(MAP_ROUTE207)->connections;
    EXPECT_EQ(city->count, 1); EXPECT_EQ(route->count, 1);
    EXPECT_EQ(city->connections[0].direction, CONNECTION_NORTH);
    EXPECT_EQ(city->connections[0].offset, 35);
    EXPECT_EQ(route->connections[0].direction, CONNECTION_SOUTH);
    EXPECT_EQ(route->connections[0].offset, -35);
    EXPECT_EQ(city->connections[0].mapNum, MAP_NUM(MAP_ROUTE207));
    EXPECT_EQ(route->connections[0].mapNum, MAP_NUM(MAP_OREBURGH_CITY));
}

TEST("Averon DEV Oreburgh uses explicit temporary origins and no gameplay objects")
{
    static const u16 maps[] = {MAP_OREBURGH_CITY,MAP_ROUTE207,MAP_OREBURGH_MINE_B1F,MAP_OREBURGH_MINE_B2F};
    EXPECT_EQ(HEADER(MAP_OREBURGH_GATE_1F)->regionMapSectionId, MAPSEC_OREBURGH_GATE);
    for (u32 i = 0; i < ARRAY_COUNT(maps); i++)
    {
        const struct MapHeader *h = HEADER(maps[i]);
        EXPECT_EQ(h->regionMapSectionId, MAPSEC_ROUTE_201);
        EXPECT_EQ(h->events->objectEventCount, 0); EXPECT_EQ(h->events->coordEventCount, 0);
        EXPECT_EQ(h->events->bgEventCount, 0);
    }
}
