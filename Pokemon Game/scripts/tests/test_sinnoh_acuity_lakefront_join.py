"""Native two-column Acuity entry, with water and existing identities immutable."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/acuity-lakefront-join'
s=importlib.util.spec_from_file_location('lakefront_join_test',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class LakefrontJoinTests(unittest.TestCase):
    def setUp(self):self.r=json.loads((HERE/'receipt.json').read_text())
    def test_exact_four_semantic_cells_all_other_words_and_borders_unchanged(self):
        for name,source,w,expected in [('AcuityLakefront',HERE/'lakefront-source',64,{(20,39),(21,39)}),('LakeAcuity',m.ISLAND/'staged/LakeAcuity',48,{(6,48),(7,48)})]:
            before=(source/'map.bin').read_bytes();after=(HERE/'staged'/name/'map.bin').read_bytes()
            changed={(i%w,i//w) for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after))) if a!=b}
            self.assertEqual(changed,expected)
            self.assertEqual([a&0xfc00 for (a,) in struct.iter_unpack('<H',before)],[a&0xfc00 for (a,) in struct.iter_unpack('<H',after)])
            self.assertEqual((source/'border.bin').read_bytes(),(HERE/'staged'/name/'border.bin').read_bytes())
    def test_real_water_cannot_be_used_as_ground_and_all_water_words_preserved(self):
        for name,source,family in [('AcuityLakefront',HERE/'lakefront-source',m.CITY),('LakeAcuity',m.ISLAND/'staged/LakeAcuity',m.ISLAND/'families/LakeAcuity')]:
            pa=(family/'primary-attributes.bin').read_bytes();sa=(family/'secondary-attributes.bin').read_bytes()
            before=(source/'map.bin').read_bytes();after=(HERE/'staged'/name/'map.bin').read_bytes();attrs=json.loads((HERE/'staged'/name/'attributes.json').read_text());count=0
            for (a,),(b,) in zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after)):
                word=m.g.pack.attribute((pa,sa)[(a&1023)//512],a%512)
                if word&255==0x10:self.assertEqual(a,b);self.assertEqual(attrs[str(b&1023)],word);count+=1
            self.assertEqual(count,self.r['preserved_water_cells'][name]);self.assertGreater(count,0)
        raw=(HERE/'staged/LakeAcuity/map.bin').read_bytes();attrs=json.loads((HERE/'staged/LakeAcuity/attributes.json').read_text())
        v=struct.unpack_from('<H',raw,2*(32*48+23))[0];self.assertEqual(attrs[str(v&1023)]&255,0x10)
        foot={mid:(v&~255 if v&255==0x21 else v) for mid,v in attrs.items()}
        self.assertFalse(m.g.a.static_path(raw,48,52,[23,32],[23,32],foot))
        # Real water semantics still reject ground traversal even if a fixture
        # gives the tile ordinary elevation3, isolating behavior from height.
        fixture=bytearray(raw);struct.pack_into('<H',fixture,2*(32*48+23),(v&1023)|0x3000)
        self.assertFalse(m.g.a.static_path(fixture,48,52,[23,32],[23,32],foot))
    def test_reciprocal_indices_trigger_heights_and_original_island_event_preserved(self):
        headers={};dims={'AcuityLakefront':64,'LakeAcuity':48}
        for n,w in dims.items():
            h=json.loads((HERE/'staged'/n/'map.json').read_text());headers[h['id']]=h
            attrs=json.loads((HERE/'staged'/n/'attributes.json').read_text());raw=(HERE/'staged'/n/'map.bin').read_bytes()
            for e in h['warp_events'][0 if n=='AcuityLakefront' else 1:]:
                v=struct.unpack_from('<H',raw,2*(e['y']*w+e['x']))[0]
                self.assertFalse(v&0xc00);self.assertEqual(v>>12,e['elevation']);self.assertEqual(attrs[str(v&1023)],0x1061)
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
        for identity,h in headers.items():
            for i,e in enumerate(h['warp_events']):
                if e['dest_map'] not in headers:continue
                back=headers[e['dest_map']]['warp_events'][int(e['dest_warp_id'])];self.assertEqual((back['dest_map'],int(back['dest_warp_id'])),(identity,i))
        old=json.loads((m.ISLAND/'staged/LakeAcuity/map.json').read_text())
        self.assertEqual(headers['MAP_LAKE_ACUITY']['warp_events'][:1],old['warp_events'])
        self.assertEqual(json.loads((HERE/'lakefront-source/map.json').read_text())['connections'],headers['MAP_ACUITY_LAKEFRONT']['connections'])
    def test_native_prefixes_and_full_render_replay(self):
        for n,folder in [('AcuityLakefront',m.CITY),('LakeAcuity',m.ISLAND/'families/LakeAcuity')]:
            for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
                old=(folder/p).read_bytes();self.assertEqual((HERE/'families'/n/p).read_bytes()[:len(old)],old)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'new';r=m.build(ENGINE,out);self.assertEqual(r,self.r)
            for p,h in r['output_sha256'].items():self.assertEqual(m.g.base.sha((out/p).read_bytes()),h);self.assertEqual((out/p).read_bytes(),(HERE/p).read_bytes())
    def test_dirty_source_and_engine_output_rejected_before_write(self):
        original=Path.read_bytes;target=HERE/'lakefront-source/map.bin'
        def dirty(p):
            v=original(p);return bytes([v[0]^1])+v[1:] if p==target else v
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad')
if __name__=='__main__':unittest.main()
