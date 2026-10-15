#include "global.h"
#include "test/test.h"
#include "event_data.h"
#include "load_save.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "averon_region_fixture.h"
#include "constants/maps.h"
#include "heal_location.h"
#include "overworld.h"
#include "constants/heal_locations.h"

// Opaque test-only handle, outside the engine's healer registry. Never saved.
#define FIXTURE_SINNOH_HEAL 0x10000

struct HealReadFixture
{
    u32 calls;
    int mode;
};

static const struct AveronFixtureMapBinding sHealFixtureMaps[] = {
    {MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), AVERON_FIXTURE_AVERON},
    {MAP_GROUP(MAP_ALDERFIELD), MAP_NUM(MAP_ALDERFIELD), AVERON_FIXTURE_AVERON},
    {255, 1, AVERON_FIXTURE_SINNOH},
};

static int ReadHealFixture(uint32_t id, void *context, uint32_t *group, uint32_t *number)
{
    struct HealReadFixture *fixture = context;
    fixture->calls++;
    if (fixture->mode == 1)
        return 0;
    if (fixture->mode == 2)
        return 2;
    if (fixture->mode == 3)
    {
        *group = 259;
        *number = 7;
        return 1;
    }
    if (fixture->mode == 4)
        return 1; // Deliberately fails to initialize metadata outputs.
    if (id == FIXTURE_SINNOH_HEAL)
    {
        *group = 255;
        *number = 1;
        return 1;
    }
    const struct HealLocation *heal = GetHealLocation(id);
    if (!heal)
        return 0;
    *group = (u8) heal->mapGroup;
    *number = (u8) heal->mapNum;
    return 1;
}

TEST("Averon region fixture validates existing heal metadata and region fallback")
{
    struct HealReadFixture reader = {0};
    u32 selected = 0xDEADBEEF;
    struct WarpData before;
    memcpy(&before, &gSaveBlock1Ptr->lastHealLocation, sizeof(before));
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
        MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), HEAL_LOCATION_ALDERFIELD,
        HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F, ReadHealFixture, &reader, &selected), TRUE);
    EXPECT_EQ(selected, HEAL_LOCATION_ALDERFIELD);
    EXPECT_EQ(reader.calls, 1);
    reader.calls = 0;
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
        MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), FIXTURE_SINNOH_HEAL,
        HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F, ReadHealFixture, &reader, &selected), TRUE);
    EXPECT_EQ(selected, HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F);
    EXPECT_EQ(reader.calls, 2);
    reader.calls = 0;
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
        255, 1, HEAL_LOCATION_ALDERFIELD, FIXTURE_SINNOH_HEAL, ReadHealFixture, &reader, &selected), TRUE);
    EXPECT_EQ(selected, FIXTURE_SINNOH_HEAL);
    EXPECT_EQ(reader.calls, 2);
    EXPECT_EQ(memcmp(&before, &gSaveBlock1Ptr->lastHealLocation, sizeof(before)), 0);
}

TEST("Averon region fixture rejects invalid healer IDs and never retries the same failed ID")
{
    const u32 invalid[] = {0, FIXTURE_SINNOH_HEAL + 1, 0xFFFFFFFF};
    for (u32 i = 0; i < ARRAY_COUNT(invalid); ++i)
    {
        struct HealReadFixture reader = {0};
        u32 selected = 0xDEADBEEF;
        EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
            MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), invalid[i],
            HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F, ReadHealFixture, &reader, &selected), TRUE);
        EXPECT_EQ(selected, HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F);
        reader.calls = 0;
        selected = 0xDEADBEEF;
        EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
            MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), invalid[i], invalid[i],
            ReadHealFixture, &reader, &selected), FALSE);
        EXPECT_EQ(reader.calls, invalid[i] == 0 ? 0 : 1);
        EXPECT_EQ(selected, 0xDEADBEEF);
    }
}

TEST("Averon region fixture refuses malformed or unwritten healer metadata")
{
    for (int mode = 1; mode <= 4; ++mode)
    {
        struct HealReadFixture reader = {.mode = mode};
        u32 selected = 0xDEADBEEF;
        EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
            MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), HEAL_LOCATION_ALDERFIELD,
            0, ReadHealFixture, &reader, &selected), FALSE);
        EXPECT_EQ(selected, 0xDEADBEEF);
        EXPECT_EQ(reader.calls, 1);
    }
}

