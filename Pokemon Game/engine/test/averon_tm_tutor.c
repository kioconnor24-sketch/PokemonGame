#include "global.h"
#include "test/test.h"
#include "battle_dynamax.h"
#include "battle_z_move.h"
#include "item.h"
#include "malloc.h"
#include "move.h"
#include "party_menu.h"
#include "pokemon.h"

// The TM/HM and tutor teaching interface, on Averon's data as it is: no TM,
// tutor or learnset is added or changed. The Gym TM01 reward is tested in
// averon_gym_reward.c; here every machine is checked.

TEST("Averon every TM and HM item is in the TM pocket and teaches its own real move")
{
    // gTMHMItemMoveIds[0] is a failsafe entry; machines are 1..NUM_ALL_MACHINES.
    for (u32 i = 1; i <= NUM_ALL_MACHINES; i++)
    {
        enum Item item = GetTMHMItemId(i);
        enum Move move = GetTMHMMoveId(i);
        EXPECT_NE(item, ITEM_NONE);
        EXPECT_NE(move, MOVE_NONE);
        EXPECT_LT(move, MOVES_COUNT);
        EXPECT_EQ(GetItemPocket(item), POCKET_TM_HM);
        EXPECT_EQ(ItemIdToBattleMoveId(item), move);
        EXPECT(!IsZMove(move));
        EXPECT(!IsMaxMove(move));
    }
}

// A TM no enabled species can learn would be a dead reward.
TEST("Averon every TM and HM move can be learned by at least one enabled species")
{
    u8 *learnable = AllocZeroed((MOVES_COUNT + 7) / 8);
    for (enum Species species = 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species))
            continue;
        const u16 *learnset = GetSpeciesTeachableLearnset(species);
        for (u32 j = 0; learnset[j] != MOVE_UNAVAILABLE; j++)
        {
            if (learnset[j] < MOVES_COUNT)
                learnable[learnset[j] / 8] |= 1 << (learnset[j] % 8);
        }
    }

    u32 dead = 0;
    // gTMHMItemMoveIds[0] is a failsafe entry; machines are 1..NUM_ALL_MACHINES.
    for (u32 i = 1; i <= NUM_ALL_MACHINES; i++)
    {
        enum Move move = GetTMHMMoveId(i);
        if (!(learnable[move / 8] & (1 << (move % 8))))
        {
            DebugPrintf("No enabled species learns TM/HM move %S", GetMoveName(move));
            dead++;
        }
    }
    Free(learnable);
    EXPECT_EQ(dead, 0);
}

TEST("Averon a TM move is taught only to a species whose teachable learnset has it")
{
    enum Move move = GetTMHMMoveId(1);
    ASSUME(CanLearnTeachableMove(SPECIES_PIKACHU, MOVE_THUNDERBOLT));
    ASSUME(!CanLearnTeachableMove(SPECIES_MAGIKARP, MOVE_THUNDERBOLT));
    EXPECT(!CanLearnTeachableMove(SPECIES_EGG, move));

    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][0];
    static const u16 sMoves[MAX_MON_MOVES] = { MOVE_TACKLE, MOVE_NONE, MOVE_GROWL, MOVE_QUICK_ATTACK };
    ZeroPlayerPartyMons();
    CreateMon(mon, SPECIES_PIKACHU, 20, 0, OTID_STRUCT_PLAYER_ID);
    for (u32 j = 0; j < MAX_MON_MOVES; j++)
        SetMonData(mon, MON_DATA_MOVE1 + j, &sMoves[j]);

    // Teaching fills the empty slot with the move and its full PP.
    u32 result = GiveMoveToMon(mon, MOVE_THUNDERBOLT);
    EXPECT_EQ(result, MOVE_THUNDERBOLT);
    EXPECT_EQ(GetMonData(mon, MON_DATA_MOVE2), MOVE_THUNDERBOLT);
    EXPECT_EQ(GetMonData(mon, MON_DATA_PP2), GetMovePP(MOVE_THUNDERBOLT));

    // Teaching it again is refused; a fifth move does not fit.
    result = GiveMoveToMon(mon, MOVE_THUNDERBOLT);
    EXPECT_EQ(result, MON_ALREADY_KNOWS_MOVE);
    result = GiveMoveToMon(mon, MOVE_IRON_TAIL);
    EXPECT_EQ(result, MON_HAS_MAX_MOVES);
    EXPECT(!MonKnowsMove(mon, MOVE_IRON_TAIL));
    ZeroPlayerPartyMons();
}
