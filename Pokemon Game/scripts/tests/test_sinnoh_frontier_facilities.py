"""Neutral physical templates, isolated portals and immutable source preservation."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/frontier-facilities'
s=importlib.util.spec_from_file_location('facility_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class FacilityTests(unittest.TestCase):
    def setUp(self):self.receipt=json.loads((HERE/'receipt.json').read_text())
    def test_ten_real_native_maps_preserved_except_one_explicit_closure(self):
        layouts={v['id']:v for v in json.loads((ENGINE/'data/layouts/layouts.json').read_text())['layouts']}
        closures={(v['map'],*v['cell']) for v in self.receipt['sealed_corridors']}
        self.assertEqual(len(closures),1);self.assertEqual(len(m.TEMPLATES),10)
        for name,source in m.TEMPLATES.items():
            h=json.loads((ENGINE/'data/maps'/source/'map.json').read_text());l=layouts[h['layout']];w=l['width']
            raw=(ENGINE/l['blockdata_filepath']).read_bytes();new=(HERE/'staged'/name/'map.bin').read_bytes()
            self.assertEqual(len(raw),len(new));changed=set()
            for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',new))):
                if a!=b:self.assertEqual(b,a|0xc00);changed.add((name,i%w,i//w))
            self.assertEqual(changed,{c for c in closures if c[0]==name})
            header=json.loads((HERE/'staged'/name/'map.json').read_text());layout=json.loads((HERE/'staged'/name/'layout.json').read_text())
            self.assertEqual(header['layout'],layout['id']);self.assertEqual(header['region_map_section'],'MAPSEC_PENDING_OWNER')
            for key in ('object_events','coord_events','bg_events','connections'):self.assertFalse(header[key])
    def test_every_active_warp_resolves_and_tower_doorstep_is_supported(self):
        headers={};raws={}
        for name in (*m.TEMPLATES,'Campus'):
            h=json.loads((HERE/'staged'/name/'map.json').read_text());headers[h['id']]=(name,h);raws[name]=(HERE/'staged'/name/'map.bin').read_bytes()
        for identity,(name,h) in headers.items():
            w=96 if name=='Campus' else self.receipt['maps'][name][0]
            for i,event in enumerate(h['warp_events']):
                cell=struct.unpack_from('<H',raws[name],2*(event['y']*w+event['x']))[0]
                target_name,target=headers[event['dest_map']];back=target['warp_events'][int(event['dest_warp_id'])]
                if cell&0xc00:
                    self.assertIn((name,i),{(v['map'],v.get('index',v.get('source_index'))) for v in self.receipt['sealed_corridors']})
                else:self.assertEqual(back['dest_map'],identity)
        tower=headers['MAP_SINNOH_FRONTIER_TOWER1'][1]
        self.assertEqual([v['dest_map'] for v in tower['warp_events'][:2]],['MAP_SINNOH_FRONTIER_CAMPUS']*2)
        self.assertEqual(m.PORTS['Tower1'],(48,18))
        campus=raws['Campus'];self.assertTrue(struct.unpack_from('<H',campus,2*(17*96+48))[0]&0xc00)
    def test_exact_five_campus_changes_source_heights_and_ladder_metadata(self):
        old=(m.BASE/'civic-candidate/map.bin').read_bytes();new=(HERE/'staged/Campus/map.bin').read_bytes()
        changed={(i%96,i//96) for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',old),struct.iter_unpack('<H',new))) if a!=b}
        self.assertEqual(changed,set(m.PORTS.values()))
        pa=(HERE/'campus-family/primary-attributes.bin').read_bytes();sa=(HERE/'campus-family/secondary-attributes.bin').read_bytes()
        h=json.loads((HERE/'staged/Campus/map.json').read_text())
        for e in h['warp_events']:
            v=struct.unpack_from('<H',new,2*(e['y']*96+e['x']))[0]
            self.assertFalse(v&0xc00);self.assertEqual(v>>12,e['elevation'])
            self.assertEqual(m.m.packer.attribute((pa,sa)[(v&1023)//512],v%512),0x1061)
        for n in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
            parent=(m.BASE/'civic-candidate'/n).read_bytes()
            self.assertEqual((HERE/'campus-family'/n).read_bytes()[:len(parent)],parent)
    def test_full_deterministic_native_render_replay(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'fresh';receipt=m.build(ENGINE,out);self.assertEqual(receipt,self.receipt)
            for path,h in receipt['output_sha256'].items():
                self.assertEqual(m.m.base.sha((out/path).read_bytes()),h);self.assertEqual((out/path).read_bytes(),(HERE/path).read_bytes())
    def test_dirty_native_source_and_engine_output_fail_before_write(self):
        original=Path.read_bytes
        def dirty(path):
            raw=original(path);return raw+b' ' if path==ENGINE/'data/layouts/layouts.json' else raw
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad')
if __name__=='__main__':unittest.main()
