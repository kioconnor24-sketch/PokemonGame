#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "averon_scripted_battle.h"
#include "battle.h"
#include "event_data.h"
#include "heal_location.h"
#include "load_save.h"
#include "money.h"
#include "overworld.h"
#include "pokemon.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "constants/heal_locations.h"
#include "constants/event_objects.h"
#include "constants/maps.h"
#include "constants/opponents.h"
#include "constants/script_commands.h"

asm(".set NULL, 0\n"
    ".set LOCALID_NONE, " STR(LOCALID_NONE) "\n"
    ".set TRAINER_NONE, " STR(TRAINER_NONE) "\n"
    ".include \"data/scripts/averon_scripted_battle.inc\"\n");

#define START_MONEY 5000

static void SetUpFaintedParty(void)
{
    u32 zero = 0, status = STATUS1_POISON;
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][0], SPECIES_WOBBUFFET, 20, 0);
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][1], SPECIES_WYNAUT, 20, 0);
    CalculatePlayerPartyCount();
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &zero);
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_HP, &zero);
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_STATUS, &status);
}

static void ExpectPartyFullyHealed(void)
{
    for (u32 slot = 0; slot < 2; slot++)
    {
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HP),
                  GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_MAX_HP));
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_STATUS), 0);
    }
    EXPECT_EQ(CalculatePlayerPartyCount(), 2);
}

// Natives and macros from data/scripts/averon_scripted_battle.inc.

TEST("Averon scripted battle tests run with a real no-whiteout flag")
{
    // The release config uses this RAM-only special flag. If it were 0, FlagSet
    // would do nothing and the leak checks would pass vacuously.
    EXPECT_EQ(B_FLAG_NO_WHITEOUT, FLAG_SPECIAL_FLAG_UNUSED_0x4003);
    FlagSet(B_FLAG_NO_WHITEOUT);
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), TRUE);
    FlagClear(B_FLAG_NO_WHITEOUT);
}

TEST("Averon scripted battle outcomes count losses, draws and forfeits as defeats")
{
    EXPECT_EQ(AveronScriptedBattle_IsPlayerDefeated(B_OUTCOME_LOST), TRUE);
    EXPECT_EQ(AveronScriptedBattle_IsPlayerDefeated(B_OUTCOME_DREW), TRUE);
    EXPECT_EQ(AveronScriptedBattle_IsPlayerDefeated(B_OUTCOME_FORFEITED), TRUE);
    EXPECT_EQ(AveronScriptedBattle_IsPlayerDefeated(B_OUTCOME_WON), FALSE);
    EXPECT_EQ(AveronScriptedBattle_IsPlayerDefeated(B_OUTCOME_RAN), FALSE);
    EXPECT_EQ(AveronScriptedBattle_IsPlayerDefeated(B_OUTCOME_CAUGHT), FALSE);
}

TEST("Averon scripted battle finish clears no-whiteout on a win or a loss")
{
    u32 outcome = B_OUTCOME_WON;
    PARAMETRIZE { outcome = B_OUTCOME_WON; }
    PARAMETRIZE { outcome = B_OUTCOME_LOST; }
    FlagClear(B_FLAG_NO_WHITEOUT);
    RUN_OVERWORLD_SCRIPT(callnative AveronScriptedBattle_Begin, requests_effects=1;);
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), TRUE);
    gBattleOutcome = outcome;
    RUN_OVERWORLD_SCRIPT(callnative AveronScriptedBattle_Finish, requests_effects=1;);
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
    EXPECT_EQ(gSpecialVar_Result, outcome == B_OUTCOME_LOST);
}

TEST("Averon scripted battle finish does not heal between chain battles")
{
    u32 damagedHP = 7, status = STATUS1_BURN;
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][0], SPECIES_WOBBUFFET, 20, 0);
    CalculatePlayerPartyCount();
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &damagedHP);
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_STATUS, &status);
    gBattleOutcome = B_OUTCOME_WON;
    RUN_OVERWORLD_SCRIPT(
        callnative AveronScriptedBattle_Begin, requests_effects=1;
        callnative AveronScriptedBattle_Finish, requests_effects=1;
    );
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), damagedHP);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_STATUS), STATUS1_BURN);
    EXPECT_EQ(gSpecialVar_Result, FALSE);
}