TEST("Averon region fixture validates recovery inputs before calling the healer reader")
{
    struct HealReadFixture reader = {0};
    u32 selected = 0xDEADBEEF;
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
        MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), 1, 2, NULL, &reader, &selected), FALSE);
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
        MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), 1, 2, ReadHealFixture, &reader, NULL), FALSE);
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, 0,
        MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), 1, 2, ReadHealFixture, &reader, &selected), FALSE);
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
        256, 0, 1, 2, ReadHealFixture, &reader, &selected), FALSE);
    struct AveronFixtureMapBinding maps[ARRAY_COUNT(sHealFixtureMaps) + 1];
    memcpy(maps, sHealFixtureMaps, sizeof(sHealFixtureMaps));
    maps[ARRAY_COUNT(sHealFixtureMaps)] = maps[0];
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(maps, ARRAY_COUNT(maps),
        MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), 1, 2, ReadHealFixture, &reader, &selected), FALSE);
    EXPECT_EQ(reader.calls, 0);
    EXPECT_EQ(selected, 0xDEADBEEF);
}

struct BadgeReadFixture
{
    u32 calls;
    u32 failAt;
    int failure;
    u8 sinnoh;
    u8 reads[2][8];
};

static int ReadBadgeFixture(uint32_t region, uint32_t number, void *context)
{
    struct BadgeReadFixture *fixture = context;
    if (!fixture || number < 1 || number > 8
        || (region != AVERON_FIXTURE_AVERON && region != AVERON_FIXTURE_SINNOH))
        return -1;
    fixture->calls++;
    fixture->reads[region == AVERON_FIXTURE_AVERON ? 0 : 1][number - 1]++;
    if (fixture->calls == fixture->failAt)
        return fixture->failure;
    if (region == AVERON_FIXTURE_AVERON)
        return FlagGet(gBadgeFlags[number - 1]);
    return (fixture->sinnoh & (1u << (number - 1))) != 0;
}

static int ReadAllBadges(uint32_t region, uint32_t number, void *context)
{
    (void) context;
    return (region == AVERON_FIXTURE_AVERON || region == AVERON_FIXTURE_SINNOH)
        && number >= 1 && number <= 8;
}

static int ReadBadgeSnapshot(uint32_t region, uint32_t number, void *context)
{
    return AveronRegionFixture_HasBadge(context, region, number);
}

TEST("Averon region fixture captures legacy badge flags without allocating saved state")
{
    struct BadgeReadFixture reader = {.sinnoh = 0x81};
    struct AveronFixtureBadges badges = {0xFF, 0xFF};
    for (u32 i = 0; i < 8; ++i)
    {
        if (0xA5 & (1u << i))
            FlagSet(gBadgeFlags[i]);
        else
            FlagClear(gBadgeFlags[i]);
    }
    EXPECT_EQ(AveronRegionFixture_CaptureBadges(ReadBadgeFixture, &reader, &badges), TRUE);
    EXPECT_EQ(badges.averon, 0xA5);
    EXPECT_EQ(badges.sinnoh, 0x81);
    EXPECT_EQ(reader.calls, 16);
    for (u32 i = 0; i < 8; ++i)
    {
        EXPECT_EQ(reader.reads[0][i], 1);
        EXPECT_EQ(reader.reads[1][i], 1);
        EXPECT_EQ(FlagGet(gBadgeFlags[i]), (0xA5 & (1u << i)) != 0);
    }
}

TEST("Averon region fixture failed badge reads never partially replace a snapshot")
{
    u32 failAt = 1;
    int failure = -1;
    PARAMETRIZE { failAt = 1; failure = -1; }
    PARAMETRIZE { failAt = 9; failure = -1; }
    PARAMETRIZE { failAt = 16; failure = -1; }
    PARAMETRIZE { failAt = 1; failure = 2; }
    PARAMETRIZE { failAt = 9; failure = 2; }
    PARAMETRIZE { failAt = 16; failure = 2; }
    struct BadgeReadFixture reader = {.failAt = failAt, .failure = failure};
    struct AveronFixtureBadges badges = {0xA5, 0x81};
    EXPECT_EQ(AveronRegionFixture_CaptureBadges(ReadBadgeFixture, &reader, &badges), FALSE);
    EXPECT_EQ(reader.calls, failAt);
    EXPECT_EQ(badges.averon, 0xA5);
    EXPECT_EQ(badges.sinnoh, 0x81);
}

