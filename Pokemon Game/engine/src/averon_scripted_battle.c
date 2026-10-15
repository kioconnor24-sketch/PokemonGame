#include "global.h"
#include "averon_scripted_battle.h"
#include "battle.h"
#include "event_data.h"
#include "field_screen_effect.h"
#include "field_player_avatar.h"
#include "overworld.h"
#include "script.h"
#include "script_pokemon_util.h"
#include "constants/battle.h"

// Scripted battles (story loss, operative chain, Gym ambush) let the player
// lose without whiting out. B_FLAG_NO_WHITEOUT makes battle_setup.c return to
// the calling script and skips the prize-money payout in the lost-battle
// script. Every path out of a scripted battle clears the flag again so it can
// never carry into an ordinary battle.

bool32 AveronScriptedBattle_IsPlayerDefeated(u32 battleOutcome)
{
    switch (battleOutcome)
    {
    case B_OUTCOME_LOST:
    case B_OUTCOME_DREW:
    case B_OUTCOME_FORFEITED:
        return TRUE;
    default:
        return FALSE;
    }
}

bool32 AveronScriptedBattle_IsNoWhiteoutActive(void)
{
    return FlagGet(B_FLAG_NO_WHITEOUT);
}

void AveronScriptedBattle_ClearStaleNoWhiteout(void)
{
    FlagClear(B_FLAG_NO_WHITEOUT);
}

// Clears the previous outcome so Finish can never report a stale defeat.
void AveronScriptedBattle_Begin(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1 | SCREFF_SAVE);
    FlagSet(B_FLAG_NO_WHITEOUT);
    gBattleOutcome = 0;
}

// Reports the result in VAR_RESULT (TRUE = player lost) and always clears the
// flag. Does not heal: chain battles keep their damage between fights.
void AveronScriptedBattle_Finish(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1 | SCREFF_SAVE);
    FlagClear(B_FLAG_NO_WHITEOUT);
    gSpecialVar_Result = AveronScriptedBattle_IsPlayerDefeated(gBattleOutcome);
}

// Story loss where the scene continues on the spot.
void AveronScriptedBattle_RecoverInPlace(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1 | SCREFF_SAVE);
    FlagClear(B_FLAG_NO_WHITEOUT);
    HealPlayerParty();
}

// Story loss that sends the player back to the last heal location, like a
// whiteout but without the money loss. Split from the warp so it can be tested
// without a loaded overworld.
void AveronScriptedBattle_PrepareRespawn(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1 | SCREFF_SAVE);
    FlagClear(B_FLAG_NO_WHITEOUT);
    HealPlayerParty();
    SetWarpDestinationToLastHealLocation();
}

void AveronScriptedBattle_DoRespawnWarp(struct ScriptContext *ctx)
{
    Script_RequestEffects(SCREFF_V1 | SCREFF_SAVE | SCREFF_HARDWARE);
    DoWarp();
    ResetInitialPlayerAvatarState();
    ctx->waitAfterCallNative = TRUE;
}
