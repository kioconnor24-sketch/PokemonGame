"""Pinned real League cave doors coupled to authored core; no terrain rewrite."""
from collections import deque
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(os.environ.get('AVERON_TEST_SOURCE_ROOT',Path(__file__).resolve().parents[3]))
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/victory-road-shell'
PROTOTYPE=Path(os.environ.get('AVERON_CONNECTOR_FIXTURE',HERE))
PACKET=Path(os.environ.get('AVERON_CONNECTED_PACKET',HERE))
spec=importlib.util.spec_from_file_location('victory_connected_test',PROTOTYPE/'connect_league.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
ENGINE=ROOT/'Pokemon Game/engine'
sys.path.insert(0,str(ROOT/'Pokemon Game/scripts/claude_play'))
import mapdata

def words(raw):return struct.unpack('<%dH'%(len(raw)//2),raw)

def frozen_inputs(repo,pins,read=lambda p:p.read_bytes()):
    """CI's shallow checkout need not fetch history to verify frozen packets.

    The production CLI still reads immutable Git revisions. Tests bind all
    checked-out inputs to the actual receipt's hashes, with no silent fallback.
    """
    files={}
    for name in c.NAMES:
        coast=name=='PokmonLeague'
        folder=repo/c.PREFIX/('sunyshore-coast' if coast else 'victory-road-shell')/'staged'/name
        for suffix in ('map.bin','border.bin','map.json','attributes.json','averon.png'):
            filename='averon-map.bin' if coast and suffix=='map.bin' else 'averon-border.bin' if coast and suffix=='border.bin' else suffix
            files[name+'/'+suffix]=read(folder/filename)
    for bank in ('primary','secondary'):
        files['league-'+bank+'-attributes.bin']=read(repo/c.PREFIX/'sunyshore-coast/outdoor-family'/(bank+'-attributes.bin'))
    if set(files)!=set(pins):raise ValueError('exact frozen source packet set required')
    if any(hashlib.sha256(v).hexdigest()!=pins[p] for p,v in files.items()):raise ValueError('frozen source packet hash differs')
    return files

class ConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pins=json.loads((PACKET/'connected-receipt.json').read_text())['input_sha256']
        cls.inputs=frozen_inputs(ROOT,cls.pins)
        cls.general=(ENGINE/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes()
        cls.cave=(ENGINE/'data/tilesets/secondary/cave/metatile_attributes.bin').read_bytes()
        cls.output,cls.changes=c.couple(cls.inputs,cls.cave,cls.general)
        cls.names=mapdata._behavior_names(ENGINE)

    def test_only_two_authored_core_door_cells_change_coast_and_other_floors_identical(self):
        before=words(self.inputs['SinnohVictoryRoad_1F/map.bin']);after=words(self.output['SinnohVictoryRoad_1F/map.bin'])
        changed=[(i%52,i//52,x,y) for i,(x,y) in enumerate(zip(before,after)) if x!=y]
        self.assertEqual(changed,[(34,5,0xC00|521,532),(15,78,0xC00|521,532)])
        for n in ('PokmonLeague','SinnohVictoryRoad_2F','SinnohVictoryRoad_B1F'):
            for f in ('map.bin','border.bin','averon.png'):self.assertEqual(self.output[n+'/'+f],self.inputs[n+'/'+f])
        for n in ('SinnohVictoryRoad_2F','SinnohVictoryRoad_B1F'):
            for f in ('map.json','attributes.json'):self.assertEqual(self.output[n+'/'+f],self.inputs[n+'/'+f])
        self.assertEqual(self.output['SinnohVictoryRoad_1F/border.bin'],self.inputs['SinnohVictoryRoad_1F/border.bin'])

    def test_all_six_existing_stairs_and_eight_reciprocal_portal_pairs_preserved(self):
        headers={n:json.loads(self.output[n+'/map.json']) for n in c.NAMES};byid={h['id']:h for h in headers.values()}
        original=json.loads(self.inputs['SinnohVictoryRoad_1F/map.json'])
        self.assertEqual(original['warp_events'],headers['SinnohVictoryRoad_1F']['warp_events'][:6])
        total=0
        for h in headers.values():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])
            for i,p in enumerate(h['warp_events']):
                other=byid[p['dest_map']]['warp_events'][int(p['dest_warp_id'])]
                self.assertEqual(other['dest_map'],h['id']);self.assertEqual(int(other['dest_warp_id']),i);total+=1
        self.assertEqual(total,16)
        self.assertEqual([p['ds_1f_canonical_index'] for p in self.changes],[7,8])
        self.assertEqual([(p['x'],p['y']) for p in headers['PokmonLeague']['warp_events']],[(21,58),(23,41)])
        self.assertEqual(headers['PokmonLeague']['connections'],json.loads(self.inputs['PokmonLeague/map.json'])['connections'])

    def test_source_native_doors_and_both_dry_arrival_approaches_have_correct_behavior(self):
        for n,w in [('PokmonLeague',33),('SinnohVictoryRoad_1F',52)]:
            raw=words(self.output[n+'/map.bin']);attrs=json.loads(self.output[n+'/attributes.json'])['used_source_attribute_words']
            h=json.loads(self.output[n+'/map.json']);ports=h['warp_events'] if n=='PokmonLeague' else h['warp_events'][6:]
            for p in ports:
                door=raw[p['y']*w+p['x']];standing=raw[(p['y']+1)*w+p['x']]
                self.assertEqual(door&0xC00,0);self.assertEqual(attrs[str(door&1023)]&511,0x60)
                self.assertEqual(standing&0xC00,0);self.assertEqual(standing>>12,3)
                self.assertNotIn('WATER',self.names[attrs[str(standing&1023)]&511])

    def test_source_dry_graph_connects_actual_lower_and_upper_league_doors_via_core(self):
        dimensions={'PokmonLeague':(33,69),'SinnohVictoryRoad_1F':(52,84),'SinnohVictoryRoad_2F':(32,32),'SinnohVictoryRoad_B1F':(40,52)}
        maps={n:words(self.output[n+'/map.bin']) for n in c.NAMES}
        attrs={n:json.loads(self.output[n+'/attributes.json'])['used_source_attribute_words'] for n in c.NAMES}
        headers={n:json.loads(self.output[n+'/map.json']) for n in c.NAMES};byid={h['id']:n for n,h in headers.items()}
        def walk(n,x,y):
            w,h=dimensions[n]
            if not 0<=x<w or not 0<=y<h:return False
            v=maps[n][y*w+x];b=self.names[attrs[n][str(v&1023)]&511]
            return not v&0xC00 and 'WATER' not in b and not b.startswith('MB_JUMP') and b!='MB_COUNTER'
        start=('PokmonLeague',21,59);goal=('PokmonLeague',23,42);seen={start};queue=deque([start])
        while queue:
            n,x,y=queue.popleft();nexts=[(n,x+dx,y+dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) if walk(n,x+dx,y+dy)]
            for p in headers[n]['warp_events']:
                if (x,y)!=(p['x'],p['y']+1):continue
                dest=byid[p['dest_map']];other=headers[dest]['warp_events'][int(p['dest_warp_id'])]
                # Nonanimated doors arrive below. Native ladders arrive on tile.
                v=maps[dest][other['y']*dimensions[dest][0]+other['x']]
                yy=other['y']+(attrs[dest][str(v&1023)]&511==0x60)
                nexts.append((dest,other['x'],yy))
            for state in nexts:
                if state not in seen:seen.add(state);queue.append(state)
        self.assertIn(goal,seen)

    def test_actual_packet_matches_receipt_no_fake_new_scene_acceptance(self):
        r=json.loads((PACKET/'connected-receipt.json').read_text())
        self.assertEqual(r['status'],'SOURCE_COUPLING_ONLY_NOT_ROM_OR_NATURAL_TRAVEL_ACCEPTANCE')
        import hashlib
        for p,h in r['output_sha256'].items():self.assertEqual(hashlib.sha256((PACKET/'connected'/p).read_bytes()).hexdigest(),h)
        self.assertEqual(r['core_changes'],self.changes)

    def test_frozen_fixture_needs_no_git_history_but_rejects_tampering_and_bad_set(self):
        with patch.object(c,'read_packet',side_effect=AssertionError('history must not be consulted')):
            self.assertEqual(frozen_inputs(ROOT,self.pins),self.inputs)
        def altered(path):
            data=path.read_bytes()
            return bytes([data[0]^1])+data[1:] if path.name=='averon-map.bin' else data
        with self.assertRaisesRegex(ValueError,'hash differs'):frozen_inputs(ROOT,self.pins,altered)
        with self.assertRaisesRegex(ValueError,'packet set'):frozen_inputs(ROOT,{})

    def test_altered_existing_warp_door_behavior_or_sealed_anchor_refused(self):
        for kind in ('events','outside','sealed','native'):
            f=dict(self.inputs);ca=self.cave
            if kind=='events':
                h=json.loads(f['PokmonLeague/map.json']);h['warp_events']=[{}];f['PokmonLeague/map.json']=c.encode(h)
            elif kind=='outside':
                raw=bytearray(f['PokmonLeague/map.bin']);raw[2*(58*33+21)+1]^=4;f['PokmonLeague/map.bin']=bytes(raw)
            elif kind=='sealed':
                raw=bytearray(f['SinnohVictoryRoad_1F/map.bin']);raw[2*(78*52+15)]^=1;f['SinnohVictoryRoad_1F/map.bin']=bytes(raw)
            else:
                raw=bytearray(ca);raw[40]^=1;ca=bytes(raw)
            with self.subTest(kind=kind),self.assertRaises(ValueError):c.couple(f,ca,self.general)
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'new off-engine'):c.build(ROOT,ENGINE,Path(t))
            with self.assertRaisesRegex(ValueError,'new off-engine'):c.build(ROOT,ENGINE,ENGINE/'forbidden-connected')

if __name__=='__main__':unittest.main()
