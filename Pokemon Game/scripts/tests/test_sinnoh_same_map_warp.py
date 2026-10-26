"""Source-pinned driver fixtures: coordinate transitions are not map-ID changes.

These exercise real QA helpers/checks, not an emulator or gameplay acceptance.
"""
import importlib.util
import json
from pathlib import Path
import struct
import sys
import types
import unittest

ROOT=Path(__file__).resolve().parents[3]
SCRIPTS=ROOT/'Pokemon Game/scripts/claude_play'
sys.path.insert(0,str(SCRIPTS))
import map_qa as qa
import mapdata

SOURCE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/forest-chateau/staged'


def source_map(name,width,height):
    folder=SOURCE/name;h=json.loads((folder/'map.json').read_text());attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
    m=mapdata.MapInfo.__new__(mapdata.MapInfo);m.width=width;m.height=height
    m.blocks=struct.unpack('<%dH'%(width*height),(folder/'map.bin').read_bytes())
    banks=[[0]*512,[0]*512]
    for mid,value in attrs.items():b,i=divmod(int(mid),512);banks[b][i]=value
    m._primary,m._secondary=banks;m.world=types.SimpleNamespace(behavior_names=mapdata._behavior_names(ROOT/'Pokemon Game/engine'))
    m._derive_behaviors();m.triggers=set()
    m.warps=[(w['x'],w['y'],w['dest_map'],int(w['dest_warp_id'])) for w in h['warp_events']]
    return h['id'],m


class DriverFixture:
    def __init__(self,start):self.position=start;self.shots=[]
    def here(self):return self.position
    def shot(self,name):self.shots.append(name)
    def log(self,*args,**kwargs):pass


class FixtureRunner(qa.Runner):
    def __init__(self,maps,map_id,point,wrong_out=False,wrong_return=False):
        self.point=point;self.mid=map_id;self.maps=maps;self.phase='out';self.presses=[];self.hooks=[]
        self.wrong_out=wrong_out;self.wrong_return=wrong_return;self.expected_return=None
        super().__init__(DriverFixture((map_id,tuple(point['tile']))),types.SimpleNamespace(map=maps.__getitem__),{},None)

    def go(self,map_id,tile,*args):
        self.d.position=(map_id,tuple(tile))
        if self.presses:self.phase='return'
        return True

    def press(self,direction,**kwargs):
        previous=[p for p in self.presses if p[0]==self.phase];self.presses.append((self.phase,direction))
        if previous:
            # A redundant press after teleport walks away. It must not be sent.
            mid,(x,y)=self.d.position;self.d.position=(mid,(x+1,y));return
        if self.phase=='out':
            dest=self.maps[self.point['dest']];index=self.point['dest_warp']
            target=qa.warp_arrive(dest,*dest.warps[index][:2]) if index<len(dest.warps) else (-10,-10)
            self.d.position=(self.point['dest'],(-10,-10) if self.wrong_out else target)
        else:
            self.d.position=(self.mid,(-10,-10) if self.wrong_return else self.expected_return)

    def wait_settled(self,*args):return self.d.here()
    def follower(self,label):self.hooks.append(('follower',label));return True
    def can_leave(self,label):self.hooks.append(('exit',label));return True


class SameMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps=dict([source_map('OldChateau_2F',38,14),source_map('OldChateau_Entrance',19,17)])
        cls.mid='MAP_OLD_CHATEAU_2F';cls.m=cls.maps[cls.mid]

    def probe(self,index,**kwargs):
        x,y,dest,di=self.m.warps[index]
        p=dict(index=index,warp=[x,y],tile=qa.warp_stand(self.m,x,y),push=qa.warp_push(self.m,x,y),
               dest=dest,dest_warp=di,kind='warp',exit=mapdata.takeable(self.m,x,y))
        runner=FixtureRunner(self.maps,self.mid,p,**kwargs)
        runner.expected_return=qa.warp_arrive(self.m,x,y)
        return runner,p

    def test_all_15_actual_same_map_events_stop_after_one_push_each_way(self):
        indices=[i for i,w in enumerate(self.m.warps) if w[2]==self.mid]
        self.assertEqual(len(self.m.warps),17);self.assertEqual(len(indices),15)
        for index in indices:
            with self.subTest(event=index):
                r,p=self.probe(index);self.assertTrue(r.warp(self.mid,p))
                self.assertEqual(len(r.presses),2)
                self.assertEqual([h[0] for h in r.hooks],['follower','exit','follower'])
                self.assertEqual(r.checks[-1]['leg'],'back');self.assertTrue(r.checks[-1]['ok'])

    def test_both_external_stair_events_keep_the_same_inter_map_contract(self):
        indices=[i for i,w in enumerate(self.m.warps) if w[2]!=self.mid];self.assertEqual(indices,[0,1])
        for index in indices:
            r,p=self.probe(index);self.assertTrue(r.warp(self.mid,p));self.assertEqual(len(r.presses),2)

    def test_wrong_same_map_arrival_still_fails_before_follower_or_exit_claim(self):
        r,p=self.probe(2,wrong_out=True);self.assertFalse(r.warp(self.mid,p))
        self.assertEqual(r.checks[-1]['leg'],'in');self.assertFalse(r.checks[-1]['ok']);self.assertFalse(r.hooks)

    def test_wrong_same_map_return_still_fails_exact_original_group(self):
        r,p=self.probe(2,wrong_return=True);self.assertFalse(r.warp(self.mid,p))
        self.assertEqual(r.checks[-1]['leg'],'back');self.assertFalse(r.checks[-1]['ok'])
        self.assertEqual([h[0] for h in r.hooks],['follower','exit'])

    def test_invalid_destination_warp_cannot_pass(self):
        r,p=self.probe(2);p['dest_warp']=999;self.assertFalse(r.warp(self.mid,p));self.assertFalse(r.checks[-1]['ok'])

    def test_same_map_region_entry_stops_at_actual_destination_coordinate(self):
        r,p=self.probe(2);p['kind']='warp';r.plan={self.mid:dict(points=[p])}
        target=qa.warp_arrive(self.m,*self.m.warps[p['dest_warp']][:2])
        self.assertTrue(r.enter_region(self.mid,target,0))
        self.assertEqual(r.d.here(),(self.mid,target));self.assertEqual(len(r.presses),1)

    def test_same_map_region_entry_rejects_a_teleport_to_the_wrong_room(self):
        r,p=self.probe(2,wrong_out=True);p['kind']='warp';r.plan={self.mid:dict(points=[p])}
        target=qa.warp_arrive(self.m,*self.m.warps[p['dest_warp']][:2])
        self.assertFalse(r.enter_region(self.mid,target,0))


if __name__=='__main__':unittest.main()
