"""Source-pinned neutral Hotel connector and four-cell ghost-seam regression."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock
from contextlib import contextmanager

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eastern-loop'
spec=importlib.util.spec_from_file_location('hotel_runtime_contract',HERE/'prepare_runtime.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ROOT=HERE.parents[4];ENGINE=ROOT/a.ENGINE;LINK=HERE/'hotel-link'


class HotelLinkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=a.assemble(ROOT)

    @contextmanager
    def world(self):
        sys.path.insert(0,str(HERE.parents[3]/'scripts/claude_play'))
        import mapdata,map_qa
        text0,binary0=Path.read_text,Path.read_bytes
        def lookup(path):
            try:return self.files.get(str(path.relative_to(ENGINE)))
            except ValueError:return None
        def text(path,*args,**kwargs):
            v=lookup(path);return v.decode() if v is not None else text0(path,*args,**kwargs)
        def binary(path):
            v=lookup(path);return v if v is not None else binary0(path)
        with mock.patch.object(Path,'read_text',new=text),mock.patch.object(Path,'read_bytes',new=binary):
            yield mapdata.World(ENGINE),map_qa

    def test_original180_cell_hotel_blob_and_two_neutral_source_returns(self):
        f=LINK/'staged/HotelGrandLake';raw=(f/'map.bin').read_bytes()
        self.assertEqual(len(raw),360)
        self.assertEqual(hashlib.sha1(b'blob 360\0'+raw).hexdigest(),'4ffd2c9d215171d44aa4396ccd93d76b7026ff85')
        h=json.loads((f/'map.json').read_text())
        self.assertEqual([(w['x'],w['y'],w['dest_map'],int(w['dest_warp_id'])) for w in h['warp_events']],[(7,1,'MAP_ROUTE213',2),(7,10,'MAP_ROUTE213',1)])
        self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
        self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])

    def test_every34900_cell_retains_full_attrs_and_only_five_recorded_collision_changes(self):
        count=changed=0
        changes={('Route213',68,11):'open',('Route213',82,0):'close',('Route213',83,0):'close',('ValorLakefront',42,65):'close',('ValorLakefront',43,65):'close'}
        for name,(w,h) in a.MAPS.items():
            hotel=name=='HotelGrandLake';folder=(LINK/'staged'/name) if hotel else HERE/'staged'/name
            source=struct.unpack('<%dH'%(w*h),(folder/'map.bin').read_bytes());new=struct.unpack('<%dH'%(w*h),self.files[f'data/layouts/{name}/map.bin'])
            attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            bank=LINK/('gate-art' if hotel or name.endswith('_Access') else 'outdoor-family');values=[(bank/(b+'-attributes.bin')).read_bytes() for b in ('primary','secondary')]
            for i,(old,current) in enumerate(zip(source,new)):
                kind=changes.get((name,i%w,i//w));expected=(old&~0x400) if kind=='open' else (old|0x400) if kind=='close' else old
                self.assertEqual(current&0xFC00,expected&0xFC00)
                changed+=bool((current^old)&0xC00);b,n=divmod(current&1023,512)
                self.assertEqual(a.art.pack.attribute(values[b],n),attrs[str(old&1023)]);count+=1
        self.assertEqual(count,34900);self.assertEqual(changed,5)

    def test_all_seventeen_original_event_indices_and_four_gateway_records_survive(self):
        total=0
        for name in a.MAPS:
            h=self.receipt['source_headers'][name];total+=len(h['warp_events'])
            if name=='HotelGrandLake':continue
            old=json.loads((HERE/'staged'/name/'map.json').read_text())
            self.assertEqual(h['warp_events'][:len(old['warp_events'])],old['warp_events'])
            self.assertEqual(h['connections'],old['connections'])
        self.assertEqual(total,21)
        for family in ('gate-art','outdoor-family'):
            for f in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
                self.assertTrue((LINK/family/f).read_bytes().startswith((HERE/family/f).read_bytes()))
        self.assertEqual(self.receipt['temporary_map_slots']['HotelGrandLake'],31)

    def test_native_animated_south_door_stays_solid_and_north_arrow_alone_reopens(self):
        raw=self.files['data/layouts/Route213/map.bin']
        north=struct.unpack_from('<H',raw,2*(11*100+68))[0];south=struct.unpack_from('<H',raw,2*(16*100+68))[0]
        self.assertEqual(north&0xC00,0);self.assertEqual(south&0xC00,0x400)
        self.assertEqual(south&1023,33) # real existing Generic door animation lookup
        b,i=divmod(north&1023,512)
        bank=LINK/'outdoor-family'/('secondary-attributes.bin' if b else 'primary-attributes.bin')
        self.assertEqual(a.art.pack.attribute(bank.read_bytes(),i),4197)

    def test_actual_world_audit_is_clean_and_pre_cap_frontier_is_exactly_four_cells(self):
        with self.world() as (world,qa):
            ids=[h['id'] for h in self.receipt['source_headers'].values()]
            findings,_=qa.static_audit(world,ids);self.assertEqual(findings,[])
            reachable=qa.batch_reach(world,ids,'MAP_ROUTE213',(4,9))
            self.assertEqual({m for m,p in reachable},set(ids))
            expected={('MAP_ROUTE213',(82,0)),('MAP_ROUTE213',(83,0)),('MAP_VALOR_LAKEFRONT',(42,65)),('MAP_VALOR_LAKEFRONT',(43,65))}
            self.assertFalse(reachable&expected)
            for mid,point in expected:
                m=world.map(mid);cells=list(m.blocks);i=point[1]*m.width+point[0];self.assertEqual(cells[i]&0xC00,0x400);cells[i]&=~0xC00;m.blocks=tuple(cells)
            frontier=qa.batch_reach(world,ids,'MAP_ROUTE213',(82,0));self.assertEqual(frontier,expected)
            self.assertTrue(all(world.map(mid).warp_at(*p) is None for mid,p in frontier))

    def test_all_three_derived_previews_match_actual_existing_assets(self):
        pack=a.art.pack;dual=pack.accepted.dual
        for name,folder,geometry,border,dims,output in [('HotelGrandLake','gate-art',LINK/'staged/HotelGrandLake/averon-map.bin',LINK/'staged/HotelGrandLake/border.bin',(15,12),LINK/'staged/HotelGrandLake/averon.png'),('Route213','outdoor-family',LINK/'route213-map.bin',HERE/'staged/Route213/averon-border.bin',(100,60),LINK/'route213-preview.png'),('ValorLakefront','outdoor-family',LINK/'valor-map.bin',HERE/'staged/ValorLakefront/averon-border.bin',(56,66),LINK/'valor-preview.png')]:
            paths=['data/tilesets/primary/building/','data/tilesets/secondary/shop/'] if folder=='gate-art' else ['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
            banks=[(LINK/folder/(b+'-metatiles.bin')).read_bytes() for b in ('primary','secondary')];images=[dual.indexed((ENGINE/(p+'tiles.png')).read_bytes()) for p in paths]
            dep=dual.closure(geometry.read_bytes()+border.read_bytes(),banks,images);pals={i:pack.accepted.base.palette((ENGINE/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in dep['palettes']}
            actual=dual.render(geometry.read_bytes(),banks,images,pals,*dims)
            with dual.Image.open(output) as rendered:self.assertEqual(actual.tobytes(),rendered.convert('RGB').tobytes())


if __name__=='__main__':unittest.main()
