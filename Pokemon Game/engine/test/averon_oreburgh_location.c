#include "global.h"
#include "test/test.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "pokemon_summary_screen.h"
#include "region_map.h"
#include "map_name_popup.h"
#include "regions.h"
#include "string_util.h"
#include "overworld.h"
#include "averon_region_save.h"
#include "save.h"
#include "load_save.h"
#include "gba/flash_internal.h"
#include "constants/maps.h"

// Owner decision delegated to Claude, 2026-10-27 (#15 comment 6434228501): one code, 227 = Oreburgh City.
STATIC_ASSERT(MAPSEC_OREBURGH_CITY == 227, oreburgh_owner_value);
STATIC_ASSERT(MAPSEC_ROUTE_205 == 226, oreburgh_prior_codes_unchanged);
STATIC_ASSERT(MAPSEC_NONE == 215, oreburgh_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 228, oreburgh_no_unapproved_allocations);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, oreburgh_box_format_preserved);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, oreburgh_party_format_preserved);

// West packet C: slots 30-40, the city and its ten interiors, all under the one approved code.
static const u32 sOreburghMaps[] = {
    MAP_OREBURGH_CITY, MAP_OREBURGH_CITY_POKEMON_CENTER_1F, MAP_OREBURGH_CITY_MART, MAP_OREBURGH_CITY_MUSEUM_1F,
    MAP_OREBURGH_CITY_MUSEUM_2F, MAP_OREBURGH_CITY_CONDO, MAP_OREBURGH_CITY_HOUSE1, MAP_OREBURGH_CITY_HOUSE2,
    MAP_OREBURGH_CITY_HOUSE3, MAP_OREBURGH_CITY_HOUSE4, MAP_OREBURGH_CITY_HOUSE5,
};

static bool32 Contains(const u8 *text, const u8 *needle)
{
    for (u32 i = 0; i + StringLength(needle) <= StringLength(text); i++)
        if (memcmp(text + i, needle, StringLength(needle)) == 0)
            return TRUE;
    return FALSE;
}

TEST("Averon Oreburgh City and its interiors share only the approved origin name")
{
    for (u32 i = 0; i < ARRAY_COUNT(sOreburghMaps); i++)
    {
        const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(
            MAP_GROUP(sOreburghMaps[i]), MAP_NUM(sOreburghMaps[i]));
        u8 text[64];
        EXPECT_EQ(MAP_GROUP(sOreburghMaps[i]), MAP_GROUP(MAP_SANDGEM_TOWN));
        EXPECT_EQ(MAP_NUM(sOreburghMaps[i]), 30 + i);
        EXPECT_EQ(header->regionMapSectionId, MAPSEC_OREBURGH_CITY);
        EXPECT_EQ(GetRegionForSectionId(header->regionMapSectionId), REGION_SINNOH);
        EXPECT(IsRegionMapSectionIdValid(header->regionMapSectionId));
        GetMapName(text, header->regionMapSectionId, 0);
        EXPECT_EQ(StringCompare(text, COMPOUND_STRING("OREBURGH CITY")), 0);
        GetPopUpMapName(text, header);
        EXPECT_EQ(StringCompare(text, COMPOUND_STRING("OREBURGH CITY")), 0);
    }
}

TEST("Averon Oreburgh summary names caught hatched and traded origins without changing encrypted data")
{
    u32 section = MAPSEC_OREBURGH_CITY;
    for (u32 mode = 0; mode < 3; mode++)
    {
        struct Pokemon mon;
        u8 memo[1024];
        u32 level = mode == 1 ? 0 : 12, game = VERSION_EMERALD;
        StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CLAUDE"));
        gSaveBlock2Ptr->playerGender = MALE;
        CreateMon(&mon, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
        SetMonData(&mon, MON_DATA_MET_LOCATION, &section);
        SetMonData(&mon, MON_DATA_MET_LEVEL, &level);
        SetMonData(&mon, MON_DATA_MET_GAME, &game);
        if (mode == 2)
            SetBoxMonOtIdKeepingData(&mon.box, GetMonData(&mon, MON_DATA_OT_ID) ^ 1);
        struct BoxPokemon before = mon.box;
        EXPECT(TestSummaryBufferTrainerMemo(&mon, memo));
        EXPECT(Contains(memo, COMPOUND_STRING("OREBURGH CITY")));
        EXPECT(Contains(memo, mode == 1 ? COMPOUND_STRING("hatched at")
            : mode == 2 ? COMPOUND_STRING("probably met at") : COMPOUND_STRING("met at")));
        EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION), section);
        EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        EXPECT_EQ(memcmp(&before, &mon.box, sizeof(before)), 0);
    }
}

TEST("Averon Oreburgh flash reload preserves party PC legacy special origins and city position")
{
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    ZeroPlayerPartyMons();
    u32 origin = MAPSEC_OREBURGH_CITY;
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PRESET(0x12345678));
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION, &origin);
    CalculatePlayerPartyCount();
    struct BoxPokemon party = gParties[B_TRAINER_PLAYER][0].box, boxes[3];
    const u32 origins[] = {origin, MAPSEC_SALTMERE, METLOC_FATEFUL_ENCOUNTER};
    for (u32 i = 0; i < ARRAY_COUNT(boxes); i++)
    {
        CreateBoxMon(&boxes[i], SPECIES_PIPLUP, 12, i, OTID_STRUCT_PRESET(0x87654321));
        SetBoxMonData(&boxes[i], MON_DATA_MET_LOCATION, &origins[i]);
        SetBoxMonAt(0, i, &boxes[i]);
    }
    struct WarpData position = {MAP_GROUP(MAP_OREBURGH_CITY), MAP_NUM(MAP_OREBURGH_CITY), WARP_ID_NONE, 6, 13};
    gSaveBlock1Ptr->location = position;
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    EXPECT(AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &position));
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    memset(&gSaveBlock1Ptr->location, 0, sizeof(position));
    ZeroPlayerPartyMons();
    for (u32 i = 0; i < ARRAY_COUNT(boxes); i++)
        ZeroBoxMonAt(0, i);
    AveronRegionSave_InitNewGame();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(memcmp(&position, &gSaveBlock1Ptr->location, sizeof(position)), 0);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
    EXPECT_EQ(memcmp(&party, &gParties[B_TRAINER_PLAYER][0].box, sizeof(party)), 0);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION), origin);
    for (u32 i = 0; i < ARRAY_COUNT(boxes); i++)
    {
        EXPECT_EQ(memcmp(&boxes[i], GetBoxedMonPtr(0, i), sizeof(boxes[i])), 0);
        EXPECT_EQ(GetBoxMonData(GetBoxedMonPtr(0, i), MON_DATA_MET_LOCATION), origins[i]);
    }
}
