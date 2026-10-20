"""Temporary Git bank fixtures and executable host animation scheduling checks."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import unittest
from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1]
def load(name, file):
    s=importlib.util.spec_from_file_location(name, SCRIPTS/file); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
m=load('dual_family', 'sinnoh-dual-bank-family.py')
fmod=load('static_fixtures', 'tests/test_sinnoh_isolated_tileset.py')
ENGINE=SCRIPTS.parent/'engine'


class PairedFamilyTests(unittest.TestCase):
    def setUp(self):
        f=self.f=fmod.IsolatedFamilyTests('test_wrong_head'); f.setUp(); self.addCleanup(f.doCleanups)
        for rel in m.base.CONTRACTS:
            data=(ENGINE/rel).read_bytes(); (f.root/rel).write_bytes(data); (f.engine/rel).write_bytes(data)
        for bank,folder in enumerate(m.BANKS):
            p=f.root/'data/tilesets'/folder; p.mkdir(parents=True,exist_ok=True)
            im=Image.new('P',(128,256),1); im.putpalette([v for i in range(256) for v in (i,i,i)]); im.save(p/'tiles.png')
            record=struct.pack('<8H', *([432 if bank==0 else (512 | (6<<12))]*8))
            (p/'metatiles.bin').write_bytes(record+bytes(511*16))
            (p/'metatile_attributes.bin').write_bytes(bytes(1024))
            for i in range(16):
                q=p/('palettes/%02d.pal'%i); q.parent.mkdir(exist_ok=True)
                q.write_text('JASC-PAL\n0100\n16\n'+('255 0 0\n' if bank==0 else '0 0 255\n')*16)
        for kind,(count,tiles) in m.ANIMS.items():
            for frame in range(count):
                p=f.bank/('anim/%s/%d.png'%(kind,frame)); p.parent.mkdir(parents=True,exist_ok=True)
                im=Image.new('P',(8,tiles*8),frame%15+1); im.putpalette([v for i in range(256) for v in (i,i,i)]); im.save(p)
        (f.root/f.layout['blockdata_filepath']).write_bytes(struct.pack('<2H',0x1400,0xFC00|512))
        f.commit()

    def stage(self, name='Route202'):
        f=self.f; return m.stage(f.root,f.engine,f.rev,name,f.output)

    def test_paired_banks_and_source_bits_are_preserved(self):
        r=self.stage(); f=self.f
        self.assertEqual(r['dependencies']['metatiles'],[0,512])
        self.assertEqual(r['dependencies']['graphic_tiles'],[432,512])
        self.assertEqual((f.output/'map.bin').read_bytes(),struct.pack('<2H',0x1400,0xFC00|512))
        self.assertEqual(r['animation_frames'],26)
        self.assertEqual(len(list((f.output/'data').rglob('*.pal'))),32)
        im=Image.open(f.output/'preview.png')
        self.assertEqual(im.getpixel((0,0)),(248,0,0)); self.assertEqual(im.getpixel((16,0)),(0,0,248))
        self.assertFalse(any(x.name=='map.json' for x in f.output.rglob('*')))

    def test_generated_symbols_and_paths_are_isolated(self):
        self.stage(); f=self.f
        text=(f.output/'animations.inc').read_text()
        self.assertIn('InitTilesetAnim_SinnohImported',text)
        self.assertNotIn('_General',text)
        self.assertIn('data/tilesets/primary/sinnoh_imported/anim/water/0.png',text)
        self.assertIn('gTileset_SinnohImportedPetalburg',(f.output/'family.c').read_text())

    def test_second_map_uses_same_reusable_family(self):
        f=self.f; p=f.root/'data/maps/FixtureTown/map.json'; p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'id':'MAP_FIXTURE_TOWN','layout':'LAYOUT_ROUTE202'})); f.commit()
        self.assertEqual(self.stage('FixtureTown')['map'],'FixtureTown')

    def test_unverified_pair_refused(self):
        f=self.f; f.layout['secondary_tileset']='gTileset_Rustboro'
        f.table.write_text(json.dumps({'layouts':[f.layout]})); f.commit()
        with self.assertRaisesRegex(ValueError,'unsupported tileset pair'): self.stage()
        self.assertFalse(f.output.exists())

    def test_dirty_animation_refused(self):
        (self.f.bank/'anim/water/0.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'dirty'): self.stage()

    def test_frame_transfer_size_refused(self):
        p=self.f.bank/'anim/water/0.png'; im=Image.new('P',(8,8)); im.save(p); self.f.commit()
        with self.assertRaisesRegex(ValueError,'transfer size'): self.stage()

    def test_secondary_attribute_count_refused(self):
        p=self.f.root/'data/tilesets/secondary/petalburg/metatile_attributes.bin'; p.write_bytes(bytes(2)); self.f.commit()
        with self.assertRaisesRegex(ValueError,'attribute count'): self.stage()

    def test_secondary_graphic_bounds(self):
        p=self.f.root/'data/tilesets/secondary/petalburg/tiles.png'; im=Image.new('P',(128,8)); im.save(p)
        records=self.f.bank/'metatiles.bin'; records.write_bytes(struct.pack('<8H',*([1023]*8))+bytes(511*16));self.f.commit()
        with self.assertRaisesRegex(ValueError,'absent source graphic'): self.stage()

    def test_source_contract_change_refused(self):
        (self.f.engine/'src/tileset_anims.c').write_text('changed')
        with self.assertRaisesRegex(ValueError,'contract mismatch'): self.stage()

    def test_malformed_callback_closure_refused(self):
        with self.assertRaisesRegex(ValueError,'function shape'): m.animation_include('void Other(void) {}')

    def test_border_secondary_references_checked(self):
        f=self.f; p=f.root/'data/tilesets/secondary/petalburg/metatiles.bin';p.write_bytes(bytes(16))
        (f.root/'data/tilesets/secondary/petalburg/metatile_attributes.bin').write_bytes(bytes(2))
        (f.root/f.layout['border_filepath']).write_bytes(struct.pack('<4H',513,0,0,0));f.commit()
        with self.assertRaisesRegex(ValueError,'absent source metatile'): self.stage()

    def test_generated_callback_executes_full_256_tick_schedule(self):
        self.stage(); f=self.f
        harness='''#include <stdint.h>
#include <assert.h>
typedef uint16_t u16;
typedef uint8_t u8;
#define INCGFX_U16(...) {0}
#define ARRAY_COUNT(x) (sizeof(x)/sizeof((x)[0]))
#define TILE_OFFSET_4BPP(x) ((uintptr_t)(x)*32)
#define TILE_SIZE_4BPP 32
#define BG_VRAM ((uintptr_t)0)
static u16 sPrimaryTilesetAnimCounter,sPrimaryTilesetAnimCounterMax;
static void (*sPrimaryTilesetAnimCallback)(u16);
static unsigned calls;
static void AppendTilesetAnimToBuffer(const u16 *src,u16 *dst,unsigned size);
#include "animations.inc"
static unsigned tick;
static void AppendTilesetAnimToBuffer(const u16 *src,u16 *dst,unsigned size) {
 const unsigned offsets[]={508,432,464,496,480}, counts[]={4,30,10,6,10};
 unsigned phase=tick%16, frame=tick/16; assert(phase<5);
 assert((uintptr_t)dst==offsets[phase]*32); assert(size==counts[phase]*32);
 const u16 *expected=0;
 switch(phase) {
 case 0:expected=gTilesetAnims_SinnohImported_Flower[frame%4];break;
 case 1:expected=gTilesetAnims_SinnohImported_Water[frame%8];break;
 case 2:expected=gTilesetAnims_SinnohImported_SandWaterEdge[frame%8];break;
 case 3:expected=gTilesetAnims_SinnohImported_Waterfall[frame%4];break;
 case 4:expected=gTilesetAnims_SinnohImported_LandWaterEdge[frame%4];break;
 }
 assert(src==expected);++calls;
}
int main(void) {
 InitTilesetAnim_SinnohImported(); assert(sPrimaryTilesetAnimCounter==0);
 assert(sPrimaryTilesetAnimCounterMax==256); assert(sPrimaryTilesetAnimCallback);
 for(tick=0;tick<256;++tick) sPrimaryTilesetAnimCallback(tick);
 assert(calls==80);return 0;
}
'''
        (f.output/'harness.c').write_text(harness)
        subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',str(f.output/'harness.c'),'-o',str(f.output/'harness')],check=True)
        subprocess.run([str(f.output/'harness')],check=True)


if __name__=='__main__': unittest.main()
