#include "global.h"
#include "test/test.h"
#include "battle.h"
#include "battle_setup.h"
#include "data.h"
#include "malloc.h"
#include "item.h"
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

TEST("Averon Gym TM01 reward resolves to Work Up")
{
    EXPECT_EQ(GetItemTMHMIndex(ITEM_TM_WORK_UP), 1);
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_WORK_UP), MOVE_WORK_UP);
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM01), MOVE_WORK_UP);
    EXPECT_EQ(GetItemPocket(ITEM_TM_WORK_UP), POCKET_TM_HM);
}

TEST("Averon Elio generates the approved team with Work Up and a healing berry")
{
    const struct Trainer *trainer=&sAveronProductionTrainers[DIFFICULTY_NORMAL][TRAINER_AVERON_ELIO];
    struct Pokemon *party=AllocZeroed(PARTY_SIZE*sizeof(struct Pokemon));
    bool32 knowsWorkUp=FALSE;
    EXPECT(party != NULL);
    EXPECT_EQ((u32)trainer->partySize, 3);
    EXPECT(trainer->aiFlags & AI_FLAG_CHECK_VIABILITY);
    EXPECT_EQ(trainer->aiFlags & AI_FLAG_OMNISCIENT, 0);
    CreateNPCTrainerPartyFromTrainer(party,trainer);
    EXPECT_EQ(GetMonData(&party[0],MON_DATA_SPECIES),SPECIES_BUNNELBY);
    EXPECT_EQ(GetMonData(&party[0],MON_DATA_LEVEL),12);
    EXPECT_EQ(GetMonData(&party[1],MON_DATA_SPECIES),SPECIES_LECHONK);
    EXPECT_EQ(GetMonData(&party[1],MON_DATA_LEVEL),13);
    EXPECT_EQ(GetMonData(&party[2],MON_DATA_SPECIES),SPECIES_LILLIPUP);
    EXPECT_EQ(GetMonData(&party[2],MON_DATA_LEVEL),15);
    EXPECT_EQ(GetMonData(&party[2],MON_DATA_HELD_ITEM),ITEM_ORAN_BERRY);
    for (u32 move=0;move<MAX_MON_MOVES;++move)
        if (GetMonData(&party[2],MON_DATA_MOVE1+move)==MOVE_WORK_UP)
            knowsWorkUp=TRUE;
    EXPECT(knowsWorkUp);
    Free(party);
}

TEST("Averon coast trainer reuses the unused slot without expanding save flags")
{
    const struct Trainer *trainer=&sAveronProductionTrainers[DIFFICULTY_NORMAL][TRAINER_AVERON_COAST];
    struct Pokemon *party=AllocZeroed(PARTY_SIZE*sizeof(struct Pokemon));
    EXPECT(party != NULL);
    EXPECT_EQ(TRAINER_AVERON_COAST,568);
    EXPECT_EQ(MAX_TRAINERS_COUNT_EMERALD,864);
    EXPECT_EQ((u32)trainer->partySize,2);
    CreateNPCTrainerPartyFromTrainer(party,trainer);
    EXPECT_EQ(GetMonData(&party[0],MON_DATA_SPECIES),SPECIES_WINGULL);
    EXPECT_EQ(GetMonData(&party[0],MON_DATA_LEVEL),14);
    EXPECT_EQ(GetMonData(&party[1],MON_DATA_SPECIES),SPECIES_ROOKIDEE);
    EXPECT_EQ(GetMonData(&party[1],MON_DATA_LEVEL),15);
    Free(party);
}
