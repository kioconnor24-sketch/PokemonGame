#include "global.h"
#include "test/battle.h"
#include "test/overworld_script.h"
#include "averon_legend.h"
#include "event_data.h"
#include "load_save.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "constants/script_commands.h"

asm(".set ITEM_NONE, 0\n" // an enum, so STR() cannot expand it
    ".set VAR_0x8004, " STR(VAR_0x8004) "\n"
    ".set VAR_0x8005, " STR(VAR_0x8005) "\n"
    ".set VAR_0x8006, " STR(VAR_0x8006) "\n"
    ".include \"data/scripts/averon_legend.inc\"\n");

// Synthetic, test-only in-memory flags: no real encounter or saved ID.
#define CAUGHT   TESTING_FLAG_UNUSED_3
#define DEFEATED TESTING_FLAG_UNUSED_4

static void ResetEncounter(void)
{
    FlagClear(CAUGHT);
    FlagClear(DEFEATED);
}

// Every outcome the engine defines. scripts/test-averon-legend.py fails if
// include/constants/battle.h gains a B_OUTCOME_ value missing here.
static const u32 sAllOutcomes[] =
{
    0,
    B_OUTCOME_WON,
    B_OUTCOME_LOST,
    B_OUTCOME_DREW,
    B_OUTCOME_RAN,
    B_OUTCOME_PLAYER_TELEPORTED,
    B_OUTCOME_MON_FLED,
    B_OUTCOME_CAUGHT,
    B_OUTCOME_NO_SAFARI_BALLS,
    B_OUTCOME_FORFEITED,
    B_OUTCOME_MON_TELEPORTED,
    B_OUTCOME_LINK_BATTLE_RAN,
};

TEST("Averon legend only a capture counts as caught and only a knockout as defeated")
{
    for (u32 outcome = 0; outcome < 0x200; outcome++)
    {
        enum AveronLegendResult expected = AVERON_LEGEND_AVAILABLE;
        if (outcome == B_OUTCOME_CAUGHT)
            expected = AVERON_LEGEND_CAUGHT;
        else if (outcome == B_OUTCOME_WON)
            expected = AVERON_LEGEND_DEFEATED;
        EXPECT_EQ(AveronLegend_ClassifyOutcome(outcome), expected);
    }
}

TEST("Averon legend outcomes without a capture or knockout record nothing")
{
    for (u32 i = 0; i < ARRAY_COUNT(sAllOutcomes); i++)
    {
        u32 outcome = sAllOutcomes[i];
        if (outcome == B_OUTCOME_CAUGHT || outcome == B_OUTCOME_WON)
            continue;
        ResetEncounter();
        EXPECT_EQ(AveronLegend_RecordOutcome(outcome, CAUGHT, DEFEATED), AVERON_LEGEND_AVAILABLE);
        EXPECT_EQ(FlagGet(CAUGHT), FALSE);
        EXPECT_EQ(FlagGet(DEFEATED), FALSE);
        EXPECT_EQ(AveronLegend_IsAvailable(CAUGHT, DEFEATED, FALSE), TRUE);
    }
    ResetEncounter();
}

TEST("Averon legend capture is final and replaces an earlier defeat")
{
    ResetEncounter();
    EXPECT_EQ(AveronLegend_RecordOutcome(B_OUTCOME_WON, CAUGHT, DEFEATED), AVERON_LEGEND_DEFEATED);
    EXPECT_EQ(AveronLegend_RecordOutcome(B_OUTCOME_CAUGHT, CAUGHT, DEFEATED), AVERON_LEGEND_CAUGHT);
    EXPECT_EQ(FlagGet(CAUGHT), TRUE);
    EXPECT_EQ(FlagGet(DEFEATED), FALSE);
    // Nothing afterwards can undo or downgrade the capture.
    EXPECT_EQ(AveronLegend_RecordOutcome(B_OUTCOME_WON, CAUGHT, DEFEATED), AVERON_LEGEND_CAUGHT);
    EXPECT_EQ(AveronLegend_RecordOutcome(B_OUTCOME_MON_TELEPORTED, CAUGHT, DEFEATED), AVERON_LEGEND_CAUGHT);
    AveronLegend_AllowRetry(CAUGHT, DEFEATED);
    EXPECT_EQ(FlagGet(CAUGHT), TRUE);
    EXPECT_EQ(FlagGet(DEFEATED), FALSE);
    EXPECT_EQ(AveronLegend_IsAvailable(CAUGHT, DEFEATED, TRUE), FALSE);
    ResetEncounter();
}

