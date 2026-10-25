#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "tilesets.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
extern const struct Tileset gTileset_Cave;
STATIC_ASSERT(MAPSEC_NONE==215, temple_none_stable);
STATIC_ASSERT(MAPSEC_COUNT==227, temple_no_new_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon)==80, temple_box_stable);
STATIC_ASSERT(sizeof(struct Pokemon)==100, temple_party_stable);
static const u16 sTemple[]={MAP_SINNOH_SNOWPOINT_TEMPLE_1F,MAP_SINNOH_SNOWPOINT_TEMPLE_B1F,MAP_SINNOH_SNOWPOINT_TEMPLE_B2F,MAP_SINNOH_SNOWPOINT_TEMPLE_B3F,MAP_SINNOH_SNOWPOINT_TEMPLE_B4F,MAP_SINNOH_SNOWPOINT_TEMPLE_B5F};
TEST("Averon DEV source-height Temple preserves original registry prefix and native assets")
{
    for(u32 i=0;i<ARRAY_COUNT(sTemple);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(sTemple[i]),MAP_NUM(sTemple[i]));
        EXPECT_EQ(MAP_NUM(sTemple[i]),19+i);EXPECT_EQ(h->mapLayout->width,32);EXPECT_EQ(h->mapLayout->height,32);
        EXPECT(h->mapLayout->primaryTileset==&gTileset_General);EXPECT(h->mapLayout->secondaryTileset==&gTileset_Cave);
        EXPECT_EQ(h->regionMapSectionId,MAPSEC_ROUTE_201);EXPECT_EQ(h->events->objectEventCount,0);EXPECT_EQ(h->events->coordEventCount,0);EXPECT_EQ(h->events->bgEventCount,0);
    }
    EXPECT_EQ(MAP_NUM(MAP_ROUTE205_NORTH),18);
}
TEST("Averon DEV source-height Temple ten compiled stairs preserve exact reciprocal indices")
{
    u32 count=0;
    for(u32 i=0;i<ARRAY_COUNT(sTemple);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(sTemple[i]),MAP_NUM(sTemple[i]));
        for(u32 j=0;j<h->events->warpCount;j++)
        {
            const struct WarpEvent *p=&h->events->warps[j];
            EXPECT_EQ(p->mapGroup,MAP_GROUP(sTemple[0]));EXPECT(p->mapNum>=19&&p->mapNum<=24);
            const struct MapHeader *other=Overworld_GetMapHeaderByGroupAndId(p->mapGroup,p->mapNum);
            EXPECT(p->warpId<other->events->warpCount);EXPECT_EQ(other->events->warps[p->warpId].mapNum,MAP_NUM(sTemple[i]));EXPECT_EQ(other->events->warps[p->warpId].warpId,j);count++;
        }
    }
    EXPECT_EQ(count,10);
}
TEST("Averon DEV source-height Temple keeps city entrance closed and has no story gate")
{
    const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(sTemple[0]),MAP_NUM(sTemple[0]));
    EXPECT(h->mapLayout->map[13*32+8]&0xc00);EXPECT_EQ(h->events->warpCount,1);
    EXPECT_EQ(h->events->warps[0].x,14);EXPECT_EQ(h->events->warps[0].y,3);
}

TEST("Averon DEV source-height Temple compiled ice and walkable totals match verified surfaces")
{
    u32 ice=0,walkable=0;
    for(u32 i=0;i<ARRAY_COUNT(sTemple);i++)
    {
        const struct MapLayout *l=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(sTemple[i]),MAP_NUM(sTemple[i]))->mapLayout;
        for(u32 j=0;j<32*32;j++)
        {
            u16 cell=l->map[j],tile=cell&1023;
            u16 attr=tile<512?l->primaryTileset->metatileAttributes[tile]:l->secondaryTileset->metatileAttributes[tile-512];
            if((attr&511)==0x20) { ice++; EXPECT_EQ(cell&0xc00,0); }
            if(!(cell&0xc00)) { walkable++; EXPECT_EQ(cell>>12,3); }
        }
    }
    EXPECT_EQ(ice,338);EXPECT_EQ(walkable,886);
}
