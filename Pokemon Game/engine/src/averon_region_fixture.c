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
