#include "global.h"
#include "test/battle.h"

// Locked Averon battle rules (root AGENTS.md): Mega Evolution stays;
// Primal Reversion, Z-Moves, Dynamax, Terastallization and Ultra Burst are off.

SINGLE_BATTLE_TEST("Averon Groudon and Kyogre holding their orbs do not undergo Primal Reversion")
{
    GIVEN {
        PLAYER(SPECIES_GROUDON) { Item(ITEM_RED_ORB); }
        OPPONENT(SPECIES_KYOGRE) { Item(ITEM_BLUE_ORB); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); MOVE(opponent, MOVE_CELEBRATE); }
    } SCENE {
        NONE_OF {
            ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_PRIMAL_REVERSION, player);
            ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_PRIMAL_REVERSION, opponent);
            MESSAGE("Groudon's Primal Reversion! It reverted to its primal state!");
            MESSAGE("The opposing Kyogre's Primal Reversion! It reverted to its primal state!");
        }
    } THEN {
        EXPECT_EQ(player->species, SPECIES_GROUDON);
        EXPECT_EQ(opponent->species, SPECIES_KYOGRE);
    }
}

SINGLE_BATTLE_TEST("Averon orb holders switched in mid-battle do not undergo Primal Reversion")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET);
        PLAYER(SPECIES_GROUDON) { Item(ITEM_RED_ORB); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { SWITCH(player, 1); }
    } SCENE {
        NOT ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_PRIMAL_REVERSION, player);
    } THEN {
        EXPECT_EQ(player->species, SPECIES_GROUDON);
    }
}

SINGLE_BATTLE_TEST("Averon Mega Evolution still works")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
    } THEN {
        EXPECT_EQ(player->species, SPECIES_VENUSAUR_MEGA);
    }
}
