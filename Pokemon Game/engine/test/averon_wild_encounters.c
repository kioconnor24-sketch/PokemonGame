#include "global.h"
#include "test/test.h"
#include "event_data.h"
#include "pokemon.h"
#include "wild_encounter.h"
#include "constants/item.h"

// The wild-encounter interface on Averon's existing maps, read as they are.
// No map, table or species is added or changed. Each existing table is
// checked for: its header resolves, every generated Pokemon and level comes
// from the table, every listed species can be met, and Repel works.

struct AveronEncounterMap
{
    u8 group;
    u8 num;
    u8 minLevel;
    u8 maxLevel;
};

static const struct AveronEncounterMap sMaps[] =
{
    { MAP_GROUP(MAP_COASTALMEADOW), MAP_NUM(MAP_COASTALMEADOW), 2, 4 },
    { MAP_GROUP(MAP_ORCHARDLANE), MAP_NUM(MAP_ORCHARDLANE), 5, 7 },
    { MAP_GROUP(MAP_COASTALBLUFFS), MAP_NUM(MAP_COASTALBLUFFS), 10, 13 },
};

static const struct WildPokemonInfo *SetMapAndGetLandInfo(u32 i)
{
    gSaveBlock1Ptr->location.mapGroup = sMaps[i].group;
    gSaveBlock1Ptr->location.mapNum = sMaps[i].num;
    u32 headerId = GetCurrentMapWildMonHeaderId();
    if (headerId == HEADER_NONE)
        return NULL;
    enum TimeOfDay timeOfDay = GetTimeOfDayForEncounters(headerId, WILD_AREA_LAND);
    return gWildMonHeaders[headerId].encounterTypes[timeOfDay].landMonsInfo;
}

static bool32 IsInTable(const struct WildPokemonInfo *info, enum Species species)
{
    for (u32 slot = 0; slot < NUM_LAND_MONS_ENCOUNTER_SLOTS; slot++)
    {
        if (info->wildPokemon[slot].species == species)
            return TRUE;
    }
    return FALSE;
}

TEST("Averon wild encounters: each existing Averon table generates only its own species and levels")
{
    u32 i = 0;
    PARAMETRIZE { i = 0; }
    PARAMETRIZE { i = 1; }
    PARAMETRIZE { i = 2; }

    const struct WildPokemonInfo *info = SetMapAndGetLandInfo(i);
    ASSUME(info != NULL);
    EXPECT_GT(info->encounterRate, 0);

    // Which of the table's slots produced a Pokemon at least once.
    u32 seen = 0;
    VarSet(VAR_REPEL_STEP_COUNT, 0);
    for (u32 n = 0; n < 400; n++)
    {
        EXPECT(TryGenerateWildMon(info, WILD_AREA_LAND, 0));
        enum Species species = GetMonData(&gParties[B_TRAINER_OPPONENT_A][0], MON_DATA_SPECIES);
        u32 level = GetMonData(&gParties[B_TRAINER_OPPONENT_A][0], MON_DATA_LEVEL);
        EXPECT(IsInTable(info, species));
        EXPECT_GE(level, sMaps[i].minLevel);
        EXPECT_LE(level, sMaps[i].maxLevel);
        for (u32 slot = 0; slot < NUM_LAND_MONS_ENCOUNTER_SLOTS; slot++)
        {
            if (info->wildPokemon[slot].species == species)
                seen |= 1u << slot;
        }
    }

    // Every species listed in the table is met at least once.
    for (u32 slot = 0; slot < NUM_LAND_MONS_ENCOUNTER_SLOTS; slot++)
    {
        enum Species species = info->wildPokemon[slot].species;
        bool32 met = FALSE;
        for (u32 other = 0; other < NUM_LAND_MONS_ENCOUNTER_SLOTS; other++)
        {
            if (info->wildPokemon[other].species == species && (seen & (1u << other)))
                met = TRUE;
        }
        EXPECT(met);
    }
}

TEST("Averon wild encounters: Repel blocks Pokemon below the lead's level on every Averon table")
{
    u32 i = 0;
    PARAMETRIZE { i = 0; }
    PARAMETRIZE { i = 1; }
    PARAMETRIZE { i = 2; }

    const struct WildPokemonInfo *info = SetMapAndGetLandInfo(i);
    ASSUME(info != NULL);

    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_WOBBUFFET, sMaps[i].maxLevel + 1, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    VarSet(VAR_REPEL_STEP_COUNT, 100);
    for (u32 n = 0; n < 50; n++)
        EXPECT(!TryGenerateWildMon(info, WILD_AREA_LAND, WILD_CHECK_REPEL));

    // A lead at the table's lowest level lets every encounter through.
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_LEVEL, &sMaps[i].minLevel);
    for (u32 n = 0; n < 50; n++)
        EXPECT(TryGenerateWildMon(info, WILD_AREA_LAND, WILD_CHECK_REPEL));

    VarSet(VAR_REPEL_STEP_COUNT, 0);
    ZeroPlayerPartyMons();
}

TEST("Averon wild encounters: an existing map without a table reports no encounter header")
{
    gSaveBlock1Ptr->location.mapGroup = MAP_GROUP(MAP_AVERONFIELDLAB);
    gSaveBlock1Ptr->location.mapNum = MAP_NUM(MAP_AVERONFIELDLAB);
    EXPECT_EQ(GetCurrentMapWildMonHeaderId(), HEADER_NONE);
}
