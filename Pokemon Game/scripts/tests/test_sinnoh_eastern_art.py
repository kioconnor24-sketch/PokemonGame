"""Actual eight-map shared existing-Averon art, with immutable source physics."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eastern-loop'
spec=importlib.util.spec_from_file_location('eastern_outdoor_art_test',HERE/'adapt_outdoor_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'


class OutdoorArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads((HERE/'outdoor-art-receipt.json').read_text())
        cls.banks=[(HERE/'outdoor-family'/(b+'-metatiles.bin')).read_bytes() for b in ('primary','secondary')]
        cls.attrs=[(HERE/'outdoor-family'/(b+'-attributes.bin')).read_bytes() for b in ('primary','secondary')]
        cls.stock=[(ENGINE/('data/tilesets/'+p+'/metatiles.bin')).read_bytes() for p in ('primary/general','secondary/rustboro')]
        cls.city=struct.unpack('<2400H',(ENGINE/'data/layouts/RustboroCity/map.bin').read_bytes())

    def test_every_map_and_border_preserves_all_physics_and_full_attribute_words(self):
        count=0
        for name,(w,h) in a.MAPS.items():
            folder=HERE/'staged'/name;raw,border,header,attrs=a.source(name)
            adapted=(folder/'averon-map.bin').read_bytes()+(folder/'averon-border.bin').read_bytes()
            self.assertEqual(len(adapted),len(raw+border))
            for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',adapted)):
                self.assertEqual(old&0xFC00,new&0xFC00)
                b,i=divmod(new&1023,512);self.assertEqual(a.pack.attribute(self.attrs[b],i),attrs[str(old&1023)]);count+=1
        self.assertEqual(count,34320);self.assertEqual(count,self.receipt['verified_physics_behavior_cells'])

    def test_primary_is_unchanged_and_secondary_fits_actual_hardware_budget(self):
        self.assertEqual(self.banks[0],self.stock[0])
        self.assertEqual(self.attrs[0],(ENGINE/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes())
        self.assertEqual(len(self.banks[1])//16,self.receipt['secondary_records'])
        self.assertEqual(len(self.banks[1]),len(self.attrs[1])*8)
        self.assertLessEqual(len(self.banks[1]),8192)
        self.assertEqual(self.receipt['remaining_secondary_slots'],512-len(self.banks[1])//16)

    def test_actual_render_of_all_eight_uses_only_current_general_rustboro_assets(self):
        dual=a.pack.accepted.dual;base=a.pack.accepted.base
        paths=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
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
        self.assertEqual(self.receipt['status'],'EXISTING_AVERON_EASTERN_OUTDOOR_ART_NOT_RUNTIME_ACCEPTANCE')

    def test_all_source_bridge_and_road_heights_are_identical_after_adaptation(self):
        for name in a.MAPS:
            folder=HERE/'staged'/name
            raw=struct.unpack('<%dH'%((folder/'map.bin').stat().st_size//2),(folder/'map.bin').read_bytes())
            new=struct.unpack('<%dH'%len(raw),(folder/'averon-map.bin').read_bytes())
            self.assertEqual([v>>12 for v in raw],[v>>12 for v in new])
            self.assertEqual(sum(v>>12==15 for v in raw),self.receipt['elevation15_preserved'][name])
        self.assertEqual(sum(self.receipt['elevation15_preserved'].values()),97)

    def test_incomplete_attributes_unknown_secondary_and_wrong_dimensions_rejected(self):
        raw,border,header,attrs=a.source('Route214')
        for kind in ('dimension','attribute','secondary','anchor'):
            r=raw;b=border;h=copy.deepcopy(header);at=dict(attrs)
            if kind=='dimension':r=r[:-2]
            elif kind=='attribute':at.pop(next(iter(at)))
            elif kind=='secondary':
                cells=list(struct.unpack('<%dH'%(len(raw)//2),raw));old=cells[0]&1023
                cells[0]=(cells[0]&0xFC00)|1023;r=struct.pack('<%dH'%len(cells),*cells);at['1023']=at[str(old)]
            else:h['warp_events'][0]['x']=44
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                a.desired_art('Route214',r,b,h,at,self.stock,self.city)

    def test_facade_out_of_bounds_fails_and_inputs_are_not_mutated(self):
        raw,border,header,attrs=a.source('VeilstoneCity');before=copy.deepcopy((header,attrs))
        a.desired_art('VeilstoneCity',raw,border,header,attrs,self.stock,self.city)
        self.assertEqual(before,(header,attrs))
        bad=dict(a.FACADES);bad['VeilstoneCity']=[((65,67,5,5),'house')]
        with mock.patch.object(a,'FACADES',bad),self.assertRaises(ValueError):
            a.desired_art('VeilstoneCity',raw,border,header,attrs,self.stock,self.city)

    def test_bridge_decks_and_both_centers_use_complete_existing_art(self):
        count=0
        for name,(w,h) in a.MAPS.items():
            raw,border,header,attrs=a.source(name)
            new=struct.unpack('<%dH'%(len(raw)//2),(HERE/'staged'/name/'averon-map.bin').read_bytes())
            for (old,),adapted in zip(struct.iter_unpack('<H',raw),new):
                mid=old&1023
                if mid>=512 and a.SECONDARY[name][mid]==528:
                    bank,i=divmod(adapted&1023,512)
                    self.assertEqual(a.pack.words(self.banks[bank],i),a.pack.words(self.stock[1],16));count+=1
        self.assertGreater(count,100)
        for name,x,y in [('VeilstoneCity',39,33),('PastoriaCity',24,11)]:
            w,h=a.MAPS[name];raw=struct.unpack('<%dH'%(w*h),(HERE/'staged'/name/'averon-map.bin').read_bytes())
            for yy in range(4):
                for xx in range(4):
                    old=self.city[(35+yy)*40+15+xx]&1023;b,i=divmod(old,512)
                    new=raw[(y+yy)*w+x+xx]&1023;nb,ni=divmod(new,512)
                    self.assertEqual(a.pack.words(self.banks[nb],ni),a.pack.words(self.stock[b],i))

    def test_paving_and_sand_fill_are_not_repeated_grass_or_shore_edges(self):
        paving=sand=0
        for name,(w,h) in a.MAPS.items():
            raw,border,header,attrs=a.source(name);new=struct.unpack('<%dH'%(w*h),(HERE/'staged'/name/'averon-map.bin').read_bytes())
            anchors={(p['x'],p['y']) for p in header['warp_events']}
            for index,((cell,),adapted) in enumerate(zip(struct.iter_unpack('<H',raw),new)):
                mid=cell&1023;x,y=index%w,index//w
                if mid<512 or (x,y) in anchors or any(dx<=x<dx+dw and dy<=y<dy+dh for (dx,dy,dw,dh),kind in a.FACADES[name]):continue
                wanted=None
                if name=='VeilstoneCity' and not cell&0xC00 and a.SECONDARY[name][mid]==-1:
                    wanted=a.pack.words(self.stock[1],699-512);paving+=1
                if attrs[str(mid)]&255==33:
                    wanted=a.pack.words(self.stock[0],292);sand+=1
                if wanted is not None:
                    b,i=divmod(adapted&1023,512);self.assertEqual(a.pack.words(self.banks[b],i),wanted)
        self.assertGreater(paving,200);self.assertGreater(sand,100)

    def test_previous_four_gate_artifacts_and_source_metadata_are_unchanged(self):
        base=a.pack.accepted.base;root=HERE.parents[4];prefix=str(HERE.relative_to(root))
        paths=list((HERE/'gate-art').glob('*.bin'))+[HERE/'gate-art-receipt.json']
        for name in ('Route212_Access','Route213_Access','Route214_Access','Route215_Access'):
            paths += [HERE/'staged'/name/f for f in ('averon-map.bin','averon.png')]
        self.assertEqual(len(paths),13)
        for p in paths:
            self.assertEqual(p.read_bytes(),base.git(root,'show','ea801a08bb6de9ad7d9a528a37843a102302db00:'+str(p.relative_to(root))))
        self.assertEqual(sum(len(__import__('json').loads(p.read_text())['warp_events']) for p in (HERE/'staged').glob('*/map.json')),17)
        for name in a.MAPS:
            h=__import__('json').loads((HERE/'staged'/name/'map.json').read_text())
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])

    def test_no_solid_dark_placeholder_cells_remain_in_any_actual_preview(self):
        # Two donor primary ordinals resolve to transparent/blank stock art.
        # Bounds checks alone accept these records; inspect actual pixels too.
        examples=[];count=0
        for name,(w,h) in a.MAPS.items():
            with a.pack.accepted.dual.Image.open(HERE/'staged'/name/'averon.png') as image:
                image=image.convert('RGB')
                for y in range(h):
                    for x in range(w):
                        colors=image.crop((x*16,y*16,x*16+16,y*16+16)).getcolors(256)
                        if colors and len(colors)==1 and sum(colors[0][1])<160:
                            count+=1
                            if len(examples)<8:examples.append((name,x,y))
        self.assertEqual(count,0,'unrendered dark cell examples: '+repr(examples))

    def test_dirty_reviewed_source_rejected_before_art_generation(self):
        original=Path.read_bytes;target=HERE/'staged/Route214/map.bin'
        def read(path):
            data=original(path);return data[:-1]+bytes([data[-1]^1]) if path==target else data
        with mock.patch.object(Path,'read_bytes',new=read),self.assertRaisesRegex(ValueError,'source identity'):
            a.source('Route214')


if __name__=='__main__':unittest.main()
