"""Original cave shell: actual portal facts, reachable returns, no engine effects."""
import copy
from collections import deque
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/victory-road-shell'
spec=importlib.util.spec_from_file_location('victory_shell_test',HERE/'build_shell.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
ENGINE=HERE.parents[3]/'engine'

def cells(raw):return struct.unpack('<%dH'%(len(raw)//2),raw)
def reach(grid,w,h,start):
    seen={start};queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<w and 0<=ny<h and (nx,ny) not in seen and not grid[ny*w+nx]&0xC00:
                seen.add((nx,ny));queue.append((nx,ny))
    return seen

class VictoryShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe=json.loads((HERE/'shell-recipe.json').read_text());cls.reference=json.loads((HERE/'portal-reference.json').read_text())
        cls.result=s.construct(cls.recipe,cls.reference);cls.receipt=json.loads((HERE/'source-receipt.json').read_text())

    def test_three_real_core_floor_portals_match_pinned_ds_coordinates_and_returns(self):
        count=0;byid={v[2]['id']:v[2] for v in self.result.values()}
        for n,(raw,border,h) in self.result.items():
            plan=self.recipe['maps'][n];ref=self.reference['files'][plan['reference']]['warp_events']
            self.assertEqual(len(plan['interior_warp_indices']),len(h['warp_events']))
            for old,p in zip(plan['interior_warp_indices'],h['warp_events']):
                self.assertEqual((ref[old]['x'],ref[old]['z']),(p['x'],p['y']))
                target=byid[p['dest_map']]['warp_events'][int(p['dest_warp_id'])]
                self.assertEqual(target['dest_map'],h['id']);count+=1
            self.assertEqual((HERE/'staged'/n/'map.bin').read_bytes(),raw)
            self.assertEqual((HERE/'staged'/n/'border.bin').read_bytes(),border)
            self.assertEqual(json.loads((HERE/'staged'/n/'map.json').read_text()),h)
        self.assertEqual(count,12)
        self.assertEqual(self.reference['revision'],'6dc1499e3127176d4cb34f41c01ee62e1d98808a')
        self.assertEqual(set(self.reference['files']),{'1f','2f','b1f','league'})
        self.assertTrue(all(set(v)=={'path','git_blob','sha256','warp_events'} for v in self.reference['files'].values()))

    def test_all7472_cells_closed_boundaries_and_every_stair_accessible_without_hm(self):
        total=0
        for n,(raw,border,h) in self.result.items():
            p=self.recipe['maps'][n];w,ht=p['width'],p['height'];grid=cells(raw);total+=len(grid)
            self.assertLessEqual((w+15)*(ht+14),10240)
            self.assertTrue(all(grid[y*w+x]&0xC00 for y in range(ht) for x in range(w) if x in (0,w-1) or y in (0,ht-1)))
            start=h['warp_events'][0];seen=reach(grid,w,ht,(start['x'],start['y']))
            floor={(x,y) for y in range(ht) for x in range(w) if not grid[y*w+x]&0xC00}
            self.assertEqual(seen,floor,'authored walkable component must be connected')
            for v in h['warp_events']:
                self.assertIn((v['x'],v['y']),seen)
                self.assertGreaterEqual(sum((v['x']+dx,v['y']+dy) in seen for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))),2)
            self.assertTrue(all(v>>12==3 for v in grid if not v&0xC00))
        self.assertEqual(total,7472)

    def test_unbuilt_side_rooms_and_exterior_anchors_closed_no_saved_identity_or_story(self):
        for n,(raw,_,h) in self.result.items():
            plan=self.recipe['maps'][n];grid=cells(raw)
            for x,y in plan['sealed_external_ports']:self.assertTrue(grid[y*plan['width']+x]&0xC00)
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'] or h['connections'])
            self.assertTrue(all(p['dest_map'] in s.IDS.values() for p in h['warp_events']))
        self.assertEqual(self.recipe['maps']['SinnohVictoryRoad_1F']['sealed_external_ports'],[[15,78],[34,5],[45,33]])

    def test_existing_graphics_native_ladders_capacity_and_actual_preview_pixels(self):
        paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
        banks=[(ENGINE/(p+'metatiles.bin')).read_bytes() for p in paths]
        attrs=[(ENGINE/(p+'metatile_attributes.bin')).read_bytes() for p in paths]
        images=[s.dual.indexed((ENGINE/(p+'tiles.png')).read_bytes()) for p in paths]
        self.assertEqual(s.art.attribute(attrs[1],s.LADDER-512)&511,0x61)
        for n,(raw,border,_) in self.result.items():
            dep=s.dual.closure(raw+border,banks,images);self.assertEqual(dep,self.receipt['maps'][n]['dependencies'])
            p=self.recipe['maps'][n];pals={i:s.base.palette((ENGINE/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in dep['palettes']}
            im=s.dual.render(raw,banks,images,pals,p['width'],p['height'])
            with s.dual.Image.open(HERE/'staged'/n/'averon.png') as actual:self.assertEqual(im.tobytes(),actual.convert('RGB').tobytes())
            words=json.loads((HERE/'staged'/n/'attributes.json').read_text())['used_source_attribute_words']
            for mid,val in words.items():self.assertEqual(s.art.attribute(attrs[int(mid)//512],int(mid)%512),val)
        root=HERE.parents[4]
        for p,h in self.receipt['existing_averon_sha256'].items():self.assertEqual(s.sha(s.base.verified_file(root,ENGINE.relative_to(root)/p,'HEAD')),h)

    def test_wrong_map_set_buffer_diagonal_floor_and_missing_stair_return_rejected(self):
        for kind in ('map','buffer','diagonal','floor','return','external'):
            r=copy.deepcopy(self.recipe);ref=copy.deepcopy(self.reference);p=r['maps']['SinnohVictoryRoad_1F']
            if kind=='map':r['maps'].pop('SinnohVictoryRoad_B1F')
            elif kind=='buffer':p['width']=1000
            elif kind=='diagonal':p['corridors'][0]=[[3,3],[4,4]]
            elif kind=='floor':p['rooms'][0]=[0,0,3,3]
            elif kind=='return':ref['files']['2f']['warp_events'][0]['dest_warp_id']=5
            else:p['interior_warp_indices'].append(6)
            with self.subTest(kind=kind),self.assertRaises(ValueError):s.construct(r,ref)

    def test_existing_and_production_output_refused(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'new off-engine'):s.build(ENGINE,Path(t))
            with self.assertRaisesRegex(ValueError,'new off-engine'):s.build(ENGINE,ENGINE/'forbidden-victory-shell')

if __name__=='__main__':unittest.main()
