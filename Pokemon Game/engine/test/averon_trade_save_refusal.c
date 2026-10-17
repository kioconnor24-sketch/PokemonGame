#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "load_save.h"
#include "main.h"
#include "malloc.h"
#include "palette.h"
#include "pokemon.h"
#include "save.h"
#include "sprite.h"
#include "task.h"
#include "gba/flash_internal.h"

extern u16 gSaveAttemptStatus;
extern MainCallback Test_GetTradeSaveCallback(bool32 wireless);

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

enum { FULL_TASK, WIRED_TRADE, WIRELESS_TRADE };

static void ExpectRefusal(u32 caller)
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 before[SECTORS_COUNT];
    MainCallback original = gMain.callback2;
    StartSave();
    BlockNewerSave(sector);
    for (u32 i = 0; i < SECTORS_COUNT; i++)
    {
        ReadFlash(i, 0, (u8 *)sector, sizeof(*sector));
        before[i] = AveronRegionSave_Crc32((const u8 *)sector, sizeof(*sector));
    }
    // Obtain the actual screen callback without running/allocating its UI.
    DoSaveFailedScreen(SAVE_NORMAL);
    MainCallback failure = gMain.callback2;
    SetMainCallback2(original);
    ResetTasks();
    ResetSpriteData();
    ResetPaletteFade();
    gDamagedSaveSectors = 0;
    gSaveAttemptStatus = SAVE_STATUS_OK;
    u32 counter = gSaveCounter;
    u32 rotation = gLastWrittenSector;
    u32 incremental = gIncrementalSectorId;
    u8 task = TASK_NONE;
    if (caller == FULL_TASK)
    {
        task = CreateTask(Task_LinkFullSave, 0);
        gTasks[task].data[0] = 3; // the real task's save-init boundary
        gTasks[task].data[2] = TRUE; // no overworld/Battle Tower fixture needed
        gMain.state = 93;
    }
    else
    {
        // These actual save-write states do not require a link peer or private
        // trade-animation allocation when the low-level call refuses writes.
        gMain.state = caller == WIRED_TRADE ? 52 : 4;
    }
    CountWrites(TRUE);
    if (caller == FULL_TASK)
        Task_LinkFullSave(task);
    else
        Test_GetTradeSaveCallback(caller == WIRELESS_TRADE)();
    CountWrites(FALSE);
    MainCallback observed = gMain.callback2;
    u32 state = gMain.state;
    u32 attempt = gSaveAttemptStatus;
    u32 damaged = gDamagedSaveSectors;
    u32 taskState = caller == FULL_TASK ? gTasks[task].data[0] : 0;
    SetMainCallback2(original);
    if (task != TASK_NONE)
        DestroyTask(task);
    AveronRegionSave_BeginLoad();
    EXPECT_EQ(sWrites, 0);
    EXPECT_EQ(gSaveCounter, counter);
    EXPECT_EQ(gLastWrittenSector, rotation);
    EXPECT_EQ(gIncrementalSectorId, incremental);
    EXPECT_EQ(attempt, SAVE_STATUS_ERROR);
    EXPECT_EQ(damaged, 0); // refusal does not invent a physically damaged sector
    for (u32 i = 0; i < SECTORS_COUNT; i++)
    {
        ReadFlash(i, 0, (u8 *)sector, sizeof(*sector));
        EXPECT_EQ(AveronRegionSave_Crc32((const u8 *)sector, sizeof(*sector)), before[i]);
    }
    Free(sector);
    EXPECT_EQ(observed, failure);
    EXPECT_EQ(state, 0); // the screen must start at initialization, not case 1
    if (caller == FULL_TASK)
        EXPECT_EQ(taskState, 3); // did not advance toward successful completion
}

TEST("Averon trade save refusal: full-save task enters failure without writing")
{
    ExpectRefusal(FULL_TASK);
}

TEST("Averon trade save refusal: wired callback enters failure without writing")
{
    ExpectRefusal(WIRED_TRADE);
}

TEST("Averon trade save refusal: wireless callback enters failure without writing")
{
    ExpectRefusal(WIRELESS_TRADE);
}

TEST("Averon trade save refusal: a supported full-save task still initializes")
{
    StartSave();
    MainCallback callback = gMain.callback2;
    u32 counter = gSaveCounter;
    ResetTasks();
    u8 task = CreateTask(Task_LinkFullSave, 0);
    gTasks[task].data[0] = 3;
    gTasks[task].data[2] = TRUE;
    gSaveAttemptStatus = SAVE_STATUS_OK;
    Task_LinkFullSave(task);
    u32 state = gTasks[task].data[0];
    DestroyTask(task);
    EXPECT_EQ(gMain.callback2, callback);
    EXPECT_EQ(state, 4);
    EXPECT_EQ(gSaveCounter, counter + 1);
    EXPECT_EQ(gSaveAttemptStatus, SAVE_STATUS_OK);
}
