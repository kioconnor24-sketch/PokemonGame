#include "global.h"
#include "test/test.h"
#include "event_object_movement.h"
#include "load_save.h"
#include "pokemon.h"
#include "save.h"
#include "gba/flash_internal.h"

// The gameplay follower is selected by GetFirstLiveMon() and reported to
// UpdateFollowingPokemon() by GetFollowerInfo(). This is NOT the separately
// configurable follower NPC / battle-partner feature. These tests exercise
// party selection without spawning an object, changing maps, or rendering.

TEST("Averon following Pokemon: first eligible party member changes with fainting eggs and party order")
{
    struct Pokemon swapped;
    enum Species species;
    bool32 shiny, female;
    u16 noHp = 0;
    u8 isEgg = TRUE;

    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_WOBBUFFET, 25, 0, OTID_STRUCT_PLAYER_ID);
    CreateMon(&gParties[B_TRAINER_PLAYER][1], SPECIES_SNIVY, 25, 0, OTID_STRUCT_PLAYER_ID);
    CreateMon(&gParties[B_TRAINER_PLAYER][2], SPECIES_PIPLUP, 25, 0, OTID_STRUCT_PLAYER_ID);
    CalculatePlayerPartyCount();

    EXPECT(GetFirstLiveMon() == &gParties[B_TRAINER_PLAYER][0]);
    EXPECT(GetFollowerInfo(&species, &shiny, &female));
    EXPECT_EQ(species, SPECIES_WOBBUFFET);

    // A fainted party leader must not be selected.
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &noHp);
    EXPECT(GetFirstLiveMon() == &gParties[B_TRAINER_PLAYER][1]);
    EXPECT(GetFollowerInfo(&species, &shiny, &female));
    EXPECT_EQ(species, SPECIES_SNIVY);

    // Even if egg HP is nonzero, it cannot become the follower.
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_IS_EGG, &isEgg);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_IS_EGG), TRUE);
    EXPECT(GetFirstLiveMon() == &gParties[B_TRAINER_PLAYER][2]);
    EXPECT(GetFollowerInfo(&species, &shiny, &female));
    EXPECT_EQ(species, SPECIES_PIPLUP);

    // A party reordering must immediately change the selected first live
    // mon. This checks selection, not the map sprite-refresh callback.
    swapped = gParties[B_TRAINER_PLAYER][0];
    gParties[B_TRAINER_PLAYER][0] = gParties[B_TRAINER_PLAYER][2];
    gParties[B_TRAINER_PLAYER][2] = swapped;
    EXPECT(GetFirstLiveMon() == &gParties[B_TRAINER_PLAYER][0]);
    EXPECT(GetFollowerInfo(&species, &shiny, &female));
    EXPECT_EQ(species, SPECIES_PIPLUP);

    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &noHp);
    EXPECT(GetFirstLiveMon() == NULL);
    EXPECT_EQ(GetFollowerInfo(&species, &shiny, &female), FALSE);
    EXPECT_EQ(species, SPECIES_NONE);

    ZeroPlayerPartyMons();
    EXPECT(GetFirstLiveMon() == NULL);
    EXPECT_EQ(GetFollowerInfo(&species, &shiny, &female), FALSE);
}

TEST("Averon following Pokemon: eligible lead after flash load skips fainted party slots")
{
    enum Species species;
    bool32 shiny, female;
    u16 noHp = 0;

    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_WOBBUFFET, 25, 0, OTID_STRUCT_PLAYER_ID);
    CreateMon(&gParties[B_TRAINER_PLAYER][1], SPECIES_PIPLUP, 25, 0, OTID_STRUCT_PLAYER_ID);
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &noHp);
    CalculatePlayerPartyCount();

    EXPECT(GetFirstLiveMon() == &gParties[B_TRAINER_PLAYER][1]);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);

    ZeroPlayerPartyMons();
    EXPECT_EQ(GetFollowerInfo(&species, &shiny, &female), FALSE);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(CalculatePlayerPartyCount(), 2);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), 0);
    EXPECT(GetFirstLiveMon() == &gParties[B_TRAINER_PLAYER][1]);
    EXPECT(GetFollowerInfo(&species, &shiny, &female));
    EXPECT_EQ(species, SPECIES_PIPLUP);
}
