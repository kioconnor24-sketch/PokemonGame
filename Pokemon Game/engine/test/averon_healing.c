#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "battle.h"
#include "pokemon.h"
#include "move.h"

TEST("Averon home clinic and rival healing restores HP status and PP")
{
    u32 damagedHP=1, status=STATUS1_POISON, emptyPP=0, move=MOVE_TACKLE;
    u32 heldItem=ITEM_ORAN_BERRY;
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][0], SPECIES_SNIVY, 5, 0);
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][1], SPECIES_BUNNELBY, 5, 0);
    CalculatePlayerPartyCount();
    for (u32 slot=0; slot<2; ++slot)
    {
        SetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HP, &damagedHP);
        SetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_STATUS, &status);
        SetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_MOVE1, &move);
        SetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_PP1, &emptyPP);
        SetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HELD_ITEM, &heldItem);
    }
    RUN_OVERWORLD_SCRIPT(special HealPlayerParty;);
    for (u32 slot=0; slot<2; ++slot)
    {
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HP),
                  GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_MAX_HP));
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_STATUS), 0);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_PP1), GetMovePP(MOVE_TACKLE));
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HELD_ITEM), ITEM_ORAN_BERRY);
    }
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_SNIVY);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_SPECIES), SPECIES_BUNNELBY);
    EXPECT_EQ(CalculatePlayerPartyCount(), 2);
}
