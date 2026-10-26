"""W28 production-door interiors: committed staging is self-consistent; doors and rooms reciprocal; neutral rooms."""
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/production-interiors"
ENGINE = ROOT / "engine"
DOORS = {"FloaromaTown_FlowerShop": ("FloaromaTown", (22, 13)), "FloaromaTown_House1": ("FloaromaTown", (13, 16)),
         "FloaromaTown_Mart": ("FloaromaTown", (26, 19)), "FloaromaTown_House2": ("FloaromaTown", (26, 28)),
         "FloaromaMeadow_House": ("FloaromaMeadow", (35, 41))}


class ProductionInteriorsTest(unittest.TestCase):
    """The donor is not in the repository: these check the committed output."""

    def test_overlays_only_append_door_warps(self):
        for town in ("FloaromaTown", "FloaromaMeadow"):
            new = json.loads((HERE / f"staged/{town}-dev-overlay/map.json").read_text())
            old = json.loads((ENGINE / f"data/maps/{town}/map.json").read_text())
            self.assertEqual(new["warp_events"][:len(old["warp_events"])], old["warp_events"])
            self.assertEqual({k: v for k, v in new.items() if k != "warp_events"},
                             {k: v for k, v in old.items() if k != "warp_events"})
            added = {(w["x"], w["y"]) for w in new["warp_events"][len(old["warp_events"]):]}
            self.assertEqual(added, {d for t, d in DOORS.values() if t == town})

    def test_doors_and_rooms_are_reciprocal(self):
        towns = {t: json.loads((HERE / f"staged/{t}-dev-overlay/map.json").read_text())
                 for t in ("FloaromaTown", "FloaromaMeadow")}
        for room, (town, door) in DOORS.items():
            r = json.loads((HERE / f"staged/{room}/map.json").read_text())
            w = next(w for w in towns[town]["warp_events"] if (w["x"], w["y"]) == door)
            self.assertEqual(w["dest_map"], r["id"])
            self.assertEqual(r["warp_events"][int(w["dest_warp_id"])]["dest_map"], towns[town]["id"])
            back = towns[town]["warp_events"][int(r["warp_events"][0]["dest_warp_id"])]
            self.assertEqual((back["x"], back["y"]), door)

    def test_rooms_are_neutral_and_use_this_batchs_tilesets(self):
        tilesets = json.loads((HERE / "staged/tilesets.json").read_text())
        symbols = {"gTileset_" + t["symbol"] for t in tilesets}
        for room in DOORS:
            r = json.loads((HERE / f"staged/{room}/map.json").read_text())
            self.assertEqual((r["object_events"], r["coord_events"], r["bg_events"]), ([], [], []))
            self.assertEqual(r["region_map_section"], "MAPSEC_PENDING_OWNER")
            layout = json.loads((HERE / f"staged/{room}/layout.json").read_text())
            self.assertEqual({layout["primary_tileset"], layout["secondary_tileset"]}, symbols)
            raw = (HERE / f"staged/{room}/map.bin").read_bytes()
            self.assertEqual(len(raw), 2 * layout["width"] * layout["height"])

    def test_adapted_rooms_keep_the_donor_physics(self):
        for room in DOORS:
            src = (HERE / f"source/staged/{room}/map.bin").read_bytes()
            new = (HERE / f"staged/{room}/map.bin").read_bytes()
            a = struct.unpack("<%dH" % (len(src) // 2), src)
            b = struct.unpack("<%dH" % (len(new) // 2), new)
            self.assertEqual([c & 0xFC00 for c in a], [c & 0xFC00 for c in b], room)

    def test_tileset_banks_are_well_formed(self):
        for t in json.loads((HERE / "staged/tilesets.json").read_text()):
            records = (HERE / t["metatiles"]).read_bytes()
            attrs = (HERE / t["attributes"]).read_bytes()
            self.assertTrue(records and len(records) % 16 == 0 and len(records) <= 8192)
            self.assertEqual(len(attrs) * 8, len(records))


if __name__ == "__main__":
    unittest.main()