TEST("Averon story loss recovers in place with the party healed and money kept")
{
    SetUpFaintedParty();
    SetMoney(&gSaveBlock1Ptr->money, START_MONEY);
    FlagSet(B_FLAG_NO_WHITEOUT);
    RUN_OVERWORLD_SCRIPT(averon_recover_in_place;);
    ExpectPartyFullyHealed();
    EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
}

TEST("Averon ambush loss respawns at the last heal location and keeps the badge")
{
    u32 location = HEAL_LOCATION_ALDERFIELD, expectedMap = MAP_ALDERFIELDCLINIC;
    PARAMETRIZE { location = HEAL_LOCATION_ALDERFIELD; expectedMap = MAP_ALDERFIELDCLINIC; }
    PARAMETRIZE { location = HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F; expectedMap = MAP_SALTMEREHOME; }
    const struct HealLocation *heal = GetHealLocation(location);
    SetUpFaintedParty();
    SetMoney(&gSaveBlock1Ptr->money, START_MONEY);
    FlagSet(FLAG_BADGE01_GET);
    gSaveBlock1Ptr->lastHealLocation.mapGroup = heal->mapGroup;
    gSaveBlock1Ptr->lastHealLocation.mapNum = heal->mapNum;
    gSaveBlock1Ptr->lastHealLocation.warpId = WARP_ID_NONE;
    gSaveBlock1Ptr->lastHealLocation.x = heal->x;
    gSaveBlock1Ptr->lastHealLocation.y = heal->y;
    FlagSet(B_FLAG_NO_WHITEOUT);
    // averon_respawn's warp needs a loaded overworld; run its first step.
    RUN_OVERWORLD_SCRIPT(callnative AveronScriptedBattle_PrepareRespawn, requests_effects=1;);
    ExpectPartyFullyHealed();
    EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), START_MONEY);
    EXPECT_EQ(FlagGet(FLAG_BADGE01_GET), TRUE);
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
    EXPECT(GetDestinationWarpMapHeader() == Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(expectedMap), MAP_NUM(expectedMap)));
    FlagClear(FLAG_BADGE01_GET);
}

TEST("Averon stale no-whiteout state is cleared before ordinary battles")
{
    FlagSet(B_FLAG_NO_WHITEOUT);
    AveronScriptedBattle_ClearStaleNoWhiteout();
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
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

TEST("Averon scripted battle macro wraps one trainer battle between Begin and Finish")
{
    const u8 *script = OVERWORLD_SCRIPT(averon_scripted_battle 1, 0;);
    const u8 *battle = script + 5;
    u32 rest = 64;
    EXPECT(ScriptCallsNative(script, 5, AveronScriptedBattle_Begin));
    EXPECT_EQ(battle[0], SCR_OP_TRAINERBATTLE);
    // Flags byte: always fight (skip the beaten-trainer check), continue the
    // script afterwards, single battle, not a rematch.
    EXPECT(battle[1] & (1 << 7));
    EXPECT(battle[1] & (1 << 4));
    EXPECT(!(battle[1] & (1 << 0)));
    EXPECT(!(battle[1] & (1 << 1)));
    EXPECT(!ScriptCallsNative(battle, rest, AveronScriptedBattle_Begin));
    EXPECT(ScriptCallsNative(battle, rest, AveronScriptedBattle_Finish));
}

TEST("Averon scripted battle never reports a stale defeat from an earlier battle")
{
    gBattleOutcome = B_OUTCOME_LOST;
    RUN_OVERWORLD_SCRIPT(
        callnative AveronScriptedBattle_Begin, requests_effects=1;
        callnative AveronScriptedBattle_Finish, requests_effects=1;
    );
    EXPECT_EQ(gSpecialVar_Result, FALSE);
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
}

TEST("Averon scripted battle natives tolerate a repeated Begin and a Finish without Begin")
{
    FlagClear(B_FLAG_NO_WHITEOUT);
    gBattleOutcome = B_OUTCOME_LOST;
    RUN_OVERWORLD_SCRIPT(callnative AveronScriptedBattle_Finish, requests_effects=1;);
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
    EXPECT_EQ(gSpecialVar_Result, TRUE);
    RUN_OVERWORLD_SCRIPT(
        callnative AveronScriptedBattle_Begin, requests_effects=1;
        callnative AveronScriptedBattle_Begin, requests_effects=1;
    );
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), TRUE);
    gBattleOutcome = B_OUTCOME_WON;
    RUN_OVERWORLD_SCRIPT(callnative AveronScriptedBattle_Finish, requests_effects=1;);
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
    EXPECT_EQ(gSpecialVar_Result, FALSE);
}

