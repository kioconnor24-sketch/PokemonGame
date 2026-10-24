"""Eterna's shared source-art family preserves old roads and all City physics."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from unittest import mock
from PIL import Image

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eterna-cycle'
spec=importlib.util.spec_from_file_location('eterna_city_materials',HERE/'adapt_eterna_city_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'


class CityArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=HERE/'staged/EternaCity';cls.receipt=json.loads((HERE/'city-art-receipt.json').read_text())
        cls.raw=(cls.folder/'map.bin').read_bytes();cls.border=(cls.folder/'border.bin').read_bytes()
        cls.source=json.loads((cls.folder/'attributes.json').read_text())['used_source_attribute_words']
        cls.banks=[(HERE/'city-family'/(b+'-metatiles.bin')).read_bytes() for b in ('primary','secondary')]
        cls.attrs=[(HERE/'city-family'/(b+'-attributes.bin')).read_bytes() for b in ('primary','secondary')]

    def test_all_3304_city_cells_keep_physics_and_full_behavior_layer(self):
        data=(self.folder/'averon-map.bin').read_bytes()+(self.folder/'averon-border.bin').read_bytes()
        self.assertEqual(len(data),6608)
        for (old,),(new,) in zip(struct.iter_unpack('<H',self.raw+self.border),struct.iter_unpack('<H',data)):
            self.assertEqual(old&0xFC00,new&0xFC00);b,i=divmod(new&1023,512)
            self.assertEqual(a.pack.attribute(self.attrs[b],i),self.source[str(old&1023)])

    def test_entire_road_metadata_prefix_and_primary_preserved_with_capacity(self):
        for name,index in [('secondary-metatiles.bin',0),('secondary-attributes.bin',1)]:
            prefix=(HERE/'cycling-art'/name).read_bytes();self.assertTrue((self.banks[1] if index==0 else self.attrs[1]).startswith(prefix))
        self.assertEqual(self.banks[0],(HERE/'cycling-art/primary-metatiles.bin').read_bytes())
        self.assertEqual(self.attrs[0],(HERE/'cycling-art/primary-attributes.bin').read_bytes())
        self.assertEqual(self.receipt['prior_secondary_records'],27)
        self.assertLessEqual(len(self.banks[1])//16,512);self.assertEqual(len(self.banks[1]),len(self.attrs[1])*8)

    def test_all_three_actual_renders_share_one_graphics_and_metadata_family(self):
        dual=a.pack.accepted.dual;base=a.pack.accepted.base
        paths=('primary/general','secondary/rustboro');images=[dual.indexed((ENGINE/('data/tilesets/'+p+'/tiles.png')).read_bytes()) for p in paths]
        for name,(w,h) in {'EternaCity':(60,55),'Route206':(28,120),'Route211_West':(36,28)}.items():
            folder=HERE/'staged'/name;raw=(folder/'averon-map.bin').read_bytes();border=(folder/'averon-border.bin').read_bytes()
            deps=dual.closure(raw+border,self.banks,images);self.assertEqual(deps,self.receipt['dependencies'][name])
            palettes={i:base.palette((ENGINE/('data/tilesets/'+paths[i>=6]+'/palettes/%02d.pal'%i)).read_bytes()) for i in deps['palettes']}
            image=dual.render(raw,self.banks,images,palettes,w,h)
            with Image.open(folder/'averon.png') as published:self.assertEqual(image.tobytes(),published.convert('RGB').tobytes(),name)

    def args(self):
        p=ENGINE/'data/tilesets/primary/general';s=ENGINE/'data/tilesets/secondary/rustboro'
        return [self.raw,self.border,dict(self.source),(p/'metatiles.bin').read_bytes(),(p/'metatile_attributes.bin').read_bytes(),
                (HERE/'cycling-art/secondary-metatiles.bin').read_bytes(),(HERE/'cycling-art/secondary-attributes.bin').read_bytes(),
                [(p/'metatiles.bin').read_bytes(),(s/'metatiles.bin').read_bytes()],(ENGINE/'data/layouts/RustboroCity/map.bin').read_bytes(),
                json.loads((self.folder/'map.json').read_text())['warp_events']]

    def test_repack_is_exact_and_does_not_mutate_source_or_prefix_inputs(self):
        args=self.args();before=copy.deepcopy(args);raw,border,s,sa=a.candidate(*args)
        self.assertEqual(args,before);self.assertEqual(raw,(self.folder/'averon-map.bin').read_bytes())
        self.assertEqual(border,(self.folder/'averon-border.bin').read_bytes());self.assertEqual(s,self.banks[1]);self.assertEqual(sa,self.attrs[1])

    def test_bad_dimensions_gateway_missing_semantics_and_overflow_rejected(self):
        for mode in ('dimensions','border','warp','semantics','capacity'):
            args=self.args()
            if mode=='dimensions':args[0]=args[0][:-1]
            elif mode=='border':args[1]=b'bad'
            elif mode=='warp':args[-1][0]['dest_warp_id']='1'
            elif mode=='semantics':args[2].pop(str(struct.unpack_from('<H',self.raw)[0]&1023))
            else:args[5]=bytes(8192);args[6]=bytes(1024)
            with self.subTest(mode=mode),self.assertRaises(ValueError):a.candidate(*args)

    def test_bad_facade_envelope_fails_before_any_output(self):
        with mock.patch.object(a,'FACADES',[((60,0,2,2),(0,0,2,2))]),self.assertRaises(ValueError):a.candidate(*self.args())

    def test_existing_current_assets_and_source_warp_hashes_are_exact(self):
        base=a.pack.accepted.base;root=Path(base.git(ENGINE,'rev-parse','--show-toplevel').decode().strip())
        for p,h in self.receipt['existing_averon_sha256'].items():
            self.assertEqual(base.sha(base.verified_file(root,ENGINE.relative_to(root)/p,'HEAD')),h)
        for p,h in self.receipt['source_sha256'].items():self.assertEqual(base.sha((self.folder/p).read_bytes()),h)
        h=json.loads((self.folder/'map.json').read_text());self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
        self.assertEqual(h['warp_events'],[dict(x=15,y=48,elevation=0,dest_map='MAP_ROUTE206_NORTH',dest_warp_id='0')])
        self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])


if __name__=='__main__':unittest.main()
