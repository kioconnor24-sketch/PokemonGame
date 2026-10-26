"""W26 Lake Valor: the committed staging is self-consistent; the entrance joins Codex's Lakefront; the cave stays shut."""
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/lake-valor/staged"
EASTERN = ROOT / "Averon_Codex_Handoff/design/sinnoh/eastern-loop"


def cells(path):
    raw = path.read_bytes()
    return struct.unpack("<%dH" % (len(raw) // 2), raw)


class LakeValorTest(unittest.TestCase):
    """The donor is not in the repository: these check the committed output (build_lake_valor.py needs --donor-root)."""

    def setUp(self):
        self.lake = json.loads((HERE / "LakeValor/map.json").read_text())
        self.front = json.loads((HERE / "ValorLakefront-dev-overlay/map.json").read_text())
        self.blocks = cells(HERE / "LakeValor/map.bin")
        self.layout = json.loads((HERE / "LakeValor/layout.json").read_text())

    def test_layout_is_in_codex_eastern_family(self):
        self.assertEqual(self.layout, {"width": 48, "height": 52, "primary_tileset": "gTileset_General",
                                       "secondary_tileset": "gTileset_EasternDevOutdoorSecondary"})
        self.assertEqual(len(self.blocks), 48 * 52)
        self.assertEqual(len(cells(HERE / "LakeValor/border.bin")), 4)

    def test_entrance_warps_are_reciprocal(self):
        for a, b in ((self.lake, self.front), (self.front, self.lake)):
            for w in a["warp_events"]:
                if w["dest_map"] == b["id"]:
                    self.assertEqual(b["warp_events"][int(w["dest_warp_id"])]["dest_map"], a["id"])
        self.assertEqual([(w["x"], w["y"]) for w in self.lake["warp_events"]], [(40, 4), (40, 3)])

    def test_lakefront_only_gains_the_entrance(self):
        src = json.loads((EASTERN / "staged/ValorLakefront/map.json").read_text())
        self.assertEqual(self.front["warp_events"][:len(src["warp_events"])], src["warp_events"])
        self.assertEqual({k: v for k, v in self.front.items() if k != "warp_events"},
                         {k: v for k, v in src.items() if k != "warp_events"})
        before = cells(EASTERN / "staged/ValorLakefront/averon-map.bin")
        after = cells(HERE / "ValorLakefront-dev-overlay/map.bin")
        changed = [(i % 56, i // 56, a ^ b) for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual([(x, y) for x, y, _ in changed], [(41, 27), (41, 28)])
        self.assertTrue(all(d == 0x400 for _, _, d in changed))

    def test_island_cave_stays_closed_and_neutral(self):
        self.assertTrue(self.blocks[25 * 48 + 23] & 0xC00)
        self.assertNotIn((23, 25), [(w["x"], w["y"]) for w in self.lake["warp_events"]])
        self.assertEqual((self.lake["object_events"], self.lake["coord_events"], self.lake["bg_events"]), ([], [], []))
        self.assertEqual(self.lake["region_map_section"], "MAPSEC_PENDING_OWNER")

    def test_entrance_cells_walkable(self):
        for x, y in ((40, 3), (40, 4)):
            self.assertFalse(self.blocks[y * 48 + x] & 0xC00, (x, y))


if __name__ == "__main__":
    unittest.main()
