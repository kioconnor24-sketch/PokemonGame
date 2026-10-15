#include "global.h"
#include "test/test.h"
#include "battle.h"
#include "battle_setup.h"
#include "data.h"
#include "malloc.h"
#include "trainer_pools.h"
#include "constants/abilities.h"
#include "constants/items.h"
#include "constants/moves.h"
#include "constants/songs.h"
#include "constants/battle_ai.h"
#include "constants/opponents.h"

// The normal test runner replaces gTrainers with synthetic fixtures. Include
// the generated production initializer separately to exercise Averon's data.
static const struct Trainer sAveronProductionTrainers[DIFFICULTY_COUNT][TRAINERS_COUNT] =
{
#include "../../src/data/trainers.h"
};

TEST("Averon Gym preview generates two normal Pokemon for a double battle")
{
    const struct Trainer *trainer = &sAveronProductionTrainers[DIFFICULTY_NORMAL][TRAINER_AVERON_GYM1];
    struct Pokemon *party = AllocZeroed(PARTY_SIZE * sizeof(struct Pokemon));
    EXPECT(party != NULL);
    EXPECT_EQ((u32)trainer->partySize, 2);
    EXPECT_EQ((u32)trainer->battleType, TRAINER_BATTLE_TYPE_DOUBLES);
    CreateNPCTrainerPartyFromTrainer(party, trainer);
    EXPECT_EQ(GetMonData(&party[0], MON_DATA_SPECIES), SPECIES_BUNNELBY);
    EXPECT_EQ(GetMonData(&party[0], MON_DATA_LEVEL), 10);
    EXPECT_EQ(GetMonData(&party[1], MON_DATA_SPECIES), SPECIES_LILLIPUP);
    EXPECT_EQ(GetMonData(&party[1], MON_DATA_LEVEL), 11);
    EXPECT_GT(GetMonData(&party[0], MON_DATA_HP), 0);
    EXPECT_GT(GetMonData(&party[1], MON_DATA_HP), 0);
    EXPECT_EQ(GetMonData(&party[2], MON_DATA_SPECIES), SPECIES_NONE);
    Free(party);
}
