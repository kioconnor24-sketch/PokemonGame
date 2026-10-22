// Isolated DEV fixture: installed only in an exact marked disposable checkout.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"

STATIC_ASSERT(MAPSEC_NONE == 215, eterna_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, eterna_no_new_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, eterna_box_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, eterna_party_unchanged);

TEST("Averon DEV Eterna appends five compiled headers after all northern slots")
{
    static const u16 maps[] = {MAP_ETERNA_CITY,MAP_ROUTE206_NORTH,MAP_ROUTE206,MAP_ROUTE206_SOUTH,MAP_ROUTE211_WEST};
    static const u8 warps[] = {1,2,5,2,0};
    for (u32 i = 0; i < ARRAY_COUNT(maps); i++)
    {
        const struct MapHeader *h = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]), MAP_NUM(maps[i]));
        EXPECT_EQ(MAP_NUM(maps[i]), 19+i);
        EXPECT_EQ(h->regionMapSectionId, MAPSEC_ROUTE_201);
        EXPECT_EQ(h->events->warpCount, warps[i]);
        EXPECT_EQ(h->events->objectEventCount, 0);
        EXPECT_EQ(h->events->coordEventCount, 0);
        EXPECT_EQ(h->events->bgEventCount, 0);
    }
    EXPECT_EQ(MAP_NUM(MAP_ROUTE204), 13);
    EXPECT_EQ(MAP_NUM(MAP_ROUTE205_NORTH), 18);
}

TEST("Averon DEV Eterna streams City and both outdoor roads with one tileset family")
{
    const struct MapHeader *city = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ETERNA_CITY), MAP_NUM(MAP_ETERNA_CITY));
    static const u16 roads[] = {MAP_ROUTE206,MAP_ROUTE211_WEST};
    for (u32 i = 0; i < ARRAY_COUNT(roads); i++)
    {
        const struct MapHeader *road = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(roads[i]), MAP_NUM(roads[i]));
        EXPECT(road->mapLayout->primaryTileset == city->mapLayout->primaryTileset);
        EXPECT(road->mapLayout->secondaryTileset == city->mapLayout->secondaryTileset);
        EXPECT((road->mapLayout->width+15)*(road->mapLayout->height+14) <= 10240);
    }
}
