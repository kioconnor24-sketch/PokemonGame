#include "global.h"
#include "test/battle.h"
#include "battle_gimmick.h"

SINGLE_BATTLE_TEST("Averon permits a legal held-stone Mega Evolution")
{
    GIVEN {
        PLAYER(SPECIES_CHARIZARD) { Level(36); Item(ITEM_CHARIZARDITE_X); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE, gimmick: GIMMICK_MEGA); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
        MESSAGE("Charizard has Mega Evolved into Mega Charizard!");
    } THEN {
        EXPECT_EQ(player->species, SPECIES_CHARIZARD_MEGA_X);
        EXPECT_EQ(player->ability, ABILITY_TOUGH_CLAWS);
    }
}

SINGLE_BATTLE_TEST("Averon rejects all excluded gimmicks for both battlers")
{
    GIVEN {
        PLAYER(SPECIES_CHARIZARD) { Item(ITEM_CHARIZARDITE_X); }
        OPPONENT(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); }
    } THEN {
        for (u32 battler = 0; battler < gBattlersCount; ++battler)
        {
            EXPECT_EQ(CanActivateGimmick(battler, GIMMICK_MEGA), TRUE);
            EXPECT_EQ(CanActivateGimmick(battler, GIMMICK_ULTRA_BURST), FALSE);
            EXPECT_EQ(CanActivateGimmick(battler, GIMMICK_Z_MOVE), FALSE);
            EXPECT_EQ(CanActivateGimmick(battler, GIMMICK_DYNAMAX), FALSE);
            EXPECT_EQ(CanActivateGimmick(battler, GIMMICK_TERA), FALSE);
        }
    }
}

SINGLE_BATTLE_TEST("Averon uses Set mode even when an old save requests Shift")
{
    GIVEN {
        gSaveBlock2Ptr->optionsBattleStyle = OPTIONS_BATTLE_STYLE_SHIFT;
        PLAYER(SPECIES_WOBBUFFET) { Speed(100); }
        PLAYER(SPECIES_SENTRET) { Speed(100); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(1); HP(1); }
        OPPONENT(SPECIES_WYNAUT) { Speed(1); }
    } WHEN {
        TURN { MOVE(player, MOVE_SCRATCH); SEND_OUT(opponent, 1); }
        TURN { MOVE(player, MOVE_CELEBRATE); }
    } THEN {
        EXPECT_EQ(gBattleScripting.battleStyle, OPTIONS_BATTLE_STYLE_SET);
        EXPECT_EQ((u32)gSaveBlock2Ptr->optionsBattleStyle, OPTIONS_BATTLE_STYLE_SHIFT);
        EXPECT_EQ(player->species, SPECIES_WOBBUFFET);
        EXPECT_EQ(opponent->species, SPECIES_WYNAUT);
    }
}
