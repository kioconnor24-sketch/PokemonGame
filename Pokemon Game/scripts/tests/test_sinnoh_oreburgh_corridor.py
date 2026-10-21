"""Off-engine source geometry and sparse warp contracts, not gameplay tests."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE = Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/oreburgh-donor'
spec = importlib.util.spec_from_file_location('oreburgh_corridor', HERE/'stage_corridor.py')
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)
SOURCES = json.loads((HERE/'source-inspection.json').read_text())


class CorridorTest(unittest.TestCase):
    def source(self, name):
        entry = SOURCES[name]
        return dict(warp_events=copy.deepcopy(entry['warp_geometry']),
                    connections=copy.deepcopy(entry['connections']))

    def city(self):
        return stage.stage_map('OreburghCity', self.source('OreburghCity'), bytes(70*59*2),70,59)

    def test_city_retains_source_warp_ids_not_compacted_indices(self):
        raw, warps, changes = self.city()
        self.assertEqual([w['source_warp_id'] for w in warps],[0,11,12,13,14])
        self.assertEqual([(w['x'],w['y']) for w in warps[1:]],[(50,57),(51,57),(52,57),(53,57)])
        self.assertEqual([w['dest_warp_id'] for w in warps[1:]],['0','0','1','1'])
        self.assertNotIn('MAP_LILYCOVE_CITY_LILYCOVE_MUSEUM_1F',[w['dest_map'] for w in warps])

    def test_unbuilt_city_doors_are_solid_but_mine_and_gate_stay_open(self):
        raw, warps, changes = self.city()
        result=stage.cells(raw,70,59)
        for i,w in enumerate(self.source('OreburghCity')['warp_events']):
            self.assertEqual((result[w['y']*70+w['x']]>>10)&3,0 if i in stage.KEEP['OreburghCity'] else 1)

    def test_overlap_spans_are_closed_only_outside_reciprocal_offset(self):
        city=stage.cells(self.city()[0],70,59)
        route=stage.cells(stage.stage_map('Route207',self.source('Route207'),bytes(64*32*2),64,32)[0],64,32)
        self.assertTrue(all((city[x]>>10)&3==1 for x in range(35)))
        self.assertTrue(all((city[x]>>10)&3==0 for x in range(35,69)))
        self.assertTrue(all((route[31*64+x]>>10)&3==0 for x in range(1,35)))
        self.assertTrue(all((route[31*64+x]>>10)&3==1 for x in range(35,64)))
        self.assertTrue(all((route[x]>>10)&3==1 for x in range(64)))

    def test_cell_elevation_and_identity_preserved_during_closure(self):
        before=[(i%1024)|((i%16)<<12)|0x800 for i in range(64*32)]
        raw=struct.pack('<2048H',*before)
        result,_,changes=stage.stage_map('Route207',self.source('Route207'),raw,64,32)
        after=stage.cells(result,64,32)
        self.assertTrue(changes)
        for old,new in zip(before,after):
            self.assertEqual(old&0xF3FF,new&0xF3FF)
        self.assertEqual((after[5*64+52]>>10)&3,1)  # Mt Coronet remains closed.

    def test_bad_dimensions_and_truncated_cells_rejected(self):
        for raw,w,h in ((b'',70,59),(bytes(70*59*2-1),70,59),(b'',0,0)):
            with self.subTest(dimensions=(w,h)),self.assertRaises(ValueError):
                stage.stage_map('OreburghCity',self.source('OreburghCity'),raw,w,h)

    def test_invalid_warp_coordinates_elevation_and_duplicates_rejected(self):
        for key,value in [('x',70),('y',-1),('elevation',16),('x',1.5)]:
            source=self.source('OreburghCity');source['warp_events'][0][key]=value
            with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'warp coordinate'):
                stage.stage_map('OreburghCity',source,bytes(8260),70,59)
        source=self.source('OreburghCity');source['warp_events'][1]=copy.deepcopy(source['warp_events'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):
            stage.stage_map('OreburghCity',source,bytes(8260),70,59)

    def test_no_silent_close_of_active_exit(self):
        source=self.source('OreburghCity');source['warp_events'][0]['x']=0
        with self.assertRaisesRegex(ValueError,'retained warp'):
            stage.stage_map('OreburghCity',source,bytes(8260),70,59)

    def gate(self):
        return dict(warp_events=[{},dict(x=25,y=20,elevation=0,dest_map='MAP_OREBURGH_CITY',dest_warp_id='0')])

    def test_reciprocal_mine_city_gate_and_source_seam(self):
        headers={n:self.source(n) for n in stage.KEEP}
        stage.validate_links(headers,self.gate())
        self.assertEqual(headers['OreburghCity']['warp_events'][11]['dest_warp_id'],'0')
        self.assertEqual(headers['OreburghCity']['warp_events'][14]['dest_warp_id'],'1')

    def test_changed_offset_or_gate_return_rejected(self):
        headers={n:self.source(n) for n in stage.KEEP}
        headers['Route207']['connections'][1]['offset']=-34
        with self.assertRaisesRegex(ValueError,'connection'):
            stage.validate_links(headers,self.gate())
        headers={n:self.source(n) for n in stage.KEEP};gate=self.gate();gate['warp_events'][1]['dest_warp_id']='1'
        with self.assertRaisesRegex(ValueError,'warp identity'):
            stage.validate_links(headers,gate)

    def test_published_geometry_matches_source_hash_and_disclosed_changes(self):
        for name,(width,height,blob) in stage.accepted.MAPS.items():
            if name not in stage.KEEP:
                continue
            folder=HERE/'corridor'/name
            source=(folder/'source.bin').read_bytes();staged=(folder/'map.bin').read_bytes()
            self.assertEqual(hashlib.sha1(b'blob %d\0'%len(source)+source).hexdigest(),blob)
            info=json.loads((folder/'map.json').read_text())
            changes={c['y']*width+c['x']:c for c in info['collision_closures']}
            before,after=stage.cells(source,width,height),stage.cells(staged,width,height)
            self.assertEqual({i for i,(a,b) in enumerate(zip(before,after)) if a!=b},set(changes))
            for i,(a,b) in enumerate(zip(before,after)):
                self.assertEqual(a&0xF3FF,b&0xF3FF)
                if i in changes:
                    self.assertEqual(changes[i]['before'],a);self.assertEqual(changes[i]['after'],b)
                    self.assertEqual((b>>10)&3,1)
            self.assertIsNone(info['section'])
            self.assertEqual(info['object_events']+info['scripts']+info['encounters'],[])
            self.assertEqual(info['status'],'OFF_ENGINE_GEOMETRY_ONLY_GRAPHICS_PENDING')


if __name__=='__main__':
    unittest.main()
