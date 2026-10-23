// Marked twelve-map eastern DEV fixture; no production origin allocation.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
STATIC_ASSERT(MAPSEC_NONE == 215, eastern_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, eastern_no_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, eastern_box_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, eastern_party_unchanged);
TEST("Averon DEV eastern appends thirteen compiled headers without allocating origins")
{
    static const u16 maps[] = {MAP_ROUTE212_ACCESS,MAP_ROUTE212_NORTH,MAP_ROUTE212_SOUTH,MAP_ROUTE213,MAP_ROUTE213_ACCESS,MAP_ROUTE214,MAP_ROUTE214_ACCESS,MAP_ROUTE215,MAP_ROUTE215_ACCESS,MAP_VALOR_LAKEFRONT,MAP_VEILSTONE_CITY,MAP_PASTORIA_CITY,MAP_HOTEL_GRAND_LAKE};
    static const u8 warps[] = {1,2,0,3,2,2,2,1,2,0,3,1,2};
    for (u32 i=0; i<ARRAY_COUNT(maps); i++)
    {
        const struct MapHeader *h = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        EXPECT_EQ(MAP_NUM(maps[i]),19+i);
        EXPECT_EQ(h->regionMapSectionId,MAPSEC_ROUTE_201);
        EXPECT_EQ(h->events->warpCount,warps[i]);
        EXPECT_EQ(h->events->objectEventCount,0);
        EXPECT_EQ(h->events->coordEventCount,0);
        EXPECT_EQ(h->events->bgEventCount,0);
        EXPECT((h->mapLayout->width+15)*(h->mapLayout->height+14)<=10240);
    }
    EXPECT_EQ(MAP_NUM(MAP_ROUTE205_NORTH),18);
    EXPECT_EQ(MAP_NUM(MAP_HOTEL_GRAND_LAKE),31);
}
TEST("Averon DEV eastern gateways and outdoors stream separate coherent families")
{
    const struct MapHeader *city=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_VEILSTONE_CITY),MAP_NUM(MAP_VEILSTONE_CITY));
    const struct MapHeader *coast=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE213),MAP_NUM(MAP_ROUTE213));
    const struct MapHeader *gate=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE213_ACCESS),MAP_NUM(MAP_ROUTE213_ACCESS));
    const struct MapHeader *other=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE215_ACCESS),MAP_NUM(MAP_ROUTE215_ACCESS));
    EXPECT(city->mapLayout->primaryTileset==coast->mapLayout->primaryTileset);
    EXPECT(city->mapLayout->secondaryTileset==coast->mapLayout->secondaryTileset);
    EXPECT(gate->mapLayout->secondaryTileset==other->mapLayout->secondaryTileset);
    EXPECT(gate->mapLayout->secondaryTileset!=city->mapLayout->secondaryTileset);
}
