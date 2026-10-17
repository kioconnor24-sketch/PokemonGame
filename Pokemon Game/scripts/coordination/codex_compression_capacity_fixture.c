// EXPERIMENT ONLY: stage the nine existing host roundtrip files as documented
// in SINNOH_TECHNICAL_READINESS_20261017.md; copy this fixture into a disposable
// engine/test/averon_codex_compression_capacity.c. No assets are committed.
#include "global.h"
#include "test/test.h"
#include "decompress.h"
#include "malloc.h"

static const u32 sPetalburgRaw[] = INCBIN_U32("/tmp/averon-sinnoh-compression/petalburg.4bpp");
static const u32 sPetalburgFast[] = INCBIN_U32("/tmp/averon-sinnoh-compression/petalburg.4bpp.fastSmol");
static const u32 sPetalburgFull[] = INCBIN_U32("/tmp/averon-sinnoh-compression/petalburg.4bpp.smol");
static const u32 sRustboroRaw[] = INCBIN_U32("/tmp/averon-sinnoh-compression/rustboro.4bpp");
static const u32 sRustboroFast[] = INCBIN_U32("/tmp/averon-sinnoh-compression/rustboro.4bpp.fastSmol");
static const u32 sRustboroFull[] = INCBIN_U32("/tmp/averon-sinnoh-compression/rustboro.4bpp.smol");
static const u32 sSlateportRaw[] = INCBIN_U32("/tmp/averon-sinnoh-compression/slateport.4bpp");
static const u32 sSlateportFast[] = INCBIN_U32("/tmp/averon-sinnoh-compression/slateport.4bpp.fastSmol");
static const u32 sSlateportFull[] = INCBIN_U32("/tmp/averon-sinnoh-compression/slateport.4bpp.smol");

static u32 FreePayload(void)
{
    const struct MemBlock *head = HeapHead(), *block = head;
    u32 free = 0;
    do
    {
        if (!block->allocated)
            free += block->size;
        block = block->next;
    } while (block != head);
    return free;
}

TEST("Codex compression capacity fast and full cold decode preserve bytes and heap")
{
    const u32 *raw, *fast, *full;
    u32 size, id;
    PARAMETRIZE { id = 0; raw = sPetalburgRaw; fast = sPetalburgFast; full = sPetalburgFull; size = sizeof(sPetalburgRaw); }
    PARAMETRIZE { id = 1; raw = sRustboroRaw; fast = sRustboroFast; full = sRustboroFull; size = sizeof(sRustboroRaw); }
    PARAMETRIZE { id = 2; raw = sSlateportRaw; fast = sSlateportFast; full = sSlateportFull; size = sizeof(sSlateportRaw); }
    u32 initialFree = FreePayload();
    void *buffer = Alloc(size);
    struct Benchmark fastTicks, fullTicks;
    EXPECT_EQ(GetDecompressedDataSize(fast), size);
    EXPECT_EQ(GetDecompressedDataSize(full), size);
    BENCHMARK(&fastTicks) { DecompressDataWithHeaderWram(fast, buffer); }
    EXPECT_EQ(memcmp(buffer, raw, size), 0);
    BENCHMARK(&fullTicks) { DecompressDataWithHeaderWram(full, buffer); }
    EXPECT_EQ(memcmp(buffer, raw, size), 0);
    const struct SmolHeader *h = (const void *)full;
    // Exact temporary payload requested by current SmolDecompressData.
    u32 scratch = 2*((h->symSize+1)&~1) + ((h->loSize+1)&~1);
    Free(buffer);
    EXPECT_EQ(FreePayload(), initialFree);
    Test_MgbaPrintf("CAPACITY DECODE id=%d raw=%d fast_ticks64=%d full_ticks64=%d scratch_payload=%d free_restored=%d",
        id, size, fastTicks.ticks, fullTicks.ticks, scratch, initialFree);
}
