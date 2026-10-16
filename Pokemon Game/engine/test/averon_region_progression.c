#include "global.h"
#include "test/battle.h"
#include "averon_region_progression.h"
#include "battle_util.h"
#include "caps.h"
#include "event_data.h"
#include "load_save.h"
#include "save.h"
#include "constants/battle.h"

// Region-aware progression (averon_region_progression.c). The profile below
// is a TEST PARAMETER, deliberately unlike any real progression: it is not a
// Sinnoh cap or obedience proposal. Sinnoh's numbers are owner-reserved.
static const struct AveronProgressionProfile sTestProfile =
{
    .levelCaps       = { 11, 12, 13, 14, 15, 16, 17, 18, 19 },
    .obedienceLevels = { 21, 22, 23, 24, 25, 26, 27, 28, MAX_LEVEL },
};

// The existing Averon ladders, as caps.c and GetAttackerObedienceForAction
// have them today, indexed by the number of Averon badges in order.
static const u8 sAveronCaps[] = { 15, 23, 31, 39, 47, 55, 62, 69 };

static void SetAveronBadges(u32 count)
{
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; badge++)
        AveronRegion_SetBadge(AVERON_SAVE_REGION_AVERON, badge, badge <= count);
}

static void SetSinnohBadges(u32 count)
{
    for (u32 badge = 1; badge <= AVERON_REGION_BADGES; badge++)
        AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, badge, badge <= count);
}

static void ResetProgression(void)
{
    AveronProgression_SetTestProfile(AVERON_SAVE_REGION_AVERON, NULL);
    AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, NULL);
    AveronRegionSave_InitNewGame();
    SetAveronBadges(0);
    FlagClear(FLAG_AVERON_ASSAULT_COMPLETE);
    FlagClear(FLAG_IS_CHAMPION);
}

static u32 ExpectedAveronCap(u32 badges, bool32 assault, bool32 champion)
{
    if (badges < ARRAY_COUNT(sAveronCaps))
        return sAveronCaps[badges];
    if (!assault)
        return 72;
    if (!champion)
        return 76;
    return MAX_LEVEL;
}

TEST("Averon region progression: with no regional profile both regions keep today's level caps")
{
    u32 i = 0;
    PARAMETRIZE { i = 0; }
    PARAMETRIZE { i = 1; }
    u32 region = i == 0 ? AVERON_SAVE_REGION_AVERON : AVERON_SAVE_REGION_SINNOH;

    ResetProgression();
    EXPECT(AveronRegion_SetActive(region));
    for (u32 badges = 0; badges <= AVERON_REGION_BADGES; badges++)
    {
        SetAveronBadges(badges);
        SetSinnohBadges(AVERON_REGION_BADGES - badges);
        EXPECT_EQ(GetCurrentLevelCap(), ExpectedAveronCap(badges, FALSE, FALSE));
    }
    FlagSet(FLAG_AVERON_ASSAULT_COMPLETE);
    EXPECT_EQ(GetCurrentLevelCap(), ExpectedAveronCap(8, TRUE, FALSE));
    FlagSet(FLAG_IS_CHAMPION);
    EXPECT_EQ(GetCurrentLevelCap(), ExpectedAveronCap(8, TRUE, TRUE));
    ResetProgression();
}

TEST("Averon region progression: a Sinnoh profile reads only the Sinnoh badge bank")
{
    ResetProgression();
    EXPECT(AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &sTestProfile));
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));

    // Every Averon badge and the Averon postgame flags change nothing in Sinnoh.
    SetAveronBadges(AVERON_REGION_BADGES);
    FlagSet(FLAG_AVERON_ASSAULT_COMPLETE);
    FlagSet(FLAG_IS_CHAMPION);
    for (u32 badges = 0; badges <= AVERON_REGION_BADGES; badges++)
    {
        SetSinnohBadges(badges);
        u32 obedience = 0;
        EXPECT_EQ(AveronProgression_CountActiveRegionBadges(), badges);
        EXPECT_EQ(GetCurrentLevelCap(), sTestProfile.levelCaps[badges]);
        EXPECT(AveronProgression_GetRegionalObedienceLevel(&obedience));
        EXPECT_EQ(obedience, sTestProfile.obedienceLevels[badges]);
    }

    // Back in Averon, the Averon ladder applies again with the same flags.
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_AVERON));
    EXPECT_EQ(GetCurrentLevelCap(), MAX_LEVEL);
    EXPECT_EQ(AveronProgression_CountActiveRegionBadges(), AVERON_REGION_BADGES);
    ResetProgression();
}

