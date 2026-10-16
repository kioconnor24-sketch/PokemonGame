#include "global.h"
#include "averon_region_progression.h"

// Per-region profiles. Averon stays on the engine's existing ladders (NULL).
// Sinnoh's numbers are owner-reserved: NULL until they are decided.
static const struct AveronProgressionProfile *const sRegionProfiles[AVERON_SAVE_REGION_COUNT] =
{
    [AVERON_SAVE_REGION_NONE] = NULL,
    [AVERON_SAVE_REGION_AVERON] = NULL,
    [AVERON_SAVE_REGION_SINNOH] = NULL,
};

#if TESTING
static const struct AveronProgressionProfile *sTestProfiles[AVERON_SAVE_REGION_COUNT];
#endif

static const struct AveronProgressionProfile *GetProfile(u32 region)
{
    if (region <= AVERON_SAVE_REGION_NONE || region >= AVERON_SAVE_REGION_COUNT)
        return NULL;
#if TESTING
    if (sTestProfiles[region] != NULL)
        return sTestProfiles[region];
#endif
    return sRegionProfiles[region];
}

bool32 AveronProgression_IsProfileValid(const struct AveronProgressionProfile *profile)
{
    if (profile == NULL)
        return FALSE;
    for (u32 i = 0; i <= AVERON_REGION_BADGES; i++)
    {
        if (profile->levelCaps[i] == 0 || profile->levelCaps[i] > MAX_LEVEL)
            return FALSE;
        if (profile->obedienceLevels[i] == 0 || profile->obedienceLevels[i] > MAX_LEVEL)
            return FALSE;
    }
    return TRUE;
}

u32 AveronProgression_GetActiveRegion(void)
{
    return AveronRegion_GetActive();
}

bool32 AveronProgression_HasActiveRegionBadge(u32 badgeNumber)
{
    return AveronRegion_HasBadge(AveronProgression_GetActiveRegion(), badgeNumber);
}

u32 AveronProgression_CountActiveRegionBadges(void)
{
    return AveronRegion_CountBadges(AveronProgression_GetActiveRegion());
}

// A profile that fails validation is treated as absent, so a bad table can
// never produce a cap of 0 or above MAX_LEVEL.
static const struct AveronProgressionProfile *GetActiveProfile(void)
{
    const struct AveronProgressionProfile *profile = GetProfile(AveronProgression_GetActiveRegion());
    return AveronProgression_IsProfileValid(profile) ? profile : NULL;
}

bool32 AveronProgression_GetRegionalLevelCap(u32 *levelCap)
{
    const struct AveronProgressionProfile *profile = GetActiveProfile();
    if (profile == NULL || levelCap == NULL)
        return FALSE;
    *levelCap = profile->levelCaps[AveronProgression_CountActiveRegionBadges()];
    return TRUE;
}

bool32 AveronProgression_GetRegionalObedienceLevel(u32 *obedienceLevel)
{
    const struct AveronProgressionProfile *profile = GetActiveProfile();
    if (profile == NULL || obedienceLevel == NULL)
        return FALSE;
    *obedienceLevel = profile->obedienceLevels[AveronProgression_CountActiveRegionBadges()];
    return TRUE;
}

#if TESTING
bool32 AveronProgression_SetTestProfile(u32 region, const struct AveronProgressionProfile *profile)
{
    if (region <= AVERON_SAVE_REGION_NONE || region >= AVERON_SAVE_REGION_COUNT)
        return FALSE;
    if (profile != NULL && !AveronProgression_IsProfileValid(profile))
        return FALSE;
    sTestProfiles[region] = profile;
    return TRUE;
}
#endif
