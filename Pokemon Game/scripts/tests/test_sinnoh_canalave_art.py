"""Existing-Averon Canalave art: complete physics, graphics and negative guards."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/canalave-west'
spec=importlib.util.spec_from_file_location('canalave_outdoor_test',HERE/'adapt_outdoor_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'


class CanalaveArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads((HERE/'outdoor-art-receipt.json').read_text())
        cls.banks=[(HERE/'outdoor-family'/(b+'-metatiles.bin')).read_bytes() for b in ('primary','secondary')]
        cls.attrs=[(HERE/'outdoor-family'/(b+'-attributes.bin')).read_bytes() for b in ('primary','secondary')]
        cls.stock=[(ENGINE/('data/tilesets/'+p+'/metatiles.bin')).read_bytes() for p in ('primary/general','secondary/rustboro')]
        cls.city=struct.unpack('<2400H',(ENGINE/'data/layouts/RustboroCity/map.bin').read_bytes())

    def test_every4488_map_border_cell_keeps_collision_elevation_full_behavior(self):
        count=0
        for name in a.MAPS:
            raw,border,_,attrs=a.source(name);folder=HERE/'staged'/name
            new=(folder/'averon-map.bin').read_bytes()+(folder/'averon-border.bin').read_bytes()
            self.assertEqual(len(new),len(raw+border))
            for (old,),(v,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',new)):
                self.assertEqual(old&0xFC00,v&0xFC00);bank,mid=divmod(v&1023,512)
                self.assertEqual(a.pack.attribute(self.attrs[bank],mid),attrs[str(old&1023)]);count+=1
        self.assertEqual(count,4488);self.assertEqual(count,self.receipt['verified_physics_behavior_cells'])

    def test_general_unchanged_isolated_bank_capacity_and_assets_are_exact(self):
        self.assertEqual(self.banks[0],self.stock[0]);self.assertEqual(self.attrs[0],(ENGINE/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes())
        self.assertLessEqual(len(self.banks[1]),8192);self.assertEqual(len(self.banks[1]),len(self.attrs[1])*8)
        self.assertEqual(len(self.banks[1])//16,self.receipt['secondary_records']);self.assertEqual(self.receipt['remaining_secondary_slots'],512-len(self.banks[1])//16)
        base=a.pack.accepted.base;root=HERE.parents[4]
        for p,h in self.receipt['existing_averon_sha256'].items():self.assertEqual(base.sha(base.verified_file(root,ENGINE.relative_to(root)/p,'HEAD')),h)
        self.assertEqual(self.receipt['status'],'EXISTING_AVERON_CANALAVE_ART_NOT_RUNTIME_ACCEPTANCE')

    def test_actual_two_previews_resolve_every_graphic_tile_and_palette(self):
        dual=a.pack.accepted.dual;base=a.pack.accepted.base
        paths=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
        images=[dual.indexed((ENGINE/(p+'tiles.png')).read_bytes()) for p in paths]
        for name,(w,h) in a.MAPS.items():
            f=HERE/'staged'/name;raw=(f/'averon-map.bin').read_bytes();border=(f/'averon-border.bin').read_bytes()
            deps=dual.closure(raw+border,self.banks,images);self.assertEqual(deps,self.receipt['dependencies'][name])
            palettes={i:base.palette((ENGINE/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in deps['palettes']}
            actual=dual.render(raw,self.banks,images,palettes,w,h)
            with dual.Image.open(f/'averon.png') as im:self.assertEqual(actual.tobytes(),im.convert('RGB').tobytes())

    def test_original_geometry_headers_source_hashes_and_water_not_overwritten(self):
        receipt=json.loads((HERE/'source-receipt.json').read_text());water=0
        for name in a.MAPS:
            f=HERE/'staged'/name;raw,border,h,attrs=a.source(name)
            self.assertEqual(a.pack.accepted.base.sha(raw),receipt['maps'][name]['staged_sha256'])
            self.assertEqual(a.pack.accepted.base.sha(border),receipt['maps'][name]['border_sha256'])
            for p,sha in self.receipt['source_sha256'][name].items():self.assertEqual(a.pack.accepted.base.sha((f/p).read_bytes()),sha)
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])
            self.assertTrue(any(v&0xC00 for (v,) in struct.iter_unpack('<H',raw)))
            water+=sum(attrs[str(v&1023)]&0x1FF==0x15 for (v,) in struct.iter_unpack('<H',raw))
        self.assertGreater(water,1000)
        self.assertEqual(self.receipt['elevation15_preserved'],{'Route218':0,'CanalaveCity':0})

    def test_bridge_pixels_use_actual_wood_instead_of_paving_or_house_tiles(self):
        plank=a.pack.words(self.stock[1],16);wood=tuple(plank[i] for i in (1,1,3,3,5,5,7,7));count=0
        for name in a.MAPS:
            f=HERE/'staged'/name
            old=struct.unpack('<%dH'%((f/'map.bin').stat().st_size//2),(f/'map.bin').read_bytes())
            new=struct.unpack('<%dH'%len(old),(f/'averon-map.bin').read_bytes())
            for x,y in zip(old,new):
                if x&1023 in a.BRIDGES[name]:
                    b,i=divmod(y&1023,512);self.assertEqual(a.pack.words(self.banks[b],i),wood);count+=1
        self.assertGreater(count,50)

    def test_source_fields_cannot_expand_art_without_reviewed_mapping(self):
        raw,border,header,attrs=a.source('Route218')
        for kind in ('dimension','missing-attribute','unknown-secondary','warp-anchor'):
            r=raw;h=copy.deepcopy(header);at=dict(attrs)
            if kind=='dimension':r=r[:-2]
            elif kind=='missing-attribute':at.pop(next(iter(at)))
            elif kind=='unknown-secondary':
                cells=list(struct.unpack('<%dH'%(len(raw)//2),raw));at['1023']=at[str(cells[0]&1023)];cells[0]=(cells[0]&0xFC00)|1023;r=struct.pack('<%dH'%len(cells),*cells)
            else:h['warp_events'][0]['x']=64
            with self.subTest(kind=kind),self.assertRaises(ValueError):a.desired_art('Route218',r,border,h,at,self.stock,self.city)

    def test_facade_outside_source_fails_and_valid_inputs_not_mutated(self):
        raw,border,header,attrs=a.source('CanalaveCity');before=copy.deepcopy((header,attrs));a.desired_art('CanalaveCity',raw,border,header,attrs,self.stock,self.city);self.assertEqual(before,(header,attrs))
        bad=dict(a.FACADES);bad['CanalaveCity']=[((37,63,5,5),a.HOUSE)]
        with mock.patch.object(a.templates,'FACADES',bad),self.assertRaises(ValueError):a.desired_art('CanalaveCity',raw,border,header,attrs,self.stock,self.city)

    def test_builder_refuses_existing_output_and_engine_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'new off-engine'):a.build(ENGINE,Path(directory))
            with self.assertRaisesRegex(ValueError,'new off-engine'):a.build(ENGINE,ENGINE/'forbidden-canalave-test-output')


if __name__=='__main__':unittest.main()
