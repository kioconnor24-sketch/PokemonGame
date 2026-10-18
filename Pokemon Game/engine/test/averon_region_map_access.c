#include "global.h"
#include "test/test.h"
#include "follower_npc.h"
#include "fieldmap.h"
#include "main.h"
#include "overworld.h"
#include "pokenav.h"
#include "region_map.h"
#include "regions.h"
#include "party_menu.h"
#include "constants/map_types.h"
#include "constants/region_map_sections.h"

TEST("Averon region map access refuses Fly from Sinnoh without an approved grid")
{
    ClearFollowerNPCData();
    gMapHeader.mapType = MAP_TYPE_TOWN;
    gMapHeader.regionMapSectionId = MAPSEC_SANDGEM_TOWN;
    EXPECT_EQ(SetUpFieldMove_Fly(), FALSE);
}

TEST("Averon region map access retains every legacy section and rejects explicit Sinnoh")
{
    for (u32 section = 0; section < MAPSEC_NONE; ++section)
        EXPECT(IsRegionMapAvailableForSection(section));
    EXPECT_EQ(GetRegionForSectionId(MAPSEC_SANDGEM_TOWN), REGION_SINNOH);
    EXPECT_EQ(IsRegionMapAvailableForSection(MAPSEC_SANDGEM_TOWN), FALSE);
}

TEST("Averon region map access preserves legacy Fly map type restrictions")
{
    u32 section = MAPSEC_PETALBURG_CITY;
    PARAMETRIZE { section = MAPSEC_PETALBURG_CITY; }
    PARAMETRIZE { section = MAPSEC_SALTMERE; }
    PARAMETRIZE { section = MAPSEC_PALLET_TOWN; }
    PARAMETRIZE { section = MAPSEC_ONE_ISLAND; }
    ClearFollowerNPCData();
    gMapHeader.regionMapSectionId = section;
    for (u32 type = MAP_TYPE_NONE; type <= MAP_TYPE_SECRET_BASE; ++type)
    {
        gMapHeader.mapType = type;
        EXPECT_EQ(SetUpFieldMove_Fly(), Overworld_MapTypeAllowsTeleportAndFly(type));
    }
}

static void ReturnFromMap(void) {}

TEST("Averon region map access wall map returns without replacing VBlank or allocating")
{
    MainCallback previous = gMain.callback2;
    IntrCallback vblank = gMain.vblankCallback;
    MainCallback actual;
    gMapHeader.regionMapSectionId = MAPSEC_SANDGEM_TOWN;
    FieldInitRegionMap(ReturnFromMap);
    actual = gMain.callback2;
    SetMainCallback2(previous); // restore runner before assertions
    EXPECT(actual == ReturnFromMap);
    EXPECT(gMain.vblankCallback == vblank);
}

TEST("Averon region map access PokeNav refuses before changing or freeing the main menu")
{
    bool32 unchanged = FALSE;
    gMapHeader.regionMapSectionId = MAPSEC_SANDGEM_TOWN;
    EXPECT_EQ(TestPokenavMainMenuMapInput(&unchanged), POKENAV_MENU_FUNC_NONE);
    EXPECT(unchanged);
}

TEST("Averon region map access PokeNav still schedules the legacy map feature")
{
    u32 section = MAPSEC_SALTMERE;
    bool32 unchanged = TRUE;
    PARAMETRIZE { section = MAPSEC_SALTMERE; }
    PARAMETRIZE { section = MAPSEC_PALLET_TOWN; }
    gMapHeader.regionMapSectionId = section;
    EXPECT_EQ(TestPokenavMainMenuMapInput(&unchanged), POKENAV_MENU_FUNC_OPEN_FEATURE);
    EXPECT(!unchanged);
}
