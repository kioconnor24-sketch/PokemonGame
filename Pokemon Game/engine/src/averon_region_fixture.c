#include "averon_region_fixture.h"

int AveronRegionFixture_CaptureBadges(AveronFixtureBadgeReader reader, void *context,
                                    struct AveronFixtureBadges *badges)
{
    const uint32_t regions[] = {AVERON_FIXTURE_AVERON, AVERON_FIXTURE_SINNOH};
    struct AveronFixtureBadges snapshot = {0, 0};
    if (!reader || !badges)
        return 0;
    for (size_t i = 0; i < sizeof(regions) / sizeof(regions[0]); ++i)
    {
        uint8_t *mask = regions[i] == AVERON_FIXTURE_AVERON ? &snapshot.averon : &snapshot.sinnoh;
        for (uint32_t number = 1; number <= AVERON_FIXTURE_BADGES_PER_REGION; ++number)
        {
            int value = reader(regions[i], number, context);
            if (value != 0 && value != 1)
                return 0;
            if (value)
                *mask |= 1u << (number - 1);
        }
    }
    *badges = snapshot;
    return 1;
}

enum AveronFixtureRegion AveronRegionFixture_ResolveMap(
    const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
    uint32_t mapGroup, uint32_t mapNum)
{
    enum AveronFixtureRegion found = AVERON_FIXTURE_UNKNOWN;
    int matched = 0;
    if (!bindings || mapGroup > UINT8_MAX || mapNum > UINT8_MAX)
        return AVERON_FIXTURE_UNKNOWN;
    for (size_t i = 0; i < bindingCount; ++i)
    {
        if (bindings[i].mapGroup != mapGroup || bindings[i].mapNum != mapNum)
            continue;
        if (matched || (bindings[i].region != AVERON_FIXTURE_AVERON
                     && bindings[i].region != AVERON_FIXTURE_SINNOH))
            return AVERON_FIXTURE_UNKNOWN;
        matched = 1;
        found = (enum AveronFixtureRegion) bindings[i].region;
    }
    return found;
}

int AveronRegionFixture_IsFlyDestinationEligible(
    const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
    uint32_t currentGroup, uint32_t currentNum,
    uint32_t destinationGroup, uint32_t destinationNum, int destinationVisited)
{
    if (destinationVisited != 1)
        return 0;
    uint32_t currentRegion = AveronRegionFixture_ResolveMap(bindings, bindingCount, currentGroup, currentNum);
    uint32_t destinationRegion = AveronRegionFixture_ResolveMap(bindings, bindingCount, destinationGroup, destinationNum);
    if (currentRegion == AVERON_FIXTURE_UNKNOWN || destinationRegion == AVERON_FIXTURE_UNKNOWN)
        return 0;
    return currentRegion == destinationRegion;
}

int AveronRegionFixture_IsWarpRequestValid(
    const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
    uint32_t mapGroup, uint32_t mapNum, int32_t warpId, int32_t x, int32_t y,
    AveronFixtureWarpMapReader reader, void *context)
{
    if (!reader || mapGroup > INT8_MAX || mapNum > INT8_MAX || warpId < -1 || warpId > INT8_MAX)
        return 0;
    if (warpId >= 0)
    {
        if (x != -1 || y != -1)
            return 0;
    }
    else if (x < 0 || y < 0 || x > INT8_MAX || y > INT8_MAX)
        return 0;
    if (AveronRegionFixture_ResolveMap(bindings, bindingCount, mapGroup, mapNum) == AVERON_FIXTURE_UNKNOWN)
        return 0;
    struct AveronFixtureWarpMetadata metadata = {UINT32_MAX, UINT32_MAX, UINT32_MAX};
    if (reader(mapGroup, mapNum, context, &metadata) != 1)
        return 0;
    if (metadata.width == 0 || metadata.width > INT16_MAX
        || metadata.height == 0 || metadata.height > INT16_MAX || metadata.warpCount > UINT8_MAX)
        return 0;
    if (warpId >= 0)
        return (uint32_t)warpId < metadata.warpCount;
    return (uint32_t)x < metadata.width && (uint32_t)y < metadata.height;
}

