#include "global.h"
#include "test/test.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "field_player_avatar.h"
#include "load_save.h"
#include "overworld.h"
#include "pokemon.h"
#include "save.h"
#include "sprite.h"
#include "gba/flash_internal.h"
#include "constants/event_objects.h"
#include "constants/map_types.h"
#include "constants/maps.h"

// Following Pokemon runtime checks: the real UpdateFollowingPokemon spawns,
// updates and removes the follower object on existing, unchanged maps.
// Rendering and movement on screen are left to emulator QA.

static void AddMon(u32 slot, u32 species, u32 personality, bool32 fainted, bool32 egg)
{
    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][slot];
    u32 zero = 0;
    CreateMon(mon, species, 10, personality, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(mon);
    if (fainted)
        SetMonData(mon, MON_DATA_HP, &zero);
    if (egg)
    {
        bool32 isEgg = TRUE;
        SetMonData(mon, MON_DATA_IS_EGG, &isEgg);
    }
}

static void EnterMap(u32 mapGroup, u32 mapNum)
{
    SetWarpDestination(mapGroup, mapNum, WARP_ID_NONE, 4, 4);
    WarpIntoMap();
    ResetSpriteData();
    ResetObjectEvents();
}

static u32 FollowerSpecies(void)
{
    UpdateFollowingPokemon();
    struct ObjectEvent *follower = GetFollowerObject();
    return follower == NULL ? SPECIES_NONE : OW_SPECIES(follower);
}

static void CleanUp(void)
{
    RemoveFollowingPokemon();
    FlagClear(FLAG_TEMP_HIDE_FOLLOWER);
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
}

TEST("Averon follower is the first party Pokemon that is not fainted or an egg")
{
    ZeroPlayerPartyMons();
    AddMon(0, SPECIES_TOGEPI, 0, FALSE, TRUE);
    AddMon(1, SPECIES_WOBBUFFET, 0, TRUE, FALSE);
    AddMon(2, SPECIES_PIKACHU, 0, FALSE, FALSE);
    CalculatePlayerPartyCount();
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    CleanUp();
}

TEST("Averon follower changes when the party order or health changes")
{
    struct Pokemon temp;
    u32 zero = 0;
    ZeroPlayerPartyMons();
    AddMon(0, SPECIES_PIKACHU, 0, FALSE, FALSE);
    AddMon(1, SPECIES_BULBASAUR, 0, FALSE, FALSE);
    CalculatePlayerPartyCount();
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    // Swap the first two, as the party menu does.
    temp = gParties[B_TRAINER_PLAYER][0];
    gParties[B_TRAINER_PLAYER][0] = gParties[B_TRAINER_PLAYER][1];
    gParties[B_TRAINER_PLAYER][1] = temp;
    EXPECT_EQ(FollowerSpecies(), SPECIES_BULBASAUR);
    // The lead faints: the next live Pokemon follows.
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &zero);
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    // Everyone fainted: no follower, and no crash.
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_HP, &zero);
    EXPECT_EQ(FollowerSpecies(), SPECIES_NONE);
    CleanUp();
}

TEST("Averon follower is removed for an empty party or while hidden by script")
{
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(FollowerSpecies(), SPECIES_NONE);
    AddMon(0, SPECIES_PIKACHU, 0, FALSE, FALSE);
    CalculatePlayerPartyCount();
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    FlagSet(FLAG_TEMP_HIDE_FOLLOWER);
    EXPECT_EQ(FollowerSpecies(), SPECIES_NONE);
    FlagClear(FLAG_TEMP_HIDE_FOLLOWER);
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    CleanUp();
}

