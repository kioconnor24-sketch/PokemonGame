#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "tilesets.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
// The production layout references this native symbol from assembly; it is
// intentionally not exported by the small public tilesets declaration list.
extern const struct Tileset gTileset_Cave;
STATIC_ASSERT(MAPSEC_NONE == 215, coronet_upper_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, coronet_upper_no_new_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, coronet_upper_box_preserved);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, coronet_upper_party_preserved);
TEST("Averon DEV Coronet ten-map upper maps preserve native cave assets and temporary-only identities")
{
    static const u16 maps[]={MAP_SINNOH_MT_CORONET_2F,MAP_SINNOH_MT_CORONET_3F,MAP_SINNOH_MT_CORONET_OUTSIDE_SOUTH,MAP_SINNOH_MT_CORONET_OUTSIDE_NORTH,MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2,MAP_SINNOH_MT_CORONET_4F_ROOM_3,MAP_SINNOH_MT_CORONET_5F,MAP_SINNOH_MT_CORONET_6F,MAP_SINNOH_MT_CORONET_1F_TUNNEL_ROOM};
    static const u8 counts[]={5,3,3,3,5,2,2,1,1};
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        EXPECT_EQ(MAP_NUM(maps[i]),19+i);
        EXPECT_EQ(h->regionMapSectionId,MAPSEC_ROUTE_201);
        EXPECT_EQ(h->events->warpCount,counts[i]);
        EXPECT_EQ(h->events->objectEventCount,0);
        EXPECT_EQ(h->events->coordEventCount,0);
        EXPECT_EQ(h->events->bgEventCount,0);
        EXPECT(h->mapLayout->primaryTileset==&gTileset_General);
        EXPECT(h->mapLayout->secondaryTileset==&gTileset_Cave);
        EXPECT((h->mapLayout->width+15)*(h->mapLayout->height+14)<=10240);
    }
    EXPECT_EQ(MAP_NUM(MAP_ROUTE205_NORTH),18);
}
TEST("Averon DEV Coronet ten-map upper all twenty-six stairs have reciprocal core-only destinations")
{
    static const u16 maps[]={MAP_SINNOH_MT_CORONET_2F,MAP_SINNOH_MT_CORONET_3F,MAP_SINNOH_MT_CORONET_OUTSIDE_SOUTH,MAP_SINNOH_MT_CORONET_OUTSIDE_NORTH,MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2,MAP_SINNOH_MT_CORONET_4F_ROOM_3,MAP_SINNOH_MT_CORONET_5F,MAP_SINNOH_MT_CORONET_6F,MAP_SINNOH_MT_CORONET_1F_TUNNEL_ROOM,MAP_MT_CORONET_1F_SOUTH};
    u32 total=0;
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        for (u32 j=0;j<h->events->warpCount;j++)
        {
            const struct WarpEvent *p=&h->events->warps[j];
            const struct MapHeader *other=Overworld_GetMapHeaderByGroupAndId(p->mapGroup,p->mapNum);
            EXPECT_EQ(p->mapGroup,MAP_GROUP(maps[0]));
            EXPECT(p->mapNum>=19 && p->mapNum<=28);
            EXPECT(p->warpId<other->events->warpCount);
            EXPECT_EQ(other->events->warps[p->warpId].mapNum,MAP_NUM(maps[i]));
            EXPECT_EQ(other->events->warps[p->warpId].warpId,j);
            total++;
        }
    }
    EXPECT_EQ(total,26);
}

TEST("Averon DEV Coronet essential same-floor stair preserves distinct reciprocal coordinates")
{
    const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_SINNOH_MT_CORONET_2F),MAP_NUM(MAP_SINNOH_MT_CORONET_2F));
    EXPECT_EQ(h->events->warps[0].mapNum,MAP_NUM(MAP_SINNOH_MT_CORONET_2F));
    EXPECT_EQ(h->events->warps[1].mapNum,MAP_NUM(MAP_SINNOH_MT_CORONET_2F));
    EXPECT_EQ(h->events->warps[0].x,7); EXPECT_EQ(h->events->warps[0].y,23);
    EXPECT_EQ(h->events->warps[1].x,7); EXPECT_EQ(h->events->warps[1].y,12);
    EXPECT_EQ(h->events->warps[0].warpId,1); EXPECT_EQ(h->events->warps[1].warpId,0);
}

