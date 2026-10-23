"""Actual permitted-art Forest adaptation, with source physics/warps intact."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from PIL import Image

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/forest-chateau'
spec=importlib.util.spec_from_file_location('forest_materials',HERE/'adapt_forest_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'


class ForestArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=HERE/'staged/EternaForest';cls.raw=(cls.folder/'map.bin').read_bytes();cls.border=(cls.folder/'border.bin').read_bytes()
        cls.receipt=json.loads((HERE/'forest-art-receipt.json').read_text())
        cls.source=json.loads((cls.folder/'attributes.json').read_text())['used_source_attribute_words']
        cls.primary=(HERE/'forest-art/primary-metatiles.bin').read_bytes();cls.pa=(HERE/'forest-art/primary-attributes.bin').read_bytes()
        cls.secondary=(HERE/'forest-art/secondary-metatiles.bin').read_bytes();cls.sa=(HERE/'forest-art/secondary-attributes.bin').read_bytes()
        cls.source_attrs=[bytearray(1024),bytearray(1024)]
        for mid,v in cls.source.items():
            b,i=divmod(int(mid),512);struct.pack_into('<H',cls.source_attrs[b],i*2,v)

    def test_all_6892_map_border_cells_preserve_physics_full_behavior_layer(self):
        dst=(self.folder/'averon-map.bin').read_bytes()+(self.folder/'averon-border.bin').read_bytes()
        self.assertEqual(len(dst),len(self.raw+self.border));count=0
        for (old,),(new,) in zip(struct.iter_unpack('<H',self.raw+self.border),struct.iter_unpack('<H',dst)):
            self.assertEqual(old&0xFC00,new&0xFC00)
            b,i=divmod(new&1023,512)
            self.assertEqual(a.pack.attribute((self.pa,self.sa)[b],i),self.source[str(old&1023)])
            count+=1
        self.assertEqual(count,6892)

    def test_existing_metadata_prefixes_and_capacity_preserved(self):
        p=ENGINE/'data/tilesets/primary/general';s=ENGINE/'data/tilesets/secondary/rustboro'
        self.assertEqual(self.primary,(p/'metatiles.bin').read_bytes());self.assertEqual(self.pa,(p/'metatile_attributes.bin').read_bytes())
        for data,path in ((self.secondary,s/'metatiles.bin'),(self.sa,s/'metatile_attributes.bin')):
            self.assertTrue(data.startswith(path.read_bytes()))
        self.assertLessEqual(len(self.secondary)//16,512);self.assertEqual(len(self.secondary),len(self.sa)*8)

    def test_actual_preview_reproduces_from_only_current_averon_dependencies(self):
        dual=a.pack.accepted.dual;base=a.pack.accepted.base
        images=[dual.indexed((ENGINE/('data/tilesets/'+family+'/tiles.png')).read_bytes()) for family in ('primary/general','secondary/rustboro')]
        raw=(self.folder/'averon-map.bin').read_bytes();border=(self.folder/'averon-border.bin').read_bytes()
        deps=dual.closure(raw+border,[self.primary,self.secondary],images)
        self.assertEqual(deps,self.receipt['dependencies'])
        palettes={i:base.palette((ENGINE/('data/tilesets/'+('primary/general' if i<6 else 'secondary/rustboro')+'/palettes/%02d.pal'%i)).read_bytes()) for i in deps['palettes']}
        actual=dual.render(raw,[self.primary,self.secondary],images,palettes,82,84)
        with Image.open(self.folder/'averon.png') as published:self.assertEqual(actual.tobytes(),published.convert('RGB').tobytes())

    def test_source_fingerprints_and_exact_doorway_unchanged(self):
        base=a.pack.accepted.base
        for p,h in self.receipt['source_sha256'].items():self.assertEqual(base.sha((self.folder/p).read_bytes()),h)
        h=json.loads((self.folder/'map.json').read_text())
        self.assertEqual(h['warp_events'],[dict(x=59,y=7,elevation=0,dest_map='MAP_OLD_CHATEAU_ENTRANCE',dest_warp_id='0')])
        self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])

    def args(self):
        p=ENGINE/'data/tilesets/primary/general';s=ENGINE/'data/tilesets/secondary/rustboro'
        return [self.raw,self.border,self.source_attrs,(p/'metatiles.bin').read_bytes(),(p/'metatile_attributes.bin').read_bytes(),
                (s/'metatiles.bin').read_bytes(),(s/'metatile_attributes.bin').read_bytes(),
                (ENGINE/'data/layouts/RustboroCity/map.bin').read_bytes(),json.loads((self.folder/'map.json').read_text())['warp_events']]

    def test_pack_reproduces_published_maps_banks_without_mutating_input(self):
        args=self.args();before=[bytes(x) for x in self.source_attrs]
        raw,border,secondary,attrs=a.candidate(*args)
        self.assertEqual(raw,(self.folder/'averon-map.bin').read_bytes());self.assertEqual(border,(self.folder/'averon-border.bin').read_bytes())
        self.assertEqual(secondary,self.secondary);self.assertEqual(attrs,self.sa)
        self.assertEqual(before,[bytes(x) for x in self.source_attrs])

    def test_bad_dimensions_warp_unknown_terrain_and_facade_outside_envelope_rejected(self):
        for mode in ('dimensions','border','warp','unknown','envelope'):
            args=self.args()
            if mode=='dimensions':args[0]=args[0][:-1]
            elif mode=='border':args[1]=b'bad'
            elif mode=='warp':args[-1][0]['x']=58
            else:
                raw=bytearray(args[0]);struct.pack_into('<H',raw,0,1023 if mode=='unknown' else 724);args[0]=raw
            with self.subTest(mode=mode),self.assertRaises(ValueError):a.candidate(*args)

    def test_declared_current_asset_hashes_are_verified(self):
        base=a.pack.accepted.base
        root=Path(base.git(ENGINE,'rev-parse','--show-toplevel').decode().strip())
        for path,h in self.receipt['existing_averon_sha256'].items():
            # Historical receipt provenance need not exist in a shallow PR clone.
            # Verify current tracked bytes, then independently require the exact
            # immutable published asset hash; never fetch history to run fixtures.
            data=base.verified_file(root,ENGINE.relative_to(root)/path,'HEAD')
            self.assertEqual(base.sha(data),h)


if __name__=='__main__':unittest.main()
