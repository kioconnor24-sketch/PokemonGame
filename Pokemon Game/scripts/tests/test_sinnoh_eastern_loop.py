"""Pinned12-map eastern loop: replay source, compact warps and close unknown exits."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eastern-loop'
spec=importlib.util.spec_from_file_location('eastern_source',HERE/'stage_eastern.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


class EasternLoopTest(unittest.TestCase):
    def setUp(self):
        self.receipt=json.loads((HERE/'source-receipt.json').read_text())
        self.headers=copy.deepcopy(self.receipt['source_geometry_headers'])
        self.layouts={n:dict(width=v[0],height=v[1]) for n,v in s.MAPS.items()};self.raws={}
        for n,(w,h,_) in s.MAPS.items():
            raw=bytearray((HERE/'staged'/n/'map.bin').read_bytes())
            for c in self.receipt['closure_changes'][n]:struct.pack_into('<H',raw,2*(c['y']*w+c['x']),c['before'])
            self.raws[n]=bytes(raw)

    def stage(self):return s.base.sanitize(self.headers,self.layouts,self.raws)

    def test_every_original_blob_cell_and_published_header_replays_exactly(self):
        result,closures,_=self.stage();count=0
        for n,(raw,h) in result.items():
            source=self.raws[n];blob=hashlib.sha1(('blob '+str(len(source))+'\0').encode()+source).hexdigest()
            self.assertEqual(blob,s.MAPS[n][2]);self.assertEqual(s.base.sha(source),self.receipt['maps'][n]['source_sha256'])
            self.assertEqual(raw,(HERE/'staged'/n/'map.bin').read_bytes());self.assertEqual(h,json.loads((HERE/'staged'/n/'map.json').read_text()))
            self.assertEqual(closures[n],self.receipt['closure_changes'][n])
            for (old,),(new,) in zip(struct.iter_unpack('<H',source),struct.iter_unpack('<H',raw)):
                self.assertEqual(old&0xF3FF,new&0xF3FF);count+=1
        self.assertEqual(count,34720)

    def test_all17_warps_retain_source_coordinates_and_resolve_coupled_returns(self):
        result,_,tr=self.stage();by_id={h['id']:n for n,(_,h) in result.items()};count=0
        for name,(_,h) in result.items():
            for source_index,stage_index in tr[name].items():
                before=self.headers[name]['warp_events'][source_index];after=h['warp_events'][stage_index]
                for key in ('x','y','elevation','dest_map'):self.assertEqual(before[key],after[key])
                target=by_id[after['dest_map']]
                self.assertEqual(int(after['dest_warp_id']),tr[target][int(before['dest_warp_id'])]);count+=1
        self.assertEqual(count,17)
        self.assertEqual(tr['Route212_Access'],{0:0})
        self.assertEqual(tr['VeilstoneCity'],{0:0,1:1,2:2})
        self.assertEqual(tr['Route213'],{0:0})
        self.assertEqual(tr['ValorLakefront'],{})
        # Actual pinned header uses numeric0, not an invented connection list.
        self.assertEqual(self.headers['Route215_Access']['connections'],0)
        self.assertEqual(result['Route215_Access'][1]['connections'],[])

    def test_every_open_boundary_has_a_real_reciprocal_walkable_endpoint(self):
        result,closures,_=self.stage();by_id={h['id']:n for n,(_,h) in result.items()};checked=0
        opposite={'up':'down','down':'up','left':'right','right':'left'}
        for name,(raw,h) in result.items():
            w,height=s.MAPS[name][:2];cells=struct.unpack('<%dH'%(w*height),raw)
            edges={'up':[(x,0) for x in range(w)],'down':[(x,height-1) for x in range(w)],
                   'left':[(0,y) for y in range(height)],'right':[(w-1,y) for y in range(height)]}
            anchors={(v['x'],v['y']) for v in h['warp_events']}
            for direction,points in edges.items():
                con=next((v for v in h['connections'] if v['direction']==direction),None)
                for x,y in points:
                    if cells[y*w+x]&0xC00 or (x,y) in anchors:continue
                    self.assertIsNotNone(con,(name,direction,x,y))
                    other=by_id[con['map']];tw,th=s.MAPS[other][:2]
                    tx,ty=s.base.destination((x,y),direction,con['offset'],tw,th)
                    self.assertTrue(0<=tx<tw and 0<=ty<th)
                    target=struct.unpack_from('<H',result[other][0],2*(ty*tw+tx))[0]
                    self.assertFalse(target&0xC00,(name,direction,(x,y),other,(tx,ty)))
                    self.assertIn(dict(map=h['id'],direction=opposite[direction],offset=-con['offset']),result[other][1]['connections']);checked+=1
        self.assertGreater(checked,0);self.assertEqual(sum(len(v) for v in closures.values()),340)

    def test_final_corner_closure_cannot_leave_an_originally_open_dangling_seam(self):
        headers={n:dict(id='MAP_'+n,name=n,layout=n+'_Layout',warp_events=[],connections=[])
                 for n in ('A','B')}
        headers['A']['connections']=[dict(map='MAP_B',offset=1,direction='right')]
        headers['B']['connections']=[dict(map='MAP_A',offset=-1,direction='left')]
        layouts={'A':dict(width=3,height=4),'B':dict(width=3,height=2)}
        raws={'A':struct.pack('<12H',*[0x3001]*12),'B':struct.pack('<6H',*[0x3001]*6)}
        out,closures,_=s.base.sanitize(headers,layouts,raws)
        values=struct.unpack('<12H',out['A'][0])
        self.assertEqual(values[1*3+1],0x3001) # actual interior remains open
        self.assertEqual(values[1*3+2],0x3401)
        self.assertEqual(values[2*3+2],0x3401)
        extra=[c for c in closures['A'] if c['reason']=='destination closed by final cluster sanitization']
        self.assertEqual({(c['x'],c['y']) for c in extra},{(2,1),(2,2)})
        # A real retained paired boundary warp remains untouched, even at
        # the destination's corner; the guard must not erase a valid exit.
        headers['A']['warp_events']=[dict(x=2,y=1,elevation=0,dest_map='MAP_B',dest_warp_id='0')]
        headers['B']['warp_events']=[dict(x=0,y=0,elevation=0,dest_map='MAP_A',dest_warp_id='0')]
        out,_,_=s.base.sanitize(headers,layouts,raws)
        self.assertEqual(struct.unpack_from('<H',out['A'][0],2*(1*3+2))[0],0x3001)
        self.assertEqual(struct.unpack_from('<H',out['B'][0],0)[0],0x3001)

    def test_all97_bridge_elevation15_cells_and_real_hardware_footprints_remain(self):
        result,_,_=self.stage();count=0
        for n,(raw,h) in result.items():
            w,height=s.MAPS[n][:2];self.assertLessEqual((w+15)*(height+14),10240)
            count+=sum(c[0]>>12==15 for c in struct.iter_unpack('<H',raw))
        self.assertEqual(count,97)
        self.assertEqual(max((w+15)*(h+14) for w,h,_ in s.MAPS.values()),8510)

    def test_every_map_border_attribute_is_present_without_gameplay_or_saved_ids(self):
        for n in s.MAPS:
            folder=HERE/'staged'/n;h=json.loads((folder/'map.json').read_text())
            attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            self.assertEqual(set(map(int,attrs)),{v[0]&1023 for v in struct.iter_unpack('<H',(folder/'map.bin').read_bytes()+(folder/'border.bin').read_bytes())})
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])
            self.assertTrue(all(w['dest_map'] in {v['id'] for v in self.headers.values()} for w in h['warp_events']))

    def test_wrong_offset_removed_destination_and_invalid_index_are_rejected(self):
        saved=copy.deepcopy(self.headers)
        self.headers['Route213']['connections'][0]['offset']=3
        with self.assertRaises(ValueError):self.stage()
        self.headers=copy.deepcopy(saved);self.headers['Route212_North']['warp_events'][0]['dest_warp_id']='1'
        with self.assertRaises(ValueError):self.stage() # gate1 leads to unbuilt Hearthome
        self.headers=copy.deepcopy(saved);self.headers['Route215']['warp_events'][0]['dest_warp_id']='99'
        with self.assertRaises(ValueError):self.stage()

    def test_duplicate_anchor_and_invalid_dimensions_are_rejected(self):
        self.headers['Route215']['warp_events']*=2
        with self.assertRaises(ValueError):self.stage()
        with self.assertRaises(ValueError):s.base.cells(b'bad',1,1)

    def test_source_inputs_immutable_and_pure_stage_deterministic(self):
        before=copy.deepcopy((self.headers,self.layouts,self.raws))
        self.assertEqual(self.stage(),self.stage());self.assertEqual(before,(self.headers,self.layouts,self.raws))


if __name__=='__main__':unittest.main()
