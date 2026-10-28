#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "constants/maps.h"
TEST("Averon DEV Route222 safety cliff prevents jumps into preserved boulders")
{
    const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE222),MAP_NUM(MAP_ROUTE222));
    const struct MapLayout *l=h->mapLayout;
    EXPECT_EQ(l->width,92); EXPECT_EQ(l->height,32);
    for (u32 x=36;x<=37;x++)
    {
        EXPECT_EQ(l->map[16*92+x],0x491);
        EXPECT_EQ(l->map[17*92+x],0x4e1);
        EXPECT(l->map[18*92+x]&0xc00);
    }
    EXPECT_EQ(l->primaryTileset->metatileAttributes[145]&511,0);
    EXPECT_EQ(l->primaryTileset->metatileAttributes[135]&511,0x3b);
    EXPECT_EQ(l->map[16*92+35],0x487); EXPECT_EQ(l->map[16*92+38],0x487);
    EXPECT_EQ(l->map[17*92+35]&0xc00,0); EXPECT_EQ(l->map[17*92+38]&0xc00,0);
}
