#include "averon_region_fixture.h"

static uint8_t GetBadgeMask(const struct AveronFixtureBadges *badges,
                            enum AveronFixtureRegion region)
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
                               enum AveronFixtureRegion region, uint32_t badgeNumber)
{
    if (badgeNumber == 0 || badgeNumber > AVERON_FIXTURE_BADGES_PER_REGION)
        return 0;
    return (GetBadgeMask(badges, region) & (1u << (badgeNumber - 1))) != 0;
}

uint32_t AveronRegionFixture_CountBadges(const struct AveronFixtureBadges *badges,
                                       enum AveronFixtureRegion region)
{
    uint8_t mask = GetBadgeMask(badges, region);
    uint32_t count = 0;
    for (; mask; mask >>= 1)
        count += mask & 1u;
    return count;
}
