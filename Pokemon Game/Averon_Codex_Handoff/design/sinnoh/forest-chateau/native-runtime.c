// Exact-base marked DEV checkout only; never a production origin allocation.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"

STATIC_ASSERT(MAPSEC_NONE == 215, forest_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, forest_no_new_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, forest_box_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, forest_party_unchanged);

TEST("Averon DEV Forest appends six compiled headers after all northern slots")
{
    static const u16 maps[] = {MAP_ETERNA_FOREST,MAP_OLD_CHATEAU_ENTRANCE,MAP_OLD_CHATEAU_DINING_ROOM,
        MAP_OLD_CHATEAU_2F,MAP_OLD_CHATEAU_SIDE_ROOM_1,MAP_OLD_CHATEAU_SIDE_ROOM_2};
    static const u8 warps[] = {1,7,2,17,2,2};
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

TEST("Averon DEV Chateau retains fifteen same-map room warps and shared interior primary")
{
    const struct MapHeader *floor = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_OLD_CHATEAU_2F), MAP_NUM(MAP_OLD_CHATEAU_2F));
    const struct MapHeader *entrance = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_OLD_CHATEAU_ENTRANCE), MAP_NUM(MAP_OLD_CHATEAU_ENTRANCE));
    u32 internal = 0;
    for (u32 i = 0; i < floor->events->warpCount; i++)
    {
        const struct WarpEvent *w = &floor->events->warps[i];
        if (w->mapGroup == MAP_GROUP(MAP_OLD_CHATEAU_2F) && w->mapNum == MAP_NUM(MAP_OLD_CHATEAU_2F))
        {
            internal++;
            EXPECT(w->warpId < floor->events->warpCount);
        }
    }
    EXPECT_EQ(internal, 15);
    EXPECT(floor->mapLayout->primaryTileset == entrance->mapLayout->primaryTileset);
    EXPECT(floor->mapLayout->secondaryTileset != entrance->mapLayout->secondaryTileset);
}
