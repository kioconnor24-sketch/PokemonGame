"""Match native ForcedMovement_MuddySlope for the driver's on-foot plans."""
import importlib.util
from pathlib import Path
import struct
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("mud_fixture", Path(__file__).with_name("test_sinnoh_arrow_warp_pathfinding.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
md, qa = fixtures.md, fixtures.qa


class Strip:
    def __init__(self, mud=True): self.mud = mud
    def inside(self, x, y): return x == 0 and 0 <= y < 4
    def walkable(self, x, y): return self.inside(x, y)
    def elevation(self, x, y): return 3
    def warp_at(self, x, y): return None
    def behavior(self, x, y): return "MB_MUDDY_SLOPE" if self.mud and y in (1, 2) else "MB_NORMAL"


class MuddySlopePathfindingTest(unittest.TestCase):
    def test_uphill_is_not_an_ordinary_foot_path(self):
        m = Strip()
        self.assertIsNone(md.bfs(m, (0, 3), {(0, 0)}, elevation=3))
        self.assertNotIn((0, 0), md.reach_states(m, (0, 3), elevation=3))
        self.assertNotIn((0, 2), list(qa.moves(m, 0, 3)))

    def test_downhill_and_plain_floor_paths_remain_available(self):
        self.assertEqual(md.bfs(Strip(), (0, 0), {(0, 3)}, elevation=3), ["down"] * 3)
        self.assertEqual(md.bfs(Strip(False), (0, 3), {(0, 0)}, elevation=3), ["up"] * 3)

    def test_actual_route207_muddy_neck_cannot_be_climbed_on_foot(self):
        family = ROOT / "Averon_Codex_Handoff/design/sinnoh/oreburgh-donor/city-family"
        m = md.MapInfo.__new__(md.MapInfo)
        m.width, m.height = 64, 32
        m.blocks = struct.unpack("<2048H", (family / "Route207/map.bin").read_bytes())
        for label in ("primary", "secondary"):
            raw = (family / f"banks/{label}/metatile_attributes.bin").read_bytes()
            setattr(m, "_" + label, struct.unpack("<%dH" % (len(raw) // 2), raw))
        m.world = types.SimpleNamespace(behavior_names=md._behavior_names(ROOT / "engine"))
        m._derive_behaviors()
        m.triggers, m.warps = set(), []
        for y in (14, 15): self.assertEqual(m.behavior(18, y), "MB_MUDDY_SLOPE")
        self.assertIsNone(md.bfs(m, (18, 16), {(18, 13)}, elevation=3))
        self.assertNotIn((18, 13), md.reach_states(m, (18, 16), elevation=3))
        self.assertEqual(md.bfs(m, (18, 13), {(18, 16)}, elevation=3), ["down"] * 3)


if __name__ == "__main__": unittest.main()
