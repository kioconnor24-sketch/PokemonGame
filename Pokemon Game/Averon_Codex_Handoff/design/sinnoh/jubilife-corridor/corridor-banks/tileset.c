#include "global.h"
#include "tileset_anims.h"
extern const u32 gTilesetTiles_Rustboro[];
extern const u16 gTilesetPalettes_Rustboro[][16];
const u16 gMetatiles_AveronCorridorRustboro[] = INCBIN_U16("data/tilesets/secondary/averon_corridor_rustboro/metatiles.bin");
const u16 gMetatileAttributes_AveronCorridorRustboro[] = INCBIN_U16("data/tilesets/secondary/averon_corridor_rustboro/metatile_attributes.bin");
const struct Tileset gTileset_AveronCorridorRustboro = {
 .isCompressed=TRUE, .isSecondary=TRUE,
 .tiles=gTilesetTiles_Rustboro, .palettes=gTilesetPalettes_Rustboro,
 .metatiles=gMetatiles_AveronCorridorRustboro,
 .metatileAttributes=gMetatileAttributes_AveronCorridorRustboro,
 .callback=InitTilesetAnim_Rustboro,
};
