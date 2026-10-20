#include "global.h"
#include "test/test.h"
#include "pokemon.h"
#include "pokemon_summary_screen.h"
#include "region_map.h"
#include "map_name_popup.h"
#include "regions.h"
#include "string_util.h"
#include "overworld.h"
#include "constants/map_groups.h"

// Owner decision 6272466493 (Issue #15): Lake Verity is section 220, shared by Verity Lakefront and Lake Verity.
STATIC_ASSERT(MAPSEC_LAKE_VERITY == 220, lake_verity_section_value);

static bool32 Contains(const u8 *text, const u8 *needle)
{
    u32 length = StringLength(text), n = StringLength(needle);
    for (u32 i = 0; i + n <= length; i++)
        if (memcmp(text + i, needle, n) == 0)
            return TRUE;
    return FALSE;
}

TEST("Averon Lake Verity is section 220 in Sinnoh with its own name and popup")
{
    u8 text[64];
    GetMapName(text, MAPSEC_LAKE_VERITY, 0);
    EXPECT_EQ(StringCompare(text, COMPOUND_STRING("LAKE VERITY")), 0);
    struct MapHeader map = {.regionMapSectionId = MAPSEC_LAKE_VERITY};
    GetPopUpMapName(text, &map);
    EXPECT_EQ(StringCompare(text, COMPOUND_STRING("LAKE VERITY")), 0);
    EXPECT_EQ(GetRegionForSectionId(MAPSEC_LAKE_VERITY), REGION_SINNOH);
    EXPECT(IsRegionMapSectionIdValid(MAPSEC_LAKE_VERITY));
    // Hoenn's Route 102 keeps its legacy identity and region.
    GetMapName(text, MAPSEC_ROUTE_102, 0);
    EXPECT_EQ(StringCompare(text, COMPOUND_STRING("ROUTE 102")), 0);
    EXPECT_EQ(GetRegionForSectionId(MAPSEC_ROUTE_102), REGION_HOENN);
}

TEST("Averon Lake Verity origin survives the real summary formatter unchanged")
{
    struct Pokemon mon;
    StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CLAUDE"));
    gSaveBlock2Ptr->playerGender = MALE;
    CreateMon(&mon, SPECIES_PIPLUP, 5, 0, OTID_STRUCT_PLAYER_ID);
    u32 location = MAPSEC_LAKE_VERITY, level = 5, game = VERSION_EMERALD;
    SetMonData(&mon, MON_DATA_MET_LOCATION, &location);
    SetMonData(&mon, MON_DATA_MET_LEVEL, &level);
    SetMonData(&mon, MON_DATA_MET_GAME, &game);
    struct BoxPokemon before = mon.box;
    u8 text[1024];
    EXPECT(TestSummaryBufferTrainerMemo(&mon, text));
    EXPECT(Contains(text, COMPOUND_STRING("LAKE VERITY")));
    EXPECT(!Contains(text, COMPOUND_STRING("ROUTE 201")) && !Contains(text, COMPOUND_STRING("ROUTE 102")));
    EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION), MAPSEC_LAKE_VERITY);
    EXPECT_EQ(memcmp(&before, &mon.box, sizeof(before)), 0);
    EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
}

TEST("Averon Verity Lakefront and Lake Verity share section 220 and stay in the Sinnoh group")
{
    const struct MapHeader *front = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_VERITY_LAKEFRONT), MAP_NUM(MAP_VERITY_LAKEFRONT));
    const struct MapHeader *lake = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_LAKE_VERITY), MAP_NUM(MAP_LAKE_VERITY));
    EXPECT_EQ(front->regionMapSectionId, MAPSEC_LAKE_VERITY);
    EXPECT_EQ(lake->regionMapSectionId, MAPSEC_LAKE_VERITY);
    EXPECT_EQ(MAP_GROUP(MAP_VERITY_LAKEFRONT), MAP_GROUP(MAP_SANDGEM_TOWN));
    EXPECT_EQ(MAP_GROUP(MAP_LAKE_VERITY), MAP_GROUP(MAP_SANDGEM_TOWN));
    EXPECT_EQ(MAP_NUM(MAP_ROUTE202) + 1, MAP_NUM(MAP_VERITY_LAKEFRONT));
    EXPECT_EQ(MAP_NUM(MAP_VERITY_LAKEFRONT) + 1, MAP_NUM(MAP_LAKE_VERITY));
}
