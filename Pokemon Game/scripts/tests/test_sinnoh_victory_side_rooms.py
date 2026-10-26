"""Narrow source/portal checks for the three real Victory Road side rooms."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/victory-road-side-rooms'
s=importlib.util.spec_from_file_location('victory_side_tests',HERE/'build.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class SideRooms(unittest.TestCase):
 def test_source_surfaces_water_and_slope_preservation(self):
  g=json.loads((HERE/'geometry.json').read_text())
  self.assertEqual([len(g[n]['surfaces']) for n in m.existing.DIMS],[368,1820,294])
  for n,(w,h) in m.existing.DIMS.items():
   data=(HERE/'staged'/n/'map.bin').read_bytes();cells=struct.unpack('<%dH'%(w*h),data)
   attrs=json.loads((HERE/'staged'/n/'attributes.json').read_text())
   pts={tuple(p['tile']):p for p in g[n]['surfaces']}
   for i,v in enumerate(cells):
    p=pts.get((i%w,i//w))
    if not v&0xc00:self.assertIsNotNone(p)
    if p and p['permission']==0x15:
     self.assertEqual(attrs[str(v&1023)]&255,0x15);self.assertEqual(v>>12,1)
  self.assertEqual(sum(p['permission']==0x15 for p in g['Room2']['surfaces']),891)
 def test_reciprocal_graph_and_clear_same_height_approaches(self):
  heads={}
  for n in m.existing.DIMS:
   h=json.loads((HERE/'staged'/n/'map.json').read_text());heads[h['id']]=(n,h)
  core=json.loads((HERE/'staged/Core1F/map.json').read_text());heads[core['id']]=('Core1F',core)
  for ident,(n,h) in heads.items():
   if n=='Core1F':events=h['warp_events'][-1:]
   else:
    self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
    for key in ('object_events','coord_events','bg_events'):self.assertFalse(h[key])
    events=h['warp_events']
   w=52 if n=='Core1F' else m.existing.DIMS[n][0]
   data=(HERE/'staged'/n/'map.bin').read_bytes()
   for e in events:
    other=heads[e['dest_map']][1]['warp_events'][int(e['dest_warp_id'])]
    self.assertEqual(other['dest_map'],ident)
    self.assertEqual(h['warp_events'][int(other['dest_warp_id'])],e)
    x,y=e['x'],e['y'];v=struct.unpack_from('<H',data,2*(y*w+x))[0]
    self.assertFalse(v&0xc00);self.assertEqual(v>>12,e['elevation'])
    neighbors=[struct.unpack_from('<H',data,2*(yy*w+xx))[0] for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))]
    self.assertTrue(any(not q&0xc00 and q>>12==e['elevation'] for q in neighbors))
  self.assertEqual(len(heads['MAP_SINNOH_VICTORY_SIDE_ROOM3'][1]['warp_events']),1)
 def test_only_one_parent_cell_and_unchanged_event_prefix(self):
  parent=HERE.parent/'victory-road-shell/connected/SinnohVictoryRoad_1F'
  old=(parent/'map.bin').read_bytes();new=(HERE/'staged/Core1F/map.bin').read_bytes()
  changes=[i for i,(a,b) in enumerate(zip(struct.iter_unpack('<H',old),struct.iter_unpack('<H',new))) if a!=b]
  self.assertEqual(changes,[33*52+45])
  self.assertEqual((parent/'border.bin').read_bytes(),(HERE/'staged/Core1F/border.bin').read_bytes())
  self.assertEqual(json.loads((parent/'map.json').read_text())['warp_events'],json.loads((HERE/'staged/Core1F/map.json').read_text())['warp_events'][:-1])
 def test_replay_and_refuse_unsafe_outputs(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'new';r=m.build(ENGINE,out)
   self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
   for p,sha in r['output_sha256'].items():self.assertEqual(m.existing.base.sha((out/p).read_bytes()),sha)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
if __name__=='__main__':unittest.main()
