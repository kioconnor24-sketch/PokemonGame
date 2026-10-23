"""Real Driver.go_map against pinned Chateau geometry, no emulator claim."""
import importlib.util
from pathlib import Path
import types
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('chateau_existing_driver_fixtures',HERE/'test_sinnoh_same_map_warp.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
import driver
import mapdata


class ControllerFixture(driver.Driver):
    def __init__(self,maps,mid,index,blocked_goals=()):
        self.maps=maps;self.w=types.SimpleNamespace(map=maps.__getitem__)
        self.blocked_goals=set(blocked_goals);self.steps=[];self.positions=[]
        self.position=(mid,self.warp_goal(maps[mid],maps[mid].warps[index][:2])[0])

    def here(self,*args):return self.position
    def log(self,*args,**kwargs):pass
    def settle(self):return None

    def walk_path(self,mid,goals,**kwargs):
        if self.position[0]!=mid:return self.position
        available=set(goals)-self.blocked_goals
        path=mapdata.bfs(self.maps[mid],self.position[1],available)
        if path is None:raise driver.Stuck('fixture: no actual source foot path')
        x,y=self.position[1]
        for direction in path:
            dx,dy=mapdata.DIRS[direction];x+=dx;y+=dy
        self.position=(mid,(x,y));return self.position

    def step(self,direction,**kwargs):
        mid,pos=self.position;m=self.maps[mid]
        for index,(x,y,dest,di) in enumerate(m.warps):
            if self.warp_goal(m,(x,y))==(pos,direction):
                self.steps.append(index);target=self.maps[dest]
                self.position=(dest,mapdata.warp_arrival(target,*target.warps[di][:2]))
                self.positions.append(self.position);return types.SimpleNamespace()
        raise AssertionError(('not an actual source warp controller step',mid,pos,direction))


class SameMapDriverTest(unittest.TestCase):
    def setUp(self):
        self.maps=dict([source.source_map('OldChateau_2F',38,14),source.source_map('OldChateau_Entrance',19,17)])
        self.mid='MAP_OLD_CHATEAU_2F';self.m=self.maps[self.mid]

    def execute(self,index,**kwargs):
        d=ControllerFixture(self.maps,self.mid,index,**kwargs)
        with mock.patch.object(driver.time,'sleep'):
            d.go_map([(self.mid,'warp',self.m.warps[index][:2],d.warp_push(self.m,self.m.warps[index][:2]))])
        return d

    def test_all15_real_self_map_events_stop_at_exact_arrival_after_one_input(self):
        ids=[i for i,w in enumerate(self.m.warps) if w[2]==self.mid];self.assertEqual(len(ids),15)
        for index in ids:
            with self.subTest(event=index):
                target=self.m.warps[index][3];expected=mapdata.warp_arrival(self.m,*self.m.warps[target][:2])
                d=self.execute(index);self.assertEqual(d.position,(self.mid,expected));self.assertEqual(d.steps,[index])

    def test_two_external_stairs_keep_original_single_input_behavior(self):
        for index in (0,1):
            d=self.execute(index);self.assertEqual(d.position[0],'MAP_OLD_CHATEAU_ENTRANCE');self.assertEqual(d.steps,[index])

    def test_paired_alternate_with_same_target_index_remains_usable(self):
        blocked=self.warp_goal(3)
        d=self.execute(3,blocked_goals={blocked})
        self.assertEqual(d.steps,[4])
        self.assertEqual(d.position,(self.mid,mapdata.warp_arrival(self.m,*self.m.warps[2][:2])))

    def test_other_rooms_are_not_interchangeable_same_map_destinations(self):
        # Hallway->room2 has no equivalent alternate. An unreachable source
        # must not be replaced by the reachable door into unrelated room1.
        d=self.execute(5,blocked_goals={self.warp_goal(5)})
        self.assertEqual(d.steps,[])

    def test_invalid_self_destination_rejected_before_any_controller_input(self):
        x,y,dest,_=self.m.warps[2];self.m.warps[2]=(x,y,dest,999)
        with self.assertRaises(driver.Stuck):self.execute(2)

    def warp_goal(self,index):return ControllerFixture(self.maps,self.mid,index).position[1]


if __name__=='__main__':unittest.main()
