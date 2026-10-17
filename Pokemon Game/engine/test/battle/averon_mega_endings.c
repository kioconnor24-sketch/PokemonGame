#include "global.h"
#include "test/battle.h"
#include "battle_gimmick.h"

// The existing readiness test covers the base form after a won battle. These
// cover the other ways a battle with a Mega Evolved Pokemon can end, and the
// one-Mega rule after the Mega Evolved Pokemon is gone.

static void ExpectPartyVenusaurReverted(u32 slot)
{
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_SPECIES), SPECIES_VENUSAUR);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HELD_ITEM), ITEM_VENUSAURITE);
}

WILD_BATTLE_TEST("Averon Mega endings: the Pokemon reverts when the player Teleports away")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); Moves(MOVE_TELEPORT); }
        OPPONENT(SPECIES_WOBBUFFET) { Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TELEPORT, gimmick: GIMMICK_MEGA); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_PLAYER_TELEPORTED);
        ExpectPartyVenusaurReverted(0);
    }
}

WILD_BATTLE_TEST("Averon Mega endings: the Pokemon reverts when a wild Pokemon blows the player away")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); Level(50); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_HO_OH) { Level(70); Moves(MOVE_WHIRLWIND); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); MOVE(opponent, MOVE_WHIRLWIND); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
    } THEN {
        EXPECT_NE(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_NE(gBattleOutcome, 0);
        ExpectPartyVenusaurReverted(0);
    }
}

SINGLE_BATTLE_TEST("Averon Mega endings: a Mega Evolved Pokemon that faints is in base form after a win")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        PLAYER(SPECIES_WOBBUFFET) { Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(1); Speed(50); Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); MOVE(opponent, MOVE_TACKLE); SEND_OUT(player, 1); }
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
        MESSAGE("Venusaur fainted!");
        MESSAGE("The opposing Wobbuffet fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), 0);
        ExpectPartyVenusaurReverted(0);
    }
}

SINGLE_BATTLE_TEST("Averon Mega endings: the Pokemon reverts when the player loses the battle")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(50); Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
        MESSAGE("Venusaur fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_LOST);
        ExpectPartyVenusaurReverted(0);
    }
}

SINGLE_BATTLE_TEST("Averon Mega endings: no second Mega Evolution after the first Mega Pokemon faints")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        PLAYER(SPECIES_CHARIZARD) { Item(ITEM_CHARIZARDITE_X); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(50); Moves(MOVE_TACKLE, MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); MOVE(opponent, MOVE_TACKLE); SEND_OUT(player, 1); }
        TURN { MOVE(player, MOVE_CELEBRATE); MOVE(opponent, MOVE_CELEBRATE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
        MESSAGE("Venusaur fainted!");
        NONE_OF { ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player); }
    } THEN {
        EXPECT_EQ(player->species, SPECIES_CHARIZARD);
        EXPECT_EQ(CanActivateGimmick(GetBattlerAtPosition(B_POSITION_PLAYER_LEFT), GIMMICK_MEGA), FALSE);
    }
}
