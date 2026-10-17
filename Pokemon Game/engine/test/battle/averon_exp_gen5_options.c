#include "global.h"
#include "test/battle.h"
#include "event_data.h"

// Decision support for the owner's "Gen 5 EXP" requirement (#46 comment
// 6212628111). Averon currently uses GEN_LATEST for both options below; these
// tests prove what each choice actually does in a real battle, so either
// answer is a tested one-line change in config/battle.h (protected). Nothing
// here changes the configuration the game uses. Caps are lifted so they do
// not hide the difference.

static const u16 sCapFlags[] =
{
    FLAG_BADGE01_GET, FLAG_BADGE02_GET, FLAG_BADGE03_GET, FLAG_BADGE04_GET,
    FLAG_BADGE05_GET, FLAG_BADGE06_GET, FLAG_BADGE07_GET, FLAG_BADGE08_GET,
    FLAG_AVERON_ASSAULT_COMPLETE, FLAG_IS_CHAMPION,
};

static void LiftCaps(bool32 lift)
{
    for (u32 j = 0; j < ARRAY_COUNT(sCapFlags); j++)
    {
        if (lift)
            FlagSet(sCapFlags[j]);
        else
            FlagClear(sCapFlags[j]);
    }
}

static s32 ExpGained(u32 slot, enum Species species, u32 level)
{
    return GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_EXP)
         - gExperienceTables[gSpeciesInfo[species].growthRate][level];
}

// B_TRAINER_EXP_MULTIPLIER: Gen 5 gives 1.5x for a trainer's Pokemon,
// GEN_LATEST does not. Checked with a held EXP Share on the bench, so the
// Gen 5 split still applies to the boosted total.
AI_SINGLE_BATTLE_TEST("Averon EXP options: Gen 5 trainer bonus is 1.5x and reaches the EXP Share holder", s32 lead, s32 holder)
{
    u32 config = GEN_LATEST;
    PARAMETRIZE { config = GEN_LATEST; }
    PARAMETRIZE { config = GEN_5; }
    GIVEN {
        WITH_CONFIG(B_TRAINER_EXP_MULTIPLIER, config);
        LiftCaps(TRUE);
        PLAYER(SPECIES_WOBBUFFET) { Level(20); Moves(MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(20); Item(ITEM_EXP_SHARE); }
        OPPONENT(SPECIES_BLISSEY) { Level(30); HP(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The opposing Blissey fainted!");
    } THEN {
        results[i].lead = ExpGained(0, SPECIES_WOBBUFFET, 20);
        results[i].holder = ExpGained(1, SPECIES_WOBBUFFET, 20);
        LiftCaps(FALSE);
    } FINALLY {
        EXPECT_GT(results[0].lead, 0);
        EXPECT_GT(results[0].holder, 0);
        // 1.5x, allowing integer rounding in the split and level scaling.
        EXPECT_GE(results[1].lead * 2, results[0].lead * 3 - 4);
        EXPECT_LE(results[1].lead * 2, results[0].lead * 3 + 4);
        EXPECT_GE(results[1].holder * 2, results[0].holder * 3 - 4);
        EXPECT_LE(results[1].holder * 2, results[0].holder * 3 + 4);
    }
}

// B_UNEVOLVED_EXP_MULTIPLIER: GEN_LATEST gives about 1.2x (4915/4096) to a
// Pokemon at or past the level where it could have evolved; Gen 5 does not.
WILD_BATTLE_TEST("Averon EXP options: the Gen 6+ unevolved bonus applies only after the evolution level", s32 exp)
{
    u32 config = GEN_LATEST, level = 20;
    PARAMETRIZE { config = GEN_LATEST; level = 20; } // Charmander evolves at 16
    PARAMETRIZE { config = GEN_5;      level = 20; }
    PARAMETRIZE { config = GEN_LATEST; level = 15; } // not yet able to evolve
    PARAMETRIZE { config = GEN_5;      level = 15; }
    GIVEN {
        WITH_CONFIG(B_UNEVOLVED_EXP_MULTIPLIER, config);
        LiftCaps(TRUE);
        PLAYER(SPECIES_CHARMANDER) { Level(level); Moves(MOVE_SCRATCH); Item(ITEM_EVERSTONE); }
        OPPONENT(SPECIES_BLISSEY) { Level(25); HP(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_SCRATCH); }
    } SCENE {
        MESSAGE("The wild Blissey fainted!");
    } THEN {
        results[i].exp = ExpGained(0, SPECIES_CHARMANDER, level);
        LiftCaps(FALSE);
    } FINALLY {
        // Past the evolution level: latest is about 1.2x Gen 5.
        EXPECT_GE(results[0].exp * 4096, results[1].exp * 4915 - 4096 * 2);
        EXPECT_LE(results[0].exp * 4096, results[1].exp * 4915 + 4096 * 2);
        EXPECT_GT(results[0].exp, results[1].exp);
        // Below it, the two configurations agree.
        EXPECT_EQ(results[2].exp, results[3].exp);
    }
}
