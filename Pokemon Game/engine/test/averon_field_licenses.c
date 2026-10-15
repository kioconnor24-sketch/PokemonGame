#include "global.h"
#include "test/test.h"
#include "test/field_menu.h"
#include "main.h"
#include "battle.h"
#include "event_data.h"
#include "field_move.h"
#include "load_save.h"
#include "pokemon.h"
#include "party_menu.h"
#include "save.h"
#include "script.h"
#include "overworld.h"
#include "region_map.h"
#include "field_player_avatar.h"
#include "follower_npc.h"
#include "fldeff.h"
#include "constants/event_objects.h"
#include "constants/maps.h"
#include "constants/map_types.h"
#include "constants/heal_locations.h"
#include "constants/region_map_sections.h"

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

static void WaitForActions(void)
{
    for (u32 i = 0; i < 240 && !Test_FieldMenuActionsReady(); ++i)
        Test_FieldMenuStep(0);
    EXPECT_EQ(Test_FieldMenuActionsReady(), TRUE);
}

static void SelectAction(u32 index)
{
    for (u32 i = 0; i < index; ++i)
    {
        Test_FieldMenuStep(DPAD_DOWN);
        Test_FieldMenuStep(0);
    }
    Test_FieldMenuStep(A_BUTTON);
    Test_FieldMenuStep(0);
}

static void OpenToolkit(void)
{
    WaitForActions();
    s32 index = Test_FieldMenuToolkitIndex();
    EXPECT(index >= 0);
    if (index < 0)
        return;
    SelectAction(index);
    WaitForActions();
    EXPECT_EQ(Test_FieldMenuActionCount(), 8);
}

TEST("Averon Field Kit B returns to actions then party selection and exits cleanly")
{
    CreatePartner();
    Test_FieldMenuBegin();
    WaitForActions();
    u32 ordinaryCount = Test_FieldMenuActionCount();
    OpenToolkit();
    for (u32 i = 0; i < ARRAY_COUNT(sLicensedMoves); ++i)
        EXPECT(Test_FieldMenuMoveIndex(sLicensedMoves[i]) >= 0);
    Test_FieldMenuStep(B_BUTTON);
    Test_FieldMenuStep(0);
    WaitForActions();
    EXPECT_EQ(Test_FieldMenuActionCount(), ordinaryCount);
    EXPECT(Test_FieldMenuToolkitIndex() >= 0);
    Test_FieldMenuStep(B_BUTTON);
    Test_FieldMenuStep(0);
    EXPECT_EQ(Test_FieldMenuChoosingMon(), TRUE);
    Test_FieldMenuStep(B_BUTTON);
    for (u32 i = 0; i < 120 && !Test_FieldMenuExited(); ++i)
        Test_FieldMenuStep(0);
    EXPECT_EQ(Test_FieldMenuExited(), TRUE);
    EXPECT_EQ(gPartyMenu.slotId, PARTY_SIZE + 1);
    Test_FieldMenuEnd();
}

TEST("Averon locked Field Kit actions return safely without changing map or licenses")
{
    u32 which = 0;
    PARAMETRIZE { which = 0; }
    PARAMETRIZE { which = 1; }
    PARAMETRIZE { which = 2; }
    PARAMETRIZE { which = 3; }
    PARAMETRIZE { which = 4; }
    PARAMETRIZE { which = 5; }
    PARAMETRIZE { which = 6; }
    CreatePartner();
    FlagClear(FLAG_AVERON_LICENSE_CUT + which);
    SetWarpDestination(MAP_GROUP(MAP_AVERONFIELDLAB), MAP_NUM(MAP_AVERONFIELDLAB), WARP_ID_NONE, 4, 4);
    WarpIntoMap();
    Test_FieldMenuBegin();
    OpenToolkit();
    s32 index = Test_FieldMenuMoveIndex(sLicensedMoves[which]);
    EXPECT(index >= 0);
    if (index >= 0)
        SelectAction(index);
    for (u32 i = 0; i < 240 && !Test_FieldMenuChoosingMon(); ++i)
        Test_FieldMenuStep(A_BUTTON);
    EXPECT_EQ(Test_FieldMenuChoosingMon(), TRUE);
    EXPECT_EQ(IsFieldMoveUnlocked(sLicensedMoves[which]), FALSE);
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_AVERONFIELDLAB));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_AVERONFIELDLAB));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, 4);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, 4);
    EXPECT_EQ(gPartyMenu.slotId, 0);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MOVE1), MOVE_TACKLE);
    Test_FieldMenuEnd();
}

