#include "global.h"
#include "test/battle.h"
#include "averon_scripted_battle.h"
#include "event_data.h"
#include "money.h"
#include "script.h"
#include "test/overworld_script.h"

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

// The macro's own natives, run by the script engine around a real battle.
AI_SINGLE_BATTLE_TEST("Averon scripted battle natives around a real battle report the result and clear the flag")
{
    u32 lose;
    PARAMETRIZE { lose = FALSE; }
    PARAMETRIZE { lose = TRUE; }
    GIVEN {
        RUN_OVERWORLD_SCRIPT(callnative AveronScriptedBattle_Begin, requests_effects=1;);
        SetMoney(&gSaveBlock1Ptr->money, START_MONEY);
        PLAYER(SPECIES_WOBBUFFET) { HP(lose ? 1 : 60); Speed(lose ? 1 : 100); Moves(lose ? MOVE_SPLASH : MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(lose ? 100 : 1); Speed(lose ? 100 : 1); Moves(MOVE_TACKLE); }
    } WHEN {
        if (lose)
            TURN { MOVE(player, MOVE_SPLASH); EXPECT_MOVE(opponent, MOVE_TACKLE); }
        else
            TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        if (lose)
            NOT MESSAGE("You have no more Pokémon that can fight!\p");
        else
            MESSAGE("The opposing Wobbuffet fainted!");
    } THEN {
        // Nothing in the battle cleared the flag; only Finish does.
        EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), TRUE);
        gSpecialVar_Result = 0xFF;
        RUN_OVERWORLD_SCRIPT(callnative AveronScriptedBattle_Finish, requests_effects=1;);
        EXPECT_EQ(gSpecialVar_Result, lose);
        EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
        EXPECT_EQ(gBattleOutcome, lose ? B_OUTCOME_LOST : B_OUTCOME_WON);
        if (lose)
            EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
        else
            EXPECT_GT(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
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

AI_SINGLE_BATTLE_TEST("Averon an ordinary loss after a scripted battle whites out and pays money again")
{
    struct ScriptContext ctx = {0};
    GIVEN {
        // A scripted battle that the player won: Begin set the flag, Finish cleared it.
        AveronScriptedBattle_Begin(&ctx);
        gBattleOutcome = B_OUTCOME_WON;
        AveronScriptedBattle_Finish(&ctx);
        SetMoney(&gSaveBlock1Ptr->money, START_MONEY);
        PLAYER(SPECIES_WOBBUFFET) { HP(1); Moves(MOVE_SPLASH); }
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_SPLASH); EXPECT_MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
        MESSAGE("You have no more Pokémon that can fight!\p");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_LOST);
        EXPECT_LT(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
        EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
    }
}

AI_SINGLE_BATTLE_TEST("Averon scripted battle ended by the player's Explosion still counts as a safe defeat")
{
    u32 scripted;
    PARAMETRIZE { scripted = FALSE; }
    PARAMETRIZE { scripted = TRUE; }
    GIVEN {
        ASSUME(IsExplosionMove(MOVE_EXPLOSION));
        if (scripted)
            FLAG_SET(B_FLAG_NO_WHITEOUT);
        SetMoney(&gSaveBlock1Ptr->money, START_MONEY);
        PLAYER(SPECIES_WOBBUFFET) { Speed(100); Moves(MOVE_EXPLOSION); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(1); Speed(1); Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_EXPLOSION); EXPECT_MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("Wobbuffet used Explosion!");
        if (scripted)
            NOT MESSAGE("You have no more Pokémon that can fight!\p");
        else
            MESSAGE("You have no more Pokémon that can fight!\p");
    } THEN {
        EXPECT(gBattleOutcome == B_OUTCOME_LOST || gBattleOutcome == B_OUTCOME_DREW);
        EXPECT_EQ(AveronScriptedBattle_IsPlayerDefeated(gBattleOutcome), TRUE);
        if (scripted)
            EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
        else
            EXPECT_LT(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
    }
}
