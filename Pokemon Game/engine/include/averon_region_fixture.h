#ifndef GUARD_AVERON_REGION_FIXTURE_H
#define GUARD_AVERON_REGION_FIXTURE_H

#include <stdint.h>
#include <stddef.h>

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

typedef int (*AveronFixtureBadgeReader)(uint32_t region, uint32_t badgeNumber, void *context);

// Read both banks using only valid region IDs and badge numbers 1..8.
// Reader returns exactly 0/1; any other result aborts without changing output.
// Context may be NULL or alias output. No saved IDs/format are assigned here.
int AveronRegionFixture_CaptureBadges(AveronFixtureBadgeReader reader, void *context,
                                    struct AveronFixtureBadges *badges);

struct AveronFixtureMapBinding
{
    uint8_t mapGroup;
    uint8_t mapNum;
    uint32_t region;
};

// The caller supplies an array of bindingCount valid entries. A missing,
// out-of-range, unknown-region or duplicate matching identity returns UNKNOWN.
// These bindings are temporary inputs, not registered or playable maps.
enum AveronFixtureRegion AveronRegionFixture_ResolveMap(
    const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
    uint32_t mapGroup, uint32_t mapNum);

// Region/discovery policy only. The engine must separately enforce its
// existing license, partner and source-map restrictions before starting Fly.
// No destination/visited flags, transport routes or map content are created.
int AveronRegionFixture_IsFlyDestinationEligible(
    const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
    uint32_t currentGroup, uint32_t currentNum,
    uint32_t destinationGroup, uint32_t destinationNum, int destinationVisited);

typedef int (*AveronFixtureHealMapReader)(uint32_t healId, void *context,
                                        uint32_t *mapGroup, uint32_t *mapNum);

// Select metadata only; never heals, warps, spends money or changes saved state.
// Zero is no healer. Reader must return exactly 1 and supply a known map.
// A caller-supplied fallback is subject to the same current-region validation.
// Failure leaves output untouched; a failed identical ID is not read twice.
int AveronRegionFixture_SelectRegionalHeal(
    const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
    uint32_t currentGroup, uint32_t currentNum,
    uint32_t preferredHealId, uint32_t fallbackHealId,
    AveronFixtureHealMapReader reader, void *context, uint32_t *selectedHealId);

// Badge numbers are 1..8, with bit 0 representing Badge 1 in each bank.
// Full-width region inputs reject invalid values before -fshort-enums can
// truncate them into a valid bank. This struct is not a persistent format.
// Null snapshots, unknown regions and invalid numbers fail closed.
int AveronRegionFixture_HasBadge(const struct AveronFixtureBadges *badges,
                               uint32_t region, uint32_t badgeNumber);
uint32_t AveronRegionFixture_CountBadges(const struct AveronFixtureBadges *badges,
                                       uint32_t region);

#endif
