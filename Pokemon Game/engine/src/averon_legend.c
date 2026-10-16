#include "global.h"
#include "averon_legend.h"
#include "battle.h"
#include "event_data.h"
#include "script.h"
#include "constants/battle.h"

// Static encounters (legendaries, mythicals, other one-of-a-kind Pokemon)
// must never be lost through a battle the player did not win by catching.
// Only a real capture marks the encounter caught. A knockout marks it
// defeated, which the caller may allow to be retried. Every other outcome,
// including the wild Pokemon's own Roar, Whirlwind, Teleport or Emergency
// Exit (B_OUTCOME_MON_TELEPORTED) and any unknown value, leaves it available.
//
// The upstream Hoenn scripts check only WON, RAN and PLAYER_TELEPORTED and
// treat everything else as caught, which removes a legendary that teleported
// away. Use these helpers instead of copying that pattern.
//
// Callers pass their own saved flags. Nothing here allocates IDs.

enum AveronLegendResult AveronLegend_ClassifyOutcome(u32 battleOutcome)
{
    switch (battleOutcome)
    {
    case B_OUTCOME_CAUGHT:
        return AVERON_LEGEND_CAUGHT;
    case B_OUTCOME_WON:
        return AVERON_LEGEND_DEFEATED;
    default:
        return AVERON_LEGEND_AVAILABLE;
    }
}

// Flag 0 means "no flag": FlagSet and FlagClear ignore it, so a missing
// defeated flag simply records nothing for a knockout.
enum AveronLegendResult AveronLegend_RecordOutcome(u32 battleOutcome, u16 caughtFlag, u16 defeatedFlag)
{
    enum AveronLegendResult result = AveronLegend_ClassifyOutcome(battleOutcome);

    if (caughtFlag != 0 && FlagGet(caughtFlag))
        return AVERON_LEGEND_CAUGHT; // a capture is final; nothing can undo it

    switch (result)
    {
    case AVERON_LEGEND_CAUGHT:
        FlagSet(caughtFlag);
        FlagClear(defeatedFlag);
        break;
    case AVERON_LEGEND_DEFEATED:
        FlagSet(defeatedFlag);
        break;
    default:
        break;
    }
    return result;
}

bool32 AveronLegend_IsAvailable(u16 caughtFlag, u16 defeatedFlag, bool32 retryAfterDefeat)
{
    if (caughtFlag != 0 && FlagGet(caughtFlag))
        return FALSE;
    if (defeatedFlag != 0 && FlagGet(defeatedFlag))
        return retryAfterDefeat;
    return TRUE;
}

// Makes a defeated encounter available again, e.g. after a story milestone.
// Never touches a caught encounter.
void AveronLegend_AllowRetry(u16 caughtFlag, u16 defeatedFlag)
{
    if (caughtFlag != 0 && FlagGet(caughtFlag))
        return;
    FlagClear(defeatedFlag);
}

// Script natives for data/scripts/averon_legend.inc. Arguments arrive in
// VAR_0x8004 (caught flag), VAR_0x8005 (defeated flag) and VAR_0x8006
// (retry after defeat); results go to VAR_RESULT.

// Clears the previous outcome so a stale capture can never be recorded.
void AveronLegend_Begin(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1);
    gBattleOutcome = 0;
}

void AveronLegend_Record(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1 | SCREFF_SAVE);
    gSpecialVar_Result = AveronLegend_RecordOutcome(gBattleOutcome, gSpecialVar_0x8004, gSpecialVar_0x8005);
}

void AveronLegend_CheckAvailable(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1);
    gSpecialVar_Result = AveronLegend_IsAvailable(gSpecialVar_0x8004, gSpecialVar_0x8005, gSpecialVar_0x8006);
}

void AveronLegend_Retry(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1 | SCREFF_SAVE);
    AveronLegend_AllowRetry(gSpecialVar_0x8004, gSpecialVar_0x8005);
}
