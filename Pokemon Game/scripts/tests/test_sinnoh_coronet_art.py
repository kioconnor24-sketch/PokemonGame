"""Actual three-map shared existing-Averon art, with immutable source physics."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/celestic-north'
spec=importlib.util.spec_from_file_location('coronet_cave_art_test',HERE/'adapt_cave_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'


class OutdoorArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads((HERE/'cave-art-receipt.json').read_text())
        cls.banks=[(HERE/'cave-family'/(b+'-metatiles.bin')).read_bytes() for b in ('primary','secondary')]
        cls.attrs=[(HERE/'cave-family'/(b+'-attributes.bin')).read_bytes() for b in ('primary','secondary')]
        cls.stock=[(ENGINE/('data/tilesets/'+p+'/metatiles.bin')).read_bytes() for p in ('primary/general','secondary/cave')]
        cls.city=None

    def test_every_map_and_border_preserves_all_physics_and_full_attribute_words(self):
        count=0
        for name,(w,h) in a.MAPS.items():
            folder=HERE/'staged'/name;raw,border,header,attrs=a.source(name)
            adapted=(folder/'averon-map.bin').read_bytes()+(folder/'averon-border.bin').read_bytes()
            self.assertEqual(len(adapted),len(raw+border))
            for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',adapted)):
                self.assertEqual(old&0xFC00,new&0xFC00)
                b,i=divmod(new&1023,512);self.assertEqual(a.pack.attribute(self.attrs[b],i),attrs[str(old&1023)]);count+=1
        self.assertEqual(count,4232);self.assertEqual(count,self.receipt['verified_physics_behavior_cells'])

    def test_primary_is_unchanged_and_secondary_fits_actual_hardware_budget(self):
        self.assertEqual(self.banks[0],self.stock[0])
        self.assertEqual(self.attrs[0],(ENGINE/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes())
        self.assertEqual(len(self.banks[1])//16,self.receipt['secondary_records'])
        self.assertEqual(len(self.banks[1]),len(self.attrs[1])*8)
        self.assertLessEqual(len(self.banks[1]),8192)
        self.assertEqual(self.receipt['remaining_secondary_slots'],512-len(self.banks[1])//16)

    def test_actual_render_of_all_three_uses_only_current_general_cave_assets(self):
        dual=a.pack.accepted.dual;base=a.pack.accepted.base
        paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
        images=[dual.indexed((ENGINE/(p+'tiles.png')).read_bytes()) for p in paths]
        for name,(w,h) in a.MAPS.items():
            folder=HERE/'staged'/name;raw=(folder/'averon-map.bin').read_bytes();border=(folder/'averon-border.bin').read_bytes()
            dependencies=dual.closure(raw+border,self.banks,images)
            self.assertEqual(dependencies,self.receipt['dependencies'][name])
            palettes={i:base.palette((ENGINE/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in dependencies['palettes']}
            actual=dual.render(raw,self.banks,images,palettes,w,h)
            with dual.Image.open(folder/'averon.png') as image:
                self.assertEqual(actual.size,image.size);self.assertEqual(actual.tobytes(),image.convert('RGB').tobytes())

    def test_all_source_hashes_and_existing_graphics_provenance_are_actual(self):
        for name,hashes in self.receipt['source_sha256'].items():
            for p,h in hashes.items():self.assertEqual(a.pack.accepted.base.sha((HERE/'staged'/name/p).read_bytes()),h)
        base=a.pack.accepted.base;root=HERE.parents[4]
        head=base.git(root,'rev-parse','HEAD').decode().strip()
        for p,h in self.receipt['existing_averon_sha256'].items():
            # Reuse the real dirty-file/eol=crlf check. Hash committed palette
            # bytes, not the declared Windows checkout representation.
            self.assertEqual(base.sha(base.verified_file(root,ENGINE.relative_to(root)/p,head)),h)
        self.assertEqual(self.receipt['status'],'EXISTING_AVERON_CORONET_CAVE_ART_NOT_RUNTIME_ACCEPTANCE')

    def test_all_source_bridge_and_road_heights_are_identical_after_adaptation(self):
        for name in a.MAPS:
            folder=HERE/'staged'/name
            raw=struct.unpack('<%dH'%((folder/'map.bin').stat().st_size//2),(folder/'map.bin').read_bytes())
            new=struct.unpack('<%dH'%len(raw),(folder/'averon-map.bin').read_bytes())
            self.assertEqual([v>>12 for v in raw],[v>>12 for v in new])
            self.assertEqual(sum(v>>12==15 for v in raw),self.receipt['elevation15_preserved'][name])
        self.assertEqual(self.receipt['elevation15_preserved']['MtCoronet_B1F'],0)

    def test_incomplete_attributes_unknown_secondary_and_wrong_dimensions_rejected(self):
        raw,border,header,attrs=a.source('MtCoronet_B1F')
        for kind in ('dimension','attribute','secondary'):
            r=raw;b=border;h=copy.deepcopy(header);at=dict(attrs)
            if kind=='dimension':r=r[:-2]
            elif kind=='attribute':at.pop(next(iter(at)))
            elif kind=='secondary':
                cells=list(struct.unpack('<%dH'%(len(raw)//2),raw));old=cells[0]&1023
                cells[0]=(cells[0]&0xFC00)|1023;r=struct.pack('<%dH'%len(cells),*cells);at['1023']=at[str(old)]
            else:raise AssertionError('unexpected fixture')
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                a.desired_art('MtCoronet_B1F',r,b,h,at,self.stock,self.city)

    def test_all_explicit_ladder_water_and_transition_roles_are_present(self):
        self.assertEqual(a.REPLACEMENTS[933],575)
        self.assertEqual(a.REPLACEMENTS[922],513)
        self.assertEqual({a.REPLACEMENTS[i] for i in range(934,943)},{161})
        self.assertEqual({a.REPLACEMENTS[i] for i in range(944,950)},{207})
        for name in a.MAPS:
            header=json.loads((HERE/'staged'/name/'map.json').read_text())
            self.assertEqual(header['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(header['object_events'] or header['coord_events'] or header['bg_events'])
            old=(HERE/'staged'/name/'map.json').read_bytes()
            raw,border,h,attrs=a.source(name)
            a.desired_art(name,raw,border,h,attrs,self.stock)
            self.assertEqual(old,(HERE/'staged'/name/'map.json').read_bytes())


if __name__=='__main__':unittest.main()
