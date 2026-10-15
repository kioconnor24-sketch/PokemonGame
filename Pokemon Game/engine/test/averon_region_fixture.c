#include "global.h"
#include "test/test.h"
#include "event_data.h"
#include "averon_region_fixture.h"

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
    const enum AveronFixtureRegion invalidRegions[] = {AVERON_FIXTURE_UNKNOWN, -1, 3, 0x7FFFFFFF};
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
