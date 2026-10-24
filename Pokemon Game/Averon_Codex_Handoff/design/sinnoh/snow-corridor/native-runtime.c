// Exact-base marked DEV only; no permanent origin or production map allocation.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "tilesets.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
#include "constants/weather.h"

STATIC_ASSERT(MAPSEC_NONE == 215, snow_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, snow_no_new_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, snow_box_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, snow_party_unchanged);

TEST("Averon DEV snow headers append four exact slots with original weather and no events")
{
    static const u16 maps[] = {MAP_ROUTE216,MAP_ROUTE217,MAP_ACUITY_LAKEFRONT,MAP_SNOWPOINT_CITY};
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        EXPECT_EQ(MAP_NUM(maps[i]),19+i);
        EXPECT_EQ(h->regionMapSectionId,MAPSEC_ROUTE_201);
        EXPECT_EQ(h->weather,WEATHER_SNOW);
        EXPECT_EQ(h->events->warpCount,0);
        EXPECT_EQ(h->events->objectEventCount,0);
        EXPECT_EQ(h->events->coordEventCount,0);
        EXPECT_EQ(h->events->bgEventCount,0);
    }
    EXPECT_EQ(MAP_NUM(MAP_ROUTE204),13);
    EXPECT_EQ(MAP_NUM(MAP_ROUTE205_NORTH),18);
}

TEST("Averon DEV snow uses native General pointer and retains 24 upper bridge cells")
{
    const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE216),MAP_NUM(MAP_ROUTE216));
    const struct MapLayout *layout=h->mapLayout;
    u32 upper=0;
    EXPECT(layout->primaryTileset == &gTileset_General);
    EXPECT_EQ(layout->width,96);
    EXPECT_EQ(layout->height,40);
    for (u32 i=0;i<layout->width*layout->height;i++)
        if ((layout->map[i] >> 12) == 15) upper++;
    EXPECT_EQ(upper,24);
}
