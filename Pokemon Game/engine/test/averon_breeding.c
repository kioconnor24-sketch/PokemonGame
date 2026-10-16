#include "global.h"
#include "test/test.h"
#include "daycare.h"
#include "pokemon.h"

// Breeding hatches GetEggSpecies of the mother. For every breedable species
// the result must be a real, enabled species and the bottom of its own
// family. GetEggSpecies scans every species, so the run is split into 16
// parts to stay inside the runner's per-run time limit.

#define PARTS 16

static bool32 IsBattleOnlySpecies(u32 species)
{
    const struct SpeciesInfo *info = &gSpeciesInfo[species];
    return info->isTotem || info->isMegaEvolution || info->isPrimalReversion
        || info->isUltraBurst || info->isGigantamax || info->isTeraForm;
}

TEST("Averon every breedable species hatches from a real base species")
{
    u32 part = 0, bad = 0, checked = 0;
    for (u32 p = 0; p < PARTS; p++)
        PARAMETRIZE { part = p; }
    for (u32 species = SPECIES_NONE + 1 + part; species < NUM_SPECIES; species += PARTS)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG || IsBattleOnlySpecies(species)
         || gSpeciesInfo[species].eggGroups[0] == EGG_GROUP_NO_EGGS_DISCOVERED)
            continue;
        u32 egg = GetEggSpecies(species);
        checked++;
        if (egg == SPECIES_NONE || egg >= NUM_SPECIES || !IsSpeciesEnabled(egg)
         || IsBattleOnlySpecies(egg) || GetEggSpecies(egg) != egg)
        {
            DebugPrintf("egg species %S -> %u", GetSpeciesName(species), egg);
            bad++;
        }
    }
    DebugPrintf("part %u: breedable species checked %u", part, checked);
    EXPECT_GT(checked, 0);
    EXPECT_EQ(bad, 0);
}
