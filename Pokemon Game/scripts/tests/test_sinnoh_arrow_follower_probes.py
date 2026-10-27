"""Follower observation must not accidentally execute a directional warp."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "arrow_probe_fixtures", Path(__file__).with_name("test_sinnoh_arrow_warp_pathfinding.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
qa = fixtures.qa


class Controller:
    def __init__(self, m):
        self.m = m
        self.position = (1, 1)
        self.inputs = []

    def here(self): return "MAP_FIXTURE", self.position
    def live_map(self, mid): return self.m
    def log(self, *args, **kwargs): pass

    def step(self, direction):
        # Independent native-rule fixture: NORTH_ARROW_WARP at the current
        # tile warps on UP; this is never an ordinary observation step.
        if self.position == (1, 1) and self.m.event and direction == "up":
            raise AssertionError("follower probe activated the current north arrow warp")
        self.inputs.append(direction)
        dx, dy = qa.DIRS[direction]
        self.position = self.position[0] + dx, self.position[1] + dy
        return object()


class ArrowFollowerProbesTest(unittest.TestCase):
    def run_probe(self, method, event=True):
        m = fixtures.ArrowMap("MB_NORTH_ARROW_WARP", event=event)
        m.objects = []
        d = Controller(m)
        runner = qa.Runner(d, types.SimpleNamespace(map=lambda mid: m), {}, None)
        play = types.SimpleNamespace(observe=lambda *args: {"follower": {"invisible": False}})
        with mock.patch.dict(sys.modules, {"run": play}):
            ok = runner.follower("fixture") if method == "follower" else runner.follower_step()
        self.assertTrue(ok)
        self.assertEqual(d.position, (1, 1))
        return d.inputs

    def test_observation_avoids_the_current_north_arrow_warp(self):
        self.assertEqual(self.run_probe("follower"), ["down", "up"])

    def test_region_ui_movement_probe_avoids_the_current_north_arrow_warp(self):
        self.assertEqual(self.run_probe("follower_step"), ["down", "up"])

    def test_arrow_art_without_a_warp_event_keeps_the_original_probe(self):
        for method in ("follower", "follower_step"):
            with self.subTest(method=method):
                self.assertEqual(self.run_probe(method, event=False), ["up", "down"])


if __name__ == "__main__":
    unittest.main()
