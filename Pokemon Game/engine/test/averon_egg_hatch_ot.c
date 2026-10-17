#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "daycare.h"
#include "egg_hatch.h"
#include "event_data.h"
#include "load_save.h"
#include "move.h"
#include "pokemon.h"
#include "save.h"
#include "constants/items.h"

// Issue #100: hatching gives the egg the hatching player's original-trainer
// ID. OT_ID is part of the secure-data key (personality ^ OT ID), and the raw
// MON_DATA_OT_ID setter does not re-encrypt. An egg made in another save (a
// traded egg) carries that save's OT ID until it hatches here. The control
// is an egg made in this save, whose OT ID already matches.
#define PLAYER_OT_ID 0x78563412
#define FOREIGN_OT_ID 0xA1B2C3D4

static void SetPlayerOtId(u32 id)
{
    gSaveBlock2Ptr->playerTrainerId[0] = id;
    gSaveBlock2Ptr->playerTrainerId[1] = id >> 8;
    gSaveBlock2Ptr->playerTrainerId[2] = id >> 16;
    gSaveBlock2Ptr->playerTrainerId[3] = id >> 24;
}

static void ExpectHatched(struct Pokemon *mon, u32 personality, u32 exp, u32 move1)
{
    EXPECT_EQ(GetMonData(mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_IS_EGG), FALSE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_SPECIES), SPECIES_TOGEPI);
    EXPECT_EQ(GetMonData(mon, MON_DATA_HELD_ITEM), ITEM_ORAN_BERRY);
    EXPECT_EQ(GetMonData(mon, MON_DATA_EXP), exp);
    EXPECT_EQ(GetMonData(mon, MON_DATA_MOVE1), move1);
    EXPECT_EQ(GetMonData(mon, MON_DATA_PP1), GetMovePP(move1));
    EXPECT_EQ(GetMonData(mon, MON_DATA_PERSONALITY), personality);
    EXPECT_EQ(GetMonData(mon, MON_DATA_OT_ID), PLAYER_OT_ID);
    EXPECT_GT(GetMonData(mon, MON_DATA_MAX_HP), 0);
}

TEST("Averon egg hatch keeps the Pokemon intact whatever save made the egg")
{
    u32 maker;
    PARAMETRIZE { maker = PLAYER_OT_ID; }   // control: egg from this save
    PARAMETRIZE { maker = FOREIGN_OT_ID; }  // egg received from another save

    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][0];
    struct Pokemon hatched;
    u8 dexSeen[sizeof(gSaveBlock1Ptr->dexSeen)], dexCaught[sizeof(gSaveBlock1Ptr->dexCaught)];
    u8 savedOtId[sizeof(gSaveBlock2Ptr->playerTrainerId)];
    u16 savedVar = gSpecialVar_0x8004;
    u32 item = ITEM_ORAN_BERRY, personality, exp, move1;

    memcpy(dexSeen, gSaveBlock1Ptr->dexSeen, sizeof(dexSeen));
    memcpy(dexCaught, gSaveBlock1Ptr->dexCaught, sizeof(dexCaught));
    memcpy(savedOtId, gSaveBlock2Ptr->playerTrainerId, sizeof(savedOtId));

    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();

    ZeroPlayerPartyMons();
    SetPlayerOtId(maker);
    CreateEgg(mon, SPECIES_TOGEPI, FALSE);
    SetMonData(mon, MON_DATA_HELD_ITEM, &item);
    personality = GetMonData(mon, MON_DATA_PERSONALITY);
    exp = GetMonData(mon, MON_DATA_EXP);
    move1 = GetMonData(mon, MON_DATA_MOVE1);
    EXPECT_NE(move1, MOVE_NONE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_IS_EGG), TRUE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_OT_ID), maker);
    EXPECT_EQ(GetMonData(mon, MON_DATA_HELD_ITEM), ITEM_ORAN_BERRY);

    // The egg now sits in the hatching player's party.
    SetPlayerOtId(PLAYER_OT_ID);
    EXPECT_EQ(CalculatePlayerPartyCount(), 1);
    gSpecialVar_0x8004 = 0;
    ScriptHatchMon();
    ExpectHatched(mon, personality, exp, move1);

    // Normal flash save, a different live party, then load.
    hatched = *mon;
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(CalculatePlayerPartyCount(), 1);
    EXPECT_EQ(memcmp(&hatched, mon, sizeof(hatched)), 0);
    ExpectHatched(mon, personality, exp, move1);

    ZeroPlayerPartyMons();
    CalculatePlayerPartyCount();
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    memcpy(gSaveBlock1Ptr->dexSeen, dexSeen, sizeof(dexSeen));
    memcpy(gSaveBlock1Ptr->dexCaught, dexCaught, sizeof(dexCaught));
    memcpy(gSaveBlock2Ptr->playerTrainerId, savedOtId, sizeof(savedOtId));
    gSpecialVar_0x8004 = savedVar;
}