TEST("Averon DEV Coronet fourth-floor same-map stairs preserve both separated room destinations")
{
    const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2),MAP_NUM(MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2));
    EXPECT_EQ(h->events->warps[2].mapNum,MAP_NUM(MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2));
    EXPECT_EQ(h->events->warps[3].mapNum,MAP_NUM(MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2));
    EXPECT_EQ(h->events->warps[2].x,17); EXPECT_EQ(h->events->warps[2].y,6);
    EXPECT_EQ(h->events->warps[3].x,59); EXPECT_EQ(h->events->warps[3].y,6);
    EXPECT_EQ(h->events->warps[2].warpId,3); EXPECT_EQ(h->events->warps[3].warpId,2);
}

TEST("Averon DEV Coronet new upper and lower anchors retain original compiled stair indices")
{
    const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_SINNOH_MT_CORONET_2F),MAP_NUM(MAP_SINNOH_MT_CORONET_2F));
    EXPECT_EQ(h->events->warpCount,5);
    EXPECT_EQ(h->mapLayout->map[48*34+27]&0xc00,0);
    h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_SINNOH_MT_CORONET_OUTSIDE_NORTH),MAP_NUM(MAP_SINNOH_MT_CORONET_OUTSIDE_NORTH));
    EXPECT_EQ(h->events->warps[2].mapNum,MAP_NUM(MAP_SINNOH_MT_CORONET_1F_TUNNEL_ROOM));
    EXPECT_EQ(h->events->warps[2].x,45); EXPECT_EQ(h->events->warps[2].y,28);
    h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_SINNOH_MT_CORONET_4F_ROOM_3),MAP_NUM(MAP_SINNOH_MT_CORONET_4F_ROOM_3));
    EXPECT_EQ(h->events->warps[1].mapNum,MAP_NUM(MAP_SINNOH_MT_CORONET_5F));
    h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_SINNOH_MT_CORONET_5F),MAP_NUM(MAP_SINNOH_MT_CORONET_5F));
    EXPECT_EQ(h->events->warps[1].mapNum,MAP_NUM(MAP_SINNOH_MT_CORONET_6F));
    h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_SINNOH_MT_CORONET_6F),MAP_NUM(MAP_SINNOH_MT_CORONET_6F));
    EXPECT(h->mapLayout->map[5*14+7]&0xc00);
}

TEST("Averon DEV Coronet reused South preserves isolated native banks and actual donor ladder")
{
    const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_MT_CORONET_1F_SOUTH),MAP_NUM(MAP_MT_CORONET_1F_SOUTH));
    EXPECT_EQ(MAP_NUM(MAP_MT_CORONET_1F_SOUTH),28);
    EXPECT_EQ(h->events->warpCount,1);
    EXPECT_EQ(h->events->warps[0].x,29); EXPECT_EQ(h->events->warps[0].y,2);
    EXPECT_EQ(h->events->warps[0].mapNum,MAP_NUM(MAP_SINNOH_MT_CORONET_2F));
    EXPECT_EQ(h->events->warps[0].warpId,4);
    EXPECT(h->mapLayout->primaryTileset==&gTileset_CoronetSouthPrimary);
    EXPECT(h->mapLayout->secondaryTileset==&gTileset_CoronetSouthSecondary);
    EXPECT_EQ(h->mapLayout->width,42); EXPECT_EQ(h->mapLayout->height,32);
    EXPECT(h->mapLayout->map[7*42+5]&0xc00);
    EXPECT(h->mapLayout->map[20*42+36]&0xc00);
    EXPECT_EQ(h->mapLayout->map[2*42+29]&0xfc00,0x3000);
    EXPECT_EQ(h->regionMapSectionId,MAPSEC_ROUTE_201);
}