TEST("Averon Fly map B returns to the same party and Field Kit can reopen")
{
    CreatePartner();
    FlagSet(FLAG_AVERON_LICENSE_FLY);
    FlagSet(FLAG_VISITED_LITTLEROOT_TOWN);
    SetWarpDestination(MAP_GROUP(MAP_AVERONFIELDLAB), MAP_NUM(MAP_AVERONFIELDLAB), WARP_ID_NONE, 4, 4);
    WarpIntoMap();
    Test_FieldMenuBegin();
    OpenToolkit();
    SelectAction(Test_FieldMenuMoveIndex(FIELD_MOVE_FLY));
    for (u32 i = 0; i < 240 && !Test_FlyMenuReady(); ++i)
        Test_FieldMenuStep(0);
    EXPECT_EQ(Test_FlyMenuReady(), TRUE);
    Test_FieldMenuStep(B_BUTTON);
    Test_FieldMenuStep(0);
    for (u32 i = 0; i < 240 && !Test_FieldMenuChoosingMon(); ++i)
        Test_FieldMenuStep(0);
    EXPECT_EQ(Test_FieldMenuChoosingMon(), TRUE);
    EXPECT_EQ(gPartyMenu.slotId, 0);
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_AVERONFIELDLAB));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, 4);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, 4);
    EXPECT_EQ(IsFieldMoveUnlocked(FIELD_MOVE_FLY), TRUE);
    Test_FieldMenuStep(A_BUTTON);
    Test_FieldMenuStep(0);
    OpenToolkit();
    Test_FieldMenuEnd();
}

TEST("Averon Field Kit fits alongside four learned actions and survives Back")
{
    CreatePartner();
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][1], SPECIES_PIPLUP, 5, 0);
    CalculatePlayerPartyCount();
    const u16 moves[] = {MOVE_FLASH, MOVE_TELEPORT, MOVE_DIG, MOVE_SWEET_SCENT};
    for (u32 i = 0; i < ARRAY_COUNT(moves); ++i)
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MOVE1 + i, &moves[i]);
    Test_FieldMenuBegin();
    WaitForActions();
    EXPECT_EQ(Test_FieldMenuActionCount(), 9);
    OpenToolkit();
    // Select the actual last BACK entry with A, separately from the B test.
    SelectAction(Test_FieldMenuActionCount() - 1);
    WaitForActions();
    EXPECT_EQ(Test_FieldMenuActionCount(), 9);
    EXPECT(Test_FieldMenuToolkitIndex() >= 0);
    EXPECT(Test_FieldMenuMoveIndex(FIELD_MOVE_FLASH) >= 0);
    EXPECT(Test_FieldMenuMoveIndex(FIELD_MOVE_TELEPORT) >= 0);
    EXPECT(Test_FieldMenuMoveIndex(FIELD_MOVE_DIG) >= 0);
    EXPECT(Test_FieldMenuMoveIndex(FIELD_MOVE_SWEET_SCENT) >= 0);
    Test_FieldMenuEnd();
}

TEST("Averon Field Kit is unavailable on fainted partners and eggs")
{
    u32 egg = FALSE;
    PARAMETRIZE { egg = FALSE; }
    PARAMETRIZE { egg = TRUE; }
    CreatePartner();
    u16 hp = 0;
    if (egg)
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_IS_EGG, &egg);
    else
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &hp);
    Test_FieldMenuBegin();
    WaitForActions();
    EXPECT_EQ(Test_FieldMenuToolkitIndex(), -1);
    Test_FieldMenuEnd();
}

