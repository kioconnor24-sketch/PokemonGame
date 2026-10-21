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
#include "averon_region_save.h"
#include "save.h"
#include "gba/flash_internal.h"

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

TEST("Averon Verity return warp accepts both real entrances and refuses an absent entrance atomically")
{
    u32 map = MAP_VERITY_LAKEFRONT, entrance = 0;
    PARAMETRIZE { map = MAP_VERITY_LAKEFRONT; entrance = 0; }
    PARAMETRIZE { map = MAP_VERITY_LAKEFRONT; entrance = 1; }
    PARAMETRIZE { map = MAP_LAKE_VERITY; entrance = 0; }
    PARAMETRIZE { map = MAP_LAKE_VERITY; entrance = 1; }
    struct WarpData warp = {MAP_GROUP(map), MAP_NUM(map), entrance, -1, -1}, observed;
    struct AveronRegionState before, after;
    AveronRegionSave_InitNewGame();
    EXPECT(AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    EXPECT(AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &observed));
    EXPECT_EQ(warp.mapGroup, observed.mapGroup);
    EXPECT_EQ(warp.mapNum, observed.mapNum);
    EXPECT_EQ(warp.warpId, observed.warpId);
    EXPECT_EQ(warp.x, observed.x);
    EXPECT_EQ(warp.y, observed.y);
    EXPECT(AveronRegionSave_GetState(&before));
    warp.warpId = 2; // Only entrances 0 and 1 exist in either linked map.
    EXPECT(!AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    EXPECT(AveronRegionSave_GetState(&after));
    EXPECT_EQ(memcmp(&before, &after, sizeof(before)), 0);
}

TEST("Averon Verity flash reload preserves the new map position origin and regional return destination")
{
    u32 map = MAP_VERITY_LAKEFRONT;
    PARAMETRIZE { map = MAP_VERITY_LAKEFRONT; }
    PARAMETRIZE { map = MAP_LAKE_VERITY; }
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 5, 0, OTID_STRUCT_PRESET(0x12345678));
    u32 origin = MAPSEC_LAKE_VERITY;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION, &origin);
    CalculatePlayerPartyCount();
    struct BoxPokemon before = gParties[B_TRAINER_PLAYER][0].box;
    struct WarpData position = {MAP_GROUP(map), MAP_NUM(map), WARP_ID_NONE,
        map == MAP_VERITY_LAKEFRONT ? 2 : 38, map == MAP_VERITY_LAKEFRONT ? 5 : 42};
    gSaveBlock1Ptr->location = position;
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    EXPECT(AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &position));
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    memset(&gSaveBlock1Ptr->location, 0, sizeof(gSaveBlock1Ptr->location));
    ZeroPlayerPartyMons();
    AveronRegionSave_InitNewGame();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(memcmp(&position, &gSaveBlock1Ptr->location, sizeof(position)), 0);
    struct WarpData observed;
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
    EXPECT(AveronRegion_GetReturnWarp(AVERON_SAVE_REGION_SINNOH, &observed));
    EXPECT_EQ(position.mapGroup, observed.mapGroup);
    EXPECT_EQ(position.mapNum, observed.mapNum);
    EXPECT_EQ(position.warpId, observed.warpId);
    EXPECT_EQ(position.x, observed.x);
    EXPECT_EQ(position.y, observed.y);
    EXPECT_EQ(memcmp(&before, &gParties[B_TRAINER_PLAYER][0].box, sizeof(before)), 0);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION), MAPSEC_LAKE_VERITY);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SANITY_IS_BAD_EGG), FALSE);
}
