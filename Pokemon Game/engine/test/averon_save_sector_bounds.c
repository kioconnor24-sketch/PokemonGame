#include "global.h"
#include "test/test.h"
#include "save.h"
#include "load_save.h"
#include "event_data.h"
#include "gba/flash_internal.h"
#include "malloc.h"
#include "money.h"
#include "item.h"
#include "pokemon.h"
#include "overworld.h"
#include "constants/maps.h"
#include "constants/heal_locations.h"

static void SeedSaveBoundsState(void)
{
    ClearSaveData();
    Save_ResetSaveCounters();
    ClearBag();
    EXPECT(AddBagItem(ITEM_GREAT_BALL, 4));
    memset(gParties[B_TRAINER_PLAYER], 0, sizeof(gParties[B_TRAINER_PLAYER]));
    ZeroPlayerPartyMons();
    CreateRandomMonWithIVs(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0);
    u32 hp = 1, status = STATUS1_POISON;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &hp);
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_STATUS, &status);
    CalculatePlayerPartyCount();
    for (u32 i = 0; i < 8; ++i)
    {
        if (0xA5 & (1 << i))
            FlagSet(FLAG_BADGE01_GET + i);
        else
            FlagClear(FLAG_BADGE01_GET + i);
    }
    FlagSet(FLAG_AVERON_LICENSE_CUT);
    SetMoney(&gSaveBlock1Ptr->money, 9876);
    SetLastHealLocationWarp(HEAL_LOCATION_ALDERFIELD);
    SetWarpDestination(MAP_GROUP(MAP_COASTALMEADOW), MAP_NUM(MAP_COASTALMEADOW), -1, 18, 22);
    WarpIntoMap();
}

static void ExpectSaveBoundsState(const struct Pokemon *party)
{
    EXPECT_EQ(gSaveBlock1Ptr->location.mapGroup, MAP_GROUP(MAP_COASTALMEADOW));
    EXPECT_EQ(gSaveBlock1Ptr->location.mapNum, MAP_NUM(MAP_COASTALMEADOW));
    EXPECT_EQ(gSaveBlock1Ptr->pos.x, 18);
    EXPECT_EQ(gSaveBlock1Ptr->pos.y, 22);
    for (u32 i = 0; i < 8; ++i)
        EXPECT_EQ(FlagGet(FLAG_BADGE01_GET + i), (0xA5 & (1 << i)) != 0);
    EXPECT_EQ(FlagGet(FLAG_AVERON_LICENSE_CUT), TRUE);
    EXPECT_EQ(GetMoney(&gSaveBlock1Ptr->money), 9876);
    EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_GREAT_BALL), 4);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], 1);
    EXPECT_EQ(memcmp(party, gParties[B_TRAINER_PLAYER], sizeof(gParties[B_TRAINER_PLAYER])), 0);
}

static void CorruptSaveBoundsSector(u32 physical, u16 id, bool32 signatureValid)
{
    struct SaveSector *sector = Alloc(sizeof(*sector));
    EXPECT(sector != NULL);
    ReadFlash(physical, 0, (u8 *)sector, sizeof(*sector));
    EXPECT_EQ(sector->signature, SECTOR_SIGNATURE);
    sector->id = id;
    if (!signatureValid)
        sector->signature = 0;
    EXPECT_EQ(EraseFlashSector(physical), 0);
    EXPECT_EQ(ProgramFlashSector(physical, (u8 *)sector), 0);
    ReadFlash(physical, 0, (u8 *)sector, sizeof(*sector));
    EXPECT_EQ(sector->id, id);
    EXPECT_EQ(sector->signature, signatureValid ? SECTOR_SIGNATURE : 0);
    Free(sector);
}

TEST("Averon save bounds healthy slots retain old format and alternate normally")
{
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    SeedSaveBoundsState();
    struct Pokemon party[PARTY_SIZE];
    memcpy(party, gParties[B_TRAINER_PLAYER], sizeof(party));
    for (u32 i = 0; i < 4; ++i)
    {
        u32 counter = gSaveCounter;
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        EXPECT_EQ(gSaveCounter, counter + 1);
        SetMoney(&gSaveBlock1Ptr->money, 0);
        ClearBag();
        ZeroPlayerPartyMons();
        EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
        ExpectSaveBoundsState(party);
    }
}

