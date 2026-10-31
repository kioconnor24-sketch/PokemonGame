#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
STATIC_ASSERT(MAPSEC_ROUTE_206 == 228, packet_d_route206_fixed);
STATIC_ASSERT(MAPSEC_ROUTE_207 == 229, packet_d_route207_fixed);
STATIC_ASSERT(MAPSEC_MT_CORONET == 230, packet_d_coronet_fixed);
STATIC_ASSERT(MAPSEC_COUNT == 239, packet_d_only_approved_origins);
TEST("Averon packet D production map slots and section meanings are append only")
{
    const u32 maps[] = {MAP_ROUTE206_NORTH,MAP_ROUTE206,MAP_ROUTE206_SOUTH,MAP_ROUTE207,MAP_MT_CORONET_1F_SOUTH};
    const u32 sections[] = {228,228,228,229,230};
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        EXPECT_EQ(MAP_GROUP(maps[i]),76); EXPECT_EQ(MAP_NUM(maps[i]),41+i);
        EXPECT_EQ(h->regionMapSectionId,sections[i]);
    }
}
TEST("Averon packet D retains west Coronet return and closes unbuilt north east and upper ports")
{
    const struct MapHeader *s=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_MT_CORONET_1F_SOUTH),MAP_NUM(MAP_MT_CORONET_1F_SOUTH));
    const struct MapHeader *n=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE206_NORTH),MAP_NUM(MAP_ROUTE206_NORTH));
    EXPECT_EQ(s->events->warpCount,1); EXPECT_EQ(s->events->warps[0].mapNum,MAP_NUM(MAP_ROUTE207));
    EXPECT_EQ(s->events->warps[0].warpId,0); EXPECT_EQ(s->mapLayout->map[299],0x321a);
    EXPECT_EQ(s->mapLayout->map[876],0x3604); EXPECT_EQ(s->mapLayout->map[113],0x3604);
    EXPECT_EQ(n->events->warpCount,1); EXPECT_EQ(n->mapLayout->map[13],0x3721);
}
