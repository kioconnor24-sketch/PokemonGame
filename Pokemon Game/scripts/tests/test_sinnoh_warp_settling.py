"""Warp inputs must wait for approach movement and re-read actual arrival."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("settling_source", Path(__file__).with_name("test_sinnoh_same_map_driver.py"))
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)


class MovingController(source.ControllerFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.in_flight = False
        self.events = []

    def walk_path(self, *args, **kwargs):
        result = super().walk_path(*args, **kwargs)
        self.in_flight = True  # coordinates update before animation finishes
        self.events.append("approach")
        return result

    def settle(self):
        self.in_flight = False
        self.events.append("settle")

    def step(self, direction, **kwargs):
        if self.in_flight:
            raise AssertionError("warp input issued before approach movement settled")
        self.events.append("push")
        return super().step(direction, **kwargs)


class WarpSettlingTest(unittest.TestCase):
    def fixtures(self, index):
        maps = dict([source.source.source_map("OldChateau_2F", 38, 14),
                     source.source.source_map("OldChateau_Entrance", 19, 17)])
        mid = "MAP_OLD_CHATEAU_2F"
        d = MovingController(maps, mid, index)
        return d, mid, maps[mid]

    def test_same_map_warp_approach_settles_before_exactly_one_push(self):
        d, mid, m = self.fixtures(3)
        d.go_map([(mid, "warp", m.warps[3][:2], d.warp_push(m, m.warps[3][:2]))])
        self.assertEqual(d.steps, [3])
        self.assertLess(d.events.index("settle"), d.events.index("push"))

    def test_external_warp_approach_settles_before_exactly_one_push(self):
        d, mid, m = self.fixtures(0)
        d.go_map([(mid, "warp", m.warps[0][:2], d.warp_push(m, m.warps[0][:2]))])
        self.assertEqual(d.steps, [0])
        self.assertLess(d.events.index("settle"), d.events.index("push"))

    def test_transition_during_settle_is_not_followed_by_an_extra_push(self):
        d, mid, m = self.fixtures(0)
        def settle():
            d.in_flight = False
            dest, warp = m.warps[0][2:]
            target = d.maps[dest]
            d.position = (dest, source.mapdata.warp_arrival(target, *target.warps[warp][:2]))
        d.settle = settle
        d.go_map([(mid, "warp", m.warps[0][:2], d.warp_push(m, m.warps[0][:2]))])
        self.assertEqual(d.steps, [])
        self.assertEqual(d.position[0], "MAP_OLD_CHATEAU_ENTRANCE")


if __name__ == "__main__": unittest.main()
