// Four-map disposable source fixture; saved-origin policy remains unchanged.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "tilesets.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
STATIC_ASSERT(MAPSEC_NONE == 215, canalave_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, canalave_no_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, canalave_box_preserved);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, canalave_party_preserved);
TEST("Averon DEV Canalave appends four maps with original graphics bindings and no new origins")
{
    static const u16 maps[]={MAP_ROUTE218_EAST,MAP_ROUTE218,MAP_ROUTE218_WEST,MAP_CANALAVE_CITY};
    static const u8 warps[]={1,2,2,1};
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        EXPECT_EQ(MAP_NUM(maps[i]),19+i);
        EXPECT_EQ(h->regionMapSectionId,MAPSEC_ROUTE_201);
        EXPECT_EQ(h->events->warpCount,warps[i]);
        EXPECT_EQ(h->events->objectEventCount,0);
        EXPECT_EQ(h->events->coordEventCount,0);
        EXPECT_EQ(h->events->bgEventCount,0);
        EXPECT(h->mapLayout->primaryTileset==((i==0||i==2)?&gTileset_Building:&gTileset_General));
        EXPECT((h->mapLayout->width+15)*(h->mapLayout->height+14)<=10240);
    }
    EXPECT_EQ(MAP_NUM(MAP_ROUTE205_NORTH),18);
}
TEST("Averon DEV Canalave retains the exact paired east gate source correction")
{
    const struct MapHeader *east=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE218_EAST),MAP_NUM(MAP_ROUTE218_EAST));
    const struct MapHeader *route=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE218),MAP_NUM(MAP_ROUTE218));
    const struct WarpEvent *out=&east->events->warps[0],*back=&route->events->warps[0];
    EXPECT_EQ(out->mapGroup,MAP_GROUP(MAP_ROUTE218));
    EXPECT_EQ(out->mapNum,MAP_NUM(MAP_ROUTE218));
    EXPECT_EQ(out->warpId,0);
    EXPECT_EQ(back->mapGroup,MAP_GROUP(MAP_ROUTE218_EAST));
    EXPECT_EQ(back->mapNum,MAP_NUM(MAP_ROUTE218_EAST));
    EXPECT_EQ(back->warpId,0);
}
