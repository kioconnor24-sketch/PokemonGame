#include "global.h"
#include "test/battle.h"
#include "event_data.h"
#include "money.h"

// Averon uses B_WHITEOUT_MONEY = GEN_LATEST: a normal loss drops
// badge-based money (8, 16, 24, 36, 48, 64, 80, 100 or 120 per level of the
// highest-level party Pokemon), never more than the player has. Upstream
// marks this config "TODO: use in tests". The two-region work changes how
// badges are counted, so these pin the current behaviour.

static void SetBadges(u32 count)
{
    for (u32 i = 0; i < NUM_BADGES; i++)
    {
        if (i < count)
            FlagSet(gBadgeFlags[i]);
        else
            FlagClear(gBadgeFlags[i]);
    }
}

AI_SINGLE_BATTLE_TEST("Averon whiteout money: a loss drops badge rate times the highest party level", u32 lost)
{
    u32 badges = 0, expected = 0;
    PARAMETRIZE { badges = 0; expected = 8 * 40; }
    PARAMETRIZE { badges = 1; expected = 16 * 40; }
    PARAMETRIZE { badges = 4; expected = 48 * 40; }
    PARAMETRIZE { badges = 8; expected = 120 * 40; }
    GIVEN {
        SetBadges(badges);
        SetMoney(&gSaveBlock1Ptr->money, 50000);
        PLAYER(SPECIES_WOBBUFFET) { Level(20); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        PLAYER(SPECIES_WYNAUT) { Level(40); HP(0); Speed(1); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(100); Moves(MOVE_SEISMIC_TOSS); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); EXPECT_MOVE(opponent, MOVE_SEISMIC_TOSS); }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_LOST);
        EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), 50000 - expected);
        SetBadges(0);
    }
}

AI_SINGLE_BATTLE_TEST("Averon whiteout money: a loss never takes more money than the player has")
{
    GIVEN {
        SetBadges(8);
        SetMoney(&gSaveBlock1Ptr->money, 100);
        PLAYER(SPECIES_WOBBUFFET) { Level(100); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(100); Moves(MOVE_SEISMIC_TOSS); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); EXPECT_MOVE(opponent, MOVE_SEISMIC_TOSS); }
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_LOST);
        EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), 0);
        SetBadges(0);
    }
}

WILD_BATTLE_TEST("Averon whiteout money: losing to a wild Pokemon also drops badge-based money")
{
    GIVEN {
        SetBadges(2);
        SetMoney(&gSaveBlock1Ptr->money, 5000);
        PLAYER(SPECIES_WOBBUFFET) { Level(30); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(100); Moves(MOVE_SEISMIC_TOSS); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); MOVE(opponent, MOVE_SEISMIC_TOSS); }
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_LOST);
        EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), 5000 - 24 * 30);
        SetBadges(0);
    }
}
