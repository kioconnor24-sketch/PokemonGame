// Isolated four-floor DEV fixture; not production registration or saved origins.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "tilesets.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
STATIC_ASSERT(MAPSEC_NONE == 215, room_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 227, room_no_new_origins);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, room_box_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, room_party_unchanged);
static const u16 sRoomMaps[] = {MAP_TWINLEAF_TOWN_MAIN_HOUSE_1F, MAP_TWINLEAF_TOWN_MAIN_HOUSE_2F,
    MAP_TWINLEAF_TOWN_RIVALS_HOUSE_F1, MAP_TWINLEAF_TOWN_RIVALS_HOUSE_F2};
TEST("Averon DEV room headers append four slots without new saved identities")
{
    for (u32 i=0; i<ARRAY_COUNT(sRoomMaps); i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(sRoomMaps[i]),MAP_NUM(sRoomMaps[i]));
        EXPECT_EQ(MAP_NUM(sRoomMaps[i]),19+i);
        EXPECT_EQ(h->regionMapSectionId,MAPSEC_ROUTE_201);
        EXPECT_EQ(h->events->warpCount,1);
        EXPECT_EQ(h->events->objectEventCount,0);
        EXPECT_EQ(h->events->coordEventCount,0);
        EXPECT_EQ(h->events->bgEventCount,0);
        EXPECT(h->mapLayout->primaryTileset==&gTileset_Building);
        EXPECT((h->mapLayout->width+15)*(h->mapLayout->height+14)<=10240);
    }
    EXPECT_EQ(MAP_NUM(MAP_ROUTE205_NORTH),18);
}
TEST("Averon DEV room stairs retain exact reciprocal compiled floor pairs")
{
    for (u32 i=0; i<ARRAY_COUNT(sRoomMaps); i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(sRoomMaps[i]),MAP_NUM(sRoomMaps[i]));
        const struct WarpEvent *w=&h->events->warps[0];
        EXPECT_EQ(w->mapGroup,MAP_GROUP(sRoomMaps[i^1]));
        EXPECT_EQ(w->mapNum,MAP_NUM(sRoomMaps[i^1]));
        EXPECT_EQ(w->warpId,0);
        EXPECT(w->x>=0 && w->x<h->mapLayout->width);
        EXPECT(w->y>=0 && w->y<h->mapLayout->height);
    }
}
