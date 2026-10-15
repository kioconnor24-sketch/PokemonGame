#include "global.h"
#include "test/battle.h"
#include "event_data.h"

WILD_BATTLE_TEST("Averon six-member party respects held EXP Share and the first cap", u32 leadExp)
{
    enum Item item = ITEM_NONE;
    u8 leadLevel = 10;
    u8 holderLevel = 10;

    PARAMETRIZE { item = ITEM_NONE; leadLevel = 10; }
    PARAMETRIZE { item = ITEM_EXP_SHARE; leadLevel = 10; }
    PARAMETRIZE { item = ITEM_NONE; leadLevel = 15; }
    PARAMETRIZE { item = ITEM_EXP_SHARE; leadLevel = 15; }
    PARAMETRIZE { item = ITEM_EXP_SHARE; leadLevel = 10; holderLevel = 15; }
    PARAMETRIZE { item = ITEM_EXP_SHARE; leadLevel = 15; holderLevel = 15; }

    GIVEN {
        FlagClear(FLAG_BADGE01_GET);
        PLAYER(SPECIES_WOBBUFFET) { Level(leadLevel); }
        PLAYER(SPECIES_WOBBUFFET) { Level(holderLevel); Item(item); }
        PLAYER(SPECIES_WOBBUFFET) { Level(10); }
        PLAYER(SPECIES_WOBBUFFET) { Level(10); }
        PLAYER(SPECIES_WOBBUFFET) { Level(10); }
        PLAYER(SPECIES_WOBBUFFET) { Level(10); }
        OPPONENT(SPECIES_CATERPIE) { Level(10); HP(1); }
    } WHEN {
        TURN { MOVE(player, MOVE_SCRATCH); }
    } SCENE {
        MESSAGE("Wobbuffet used Scratch!");
        MESSAGE("The wild Caterpie fainted!");
        NOT MESSAGE("The rest of your team gained EXP. Points thanks to the Exp. Share!");
    } THEN {
        u32 leadStart = gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][leadLevel];
        u32 benchStart = gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][10];
        u32 holderStart = gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][holderLevel];
        results[i].leadExp = GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP) - leadStart;
        if (leadLevel < 15)
            EXPECT_GT(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP), leadStart);
        else
            EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP), leadStart);
        if (item == ITEM_EXP_SHARE && holderLevel < 15)
            EXPECT_GT(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_EXP), holderStart);
        else
            EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_EXP), holderStart);
        for (u32 i = 2; i < PARTY_SIZE; ++i)
            EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_EXP), benchStart);
    } FINALLY {
        // Gen 5 allocation shares the available EXP pool, rather than giving
        // the active Pokemon full EXP plus a separate bonus to the holder.
        EXPECT_GT(results[0].leadExp, results[1].leadExp);
    }
}

WILD_BATTLE_TEST("Averon a large EXP reward stops exactly at the cap without banking excess")
{
    GIVEN {
        FlagClear(FLAG_BADGE01_GET);
        PLAYER(SPECIES_WOBBUFFET) { Level(14); Speed(1000); }
        OPPONENT(SPECIES_CHANSEY) { Level(100); HP(1); Speed(1); }
    } WHEN {
        TURN { MOVE(player, MOVE_SCRATCH); }
    } THEN {
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_LEVEL), 15);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP),
                  gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][15]);
    }
}
