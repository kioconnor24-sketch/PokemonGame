#ifndef GUARD_AVERON_LEGEND_H
#define GUARD_AVERON_LEGEND_H

struct ScriptContext;

// Outcome of a battle against a one-of-a-kind static encounter.
enum AveronLegendResult
{
    AVERON_LEGEND_AVAILABLE, // no capture or defeat: run, teleport, flee, whiteout or unknown
    AVERON_LEGEND_CAUGHT,
    AVERON_LEGEND_DEFEATED,
};

enum AveronLegendResult AveronLegend_ClassifyOutcome(u32 battleOutcome);
enum AveronLegendResult AveronLegend_RecordOutcome(u32 battleOutcome, u16 caughtFlag, u16 defeatedFlag);
bool32 AveronLegend_IsAvailable(u16 caughtFlag, u16 defeatedFlag, bool32 retryAfterDefeat);
void AveronLegend_AllowRetry(u16 caughtFlag, u16 defeatedFlag);

// Script natives (callnative ..., requests_effects=1). See data/scripts/averon_legend.inc.
void AveronLegend_Begin(struct ScriptContext *ctx);
void AveronLegend_Record(struct ScriptContext *ctx);
void AveronLegend_CheckAvailable(struct ScriptContext *ctx);
void AveronLegend_Retry(struct ScriptContext *ctx);

#endif // GUARD_AVERON_LEGEND_H
