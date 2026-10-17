#include "global.h"
#include "test/battle.h"
#include "averon_region_progression.h"
#include "caps.h"
#include "event_data.h"

// TESTING-only input, not a proposal for Sinnoh's production cap ladder.
// Existing suites test regional caps with one battler and held EXP Share
// against Averon's cap separately. Here the inactive holder is at the active
// region's cap while the six-member party's participant can still gain EXP.
static const struct AveronProgressionProfile sProfile =
{
    .levelCaps = {11, 15, 15, 15, 15, 15, 15, 15, 15},
    .obedienceLevels = {MAX_LEVEL, MAX_LEVEL, MAX_LEVEL, MAX_LEVEL, MAX_LEVEL,
                        MAX_LEVEL, MAX_LEVEL, MAX_LEVEL, MAX_LEVEL},
};

static void ResetProgression(void)
{
    AveronProgression_ResetTestBadgeRule();
    AveronProgression_SetTestProfile(AVERON_SAVE_REGION_AVERON, NULL);
    AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, NULL);
    AveronRegionSave_InitNewGame();
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
        AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, FALSE);
    FlagClear(FLAG_AVERON_ASSAULT_COMPLETE);
    FlagClear(FLAG_IS_CHAMPION);
}

static u32 EarnedExp(u32 slot, u32 level)
{
    return GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_EXP)
         - gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][level];
}

WILD_BATTLE_TEST("Averon regional EXP Share keeps a capped holder's pool separate in a six-member party", u32 leadExp, u32 holderExp)
{
    u32 region = AVERON_SAVE_REGION_SINNOH;
    u32 badges = 0;
    enum Item heldItem = ITEM_EXP_SHARE;
    PARAMETRIZE { } // Sinnoh cap 11: holder is capped, participant is not.
    PARAMETRIZE { badges = 1; } // Sinnoh cap 15: both can gain.
    PARAMETRIZE { region = AVERON_SAVE_REGION_AVERON; } // Averon Champion: cap 100.
    PARAMETRIZE { heldItem = ITEM_NONE; } // No holder: participant gets the whole pool.

    GIVEN {
        ResetProgression();
        AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &sProfile);
        for (u32 badge = 1; badge <= AVERON_REGION_BADGES; ++badge)
        {
            AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, TRUE);
            AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, badge <= badges);
        }
        FlagSet(FLAG_AVERON_ASSAULT_COMPLETE);
        FlagSet(FLAG_IS_CHAMPION);
        AveronRegion_SetActive(region);

        PLAYER(SPECIES_WOBBUFFET) { Level(10); Speed(100); Moves(MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(11); Item(heldItem); }
        PLAYER(SPECIES_WOBBUFFET) { Level(10); }
        PLAYER(SPECIES_WOBBUFFET) { Level(10); }
        PLAYER(SPECIES_WOBBUFFET) { Level(10); }
        PLAYER(SPECIES_WOBBUFFET) { Level(10); }
        OPPONENT(SPECIES_CATERPIE) { Level(10); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The wild Caterpie fainted!");
        NOT MESSAGE("The rest of your team gained EXP. Points thanks to the Exp. Share!");
    } THEN {
        EXPECT_EQ(CalculatePlayerPartyCount(), PARTY_SIZE);
        EXPECT_EQ(AveronProgression_GetActiveRegion(), region);
        EXPECT_EQ(AveronRegion_CountBadges(AVERON_SAVE_REGION_AVERON), AVERON_REGION_BADGES);
        EXPECT_EQ(AveronRegion_CountBadges(AVERON_SAVE_REGION_SINNOH), badges);
        EXPECT_EQ(GetCurrentLevelCap(), region == AVERON_SAVE_REGION_AVERON ? MAX_LEVEL : sProfile.levelCaps[badges]);
        results[i].leadExp = EarnedExp(0, 10);
        results[i].holderExp = EarnedExp(1, 11);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_LEVEL), 10);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_LEVEL), 11);
        for (u32 slot = 0; slot < PARTY_SIZE; ++slot)
        {
            EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HELD_ITEM),
                      slot == 1 ? heldItem : ITEM_NONE);
            if (slot >= 2)
                EXPECT_EQ(EarnedExp(slot, 10), 0);
        }
        ResetProgression();
    } FINALLY {
        ResetProgression();
        EXPECT_GT(results[0].leadExp, 0);
        EXPECT_EQ(results[0].holderExp, 0);
        EXPECT_GT(results[1].holderExp, 0);
        EXPECT_EQ(results[1].holderExp, results[2].holderExp);
        EXPECT_EQ(results[3].holderExp, 0);

        // The capped holder still owns its half of the Gen V pool. Its
        // inability to gain EXP does not redistribute that half to the lead.
        EXPECT_EQ(results[0].leadExp, results[1].leadExp);
        EXPECT_EQ(results[0].leadExp, results[2].leadExp);
        EXPECT_GT(results[3].leadExp, results[0].leadExp);
        EXPECT_LE(abs((s32)results[3].leadExp - 2 * (s32)results[0].leadExp), 2);
    }
}