static u32 HashBytes(const void *data, u32 size)
{
    const u8 *bytes = data;
    u32 hash = 2166136261u;
    for (u32 i = 0; i < size; i++)
        hash = (hash ^ bytes[i]) * 16777619u;
    return hash;
}

static bool32 PointerInside(const void *ptr, const void *start, u32 size)
{
    return (uintptr_t)ptr >= (uintptr_t)start && (uintptr_t)ptr < (uintptr_t)start + size;
}

// Executed proof that the flag cannot reach a save: its byte lies in EWRAM
// (wiped by every reset that precedes a save load) and outside every block
// the game writes to flash, and setting it changes no saved byte.
TEST("Averon no-whiteout flag lives in RAM outside every saved block")
{
    const u8 *flag = GetFlagPointer(B_FLAG_NO_WHITEOUT);
    u32 before[4], after[4];
    EXPECT_NE(flag, NULL);
    EXPECT(PointerInside(flag, (const void *)EWRAM_START, EWRAM_END - EWRAM_START));
    EXPECT(!PointerInside(flag, &gSaveblock1, sizeof(gSaveblock1)));
    EXPECT(!PointerInside(flag, &gSaveblock2, sizeof(gSaveblock2)));
    EXPECT(!PointerInside(flag, &gSaveblock3, sizeof(gSaveblock3)));
    EXPECT(!PointerInside(flag, &gPokemonStorage, sizeof(gPokemonStorage)));
    FlagClear(B_FLAG_NO_WHITEOUT);
    before[0] = HashBytes(&gSaveblock1, sizeof(gSaveblock1));
    before[1] = HashBytes(&gSaveblock2, sizeof(gSaveblock2));
    before[2] = HashBytes(&gSaveblock3, sizeof(gSaveblock3));
    before[3] = HashBytes(&gPokemonStorage, sizeof(gPokemonStorage));
    FlagSet(B_FLAG_NO_WHITEOUT);
    after[0] = HashBytes(&gSaveblock1, sizeof(gSaveblock1));
    after[1] = HashBytes(&gSaveblock2, sizeof(gSaveblock2));
    after[2] = HashBytes(&gSaveblock3, sizeof(gSaveblock3));
    after[3] = HashBytes(&gPokemonStorage, sizeof(gPokemonStorage));
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), TRUE);
    FlagClear(B_FLAG_NO_WHITEOUT);
    for (u32 i = 0; i < ARRAY_COUNT(before); i++)
        EXPECT_EQ(before[i], after[i]);
}

// The release B_FLAG_NO_WHITEOUT is a special flag, which lives in RAM only,
// so a set flag can never be restored from a save, while badges are.
TEST("Averon RAM-only special flag is not restored from a save but the badge is")
{
    const u32 candidate = B_FLAG_NO_WHITEOUT;
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    FlagSet(FLAG_BADGE01_GET);
    FlagSet(candidate);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    FlagClear(FLAG_BADGE01_GET);
    FlagClear(candidate);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(FlagGet(FLAG_BADGE01_GET), TRUE);
    EXPECT_EQ(FlagGet(candidate), FALSE);
    FlagClear(FLAG_BADGE01_GET);
}
