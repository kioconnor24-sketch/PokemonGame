#ifndef GUARD_AVERON_REGION_PROGRESSION_H
#define GUARD_AVERON_REGION_PROGRESSION_H

#include "averon_region_save.h"

// Region-aware progression: which badge bank, level cap and obedience level
// apply in the active region (averon_region_save.h holds the region state).
//
// A region profile gives the level cap and the obedience level for each count
// of THAT region's badges (index 0 = no badges, 8 = all eight). Every value is
// 1..MAX_LEVEL; an obedience level of MAX_LEVEL means every Pokemon obeys.
//
// Averon has no profile: it keeps the engine's existing flag ladders in
// caps.c and GetAttackerObedienceForAction exactly as they are. The Sinnoh
// profile is empty until the owner sets its numbers (Issue #15 / #53); while
// a region has no profile, the existing behaviour also applies there. This
// file allocates no saved ID, flag, var or save field.

struct AveronProgressionProfile
{
    u8 levelCaps[AVERON_REGION_BADGES + 1];
    u8 obedienceLevels[AVERON_REGION_BADGES + 1];
};

// The active region's own badges. NONE or an invalid region has none.
u32 AveronProgression_GetActiveRegion(void);
bool32 AveronProgression_HasActiveRegionBadge(u32 badgeNumber);
u32 AveronProgression_CountActiveRegionBadges(void);

// TRUE and the value when the active region has a profile; FALSE (output
// untouched) when the existing engine behaviour applies.
bool32 AveronProgression_GetRegionalLevelCap(u32 *levelCap);
bool32 AveronProgression_GetRegionalObedienceLevel(u32 *obedienceLevel);

bool32 AveronProgression_IsProfileValid(const struct AveronProgressionProfile *profile);

#if TESTING
// Tests install a parameterized profile; NULL removes it. An invalid profile
// is refused and leaves the previous one in place.
bool32 AveronProgression_SetTestProfile(u32 region, const struct AveronProgressionProfile *profile);
#endif

#endif // GUARD_AVERON_REGION_PROGRESSION_H
