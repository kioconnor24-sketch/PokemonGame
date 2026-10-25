"""Physical cavern data and executed current production behavior predicates."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3];ENGINE=ROOT/'Pokemon Game/engine'
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/acuity-cavern'
s=importlib.util.spec_from_file_location('acuity_cavern_test',HERE/'build_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class AcuityCavernTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry=json.loads((HERE/'geometry.json').read_text());cls.receipt=json.loads((HERE/'source-receipt.json').read_text())

    def test_actual_production_reflective_predicates_execute_no_surf_splash_or_encounters(self):
        source=(ENGINE/'src/metatile_behavior.c').read_text()
        prefix=source[source.index('#define TILE_FLAG'):source.index('};')+2]
        funcs=[]
        for name in ('IsReflective','IsPuddle','IsSurfableWaterOrUnderwater','IsEncounterTile'):
            start=source.index('bool8 MetatileBehavior_'+name+'(');body=source.index('{',start);depth=1;end=body+1
            while depth:
                depth+=(source[end]=='{')-(source[end]=='}');end+=1
            funcs.append(source[start:end])
        code='''#include <assert.h>
#include <limits.h>
#include "constants/metatile_behaviors.h"
typedef unsigned char u8; typedef unsigned char bool8;
#define TRUE 1
#define FALSE 0
'''+prefix+'\n'+'\n'.join(funcs)+'''
int main(void) {
 assert(MB_REFLECTION_UNDER_BRIDGE==0x2b);
 assert(MetatileBehavior_IsReflective(MB_REFLECTION_UNDER_BRIDGE));
 assert(!MetatileBehavior_IsPuddle(MB_REFLECTION_UNDER_BRIDGE));
 assert(!MetatileBehavior_IsSurfableWaterOrUnderwater(MB_REFLECTION_UNDER_BRIDGE));
 assert(!MetatileBehavior_IsEncounterTile(MB_REFLECTION_UNDER_BRIDGE));
 assert(MetatileBehavior_IsSurfableWaterOrUnderwater(MB_POND_WATER));
 assert(MetatileBehavior_IsPuddle(MB_PUDDLE));
 assert(MetatileBehavior_IsEncounterTile(MB_CAVE));
 assert(!MetatileBehavior_IsEncounterTile(MB_NORMAL));
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as t:
            path=Path(t);(path/'test.c').write_text(code)
            subprocess.run(['cc','-std=c99','-Wall','-Werror','-I',str(ENGINE/'include'),str(path/'test.c'),'-o',str(path/'check')],check=True,capture_output=True)
            subprocess.run([str(path/'check')],check=True)

    def test_source_surface_and_native_reflection_counts_preserved_closed_exit(self):
        raw,_,header=m.construct(self.geometry);cells=struct.unpack('<1024H',raw)
        self.assertEqual(sum(not v&0xc00 for v in cells),386)
        self.assertEqual(sum(v&1023==m.REFLECTIVE for v in cells),182)
        self.assertTrue(cells[29*32+14]&0xc00)
        for key in ('object_events','coord_events','bg_events','warp_events','connections'):self.assertFalse(header[key])
        self.assertEqual(header['region_map_section'],'MAPSEC_PENDING_OWNER')
        for p in self.geometry['walkable']:
            x,y=p['tile']
            self.assertEqual(bool(cells[y*32+x]&0xc00),(x,y)==(14,29))

    def test_real_native_art_replay_and_full_semantics(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'fresh';receipt=m.build(ENGINE,out)
            self.assertEqual(receipt,self.receipt)
            for path in receipt['output_sha256']:self.assertEqual((out/path).read_bytes(),(HERE/path).read_bytes())
        raw=(HERE/'staged/map.bin').read_bytes();attrs=json.loads((HERE/'staged/attributes.json').read_text())
        count=0
        for (v,) in struct.iter_unpack('<H',raw):
            if attrs[str(v&1023)]&511==0x2b:
                self.assertFalse(v&0xc00);count+=1
            elif not v&0xc00:self.assertEqual(attrs[str(v&1023)]&511,0)
        self.assertEqual(count,182)

    def test_private_input_identity_and_escape_are_refused_before_decoding(self):
        pins=json.loads((HERE/'source-pins.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'source-pins.json').write_text(json.dumps(pins))
            (root/pins['files']['land_data']['private_input_name']).write_bytes(b'corrupt')
            with patch.object(m,'HERE',root):
                with self.assertRaisesRegex(ValueError,'identity'):m.read_source(root)
            pins['files']['land_data']['private_input_name']='../outside-private.bin'
            (root/'source-pins.json').write_text(json.dumps(pins))
            with patch.object(m,'HERE',root):
                with self.assertRaisesRegex(ValueError,'escapes'):m.read_source(root)

    def test_duplicate_unreviewed_behavior_height_and_source_exit_refused(self):
        for mutate,error in ((lambda d:d['walkable'].append(d['walkable'][0]),'duplicate'),
                             (lambda d:d['walkable'][0].update(source_behavior=0x10),'unreviewed'),
                             (lambda d:d.update(height=17),'flat'),
                             (lambda d:d['technical_warp'].update(dest_warp_id=0),'exit')):
            d=copy.deepcopy(self.geometry);mutate(d)
            with self.assertRaisesRegex(ValueError,error):m.construct(d)
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad-output')

if __name__=='__main__':unittest.main()
