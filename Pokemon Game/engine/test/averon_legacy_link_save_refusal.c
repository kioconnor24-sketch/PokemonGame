#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "load_save.h"
#include "main.h"
#include "malloc.h"
#include "palette.h"
#include "pokemon.h"
#include "save.h"
#include "task.h"
#include "gba/flash_internal.h"

extern u16 gSaveAttemptStatus;
extern TaskFunc Test_GetSaveAfterLinkBattleTask(void);
extern TaskFunc Test_GetRecordMixingSaveTask(void);

static u16 (*sProgram)(u16, u8 *);
static u16 (*sErase)(u16);
static u16 (*sProgramByte)(u16, u32, u8);
static u32 sWrites;

static u16 CountProgram(u16 sector, u8 *data)
{
    sWrites++;
    return sProgram(sector, data);
}

static u16 CountErase(u16 sector)
{
    sWrites++;
    return sErase(sector);
}

static u16 CountProgramByte(u16 sector, u32 offset, u8 data)
{
    sWrites++;
    return sProgramByte(sector, offset, data);
}

static void CountWrites(bool32 start)
{
    if (start)
    {
        sProgram = ProgramFlashSector;
        sErase = EraseFlashSector;
        sProgramByte = ProgramFlashByte;
        sWrites = 0;
        ProgramFlashSector = CountProgram;
        EraseFlashSector = CountErase;
        ProgramFlashByte = CountProgramByte;
    }
    else
    {
        ProgramFlashSector = sProgram;
        EraseFlashSector = sErase;
        ProgramFlashByte = sProgramByte;
    }
}

static void StartSave(void)
{
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(&gParties[B_TRAINER_PLAYER][0]);
    CalculatePlayerPartyCount();
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
}

static void BlockNewerSave(struct SaveSector *sector)
{
    // Keep the sector checksum valid: this is a newer-format save, not bad flash.
    bool32 found = FALSE;
    for (u32 i = 0; i < NUM_SECTORS_PER_SLOT; i++)
    {
        u32 physical = gSaveCounter % NUM_SAVE_SLOTS * NUM_SECTORS_PER_SLOT + i;
        ReadFlash(physical, 0, (u8 *)sector, sizeof(*sector));
        if (sector->id == SECTOR_ID_SAVEBLOCK2)
        {
            u32 offset = offsetof(struct SaveBlock2, averonRegionAnchor);
            sector->data[offset + 4] = AVERON_REGION_SAVE_FORMAT + 1;
            sector->data[offset + 5] = 0;
            sector->data[offset + 6] = ~(AVERON_REGION_SAVE_FORMAT + 1);
            sector->data[offset + 7] = 0xFF;
            u32 sum = 0;
            for (u32 word = 0; word < sizeof(struct SaveBlock2) / 4; word++)
                sum += ((u32 *)sector->data)[word];
            sector->checksum = (sum >> 16) + sum;
            EXPECT_EQ(EraseFlashSector(physical), 0);
            EXPECT_EQ(ProgramFlashSector(physical, (u8 *)sector), 0);
            found = TRUE;
            break;
        }
    }
    EXPECT(found);
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_CORRUPT);
    EXPECT(AveronRegionSave_IsWriteBlocked());
}

// These are actual production tasks at their save-init or next-sector
// boundaries. The fixture does not emulate a link peer or graphical dialog.
static void ExpectRefusal(TaskFunc callback, u32 state)
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 before[SECTORS_COUNT];
    MainCallback original = gMain.callback2;
    StartSave();
    BlockNewerSave(sector);
    for (u32 i = 0; i < SECTORS_COUNT; ++i)
    {
        ReadFlash(i, 0, (u8 *)sector, sizeof(*sector));
        before[i] = AveronRegionSave_Crc32((const u8 *)sector, sizeof(*sector));
    }
    DoSaveFailedScreen(SAVE_NORMAL);
    MainCallback failure = gMain.callback2;
    SetMainCallback2(original);
    ResetTasks();
    ResetPaletteFade();
    gDamagedSaveSectors = 0;
    gSaveAttemptStatus = SAVE_STATUS_OK;
    gSoftResetDisabled = TRUE;
    u32 counter = gSaveCounter;
    u32 rotation = gLastWrittenSector;
    u32 incremental = gIncrementalSectorId;
    u8 task = CreateTask(callback, 0);
    gTasks[task].data[0] = state;
    gMain.state = 93;
    CountWrites(TRUE);
    callback(task);
    CountWrites(FALSE);
    MainCallback observed = gMain.callback2;
    u32 screenState = gMain.state;
    u32 attempt = gSaveAttemptStatus;
    u32 damaged = gDamagedSaveSectors;
    u32 taskState = gTasks[task].data[0];
    bool32 resetDisabled = gSoftResetDisabled;
    SetMainCallback2(original);
    DestroyTask(task);
    AveronRegionSave_BeginLoad();
    gSoftResetDisabled = FALSE;
    EXPECT_EQ(sWrites, 0);
    EXPECT_EQ(gSaveCounter, counter);
    EXPECT_EQ(gLastWrittenSector, rotation);
    EXPECT_EQ(gIncrementalSectorId, incremental);
    EXPECT_EQ(attempt, SAVE_STATUS_ERROR);
    EXPECT_EQ(damaged, 0);
    for (u32 i = 0; i < SECTORS_COUNT; ++i)
    {
        ReadFlash(i, 0, (u8 *)sector, sizeof(*sector));
        EXPECT_EQ(AveronRegionSave_Crc32((const u8 *)sector, sizeof(*sector)), before[i]);
    }
    Free(sector);
    EXPECT_EQ(observed, failure);
    EXPECT_EQ(screenState, 0);
    EXPECT_EQ(taskState, state);
    EXPECT_EQ(resetDisabled, TRUE);
}

static void ExpectSupportedInit(TaskFunc callback, u32 state)
{
    StartSave();
    MainCallback original = gMain.callback2;
    u32 counter = gSaveCounter;
    ResetTasks();
    ResetPaletteFade();
    u8 task = CreateTask(callback, 0);
    gTasks[task].data[0] = state;
    gSaveAttemptStatus = SAVE_STATUS_OK;
    CountWrites(TRUE);
    callback(task);
    CountWrites(FALSE);
    u32 observed = gTasks[task].data[0];
    DestroyTask(task);
    EXPECT_EQ(gMain.callback2, original);
    EXPECT_EQ(observed, state + 1);
    EXPECT_GT(sWrites, 0);
    EXPECT_EQ(gSaveCounter, counter);
    EXPECT_EQ(gIncrementalSectorId, 0);
    EXPECT_EQ(gSaveAttemptStatus, SAVE_STATUS_OK);
}

TEST("Averon legacy link save refusal: post-battle task stops before save completion")
{
    u32 state = 1;
    PARAMETRIZE { state = 1; }
    PARAMETRIZE { state = 2; }
    ExpectRefusal(Test_GetSaveAfterLinkBattleTask(), state);
}

TEST("Averon legacy link save refusal: Ruby Sapphire record-mixing task stops before save completion")
{
    u32 state = 2;
    PARAMETRIZE { state = 2; }
    PARAMETRIZE { state = 3; }
    ExpectRefusal(Test_GetRecordMixingSaveTask(), state);
}

TEST("Averon legacy link save refusal: supported post-battle task still writes its first sector")
{
    ExpectSupportedInit(Test_GetSaveAfterLinkBattleTask(), 1);
}

TEST("Averon legacy link save refusal: supported record-mixing task still writes its first sector")
{
    ExpectSupportedInit(Test_GetRecordMixingSaveTask(), 2);
}
