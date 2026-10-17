// EXPERIMENT ONLY. Copy to engine/test/averon_codex_audio_capacity.c in a
// disposable checkout; not registered in production or the strict baseline.
// Run the test ELF WITHOUT make check's gTestRunnerHeadless patch: headless
// mode deliberately forces CRY_NONE even with P_CRIES_ENABLED, hiding risk.
#include "global.h"
#include "test/test.h"
#include "pokemon.h"
#include "sound.h"
#include "m4a.h"
#include "task.h"
#include "gba/m4a_internal.h"
#include "constants/cries.h"
#include "constants/songs.h"
#include "data.h"

extern struct MusicPlayerInfo *gMPlay_PokemonCry;

TEST("Codex audio capacity target ABI unit costs")
{
    Test_MgbaPrintf("CAPACITY ABI Trainer=%d TrainerMon=%d MapHeader=%d MapLayout=%d Object=%d Warp=%d Coord=%d Bg=%d",
        sizeof(struct Trainer), sizeof(struct TrainerMon), sizeof(struct MapHeader),
        sizeof(struct MapLayout), sizeof(struct ObjectEventTemplate),
        sizeof(struct WarpEvent), sizeof(struct CoordEvent), sizeof(struct BgEvent));
    EXPECT_EQ(sizeof(struct MapLayout), 28);
    EXPECT_EQ(sizeof(struct ObjectEventTemplate), 24);
}

TEST("Codex audio capacity real cry lookup respects configuration")
{
    ASSUME(!gTestRunnerHeadless);
    for (u32 species = 0; species < NUM_SPECIES; ++species)
    {
        if (!IsSpeciesEnabled(species))
            continue;
        enum PokemonCry cry = GetCryIdBySpecies(species);
        EXPECT_LT(cry, CRY_COUNT);
        if (!P_CRIES_ENABLED)
            EXPECT_EQ(cry, CRY_NONE);
    }
    if (P_CRIES_ENABLED)
        EXPECT_NE(GetCryIdBySpecies(SPECIES_BULBASAUR), CRY_NONE);
}

TEST("Codex audio capacity title town route battle victory and heal sequences start")
{
    u16 song;
    PARAMETRIZE { song = MUS_TITLE; }
    PARAMETRIZE { song = MUS_LITTLEROOT; }
    PARAMETRIZE { song = MUS_ROUTE101; }
    PARAMETRIZE { song = MUS_VS_WILD; }
    PARAMETRIZE { song = MUS_VICTORY_WILD; }
    PARAMETRIZE { song = MUS_HEAL; }
    m4aSoundInit();
    PlayBGM(song);
    struct MusicPlayerInfo *player = gMPlayTable[gSongTable[song].ms].info;
    EXPECT_EQ(player->songHeader, gSongTable[song].header);
    for (u32 i = 0; i < 8; ++i)
        MPlayMain(player);
    EXPECT_NE(player->status & MUSICPLAYER_STATUS_TRACK, 0);
}

TEST("Codex audio capacity menu and door effects start")
{
    u16 song;
    PARAMETRIZE { song = SE_SELECT; }
    PARAMETRIZE { song = SE_DOOR; }
    m4aSoundInit();
    PlaySE(song);
    struct MusicPlayerInfo *player = gMPlayTable[gSongTable[song].ms].info;
    EXPECT_EQ(player->songHeader, gSongTable[song].header);
    MPlayMain(player);
    EXPECT_NE(player->status & MUSICPLAYER_STATUS_TRACK, 0);
}

TEST("Codex audio capacity script cry owns a valid completion player from cold start")
{
    ASSUME(!gTestRunnerHeadless);
    m4aSoundInit();
    gMPlay_PokemonCry = NULL; // exactly the production EWRAM initializer
    PlayBGM(MUS_ROUTE101);
    PlayCry_Script(SPECIES_BULBASAUR, CRY_MODE_NORMAL);
    // Fail BEFORE calling the production completion APIs on a null pointer.
    // IsPokemonCryPlaying dereferences ->tracks; GBA open-bus behavior is
    // not a portable guarantee that the experimental no-cries build is safe.
    EXPECT(gMPlay_PokemonCry != NULL);
    StopCryAndClearCrySongs();
    for (u32 i = 0; i < 4; ++i)
        RunTasks();
    EXPECT(IsCryFinished());
    EXPECT(!IsCryPlayingOrClearCrySongs());
}

TEST("Codex audio capacity all cry modes and Mega lookup complete with valid player fixture")
{
    ASSUME(!gTestRunnerHeadless);
    enum Species species;
    PARAMETRIZE { species = SPECIES_BULBASAUR; }
    PARAMETRIZE { species = SPECIES_CHARIZARD_MEGA_X; }
    m4aSoundInit();
    // Explicit fixture: excludes the cold-start null-player case above.
    gMPlay_PokemonCry = &gPokemonCryMusicPlayers[0];
    for (u32 mode = CRY_MODE_NORMAL; mode <= CRY_MODE_WEAK; ++mode)
    {
        PlayCryInternal(species, 0, 120, 10, mode);
        StopCryAndClearCrySongs();
        EXPECT(!IsCryPlayingOrClearCrySongs());
    }
    PlayCry_Script(species, CRY_MODE_NORMAL);
    StopCryAndClearCrySongs();
    for (u32 i = 0; i < 4; ++i)
        RunTasks();
    EXPECT(IsCryFinished());
}
