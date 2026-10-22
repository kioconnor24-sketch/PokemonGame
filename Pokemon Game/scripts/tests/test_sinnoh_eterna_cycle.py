"""Five-map source geography/bridge/warp evidence; no Averon art acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eterna-cycle'
spec=importlib.util.spec_from_file_location('eterna_stage',HERE/'stage_batch.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


class EternaCycleTest(unittest.TestCase):
    def setUp(self):
        self.receipt=json.loads((HERE/'source-receipt.json').read_text())
        self.headers=copy.deepcopy(self.receipt['source_geometry_headers'])
        self.layouts={n:dict(width=v[0],height=v[1]) for n,v in stage.MAPS.items()}
        self.raws={}
        for name in stage.MAPS:
            raw=bytearray((HERE/'staged'/name/'map.bin').read_bytes());width=self.layouts[name]['width']
            for c in self.receipt['closure_changes'][name]:struct.pack_into('<H',raw,(c['y']*width+c['x'])*2,c['before'])
            self.raws[name]=bytes(raw)

    def build(self):return stage.sanitize(self.headers,self.layouts,self.raws)

    def test_published_five_maps_reproduce_from_original_geometry_and_contract(self):
        staged,closures,translations=self.build()
        self.assertEqual(translations,{n:{int(k):v for k,v in d.items()} for n,d in self.receipt['warp_index_translation'].items()})
        for name,(raw,header) in staged.items():
            folder=HERE/'staged'/name
            self.assertEqual(raw,(folder/'map.bin').read_bytes())
            self.assertEqual(header,json.loads((folder/'map.json').read_text()))
            self.assertEqual(closures[name],self.receipt['closure_changes'][name])

    def test_complete_source_ids_and_elevations_preserved_including_bridge15(self):
        staged,_,_=self.build()
        bridge_count=0
        for name,(raw,_) in staged.items():
            self.assertEqual(stage.sha(self.raws[name]),self.receipt['maps'][name]['source_sha256'])
            for (old,),(new,) in zip(struct.iter_unpack('<H',self.raws[name]),struct.iter_unpack('<H',raw)):
                self.assertEqual(old&0xF3FF,new&0xF3FF)
                if name=='Route206' and old>>12==15:bridge_count+=1;self.assertEqual(old>>12,new>>12)
        self.assertEqual(bridge_count,271)

    def test_eterna_sparse_gateway11_and_all_five_cycle_warps_coupled(self):
        staged,_,trans=self.build();self.assertEqual(trans['EternaCity'],{11:0})
        self.assertEqual([w['dest_warp_id'] for w in staged['Route206_North'][1]['warp_events']],['0','0'])
        self.assertEqual([w['dest_warp_id'] for w in staged['Route206'][1]['warp_events']],['1','0','0','1','1'])
        self.assertEqual([w['dest_warp_id'] for w in staged['Route206_South'][1]['warp_events']],['1','3'])

    def test_unbuilt_205_207_coronet_buildings_and_gameplay_stay_absent(self):
        staged,_,_=self.build();ids={h['id'] for _,h in staged.values()}
        for raw,h in staged.values():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])
            self.assertTrue(all(w['dest_map'] in ids for w in h['warp_events']))
            self.assertTrue(all(c['map'] in ids for c in h['connections']))
        self.assertEqual(staged['Route211_West'][1]['warp_events'],[])

    def test_published_reciprocal_seam_walkability(self):
        staged,_,_=self.build();ids={h['id']:name for name,(_,h) in staged.items()}
        for name,(raw,h) in staged.items():
            w,height=stage.MAPS[name][:2];data=stage.cells(raw,w,height)
            for c in h['connections']:
                target=ids[c['map']];tw,th=stage.MAPS[target][:2];dest=stage.cells(staged[target][0],tw,th)
                if c['direction']=='up':points=[(x,0) for x in range(w)]
                elif c['direction']=='down':points=[(x,height-1) for x in range(w)]
                elif c['direction']=='left':points=[(0,y) for y in range(height)]
                else:points=[(w-1,y) for y in range(height)]
                for x,y in points:
                    if (data[y*w+x]>>10)&3:continue
                    dx,dy=stage.destination((x,y),c['direction'],c['offset'],tw,th)
                    self.assertTrue(0<=dx<tw and 0<=dy<th)
                    self.assertEqual((dest[dy*tw+dx]>>10)&3,0)

    def test_missing_wrong_or_nonreciprocal_connection_rejected(self):
        self.headers['Route206']['connections'][0]['offset']=-2
        with self.assertRaisesRegex(ValueError,'nonreciprocal'):self.build()

    def test_invalid_removed_warp_return_rejected(self):
        self.headers['Route206_North']['warp_events'][0]['dest_warp_id']='10'
        with self.assertRaisesRegex(ValueError,'return warp'):self.build()

    def test_duplicate_out_of_bounds_or_noninteger_warp_rejected(self):
        original=copy.deepcopy(self.headers)
        for key,value in [('x',9),('x',1.5),('elevation',16)]:
            self.headers=copy.deepcopy(original);self.headers['Route206_North']['warp_events'][0][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.build()
        self.headers=copy.deepcopy(original);self.headers['Route206_North']['warp_events'][1]=copy.deepcopy(self.headers['Route206_North']['warp_events'][0])
        with self.assertRaises(ValueError):self.build()

    def test_truncated_dimensions_and_unknown_direction_rejected(self):
        for raw,width,height in [(b'',1,1),(bytes(3),1,1),(b'',0,1)]:
            with self.assertRaises(ValueError):stage.cells(raw,width,height)
        with self.assertRaises(ValueError):stage.destination((0,0),'diagonal',0,10,10)

    def test_attribute_receipts_cover_every_used_map_and_border_id(self):
        for name in stage.MAPS:
            folder=HERE/'staged'/name;d=json.loads((folder/'attributes.json').read_text())
            used={v[0]&1023 for v in struct.iter_unpack('<H',(folder/'map.bin').read_bytes()+(folder/'border.bin').read_bytes())}
            self.assertEqual(used,{int(k) for k in d['used_source_attribute_words']})
            self.assertEqual(d['averon_art_compatibility'],'UNVERIFIED')

    def test_no_input_mutation_and_deterministic_replay(self):
        before=copy.deepcopy((self.headers,self.layouts,self.raws));self.assertEqual(self.build(),self.build());self.assertEqual(before,(self.headers,self.layouts,self.raws))

if __name__=='__main__':unittest.main()
