#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "fieldmap.h"
#include "hall_of_fame.h"
#include "load_save.h"
#include "main.h"
#include "malloc.h"
#include "palette.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "save.h"
#include "gba/flash_internal.h"

// Real flash tests for what happens after the build refuses a save written
// by a newer region format: no save path, retry or recovery screen may erase
// or program any of the 32 sectors. Also checks that the early save-block
// pointer selector picks the same slot as the region-aware load fallback.

extern u16 gSaveAttemptStatus;

#define ANCHOR_OFFSET offsetof(struct SaveBlock2, averonRegionAnchor)
#define RECORD_OFFSET (offsetof(struct SaveSector, saveBlock3Chunk) + offsetof(struct SaveBlock3, averonRegionRecord))

static u16 (*sRealProgram)(u16, u8 *);
static u16 (*sRealErase)(u16);
static u16 (*sRealProgramByte)(u16, u32, u8);
static u32 sProgramCalls, sEraseCalls, sProgramByteCalls;

static u16 CountingProgram(u16 sector, u8 *data)
{
    sProgramCalls++;
    return sRealProgram(sector, data);
}

static u16 CountingErase(u16 sector)
{
    sEraseCalls++;
    return sRealErase(sector);
}

static u16 CountingProgramByte(u16 sector, u32 offset, u8 data)
{
    sProgramByteCalls++;
    return sRealProgramByte(sector, offset, data);
}

static void StartCountingWrites(void)
{
    sRealProgram = ProgramFlashSector;
    sRealErase = EraseFlashSector;
    sRealProgramByte = ProgramFlashByte;
    sProgramCalls = sEraseCalls = sProgramByteCalls = 0;
    ProgramFlashSector = CountingProgram;
    EraseFlashSector = CountingErase;
    ProgramFlashByte = CountingProgramByte;
}

static void StopCountingWrites(void)
{
    ProgramFlashSector = sRealProgram;
    EraseFlashSector = sRealErase;
    ProgramFlashByte = sRealProgramByte;
}

static u32 MemoryCrc(const void *data, u32 size)
{
    return AveronRegionSave_Crc32(data, size);
}

static u16 Checksum(const u8 *data, u16 size)
{
    u32 sum = 0;
    for (u32 i = 0; i < size / 4; i++)
        sum += ((const u32 *)data)[i];
    return (sum >> 16) + sum;
}

static s32 FindPhysical(u32 slot, u32 id)
{
    for (u32 i = 0; i < NUM_SECTORS_PER_SLOT; i++)
    {
        u16 sectorId;
        ReadFlash(slot * NUM_SECTORS_PER_SLOT + i, offsetof(struct SaveSector, id), (u8 *)&sectorId, sizeof(sectorId));
        if (sectorId == id)
            return slot * NUM_SECTORS_PER_SLOT + i;
    }
    return -1;
}

static void ReadSector(u32 physical, struct SaveSector *sector)
{
    ReadFlash(physical, 0, (u8 *)sector, sizeof(*sector));
}

static void WriteSector(u32 physical, struct SaveSector *sector)
{
    EraseFlashSector(physical);
    ProgramFlashSector(physical, (u8 *)sector);
}

static void SetTrainerId(u32 seed)
{
    for (u32 i = 0; i < TRAINER_ID_LENGTH; i++)
        gSaveBlock2Ptr->playerTrainerId[i] = 0x11 * (i + 1) + seed;
}

static u32 TrainerIdSum(u32 seed)
{
    u32 sum = 0;
    for (u32 i = 0; i < TRAINER_ID_LENGTH; i++)
        sum += (u8)(0x11 * (i + 1) + seed);
    return sum;
}

static bool32 StartFlash(void)
{
    CheckForFlashMemory();
    if (!gFlashMemoryPresent)
        return FALSE;
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    CalculatePlayerPartyCount();
    return TRUE;
}

