// Instrumented native boundary test only. Copy to engine/test in a disposable
// tree and link with --wrap=m4aMPlayStop --wrap=IsPokemonCryPlaying. This traps
// NULL submissions BEFORE unsafe driver reads (GBA open bus can hide them).
// Not registered in ordinary game/native builds; never changes driver behavior
// for a valid player. Pair with the unwrapped averon_cry_safety.c regression.
#include "global.h"
#include "test/test.h"
#include "sound.h"
#include "m4a.h"
#include "task.h"
#include "gba/m4a_internal.h"
#include "constants/cries.h"

extern struct MusicPlayerInfo *gMPlay_PokemonCry;
extern u8 gPokemonCryBGMDuckingCounter;
extern void __real_m4aMPlayStop(struct MusicPlayerInfo *);
extern bool32 __real_IsPokemonCryPlaying(struct MusicPlayerInfo *);
static u32 sNullStops, sNullPolls;

void __wrap_m4aMPlayStop(struct MusicPlayerInfo *player)
{
    if (player == NULL)
        ++sNullStops;
    else
        __real_m4aMPlayStop(player);
}

bool32 __wrap_IsPokemonCryPlaying(struct MusicPlayerInfo *player)
{
    if (player == NULL)
    {
        ++sNullPolls;
        return FALSE;
    }
    return __real_IsPokemonCryPlaying(player);
}

TEST("Averon cry safety instrumented cold APIs never submit NULL to driver")
{
    m4aSoundInit();
    ResetTasks();
    gMPlay_PokemonCry = NULL;
    gPokemonCryBGMDuckingCounter = 0;
    sNullStops = sNullPolls = 0;
    StopCry();
    StopCryAndClearCrySongs();
    EXPECT(!IsCryPlaying());
    EXPECT(!IsCryPlayingOrClearCrySongs());
    PlayCry_Script(SPECIES_BULBASAUR, CRY_MODE_NORMAL);
    StopCry();
    for (u32 i = 0; i < 4; ++i)
        RunTasks();
    EXPECT(IsCryFinished());
    Test_MgbaPrintf("NULL_PROBE stops=%d polls=%d", sNullStops, sNullPolls);
    EXPECT_EQ(sNullStops, 0);
    EXPECT_EQ(sNullPolls, 0);
}
