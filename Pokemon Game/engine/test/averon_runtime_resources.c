#include "global.h"
#include "test/test.h"
#include "test/field_menu.h"
#include "averon_region_save.h"
#include "decompress.h"
#include "fieldmap.h"
#include "malloc.h"
#include "overworld.h"
#include "pokemon.h"
#include "sprite.h"
#include "constants/maps.h"
#include "../src/data/map_group_count.h"

// Native pressure and menu fixtures, not a running whole field/battle scene.
// In particular, linker-free EWRAM is NOT the heap's largest free allocation.
struct HeapSnapshot
{
    u32 freeBytes, largestFree, allocatedBytes, blocks;
};

static struct HeapSnapshot InspectHeap(void)
{
    struct HeapSnapshot result = {0};
    const struct MemBlock *head = HeapHead();
    const struct MemBlock *block = head;
    do
    {
        EXPECT_EQ(block->magic, MALLOC_SYSTEM_ID);
        EXPECT(++result.blocks <= HEAP_SIZE / sizeof(struct MemBlock));
        if (block->allocated)
            result.allocatedBytes += block->size;
        else
        {
            result.freeBytes += block->size;
            result.largestFree = max(result.largestFree, block->size);
        }
        block = block->next;
    } while (block != head);
    return result;
}

static void ExpectHeapRestored(struct HeapSnapshot before)
{
    struct HeapSnapshot after = InspectHeap();
    EXPECT_EQ(after.freeBytes, before.freeBytes);
    EXPECT_EQ(after.largestFree, before.largestFree);
    EXPECT_EQ(after.allocatedBytes, before.allocatedBytes);
    EXPECT_EQ(after.blocks, before.blocks);
}

TEST("Averon resource heap fragmented capacity refuses oversized requests and coalesces after free")
{
    struct HeapSnapshot before = InspectHeap();
    EXPECT_EQ(before.freeBytes + before.allocatedBytes + before.blocks * sizeof(struct MemBlock), HEAP_SIZE);
    u8 *first = Alloc(8192);
    u8 *middle = Alloc(8192);
    u8 *third = Alloc(8192);
    // Consume the actual remaining tail, not an assumed linker headroom.
    u32 tailSize = InspectHeap().largestFree;
    EXPECT(tailSize > 0);
    u8 *tail = Alloc(tailSize);
    memset(middle, 0x5A, 8192);
    memset(tail, 0xA5, tailSize);
    Free(first);
    Free(third);
    struct HeapSnapshot fragmented = InspectHeap();
    EXPECT_EQ(fragmented.freeBytes, 16384);
    EXPECT_EQ(fragmented.largestFree, 8192);
    EXPECT_EQ(AllocUnchecked(12288), NULL);
    for (u32 i = 0; i < 8192; ++i)
        EXPECT_EQ(middle[i], 0x5A);
    for (u32 i = 0; i < tailSize; ++i)
        EXPECT_EQ(tail[i], 0xA5);
    Free(middle);
    u8 *recovered = AllocUnchecked(12288);
    EXPECT(recovered != NULL);
    memset(recovered, 0xCC, 12288);
    for (u32 i = 0; i < tailSize; ++i)
        EXPECT_EQ(tail[i], 0xA5);
    Free(recovered);
    Free(tail);
    ExpectHeapRestored(before);
    Test_MgbaPrintf("RESOURCE heap configured=%d free=%d largest=%d runner_payload=%d headers=%d fragmented_free=%d fragmented_largest=%d",
                    HEAP_SIZE, before.freeBytes, before.largestFree,
                    before.allocatedBytes, before.blocks * sizeof(struct MemBlock),
                    fragmented.freeBytes, fragmented.largestFree);
}

static void ExpectCanary(const u8 *data, u32 count)
{
    for (u32 i = 0; i < count; ++i)
        EXPECT_EQ(data[i], 0xA7);
}

