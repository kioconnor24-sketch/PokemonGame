"""Coast art: source physics, elevated planes, dependency closure and fail closed."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/sunyshore-coast'
spec=importlib.util.spec_from_file_location('sunyshore_art_test',HERE/'adapt_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'

class CoastArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads((HERE/'outdoor-art-receipt.json').read_text())
        cls.banks=[(HERE/'outdoor-family'/(n+'-metatiles.bin')).read_bytes() for n in ('primary','secondary')]
        cls.attrs=[(HERE/'outdoor-family'/(n+'-attributes.bin')).read_bytes() for n in ('primary','secondary')]
        cls.stock=[(ENGINE/('data/tilesets/'+p+'/metatiles.bin')).read_bytes() for p in ('primary/general','secondary/rustboro')]
        cls.city=struct.unpack('<2400H',(ENGINE/'data/layouts/RustboroCity/map.bin').read_bytes())

    def test_all13933_cells_keep_physics_and_complete_attributes(self):
        count=0;heights={}
        for n in a.MAPS:
            raw,border,_,attrs=a.source(n);f=HERE/'staged'/n
            new=(f/'averon-map.bin').read_bytes()+(f/'averon-border.bin').read_bytes()
            self.assertEqual(len(new),len(raw+border))
            for (old,),(v,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',new)):
                self.assertEqual(old&0xFC00,v&0xFC00);b,i=divmod(v&1023,512)
                self.assertEqual(a.pack.attribute(self.attrs[b],i),attrs[str(old&1023)]);count+=1
            heights[n]=sum(v[0]>>12==15 for v in struct.iter_unpack('<H',raw))
        self.assertEqual(count,13933);self.assertEqual(count,self.receipt['verified_physics_behavior_cells'])
        self.assertEqual(heights,dict(SunyshoreCity=68,Route222=0,Route223=0,PokmonLeague=0))
        self.assertEqual(heights,self.receipt['elevation15_preserved'])

    def test_native_general_and_exact_permitted_asset_hashes(self):
        self.assertEqual(self.banks[0],self.stock[0])
        self.assertEqual(self.attrs[0],(ENGINE/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes())
        base=a.pack.accepted.base;root=HERE.parents[4]
        for p,h in self.receipt['existing_averon_sha256'].items():
            self.assertEqual(base.sha(base.verified_file(root,ENGINE.relative_to(root)/p,'HEAD')),h)
        self.assertEqual(self.receipt['status'],'EXISTING_AVERON_SUNYSHORE_ART_NOT_RUNTIME_ACCEPTANCE')
        self.assertEqual(self.receipt['art_roles_sha256'],base.sha((HERE/'art-map-roles.json').read_bytes()))

    def test_actual_four_previews_resolve_all_tiles_palettes_and_capacity(self):
        dual=a.pack.accepted.dual;base=a.pack.accepted.base
        paths=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
        images=[dual.indexed((ENGINE/(p+'tiles.png')).read_bytes()) for p in paths]
        self.assertLessEqual(len(self.banks[1]),8192);self.assertEqual(len(self.banks[1]),len(self.attrs[1])*8)
        self.assertEqual(self.receipt['secondary_records'],len(self.banks[1])//16)
        self.assertEqual(self.receipt['remaining_secondary_slots'],512-len(self.banks[1])//16)
        for n,(w,h) in a.MAPS.items():
            f=HERE/'staged'/n;raw=(f/'averon-map.bin').read_bytes();border=(f/'averon-border.bin').read_bytes()
            deps=dual.closure(raw+border,self.banks,images);self.assertEqual(deps,self.receipt['dependencies'][n])
            palettes={i:base.palette((ENGINE/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in deps['palettes']}
            actual=dual.render(raw,self.banks,images,palettes,w,h)
            with dual.Image.open(f/'averon.png') as im:self.assertEqual(actual.tobytes(),im.convert('RGB').tobytes())

    def test_walkways_keep_real_wood_art_and_elevated_cells_not_facades(self):
        plank=a.pack.words(self.stock[1],16);wood=tuple(plank[i] for i in (1,1,3,3,5,5,7,7));elevated=0;walks=0
        f=HERE/'staged/SunyshoreCity';raw=(f/'map.bin').read_bytes();new=(f/'averon-map.bin').read_bytes()
        for (old,),(v,) in zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',new)):
            if old&1023 in a.BRIDGES['SunyshoreCity']:
                b,i=divmod(v&1023,512);self.assertEqual(a.pack.words(self.banks[b],i),wood);walks+=1
                elevated+=old>>12==15
        self.assertEqual(elevated,68);self.assertGreater(walks,200)

    def test_source_packets_no_identity_events_or_geometry_mutation(self):
        for n in a.MAPS:
            raw,border,h,_=a.source(n);self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])
            for p,sha in self.receipt['source_sha256'][n].items():
                self.assertEqual(a.pack.accepted.base.sha((HERE/'staged'/n/p).read_bytes()),sha)
        r=json.loads((HERE/'source-receipt.json').read_text())
        self.assertEqual(len(r['closure_changes']['PokmonLeague']),21)

    def test_bad_dimensions_missing_attrs_unknown_secondary_and_portal_fail(self):
        raw,border,h,attrs=a.source('SunyshoreCity')
        for kind in ('dimensions','attributes','secondary','portal'):
            r=raw;head=copy.deepcopy(h);at=dict(attrs)
            if kind=='dimensions':r=r[:-2]
            elif kind=='attributes':at.pop(next(iter(at)))
            elif kind=='secondary':
                cells=list(struct.unpack('<%dH'%(len(raw)//2),raw));at['1023']=at[str(cells[0]&1023)];cells[0]=(cells[0]&0xFC00)|1023;r=struct.pack('<%dH'%len(cells),*cells)
            else:head['warp_events'][0]['x']=70
            with self.subTest(kind=kind),self.assertRaises(ValueError):a.desired_art('SunyshoreCity',r,border,head,at,self.stock,self.city)

    def test_facade_overflow_fails_without_mutating_source(self):
        raw,border,h,attrs=a.source('Route222');before=copy.deepcopy((h,attrs))
        a.desired_art('Route222',raw,border,h,attrs,self.stock,self.city);self.assertEqual(before,(h,attrs))
        bad=dict(a.FACADES);bad['Route222']=[((91,31,4,4),(31,15,5,5))]
        with mock.patch.object(a.existing.templates,'FACADES',bad),self.assertRaises(ValueError):a.desired_art('Route222',raw,border,h,attrs,self.stock,self.city)

    def test_builder_forbids_existing_and_production_output(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'new off-engine'):a.build(ENGINE,Path(t))
            with self.assertRaisesRegex(ValueError,'new off-engine'):a.build(ENGINE,ENGINE/'forbidden-coast-output')

    def test_changed_elevated_source_fails_before_output_creation(self):
        real_source=a.source
        def changed(name):
            raw,border,h,attrs=real_source(name)
            if name=='SunyshoreCity':
                values=list(struct.unpack('<%dH'%(len(raw)//2),raw))
                i=next(i for i,v in enumerate(values) if v>>12==15)
                values[i]&=0x0FFF
                raw=struct.pack('<%dH'%len(values),*values)
            return raw,border,h,attrs
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'new'
            with mock.patch.object(a,'source',side_effect=changed),self.assertRaisesRegex(ValueError,'elevated walkway'):
                a.build(ENGINE,out)
            self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