TEST("Averon region progression: out-of-range profiles are refused and the previous one stays")
{
    struct AveronProgressionProfile bad = sTestProfile;
    ResetProgression();
    EXPECT(AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &sTestProfile));

    bad.levelCaps[3] = 0;
    EXPECT(!AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &bad));
    bad = sTestProfile;
    bad.levelCaps[8] = MAX_LEVEL + 1;
    EXPECT(!AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &bad));
    bad = sTestProfile;
    bad.obedienceLevels[0] = 0;
    EXPECT(!AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &bad));
    bad = sTestProfile;
    bad.obedienceLevels[5] = MAX_LEVEL + 1;
    EXPECT(!AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &bad));
    EXPECT(!AveronProgression_SetTestProfile(AVERON_SAVE_REGION_NONE, &sTestProfile));
    EXPECT(!AveronProgression_SetTestProfile(AVERON_SAVE_REGION_COUNT, &sTestProfile));
    EXPECT(!AveronProgression_IsProfileValid(NULL));

    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    SetSinnohBadges(2);
    EXPECT_EQ(GetCurrentLevelCap(), sTestProfile.levelCaps[2]);

    // An invalid active region falls back to today's behaviour.
    EXPECT(!AveronRegion_SetActive(AVERON_SAVE_REGION_COUNT));
    EXPECT(!AveronRegion_SetActive(AVERON_SAVE_REGION_NONE));
    EXPECT_EQ(AveronProgression_GetActiveRegion(), AVERON_SAVE_REGION_SINNOH);
    ResetProgression();
}

TEST("Averon region progression: the active region and Sinnoh badges survive a flash save")
{
    CheckForFlashMemory();
    ASSUME(gFlashMemoryPresent);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    ResetProgression();
    EXPECT(AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &sTestProfile));
    SetAveronBadges(AVERON_REGION_BADGES);
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    SetSinnohBadges(3);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);

    AveronRegionSave_InitNewGame();
    SetAveronBadges(0);
    EXPECT_EQ(AveronProgression_GetActiveRegion(), AVERON_SAVE_REGION_AVERON);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronProgression_GetActiveRegion(), AVERON_SAVE_REGION_SINNOH);
    EXPECT_EQ(AveronProgression_CountActiveRegionBadges(), 3);
    EXPECT_EQ(GetCurrentLevelCap(), sTestProfile.levelCaps[3]);
    ResetProgression();
}

// The real EXP path uses the regional cap: at the cap no EXP, below it EXP.
WILD_BATTLE_TEST("Averon region progression: a Sinnoh profile's cap limits EXP in a real battle", s32 exp)
{
    u32 badges = 0;
    PARAMETRIZE { badges = 0; } // cap 11: the level-11 Pokemon is at it
    PARAMETRIZE { badges = 4; } // cap 15: below it
    GIVEN {
        ResetProgression();
        AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &sTestProfile);
        AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH);
        SetAveronBadges(AVERON_REGION_BADGES);
        FlagSet(FLAG_IS_CHAMPION);
        FlagSet(FLAG_AVERON_ASSAULT_COMPLETE);
        SetSinnohBadges(badges);
        PLAYER(SPECIES_WOBBUFFET) { Level(11); }
        OPPONENT(SPECIES_CATERPIE) { Level(10); HP(1); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The wild Caterpie fainted!");
    } THEN {
        results[i].exp = GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP)
                       - gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][11];
        ResetProgression();
    } FINALLY {
        EXPECT_EQ(results[0].exp, 0);
        EXPECT_GT(results[1].exp, 0);
    }
}

// The real obedience check uses the regional obedience level. Under
// B_OBEDIENCE_MECHANICS Gen 8+, a Pokemon is judged by the level it was met at.
WILD_BATTLE_TEST("Averon region progression: a Sinnoh profile's obedience level is the one the battle uses")
{
    GIVEN {
        ResetProgression();
        AveronProgression_SetTestProfile(AVERON_SAVE_REGION_SINNOH, &sTestProfile);
        AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH);
        SetAveronBadges(AVERON_REGION_BADGES); // Averon's ladder would obey all
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); }
    } THEN {
        u32 disobeyed = 0;
        // The runner plays every battle as BATTLE_TYPE_RECORDED, and recorded
        // battles always obey; clear it to reach the in-game check.
        u32 savedFlags = gBattleTypeFlags;
        gBattleTypeFlags &= ~BATTLE_TYPE_RECORDED;
        gBattlerAttacker = GetBattlerAtPosition(B_POSITION_PLAYER_LEFT);
        gCurrentMove = MOVE_CELEBRATE;

        // Sinnoh 0 badges: obedience 21. Met at 21 obeys every time.
        SetSinnohBadges(0);
        gBattleMons[gBattlerAttacker].metLevel = 21;
        gBattleMons[gBattlerAttacker].level = 21;
        for (u32 n = 0; n < 32; n++)
            EXPECT_EQ(GetAttackerObedienceForAction(), OBEYS);

        // Met at 90, it does not always obey.
        gBattleMons[gBattlerAttacker].metLevel = 90;
        gBattleMons[gBattlerAttacker].level = 90;
        for (u32 n = 0; n < 32; n++)
            disobeyed += GetAttackerObedienceForAction() != OBEYS;
        EXPECT_GT(disobeyed, 0);

        // All eight Sinnoh badges: the profile's MAX_LEVEL means every level obeys.
        SetSinnohBadges(AVERON_REGION_BADGES);
        for (u32 n = 0; n < 32; n++)
            EXPECT_EQ(GetAttackerObedienceForAction(), OBEYS);

        // In Averon with all eight Averon badges, the original ladder obeys too.
        SetSinnohBadges(0);
        AveronRegion_SetActive(AVERON_SAVE_REGION_AVERON);
        for (u32 n = 0; n < 32; n++)
            EXPECT_EQ(GetAttackerObedienceForAction(), OBEYS);
        gBattleTypeFlags = savedFlags;
        ResetProgression();
    }
}
