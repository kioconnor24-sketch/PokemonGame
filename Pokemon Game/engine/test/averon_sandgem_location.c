#include "global.h"
#include "test/test.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "pokemon_summary_screen.h"
#include "region_map.h"
#include "map_name_popup.h"
#include "regions.h"
#include "string_util.h"
#include "constants/characters.h"

STATIC_ASSERT(MAPSEC_SANDGEM_TOWN == 216, sandgem_owner_approved_value);
STATIC_ASSERT(MAPSEC_NONE == 215, sandgem_preserves_none);
STATIC_ASSERT(MAPSEC_ROUTE_201 == 217, route201_owner_approved_value);
STATIC_ASSERT(MAPSEC_TWINLEAF_TOWN == 218, twinleaf_owner_approved_value);
STATIC_ASSERT(MAPSEC_COUNT == 219, no_other_allocations);

static bool32 Contains(const u8 *text, const u8 *needle)
{
    u32 length = StringLength(text), n = StringLength(needle);
    for (u32 i = 0; i + n <= length; i++)
        if (memcmp(text + i, needle, n) == 0)
            return TRUE;
    return FALSE;
}

TEST("Averon Sandgem is section 216 in Sinnoh with no assigned sentinel or future names")
{
    u8 text[64];
    GetMapName(text, MAPSEC_SANDGEM_TOWN, 0);
    EXPECT_EQ(StringCompare(text, COMPOUND_STRING("SANDGEM TOWN")), 0);
    struct MapHeader map = {.regionMapSectionId = MAPSEC_SANDGEM_TOWN};
    GetPopUpMapName(text, &map);
    EXPECT_EQ(StringCompare(text, COMPOUND_STRING("SANDGEM TOWN")), 0);
    EXPECT_EQ(GetRegionForSectionId(MAPSEC_SANDGEM_TOWN), REGION_SINNOH);
    EXPECT(IsRegionMapSectionIdValid(MAPSEC_SANDGEM_TOWN));
    EXPECT(!IsRegionMapSectionIdValid(MAPSEC_NONE));
    EXPECT(IsRegionMapSectionIdValid(MAPSEC_ROUTE_201));
    EXPECT(IsRegionMapSectionIdValid(MAPSEC_TWINLEAF_TOWN));
    for (u32 i = 219; i <= 255; i++)
        EXPECT(!IsRegionMapSectionIdValid(i));
}

TEST("Averon Sandgem real summary formatter names caught hatched and traded origins")
{
    bool32 hatched = FALSE, traded = FALSE;
    PARAMETRIZE { hatched = FALSE; traded = FALSE; }
    PARAMETRIZE { hatched = TRUE; traded = FALSE; }
    PARAMETRIZE { hatched = FALSE; traded = TRUE; }
    struct Pokemon mon;
    StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CODEX"));
    gSaveBlock2Ptr->playerGender = MALE;
    CreateMon(&mon, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    u32 location = MAPSEC_SANDGEM_TOWN, level = hatched ? 0 : 12, game = VERSION_EMERALD;
    SetMonData(&mon, MON_DATA_MET_LOCATION, &location);
    SetMonData(&mon, MON_DATA_MET_LEVEL, &level);
    SetMonData(&mon, MON_DATA_MET_GAME, &game);
    if (traded)
        SetBoxMonOtIdKeepingData(&mon.box, GetMonData(&mon, MON_DATA_OT_ID) ^ 1);
    struct BoxPokemon before = mon.box;
    u8 text[1024];
    EXPECT(TestSummaryBufferTrainerMemo(&mon, text));
    EXPECT(Contains(text, COMPOUND_STRING("SANDGEM TOWN")));
    EXPECT(Contains(text, hatched ? COMPOUND_STRING("hatched at")
        : traded ? COMPOUND_STRING("probably met at") : COMPOUND_STRING("met at")));
    EXPECT_EQ(memcmp(&before, &mon.box, sizeof(before)), 0);
    EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
}

TEST("Averon Sandgem summary keeps NONE unassigned and special met values unnamed")
{
    struct Pokemon mon;
    StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CODEX"));
    gSaveBlock2Ptr->playerGender = MALE;
    CreateMon(&mon, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    u8 text[1024];
    static const u8 values[] = {215, 219, 252, 253, 254, 255};
    for (u32 i = 0; i < ARRAY_COUNT(values); i++)
    {
        u32 value = values[i];
        SetMonData(&mon, MON_DATA_MET_LOCATION, &value);
        EXPECT(TestSummaryBufferTrainerMemo(&mon, text));
        EXPECT(!Contains(text, COMPOUND_STRING("SANDGEM TOWN")));
        EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION), value);
    }
}

// All 215 defined legacy Gen3 popup results, frozen from main203a89cc.
static const u8 sLegacyPopupThemes[] = {
    0, 0, 0, 0, 0, 0, 0, 3, 1, 1, 1, 3, 1, 3, 1, 3, 0, 0, 0, 0,
    4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 4,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 2, 2, 0, 1, 0,
    2, 0, 1, 2, 2, 2, 2, 2, 2, 5, 2, 0, 2, 0, 2, 2, 0, 0, 2, 5,
    2, 2, 2, 2, 0, 2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 0, 2, 2,
    5, 2, 5, 5, 5, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0,
};

TEST("Averon Sandgem popup theme stays in bounds with fixed NONE and future codes")
{
    for (u32 i = 0; i < ARRAY_COUNT(sLegacyPopupThemes); i++)
        EXPECT_EQ(TestMapNamePopupTheme(i, FALSE), sLegacyPopupThemes[i]);
    static const u32 values[] = {215, 216, 217, 252, 253, 254, 255, 256, 0xFFFFFFFF};
    for (u32 i = 0; i < ARRAY_COUNT(values); i++)
    {
        EXPECT_EQ(TestMapNamePopupTheme(values[i], FALSE), 0); // existing WOOD fallback
        EXPECT_EQ(TestMapNamePopupTheme(values[i], TRUE), 0); // existing BW default
    }
    EXPECT_EQ(TestMapNamePopupTheme(MAPSEC_LITTLEROOT_TOWN, FALSE), 0);
    EXPECT_EQ(TestMapNamePopupTheme(MAPSEC_MT_CHIMNEY, FALSE), 2); // STONE remains exact
}
