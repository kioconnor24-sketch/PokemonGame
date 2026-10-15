#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "event_data.h"

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
