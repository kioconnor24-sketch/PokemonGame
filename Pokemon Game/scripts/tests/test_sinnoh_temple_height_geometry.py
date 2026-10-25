"""Source BDHC negative cases with synthetic data; never require private DS files."""
import importlib.util
from pathlib import Path
import struct
import json
import copy
import unittest
from fractions import Fraction
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[3]/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/snowpoint-temple-height'
s=importlib.util.spec_from_file_location('temple_bdhc_test',HERE/'parse_bdhc.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def fixture(points=((-1048576,-1048576),(1048576,1048576)),normals=((0,4096,0),),constants=(-65536,),plates=((0,1,0,0),),strips=((1048576,1,0),),access=(0,)):
    arrays=(points,normals,[(i,) for i in constants],plates,strips,[(i,) for i in access])
    fmts=('<ii','<iii','<i','<4H','<iHH','<H')
    return b'BDHC'+struct.pack('<6H',*[len(v) for v in arrays])+b''.join(struct.pack(fmt,*row) for rows,fmt in zip(arrays,fmts) for row in rows)

class HeightGeometryTests(unittest.TestCase):
    def test_flat_signed_fixed_plane_and_center_origin(self):
        data=m.decode(fixture())
        self.assertEqual(m.tile_candidates(data,0,0),[(0,Fraction(16*m.FX))])
        self.assertEqual(m.tile_candidates(data,31,31),[(0,Fraction(16*m.FX))])
        for x,y in ((-1,0),(0,32)):
            with self.assertRaisesRegex(ValueError,'outside'):m.tile_candidates(data,x,y)

    def test_inclusive_bounds_and_reversed_corner_order(self):
        data=m.decode(fixture(points=((10,20),(-10,-20))))
        self.assertTrue(m.candidates(data,-10,-20));self.assertTrue(m.candidates(data,10,20))
        self.assertEqual(m.candidates(data,11,20),[])
        self.assertEqual(m.candidates(data,10,21),[])

    def test_sloped_and_multiple_planes_remain_exact_not_nearest_guessed(self):
        data=m.decode(fixture(normals=((-2896,2896,0),(0,4096,0)),constants=(-139023,-65536),plates=((0,1,0,0),(0,1,1,1)),strips=((1048576,2,0),),access=(0,1)))
        values=m.candidates(data,12345,0)
        self.assertEqual(len(values),2)
        self.assertEqual(values[0][1],Fraction(2896*12345+139023*4096,2896))
        self.assertEqual(values[1][1],16*4096)

    def test_scanline_source_boundary_and_outside_last_strip(self):
        data=m.decode(fixture(plates=((0,1,0,0),(0,1,0,0)),strips=((-10,1,0),(10,1,1)),access=(0,1)))
        self.assertEqual(m.candidates(data,0,-11)[0][0],0)
        self.assertEqual(m.candidates(data,0,-10)[0][0],1)
        self.assertEqual(m.candidates(data,0,100)[0][0],1)

    def test_bad_magic_truncation_trailing_and_huge_counts_fail_closed(self):
        raw=fixture()
        for broken in (b'',raw[:15],b'NOPE'+raw[4:],raw[:-1],raw+b'x',raw[:4]+struct.pack('<6H',65535,1,1,1,1,1)+raw[16:]):
            with self.assertRaises(ValueError):m.decode(broken)

    def test_all_plate_reference_types_are_bounds_checked(self):
        for plate in ((2,1,0,0),(0,2,0,0),(0,1,1,0),(0,1,0,1)):
            with self.assertRaisesRegex(ValueError,'plate index'):m.decode(fixture(plates=(plate,)))

    def test_invalid_access_slice_target_and_duplicate_refused(self):
        for raw in (fixture(strips=((0,2,0),)),fixture(access=(2,)),fixture(strips=((0,2,0),),access=(0,0))):
            with self.assertRaisesRegex(ValueError,'access'):m.decode(raw)

    def test_empty_tables_unsorted_scanlines_and_vertical_normal_refused(self):
        for raw in (fixture(points=()),fixture(strips=((10,1,0),(0,1,0))),fixture(strips=((0,1,0),(0,1,0))),fixture(normals=((1,0,0),))):
            with self.assertRaisesRegex(ValueError,'empty|scanline|vertical'):m.decode(raw)

    def test_more_than_ten_overlaps_not_silently_truncated(self):
        data=m.decode(fixture(plates=((0,1,0,0),)*11,strips=((1048576,11,0),),access=tuple(range(11))))
        with self.assertRaisesRegex(ValueError,'ten candidate'):m.candidates(data,0,0)


class ProvisionalGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('temple_height_build_test',HERE/'build_geometry.py')
        cls.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.m)
        cls.audit=json.loads((HERE/'geometry-audit.json').read_text())
        cls.reference=json.loads((HERE.parent/'snowpoint-temple-core/portal-reference.json').read_text())
        cls.maps=cls.m.construct(cls.audit,cls.reference)

    def test_committed_native_geometry_replays_all6144_cells_and338_ice(self):
        total=0
        for name,(raw,border,header) in self.maps.items():
            p=HERE/'staged'/name
            self.assertEqual(raw,(p/'map.bin').read_bytes());self.assertEqual(border,(p/'border.bin').read_bytes())
            self.assertEqual(header,json.loads((p/'map.json').read_text()))
            self.assertEqual(len(raw),2048)
            cells=struct.unpack('<1024H',raw);total+=sum(v&1023==self.m.ICE for v in cells)
            attrs=json.loads((p/'attributes.json').read_text())['used_source_attribute_words']
            self.assertEqual(attrs[str(self.m.ICE)]&511,32) if str(self.m.ICE) in attrs else None
        self.assertEqual(total,338)

    def test_unsupported_permission_clear_cells_never_become_floor(self):
        unsupported=0;walkable=0
        for floor,info in self.audit['floors'].items():
            raw=self.maps[self.m.core.NAMES[floor]][0];cells=struct.unpack('<1024H',raw)
            for x,y in info['permission_clear_without_surface']:
                self.assertTrue(cells[y*32+x]&0xc00);unsupported+=1
            self.assertTrue(all(p['height_candidates']==['16'] for p in info['walkable_center_samples']))
            walkable+=len(info['walkable_center_samples'])
        self.assertEqual(unsupported,4204);self.assertEqual(walkable,887)

    def test_actual_corners_have_flat_support_and_ramp_edge_ambiguity_is_disclosed(self):
        self.assertEqual(sum(v['sampled_walkable_corners'] for v in self.audit['floors'].values()),3548)
        self.assertEqual(sum(len(v['nonflat_edge_candidates']) for v in self.audit['floors'].values()),50)
        for v in self.audit['floors'].values():
            self.assertFalse(v['corners_without_flat16'])
            self.assertTrue(all('16' in p['height_candidates'] for p in v['nonflat_edge_candidates']))
        bad=copy.deepcopy(self.audit);bad['floors']['1f']['corners_without_flat16']=[[14,3,-8,-8]]
        with self.assertRaisesRegex(ValueError,'footprint'):self.m.construct(bad,self.reference)

    def test_stairs_reciprocal_and_reachable_with_host_ice_stops_city_closed(self):
        byid={v[2]['id']:v for v in self.maps.values()};events=0
        for raw,_,h in self.maps.values():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            for key in ('object_events','coord_events','bg_events','connections'):self.assertFalse(h[key])
            for i,p in enumerate(h['warp_events']):
                seen=self.m.stop_graph(raw,(p['x'],p['y']))
                self.assertTrue({(q['x'],q['y']) for q in h['warp_events']}<=seen)
                q=byid[p['dest_map']][2]['warp_events'][int(p['dest_warp_id'])]
                self.assertEqual((q['dest_map'],int(q['dest_warp_id'])),(h['id'],i));events+=1
        self.assertEqual(events,10)
        raw=self.maps[self.m.core.NAMES['1f']][0]
        self.assertTrue(struct.unpack_from('<H',raw,2*(13*32+8))[0]&0xc00)

    def test_nonflat_duplicate_bad_behavior_bad_ice_and_revision_rejected(self):
        for mutate,error in ((lambda a:a['floors']['1f']['walkable_center_samples'][0].update(height_candidates=['17']),'nonflat'),
                             (lambda a:a['floors']['1f']['walkable_center_samples'].append(a['floors']['1f']['walkable_center_samples'][0]),'duplicate'),
                             (lambda a:a['floors']['1f']['walkable_center_samples'][0].update(source_behavior=255),'behavior'),
                             (lambda a:a['floors']['1f']['ice'][0].update(collision_bit=True),'ice'),
                             (lambda a:a.update(revision='different'),'revision')):
            data=copy.deepcopy(self.audit);mutate(data)
            with self.assertRaisesRegex(ValueError,error):self.m.construct(data,self.reference)

    def test_host_ice_model_cannot_turn_in_middle_of_sliding(self):
        cells=[self.m.WALL|0xc00]*1024
        for x,y,tile in ((2,2,self.m.FLOOR),(3,2,self.m.ICE),(4,2,self.m.FLOOR),(3,3,self.m.FLOOR)):
            cells[y*32+x]=tile|0x3000
        seen=self.m.stop_graph(struct.pack('<1024H',*cells),(2,2))
        self.assertIn((4,2),seen);self.assertNotIn((3,2),seen);self.assertNotIn((3,3),seen)


class HeightRuntimePreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('temple_height_prepare_test',HERE/'prepare_runtime.py')
        cls.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.m)
        cls.root=HERE.parents[4];cls.files,cls.receipt=cls.m.assemble(cls.root)

    def test_separate29_file_scene_keeps19_slots_native_assets_and_temporary_codes(self):
        self.assertEqual(len(self.files),29)
        groups=json.loads(self.files['data/maps/map_groups.json'])['gMapGroup_Sinnoh']
        self.assertEqual(groups[:19],self.receipt['existing_map_names_preserved'])
        self.assertEqual(groups[19:],list(self.m.core.MAPS))
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        for name in self.m.core.MAPS:
            self.assertEqual(len(self.files[f'data/layouts/{name}/map.bin']),2048)
            layout=next(v for v in layouts if v['name']==name+'_Layout')
            self.assertEqual((layout['width'],layout['height']),(32,32))
            self.assertEqual(layout['primary_tileset'],'gTileset_General');self.assertEqual(layout['secondary_tileset'],'gTileset_Cave')
            h=json.loads(self.files[f'data/maps/{name}/map.json']);self.assertEqual(h['region_map_section'],'MAPSEC_ROUTE_201')
        self.assertNotIn('test/averon_temple_core_runtime.c',self.files)
        self.assertFalse(any('region_map_sections' in p or 'tileset' in p or p.endswith(('.png','.sav','.gba')) for p in self.files))

    def test_tampered_source_and_production_install_refused(self):
        original=self.m.sha;target=(HERE/'geometry-audit.json').read_bytes()
        with patch.object(self.m,'sha',side_effect=lambda data:'bad' if data==target else original(data)):
            with self.assertRaisesRegex(ValueError,'height source input'):self.m.assemble(self.root)
        with self.assertRaisesRegex(ValueError,'marked height'):self.m.install(self.root)

if __name__=='__main__':unittest.main()
