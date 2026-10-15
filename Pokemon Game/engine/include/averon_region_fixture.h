#ifndef GUARD_AVERON_REGION_FIXTURE_H
#define GUARD_AVERON_REGION_FIXTURE_H

#include <stdint.h>

// Experimental pure queries, not a save format or the engine's enum Region.
// Bind to persistent flags only after the coordinated TWO-REGION integration.
enum AveronFixtureRegion
{
    AVERON_FIXTURE_UNKNOWN,
    AVERON_FIXTURE_AVERON,
    AVERON_FIXTURE_SINNOH,
};

#define AVERON_FIXTURE_BADGES_PER_REGION 8

struct AveronFixtureBadges
{
    uint8_t averon;
    uint8_t sinnoh;
};

// Badge numbers are 1..8, with bit 0 representing Badge 1 in each bank.
// Null snapshots, unknown regions and invalid numbers fail closed.
int AveronRegionFixture_HasBadge(const struct AveronFixtureBadges *badges,
                               enum AveronFixtureRegion region, uint32_t badgeNumber);
uint32_t AveronRegionFixture_CountBadges(const struct AveronFixtureBadges *badges,
                                       enum AveronFixtureRegion region);

#endif
