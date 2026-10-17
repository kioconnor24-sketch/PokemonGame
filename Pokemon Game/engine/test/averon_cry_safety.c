#include "global.h"
#include "test/test.h"
#include "pokemon.h"
#include "sound.h"
#include "m4a.h"
#include "task.h"
#include "gba/m4a_internal.h"
#include "constants/cries.h"
#include "constants/songs.h"
#include "script.h"
#include "constants/script_commands.h"

extern struct MusicPlayerInfo *gMPlay_PokemonCry;
extern u8 gPokemonCryBGMDuckingCounter;
extern ScrCmdFunc gScriptCmdTable[], gScriptCmdTableEnd[];

static void ColdStart(void)
{
    m4aSoundInit();
    ResetTasks();
    gMPlay_PokemonCry = NULL;
    gPokemonCryBGMDuckingCounter = 0;
    PlayBGM(MUS_ROUTE101);
    MPlayMain(&gMPlayInfo_BGM);
}

static void ExpectFullBGMVolume(void)
{
    bool32 active = FALSE;
    for (u32 i = 0; i < gMPlayInfo_BGM.trackCount; ++i)
    {
        if (gMPlayInfo_BGM.tracks[i].flags & MPT_FLG_EXIST)
        {
            active = TRUE;
            EXPECT_EQ(gMPlayInfo_BGM.tracks[i].volX, 64);
        }
    }
    EXPECT(active);
    EXPECT_EQ(gMPlayInfo_BGM.songHeader, gSongTable[MUS_ROUTE101].header);
}

TEST("Averon cry safety cold stop and completion before any cry")
{
    ColdStart();
    StopCry();
    StopCryAndClearCrySongs();
    EXPECT(!IsCryPlaying());
    EXPECT(!IsCryPlayingOrClearCrySongs());
    EXPECT(IsCryFinished());
    ExpectFullBGMVolume();
}

TEST("Averon cry safety script wait and replay restore music")
{
    ColdStart();
    for (u32 replay = 0; replay < 2; ++replay)
    {
        PlayCry_Script(SPECIES_BULBASAUR, CRY_MODE_NORMAL);
        EXPECT(!IsCryFinished());
        StopCry();
        for (u32 i = 0; i < 4; ++i)
            RunTasks();
        EXPECT(IsCryFinished());
        EXPECT(!IsCryPlaying());
        EXPECT(!FuncIsActiveTask(Task_DuckBGMForPokemonCry));
        ExpectFullBGMVolume();
    }
}

TEST("Averon cry safety all modes and Mega stop without a seeded player")
{
    enum Species species;
    PARAMETRIZE { species = SPECIES_BULBASAUR; }
    PARAMETRIZE { species = SPECIES_CHARIZARD_MEGA_X; }
    ColdStart();
    // Includes weak doubles and the API's Dynamax mode; no mechanic enabled.
    for (u32 mode = CRY_MODE_NORMAL; mode <= CRY_MODE_DYNAMAX; ++mode)
    {
        PlayCryInternal(species, 0, 120, 10, mode);
        StopCryAndClearCrySongs();
        EXPECT(!IsCryPlayingOrClearCrySongs());
    }
    ExpectFullBGMVolume();
}

TEST("Averon cry safety silent unpaired duck never lowers music")
{
    ColdStart();
    if (!P_CRIES_ENABLED)
    {
        PlayCry_DuckNoRestore(SPECIES_BULBASAUR, 0, CRY_MODE_NORMAL);
        ExpectFullBGMVolume();
        PlayCry_ReleaseDouble(SPECIES_BULBASAUR, 0, CRY_MODE_NORMAL);
        ExpectFullBGMVolume();
    }
    else
    {
        // Positive control: enabled profile retains the original duck.
        PlayCry_DuckNoRestore(SPECIES_BULBASAUR, 0, CRY_MODE_NORMAL);
        EXPECT_EQ(gMPlayInfo_BGM.tracks[0].volX, 21);
    }
    StopCryAndClearCrySongs();
}

TEST("Averon cry safety normal and by-mode cleanup preserve music and effects")
{
    ColdStart();
    for (u32 mode = CRY_MODE_NORMAL; mode <= CRY_MODE_DYNAMAX; ++mode)
    {
        PlayCry_Normal(SPECIES_BULBASAUR, 0);
        PlayCry_ByMode(SPECIES_BULBASAUR, 0, mode);
        StopCryAndClearCrySongs();
        for (u32 i = 0; i < 4; ++i)
            RunTasks();
        EXPECT(IsCryFinished());
        ExpectFullBGMVolume();
    }
    PlaySE(SE_SELECT);
    EXPECT_EQ(gMPlayTable[gSongTable[SE_SELECT].ms].info->songHeader, gSongTable[SE_SELECT].header);
}

TEST("Averon cry safety real playmoncry waitmoncry bytecode resumes")
{
    static const u8 script[] = {
        SCR_OP_PLAYMONCRY, SPECIES_BULBASAUR & 0xff, SPECIES_BULBASAUR >> 8,
        CRY_MODE_NORMAL, 0, SCR_OP_WAITMONCRY, SCR_OP_END,
    };
    struct ScriptContext ctx;
    ColdStart();
    InitScriptContext(&ctx, gScriptCmdTable, gScriptCmdTableEnd);
    SetupBytecodeScript(&ctx, script);
    EXPECT(RunScriptCommand(&ctx));
    EXPECT_EQ(ctx.nativePtr, IsCryFinished);
    EXPECT(!IsCryFinished());
    StopCry();
    bool32 finished = FALSE;
    for (u32 frame = 0; frame < 6; ++frame)
    {
        RunTasks();
        if (!RunScriptCommand(&ctx))
        {
            finished = TRUE;
            break;
        }
    }
    EXPECT(finished);
    EXPECT_EQ(ctx.scriptPtr, NULL);
    ExpectFullBGMVolume();
}

TEST("Averon cry safety absent species completes without a previous player")
{
    ColdStart();
    PlayCry_Script(SPECIES_NONE, CRY_MODE_NORMAL);
    StopCryAndClearCrySongs();
    EXPECT(!IsCryPlayingOrClearCrySongs());
    for (u32 i = 0; i < 4; ++i)
        RunTasks();
    EXPECT(IsCryFinished());
    ExpectFullBGMVolume();
}