// Two whole saves with different trainer IDs, so the slot each selector
// picks can be told apart.
static void SaveTwo(void)
{
    SetTrainerId(1);
    TrySavingData(SAVE_NORMAL);
    SetTrainerId(2);
    TrySavingData(SAVE_NORMAL);
}

// The Hall of Fame, Trainer Hill and Recorded Battle sectors as a newer
// build might have left them.
static void FillSpecialSectors(struct SaveSector *sector)
{
    for (u32 physical = SECTOR_ID_HOF_1; physical < SECTORS_COUNT; physical++)
    {
        for (u32 i = 0; i < sizeof(*sector); i++)
            ((u8 *)sector)[i] = physical * 31 + i * 7 + 3;
        WriteSector(physical, sector);
    }
}

// Rewrites the newest slot's anchor as one from a newer region format.
static void MakeNewestNewerFormat(struct SaveSector *sector)
{
    s32 physical = FindPhysical(gSaveCounter % NUM_SAVE_SLOTS, SECTOR_ID_SAVEBLOCK2);
    ReadSector(physical, sector);
    sector->data[ANCHOR_OFFSET + 4] = AVERON_REGION_SAVE_FORMAT + 1;
    sector->data[ANCHOR_OFFSET + 5] = 0;
    sector->data[ANCHOR_OFFSET + 6] = ~(AVERON_REGION_SAVE_FORMAT + 1);
    sector->data[ANCHOR_OFFSET + 7] = 0xFF;
    sector->checksum = Checksum(sector->data, sizeof(struct SaveBlock2));
    WriteSector(physical, sector);
}

static void SnapshotFlash(struct SaveSector *sector, u32 *crcs)
{
    for (u32 i = 0; i < SECTORS_COUNT; i++)
    {
        ReadSector(i, sector);
        crcs[i] = AveronRegionSave_Crc32((const u8 *)sector, sizeof(*sector));
    }
}

// Sets up a refused newer-format save; returns FALSE without flash.
static bool32 StartRefusedSave(struct SaveSector *sector, u32 *crcs)
{
    if (!StartFlash())
        return FALSE;
    SaveTwo();
    FillSpecialSectors(sector);
    MakeNewestNewerFormat(sector);
    SnapshotFlash(sector, crcs);
    Save_ResetSaveCounters();
    return LoadGameSave(SAVE_NORMAL) == SAVE_STATUS_CORRUPT && AveronRegionSave_IsWriteBlocked();
}

static u32 CountChangedSectors(struct SaveSector *sector, const u32 *before)
{
    u32 changed = 0;
    u32 after[SECTORS_COUNT];
    SnapshotFlash(sector, after);
    for (u32 i = 0; i < SECTORS_COUNT; i++)
    {
        if (after[i] != before[i])
            changed++;
    }
    return changed;
}

enum
{
    REJECT_NEWER_FORMAT,
    REJECT_BOTH_REGION_RECORDS,
    REJECT_BOTH_PARTIAL_SLOTS,
    REJECT_EMPTY_FLASH,
};