TEST("Averon legend defeat is retryable only by the caller's policy or an explicit retry")
{
    ResetEncounter();
    EXPECT_EQ(AveronLegend_RecordOutcome(B_OUTCOME_WON, CAUGHT, DEFEATED), AVERON_LEGEND_DEFEATED);
    EXPECT_EQ(FlagGet(CAUGHT), FALSE);
    EXPECT_EQ(FlagGet(DEFEATED), TRUE);
    EXPECT_EQ(AveronLegend_IsAvailable(CAUGHT, DEFEATED, FALSE), FALSE);
    EXPECT_EQ(AveronLegend_IsAvailable(CAUGHT, DEFEATED, TRUE), TRUE);
    AveronLegend_AllowRetry(CAUGHT, DEFEATED);
    EXPECT_EQ(FlagGet(DEFEATED), FALSE);
    EXPECT_EQ(AveronLegend_IsAvailable(CAUGHT, DEFEATED, FALSE), TRUE);
    ResetEncounter();
}

// The upstream Hoenn pattern (e.g. data/maps/NavelRock_Top/scripts.inc)
// treats every outcome other than WON, RAN and PLAYER_TELEPORTED as caught.
TEST("Averon legend the upstream script pattern marks a teleported legendary caught")
{
    ResetEncounter();
    RUN_OVERWORLD_SCRIPT(
        setvar VAR_RESULT, B_OUTCOME_MON_TELEPORTED;
        goto_if_eq VAR_RESULT, B_OUTCOME_WON, 3f;
        goto_if_eq VAR_RESULT, B_OUTCOME_RAN, 3f;
        goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, 3f;
        setflag CAUGHT;
        3:;
    );
    EXPECT_EQ(FlagGet(CAUGHT), TRUE);
    // The contract keeps the same outcome available.
    ResetEncounter();
    EXPECT_EQ(AveronLegend_RecordOutcome(B_OUTCOME_MON_TELEPORTED, CAUGHT, DEFEATED), AVERON_LEGEND_AVAILABLE);
    EXPECT_EQ(FlagGet(CAUGHT), FALSE);
    ResetEncounter();
}

static bool32 ScriptCallsNative(const u8 *script, u32 length, void (*native)(struct ScriptContext *))
{
    u32 target = (u32)native + 0x2000000, word; // callnative ..., requests_effects=1 adds ROM_SIZE
    for (u32 i = 0; i + 5 <= length; i++)
    {
        memcpy(&word, &script[i + 1], sizeof(word));
        if (script[i] == SCR_OP_CALLNATIVE && word == target)
            return TRUE;
    }
    return FALSE;
}

TEST("Averon legend battle macro clears the old outcome, fights, then records")
{
    const u8 *script = OVERWORLD_SCRIPT(averon_legend_battle SPECIES_HO_OH, 70, CAUGHT, DEFEATED;);
    const u8 *battle = script + 5;
    EXPECT(ScriptCallsNative(script, 5, AveronLegend_Begin));
    EXPECT_EQ(battle[0], SCR_OP_SETWILDBATTLE);
    EXPECT_EQ(battle[1] | (battle[2] << 8), SPECIES_HO_OH);
    EXPECT_EQ(battle[3], 70);
    EXPECT_EQ(battle[11], SCR_OP_DOWILDBATTLE);
    EXPECT(!ScriptCallsNative(script, 12, AveronLegend_Record));
    EXPECT(ScriptCallsNative(battle + 12, 16, AveronLegend_Record));
}

