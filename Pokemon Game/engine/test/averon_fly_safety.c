#include "global.h"
#include "test/test.h"
#include "event_data.h"
#include "heal_location.h"
#include "malloc.h"
#include "overworld.h"
#include "region_map.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"

static const struct
{
    u16 section;
    u8 group, number;
    u16 heal;
} sLegacyFly[] = {
#define LEGACY_FLY(section, map, heal) {section, MAP_GROUP(map), MAP_NUM(map), heal},
#include "data/averon_legacy_fly_destinations.inc"
#undef LEGACY_FLY
};

TEST("Averon location Fly zero-filled gaps cannot replace a prepared warp with Petalburg")
{
    struct RegionMap *map = AllocZeroed(sizeof(*map));
    EXPECT(map != NULL);
    if (map == NULL)
        return;
    u32 checked = 0;
    // All 38 absent rows inside the CURRENT table; these two intentionally
    // resolve via FilterFlyDestination's existing special cases.
    for (u32 section = MAPSEC_UNDERWATER_124; section <= MAPSEC_DYNAMIC; section++)
    {
        if (section == MAPSEC_BATTLE_FRONTIER || section == MAPSEC_SOUTHERN_ISLAND)
            continue;
        map->mapSecId = section;
        SetWarpDestination(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18);
        EXPECT_EQ(FilterFlyDestination(map), (u32)WARP_ID_NONE);
        SetFlyDestination(map);
        WarpIntoMap();
        EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_SALTMERE));
        EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_SALTMERE));
        EXPECT_EQ(gSaveBlock1Ptr->pos.x, 18);
        EXPECT_EQ(gSaveBlock1Ptr->pos.y, 18);
        checked++;
    }
    EXPECT_EQ(checked, 36);
    Free(map);
}

TEST("Averon location Fly preserves all 154 explicit legacy destinations including Petalburg")
{
    struct RegionMap *map = AllocZeroed(sizeof(*map));
    EXPECT(map != NULL);
    if (map == NULL)
        return;
    gSaveBlock2Ptr->playerGender = MALE;
    FlagClear(FLAG_LANDMARK_POKEMON_LEAGUE);
    EXPECT_EQ(ARRAY_COUNT(sLegacyFly), 154);
    for (u32 i = 0; i < ARRAY_COUNT(sLegacyFly); i++)
    {
        map->mapSecId = sLegacyFly[i].section;
        map->posWithinMapSec = 0;
        SetWarpDestination(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18);
        EXPECT_EQ(FilterFlyDestination(map), sLegacyFly[i].heal == HEAL_LOCATION_NONE
            ? (u32)WARP_ID_NONE : sLegacyFly[i].heal);
        SetFlyDestination(map);
        WarpIntoMap();
        if (sLegacyFly[i].heal != HEAL_LOCATION_NONE)
        {
            const struct HealLocation *heal = GetHealLocation(sLegacyFly[i].heal);
            EXPECT(heal != NULL);
            if (heal == NULL)
                continue;
            EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, heal->mapGroup);
            EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, heal->mapNum);
            EXPECT_EQ(gSaveBlock1Ptr->pos.x, heal->x);
            EXPECT_EQ(gSaveBlock1Ptr->pos.y, heal->y);
        }
        else
        {
            EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, sLegacyFly[i].group);
            EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, sLegacyFly[i].number);
            EXPECT_EQ(gSaveBlock1Ptr->location.x, -1);
            EXPECT_EQ(gSaveBlock1Ptr->location.y, -1);
        }
        EXPECT_EQ(gSaveBlock1Ptr->location.warpId, WARP_ID_NONE);
    }
    Free(map);
}
