#include "global.h"
#include "test/test.h"
#include "pokemon.h"
#include "pokemon_summary_screen.h"
#include "region_map.h"
#include "map_name_popup.h"
#include "regions.h"
#include "string_util.h"

// Owner approval: Issue #15 comment 6258911084 (Route 201, section 217).
STATIC_ASSERT(MAPSEC_ROUTE_201 == 217, route201_section_value);

static bool32 Contains(const u8 *text, const u8 *needle)
{
    u32 length = StringLength(text), n = StringLength(needle);
    for (u32 i = 0; i + n <= length; i++)
        if (memcmp(text + i, needle, n) == 0)
            return TRUE;
    return FALSE;
}

TEST("Averon Route 201 is section 217 in Sinnoh with its own name and popup")
{
    u8 text[64];
    GetMapName(text, MAPSEC_ROUTE_201, 0);
    EXPECT_EQ(StringCompare(text, COMPOUND_STRING("ROUTE 201")), 0);
    struct MapHeader map = {.regionMapSectionId = MAPSEC_ROUTE_201};
    GetPopUpMapName(text, &map);
    EXPECT_EQ(StringCompare(text, COMPOUND_STRING("ROUTE 201")), 0);
    EXPECT_EQ(GetRegionForSectionId(MAPSEC_ROUTE_201), REGION_SINNOH);
    EXPECT(IsRegionMapSectionIdValid(MAPSEC_ROUTE_201));
    // Hoenn's own Route 101 keeps its legacy identity and region.
    GetMapName(text, MAPSEC_ROUTE_101, 0);
    EXPECT_EQ(StringCompare(text, COMPOUND_STRING("ROUTE 101")), 0);
    EXPECT_EQ(GetRegionForSectionId(MAPSEC_ROUTE_101), REGION_HOENN);
}

TEST("Averon Route 201 origin survives the real summary formatter unchanged")
{
    struct Pokemon mon;
    StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CLAUDE"));
    gSaveBlock2Ptr->playerGender = MALE;
    CreateMon(&mon, SPECIES_PIPLUP, 5, 0, OTID_STRUCT_PLAYER_ID);
    u32 location = MAPSEC_ROUTE_201, level = 5, game = VERSION_EMERALD;
    SetMonData(&mon, MON_DATA_MET_LOCATION, &location);
    SetMonData(&mon, MON_DATA_MET_LEVEL, &level);
    SetMonData(&mon, MON_DATA_MET_GAME, &game);
    struct BoxPokemon before = mon.box;
    u8 text[1024];
    EXPECT(TestSummaryBufferTrainerMemo(&mon, text));
    EXPECT(Contains(text, COMPOUND_STRING("ROUTE 201")));
    EXPECT(!Contains(text, COMPOUND_STRING("SANDGEM TOWN")));
    EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION), MAPSEC_ROUTE_201);
    EXPECT_EQ(memcmp(&before, &mon.box, sizeof(before)), 0);
    EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
}