static void ExerciseSaveBoundsRecovery(u32 prime, u16 id, bool32 signatureValid, u32 offset)
{
    EXPECT_EQ(NUM_SECTORS_PER_SLOT, 14);
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    {
        // Keep per-case evidence for this long real-flash matrix, including
        // the bank direction, invalid ID and signature variant under test.
        Test_MgbaPrintf("SAVE_BOUNDS prime=%d id=%d sig=%d offset=%d", prime, id, signatureValid, offset);
        SeedSaveBoundsState();
        struct Pokemon party[PARTY_SIZE];
        memcpy(party, gParties[B_TRAINER_PLAYER], sizeof(party));
        if (prime)
            EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        u32 previous = gSaveCounter;
        SetMoney(&gSaveBlock1Ptr->money, 42);
        FlagClear(FLAG_BADGE01_GET);
        ClearBag();
        ZeroPlayerPartyMons();
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        CorruptSaveBoundsSector((gSaveCounter % NUM_SAVE_SLOTS) * NUM_SECTORS_PER_SLOT + offset,
                                id, signatureValid);
        EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_ERROR);
        EXPECT_EQ(gSaveCounter, previous);
        ExpectSaveBoundsState(party);
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
        ExpectSaveBoundsState(party);
    }
}

// Count each direction/footer variant independently, keeping each real-flash
// run bounded and making an omitted variant visible in the positive count.
#define SAVE_BOUNDS_SECTOR_PARAMETERS \
    PARAMETRIZE { offset = 0; } \
    PARAMETRIZE { offset = 1; } \
    PARAMETRIZE { offset = 2; } \
    PARAMETRIZE { offset = 3; } \
    PARAMETRIZE { offset = 4; } \
    PARAMETRIZE { offset = 5; } \
    PARAMETRIZE { offset = 6; } \
    PARAMETRIZE { offset = 7; } \
    PARAMETRIZE { offset = 8; } \
    PARAMETRIZE { offset = 9; } \
    PARAMETRIZE { offset = 10; } \
    PARAMETRIZE { offset = 11; } \
    PARAMETRIZE { offset = 12; } \
    PARAMETRIZE { offset = 13; }

TEST("Averon save bounds ID14 signed unprimed recovery")
{
    u32 offset;
    SAVE_BOUNDS_SECTOR_PARAMETERS
    ExerciseSaveBoundsRecovery(0, 14, TRUE, offset);
}

TEST("Averon save bounds ID14 signed primed recovery")
{
    u32 offset;
    SAVE_BOUNDS_SECTOR_PARAMETERS
    ExerciseSaveBoundsRecovery(1, 14, TRUE, offset);
}

TEST("Averon save bounds ID65535 signed unprimed recovery")
{
    u32 offset;
    SAVE_BOUNDS_SECTOR_PARAMETERS
    ExerciseSaveBoundsRecovery(0, 65535, TRUE, offset);
}

TEST("Averon save bounds ID65535 signed primed recovery")
{
    u32 offset;
    SAVE_BOUNDS_SECTOR_PARAMETERS
    ExerciseSaveBoundsRecovery(1, 65535, TRUE, offset);
}

TEST("Averon save bounds ID14 unsigned unprimed recovery")
{
    u32 offset;
    SAVE_BOUNDS_SECTOR_PARAMETERS
    ExerciseSaveBoundsRecovery(0, 14, FALSE, offset);
}

TEST("Averon save bounds ID14 unsigned primed recovery")
{
    u32 offset;
    SAVE_BOUNDS_SECTOR_PARAMETERS
    ExerciseSaveBoundsRecovery(1, 14, FALSE, offset);
}

TEST("Averon save bounds ID65535 unsigned unprimed recovery")
{
    u32 offset;
    SAVE_BOUNDS_SECTOR_PARAMETERS
    ExerciseSaveBoundsRecovery(0, 65535, FALSE, offset);
}

TEST("Averon save bounds ID65535 unsigned primed recovery")
{
    u32 offset;
    SAVE_BOUNDS_SECTOR_PARAMETERS
    ExerciseSaveBoundsRecovery(1, 65535, FALSE, offset);
}

#undef SAVE_BOUNDS_SECTOR_PARAMETERS

TEST("Averon save bounds handle erased and invalid-ID slots without a backup")
{
    u16 id;
    PARAMETRIZE { id = 14; }
    PARAMETRIZE { id = 65535; }
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    ClearSaveData();
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_EMPTY);
    SeedSaveBoundsState();
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    u32 first = gSaveCounter % NUM_SAVE_SLOTS;
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    u32 second = gSaveCounter % NUM_SAVE_SLOTS;
    CorruptSaveBoundsSector(first * NUM_SECTORS_PER_SLOT, id, TRUE);
    CorruptSaveBoundsSector(second * NUM_SECTORS_PER_SLOT, id, TRUE);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_CORRUPT);
    // Both-invalid status is preserved; never pretend partial copied data is
    // an accepted save. A new clean save must still be possible afterward.
    SeedSaveBoundsState();
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
}