TEST("Averon region save refusal: rejected slots publish no save blocks, party or objects")
{
    u32 kind = REJECT_NEWER_FORMAT;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 sb1Crc, sb2Crc, sb3PrefixCrc, storageCrc, partyCrc, objectsCrc;
    u32 issue, blocked, partyCount;
    u16 offset;
    u8 status;
    PARAMETRIZE { kind = REJECT_NEWER_FORMAT; }
    PARAMETRIZE { kind = REJECT_BOTH_REGION_RECORDS; }
    PARAMETRIZE { kind = REJECT_BOTH_PARTIAL_SLOTS; }
    PARAMETRIZE { kind = REJECT_EMPTY_FLASH; }
    EXPECT(StartFlash());
    SaveTwo();
    if (kind == REJECT_NEWER_FORMAT)
        MakeNewestNewerFormat(sector);
    else if (kind == REJECT_EMPTY_FLASH)
        ClearSaveData();
    else
    {
        for (u32 slot = 0; slot < NUM_SAVE_SLOTS; slot++)
        {
            if (kind == REJECT_BOTH_PARTIAL_SLOTS)
                EraseFlashSector(FindPhysical(slot, SECTOR_ID_SAVEBLOCK1_START));
            else
            {
                u32 physical = FindPhysical(slot, SECTOR_ID_SAVEBLOCK2);
                ReadSector(physical, sector);
                ((u8 *)sector)[RECORD_OFFSET + 18] ^= 1; // outside the primary checksum
                WriteSector(physical, sector);
            }
        }
    }

    // Keep valid saved party bytes in SaveBlock1, but give runtime a different
    // party. This detects publication even on empty flash, independently of
    // the sector-copy guard. Save-block sentinels differ from either slot.
    SetTrainerId(9);
    gSaveBlock1Ptr->money ^= 0x43434343;
    gSaveBlock1Ptr->flags[0] ^= 0x20;
    gSaveBlock3Ptr->dexNavChain = 0xA7;
    gPokemonStoragePtr->currentBox = 7;
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_TURTWIG, 17, 0, OTID_STRUCT_PLAYER_ID);
    CreateMon(&gParties[B_TRAINER_PLAYER][1], SPECIES_CHIMCHAR, 18, 0, OTID_STRUCT_PLAYER_ID);
    CalculatePlayerPartyCount();
    gObjectEvents[0].currentCoords.x = 99;
    gObjectEvents[0].currentCoords.y = 88;
    gObjectEvents[0].spriteId = 47;
    sb1Crc = MemoryCrc(gSaveBlock1Ptr, sizeof(*gSaveBlock1Ptr));
    sb2Crc = MemoryCrc(gSaveBlock2Ptr, sizeof(*gSaveBlock2Ptr));
    sb3PrefixCrc = MemoryCrc(gSaveBlock3Ptr, offsetof(struct SaveBlock3, averonRegionRecord));
    storageCrc = MemoryCrc(gPokemonStoragePtr, sizeof(*gPokemonStoragePtr));
    partyCrc = MemoryCrc(gParties[B_TRAINER_PLAYER], sizeof(gParties[B_TRAINER_PLAYER]));
    partyCount = gPartiesCount[B_TRAINER_PLAYER];
    objectsCrc = MemoryCrc(gObjectEvents, sizeof(gObjectEvents));

    Save_ResetSaveCounters();
    StartCountingWrites();
    offset = GetSaveBlocksPointersBaseOffset();
    status = LoadGameSave(SAVE_NORMAL);
    StopCountingWrites(); // restore every hook before an assertion can abort
    issue = AveronRegionSave_GetLoadIssue();
    blocked = AveronRegionSave_IsWriteBlocked();
    AveronRegionSave_BeginLoad();
    Save_ResetSaveCounters();
    EXPECT_EQ(status, kind == REJECT_EMPTY_FLASH ? SAVE_STATUS_EMPTY : SAVE_STATUS_CORRUPT);
    EXPECT_EQ(offset, 0); // no trainer ID from an unaccepted slot
    EXPECT_EQ(sProgramCalls, 0);
    EXPECT_EQ(sEraseCalls, 0);
    EXPECT_EQ(sProgramByteCalls, 0);
    EXPECT_EQ(MemoryCrc(gSaveBlock1Ptr, sizeof(*gSaveBlock1Ptr)), sb1Crc);
    EXPECT_EQ(MemoryCrc(gSaveBlock2Ptr, sizeof(*gSaveBlock2Ptr)), sb2Crc);
    EXPECT_EQ(MemoryCrc(gSaveBlock3Ptr, offsetof(struct SaveBlock3, averonRegionRecord)), sb3PrefixCrc);
    EXPECT_EQ(MemoryCrc(gPokemonStoragePtr, sizeof(*gPokemonStoragePtr)), storageCrc);
    EXPECT_EQ(MemoryCrc(gParties[B_TRAINER_PLAYER], sizeof(gParties[B_TRAINER_PLAYER])), partyCrc);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], partyCount);
    EXPECT_EQ(MemoryCrc(gObjectEvents, sizeof(gObjectEvents)), objectsCrc);
    // The region-only defaults are initialized in RAM after rejection.
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_AVERON);
    EXPECT_EQ(AveronRegion_CountBadges(AVERON_SAVE_REGION_SINNOH), 0);
    EXPECT_EQ(blocked, kind == REJECT_NEWER_FORMAT);
    if (kind == REJECT_NEWER_FORMAT)
        EXPECT_EQ(issue, AVERON_REGION_LOAD_UNSUPPORTED);
    Free(sector);
}