TEST("Averon region fixture capture validates required arguments before reading")
{
    struct BadgeReadFixture reader = {0};
    struct AveronFixtureBadges badges = {0xA5, 0x81};
    EXPECT_EQ(AveronRegionFixture_CaptureBadges(NULL, &reader, &badges), FALSE);
    EXPECT_EQ(AveronRegionFixture_CaptureBadges(ReadBadgeFixture, &reader, NULL), FALSE);
    EXPECT_EQ(reader.calls, 0);
    EXPECT_EQ(badges.averon, 0xA5);
    EXPECT_EQ(badges.sinnoh, 0x81);
    EXPECT_EQ(AveronRegionFixture_CaptureBadges(ReadAllBadges, NULL, &badges), TRUE);
    EXPECT_EQ(badges.averon, 0xFF);
    EXPECT_EQ(badges.sinnoh, 0xFF);
}

TEST("Averon region fixture capture allows its reader context to alias output")
{
    struct AveronFixtureBadges badges = {0xA5, 0x81};
    EXPECT_EQ(AveronRegionFixture_CaptureBadges(ReadBadgeSnapshot, &badges, &badges), TRUE);
    EXPECT_EQ(badges.averon, 0xA5);
    EXPECT_EQ(badges.sinnoh, 0x81);
}

TEST("Averon region fixture Fly policy requires visited destinations in the current region")
{
    const struct AveronFixtureMapBinding maps[] = {
        {MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), AVERON_FIXTURE_AVERON},
        {MAP_GROUP(MAP_ALDERFIELD), MAP_NUM(MAP_ALDERFIELD), AVERON_FIXTURE_AVERON},
        {255, 0, AVERON_FIXTURE_SINNOH},
        {255, 1, AVERON_FIXTURE_SINNOH},
    };
    struct AveronFixtureMapBinding before[ARRAY_COUNT(maps)];
    memcpy(before, maps, sizeof(maps));
    for (u32 current = 0; current < ARRAY_COUNT(maps); ++current)
        for (u32 destination = 0; destination < ARRAY_COUNT(maps); ++destination)
            for (int visited = 0; visited <= 1; ++visited)
                EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, ARRAY_COUNT(maps),
                    maps[current].mapGroup, maps[current].mapNum,
                    maps[destination].mapGroup, maps[destination].mapNum, visited),
                    visited && maps[current].region == maps[destination].region);
    EXPECT_EQ(memcmp(before, maps, sizeof(maps)), 0);
}

TEST("Averon region fixture Fly policy rejects invalid source destination and discovery state")
{
    const struct AveronFixtureMapBinding maps[] = {{3, 7, AVERON_FIXTURE_AVERON}};
    const int invalidVisited[] = {-1, 2, 0x7FFFFFFF};
    for (u32 i = 0; i < ARRAY_COUNT(invalidVisited); ++i)
        EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 1, 3, 7, 3, 7, invalidVisited[i]), FALSE);
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(NULL, 1, 3, 7, 3, 7, TRUE), FALSE);
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 0, 3, 7, 3, 7, TRUE), FALSE);
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 1, 3, 8, 3, 7, TRUE), FALSE);
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 1, 3, 7, 3, 8, TRUE), FALSE);
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 1, 259, 7, 3, 7, TRUE), FALSE);
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 1, 3, 7, 259, 7, TRUE), FALSE);
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 1, 3, 263, 3, 7, TRUE), FALSE);
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 1, 3, 7, 3, 263, TRUE), FALSE);
}

TEST("Averon region fixture Fly policy rejects ambiguous or invalid region bindings")
{
    struct AveronFixtureMapBinding maps[] = {
        {3, 7, AVERON_FIXTURE_AVERON}, {3, 8, AVERON_FIXTURE_AVERON}, {3, 7, AVERON_FIXTURE_AVERON},
    };
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 3, 3, 7, 3, 8, TRUE), FALSE);
    maps[2].mapNum = 8;
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 3, 3, 7, 3, 8, TRUE), FALSE);
    maps[2].mapNum = 9;
    maps[1].region = 257;
    EXPECT_EQ(AveronRegionFixture_IsFlyDestinationEligible(maps, 3, 3, 7, 3, 8, TRUE), FALSE);
}

