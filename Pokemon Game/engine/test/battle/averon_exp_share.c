#include "global.h"
#include "test/battle.h"
#include "event_data.h"

// Averon uses the Generation 5 held-item EXP Share (I_EXP_SHARE_ITEM GEN_5,
// no party-wide flag) with Generation 5 splitting (B_SPLIT_EXP GEN_5):
// with at least one holder, the Pokemon that were sent out share half the
// EXP and the holders share the other half; a sent-out holder gets both.
// Without a holder, the sent-out Pokemon share all of it. Nobody else gets
// any. Every Averon level cap is lifted here so caps do not mask the split;
// caps have their own tests (averon_exp.c, averon_pokemon_readiness.c).

static const u16 sCapFlags[] =
{
    FLAG_BADGE01_GET, FLAG_BADGE02_GET, FLAG_BADGE03_GET, FLAG_BADGE04_GET,
    FLAG_BADGE05_GET, FLAG_BADGE06_GET, FLAG_BADGE07_GET, FLAG_BADGE08_GET,
    FLAG_AVERON_ASSAULT_COMPLETE, FLAG_IS_CHAMPION,
};

static void LiftCaps(bool32 lift)
{
    for (u32 i = 0; i < ARRAY_COUNT(sCapFlags); i++)
    {
        if (lift)
            FlagSet(sCapFlags[i]);
        else
            FlagClear(sCapFlags[i]);
    }
}

static u32 ExpGained(u32 slot, u32 startLevel)
{
    return GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_EXP)
         - gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][startLevel];
}

#define LEVEL 30

// The Gen 5+ scaled formula adds 1 after scaling, so a split share can be one
// point above the exact fraction.
#define EXPECT_ABOUT(a, b) EXPECT_LE(abs((s32)(a) - (s32)(b)), 1)

// One battle, one knockout, by the lead; the party is set up per case.
WILD_BATTLE_TEST("Averon EXP Share: only participants and holders gain, split half and half", s32 exp0, s32 exp1, s32 exp2, s32 exp3)
{
    u32 item1 = ITEM_NONE, item2 = ITEM_NONE, item0 = ITEM_NONE;
    PARAMETRIZE { }                                                   // 0: lead alone
    PARAMETRIZE { item1 = ITEM_EXP_SHARE; }                           // 1: one holder
    PARAMETRIZE { item1 = ITEM_EXP_SHARE; item2 = ITEM_EXP_SHARE; }   // 2: two holders
    PARAMETRIZE { item0 = ITEM_EXP_SHARE; }                           // 3: lead holds it
    GIVEN {
        LiftCaps(TRUE);
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Item(item0); Speed(100); Moves(MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Item(item1); Speed(100); }
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Item(item2); Speed(100); }
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Speed(100); }
        OPPONENT(SPECIES_BLISSEY) { Level(LEVEL); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The wild Blissey fainted!");
    } THEN {
        results[i].exp0 = ExpGained(0, LEVEL);
        results[i].exp1 = ExpGained(1, LEVEL);
        results[i].exp2 = ExpGained(2, LEVEL);
        results[i].exp3 = ExpGained(3, LEVEL);
        LiftCaps(FALSE);
    } FINALLY {
        s32 full = results[0].exp0;
        EXPECT_GT(full, 0);
        // 0: the lead gets everything; the bench without EXP Share gets nothing.
        EXPECT_EQ(results[0].exp1, 0);
        EXPECT_EQ(results[0].exp2, 0);
        EXPECT_EQ(results[0].exp3, 0);
        // 1: lead and holder get half each; the others nothing.
        EXPECT_ABOUT(results[1].exp0, full / 2);
        EXPECT_ABOUT(results[1].exp1, full / 2);
        EXPECT_EQ(results[1].exp2, 0);
        EXPECT_EQ(results[1].exp3, 0);
        // 2: the holders share their half.
        EXPECT_ABOUT(results[2].exp0, full / 2);
        EXPECT_ABOUT(results[2].exp1, full / 2 / 2);
        EXPECT_ABOUT(results[2].exp2, full / 2 / 2);
        EXPECT_EQ(results[2].exp3, 0);
        // 3: a participating holder gets both halves; it is not party-wide.
        EXPECT_ABOUT(results[3].exp0, full / 2 + full / 2);
        EXPECT_EQ(results[3].exp1, 0);
        EXPECT_EQ(results[3].exp3, 0);
    }
}

