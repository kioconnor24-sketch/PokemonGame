#include "global.h"
#include "test/test.h"
#include "event_data.h"
#include "load_save.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "averon_region_fixture.h"
#include "constants/maps.h"

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
