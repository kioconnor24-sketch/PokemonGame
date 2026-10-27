"""compose_scene: several Codex DEV family scenes compose append-only into one; any conflict fails closed."""
import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPO = ROOT.parent
spec = importlib.util.spec_from_file_location("compose_scene", ROOT / "scripts/claude_play/compose_scene.py")
comp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comp)
FAMILIES = ["hearthome-solaceon", "eastern-loop", "celestic-north"]


def base(path):
    return (REPO / comp.ENGINE / path).read_bytes()


def fake(maps, tileset, extra_files=()):
    """A family scene appending MAPS (one layout each) and one tileset declaration to main."""
    groups, layouts = json.loads(base(comp.GROUPS)), json.loads(base(comp.LAYOUTS))
    group = groups["group_order"].index("gMapGroup_Sinnoh")
    registry = base(comp.REGISTRY).decode()
    files = {}
    for i, name in enumerate(maps, len(groups["gMapGroup_Sinnoh"])):
        files[f"data/maps/{name}/map.json"] = name.encode()
        registry += f"REGISTRY_SLOT({group}, {i}, MAP_{name.upper()}, {name}, 1)\n"
        layouts["layouts"].append({"id": f"LAYOUT_{name.upper()}", "name": f"{name}_Layout"})
    groups["gMapGroup_Sinnoh"] += maps
    files.update({comp.GROUPS: json.dumps(groups).encode(), comp.LAYOUTS: json.dumps(layouts).encode(),
                  comp.REGISTRY: registry.encode(),
                  "include/tilesets.h": base("include/tilesets.h") + f"extern const struct Tileset {tileset};\n".encode()})
    files.update(dict(extra_files))
    return files


class ComposeSceneTest(unittest.TestCase):
    def setUp(self):
        self.orig = comp.family_files

    def tearDown(self):
        comp.family_files = self.orig

    def test_real_families_compose_in_order(self):
        parts = {f: comp.family_files(REPO, f) for f in FAMILIES}
        comp.family_files = lambda repo, f: parts[f]
        files, receipt = comp.assemble(REPO, FAMILIES)
        prefix = json.loads(base(comp.GROUPS))["gMapGroup_Sinnoh"]
        expected = sum((json.loads(parts[f][comp.GROUPS])["gMapGroup_Sinnoh"][len(prefix):] for f in FAMILIES), [])
        self.assertEqual(json.loads(files[comp.GROUPS])["gMapGroup_Sinnoh"], prefix + expected)
        group = json.loads(base(comp.GROUPS))["group_order"].index("gMapGroup_Sinnoh")
        slots = re.findall(rf"REGISTRY_SLOT\({group}, (\d+), \w+, (\w+), 1\)", files[comp.REGISTRY].decode())
        self.assertEqual([(int(i), n) for i, n in slots], list(enumerate(prefix + expected)))
        for path in comp.APPEND:
            self.assertTrue(files[path].startswith(base(path)))
            for f in FAMILIES:
                self.assertIn(parts[f][path][len(base(path)):], files[path])
        for f in FAMILIES:
            for path, data in parts[f].items():
                if path not in comp.APPEND + (comp.GROUPS, comp.LAYOUTS, comp.REGISTRY):
                    self.assertEqual(files[path], data, path)

    def test_two_families_writing_one_file_differently_fail(self):
        parts = {"a": fake(["MapA"], "gTileset_A", {"data/shared.bin": b"1"}),
                 "b": fake(["MapB"], "gTileset_B", {"data/shared.bin": b"2"})}
        comp.family_files = lambda repo, f: parts[f]
        with self.assertRaisesRegex(ValueError, "differs between"):
            comp.assemble(REPO, ["a", "b"])

    def test_a_family_rewriting_an_index_file_fails(self):
        parts = {"a": fake(["MapA"], "gTileset_A"),
                 "b": fake(["MapB"], "gTileset_B", {"data/event_scripts.s": b"rewritten\n"})}
        comp.family_files = lambda repo, f: parts[f]
        with self.assertRaisesRegex(ValueError, "does not append"):
            comp.assemble(REPO, ["a", "b"])

    def test_a_tileset_declared_twice_fails(self):
        parts = {"a": fake(["MapA"], "gTileset_Same"), "b": fake(["MapB"], "gTileset_Same")}
        comp.family_files = lambda repo, f: parts[f]
        with self.assertRaisesRegex(ValueError, "declared twice"):
            comp.assemble(REPO, ["a", "b"])

    def test_fake_families_compose(self):
        parts = {"a": fake(["MapA"], "gTileset_A"), "b": fake(["MapB", "MapC"], "gTileset_B")}
        comp.family_files = lambda repo, f: parts[f]
        files, receipt = comp.assemble(REPO, ["a", "b"])
        self.assertEqual(receipt["maps"], ["MapA", "MapB", "MapC"])


if __name__ == "__main__":
    unittest.main()
