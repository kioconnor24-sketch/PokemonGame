#include "global.h"
#include "test/test.h"
#include "battle.h"
#include "event_data.h"
#include "field_move.h"
#include "load_save.h"
#include "pokemon.h"
#include "party_menu.h"
#include "save.h"
#include "script.h"

static const enum FieldMove sLicensedMoves[] = {
    FIELD_MOVE_CUT, FIELD_MOVE_ROCK_SMASH, FIELD_MOVE_STRENGTH,
    FIELD_MOVE_SURF, FIELD_MOVE_WATERFALL, FIELD_MOVE_DIVE, FIELD_MOVE_FLY,
};

static void CreatePartner(void)
{
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][0], SPECIES_WOBBUFFET, 5, 0);
    u16 move=MOVE_TACKLE;
    for (u32 i=0; i<MAX_MON_MOVES; ++i)
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MOVE1+i, &move);
    CalculatePlayerPartyCount();
}

TEST("Averon field licenses gate all seven native script actions without learned HMs")
{
    u32 which=0;
    PARAMETRIZE { which=0; }
    PARAMETRIZE { which=1; }
    PARAMETRIZE { which=2; }
    PARAMETRIZE { which=3; }
    PARAMETRIZE { which=4; }
    PARAMETRIZE { which=5; }
    PARAMETRIZE { which=6; }
    enum FieldMove field=sLicensedMoves[which];
    u16 license=FLAG_AVERON_LICENSE_CUT+which;
    // Native opcode0x7c: checkfieldmove; opcode0x02: end (script_cmd_table.inc).
    // FALSE deliberately exercises scripts which omit the optional badge check.
    const u8 script[]={0x7c, field, FALSE, 0x02};
    CreatePartner();
    for (u32 i=0; i<8; ++i)
        FlagSet(FLAG_BADGE01_GET+i);
    FlagClear(license);
    EXPECT_EQ(IsFieldMoveUnlocked(field), FALSE);
    RunScriptImmediately(script);
    EXPECT_EQ(gSpecialVar_Result, PARTY_SIZE);
    FlagSet(license);
    EXPECT_EQ(IsFieldMoveUnlocked(field), TRUE);
    EXPECT_EQ(MonKnowsMove(&gParties[B_TRAINER_PLAYER][0], FieldMove_GetMoveId(field)), FALSE);
    RunScriptImmediately(script);
    EXPECT_EQ(gSpecialVar_Result, 0);
    EXPECT_EQ(gSpecialVar_0x8004, SPECIES_WOBBUFFET);
    FlagClear(license);
    u16 move=FieldMove_GetMoveId(field);
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MOVE1, &move);
    RunScriptImmediately(script);
    EXPECT_EQ(gSpecialVar_Result, PARTY_SIZE);
}

TEST("Averon licensed field actions refuse empty fainted and egg-only parties")
{
    FlagSet(FLAG_AVERON_LICENSE_SURF);
    ZeroPlayerPartyMons();
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVE_SURF), PARTY_SIZE);
    CreatePartner();
    u32 hp=0, egg=TRUE;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &hp);
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVE_SURF), PARTY_SIZE);
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][1], SPECIES_PIPLUP, 5, 0);
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_IS_EGG, &egg);
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVE_SURF), PARTY_SIZE);
    egg=FALSE;
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_IS_EGG, &egg);
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVE_SURF), 1);
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVES_COUNT), PARTY_SIZE);
}

TEST("Averon independent field licenses persist through actual flash save and load")
{
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    CreatePartner();
    for (u32 i=0; i<ARRAY_COUNT(sLicensedMoves); ++i)
    {
        if (i%2) FlagClear(FLAG_AVERON_LICENSE_CUT+i);
        else FlagSet(FLAG_AVERON_LICENSE_CUT+i);
    }
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    for (u32 i=0; i<ARRAY_COUNT(sLicensedMoves); ++i)
        FlagToggle(FLAG_AVERON_LICENSE_CUT+i);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    for (u32 i=0; i<ARRAY_COUNT(sLicensedMoves); ++i)
        EXPECT_EQ(IsFieldMoveUnlocked(sLicensedMoves[i]), i%2==0);
}