TEST("Averon traversal respects configured follower policy and Fly map-type rules")
{
    CreatePartner();
#if FNPC_ENABLE_NPC_FOLLOWERS
    SetFollowerNPCData(FNPC_DATA_IN_PROGRESS, TRUE);
    SetFollowerNPCData(FNPC_DATA_FOLLOWER_FLAGS, 0);
    EXPECT_EQ(PlayerHasFollowerNPC(), TRUE);
    const enum FieldMove moves[] = {FIELD_MOVE_SURF, FIELD_MOVE_WATERFALL, FIELD_MOVE_DIVE, FIELD_MOVE_FLY};
    for (u32 i = 0; i < ARRAY_COUNT(moves); ++i)
    {
        FlagSet(FLAG_AVERON_LICENSE_CUT + gFieldMoveInfo[moves[i]].arg);
        EXPECT_EQ(IsFieldMoveUnlocked(moves[i]), TRUE);
        EXPECT_EQ(FieldMove_GetPartyMember(moves[i]), 0);
        EXPECT_EQ(SetUpFieldMove(moves[i]), FALSE);
    }
    SetFollowerNPCData(FNPC_DATA_FOLLOWER_FLAGS, FOLLOWER_NPC_FLAG_CAN_LEAVE_ROUTE);
#else
    // Averon enables following Pokemon, not the optional human NPC follower
    // save structure. Do not enable that structure merely to make a test pass.
    EXPECT_EQ(PlayerHasFollowerNPC(), FALSE);
    EXPECT_EQ(CheckFollowerNPCFlag(FOLLOWER_NPC_FLAG_CAN_LEAVE_ROUTE), TRUE);
    EXPECT_EQ(CheckFollowerNPCFlag(FOLLOWER_NPC_FLAG_CAN_SURF), TRUE);
    EXPECT_EQ(CheckFollowerNPCFlag(FOLLOWER_NPC_FLAG_CAN_WATERFALL), TRUE);
    EXPECT_EQ(CheckFollowerNPCFlag(FOLLOWER_NPC_FLAG_CAN_DIVE), TRUE);
#endif
    gMapHeader.mapType = MAP_TYPE_ROUTE;
    EXPECT_EQ(SetUpFieldMove(FIELD_MOVE_FLY), TRUE);
    gMapHeader.mapType = MAP_TYPE_INDOOR;
    EXPECT_EQ(SetUpFieldMove(FIELD_MOVE_FLY), FALSE);
    SetFollowerNPCData(FNPC_DATA_IN_PROGRESS, FALSE);
    gMapHeader.mapType = MAP_TYPE_TOWN;
    EXPECT_EQ(SetUpFieldMove(FIELD_MOVE_FLY), TRUE);
}