enum
{
    INCREMENTAL_FULL_INIT,
    INCREMENTAL_FULL_WRITE,
    INCREMENTAL_FULL_REPLACE,
    INCREMENTAL_FULL_SIGNATURE,
    INCREMENTAL_BLOCK2,
    INCREMENTAL_BLOCK1,
};

TEST("Averon region save refusal: incremental entrypoints make zero flash calls and finish with an error")
{
    u32 entry = INCREMENTAL_FULL_INIT;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 before[SECTORS_COUNT];
    u32 counter, rotation, incremental, attempt;
    MainCallback callback;
    bool32 refused, finished = FALSE, screenOpened;
    PARAMETRIZE { entry = INCREMENTAL_FULL_INIT; }
    PARAMETRIZE { entry = INCREMENTAL_FULL_WRITE; }
    PARAMETRIZE { entry = INCREMENTAL_FULL_REPLACE; }
    PARAMETRIZE { entry = INCREMENTAL_FULL_SIGNATURE; }
    PARAMETRIZE { entry = INCREMENTAL_BLOCK2; }
    PARAMETRIZE { entry = INCREMENTAL_BLOCK1; }
    refused = StartRefusedSave(sector, before);
    callback = gMain.callback2;
    counter = gSaveCounter;
    rotation = gLastWrittenSector;
    gIncrementalSectorId = 0;
    incremental = gIncrementalSectorId;
    gDamagedSaveSectors = 0;
    gSaveAttemptStatus = SAVE_STATUS_OK;
    StartCountingWrites();
    switch (entry)
    {
    case INCREMENTAL_FULL_INIT:      finished = LinkFullSave_Init(); break;
    case INCREMENTAL_FULL_WRITE:     finished = LinkFullSave_WriteSector(); break;
    case INCREMENTAL_FULL_REPLACE:   finished = LinkFullSave_ReplaceLastSector(); break;
    case INCREMENTAL_FULL_SIGNATURE: finished = LinkFullSave_SetLastSectorSignature(); break;
    case INCREMENTAL_BLOCK2:         finished = WriteSaveBlock2(); break;
    case INCREMENTAL_BLOCK1:         finished = WriteSaveBlock1Sector(); break;
    }
    StopCountingWrites();
    screenOpened = gMain.callback2 != callback;
    attempt = gSaveAttemptStatus;
    SetMainCallback2(callback);
    AveronRegionSave_BeginLoad();
    EXPECT(refused);
    EXPECT(finished);
    EXPECT_EQ(attempt, SAVE_STATUS_ERROR);
    EXPECT_EQ(screenOpened, FALSE);
    EXPECT_EQ(gSaveCounter, counter);
    EXPECT_EQ(gLastWrittenSector, rotation);
    EXPECT_EQ(gIncrementalSectorId, incremental);
    EXPECT_EQ(sProgramCalls, 0);
    EXPECT_EQ(sEraseCalls, 0);
    EXPECT_EQ(sProgramByteCalls, 0); // CRCs cannot detect same-byte programming
    EXPECT_EQ(CountChangedSectors(sector, before), 0);
    Save_ResetSaveCounters();
    Free(sector);
}

