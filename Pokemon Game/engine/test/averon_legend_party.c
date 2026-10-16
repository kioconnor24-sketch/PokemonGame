#include "global.h"
#include "test/battle.h"
#include "averon_legend.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "load_save.h"
#include "save.h"

// #53 P2 "legendary capture / party / follower / flash": a real capture,
// recorded by the LEGEND native, then the party and the record must survive a
// real flash save and load together, and the follower must stay the player's
// choice. Upstream Ho-Oh flags live in the save block; no Averon encounter,
// species choice or saved ID is involved.

static struct Pokemon *sLead;

WILD_BATTLE_TEST("Averon legend party: a captured legendary, its record and the party survive flash together")
{
    GIVEN {
        FlagClear(FLAG_CAUGHT_HO_OH);
        FlagClear(FLAG_DEFEATED_HO_OH);
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_HO_OH) { Level(70); }
    } WHEN {
        TURN { USE_ITEM(player, ITEM_MASTER_BALL); }
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_CAUGHT);
        EXPECT_EQ(AveronLegend_RecordOutcome(gBattleOutcome, FLAG_CAUGHT_HO_OH, FLAG_DEFEATED_HO_OH), AVERON_LEGEND_CAUGHT);

        // The caught legendary is the second party member; the lead still follows.
        EXPECT_EQ(CalculatePlayerPartyCount(), 2);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_SPECIES), SPECIES_HO_OH);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_LEVEL), 70);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_POKEBALL), BALL_MASTER);
        sLead = GetFirstLiveMon();
        EXPECT(sLead == &gParties[B_TRAINER_PLAYER][0]);

        // Save, lose RAM state, load: record and party come back together.
        CheckForFlashMemory();
        ASSUME(gFlashMemoryPresent);
        ClearSaveData();
        Save_ResetSaveCounters();
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        FlagClear(FLAG_CAUGHT_HO_OH);
        ZeroPlayerPartyMons();
        EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
        LoadPlayerParty();
        EXPECT_EQ(FlagGet(FLAG_CAUGHT_HO_OH), TRUE);
        EXPECT_EQ(FlagGet(FLAG_DEFEATED_HO_OH), FALSE);
        EXPECT_EQ(AveronLegend_IsAvailable(FLAG_CAUGHT_HO_OH, FLAG_DEFEATED_HO_OH, TRUE), FALSE);
        EXPECT_EQ(CalculatePlayerPartyCount(), 2);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_SPECIES), SPECIES_HO_OH);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_WOBBUFFET);

        // Moving the legendary to the front makes it the follower.
        struct Pokemon temp = gParties[B_TRAINER_PLAYER][0];
        gParties[B_TRAINER_PLAYER][0] = gParties[B_TRAINER_PLAYER][1];
        gParties[B_TRAINER_PLAYER][1] = temp;
        EXPECT_EQ(GetMonData(GetFirstLiveMon(), MON_DATA_SPECIES), SPECIES_HO_OH);

        FlagClear(FLAG_CAUGHT_HO_OH);
        FlagClear(FLAG_DEFEATED_HO_OH);
    }
}