static int HealMatchesRegion(const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
                             uint32_t region, uint32_t healId,
                             AveronFixtureHealMapReader reader, void *context)
{
    uint32_t mapGroup = UINT32_MAX, mapNum = UINT32_MAX;
    if (healId == 0 || reader(healId, context, &mapGroup, &mapNum) != 1)
        return 0;
    return AveronRegionFixture_ResolveMap(bindings, bindingCount, mapGroup, mapNum) == region;
}

int AveronRegionFixture_SelectRegionalHeal(
    const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
    uint32_t currentGroup, uint32_t currentNum,
    uint32_t preferredHealId, uint32_t fallbackHealId,
    AveronFixtureHealMapReader reader, void *context, uint32_t *selectedHealId)
{
    if (!reader || !selectedHealId)
        return 0;
    uint32_t region = AveronRegionFixture_ResolveMap(bindings, bindingCount, currentGroup, currentNum);
    if (region == AVERON_FIXTURE_UNKNOWN)
        return 0;
    uint32_t candidates[] = {preferredHealId, fallbackHealId};
    for (size_t i = 0; i < sizeof(candidates) / sizeof(candidates[0]); ++i)
    {
        if (i != 0 && candidates[i] == candidates[0])
            continue;
        if (HealMatchesRegion(bindings, bindingCount, region, candidates[i], reader, context))
        {
            *selectedHealId = candidates[i];
            return 1;
        }
    }
    return 0;
}

static uint8_t GetBadgeMask(const struct AveronFixtureBadges *badges,
                            uint32_t region)
{
    if (!badges)
        return 0;
    switch (region)
    {
    case AVERON_FIXTURE_AVERON:
        return badges->averon;
    case AVERON_FIXTURE_SINNOH:
        return badges->sinnoh;
    default:
        return 0;
    }
}

int AveronRegionFixture_HasBadge(const struct AveronFixtureBadges *badges,
                               uint32_t region, uint32_t badgeNumber)
{
    if (badgeNumber == 0 || badgeNumber > AVERON_FIXTURE_BADGES_PER_REGION)
        return 0;
    return (GetBadgeMask(badges, region) & (1u << (badgeNumber - 1))) != 0;
}

uint32_t AveronRegionFixture_CountBadges(const struct AveronFixtureBadges *badges,
                                       uint32_t region)
{
    uint8_t mask = GetBadgeMask(badges, region);
    uint32_t count = 0;
    for (; mask; mask >>= 1)
        count += mask & 1u;
    return count;
}

int AveronRegionFixture_SelectProgression(const struct AveronFixtureBadges *badges,
    uint32_t region, const struct AveronFixtureProgressionPolicy *policies, size_t policyCount,
    struct AveronFixtureProgression *selected)
{
    if (!badges || !policies || !selected
        || (region != AVERON_FIXTURE_AVERON && region != AVERON_FIXTURE_SINNOH))
        return 0;
    const struct AveronFixtureProgressionPolicy *policy = NULL;
    for (size_t i = 0; i < policyCount; ++i)
    {
        if (policies[i].region != region)
            continue;
        if (policy)
            return 0;
        policy = &policies[i];
    }
    if (!policy)
        return 0;
    for (size_t i = 0; i <= AVERON_FIXTURE_BADGES_PER_REGION; ++i)
        if (policy->levelCaps[i] == 0 || policy->levelCaps[i] > 100
            || policy->obedienceCaps[i] == 0 || policy->obedienceCaps[i] > 100)
            return 0;
    uint32_t count = AveronRegionFixture_CountBadges(badges, region);
    const struct AveronFixtureProgression result = {
        .levelCap = policy->levelCaps[count],
        .obedienceCap = policy->obedienceCaps[count],
    };
    *selected = result;
    return 1;
}
