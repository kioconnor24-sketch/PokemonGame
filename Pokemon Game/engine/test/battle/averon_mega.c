#include "global.h"
#include "test/battle.h"

// Mega Evolution is Averon's only allowed battle gimmick. These cover its
// restrictions in real battles: the matching stone only, one per trainer per
// battle, persistence through switching, and Rayquaza's move-based Mega.
// Reverting after battle is covered in averon_pokemon_readiness.c.

SINGLE_BATTLE_TEST("Averon Mega: a Mega Stone for another species does nothing")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_CHARIZARDITE_X); Speed(100); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); }
    } SCENE {
        NOT ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
    } THEN {
        EXPECT_EQ(player->species, SPECIES_VENUSAUR);
    }
}

DOUBLE_BATTLE_TEST("Averon Mega: only one Pokemon per trainer can Mega Evolve in a battle")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); Speed(100); Moves(MOVE_CELEBRATE); }
        PLAYER(SPECIES_BLASTOISE) { Item(ITEM_BLASTOISINITE); Speed(90); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        // The battle menu also blocks a same-turn second request (it checks the
        // partner's queued Mega); the test runner sets requests directly, so
        // only the request after activation is tested here.
        TURN { MOVE(playerLeft, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_CELEBRATE); MOVE(playerRight, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, playerLeft);
        NOT ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, playerRight);
    } THEN {
        EXPECT_EQ(playerLeft->species, SPECIES_VENUSAUR_MEGA);
        EXPECT_EQ(playerRight->species, SPECIES_BLASTOISE);
    }
}

SINGLE_BATTLE_TEST("Averon Mega: a Mega Evolved Pokemon stays Mega after switching out and back")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); Speed(100); Moves(MOVE_CELEBRATE); }
        PLAYER(SPECIES_WOBBUFFET) { Speed(100); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); }
        TURN { SWITCH(player, 1); }
        TURN { SWITCH(player, 0); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
    } THEN {
        EXPECT_EQ(player->species, SPECIES_VENUSAUR_MEGA);
    }
}

SINGLE_BATTLE_TEST("Averon Mega: Rayquaza Mega Evolves through Dragon Ascent without a stone")
{
    u32 move;
    PARAMETRIZE { move = MOVE_DRAGON_ASCENT; }
    PARAMETRIZE { move = MOVE_CELEBRATE; }
    GIVEN {
        PLAYER(SPECIES_RAYQUAZA) { Speed(100); Moves(move); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, move, gimmick: GIMMICK_MEGA); }
    } THEN {
        EXPECT_EQ(player->species, move == MOVE_DRAGON_ASCENT ? SPECIES_RAYQUAZA_MEGA : SPECIES_RAYQUAZA);
    }
}
