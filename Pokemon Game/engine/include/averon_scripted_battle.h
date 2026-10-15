#ifndef GUARD_AVERON_SCRIPTED_BATTLE_H
#define GUARD_AVERON_SCRIPTED_BATTLE_H

struct ScriptContext;

// Script natives (callnative ..., requests_effects=1). See data/scripts/averon_scripted_battle.inc.
void AveronScriptedBattle_Begin(struct ScriptContext *ctx);
void AveronScriptedBattle_Finish(struct ScriptContext *ctx);
void AveronScriptedBattle_RecoverInPlace(struct ScriptContext *ctx);
void AveronScriptedBattle_PrepareRespawn(struct ScriptContext *ctx);
void AveronScriptedBattle_DoRespawnWarp(struct ScriptContext *ctx);

bool32 AveronScriptedBattle_IsPlayerDefeated(u32 battleOutcome);
bool32 AveronScriptedBattle_IsNoWhiteoutActive(void);
void AveronScriptedBattle_ClearStaleNoWhiteout(void);

#endif // GUARD_AVERON_SCRIPTED_BATTLE_H
