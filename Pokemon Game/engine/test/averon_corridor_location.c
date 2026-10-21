#include "global.h"
#include "test/test.h"
#include "pokemon.h"
#include "pokemon_summary_screen.h"
#include "region_map.h"
#include "regions.h"
#include "string_util.h"

STATIC_ASSERT(MAPSEC_JUBILIFE_CITY == 221, jubilife_approved_id);
STATIC_ASSERT(MAPSEC_ROUTE_203 == 222, route203_approved_id);
STATIC_ASSERT(MAPSEC_OREBURGH_GATE == 223, gate_approved_id);
STATIC_ASSERT(MAPSEC_NONE == 215, sentinel_unchanged);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, boxed_format_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, party_format_unchanged);

TEST("Averon corridor approved origins have names and survive boxed summary reads")
{
    static const struct {u16 section; const u8 *name;} cases[] = {
        {MAPSEC_JUBILIFE_CITY, COMPOUND_STRING("JUBILIFE CITY")},
        {MAPSEC_ROUTE_203, COMPOUND_STRING("ROUTE 203")},
        {MAPSEC_OREBURGH_GATE, COMPOUND_STRING("OREBURGH GATE")},
    };
    for (u32 i = 0; i < ARRAY_COUNT(cases); i++)
    {
        struct Pokemon mon;
        u8 name[64], memo[1024];
        u32 origin = cases[i].section, game = VERSION_EMERALD, level = 5;
        StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CODEX"));
        gSaveBlock2Ptr->playerGender = MALE;
        CreateMon(&mon, SPECIES_PIPLUP, 5, 0, OTID_STRUCT_PLAYER_ID);
        SetMonData(&mon, MON_DATA_MET_LOCATION, &origin);
        SetMonData(&mon, MON_DATA_MET_LEVEL, &level);
        SetMonData(&mon, MON_DATA_MET_GAME, &game);
        struct BoxPokemon boxed = mon.box;
        GetMapName(name, origin, 0);
        EXPECT_EQ(StringCompare(name, cases[i].name), 0);
        EXPECT_EQ(GetRegionForSectionId(origin), REGION_SINNOH);
        EXPECT(IsRegionMapSectionIdValid(origin));
        EXPECT(TestSummaryBufferTrainerMemo(&mon, memo));
        bool32 found = FALSE;
        for (u32 n = 0; n + StringLength(cases[i].name) <= StringLength(memo); n++)
            if (memcmp(memo+n, cases[i].name, StringLength(cases[i].name)) == 0)
                found = TRUE;
        EXPECT(found);
        EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION), origin);
        EXPECT_EQ(memcmp(&boxed, &mon.box, sizeof(boxed)), 0);
        EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    }
}
