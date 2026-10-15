#include "global.h"
#include "test/test.h"
#include "event_data.h"
#include "heal_location.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"

TEST("Averon whiteout selects the local home or Alderfield clinic healer")
{
    u32 location=HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F;
    PARAMETRIZE { location=HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F; }
    PARAMETRIZE { location=HEAL_LOCATION_ALDERFIELD; }
    const struct HealLocation *heal=GetHealLocation(location);
    struct WarpData respawn={0};
    EXPECT(heal != NULL);
    gSaveBlock1Ptr->lastHealLocation.mapGroup=heal->mapGroup;
    gSaveBlock1Ptr->lastHealLocation.mapNum=heal->mapNum;
    gSaveBlock1Ptr->lastHealLocation.warpId=WARP_ID_NONE;
    gSaveBlock1Ptr->lastHealLocation.x=heal->x;
    gSaveBlock1Ptr->lastHealLocation.y=heal->y;
    SetWhiteoutRespawnWarpAndHealerNPC(&respawn);
    EXPECT_EQ(GetHealNpcLocalId(location), 1);
    EXPECT_EQ(gSpecialVar_LastTalked, 1);
    EXPECT_EQ(gSpecialVar_0x800B, 1);
    EXPECT_EQ(respawn.warpId, WARP_ID_NONE);
    if (location==HEAL_LOCATION_ALDERFIELD)
    {
        EXPECT_EQ(respawn.mapGroup, MAP_GROUP(MAP_ALDERFIELDCLINIC));
        EXPECT_EQ(respawn.mapNum, MAP_NUM(MAP_ALDERFIELDCLINIC));
        EXPECT_EQ(respawn.x, 7);
        EXPECT_EQ(respawn.y, 4);
        EXPECT_EQ(IsLastHealLocationPlayerHouse(), FALSE);
    }
    else
    {
        EXPECT_EQ(respawn.mapGroup, MAP_GROUP(MAP_SALTMEREHOME));
        EXPECT_EQ(respawn.mapNum, MAP_NUM(MAP_SALTMEREHOME));
        EXPECT_EQ(respawn.x, 6);
        EXPECT_EQ(respawn.y, 5);
        EXPECT_EQ(IsLastHealLocationPlayerHouse(), TRUE);
    }
}
