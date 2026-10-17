#include "global.h"
#include "test/battle.h"
#include "test/test.h"
#include "event_data.h"
#include "load_save.h"
#include "pokemon.h"
#include "save.h"
#include "gba/flash_internal.h"

// Additive tests for the boundaries NOT covered by averon_exp_share.c:
// a switched-in holder belongs to both the participation and holder pools,
// while an unused party slot without the item gets nothing. These battles
// intentionally use identical species and levels so scaled EXP is comparable.
#define AVERON_EXP_LEVEL 30
#define EXPECT_EXP_NEAR(actual, expected) EXPECT_LE(abs((s32)(actual) - (s32)(expected)), 3)

static const u16 sAveronExpCapFlags[] =
{
    FLAG_BADGE01_GET, FLAG_BADGE02_GET, FLAG_BADGE03_GET,
    FLAG_BADGE04_GET, FLAG_BADGE05_GET, FLAG_BADGE06_GET,
    FLAG_BADGE07_GET, FLAG_BADGE08_GET,
    FLAG_AVERON_ASSAULT_COMPLETE, FLAG_IS_CHAMPION,
};

static void SetAveronExpCaps(bool32 enable)
{
    for (u32 i = 0; i < ARRAY_COUNT(sAveronExpCapFlags); i++)
    {
        if (enable)
            FlagSet(sAveronExpCapFlags[i]);
        else
            FlagClear(sAveronExpCapFlags[i]);
    }
}

static u32 EarnedExp(u32 slot)
{
    return GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_EXP)
         - gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][AVERON_EXP_LEVEL];
}

WILD_BATTLE_TEST("Averon EXP Share lifecycle: a switched-in holder participates in both Gen 5 pools", u32 lead, u32 switched, u32 bench)
{
    u32 holderSlot = 0; // 0 = no item; 1 = switched-in holder; 2 = inactive holder
    PARAMETRIZE { holderSlot = 0; }
    PARAMETRIZE { holderSlot = 1; }
    PARAMETRIZE { holderSlot = 2; }
    GIVEN {
        SetAveronExpCaps(TRUE);
        PLAYER(SPECIES_WOBBUFFET) { Level(AVERON_EXP_LEVEL); Speed(100); Moves(MOVE_CELEBRATE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(AVERON_EXP_LEVEL); Speed(100); Moves(MOVE_TACKLE); Item(holderSlot == 1 ? ITEM_EXP_SHARE : ITEM_NONE); }
        PLAYER(SPECIES_WOBBUFFET) { Level(AVERON_EXP_LEVEL); Speed(100); Item(holderSlot == 2 ? ITEM_EXP_SHARE : ITEM_NONE); }
        OPPONENT(SPECIES_BLISSEY) { Level(AVERON_EXP_LEVEL); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { SWITCH(player, 1); }
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The wild Blissey fainted!");
    } THEN {
        results[i].lead = EarnedExp(0);
        results[i].switched = EarnedExp(1);
        results[i].bench = EarnedExp(2);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_HELD_ITEM),
                  holderSlot == 1 ? ITEM_EXP_SHARE : ITEM_NONE);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_HELD_ITEM),
                  holderSlot == 2 ? ITEM_EXP_SHARE : ITEM_NONE);
        SetAveronExpCaps(FALSE);
    } FINALLY {
        u32 total = results[0].lead + results[0].switched;
        EXPECT_GT(total, 0);
        EXPECT_EXP_NEAR(results[0].lead, total / 2);
        EXPECT_EXP_NEAR(results[0].switched, total / 2);
        EXPECT_EQ(results[0].bench, 0);

        // Gen 5: half for participation shared by two; half for the
        // one holder. A participating holder therefore earns ~3/4.
        EXPECT_EXP_NEAR(results[1].lead, total / 4);
        EXPECT_EXP_NEAR(results[1].switched, total * 3 / 4);
        EXPECT_EQ(results[1].bench, 0);

        // A nonparticipant holder earns ~1/2; both participants ~1/4.
        EXPECT_EXP_NEAR(results[2].lead, total / 4);
        EXPECT_EXP_NEAR(results[2].switched, total / 4);
        EXPECT_EXP_NEAR(results[2].bench, total / 2);
    }
}

// Saving itself must not grant an EXP Share item to another party member,
// erase earned EXP, or unexpectedly raise the level. This is a persistent
// state round-trip; the actual battle allocation is exercised above.
TEST("Averon EXP Share lifecycle: EXP and held items survive two flash save and load cycles")
{
    u16 share = ITEM_EXP_SHARE, noItem = ITEM_NONE;
    u32 baseline, earnedLead, earnedHolder, earnedBench;
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;

    ClearSaveData();
    Save_ResetSaveCounters();
    ZeroPlayerPartyMons();
    for (u32 i = 0; i < 3; i++)
        CreateMon(&gParties[B_TRAINER_PLAYER][i], SPECIES_WOBBUFFET,
                  AVERON_EXP_LEVEL, 0, OTID_STRUCT_PLAYER_ID);
    CalculatePlayerPartyCount();
    EXPECT_EQ(CalculatePlayerPartyCount(), 3);

    baseline = gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][AVERON_EXP_LEVEL];
    earnedLead = baseline + 100;
    earnedHolder = baseline + 50;
    earnedBench = baseline;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP, &earnedLead);
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_EXP, &earnedHolder);
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_HELD_ITEM, &share);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);

    ZeroPlayerPartyMons();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(CalculatePlayerPartyCount(), 3);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP), earnedLead);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_EXP), earnedHolder);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_EXP), earnedBench);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HELD_ITEM), ITEM_NONE);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_HELD_ITEM), ITEM_EXP_SHARE);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_HELD_ITEM), ITEM_NONE);

    // Move the held item; a second save must restore the new owner, not
    // accidentally keep the earlier holder, and preserve distinct EXP.
    earnedLead += 70;
    earnedBench += 40;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP, &earnedLead);
    SetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_EXP, &earnedBench);
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_HELD_ITEM, &noItem);
    SetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_HELD_ITEM, &share);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);

    ZeroPlayerPartyMons();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(CalculatePlayerPartyCount(), 3);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP), earnedLead);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_EXP), earnedHolder);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_EXP), earnedBench);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_HELD_ITEM), ITEM_NONE);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_HELD_ITEM), ITEM_EXP_SHARE);
    for (u32 i = 0; i < 3; i++)
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_LEVEL), AVERON_EXP_LEVEL);
}