TEST("Averon region save refusal: TrySavingData touches no sector and skips the save failed screen")
{
    u32 saveType = SAVE_NORMAL;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 before[SECTORS_COUNT];
    MainCallback callback;
    bool32 refused, screenOpened;
    u16 attempt;
    u8 status;
    PARAMETRIZE { saveType = SAVE_NORMAL; }
    PARAMETRIZE { saveType = SAVE_OVERWRITE_DIFFERENT_FILE; } // New Game's first save
    PARAMETRIZE { saveType = SAVE_HALL_OF_FAME; }
    PARAMETRIZE { saveType = SAVE_LINK; }
    refused = StartRefusedSave(sector, before);
    gHoFSaveBuffer = Alloc(SECTOR_DATA_SIZE * NUM_HOF_SECTORS);
    memset(gHoFSaveBuffer, 0x5C, SECTOR_DATA_SIZE * NUM_HOF_SECTORS);
    callback = gMain.callback2;
    status = TrySavingData(saveType);
    attempt = gSaveAttemptStatus;
    screenOpened = gMain.callback2 != callback;
    SetMainCallback2(callback); // back to the runner before any check can end the test
    AveronRegionSave_BeginLoad();
    Save_ResetSaveCounters();
    TRY_FREE_AND_SET_NULL(gHoFSaveBuffer);
    EXPECT(refused);
    EXPECT_EQ(status, SAVE_STATUS_ERROR);
    EXPECT_EQ(attempt, SAVE_STATUS_ERROR);
    EXPECT_EQ(screenOpened, FALSE);
    EXPECT_EQ(CountChangedSectors(sector, before), 0);
    Free(sector);
}

TEST("Averon region save refusal: no save type or special sector write reaches flash")
{
    u32 saveType = SAVE_NORMAL;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 before[SECTORS_COUNT];
    u32 damaged, hill, recorded;
    bool32 refused;
    PARAMETRIZE { saveType = SAVE_NORMAL; }
    PARAMETRIZE { saveType = SAVE_OVERWRITE_DIFFERENT_FILE; }
    PARAMETRIZE { saveType = SAVE_HALL_OF_FAME; }
    PARAMETRIZE { saveType = SAVE_HALL_OF_FAME_ERASE_BEFORE; }
    PARAMETRIZE { saveType = SAVE_LINK; }
    refused = StartRefusedSave(sector, before);
    gHoFSaveBuffer = Alloc(SECTOR_DATA_SIZE * NUM_HOF_SECTORS);
    memset(gHoFSaveBuffer, 0x5C, SECTOR_DATA_SIZE * NUM_HOF_SECTORS);
    gDamagedSaveSectors = 0;
    HandleSavingData(saveType); // as the save failed screen's retry calls it
    damaged = gDamagedSaveSectors;
    memset(sector, 0x6D, sizeof(*sector));
    hill = TryWriteSpecialSaveSector(SECTOR_ID_TRAINER_HILL, (u8 *)sector);
    recorded = TryWriteSpecialSaveSector(SECTOR_ID_RECORDED_BATTLE, (u8 *)sector);
    AveronRegionSave_BeginLoad();
    Save_ResetSaveCounters();
    gDamagedSaveSectors = 0;
    TRY_FREE_AND_SET_NULL(gHoFSaveBuffer);
    EXPECT(refused);
    EXPECT_NE(damaged, 0); // the caller still sees a failed save
    EXPECT_EQ(hill, SAVE_STATUS_ERROR);
    EXPECT_EQ(recorded, SAVE_STATUS_ERROR);
    EXPECT_EQ(CountChangedSectors(sector, before), 0);
    Free(sector);
}