TEST("Averon region fixture resolves explicit map group and number pairs")
{
    const struct AveronFixtureMapBinding maps[] = {
        {0, 0, AVERON_FIXTURE_AVERON},
        {0, 1, AVERON_FIXTURE_SINNOH},
        {1, 0, AVERON_FIXTURE_SINNOH},
        {255, 255, AVERON_FIXTURE_AVERON},
    };
    for (u32 i = 0; i < ARRAY_COUNT(maps); ++i)
        EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), maps[i].mapGroup, maps[i].mapNum), maps[i].region);
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), 1, 1), AVERON_FIXTURE_UNKNOWN);
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), 256, 0), AVERON_FIXTURE_UNKNOWN);
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), 0, 256), AVERON_FIXTURE_UNKNOWN);
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), 0xFFFFFFFF, 0), AVERON_FIXTURE_UNKNOWN);
}

TEST("Averon region fixture rejects unknown empty and ambiguous map bindings")
{
    struct AveronFixtureMapBinding maps[] = {{3, 7, AVERON_FIXTURE_AVERON}, {3, 7, AVERON_FIXTURE_SINNOH}};
    EXPECT_EQ(AveronRegionFixture_ResolveMap(NULL, 1, 3, 7), AVERON_FIXTURE_UNKNOWN);
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, 0, 3, 7), AVERON_FIXTURE_UNKNOWN);
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), 3, 7), AVERON_FIXTURE_UNKNOWN);
    maps[1].region = AVERON_FIXTURE_AVERON;
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), 3, 7), AVERON_FIXTURE_UNKNOWN);
    maps[1].region = AVERON_FIXTURE_UNKNOWN;
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), 3, 7), AVERON_FIXTURE_UNKNOWN);
    maps[0].region = (enum AveronFixtureRegion) 99;
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, 1, 3, 7), AVERON_FIXTURE_UNKNOWN);
    maps[0].region = 257;
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, 1, 3, 7), AVERON_FIXTURE_UNKNOWN);
    maps[0].region = 258;
    EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, 1, 3, 7), AVERON_FIXTURE_UNKNOWN);
}

TEST("Averon region fixture preserves existing Averon map identities and inputs")
{
    const struct AveronFixtureMapBinding maps[] = {
        {MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), AVERON_FIXTURE_AVERON},
        {MAP_GROUP(MAP_ALDERFIELD), MAP_NUM(MAP_ALDERFIELD), AVERON_FIXTURE_AVERON},
        {255, 254, AVERON_FIXTURE_SINNOH}, // Test input only, not a registered map.
    };
    struct AveronFixtureMapBinding before[ARRAY_COUNT(maps)];
    memcpy(before, maps, sizeof(maps));
    for (u32 i = 0; i < ARRAY_COUNT(maps); ++i)
        EXPECT_EQ(AveronRegionFixture_ResolveMap(maps, ARRAY_COUNT(maps), maps[i].mapGroup, maps[i].mapNum), maps[i].region);
    EXPECT_EQ(memcmp(before, maps, sizeof(maps)), 0);
}

TEST("Averon region fixture selects the badge bank from explicit map identity")
{
    const struct AveronFixtureMapBinding maps[] = {
        {MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), AVERON_FIXTURE_AVERON},
        {255, 254, AVERON_FIXTURE_SINNOH},
    };
    const struct AveronFixtureBadges badges = {.averon = 0x55, .sinnoh = 0x80};
    const u8 queries[] = {0, 1, 0}; // Lookup sequence only, not in-game travel.
    for (u32 i = 0; i < ARRAY_COUNT(queries); ++i)
    {
        u32 index = queries[i];
        enum AveronFixtureRegion region = AveronRegionFixture_ResolveMap(
            maps, ARRAY_COUNT(maps), maps[index].mapGroup, maps[index].mapNum);
        EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, region), index ? 1 : 4);
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, region, 1), !index);
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, region, 8), index != 0);
    }
    EXPECT_EQ(badges.averon, 0x55);
    EXPECT_EQ(badges.sinnoh, 0x80);
}