TEST("Averon legend a stale capture from an earlier battle is never recorded")
{
    ResetEncounter();
    gBattleOutcome = B_OUTCOME_CAUGHT;
    RUN_OVERWORLD_SCRIPT(
        callnative AveronLegend_Begin, requests_effects=1;
        setvar VAR_0x8004, CAUGHT;
        setvar VAR_0x8005, DEFEATED;
        callnative AveronLegend_Record, requests_effects=1;
    );
    EXPECT_EQ(gSpecialVar_Result, AVERON_LEGEND_AVAILABLE);
    EXPECT_EQ(FlagGet(CAUGHT), FALSE);
    ResetEncounter();
}

TEST("Averon legend check and retry macros report and restore availability")
{
    ResetEncounter();
    FlagSet(DEFEATED);
    RUN_OVERWORLD_SCRIPT(averon_legend_check_available CAUGHT, DEFEATED, FALSE;);
    EXPECT_EQ(gSpecialVar_Result, FALSE);
    RUN_OVERWORLD_SCRIPT(averon_legend_check_available CAUGHT, DEFEATED, TRUE;);
    EXPECT_EQ(gSpecialVar_Result, TRUE);
    RUN_OVERWORLD_SCRIPT(averon_legend_allow_retry CAUGHT, DEFEATED;);
    RUN_OVERWORLD_SCRIPT(averon_legend_check_available CAUGHT, DEFEATED, FALSE;);
    EXPECT_EQ(gSpecialVar_Result, TRUE);
    FlagSet(CAUGHT);
    RUN_OVERWORLD_SCRIPT(averon_legend_check_available CAUGHT, DEFEATED, TRUE;);
    EXPECT_EQ(gSpecialVar_Result, FALSE);
    ResetEncounter();
}

// Real flags that live in the save block, so the state survives a real
// flash save and load. Upstream Ho-Oh flags; no Averon encounter uses them.
TEST("Averon legend caught and defeated states survive a flash save and load")
{
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    for (u32 caught = FALSE; caught <= TRUE; caught++)
    {
        bool32 defeated = !caught;
        ClearSaveData();
        Save_ResetSaveCounters();
        FlagClear(FLAG_CAUGHT_HO_OH);
        FlagClear(FLAG_DEFEATED_HO_OH);
        AveronLegend_RecordOutcome(caught ? B_OUTCOME_CAUGHT : B_OUTCOME_WON, FLAG_CAUGHT_HO_OH, FLAG_DEFEATED_HO_OH);
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        FlagClear(FLAG_CAUGHT_HO_OH);
        FlagClear(FLAG_DEFEATED_HO_OH);
        EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
        EXPECT_EQ(FlagGet(FLAG_CAUGHT_HO_OH), caught);
        EXPECT_EQ(FlagGet(FLAG_DEFEATED_HO_OH), defeated);
        EXPECT_EQ(AveronLegend_IsAvailable(FLAG_CAUGHT_HO_OH, FLAG_DEFEATED_HO_OH, FALSE), FALSE);
        EXPECT_EQ(AveronLegend_IsAvailable(FLAG_CAUGHT_HO_OH, FLAG_DEFEATED_HO_OH, TRUE), defeated);
        FlagClear(FLAG_CAUGHT_HO_OH);
        FlagClear(FLAG_DEFEATED_HO_OH);
    }
}

// Real wild battles, then the same native the macro uses.

static void RecordAfterBattle(void)
{
    RUN_OVERWORLD_SCRIPT(
        setvar VAR_0x8004, CAUGHT;
        setvar VAR_0x8005, DEFEATED;
        callnative AveronLegend_Record, requests_effects=1;
    );
}

