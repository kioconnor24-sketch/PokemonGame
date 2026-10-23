"""Pinned snow geography and weather, independently replayed without donor art."""
import copy, hashlib, importlib.util, json, struct, tempfile, unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/snow-corridor'
spec=importlib.util.spec_from_file_location('snow_stage',HERE/'stage_snow.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class SnowTest(unittest.TestCase):
    def setUp(self):
        self.r=json.loads((HERE/'source-receipt.json').read_text());self.headers=copy.deepcopy(self.r['source_geometry_headers'])
        self.layouts={n:dict(width=d[0],height=d[1]) for n,d in a.MAPS.items()};self.raw={}
        for n,(w,h,_) in a.MAPS.items():
            raw=bytearray((HERE/'staged'/n/'map.bin').read_bytes())
            for c in self.r['closure_changes'][n]:struct.pack_into('<H',raw,2*(c['y']*w+c['x']),c['before'])
            self.raw[n]=bytes(raw)
    def build(self):return a.base.sanitize(self.headers,self.layouts,self.raw)

    def test_all14624_original_cells_git_blobs_and_four_outputs_replay(self):
        staged,closures,_=self.build();self.assertEqual(sum(len(v)//2 for v in self.raw.values()),14624)
        for n,(raw,h) in staged.items():
            original=self.raw[n];blob=hashlib.sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
            self.assertEqual(blob,a.MAPS[n][2]);self.assertEqual(a.base.sha(original),self.r['maps'][n]['source_sha256'])
            self.assertEqual(raw,(HERE/'staged'/n/'map.bin').read_bytes());h['weather']='WEATHER_SNOW'
            self.assertEqual(h,json.loads((HERE/'staged'/n/'map.json').read_text()));self.assertEqual(closures[n],self.r['closure_changes'][n])

    def test_all_elevations_ids_and24_bridge_cells_survive50_explicit_closures(self):
        staged,_,_=self.build();bridges=0;self.assertEqual(sum(len(c) for c in self.r['closure_changes'].values()),50)
        for n,(raw,h) in staged.items():
            w,height,_=a.MAPS[n];self.assertLessEqual((w+15)*(height+14),10240);closed={c['y']*w+c['x'] for c in self.r['closure_changes'][n]}
            for i,((old,),(new,)) in enumerate(zip(struct.iter_unpack('<H',self.raw[n]),struct.iter_unpack('<H',raw))):
                self.assertEqual(old&0xF3FF,new&0xF3FF);bridges+=old>>12==15
                if i in closed:self.assertEqual(new>>10&3,1)
                else:self.assertEqual(old,new)
        self.assertEqual(bridges,24)

    def test_three_connection_pairs_preserve_offsets_and_open_reciprocal_endpoints(self):
        staged,_,_=self.build();ids={h['id']:n for n,(_,h) in staged.items()};inverse={'up':'down','down':'up','left':'right','right':'left'}
        self.assertEqual(sum(len(h['connections']) for _,h in staged.values()),6)
        for n,(raw,h) in staged.items():
            w,height,_=a.MAPS[n];data=a.base.cells(raw,w,height)
            for c in h['connections']:
                target=ids[c['map']];tw,th,_=a.MAPS[target];dest=a.base.cells(staged[target][0],tw,th)
                self.assertEqual(len([v for v in staged[target][1]['connections'] if v['map']==h['id'] and v['direction']==inverse[c['direction']] and v['offset']==-c['offset']]),1)
                edges={'up':[(x,0) for x in range(w)],'down':[(x,height-1) for x in range(w)],'left':[(0,y) for y in range(height)],'right':[(w-1,y) for y in range(height)]};opened=0
                for x,y in edges[c['direction']]:
                    if data[y*w+x]>>10&3:continue
                    dx,dy=a.base.destination((x,y),c['direction'],c['offset'],tw,th)
                    self.assertTrue(0<=dx<tw and 0<=dy<th);self.assertEqual(dest[dy*tw+dx]>>10&3,0);opened+=1
                self.assertGreater(opened,0)

    def test_actual_snow_weather_restored_with_exact_source_header_hash(self):
        for n in a.MAPS:
            h=json.loads((HERE/'staged'/n/'map.json').read_text());d=self.r['source_weather_restored'][n]
            self.assertEqual((h['weather'],d['before'],d['after']),('WEATHER_SNOW','WEATHER_NONE','WEATHER_SNOW'))
            self.assertEqual(d['source_header_sha256'],self.r['donor_sha256']['data/maps/'+n+'/map.json'])

    def test_changed_weather_header_or_unexpected_weather_fail_before_target_write(self):
        for weather,bad in [('WEATHER_SNOW',True),('WEATHER_NONE',False)]:
            with self.subTest(weather=weather,bad=bad),tempfile.TemporaryDirectory() as temp:
                out=Path(temp);name=next(iter(a.MAPS));path='data/maps/'+name+'/map.json';raw=json.dumps(dict(weather=weather)).encode()
                r=dict(donor_sha256={path:'bad' if bad else a.base.sha(raw)});p=out/'staged'/name/'map.json';p.parent.mkdir(parents=True);p.write_text('{"weather":"WEATHER_NONE"}');before=p.read_bytes()
                with mock.patch.object(a.subprocess,'check_output',return_value=raw),self.assertRaises(ValueError):a.preserve_source_weather(Path('/unused'),out,r)
                self.assertEqual(p.read_bytes(),before)

    def test_every_used_map_border_attribute_is_present_and_art_stays_unverified(self):
        for n in a.MAPS:
            p=HERE/'staged'/n;d=json.loads((p/'attributes.json').read_text());used={v[0]&1023 for v in struct.iter_unpack('<H',(p/'map.bin').read_bytes()+(p/'border.bin').read_bytes())}
            self.assertEqual(used,{int(k) for k in d['used_source_attribute_words']});self.assertTrue(any(v<512 for v in used));self.assertTrue(any(v>=512 for v in used))
            self.assertEqual(d['source_tilesets'],['gTileset_General','gTileset_Snowpoint']);self.assertEqual(d['averon_art_compatibility'],'UNVERIFIED')

    def test_coronet_quarantined_without_inventing_lake_entrance_gameplay_or_saved_ids(self):
        staged,_,_=self.build();ids={h['id'] for _,h in staged.values()};self.assertNotIn('LakeAcuity',a.MAPS)
        for raw,h in staged.values():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['warp_events'] or h['object_events'] or h['coord_events'] or h['bg_events']);self.assertTrue(all(c['map'] in ids for c in h['connections']))
        source=self.headers['Route216']['warp_events'][0];self.assertEqual(source['dest_map'],'MAP_MT_CORONET_1F_NORTH_ROOM2')
        self.assertEqual(a.base.cells(staged['Route216'][0],96,40)[source['y']*96+source['x']]>>10&3,1)

    def test_wrong_connection_offset_and_impossible_source_warp_are_rejected(self):
        self.headers['Route217']['connections'][0]['offset']=3
        with self.assertRaisesRegex(ValueError,'nonreciprocal'):self.build()
        self.setUp();self.headers['Route216']['warp_events'][0]['x']=96
        with self.assertRaisesRegex(ValueError,'warp anchor'):self.build()

    def test_repeat_is_deterministic_and_does_not_mutate_input(self):
        before=copy.deepcopy((self.headers,self.layouts,self.raw));self.assertEqual(self.build(),self.build());self.assertEqual(before,(self.headers,self.layouts,self.raw))
if __name__=='__main__':unittest.main()
