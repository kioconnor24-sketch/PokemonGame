"""Source-grounded Route208 bridge and guarded graphical navigation tests."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import types
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/hearthome-solaceon'
spec=importlib.util.spec_from_file_location('central_height_qa',HERE/'run_runtime_qa.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)


class Strip:
    def __init__(self,heights,arrow=None):self.heights=heights;self.arrow=arrow
    def inside(self,x,y):return x==0 and 0<=y<len(self.heights)
    def elevation(self,x,y):return self.heights[y]
    def walkable(self,x,y):return self.inside(x,y)
    def warp_at(self,x,y):return ('MAP_OTHER',0) if y==self.arrow else None
    def behavior(self,x,y):return 'MB_SOUTH_ARROW_WARP' if y==self.arrow else 'MB_NORMAL'


class CentralNavigation(unittest.TestCase):
    def test_actual_source_upper_bridge_both_directions_and_stable_layer(self):
        raw=(HERE/'staged/Route208/averon-map.bin').read_bytes()
        cells=struct.unpack('<2584H',raw)
        heights=[cells[y*68+22]>>12 for y in range(12,22)]
        self.assertEqual(heights,[4]+[15]*8+[4])
        self.assertTrue(all(((cells[y*68+22]>>10)&3)==0 for y in range(12,22)))
        m=Strip(heights)
        self.assertEqual(qa.elevation_path(m,(0,0),{(0,9)},start_elevation=4),['down']*9)
        self.assertEqual(qa.elevation_path(m,(0,9),{(0,0)},start_elevation=4),['up']*9)
        self.assertIsNone(qa.elevation_path(m,(0,0),{(0,9)},start_elevation=3))

    def test_real_lower_soil_probe_keeps_elevation_three(self):
        cells=struct.unpack('<2584H',(HERE/'staged/Route208/averon-map.bin').read_bytes())
        heights=[cells[y*68+14]>>12 for y in range(16,20)]
        self.assertEqual(heights,[3]*4)
        self.assertEqual(qa.elevation_path(Strip(heights),(0,0),{(0,3)},start_elevation=3),['down']*3)

    def test_fifteen_does_not_permit_layer_change_or_collision(self):
        self.assertIsNone(qa.elevation_path(Strip([4,15,15,3]),(0,0),{(0,3)},start_elevation=4))
        m=Strip([4,15,15,4]);m.walkable=lambda x,y:m.inside(x,y) and y!=2
        self.assertIsNone(qa.elevation_path(m,(0,0),{(0,3)},start_elevation=4))
        self.assertIsNone(qa.elevation_path(Strip([4,15,4]),(0,0),{(0,2)},blocked={(0,1)},start_elevation=4))

    def test_zero_elevation_is_native_transition(self):
        self.assertEqual(qa.elevation_path(Strip([4,0,3]),(0,0),{(0,2)},start_elevation=4),['down']*2)
        with self.assertRaises(ValueError):qa.elevation_path(Strip([4]),(0,0),{(0,0)},start_elevation=16)

    def test_current_arrow_direction_is_not_an_ordinary_step(self):
        m=Strip([3,3,3],arrow=1)
        self.assertIsNone(qa.elevation_path(m,(0,1),{(0,2)},start_elevation=3))
        self.assertEqual(qa.elevation_path(m,(0,1),{(0,0)},start_elevation=3),['up'])

    def test_missing_marker_changed_hash_and_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=b'original';(root/'source').write_bytes(data)
            recipe=dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',files={'source':hashlib.sha256(data).hexdigest()})
            with self.assertRaises(ValueError):qa.validate_source(root,recipe)
            (root/'.map_qa_throwaway').touch();qa.validate_source(root,recipe)
            (root/'source').write_bytes(b'changed')
            with self.assertRaises(ValueError):qa.validate_source(root,recipe)
            recipe['files']={'../escape':'irrelevant'}
            with self.assertRaises(ValueError):qa.validate_source(root,recipe)

    def test_compiler_derived_elevations_read_real_object_slots(self):
        raw=bytearray(16*8);raw[2*8]=1;raw[2*8+2]=4;raw[7*8]=1;raw[7*8+1]=99;raw[7*8+2]=4
        reads=[]
        def read(addr,count):
            reads.append((addr,count));return bytes([2]) if count==1 else bytes(raw)
        g=types.SimpleNamespace(off={'oe.size':8,'avatar.objectEventId':3,'oe.elevationByte':2,'oe.localId':1},
            sym={'gPlayerAvatar':100,'gObjectEvents':200},c={'OBJ_EVENT_ID_FOLLOWER':99},gdb=types.SimpleNamespace(read=read))
        self.assertEqual(qa.observed_elevations(types.SimpleNamespace(g=g)),dict(player=4,follower=4))
        self.assertEqual(reads,[(103,1),(200,128)])


if __name__=='__main__':unittest.main()
