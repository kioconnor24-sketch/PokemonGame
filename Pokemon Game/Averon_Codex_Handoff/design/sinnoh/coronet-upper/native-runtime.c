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
TEST("Averon DEV Coronet upper floors preserve native cave assets and temporary-only identities")
{
    static const u16 maps[]={MAP_SINNOH_MT_CORONET_2F,MAP_SINNOH_MT_CORONET_3F};
    static const u8 counts[]={4,2};
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
TEST("Averon DEV Victory all six stairs have reciprocal core-only destinations")
{
    static const u16 maps[]={MAP_SINNOH_MT_CORONET_2F,MAP_SINNOH_MT_CORONET_3F};
    u32 total=0;
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        for (u32 j=0;j<h->events->warpCount;j++)
        {
            const struct WarpEvent *p=&h->events->warps[j];
            const struct MapHeader *other=Overworld_GetMapHeaderByGroupAndId(p->mapGroup,p->mapNum);
            EXPECT_EQ(p->mapGroup,MAP_GROUP(maps[0]));
            EXPECT(p->mapNum>=19 && p->mapNum<=20);
            EXPECT(p->warpId<other->events->warpCount);
            EXPECT_EQ(other->events->warps[p->warpId].mapNum,MAP_NUM(maps[i]));
            EXPECT_EQ(other->events->warps[p->warpId].warpId,j);
            total++;
        }
    }
    EXPECT_EQ(total,6);
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
