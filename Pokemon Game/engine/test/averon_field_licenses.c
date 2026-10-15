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
#include "overworld.h"
#include "region_map.h"
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
