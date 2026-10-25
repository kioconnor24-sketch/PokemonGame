"""W2 south-west coast staging (Routes 219-221): pinned output, Averon-only art, seams and the Sandgem proposal.

Off-engine source checks. Rebuilding from the donor needs a donor checkout: set SINNOH_DONOR_ROOT to one at the
pinned revision to run that test as well (it is skipped otherwise).
"""
import importlib.util
import json
import os
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/southwest-coast"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("southwest_builder", HERE / "build_southwest.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}


def load(name):
    w, h, _ = b.MAPS[name]
    raw = (HERE / "staged" / name / "map.bin").read_bytes()
    return w, h, list(struct.unpack("<%dH" % (w * h), raw))


def engine_map(name, width):
    raw = (ENGINE / f"data/layouts/{name}/map.bin").read_bytes()
    return list(struct.unpack("<%dH" % (len(raw) // 2), raw)), width


class SouthwestCoastTest(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((HERE / "receipt.json").read_text())

    def test_staged_files_match_the_receipt(self):
        for name in b.MAPS:
            d = HERE / "staged" / name
            self.assertEqual(b.sha((d / "map.bin").read_bytes()), self.receipt[name]["output_sha256"])
            self.assertEqual(b.sha((d / "border.bin").read_bytes()), self.receipt[name]["border_sha256"])
            self.assertEqual(self.receipt[name]["git_blob"], b.MAPS[name][2])
            info, text = b.headers(name)
            self.assertEqual((d / "map.json").read_text(), info)
            self.assertEqual((d / "scripts.inc").read_text(), text)

    def test_only_averon_secondary_tiles_remain(self):
        house = {c & 1023 for row in b.dewford_house(ENGINE)[0] for c in row}
        for name in b.MAPS:
            allowed = set(b.SECONDARY.get(name, {}).values()) | (house if name == "Route221" else set())
            used = {c & 1023 for c in load(name)[2] if c & 1023 >= 512}
            self.assertLessEqual(used, allowed, name)

    def test_connections_are_reciprocal_without_twinleaf(self):
        for name in b.MAPS:
            for m, o, d in b.CONNECTIONS[name]:
                if m == "MAP_SANDGEM_TOWN":
                    self.assertEqual((b.SANDGEM_TO_219["offset"], b.SANDGEM_TO_219["direction"]), (-o, OPPOSITE[d]))
                    continue
                other = next(n for n in b.MAPS if "MAP_" + n.upper() == m)
                self.assertIn(("MAP_" + name.upper(), -o, OPPOSITE[d]), b.CONNECTIONS[other])
        self.assertFalse(any(m == "MAP_TWINLEAF_TOWN" for c in b.CONNECTIONS.values() for m, _, _ in c))

    def test_sandgem_seam_matches_cell_for_cell(self):
        sandgem, sw = engine_map("SandgemTown", 32)
        sh = len(sandgem) // sw
        w, _, route = load("Route219")
        offset = b.SANDGEM_TO_219["offset"]
        open_sandgem = {x for x in range(sw) if not sandgem[(sh - 1) * sw + x] & 0xC00}
        open_route = {x + offset for x in range(w) if not route[x] & 0xC00}
        self.assertEqual(open_sandgem, open_route)
        self.assertEqual(len(open_route), 6)
        for wrong in (offset - 1, offset + 1):                                # off by one leaves dead seam cells
            self.assertNotEqual(open_sandgem, {x + wrong for x in range(w) if not route[x] & 0xC00})

    def test_route221_building_is_a_closed_house_door_on_door(self):
        w, _, cells = load("Route221")
        _, x0, y0, x1, y1 = b.BUILDING
        door = cells[15 * w + 82]
        self.assertEqual(door & 1023, 549)
        house = {(b.HOUSE[0] + i, b.HOUSE[1] + j) for i in range(5) for j in range(4)}
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x, y) not in house:
                    self.assertTrue(cells[y * w + x] & 0xC00, (x, y))     # footprint stays solid
        self.assertFalse(cells[16 * w + 82] & 0xC00)                      # the yard in front of the door
        for x, y, _ in b.YARD:
            self.assertEqual(cells[y * w + x] & 1023, 1)

    @unittest.skipUnless(os.environ.get("SINNOH_DONOR_ROOT"), "set SINNOH_DONOR_ROOT to a pinned donor checkout")
    def test_rebuild_from_the_pinned_donor(self):
        donor = pathlib.Path(os.environ["SINNOH_DONOR_ROOT"])
        for name in b.MAPS:
            data, border, receipt = b.convert(donor, ENGINE, name)
            self.assertEqual(data, (HERE / "staged" / name / "map.bin").read_bytes())
            self.assertEqual(receipt["changed_cells"], self.receipt[name]["changed_cells"])


if __name__ == "__main__":
    unittest.main()