TEST("Averon region fixture keeps both eight-badge banks independent")
{
    struct AveronFixtureBadges badges = {.averon = 0, .sinnoh = 0xFF};
    EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, AVERON_FIXTURE_AVERON), 0);
    EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, AVERON_FIXTURE_SINNOH), 8);
    for (u32 badge = 1; badge <= 8; ++badge)
    {
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_AVERON, badge), FALSE);
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_SINNOH, badge), TRUE);
    }
    badges.averon = 0xFF;
    badges.sinnoh = 0;
    EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, AVERON_FIXTURE_AVERON), 8);
    EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, AVERON_FIXTURE_SINNOH), 0);
}

TEST("Averon region fixture checks every badge position in every mask")
{
    for (u32 mask = 0; mask <= 0xFF; ++mask)
    {
        struct AveronFixtureBadges badges = {.averon = mask, .sinnoh = mask ^ 0xFF};
        u32 count = 0;
        for (u32 badge = 1; badge <= 8; ++badge)
        {
            bool32 expected = (mask & (1u << (badge - 1))) != 0;
            count += expected;
            EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_AVERON, badge), expected);
            EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_SINNOH, badge), !expected);
        }
        EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, AVERON_FIXTURE_AVERON), count);
        EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, AVERON_FIXTURE_SINNOH), 8 - count);
        EXPECT_EQ(badges.averon, mask);
        EXPECT_EQ(badges.sinnoh, mask ^ 0xFF);
    }
}

TEST("Averon region fixture rejects null snapshots and invalid badge queries")
{
    struct AveronFixtureBadges badges = {.averon = 0xFF, .sinnoh = 0xFF};
    const u32 invalidNumbers[] = {0, 9, 32, 0xFFFFFFFF};
    const u32 invalidRegions[] = {AVERON_FIXTURE_UNKNOWN, 3, 257, 258, 65537, 0xFFFFFFFF};
    for (u32 i = 0; i < ARRAY_COUNT(invalidNumbers); ++i)
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_AVERON, invalidNumbers[i]), FALSE);
    for (u32 i = 0; i < ARRAY_COUNT(invalidRegions); ++i)
    {
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, invalidRegions[i], 1), FALSE);
        EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, invalidRegions[i]), 0);
    }
    EXPECT_EQ(AveronRegionFixture_HasBadge(NULL, AVERON_FIXTURE_AVERON, 1), FALSE);
    EXPECT_EQ(AveronRegionFixture_CountBadges(NULL, AVERON_FIXTURE_SINNOH), 0);
}

TEST("Averon region fixture preserves the existing Averon badge flag ordering")
{
    const u16 originalFlags[] = {FLAG_BADGE01_GET, FLAG_BADGE02_GET, FLAG_BADGE03_GET,
        FLAG_BADGE04_GET, FLAG_BADGE05_GET, FLAG_BADGE06_GET, FLAG_BADGE07_GET, FLAG_BADGE08_GET};
    struct AveronFixtureBadges badges = {.averon = 0, .sinnoh = 0xFF};
    for (u32 i = 0; i < ARRAY_COUNT(originalFlags); ++i)
    {
        EXPECT_EQ(originalFlags[i], FLAG_BADGE01_GET + i);
        if (i & 1)
            FlagSet(originalFlags[i]);
        else
            FlagClear(originalFlags[i]);
        badges.averon |= FlagGet(originalFlags[i]) << i;
    }
    for (u32 i = 0; i < ARRAY_COUNT(originalFlags); ++i)
    {
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_AVERON, i + 1), FlagGet(originalFlags[i]));
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_SINNOH, i + 1), TRUE);
        EXPECT_EQ(FlagGet(originalFlags[i]), (i & 1) != 0);
    }
    EXPECT_EQ(badges.averon, 0xAA);
    EXPECT_EQ(AveronRegionFixture_CountBadges(&badges, AVERON_FIXTURE_AVERON), 4);
}

