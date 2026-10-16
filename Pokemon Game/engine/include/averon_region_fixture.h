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

struct AveronFixtureWarpMetadata
{
    uint32_t width;
    uint32_t height;
    uint32_t warpCount;
};

typedef int (*AveronFixtureWarpMapReader)(uint32_t mapGroup, uint32_t mapNum,
                                        void *context, struct AveronFixtureWarpMetadata *metadata);

// Request shape only, before any future SetWarpDestination(s8,...) call.
// A known region binding with group/number 0..127 is required (signed-byte API).
// Reader returns exactly 1 and fills all
// metadata (positive signed-halfword dimensions, byte-sized warpCount).
// Indexed warps require 0..127, index < warpCount, and x=y=-1.
// Coordinate mode uses warpId=-1 and 0..127 x/y within the map dimensions.
// No engine array access, state mutation, collision check or travel permission.
int AveronRegionFixture_IsWarpRequestValid(
    const struct AveronFixtureMapBinding *bindings, size_t bindingCount,
    uint32_t mapGroup, uint32_t mapNum, int32_t warpId, int32_t x, int32_t y,
    AveronFixtureWarpMapReader reader, void *context);

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

// Caller-supplied technical profiles only; no final Gym levels or saved data.
// Index0 is no badges; index8 is all eight badges of THIS region.
struct AveronFixtureProgressionPolicy
{
    uint32_t region;
    uint32_t levelCaps[AVERON_FIXTURE_BADGES_PER_REGION + 1];
    uint32_t obedienceCaps[AVERON_FIXTURE_BADGES_PER_REGION + 1];
};

struct AveronFixtureProgression
{
    uint8_t levelCap;
    uint8_t obedienceCap;
};

// Select from the matching region's independent badge count. Unknown or
// duplicate matching profiles and ANY selected-profile cap outside1..100
// fail without changing output. No fallback to another region or legacy cap.
// No EXP/obedience engine hooks are installed by this pure query.
int AveronRegionFixture_SelectProgression(const struct AveronFixtureBadges *badges,
    uint32_t region, const struct AveronFixtureProgressionPolicy *policies, size_t policyCount,
    struct AveronFixtureProgression *selected);

#endif
