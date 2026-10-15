#include "global.h"
#include "test/battle.h"
#include "money.h"

// Real trainer battles through the engine's lost-battle script. Natives and
// script macros are covered in averon_scripted_battle.c.

#define START_MONEY 5000

AI_SINGLE_BATTLE_TEST("Averon scripted loss skips the whiteout and keeps the player's money")
{
    u32 scripted;
    PARAMETRIZE { scripted = FALSE; }
    PARAMETRIZE { scripted = TRUE; }
    GIVEN {
        if (scripted)
            FLAG_SET(B_FLAG_NO_WHITEOUT);
        SetMoney(&gSaveBlock1Ptr->money, START_MONEY);
        PLAYER(SPECIES_WOBBUFFET) { HP(1); Moves(MOVE_SPLASH); }
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_SPLASH); EXPECT_MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
        if (scripted)
            NOT MESSAGE("You have no more Pokémon that can fight!\p");
        else
            MESSAGE("You have no more Pokémon that can fight!\p");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_LOST);
        if (scripted)
            EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
        else
            EXPECT_LT(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
    }
}

AI_SINGLE_BATTLE_TEST("Averon chain battle damage and status carry back into the party")
{
    u32 startHP = 60;
    GIVEN {
        FLAG_SET(B_FLAG_NO_WHITEOUT);
        PLAYER(SPECIES_WOBBUFFET) { HP(60); Status1(STATUS1_POISON); Speed(1); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(1); Speed(100); Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); EXPECT_MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The opposing Wobbuffet fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_LT(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), startHP);
        EXPECT_GT(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), 0);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_STATUS), STATUS1_POISON);
    }
}