TEST("Averon native obstacle preparation selects the facing object without learned HMs")
{
    u32 which = 0;
    PARAMETRIZE { which = 0; }
    PARAMETRIZE { which = 1; }
    PARAMETRIZE { which = 2; }
    const enum FieldMove moves[] = {FIELD_MOVE_CUT, FIELD_MOVE_ROCK_SMASH, FIELD_MOVE_STRENGTH};
    const u16 graphics[] = {OBJ_EVENT_GFX_CUTTABLE_TREE, OBJ_EVENT_GFX_BREAKABLE_ROCK, OBJ_EVENT_GFX_PUSHABLE_BOULDER};
    CreatePartner();
    SetWarpDestination(MAP_GROUP(MAP_AVERONFIELDLAB), MAP_NUM(MAP_AVERONFIELDLAB), WARP_ID_NONE, 4, 4);
    WarpIntoMap();
    memset(gObjectEvents, 0, sizeof(gObjectEvents));
    gPlayerAvatar.objectEventId = 0;
    gObjectEvents[0].active = TRUE;
    gObjectEvents[0].currentCoords.x = 12;
    gObjectEvents[0].currentCoords.y = 12;
    gObjectEvents[0].facingDirection = DIR_NORTH;
    gObjectEvents[0].currentElevation = 3;
    gObjectEvents[0].previousElevation = 3;
    gObjectEvents[1].active = TRUE;
    gObjectEvents[1].currentCoords.x = 12;
    gObjectEvents[1].currentCoords.y = 11;
    gObjectEvents[1].currentElevation = 3;
    gObjectEvents[1].graphicsId = graphics[which];
    gObjectEvents[1].localId = 7;
    gPartyMenu.slotId = 0;
    FlagSet(FLAG_AVERON_LICENSE_CUT + gFieldMoveInfo[moves[which]].arg);
    EXPECT_EQ(FieldMove_GetPartyMember(moves[which]), 0);
    EXPECT_EQ(MonKnowsMove(&gParties[B_TRAINER_PLAYER][0], FieldMove_GetMoveId(moves[which])), FALSE);
    EXPECT_EQ(SetUpFieldMove(moves[which]), TRUE);
    EXPECT_EQ(gSpecialVar_LastTalked, 7);
    EXPECT(gPostMenuFieldCallback != NULL);
    // Removing the object must not read the OBJECT_EVENTS_COUNT sentinel as
    // an actual object or preserve the previous obstacle as a usable target.
    gObjectEvents[1].active = FALSE;
    EXPECT_EQ(CheckObjectGraphicsInFrontOfPlayer(graphics[which]), FALSE);
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

TEST("Averon field lab Dive connections preserve coordinates party and licenses in both directions")
{
    CreatePartner();
    FlagSet(FLAG_AVERON_LICENSE_DIVE);
    const struct MapHeader *surface=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_AVERONFIELDLAB),MAP_NUM(MAP_AVERONFIELDLAB));
    const struct MapHeader *underwater=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_AVERONFIELDLABUNDERWATER),MAP_NUM(MAP_AVERONFIELDLABUNDERWATER));
    SetWarpDestination(MAP_GROUP(MAP_AVERONFIELDLAB),MAP_NUM(MAP_AVERONFIELDLAB),WARP_ID_NONE,4,4);
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->pos.x,4);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y,4);
    EXPECT_EQ(SetDiveWarpDive(20,12),TRUE);
    EXPECT(GetDestinationWarpMapHeader()==underwater);
    WarpIntoMap();
    EXPECT_EQ(gMapHeader.mapType,MAP_TYPE_UNDERWATER);
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum,MAP_NUM(MAP_AVERONFIELDLABUNDERWATER));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x,20);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y,12);
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVE_DIVE),0);
    EXPECT_EQ(SetDiveWarpEmerge(20,12),TRUE);
    EXPECT(GetDestinationWarpMapHeader()==surface);
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum,MAP_NUM(MAP_AVERONFIELDLAB));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x,20);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y,12);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0],MON_DATA_SPECIES),SPECIES_WOBBUFFET);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER],1);
    EXPECT_EQ(IsFieldMoveUnlocked(FIELD_MOVE_DIVE),TRUE);
}

TEST("Averon developer Fly destination lands both player genders safely in Saltmere")
{
    u32 gender = MALE;
    PARAMETRIZE { gender = MALE; }
    PARAMETRIZE { gender = FEMALE; }
    struct RegionMap destination = { .mapSecId = MAPSEC_LITTLEROOT_TOWN };
    CreatePartner();
    gSaveBlock2Ptr->playerGender = gender;
    // The debug destination control only enables the visited destination. It
    // must not substitute for a traversal license, even with a usable partner.
    FlagSet(FLAG_VISITED_LITTLEROOT_TOWN);
    FlagClear(FLAG_AVERON_LICENSE_FLY);
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVE_FLY), PARTY_SIZE);
    FlagSet(FLAG_AVERON_LICENSE_FLY);
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVE_FLY), 0);
    EXPECT_EQ(MonKnowsMove(&gParties[B_TRAINER_PLAYER][0], MOVE_FLY), FALSE);
    EXPECT_EQ(FilterFlyDestination(&destination), gender == MALE
        ? HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F
        : HEAL_LOCATION_LITTLEROOT_TOWN_MAYS_HOUSE_2F);
    SetWarpDestination(MAP_GROUP(MAP_AVERONFIELDLAB), MAP_NUM(MAP_AVERONFIELDLAB), WARP_ID_NONE, 4, 4);
    WarpIntoMap();
    SetFlyDestination(&destination);
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_SALTMERE));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, 18);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, 18);
    EXPECT_EQ(gMapHeader.mapType, MAP_TYPE_TOWN);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], 1);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_WOBBUFFET);
    EXPECT_EQ(IsFieldMoveUnlocked(FIELD_MOVE_FLY), TRUE);
    // Return uses the same destination as debug Script4, without touching the
    // player's respawn point or inventing any final-world travel connection.
    SetWarpDestination(MAP_GROUP(MAP_AVERONFIELDLAB), MAP_NUM(MAP_AVERONFIELDLAB), WARP_ID_NONE, 4, 4);
    WarpIntoMap();
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_AVERONFIELDLAB));
    EXPECT_EQ(FieldMove_GetPartyMember(FIELD_MOVE_FLY), 0);
}
