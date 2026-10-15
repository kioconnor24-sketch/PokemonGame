#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "event_data.h"
#include "battle.h"
#include "pokemon.h"

static void AcceptErrand(u32 house)
{
    switch (house)
    {
    case 1: RUN_OVERWORLD_SCRIPT(call Saltmere_AcceptGreenhouse;); break;
    case 2: RUN_OVERWORLD_SCRIPT(call Saltmere_AcceptWorkshop;); break;
    case 3: RUN_OVERWORLD_SCRIPT(call Saltmere_AcceptHarbor;); break;
    }
}

TEST("Averon first accepted errand survives all six household orders")
{
    u32 first = 1, second = 2, third = 3;
    PARAMETRIZE { first=1; second=2; third=3; }
    PARAMETRIZE { first=1; second=3; third=2; }
    PARAMETRIZE { first=2; second=1; third=3; }
    PARAMETRIZE { first=2; second=3; third=1; }
    PARAMETRIZE { first=3; second=1; third=2; }
    PARAMETRIZE { first=3; second=2; third=1; }
    VarSet(VAR_AVERON_FIRST_HOUSE, 0);
    VarSet(VAR_AVERON_GREENHOUSE, 0);
    VarSet(VAR_AVERON_WORKSHOP, 0);
    VarSet(VAR_AVERON_HARBOR, 0);
    FlagClear(FLAG_AVERON_STARTER);
    AcceptErrand(first);
    EXPECT_EQ(VarGet(VAR_AVERON_FIRST_HOUSE), first);
    AcceptErrand(second);
    AcceptErrand(third);
    EXPECT_EQ(VarGet(VAR_AVERON_FIRST_HOUSE), first);
    EXPECT_EQ(VarGet(VAR_AVERON_GREENHOUSE), 1);
    EXPECT_EQ(VarGet(VAR_AVERON_WORKSHOP), 1);
    EXPECT_EQ(VarGet(VAR_AVERON_HARBOR), 1);
    EXPECT_EQ(FlagGet(FLAG_AVERON_STARTER), FALSE);
}

TEST("Averon reaccepting errands preserves active and completed progress")
{
    u32 state = 1;
    PARAMETRIZE { state=1; }
    PARAMETRIZE { state=2; }
    VarSet(VAR_AVERON_FIRST_HOUSE, 3);
    VarSet(VAR_AVERON_GREENHOUSE, state);
    VarSet(VAR_AVERON_WORKSHOP, state);
    VarSet(VAR_AVERON_HARBOR, state);
    AcceptErrand(1);
    AcceptErrand(2);
    AcceptErrand(3);
    EXPECT_EQ(VarGet(VAR_AVERON_FIRST_HOUSE), 3);
    EXPECT_EQ(VarGet(VAR_AVERON_GREENHOUSE), state);
    EXPECT_EQ(VarGet(VAR_AVERON_WORKSHOP), state);
    EXPECT_EQ(VarGet(VAR_AVERON_HARBOR), state);
}

static void GiveStarter(u32 house)
{
    switch (house)
    {
    case 1: RUN_OVERWORLD_SCRIPT(call Saltmere_GiveSnivy;); break;
    case 2: RUN_OVERWORLD_SCRIPT(call Saltmere_GiveFennekin;); break;
    case 3: RUN_OVERWORLD_SCRIPT(call Saltmere_GivePiplup;); break;
    }
}

TEST("Averon starter awards respect party capacity and cannot be duplicated")
{
    u32 house = 1, occupied = 0;
    const u16 species[] = {SPECIES_NONE, SPECIES_SNIVY, SPECIES_FENNEKIN, SPECIES_PIPLUP};
    const u16 mira[] = {SPECIES_NONE, SPECIES_PIPLUP, SPECIES_SNIVY, SPECIES_FENNEKIN};
    PARAMETRIZE { house=1; occupied=0; }
    PARAMETRIZE { house=2; occupied=0; }
    PARAMETRIZE { house=3; occupied=0; }
    PARAMETRIZE { house=1; occupied=5; }
    PARAMETRIZE { house=2; occupied=5; }
    PARAMETRIZE { house=3; occupied=5; }
    PARAMETRIZE { house=1; occupied=6; }
    PARAMETRIZE { house=2; occupied=6; }
    PARAMETRIZE { house=3; occupied=6; }
    ZeroPlayerPartyMons();
    for (u32 slot=0; slot<occupied; ++slot)
        CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][slot], SPECIES_WOBBUFFET, 5, 0);
    CalculatePlayerPartyCount();
    FlagClear(FLAG_AVERON_STARTER);
    VarSet(VAR_AVERON_MIRA_STARTER, SPECIES_NONE);
    GiveStarter(house);
    if (occupied == PARTY_SIZE)
    {
        EXPECT_EQ(VarGet(VAR_RESULT), MON_CANT_GIVE);
        EXPECT_EQ(FlagGet(FLAG_AVERON_STARTER), FALSE);
        EXPECT_EQ(VarGet(VAR_AVERON_MIRA_STARTER), SPECIES_NONE);
        EXPECT_EQ(CalculatePlayerPartyCount(), PARTY_SIZE);
    }
    else
    {
        EXPECT_EQ(VarGet(VAR_RESULT), MON_GIVEN_TO_PARTY);
        EXPECT_EQ(FlagGet(FLAG_AVERON_STARTER), TRUE);
        EXPECT_EQ(VarGet(VAR_AVERON_MIRA_STARTER), mira[house]);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][occupied], MON_DATA_SPECIES), species[house]);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][occupied], MON_DATA_LEVEL), 5);
        EXPECT_EQ(CalculatePlayerPartyCount(), occupied+1);
        GiveStarter(house);
        EXPECT_EQ(VarGet(VAR_RESULT), MON_CANT_GIVE);
        EXPECT_EQ(CalculatePlayerPartyCount(), occupied+1);
    }
    for (u32 slot=0; slot<occupied; ++slot)
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_SPECIES), SPECIES_WOBBUFFET);
}