// Switching: both Pokemon that faced the opponent share the EXP.
WILD_BATTLE_TEST("Averon EXP Share: Pokemon switched in against the opponent share its EXP", s32 exp0, s32 exp1)
{
    u32 switched;
    PARAMETRIZE { switched = FALSE; }
    PARAMETRIZE { switched = TRUE; }
    GIVEN {
        LiftCaps(TRUE);
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Speed(100); Moves(MOVE_TACKLE, MOVE_CELEBRATE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_BLISSEY) { Level(LEVEL); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        if (switched)
        {
            TURN { SWITCH(player, 1); }
            TURN { MOVE(player, MOVE_TACKLE); }
        }
        else
        {
            TURN { MOVE(player, MOVE_CELEBRATE); }
            TURN { MOVE(player, MOVE_TACKLE); }
        }
    } SCENE {
        MESSAGE("The wild Blissey fainted!");
    } THEN {
        results[i].exp0 = ExpGained(0, LEVEL);
        results[i].exp1 = ExpGained(1, LEVEL);
        LiftCaps(FALSE);
    } FINALLY {
        s32 full = results[0].exp0;
        EXPECT_GT(full, 0);
        EXPECT_EQ(results[0].exp1, 0);
        EXPECT_ABOUT(results[1].exp0, full / 2);
        EXPECT_ABOUT(results[1].exp1, full / 2);
    }
}

// A participant that fainted before the knockout gets nothing; the EXP goes
// to the Pokemon still standing.
AI_SINGLE_BATTLE_TEST("Averon EXP Share: a participant that fainted gets no EXP")
{
    GIVEN {
        LiftCaps(TRUE);
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_BLISSEY) { Level(LEVEL); HP(1); Speed(50); Moves(MOVE_POUND); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); EXPECT_MOVE(opponent, MOVE_POUND); SEND_OUT(player, 1); }
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
        MESSAGE("The opposing Blissey fainted!");
    } THEN {
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), 0);
        EXPECT_EQ(ExpGained(0, LEVEL), 0);
        EXPECT_GT(ExpGained(1, LEVEL), 0);
        LiftCaps(FALSE);
    }
}

// Gen 7+ trainer multiplier: a trainer's Pokemon gives the same EXP as a
// wild one (no 1.5x).
AI_SINGLE_BATTLE_TEST("Averon EXP Share: a trainer's Pokemon gives the same EXP as a wild one", s32 exp)
{
    PARAMETRIZE { }
    GIVEN {
        LiftCaps(TRUE);
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_BLISSEY) { Level(LEVEL); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The opposing Blissey fainted!");
    } THEN {
        u32 yield = gSpeciesInfo[SPECIES_BLISSEY].expYield;
        // Gen 5+ scaling with equal levels: yield * level / 5 * ((2L+10)/(L+L+10))^2.5 = yield * level / 5.
        EXPECT_ABOUT(ExpGained(0, LEVEL), yield * LEVEL / 5);
        LiftCaps(FALSE);
    }
}

// Gen 5+ scaling: a lower-level Pokemon gains more from the same opponent,
// a higher-level one less.
WILD_BATTLE_TEST("Averon EXP Share: EXP is scaled by the level difference", s32 exp)
{
    u32 level;
    PARAMETRIZE { level = LEVEL - 10; }
    PARAMETRIZE { level = LEVEL; }
    PARAMETRIZE { level = LEVEL + 10; }
    GIVEN {
        LiftCaps(TRUE);
        PLAYER(SPECIES_WOBBUFFET) { Level(level); Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_BLISSEY) { Level(LEVEL); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The wild Blissey fainted!");
    } THEN {
        results[i].exp = ExpGained(0, level);
        LiftCaps(FALSE);
    } FINALLY {
        EXPECT_ABOUT(results[1].exp, gSpeciesInfo[SPECIES_BLISSEY].expYield * LEVEL / 5);
        EXPECT_GT(results[0].exp, results[1].exp);
        EXPECT_LT(results[2].exp, results[1].exp);
    }
}

// A holder at level 100, or above the current cap, gets nothing, and the
// participant still gets only its half: the holder's share is not
// redistributed.
WILD_BATTLE_TEST("Averon EXP Share: a holder at level 100 or above the cap gains nothing")
{
    u32 capsLifted;
    PARAMETRIZE { capsLifted = TRUE; }
    PARAMETRIZE { capsLifted = FALSE; }
    GIVEN {
        LiftCaps(capsLifted);
        PLAYER(SPECIES_WOBBUFFET) { Level(10); Speed(100); Moves(MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(capsLifted ? MAX_LEVEL : 20); Item(ITEM_EXP_SHARE); Speed(100); }
        OPPONENT(SPECIES_CATERPIE) { Level(5); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The wild Caterpie fainted!");
    } THEN {
        EXPECT_EQ(ExpGained(1, capsLifted ? MAX_LEVEL : 20), 0);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_LEVEL), capsLifted ? MAX_LEVEL : 20);
        EXPECT_GT(ExpGained(0, 10), 0);
        LiftCaps(FALSE);
    }
}

// Double battle: both Pokemon on the field shared in the knockout.
AI_DOUBLE_BATTLE_TEST("Averon EXP Share: both Pokemon on the field in a double battle share the EXP")
{
    GIVEN {
        LiftCaps(TRUE);
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Speed(100); Moves(MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Speed(100); Moves(MOVE_CELEBRATE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(LEVEL); Speed(100); }
        OPPONENT(SPECIES_BLISSEY) { Level(LEVEL); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_BLISSEY) { Level(LEVEL); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentLeft); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentRight); MOVE(playerRight, MOVE_CELEBRATE); }
    } SCENE {
        MESSAGE("The opposing Blissey fainted!");
    } THEN {
        u32 perKnockout = gSpeciesInfo[SPECIES_BLISSEY].expYield * LEVEL / 5;
        EXPECT_EQ(ExpGained(0, LEVEL), ExpGained(1, LEVEL));
        EXPECT_LE(abs((s32)ExpGained(0, LEVEL) - (s32)perKnockout), 2);
        EXPECT_EQ(ExpGained(2, LEVEL), 0);
        LiftCaps(FALSE);
    }
}