TEST("Averon region fixture queries preserve legacy badges and licenses through flash")
{
    u32 badgeMask = 0x55, licenseMask = 0x2A;
    PARAMETRIZE { badgeMask = 0; licenseMask = 0; }
    PARAMETRIZE { badgeMask = 0x55; licenseMask = 0x2A; }
    PARAMETRIZE { badgeMask = 0xFF; licenseMask = 0x7F; }
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    struct AveronFixtureBadges badges = {.averon = 0, .sinnoh = 0x80};
    for (u32 i = 0; i < 8; ++i)
    {
        if (badgeMask & (1u << i))
            FlagSet(FLAG_BADGE01_GET + i);
        else
            FlagClear(FLAG_BADGE01_GET + i);
        badges.averon |= FlagGet(FLAG_BADGE01_GET + i) << i;
    }
    for (u32 i = 0; i < 7; ++i)
    {
        if (licenseMask & (1u << i))
            FlagSet(FLAG_AVERON_LICENSE_CUT + i);
        else
            FlagClear(FLAG_AVERON_LICENSE_CUT + i);
    }
    for (u32 number = 1; number <= 8; ++number)
    {
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_AVERON, number), (badgeMask & (1u << (number - 1))) != 0);
        EXPECT_EQ(AveronRegionFixture_HasBadge(&badges, AVERON_FIXTURE_SINNOH, number), number == 8);
    }
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    for (u32 i = 0; i < 8; ++i)
    {
        if (badgeMask & (1u << i))
            FlagClear(FLAG_BADGE01_GET + i);
        else
            FlagSet(FLAG_BADGE01_GET + i);
    }
    for (u32 i = 0; i < 7; ++i)
    {
        if (licenseMask & (1u << i))
            FlagClear(FLAG_AVERON_LICENSE_CUT + i);
        else
            FlagSet(FLAG_AVERON_LICENSE_CUT + i);
    }
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    for (u32 i = 0; i < 8; ++i)
        EXPECT_EQ(FlagGet(FLAG_BADGE01_GET + i), (badgeMask & (1u << i)) != 0);
    for (u32 i = 0; i < 7; ++i)
        EXPECT_EQ(FlagGet(FLAG_AVERON_LICENSE_CUT + i), (licenseMask & (1u << i)) != 0);
    EXPECT_EQ(badges.averon, badgeMask);
    EXPECT_EQ(badges.sinnoh, 0x80); // Local fixture only; no Sinnoh persistence claim.
}

TEST("Averon region fixture revalidates restored healer metadata without changing saved progression")
{
    u32 healId = HEAL_LOCATION_ALDERFIELD;
    PARAMETRIZE { healId = HEAL_LOCATION_ALDERFIELD; }
    PARAMETRIZE { healId = HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F; }
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    SetLastHealLocationWarp(healId);
    struct WarpData expected;
    memcpy(&expected, &gSaveBlock1Ptr->lastHealLocation, sizeof(expected));
    for (u32 i = 0; i < 8; ++i)
    {
        if (i & 1)
            FlagSet(FLAG_BADGE01_GET + i);
        else
            FlagClear(FLAG_BADGE01_GET + i);
    }
    EXPECT_EQ(GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation), healId);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    memset(&gSaveBlock1Ptr->lastHealLocation, 0x7F, sizeof(expected));
    for (u32 i = 0; i < 8; ++i)
    {
        if (i & 1)
            FlagClear(FLAG_BADGE01_GET + i);
        else
            FlagSet(FLAG_BADGE01_GET + i);
    }
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(memcmp(&expected, &gSaveBlock1Ptr->lastHealLocation, sizeof(expected)), 0);
    u32 restoredId = GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation);
    EXPECT_EQ(restoredId, healId);
    struct HealReadFixture reader = {0};
    u32 selected = 0xDEADBEEF;
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
        MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), restoredId, 0,
        ReadHealFixture, &reader, &selected), TRUE);
    EXPECT_EQ(selected, healId);
    EXPECT_EQ(reader.calls, 1);
    selected = 0xDEADBEEF;
    EXPECT_EQ(AveronRegionFixture_SelectRegionalHeal(sHealFixtureMaps, ARRAY_COUNT(sHealFixtureMaps),
        255, 1, restoredId, 0, ReadHealFixture, &reader, &selected), FALSE);
    EXPECT_EQ(selected, 0xDEADBEEF);
    EXPECT_EQ(memcmp(&expected, &gSaveBlock1Ptr->lastHealLocation, sizeof(expected)), 0);
    for (u32 i = 0; i < 8; ++i)
        EXPECT_EQ(FlagGet(FLAG_BADGE01_GET + i), (i & 1) != 0);
}
