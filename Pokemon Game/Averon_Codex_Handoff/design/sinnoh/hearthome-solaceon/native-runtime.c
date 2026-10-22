// Exact-base marked DEV checkout only; never production saved-origin policy.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"

STATIC_ASSERT(MAPSEC_NONE == 215, central_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, central_no_new_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, central_box_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, central_party_unchanged);

TEST("Averon DEV central appends seven compiled headers after all northern slots")
{
    static const u16 maps[] = {MAP_HEARTHOME_CITY,MAP_ROUTE208,MAP_ROUTE208_ACCESS,MAP_ROUTE209,
        MAP_SOLACEON_TOWN,MAP_ROUTE210_SOUTH,MAP_ROUTE209_ACCESS};
    static const u8 warps[] = {2,1,2,1,0,0,2};
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

TEST("Averon DEV central streams all five outdoors using one exact tileset family")
{
    const struct MapHeader *city = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_HEARTHOME_CITY), MAP_NUM(MAP_HEARTHOME_CITY));
    static const u16 maps[] = {MAP_ROUTE208,MAP_ROUTE209,MAP_SOLACEON_TOWN,MAP_ROUTE210_SOUTH};
    for (u32 i = 0; i < ARRAY_COUNT(maps); i++)
    {
        const struct MapHeader *h = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]), MAP_NUM(maps[i]));
        EXPECT(h->mapLayout->primaryTileset == city->mapLayout->primaryTileset);
        EXPECT(h->mapLayout->secondaryTileset == city->mapLayout->secondaryTileset);
        EXPECT((h->mapLayout->width+15)*(h->mapLayout->height+14) <= 10240);
    }
}
