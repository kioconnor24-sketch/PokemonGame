#include "global.h"
#include "test/test.h"
#include "battle.h"
#include "caps.h"
#include "event_data.h"
#include "pokemon.h"

TEST("Averon Rare Candy respects the cap and becomes usable after the badge")
{
    struct Pokemon *mon=&gParties[B_TRAINER_PLAYER][0];
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(mon,SPECIES_WOBBUFFET,14,0);
    CalculatePlayerPartyCount();
    FlagClear(FLAG_BADGE01_GET);
    gMain.inBattle=FALSE;
    EXPECT_EQ(GetCurrentLevelCap(),15);
    EXPECT_EQ(ExecuteTableBasedItemEffect(mon,ITEM_RARE_CANDY,0,0),FALSE);
    EXPECT_EQ(GetMonData(mon,MON_DATA_LEVEL),15);
    EXPECT_EQ(ExecuteTableBasedItemEffect(mon,ITEM_RARE_CANDY,0,0),TRUE);
    EXPECT_EQ(GetMonData(mon,MON_DATA_LEVEL),15);
    EXPECT_EQ(GetMonData(mon,MON_DATA_EXP),gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][15]);
    FlagSet(FLAG_BADGE01_GET);
    EXPECT_EQ(GetCurrentLevelCap(),23);
    EXPECT_EQ(ExecuteTableBasedItemEffect(mon,ITEM_RARE_CANDY,0,0),FALSE);
    EXPECT_EQ(GetMonData(mon,MON_DATA_LEVEL),16);
}
