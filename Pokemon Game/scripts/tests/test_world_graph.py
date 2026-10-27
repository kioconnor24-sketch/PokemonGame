"""world_graph: production + staged maps and overlays form the expected joined groups."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("world_graph", ROOT / "scripts/claude_play/world_graph.py")
wg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wg)


def header(mid, warps=(), conns=()):
    return {"id": mid, "warp_events": [{"dest_map": d} for d in warps],
            "connections": [{"map": m, "offset": 0, "direction": "up"} for m in conns]}


class WorldGraphTest(unittest.TestCase):
    def tree(self, tmp, staged):
        root = pathlib.Path(tmp)
        eng = root / wg.ENGINE
        (eng / "data/maps/Town").mkdir(parents=True)
        (eng / "data/maps/map_groups.json").write_text(json.dumps({"gMapGroup_Sinnoh": ["Town"]}))
        (eng / "data/maps/Town/map.json").write_text(json.dumps(header("MAP_TOWN")))
        for rel, h in staged.items():
            path = root / wg.DESIGN / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(h))
        return root

    def test_overlays_join_staged_maps_to_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.tree(tmp, {
                "fam/staged/Route/map.json": header("MAP_ROUTE", warps=["MAP_HOUSE"]),
                "fam/staged/House/map.json": header("MAP_HOUSE", warps=["MAP_ROUTE"]),
                "fam/staged/Cave/map.json": header("MAP_CAVE"),
                "mine/staged/Town-dev-overlay/map.json": header("MAP_TOWN", conns=["MAP_ROUTE"]),
                "fam/runtime-recipe.json": {"source_headers": {"Lake": header("MAP_LAKE", conns=["MAP_CAVE"])}}})
            r = wg.report([root])
            self.assertEqual(r["maps"], 5)
            self.assertEqual([c["maps"] for c in r["components"]],
                             [["MAP_HOUSE", "MAP_ROUTE", "MAP_TOWN"], ["MAP_CAVE", "MAP_LAKE"]])
            self.assertEqual(r["components"][0]["production"], 1)
            self.assertEqual(r["links"], 3)

    def test_unknown_destinations_are_not_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.tree(tmp, {"fam/staged/Route/map.json": header("MAP_ROUTE", warps=["MAP_NOWHERE"])})
            r = wg.report([root])
            self.assertEqual((r["maps"], r["links"], len(r["components"])), (2, 0, 2))

    def test_the_repository_graph_loads(self):
        r = wg.report([ROOT.parent])
        self.assertEqual(r["production"], len(json.loads((ROOT / "engine/data/maps/map_groups.json").read_text())
                                              ["gMapGroup_Sinnoh"]))
        self.assertTrue(any(c["production"] == r["production"] for c in r["components"]))


if __name__ == "__main__":
    unittest.main()
