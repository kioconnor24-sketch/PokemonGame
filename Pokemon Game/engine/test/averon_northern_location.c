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

// Explicit owner chat decision, 2026-10-21: three shared codes, not five.
STATIC_ASSERT(MAPSEC_ROUTE_204 == 224, route204_owner_value);
STATIC_ASSERT(MAPSEC_FLOAROMA_TOWN == 225, floaroma_owner_value);
STATIC_ASSERT(MAPSEC_ROUTE_205 == 226, route205_owner_value);
STATIC_ASSERT(MAPSEC_NONE == 215, northern_none_preserved);
STATIC_ASSERT(MAPSEC_COUNT == 228, northern_no_unapproved_allocations); // + 227 Oreburgh City (averon_oreburgh_location.c)
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, northern_box_format_preserved);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, northern_party_format_preserved);

static const struct {u32 map; u8 section; s16 x, y;} sNorthernMaps[] = {
    {MAP_ROUTE204, MAPSEC_ROUTE_204, 12, 63},
    {MAP_RAVAGED_PATH, MAPSEC_ROUTE_204, 19, 3},
    {MAP_FLOAROMA_TOWN, MAPSEC_FLOAROMA_TOWN, 13, 35},
    {MAP_FLOAROMA_MEADOW, MAPSEC_FLOAROMA_TOWN, 11, 1},
    {MAP_ROUTE205_SOUTH, MAPSEC_ROUTE_205, 26, 81},
    {MAP_ROUTE205_NORTH, MAPSEC_ROUTE_205, 3, 57},
};

static const u8 *NorthernName(u32 section)
{
    switch (section)
    {
    case MAPSEC_ROUTE_204: return COMPOUND_STRING("ROUTE 204");
    case MAPSEC_FLOAROMA_TOWN: return COMPOUND_STRING("FLOAROMA TOWN");
    default: return COMPOUND_STRING("ROUTE 205");
    }
}

static bool32 Contains(const u8 *text, const u8 *needle)
{
    for (u32 i = 0; i + StringLength(needle) <= StringLength(text); i++)
        if (memcmp(text + i, needle, StringLength(needle)) == 0)
            return TRUE;
    return FALSE;
}

TEST("Averon northern map headers share only the three approved origin names")
{
    for (u32 i = 0; i < ARRAY_COUNT(sNorthernMaps); i++)
    {
        const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(
            MAP_GROUP(sNorthernMaps[i].map), MAP_NUM(sNorthernMaps[i].map));
        u8 text[64];
        EXPECT_EQ(MAP_GROUP(sNorthernMaps[i].map), MAP_GROUP(MAP_SANDGEM_TOWN));
        EXPECT_EQ(MAP_NUM(sNorthernMaps[i].map), 13 + i);
        EXPECT_EQ(header->regionMapSectionId, sNorthernMaps[i].section);
        EXPECT_EQ(GetRegionForSectionId(header->regionMapSectionId), REGION_SINNOH);
        EXPECT(IsRegionMapSectionIdValid(header->regionMapSectionId));
        GetMapName(text, header->regionMapSectionId, 0);
        EXPECT_EQ(StringCompare(text, NorthernName(header->regionMapSectionId)), 0);
        GetPopUpMapName(text, header);
        EXPECT_EQ(StringCompare(text, NorthernName(header->regionMapSectionId)), 0);
    }
}

TEST("Averon northern summary names caught hatched and traded origins without changing encrypted data")
{
    u32 section = MAPSEC_ROUTE_204;
    PARAMETRIZE { section = MAPSEC_ROUTE_204; }
    PARAMETRIZE { section = MAPSEC_FLOAROMA_TOWN; }
    PARAMETRIZE { section = MAPSEC_ROUTE_205; }
    for (u32 mode = 0; mode < 3; mode++)
    {
        struct Pokemon mon;
        u8 memo[1024];
        u32 level = mode == 1 ? 0 : 12, game = VERSION_EMERALD;
        StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CODEX"));
        gSaveBlock2Ptr->playerGender = MALE;
        CreateMon(&mon, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
        SetMonData(&mon, MON_DATA_MET_LOCATION, &section);
        SetMonData(&mon, MON_DATA_MET_LEVEL, &level);
        SetMonData(&mon, MON_DATA_MET_GAME, &game);
        if (mode == 2)
            SetBoxMonOtIdKeepingData(&mon.box, GetMonData(&mon, MON_DATA_OT_ID) ^ 1);
        struct BoxPokemon before = mon.box;
        EXPECT(TestSummaryBufferTrainerMemo(&mon, memo));
        EXPECT(Contains(memo, NorthernName(section)));
        EXPECT(Contains(memo, mode == 1 ? COMPOUND_STRING("hatched at")
            : mode == 2 ? COMPOUND_STRING("probably met at") : COMPOUND_STRING("met at")));
        EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION), section);
        EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        EXPECT_EQ(memcmp(&before, &mon.box, sizeof(before)), 0);
    }
}

TEST("Averon northern flash reload preserves party PC legacy special origins and regional position")
{
    u32 index = 0;
    PARAMETRIZE { index = 0; }
    PARAMETRIZE { index = 1; }
    PARAMETRIZE { index = 2; }
    PARAMETRIZE { index = 3; }
    PARAMETRIZE { index = 4; }
    PARAMETRIZE { index = 5; }
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    ZeroPlayerPartyMons();
    u32 origin = sNorthernMaps[index].section;
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
    struct WarpData position = {MAP_GROUP(sNorthernMaps[index].map), MAP_NUM(sNorthernMaps[index].map),
        WARP_ID_NONE, sNorthernMaps[index].x, sNorthernMaps[index].y};
    gSaveBlock1Ptr->location = position;
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    EXPECT(AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &position));
    struct AveronRegionState before, after;
    EXPECT(AveronRegionSave_GetState(&before));
    const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(position.mapGroup, position.mapNum);
    struct WarpData invalid = position;
    invalid.warpId = header->events->warpCount; // Also zero for maps with no indexed entrances.
    EXPECT(!AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &invalid));
    EXPECT(AveronRegionSave_GetState(&after));
    EXPECT_EQ(memcmp(&before, &after, sizeof(before)), 0);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    memset(&gSaveBlock1Ptr->location, 0, sizeof(position));
    ZeroPlayerPartyMons();
    for (u32 i = 0; i < ARRAY_COUNT(boxes); i++)
        ZeroBoxMonAt(0, i);
    AveronRegionSave_InitNewGame();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(memcmp(&position, &gSaveBlock1Ptr->location, sizeof(position)), 0);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
    struct WarpData observed;
    EXPECT(AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &observed));
    EXPECT_EQ(observed.mapGroup, position.mapGroup);
    EXPECT_EQ(observed.mapNum, position.mapNum);
    EXPECT_EQ(observed.warpId, position.warpId);
    EXPECT_EQ(observed.x, position.x);
    EXPECT_EQ(observed.y, position.y);
    EXPECT_EQ(memcmp(&party, &gParties[B_TRAINER_PLAYER][0].box, sizeof(party)), 0);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION), origin);
    for (u32 i = 0; i < ARRAY_COUNT(boxes); i++)
    {
        EXPECT_EQ(memcmp(&boxes[i], GetBoxedMonPtr(0, i), sizeof(boxes[i])), 0);
        EXPECT_EQ(GetBoxMonData(GetBoxedMonPtr(0, i), MON_DATA_MET_LOCATION), origins[i]);
        EXPECT_EQ(GetBoxMonData(GetBoxedMonPtr(0, i), MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    }
}
