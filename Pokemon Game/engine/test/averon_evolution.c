#include "global.h"
#include "test/test.h"
#include "battle.h"
#include "caps.h"
#include "event_data.h"
#include "pokemon.h"

TEST("Averon starters reach their first evolution only after the first badge opens the cap")
{
    u32 species = SPECIES_SNIVY, evolved = SPECIES_SERVINE, evolutionLevel = 17;
    PARAMETRIZE { species=SPECIES_SNIVY; evolved=SPECIES_SERVINE; evolutionLevel=17; }
    PARAMETRIZE { species=SPECIES_FENNEKIN; evolved=SPECIES_BRAIXEN; evolutionLevel=16; }
    PARAMETRIZE { species=SPECIES_PIPLUP; evolved=SPECIES_PRINPLUP; evolutionLevel=16; }
    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][0];
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(mon, species, 15, 0);
    CalculatePlayerPartyCount();
    gMain.inBattle = FALSE;
    FlagClear(FLAG_BADGE01_GET);
    EXPECT_EQ(GetCurrentLevelCap(), 15);
    EXPECT_EQ(ExecuteTableBasedItemEffect(mon, ITEM_RARE_CANDY, 0, 0), TRUE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_LEVEL), 15);
    EXPECT_EQ(GetEvolutionTargetSpecies(mon, EVO_MODE_NORMAL, ITEM_NONE, NULL, NULL, CHECK_EVO), SPECIES_NONE);

    FlagSet(FLAG_BADGE01_GET);
    EXPECT_EQ(GetCurrentLevelCap(), 23);
    for (u32 level = 16; level <= evolutionLevel; ++level)
    {
        EXPECT_EQ(ExecuteTableBasedItemEffect(mon, ITEM_RARE_CANDY, 0, 0), FALSE);
        EXPECT_EQ(GetMonData(mon, MON_DATA_LEVEL), level);
        EXPECT_EQ(GetEvolutionTargetSpecies(mon, EVO_MODE_NORMAL, ITEM_NONE, NULL, NULL, CHECK_EVO),
                  level == evolutionLevel ? evolved : SPECIES_NONE);
    }
}

TEST("Averon starter evolution can be postponed with Everstone and resumes after removal")
{
    u32 species = SPECIES_SNIVY, evolved = SPECIES_SERVINE, level = 17;
    PARAMETRIZE { species=SPECIES_SNIVY; evolved=SPECIES_SERVINE; level=17; }
    PARAMETRIZE { species=SPECIES_FENNEKIN; evolved=SPECIES_BRAIXEN; level=16; }
    PARAMETRIZE { species=SPECIES_PIPLUP; evolved=SPECIES_PRINPLUP; level=16; }
    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][0];
    u16 item = ITEM_EVERSTONE;
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(mon, species, level, 0);
    CalculatePlayerPartyCount();
    FlagSet(FLAG_BADGE01_GET);
    SetMonData(mon, MON_DATA_HELD_ITEM, &item);
    EXPECT_EQ(GetEvolutionTargetSpecies(mon, EVO_MODE_NORMAL, ITEM_NONE, NULL, NULL, CHECK_EVO), SPECIES_NONE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_HELD_ITEM), ITEM_EVERSTONE);
    item = ITEM_NONE;
    SetMonData(mon, MON_DATA_HELD_ITEM, &item);
    EXPECT_EQ(GetEvolutionTargetSpecies(mon, EVO_MODE_NORMAL, ITEM_NONE, NULL, NULL, CHECK_EVO), evolved);
    EXPECT_EQ(GetMonData(mon, MON_DATA_SPECIES), species);
}