TEST("Averon region save refusal: the save failed screen never wipes the refused save")
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 before[SECTORS_COUNT];
    MainCallback callback = gMain.callback2;
    IntrCallback vblank = gMain.vblankCallback;
    MainCallback wipeOrEarlier;
    bool32 refused, reachedWipe = FALSE;
    u32 damaged;
    KNOWN_LEAKING; // the screen's buffers are only freed when it returns to the title
    refused = StartRefusedSave(sector, before);
    // A link save refused sector by sector opens the screen directly.
    gDamagedSaveSectors = 0;
    HandleSavingData(SAVE_NORMAL);
    damaged = gDamagedSaveSectors;
    DoSaveFailedScreen(SAVE_NORMAL);
    wipeOrEarlier = gMain.callback2;
    // Fade in, then the wipe step, then wait for A. The fade only advances
    // after the palette transfer VBlank would do.
    for (u32 frame = 0; frame < 128; frame++)
    {
        gMain.callback2();
        TransferPlttBuffer();
        if (gMain.callback2 != wipeOrEarlier)
            reachedWipe = TRUE;
    }
    SetMainCallback2(callback);
    SetVBlankCallback(vblank);
    AveronRegionSave_BeginLoad();
    Save_ResetSaveCounters();
    gDamagedSaveSectors = 0;
    EXPECT(refused);
    EXPECT_NE(damaged, 0);
    EXPECT(reachedWipe); // the screen left its fade-in step
    EXPECT_EQ(CountChangedSectors(sector, before), 0);
    Free(sector);
}

enum
{
    NEWEST_INTACT,
    NEWEST_RECORD_BIT,
    NEWEST_ANCHOR_BIT,
    NEWEST_RECORD_FROM_OLDER,
};

TEST("Averon region save: the early save-block pointer selector picks the slot the load falls back to")
{
    u32 kind = NEWEST_INTACT;
    struct SaveSector *sector = Alloc(sizeof(*sector));
    struct SaveSector *older = Alloc(sizeof(*older));
    u32 newestCounter, offset, expectedSeed;
    s32 physical;
    u8 status;
    PARAMETRIZE { kind = NEWEST_INTACT; }
    PARAMETRIZE { kind = NEWEST_RECORD_BIT; }
    PARAMETRIZE { kind = NEWEST_ANCHOR_BIT; }
    PARAMETRIZE { kind = NEWEST_RECORD_FROM_OLDER; }
    EXPECT(StartFlash());
    SaveTwo();
    newestCounter = gSaveCounter;
    physical = FindPhysical(newestCounter % NUM_SAVE_SLOTS, SECTOR_ID_SAVEBLOCK2);
    ReadSector(physical, sector);
    switch (kind)
    {
    case NEWEST_RECORD_BIT: // the record is outside the sector checksum
        sector->saveBlock3Chunk[offsetof(struct SaveBlock3, averonRegionRecord) + 20] ^= 0x10;
        break;
    case NEWEST_ANCHOR_BIT:
        sector->data[ANCHOR_OFFSET + 1] ^= 0x01;
        sector->checksum = Checksum(sector->data, sizeof(struct SaveBlock2));
        break;
    case NEWEST_RECORD_FROM_OLDER:
        ReadSector(FindPhysical((newestCounter - 1) % NUM_SAVE_SLOTS, SECTOR_ID_SAVEBLOCK2), older);
        memcpy(&((u8 *)sector)[RECORD_OFFSET], &((u8 *)older)[RECORD_OFFSET], AVERON_REGION_RECORD_SIZE);
        break;
    }
    WriteSector(physical, sector);
    expectedSeed = kind == NEWEST_INTACT ? 2 : 1;

    SetTrainerId(9); // RAM must not decide either answer
    Save_ResetSaveCounters();
    offset = GetSaveBlocksPointersBaseOffset();
    EXPECT_EQ(offset, TrainerIdSum(expectedSeed));
    EXPECT_EQ(gSaveCounter, kind == NEWEST_INTACT ? newestCounter : newestCounter - 1);

    Save_ResetSaveCounters();
    status = LoadGameSave(SAVE_NORMAL);
    EXPECT_EQ(status, kind == NEWEST_INTACT ? SAVE_STATUS_OK : SAVE_STATUS_ERROR);
    EXPECT_EQ(gSaveCounter, kind == NEWEST_INTACT ? newestCounter : newestCounter - 1);
    EXPECT_EQ(gSaveBlock2Ptr->playerTrainerId[0], (u8)(0x11 + expectedSeed));
    EXPECT_EQ(gSaveBlock2Ptr->playerTrainerId[3], (u8)(0x44 + expectedSeed));
    Free(older);
    Free(sector);
}
