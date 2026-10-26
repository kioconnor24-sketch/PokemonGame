"""Source split, native ocean and bounded reciprocal Seabreak construction."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/seabreak-flower'
s=importlib.util.spec_from_file_location('seabreak_tests',HERE/'build.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class SeabreakTests(unittest.TestCase):
    def test_capacity_and_authentic_seams(self):
        r=json.loads((HERE/'receipt.json').read_text())
        self.assertEqual(r['unsplit_padded_cells'],12690)
        self.assertGreater(r['unsplit_padded_cells'],r['buffer_capacity'])
        self.assertEqual(r['padded_cells'],dict(FlowerParadise=2162,SeabreakNorth=6674,SeabreakSouth=6674))
        for e in r['seams']:self.assertEqual(e['ground_lanes'],[14,15,16])
        headers={n:json.loads((HERE/'staged'/n/'map.json').read_text()) for n in m.SLICES}
        for n,h in headers.items():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            for key in ('object_events','coord_events','bg_events','warp_events'):self.assertFalse(h[key])
            for e in h['connections']:
                other=next(x for x in headers.values() if x['id']==e['map'])
                reverse='down' if e['direction']=='up' else 'up'
                self.assertIn(dict(map=h['id'],direction=reverse,offset=0),other['connections'])
        self.assertNotIn('down',[e['direction'] for e in headers['SeabreakSouth']['connections']])
    def test_ground_and_sea_semantics_and_closed_south(self):
        geometry=json.loads((HERE/'geometry.json').read_text())
        for n,g in geometry.items():
            w,h=m.existing.DIMS[n];raw=(HERE/'staged'/n/'map.bin').read_bytes()
            cells=struct.unpack('<%dH'%(w*h),raw)
            attrs=json.loads((HERE/'staged'/n/'attributes.json').read_text())
            points={tuple(p['tile']):p for p in g['surfaces']}
            for i,v in enumerate(cells):
                p=points.get((i%w,i//w));behavior=attrs[str(v&1023)]&255
                if p and p['permission']==0x15:
                    self.assertEqual(behavior,0x15);self.assertEqual(v>>12,1)
                elif not v&0xc00:
                    self.assertIsNotNone(p);self.assertEqual(p['permission'],0);self.assertEqual(behavior,0)
            if n.startswith('Seabreak'):
                last=h-1 if n=='SeabreakNorth' else h-2
                for y in range(last+1):
                    for x in (14,15,16):
                        self.assertFalse(cells[y*w+x]&0xc00)
                        self.assertEqual(attrs[str(cells[y*w+x]&1023)]&255,0)
            if n=='SeabreakSouth':self.assertTrue(all(v&0xc00 for v in cells[-w:]))
    def test_defaults_closed_and_reject_invalid_geometry(self):
        spec=importlib.util.spec_from_file_location('seabreak_default',HERE.parent/'frontier-campus/build_source.py')
        default=importlib.util.module_from_spec(spec);spec.loader.exec_module(default)
        self.assertEqual(default.OPEN_BOUNDARIES,{})
        g=json.loads((HERE/'geometry.json').read_text())
        g['FlowerParadise']['surfaces'].append(g['FlowerParadise']['surfaces'][0])
        with self.assertRaisesRegex(ValueError,'duplicate|invalid'):m.construct(g)
    def test_full_replay_and_unsafe_destination(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'fresh';r=m.build(ENGINE,out)
            self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
            for p,h in r['output_sha256'].items():
                self.assertEqual(m.existing.base.sha((out/p).read_bytes()),h)
                self.assertEqual((out/p).read_bytes(),(HERE/p).read_bytes())
            with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad')
if __name__=='__main__':unittest.main()
