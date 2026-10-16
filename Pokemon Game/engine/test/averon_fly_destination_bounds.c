#include "global.h"
#include "test/test.h"
#include "malloc.h"
#include "region_map.h"
#include "overworld.h"
#include "heal_location.h"
#include "event_data.h"
#include "money.h"
#include "item.h"
#include "pokemon.h"
#include "constants/maps.h"
#include "constants/heal_locations.h"
#include "constants/region_map_sections.h"

static struct RegionMap *NewFlyBoundsMap(u16 section)
{
    // RegionMap is too large for the native runner's IWRAM stack.
    struct RegionMap *map = AllocZeroed(sizeof(*map));
    EXPECT(map != NULL);
    map->mapSecId = section;
    return map;
}

static void ExpectFlyBoundsHeal(struct RegionMap *map, u32 expected)
{
    const struct HealLocation *heal = GetHealLocation(expected);
    EXPECT(heal != NULL);
    EXPECT_EQ(FilterFlyDestination(map), expected);
    SetFlyDestination(map);
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, heal->mapGroup);
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, heal->mapNum);
    EXPECT_EQ(gSaveBlock1Ptr->location.warpId, WARP_ID_NONE);
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, heal->x);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, heal->y);
}

TEST("Averon Fly bounds preserves both home genders and mapped legacy healing")
{
    u32 gender = MALE, section = MAPSEC_LITTLEROOT_TOWN;
    PARAMETRIZE { gender = MALE; section = MAPSEC_LITTLEROOT_TOWN; }
    PARAMETRIZE { gender = FEMALE; section = MAPSEC_LITTLEROOT_TOWN; }
    PARAMETRIZE { gender = MALE; section = MAPSEC_OLDALE_TOWN; }
    struct RegionMap *map = NewFlyBoundsMap(section);
    gSaveBlock2Ptr->playerGender = gender;
    ExpectFlyBoundsHeal(map, section == MAPSEC_OLDALE_TOWN ? HEAL_LOCATION_OLDALE_TOWN
        : gender == MALE ? HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F
        : HEAL_LOCATION_LITTLEROOT_TOWN_MAYS_HOUSE_2F);
    Free(map);
}

TEST("Averon Fly bounds retains explicit island and Frontier destinations")
{
    u32 section = MAPSEC_SOUTHERN_ISLAND;
    PARAMETRIZE { section = MAPSEC_SOUTHERN_ISLAND; }
    PARAMETRIZE { section = MAPSEC_BATTLE_FRONTIER; }
    struct RegionMap *map = NewFlyBoundsMap(section);
    ExpectFlyBoundsHeal(map, section == MAPSEC_SOUTHERN_ISLAND
        ? HEAL_LOCATION_SOUTHERN_ISLAND_EXTERIOR : HEAL_LOCATION_BATTLE_FRONTIER_OUTSIDE_EAST);
    Free(map);
}

TEST("Averon Fly bounds preserves League flag and position selection")
{
    u32 flag = FALSE, position = 0;
    PARAMETRIZE { flag = FALSE; position = 0; }
    PARAMETRIZE { flag = FALSE; position = 1; }
    PARAMETRIZE { flag = TRUE; position = 0; }
    PARAMETRIZE { flag = TRUE; position = 1; }
    struct RegionMap *map = NewFlyBoundsMap(MAPSEC_EVER_GRANDE_CITY);
    map->posWithinMapSec = position;
    if (flag)
        FlagSet(FLAG_LANDMARK_POKEMON_LEAGUE);
    else
        FlagClear(FLAG_LANDMARK_POKEMON_LEAGUE);
    ExpectFlyBoundsHeal(map, flag && position == 0 ? HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE
        : HEAL_LOCATION_EVER_GRANDE_CITY);
    EXPECT_EQ(FlagGet(FLAG_LANDMARK_POKEMON_LEAGUE), flag);
    Free(map);
}

TEST("Averon Fly bounds preserves route and last-table-row map-warp fallback")
{
    u32 section = MAPSEC_ROUTE_101;
    PARAMETRIZE { section = MAPSEC_ROUTE_101; }
    PARAMETRIZE { section = MAPSEC_EMBER_SPA; }
    struct RegionMap *map = NewFlyBoundsMap(section);
    u32 expectedMap = section == MAPSEC_ROUTE_101 ? MAP_ROUTE101 : MAP_PALLET_TOWN;
    EXPECT_EQ(FilterFlyDestination(map), (u32)WARP_ID_NONE);
    SetFlyDestination(map);
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(expectedMap));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(expectedMap));
    EXPECT_EQ(gSaveBlock1Ptr->location.warpId, WARP_ID_NONE);
    EXPECT_EQ(gSaveBlock1Ptr->location.x, -1);
    EXPECT_EQ(gSaveBlock1Ptr->location.y, -1);
    Free(map);
}

TEST("Averon Fly bounds rejects invalid sections without replacing prepared warp or progress")
{
    u32 section = MAPSEC_EMBER_SPA + 1;
    PARAMETRIZE { section = MAPSEC_EMBER_SPA + 1; }
    PARAMETRIZE { section = MAPSEC_SALTMERE; }
    PARAMETRIZE { section = MAPSEC_ALDERFIELD; }
    PARAMETRIZE { section = 65535; }
    struct RegionMap *map = NewFlyBoundsMap(section);
    struct Pokemon *party = Alloc(sizeof(gParties[B_TRAINER_PLAYER]));
    EXPECT(party != NULL);
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0);
    CalculatePlayerPartyCount();
    memcpy(party, gParties[B_TRAINER_PLAYER], sizeof(gParties[B_TRAINER_PLAYER]));
    ClearBag();
    EXPECT(AddBagItem(ITEM_GREAT_BALL, 4));
    SetMoney(&gSaveBlock1Ptr->money, 9876);
    for (u32 i = 0; i < 8; ++i)
    {
        if (0xA5 & (1 << i))
            FlagSet(FLAG_BADGE01_GET + i);
        else
            FlagClear(FLAG_BADGE01_GET + i);
    }
    FlagSet(FLAG_AVERON_LICENSE_FLY);
    SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
    struct WarpData heal = gSaveBlock1Ptr->lastHealLocation;
    SetWarpDestination(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18);
    EXPECT_EQ(FilterFlyDestination(map), (u32)WARP_ID_NONE);
    SetFlyDestination(map);
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_SALTMERE));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(gSaveBlock1Ptr->location.warpId, WARP_ID_NONE);
    EXPECT_EQ(gSaveBlock1Ptr->location.x, 18);
    EXPECT_EQ(gSaveBlock1Ptr->location.y, 18);
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, 18);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, 18);
    EXPECT_EQ(memcmp(&heal, &gSaveBlock1Ptr->lastHealLocation, sizeof(heal)), 0);
    EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), 9876);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_GREAT_BALL), 4);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], 1);
    EXPECT_EQ(memcmp(party, gParties[B_TRAINER_PLAYER], sizeof(gParties[B_TRAINER_PLAYER])), 0);
    for (u32 i = 0; i < 8; ++i)
        EXPECT_EQ(FlagGet(FLAG_BADGE01_GET + i), (0xA5 & (1 << i)) != 0);
    EXPECT_EQ(FlagGet(FLAG_AVERON_LICENSE_FLY), TRUE);
    Free(party);
    Free(map);
}