// UpdateFollowingPokemon removes followers larger than 32x32 indoors.
TEST("Averon follower: a large one walks outdoors but not indoors; a small one does both")
{
    u32 large = SPECIES_NONE;
    const struct ObjectEventGraphicsInfo *placeholder = &gSpeciesInfo[SPECIES_NONE].overworldData;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES && large == SPECIES_NONE; species++)
    {
        const struct ObjectEventGraphicsInfo *info;
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        info = SpeciesToGraphicsInfo(species, FALSE, FALSE);
        if (info != NULL && info != placeholder && info->oam->size > ST_OAM_SIZE_2)
            large = species;
    }
    EXPECT_NE(large, SPECIES_NONE);
    ZeroPlayerPartyMons();
    AddMon(0, large, 0, FALSE, FALSE);
    CalculatePlayerPartyCount();
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    EXPECT_NE(gMapHeader.mapType, MAP_TYPE_INDOOR);
    EXPECT_EQ(FollowerSpecies(), large);
    EnterMap(MAP_GROUP(MAP_SALTMEREHOME), MAP_NUM(MAP_SALTMEREHOME));
    EXPECT_EQ(gMapHeader.mapType, MAP_TYPE_INDOOR);
    EXPECT_EQ(FollowerSpecies(), SPECIES_NONE);
    // A small follower stays indoors.
    AddMon(0, SPECIES_PIKACHU, 0, FALSE, FALSE);
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    CleanUp();
}

TEST("Averon follower is respawned with the right species after each warp")
{
    ZeroPlayerPartyMons();
    AddMon(0, SPECIES_PIKACHU, 0, FALSE, FALSE);
    CalculatePlayerPartyCount();
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    EnterMap(MAP_GROUP(MAP_ALDERFIELDCLINIC), MAP_NUM(MAP_ALDERFIELDCLINIC));
    EXPECT(GetFollowerObject() == NULL); // object events reset on the new map
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(FollowerSpecies(), SPECIES_PIKACHU);
    CleanUp();
}

TEST("Averon follower graphics carry the lead's shiny and female variants")
{
    u32 femalePersonality = 0;
    struct ObjectEvent *follower;
    for (u32 p = 1; p < 0x10000 && femalePersonality == 0; p++)
    {
        if (GetGenderFromSpeciesAndPersonality(SPECIES_PIKACHU, p) == MON_FEMALE)
            femalePersonality = p;
    }
    ZeroPlayerPartyMons();
    AddMon(0, SPECIES_PIKACHU, femalePersonality, FALSE, FALSE);
    {
        bool32 shiny = FALSE; // the personality alone may make it shiny
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_IS_SHINY, &shiny);
    }
    CalculatePlayerPartyCount();
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    UpdateFollowingPokemon();
    follower = GetFollowerObject();
    EXPECT(follower != NULL);
    EXPECT_NE(OW_FEMALE(follower), 0);
    EXPECT_EQ(OW_SHINY(follower), 0);
    // A shiny lead: setting the shiny flag directly.
    {
        bool32 shiny = TRUE;
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_IS_SHINY, &shiny);
    }
    UpdateFollowingPokemon();
    follower = GetFollowerObject();
    EXPECT(follower != NULL);
    EXPECT_NE(OW_SHINY(follower), 0);
    CleanUp();
}

TEST("Averon follower after a flash save and load is the saved lead")
{
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    ZeroPlayerPartyMons();
    AddMon(0, SPECIES_BULBASAUR, 0, FALSE, FALSE);
    AddMon(1, SPECIES_PIKACHU, 0, FALSE, FALSE);
    CalculatePlayerPartyCount();
    SavePlayerParty();
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ZeroPlayerPartyMons();
    AddMon(0, SPECIES_PIKACHU, 0, FALSE, FALSE);
    CalculatePlayerPartyCount();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    LoadPlayerParty();
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    EXPECT_EQ(FollowerSpecies(), SPECIES_BULBASAUR);
    CleanUp();
}

TEST("Averon follower is hidden while surfing or underwater")
{
    ZeroPlayerPartyMons();
    AddMon(0, SPECIES_PIKACHU, 0, FALSE, FALSE);
    CalculatePlayerPartyCount();
    EnterMap(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE));
    gPlayerAvatar.objectEventId = 0;
    gPlayerAvatar.flags = PLAYER_AVATAR_FLAG_SURFING;
    EXPECT_EQ(IsFollowerVisible(), FALSE);
    gPlayerAvatar.flags = PLAYER_AVATAR_FLAG_UNDERWATER;
    EXPECT_EQ(IsFollowerVisible(), FALSE);
    gPlayerAvatar.flags = PLAYER_AVATAR_FLAG_ON_FOOT;
    CleanUp();
}
