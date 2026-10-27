"""W5 Valley Windworks staging: receipt-pinned outputs, no donor turbine IDs, reciprocal DEV connections and warps."""
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/valley-windworks"
spec = importlib.util.spec_from_file_location("windworks", HERE / "build_windworks.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class WindworksTest(unittest.TestCase):
    def setUp(self):
        self.r = json.loads((HERE / "receipt.json").read_text())

    def test_outputs_match_receipt_and_headers(self):
        hdrs = b.headers()
        for src, name in b.OUT_NAME.items():
            d = HERE / "staged" / name
            self.assertEqual(b.sha((d / "map.bin").read_bytes()), self.r[name]["output_sha256"])
            self.assertEqual(json.loads((d / "map.json").read_text()), hdrs[src])

    def test_no_turbine_or_black_ids_remain(self):
        raw = (HERE / "staged/ValleyWindworks/map.bin").read_bytes()
        ids = {c & 1023 for c in struct.unpack("<%dH" % (len(raw) // 2), raw)}
        self.assertFalse(ids & set(b.TURBINE))
        self.assertNotIn(1020, ids)
        raw = (HERE / "staged/ValleyWindworks_Inside/map.bin").read_bytes()
        self.assertFalse({c & 1023 for c in struct.unpack("<%dH" % (len(raw) // 2), raw)} & {760, 761})

    def test_dev_overlay_connections_reciprocal(self):
        out = b.headers()["ValleyWindworks"]["connections"]
        for name in ("Route205_South", "Route205_North"):
            over = json.loads((HERE / "staged" / f"{name}-dev-overlay/map.json").read_text())
            back = [c for c in over["connections"] if c["map"] == "MAP_VALLEY_WINDWORKS"]
            self.assertEqual(len(back), 1)
            fwd = next(c for c in out if c["map"] == over["id"])
            self.assertEqual((back[0]["offset"], back[0]["direction"]), (-fwd["offset"], b.OPPOSITE[fwd["direction"]]))

    def test_warps_reciprocal(self):
        h = b.headers()
        self.assertEqual(h["ValleyWindworks"]["warp_events"][0]["dest_map"], "MAP_VALLEY_WINDWORKS_INSIDE")
        self.assertTrue(all(w["dest_map"] == "MAP_VALLEY_WINDWORKS" and w["dest_warp_id"] == "0"
                            for w in h["ValleyWindoworks_Indoor"]["warp_events"]))


class ScratchInstallerGuardTest(unittest.TestCase):
    """prepare_runtime.install refuses a dirty engine tree before writing anything (review 5646468435)."""

    def test_dirty_engine_tree_is_refused_and_clean_marked_tree_passes_the_guard(self):
        import importlib.util
        import subprocess
        import tempfile
        spec = importlib.util.spec_from_file_location("w5_runtime", HERE / "prepare_runtime.py")
        rt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rt)
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            git = lambda *a: subprocess.run(["git", "-C", tmp, *a], check=True, capture_output=True)
            git("init", "-q", "-b", "claude/windworks-scratch-test")
            git("config", "user.email", "t@example.invalid")
            git("config", "user.name", "t")
            eng = repo / "Pokemon Game/engine"
            (eng / "data/maps").mkdir(parents=True)
            tracked = eng / "data/maps/map_groups.json"
            tracked.write_text("{}\n")
            git("add", "-A")
            git("commit", "-qm", "base")
            (eng / ".map_qa_throwaway").write_text("")
            tracked.write_text('{"unique": "scratch work"}\n')
            with self.assertRaisesRegex(ValueError, "dirty engine tree"):
                rt.install(repo)
            self.assertEqual(tracked.read_text(), '{"unique": "scratch work"}\n')    # nothing overwritten
            git("checkout", "-q", "--", "Pokemon Game/engine/data/maps/map_groups.json")
            with self.assertRaises(Exception) as clean:                                  # past the guard: fails later
                rt.install(repo)
            self.assertNotIn("dirty", str(clean.exception))


if __name__ == "__main__":
    unittest.main()
