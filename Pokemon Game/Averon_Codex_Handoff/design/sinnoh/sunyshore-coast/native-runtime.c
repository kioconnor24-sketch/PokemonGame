// Temporary appended map fixture only, never production origins.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "tilesets.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
STATIC_ASSERT(MAPSEC_NONE == 215, coast_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, coast_no_new_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, coast_box_preserved);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, coast_party_preserved);
TEST("Averon DEV Sunyshore appends five maps preserving origins and original graphics")
{
    static const u16 maps[]={MAP_SUNYSHORE_CITY,MAP_ROUTE222,MAP_ROUTE223,MAP_POKMON_LEAGUE,MAP_ROUTE222_ACCESS};
    static const u8 warps[]={1,1,0,0,2};
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        EXPECT_EQ(MAP_NUM(maps[i]),19+i);
        EXPECT_EQ(h->regionMapSectionId,MAPSEC_ROUTE_201);
        EXPECT_EQ(h->events->warpCount,warps[i]);
        EXPECT_EQ(h->events->objectEventCount,0);
        EXPECT_EQ(h->events->coordEventCount,0);
        EXPECT_EQ(h->events->bgEventCount,0);
        EXPECT(h->mapLayout->primaryTileset==(i==4?&gTileset_Building:&gTileset_General));
        EXPECT((h->mapLayout->width+15)*(h->mapLayout->height+14)<=10240);
    }
    EXPECT_EQ(MAP_NUM(MAP_ROUTE205_NORTH),18);
}
TEST("Averon DEV Sunyshore gateway preserves both reciprocal source warp pairs")
{
    const struct MapHeader *gate=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE222_ACCESS),MAP_NUM(MAP_ROUTE222_ACCESS));
    static const u16 maps[]={MAP_ROUTE222,MAP_SUNYSHORE_CITY};
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *outside=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        EXPECT_EQ(gate->events->warps[i].mapNum,MAP_NUM(maps[i]));
        EXPECT_EQ(gate->events->warps[i].warpId,0);
        EXPECT_EQ(outside->events->warps[0].mapNum,MAP_NUM(MAP_ROUTE222_ACCESS));
        EXPECT_EQ(outside->events->warps[0].warpId,i);
    }
}
