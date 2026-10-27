"""Host walking plans must not walk through native current-tile arrow warps."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("arrow_mapdata", ROOT / "scripts/claude_play/mapdata.py")
md = importlib.util.module_from_spec(spec)
spec.loader.exec_module(md)
qa_spec = importlib.util.spec_from_file_location("arrow_map_qa", ROOT / "scripts/claude_play/map_qa.py")
qa = importlib.util.module_from_spec(qa_spec)
qa_spec.loader.exec_module(qa)


class ArrowMap:
    def __init__(self, behavior, event=True):
        self.arrow = behavior
        self.event = event

    def inside(self, x, y):
        return 0 <= x < 3 and 0 <= y < 3

    def walkable(self, x, y):
        return self.inside(x, y)

    def elevation(self, x, y):
        return 3

    def behavior(self, x, y):
        return self.arrow if (x, y) == (1, 1) else "MB_NORMAL"

    def warp_at(self, x, y):
        return ("MAP_OTHER", 0) if self.event and (x, y) == (1, 1) else None


class ArrowWarpPathfindingTest(unittest.TestCase):
    def test_all_four_current_arrow_directions_cannot_be_ordinary_steps(self):
        for word, direction in (("NORTH", "up"), ("SOUTH", "down"),
                                ("WEST", "left"), ("EAST", "right")):
            with self.subTest(direction=direction):
                m = ArrowMap("MB_" + word + "_ARROW_WARP")
                dx, dy = md.DIRS[direction]
                target = (1 + dx, 1 + dy)
                # Block alternate paths: this would be exactly one native warp input.
                blocked = {(x, y) for x in range(3) for y in range(3)} - {(1, 1), target}
                self.assertIsNone(md.bfs(m, (1, 1), {target}, blocked=blocked, elevation=3))
                self.assertNotIn(target, list(qa.moves(m, 1, 1)))

    def test_current_arrow_keeps_other_directions_available(self):
        m = ArrowMap("MB_NORTH_ARROW_WARP")
        self.assertEqual(md.bfs(m, (1, 1), {(1, 2)}, elevation=3), ["down"])
        self.assertEqual(md.bfs(m, (1, 1), {(0, 1)}, elevation=3), ["left"])

    def test_arrow_art_without_a_warp_event_is_an_ordinary_step(self):
        m = ArrowMap("MB_NORTH_ARROW_WARP", event=False)
        self.assertEqual(md.bfs(m, (1, 1), {(1, 0)}, elevation=3), ["up"])

    def test_actual_route206_pocket_is_not_reachable_by_walking_through_mat(self):
        folder = ROOT / "Averon_Codex_Handoff/design/sinnoh/eterna-cycle/staged/Route206"
        raw = (folder / "map.bin").read_bytes()
        cells = struct.unpack("<3360H", raw)
        attrs = json.loads((folder / "attributes.json").read_text())["used_source_attribute_words"]
        names = md._behavior_names(ROOT / "engine")
        header = json.loads((folder / "map.json").read_text())
        warps = {(w["x"], w["y"]) for w in header["warp_events"]}

        class SourceMap:
            def inside(self, x, y): return 0 <= x < 28 and 0 <= y < 120
            def walkable(self, x, y): return self.inside(x, y) and not cells[y * 28 + x] & 0xC00
            def elevation(self, x, y): return cells[y * 28 + x] >> 12
            def behavior(self, x, y): return names[attrs[str(cells[y * 28 + x] & 1023)] & 255]
            def warp_at(self, x, y): return ("MAP_OTHER", 0) if (x, y) in warps else None

        m = SourceMap()
        for x in (12, 13):
            with self.subTest(x=x):
                self.assertEqual(m.behavior(x, 102), "MB_NORTH_ARROW_WARP")
                self.assertIsNone(md.bfs(m, (x, 102), {(x, 101)}, elevation=3))
                self.assertNotIn((x, 101), md.reach_states(m, (x, 102), elevation=3))
                self.assertNotIn((x, 101), list(qa.moves(m, x, 102)))
                self.assertEqual(md.bfs(m, (x, 102), {(x, 103)}, elevation=3), ["down"])


if __name__ == "__main__":
    unittest.main()