TEST("Averon resource linked field tilesets decompress within paired buffers and release heap")
{
    static const u32 groups[] = {MAP_GROUP(MAP_SALTMERE), MAP_GROUP(MAP_SANDGEM_TOWN)};
    u32 group = groups[0], map = 0;
    for (u32 g = 0; g < ARRAY_COUNT(groups); ++g)
        for (u32 i = 0; i < MAP_GROUP_COUNT[groups[g]]; ++i)
            PARAMETRIZE { group = groups[g]; map = i; }
    const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(group, map);
    EXPECT(header != NULL);
    const struct MapLayout *layout = header->mapLayout;
    const struct Tileset *pair[] = {layout->primaryTileset, layout->secondaryTileset};
    u32 capacities[] = {GetNumTilesInPrimary(layout), NUM_TILES_TOTAL - GetNumTilesInPrimary(layout)};
    struct HeapSnapshot before = InspectHeap();
    u32 largestPairBytes = 0;
    for (u32 pass = 0; pass < 4; ++pass)
    {
        u8 *buffers[2] = {NULL, NULL};
        u32 sizes[2] = {0};
        for (u32 side = 0; side < ARRAY_COUNT(pair); ++side)
        {
            EXPECT(pair[side] != NULL);
            if (!pair[side]->isCompressed)
            {
                if (pass == 0)
                    Test_MgbaPrintf("RESOURCE raw tileset not decoded group=%d map=%d side=%d", group, map, side);
                continue;
            }
            sizes[side] = GetDecompressedDataSize(pair[side]->tiles);
            EXPECT(sizes[side] > 0);
            EXPECT_EQ(sizes[side] % TILE_SIZE_4BPP, 0);
            EXPECT(sizes[side] <= capacities[side] * TILE_SIZE_4BPP);
            buffers[side] = Alloc(sizes[side] + 32);
            memset(buffers[side], 0xA7, sizes[side] + 32);
        }
        // Both real outputs are live at once. This is an observed allocation
        // stage, not a claim to capture transient codec or whole-game peaks.
        struct HeapSnapshot held = InspectHeap();
        largestPairBytes = max(largestPairBytes, held.allocatedBytes - before.allocatedBytes);
        for (u32 side = 0; side < ARRAY_COUNT(pair); ++side)
        {
            if (buffers[side] == NULL)
                continue;
            DecompressDataWithHeaderWram(pair[side]->tiles, buffers[side] + 16);
            ExpectCanary(buffers[side], 16);
            ExpectCanary(buffers[side] + 16 + sizes[side], 16);
            EXPECT_EQ(InspectHeap().allocatedBytes, held.allocatedBytes);
        }
        // Alternate order to exercise coalescing in both directions.
        Free(buffers[pass & 1]);
        Free(buffers[!(pass & 1)]);
        ExpectHeapRestored(before);
    }
    Test_MgbaPrintf("RESOURCE tilesets group=%d map=%d guarded_buffers=%d heap_free_before=%d largest_before=%d passes=4",
                    group, map, largestPairBytes, before.freeBytes, before.largestFree);
}

TEST("Averon resource sprite slot exhaustion preserves live sprites and permits exact slot reuse")
{
    ResetSpriteData();
    struct HeapSnapshot before = InspectHeap();
    for (u32 i = 0; i < MAX_SPRITES; ++i)
    {
        EXPECT_EQ(CreateSpriteUnchecked(&gDummySpriteTemplate, i, i + 1, 0), i);
        gSprites[i].data[0] = i + 100;
    }
    EXPECT_EQ(CreateSpriteUnchecked(&gDummySpriteTemplate, 99, 99, 0), MAX_SPRITES);
    for (u32 i = 0; i < MAX_SPRITES; ++i)
    {
        EXPECT(gSprites[i].inUse);
        EXPECT_EQ(gSprites[i].x, i);
        EXPECT_EQ(gSprites[i].y, i + 1);
        EXPECT_EQ(gSprites[i].data[0], i + 100);
    }
    u32 freed = MAX_SPRITES / 2;
    DestroySprite(&gSprites[freed]);
    EXPECT_EQ(CreateSpriteUnchecked(&gDummySpriteTemplate, 55, 66, 0), freed);
    EXPECT_EQ(CreateSpriteUnchecked(&gDummySpriteTemplate, 99, 99, 0), MAX_SPRITES);
    for (u32 i = 0; i < MAX_SPRITES; ++i)
        DestroySprite(&gSprites[i]);
    ExpectHeapRestored(before);
    Test_MgbaPrintf("RESOURCE sprite_pool=%d exhaustion_sentinel=%d reused=%d", MAX_SPRITES, MAX_SPRITES, freed);
}

TEST("Averon resource reserved sprite palette banks survive exhaustion and free tag reuse")
{
    u32 reserved = 0;
    PARAMETRIZE { reserved = 0; }
    PARAMETRIZE { reserved = 1; }
    PARAMETRIZE { reserved = 8; }
    PARAMETRIZE { reserved = 16; }
    FreeAllSpritePalettes();
    gReservedSpritePaletteCount = reserved;
    EXPECT_EQ(CountFreePaletteSlots(), 16 - reserved);
    for (u32 i = reserved; i < 16; ++i)
    {
        EXPECT_EQ(AllocSpritePalette(0x5000 + i), i);
        EXPECT_EQ(CountFreePaletteSlots(), 15 - i);
    }
    EXPECT_EQ(AllocSpritePalette(0x6000), 0xFF);
    for (u32 i = 0; i < reserved; ++i)
        EXPECT_EQ(GetSpritePaletteTagByPaletteNum(i), TAG_NONE);
    for (u32 i = reserved; i < 16; ++i)
        EXPECT_EQ(IndexOfSpritePaletteTag(0x5000 + i), i);
    if (reserved < 16)
    {
        FreeSpritePaletteByTag(0x5000 + reserved);
        EXPECT_EQ(CountFreePaletteSlots(), 1);
        EXPECT_EQ(AllocSpritePalette(0x6000), reserved);
        EXPECT_EQ(CountFreePaletteSlots(), 0);
    }
    FreeAllSpritePalettes();
    EXPECT_EQ(gReservedSpritePaletteCount, 0);
    EXPECT_EQ(CountFreePaletteSlots(), 16);
    Test_MgbaPrintf("RESOURCE palette_banks=16 reserved=%d allocatable=%d refusal=255", reserved, 16 - reserved);
}

