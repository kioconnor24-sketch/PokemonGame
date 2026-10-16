#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "constants/maps.h"
#include "../src/data/map_group_count.h"

extern const struct MapHeader *const *const gMapGroups[];

// Validate every existing numeric ID, including maps omitted by this ROM's
// region filter. A disabled map constant is not a usable runtime pointer.
#define REGISTRY_GROUP(index, symbol, count, linked)
#define DECLARE_0(symbol)
#define DECLARE_1(symbol) extern const struct MapHeader symbol;
#define REGISTRY_SLOT(group, index, id, symbol, linked) \
    _Static_assert((id) == ((group) << 8 | (index)), "Saved map ID moved: " #id); \
    _Static_assert((group) <= 127 && (index) <= 127, "Map ID exceeds signed warp storage"); \
    _Static_assert((id) != MAP_DYNAMIC && (id) != MAP_UNDEFINED, "Reserved map ID used"); \
    DECLARE_##linked(symbol)
#include "data/averon_map_registry_slots.inc"
#undef REGISTRY_GROUP
#undef REGISTRY_SLOT

static const struct
{
    u8 count;
    bool8 linked;
} sExpectedGroups[] = {
#define REGISTRY_GROUP(index, symbol, count, linked) [index] = {count, linked},
#define REGISTRY_SLOT(group, index, id, symbol, linked)
#include "data/averon_map_registry_slots.inc"
#undef REGISTRY_GROUP
#undef REGISTRY_SLOT
};

static const struct
{
    u8 group, number;
    const struct MapHeader *header;
} sExpectedMaps[] = {
#define ENTRY_0(group, index, symbol)
#define ENTRY_1(group, index, symbol) {group, index, &symbol},
#define REGISTRY_GROUP(index, symbol, count, linked)
#define REGISTRY_SLOT(group, index, id, symbol, linked) ENTRY_##linked(group, index, symbol)
#include "data/averon_map_registry_slots.inc"
#undef REGISTRY_GROUP
#undef REGISTRY_SLOT
};

TEST("Averon map registry preserves group slots and disabled-region null entries")
{
    EXPECT_EQ(ARRAY_COUNT(sExpectedGroups), MAP_GROUPS_COUNT);
    EXPECT_EQ(ARRAY_COUNT(MAP_GROUP_COUNT), MAP_GROUPS_COUNT + 1);
    EXPECT_EQ(MAP_GROUP_COUNT[MAP_GROUPS_COUNT], 0);
    for (u32 group = 0; group < ARRAY_COUNT(sExpectedGroups); ++group)
    {
        EXPECT_EQ(MAP_GROUP_COUNT[group], sExpectedGroups[group].count);
        EXPECT_EQ(gMapGroups[group] != NULL, sExpectedGroups[group].linked);
    }
}

TEST("Averon map registry resolves every linked numeric ID to its original header symbol")
{
    EXPECT(ARRAY_COUNT(sExpectedMaps) > 0);
    for (u32 i = 0; i < ARRAY_COUNT(sExpectedMaps); ++i)
    {
        u32 group = sExpectedMaps[i].group;
        u32 number = sExpectedMaps[i].number;
        EXPECT(gMapGroups[group] != NULL);
        if (gMapGroups[group] == NULL)
            continue;
        EXPECT(number < MAP_GROUP_COUNT[group]);
        if (number >= MAP_GROUP_COUNT[group])
            continue;
        EXPECT_EQ(Overworld_GetMapHeaderByGroupAndId(group, number), sExpectedMaps[i].header);
    }
}

TEST("Averon map registry IDs round trip through the actual signed warp fields")
{
    struct WarpData warp = {.mapGroup = -1, .mapNum = -1, .warpId = -1};
    EXPECT(warp.mapGroup < 0);
    EXPECT(warp.mapNum < 0);
    EXPECT(warp.warpId < 0);
    for (u32 i = 0; i < ARRAY_COUNT(sExpectedMaps); ++i)
    {
        warp.mapGroup = sExpectedMaps[i].group;
        warp.mapNum = sExpectedMaps[i].number;
        EXPECT_EQ(warp.mapGroup, sExpectedMaps[i].group);
        EXPECT_EQ(warp.mapNum, sExpectedMaps[i].number);
    }
}
