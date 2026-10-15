#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "averon_scripted_battle.h"
#include "battle.h"
#include "event_data.h"
#include "heal_location.h"
#include "money.h"
#include "overworld.h"
#include "pokemon.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"

asm(".include \"data/scripts/averon_scripted_battle.inc\"\n");

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
    const struct HealLocation *heal = GetHealLocation(HEAL_LOCATION_ALDERFIELD);
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
    EXPECT(GetDestinationWarpMapHeader() == Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ALDERFIELDCLINIC), MAP_NUM(MAP_ALDERFIELDCLINIC)));
    FlagClear(FLAG_BADGE01_GET);
}

TEST("Averon stale no-whiteout state is cleared before ordinary battles")
{
    FlagSet(B_FLAG_NO_WHITEOUT);
    AveronScriptedBattle_ClearStaleNoWhiteout();
    EXPECT_EQ(AveronScriptedBattle_IsNoWhiteoutActive(), FALSE);
}