struct ResourceSamples
{
    u32 frames, maxAllocated, minLargestFree, maxSprites, maxUnavailablePalettes;
};

static void SampleMenu(struct ResourceSamples *samples)
{
    struct HeapSnapshot heap = InspectHeap();
    samples->maxAllocated = max(samples->maxAllocated, heap.allocatedBytes);
    samples->minLargestFree = min(samples->minLargestFree, heap.largestFree);
    u32 live = 0;
    for (u32 i = 0; i < MAX_SPRITES; ++i)
        live += gSprites[i].inUse;
    samples->maxSprites = max(samples->maxSprites, live);
    // Reserved banks are unavailable too; this is not just loaded colors.
    samples->maxUnavailablePalettes = max(samples->maxUnavailablePalettes, 16 - CountFreePaletteSlots());
}

static void StepMenu(struct ResourceSamples *samples, u16 keys)
{
    Test_FieldMenuStep(keys);
    ++samples->frames;
    SampleMenu(samples);
}

static void WaitForMenuActions(struct ResourceSamples *samples)
{
    for (u32 i = 0; i < 240 && !Test_FieldMenuActionsReady(); ++i)
        StepMenu(samples, 0);
    EXPECT(Test_FieldMenuActionsReady());
}

TEST("Averon resource real party and Field Kit menus restore heap across repeated regional visits")
{
    u32 region = AVERON_SAVE_REGION_AVERON, count = 1;
    PARAMETRIZE { region = AVERON_SAVE_REGION_AVERON; count = 1; }
    PARAMETRIZE { region = AVERON_SAVE_REGION_AVERON; count = PARTY_SIZE; }
    PARAMETRIZE { region = AVERON_SAVE_REGION_SINNOH; count = 1; }
    PARAMETRIZE { region = AVERON_SAVE_REGION_SINNOH; count = PARTY_SIZE; }
    static const enum Species species[] = {
        SPECIES_WOBBUFFET, SPECIES_PIPLUP, SPECIES_GARCHOMP,
        SPECIES_LUCARIO, SPECIES_PIKACHU, SPECIES_MIRAIDON,
    };
    ZeroPlayerPartyMons();
    for (u32 i = 0; i < count; ++i)
        CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][i], species[i], 5, 0);
    CalculatePlayerPartyCount();
    AveronRegionSave_InitNewGame();
    EXPECT(AveronRegion_SetActive(region));
    u32 map = region == AVERON_SAVE_REGION_AVERON ? MAP_SALTMERE : MAP_SANDGEM_TOWN;
    SetWarpDestination(MAP_GROUP(map), MAP_NUM(map), WARP_ID_NONE, 4, 4);
    WarpIntoMap();
    // Native TEST starts without a field scene. Initialize the tag sentinel
    // before sampling; zero-initialized tags otherwise look like 16 used banks.
    ResetSpriteData();
    FreeAllSpritePalettes();
    struct HeapSnapshot before = InspectHeap();
    struct ResourceSamples samples = {.minLargestFree = before.largestFree};
    for (u32 visit = 0; visit < 3; ++visit)
    {
        Test_FieldMenuBegin(0);
        SampleMenu(&samples);
        WaitForMenuActions(&samples);
        s32 toolkit = Test_FieldMenuToolkitIndex();
        EXPECT(toolkit >= 0);
        for (u32 i = 0; i < toolkit; ++i)
        {
            StepMenu(&samples, DPAD_DOWN);
            StepMenu(&samples, 0);
        }
        StepMenu(&samples, A_BUTTON);
        StepMenu(&samples, 0);
        WaitForMenuActions(&samples);
        StepMenu(&samples, B_BUTTON); // Field Kit -> ordinary actions
        StepMenu(&samples, 0);
        WaitForMenuActions(&samples);
        StepMenu(&samples, B_BUTTON); // actions -> party selection
        StepMenu(&samples, 0);
        EXPECT(Test_FieldMenuChoosingMon());
        StepMenu(&samples, B_BUTTON); // cancel the menu, without opening a map scene
        for (u32 i = 0; i < 120 && !Test_FieldMenuExited(); ++i)
            StepMenu(&samples, 0);
        EXPECT(Test_FieldMenuExited());
        // Check the normal close, before the harness resets global state.
        ExpectHeapRestored(before);
        Test_FieldMenuEnd();
        ExpectHeapRestored(before);
    }
    EXPECT(samples.frames > 0);
    EXPECT(samples.maxAllocated > before.allocatedBytes);
    EXPECT(samples.maxSprites > 0);
    Test_MgbaPrintf("RESOURCE menu region=%d party=%d visits=3 samples=%d allocated_max=%d largest_free_min=%d live_sprites_max=%d unavailable_palettes_max=%d",
                    region, count, samples.frames, samples.maxAllocated,
                    samples.minLargestFree, samples.maxSprites, samples.maxUnavailablePalettes);
}
