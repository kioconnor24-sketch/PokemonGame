"""Native island doorway pair without changing water or reflective terrain."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/acuity-island-link'
s=importlib.util.spec_from_file_location('acuity_link_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class AcuityLinkTests(unittest.TestCase):
    def setUp(self):self.r=json.loads((HERE/'receipt.json').read_text())
    def test_lake_water_shore_every_map_cell_and_original_borders_unchanged(self):
        self.assertEqual((m.LAKE/'LakeAcuity/averon-map.bin').read_bytes(),(HERE/'staged/LakeAcuity/map.bin').read_bytes())
        self.assertEqual((m.LAKE/'LakeAcuity/averon-border.bin').read_bytes(),(HERE/'staged/LakeAcuity/border.bin').read_bytes())
        self.assertEqual((m.CAVE/'staged/border.bin').read_bytes(),(HERE/'staged/AcuityCavern/border.bin').read_bytes())
        old=(m.CAVE/'staged/map.bin').read_bytes();new=(HERE/'staged/AcuityCavern/map.bin').read_bytes()
        changed={(i%32,i//32) for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',old),struct.iter_unpack('<H',new))) if a!=b}
        self.assertEqual(changed,{(14,29)})
    def test_all182_reflective_cells_keep_exact_no_surf_metadata(self):
        before=json.loads((m.CAVE/'staged/attributes.json').read_text());after=json.loads((HERE/'staged/AcuityCavern/attributes.json').read_text())
        old=(m.CAVE/'staged/map.bin').read_bytes();new=(HERE/'staged/AcuityCavern/map.bin').read_bytes();count=0
        for (a,),(b,) in zip(struct.iter_unpack('<H',old),struct.iter_unpack('<H',new)):
            if before[str(a&1023)]&255==0x2b:self.assertEqual(a,b);self.assertEqual(before[str(a&1023)],after[str(b&1023)]);count+=1
        self.assertEqual(count,182)
    def test_reciprocal_source_door_events_actual_triggers_and_local_ground_paths(self):
        hs={};dims={'LakeAcuity':48,'AcuityCavern':32};behaviors={'LakeAcuity':0x60,'AcuityCavern':0x61}
        for n,w in dims.items():
            h=json.loads((HERE/'staged'/n/'map.json').read_text());hs[h['id']]=h
            self.assertEqual(len(h['warp_events']),1);e=h['warp_events'][0]
            raw=(HERE/'staged'/n/'map.bin').read_bytes();attrs=json.loads((HERE/'staged'/n/'attributes.json').read_text());v=struct.unpack_from('<H',raw,2*(e['y']*w+e['x']))[0]
            self.assertFalse(v&0xc00);self.assertEqual(v>>12,e['elevation']);self.assertEqual(attrs[str(v&1023)]&255,behaviors[n])
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['connections'])
            for k in ('object_events','coord_events','bg_events'):self.assertFalse(h[k])
        for identity,h in hs.items():
            e=h['warp_events'][0];back=hs[e['dest_map']]['warp_events'][0];self.assertEqual(back['dest_map'],identity);self.assertEqual(e['dest_warp_id'],'0')
        self.assertEqual(self.r['local_paths']['LakeAcuity'],[[23,31],[23,30],[23,29]])
    def test_native_prefix_and_actual_render_replay(self):
        for n,folder in [('LakeAcuity',m.LAKE/'outdoor-family'),('AcuityCavern',m.CAVE/'cave-family')]:
            for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
                old=(folder/p).read_bytes();self.assertEqual((HERE/'families'/n/p).read_bytes()[:len(old)],old)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'new';r=m.build(ENGINE,out);self.assertEqual(r,self.r)
            for p,h in r['output_sha256'].items():self.assertEqual(m.g.base.sha((out/p).read_bytes()),h);self.assertEqual((out/p).read_bytes(),(HERE/p).read_bytes())
    def test_dirty_input_and_engine_output_rejected_before_write(self):
        original=Path.read_bytes;target=m.LAKE/'LakeAcuity/averon-map.bin'
        def dirty(p):
            v=original(p);return bytes([v[0]^1])+v[1:] if p==target else v
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad')
if __name__=='__main__':unittest.main()