WILD_BATTLE_TEST("Averon legend a wild legendary's Whirlwind leaves it available")
{
    GIVEN {
        ResetEncounter();
        PLAYER(SPECIES_WOBBUFFET) { Level(50); }
        PLAYER(SPECIES_WYNAUT) { Level(50); }
        OPPONENT(SPECIES_HO_OH) { Level(70); Moves(MOVE_WHIRLWIND); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); MOVE(opponent, MOVE_WHIRLWIND); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_WHIRLWIND, opponent);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_MON_TELEPORTED);
        RecordAfterBattle();
        EXPECT_EQ(gSpecialVar_Result, AVERON_LEGEND_AVAILABLE);
        EXPECT_EQ(FlagGet(CAUGHT), FALSE);
        EXPECT_EQ(FlagGet(DEFEATED), FALSE);
        ResetEncounter();
    }
}

WILD_BATTLE_TEST("Averon legend a wild Pokemon escaping by Emergency Exit leaves it available")
{
    GIVEN {
        ResetEncounter();
        PLAYER(SPECIES_WOBBUFFET);
        PLAYER(SPECIES_WYNAUT);
        OPPONENT(SPECIES_GOLISOPOD) { Ability(ABILITY_EMERGENCY_EXIT); MaxHP(263); HP(262); }
    } WHEN {
        TURN { MOVE(player, MOVE_SUPER_FANG); }
    } SCENE {
        ABILITY_POPUP(opponent, ABILITY_EMERGENCY_EXIT);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_MON_TELEPORTED);
        RecordAfterBattle();
        EXPECT_EQ(gSpecialVar_Result, AVERON_LEGEND_AVAILABLE);
        EXPECT_EQ(FlagGet(CAUGHT), FALSE);
        ResetEncounter();
    }
}

WILD_BATTLE_TEST("Averon legend a knockout records a defeat, not a capture")
{
    GIVEN {
        ResetEncounter();
        PLAYER(SPECIES_WOBBUFFET) { Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_HO_OH) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The wild Ho-Oh fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        RecordAfterBattle();
        EXPECT_EQ(gSpecialVar_Result, AVERON_LEGEND_DEFEATED);
        EXPECT_EQ(FlagGet(CAUGHT), FALSE);
        EXPECT_EQ(FlagGet(DEFEATED), TRUE);
        ResetEncounter();
    }
}

// A capture with a full party opens the Gen 7+ "swap into party" menu
// (B_CATCH_SWAP_INTO_PARTY, compile-time), which the headless runner cannot
// answer, so that case is left to emulator QA. The outcome is CAUGHT either way.
WILD_BATTLE_TEST("Averon legend a capture is recorded as caught")
{
    GIVEN {
        ResetEncounter();
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_HO_OH);
    } WHEN {
        TURN { USE_ITEM(player, ITEM_MASTER_BALL); }
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_CAUGHT);
        EXPECT_EQ(CalculatePlayerPartyCount(), 2);
        RecordAfterBattle();
        EXPECT_EQ(gSpecialVar_Result, AVERON_LEGEND_CAUGHT);
        EXPECT_EQ(FlagGet(CAUGHT), TRUE);
        EXPECT_EQ(FlagGet(DEFEATED), FALSE);
        ResetEncounter();
    }
}

// In the game a player loss whites out before the script records anything.
// Even if a script recorded it, nothing would be lost.
WILD_BATTLE_TEST("Averon legend a player loss leaves the encounter available")
{
    GIVEN {
        ResetEncounter();
        PLAYER(SPECIES_WOBBUFFET) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_HO_OH) { Level(70); Speed(100); Moves(MOVE_TACKLE); }
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("Wobbuffet fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_LOST);
        RecordAfterBattle();
        EXPECT_EQ(gSpecialVar_Result, AVERON_LEGEND_AVAILABLE);
        EXPECT_EQ(FlagGet(CAUGHT), FALSE);
        EXPECT_EQ(FlagGet(DEFEATED), FALSE);
        ResetEncounter();
    }
}
