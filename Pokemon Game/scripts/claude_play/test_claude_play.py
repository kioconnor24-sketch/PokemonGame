#!/usr/bin/env python3
"""Offline tests for the playthrough harness (no emulator, no ROM).

Map tests use the repository's real map sources. Everything else uses
SYNTHETIC fixtures, which test the harness only and are never gameplay
evidence.
"""
import json
import pathlib
import struct
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parents[1] / "engine"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "coordination"))

import driver  # noqa: E402
import emu  # noqa: E402
import evidence  # noqa: E402
import mapdata  # noqa: E402
import run  # noqa: E402

WORLD = mapdata.World(ENGINE)


def bare_driver():
    d = driver.Driver.__new__(driver.Driver)
    d.w = WORLD
    return d


class MapTests(unittest.TestCase):
    def test_route_exits_and_warps(self):
        self.assertTrue(mapdata.edge_exits(WORLD.map("MAP_SALTMERE"), "up"))
        self.assertFalse(mapdata.edge_exits(WORLD.map("MAP_SALTMERE"), "down"))
        d = bare_driver()
        clinic = WORLD.map("MAP_ALDERFIELDCLINIC")
        self.assertEqual(d.warp_push(clinic, (7, 8)), "down")
        self.assertEqual(d.warp_push(WORLD.map("MAP_ALDERFIELD"), (17, 12)), "up")

    def test_bfs_reaches_nurse_counter_and_refuses_walls(self):
        clinic = WORLD.map("MAP_ALDERFIELDCLINIC")
        self.assertIsNotNone(mapdata.bfs(clinic, (7, 7), {(7, 4)}))
        self.assertFalse(clinic.walkable(7, 3))  # the counter
        self.assertIsNone(mapdata.bfs(clinic, (7, 7), {(7, 1)}, allow_goal_unwalkable=False))

    def test_live_grid_opens_the_gym_gate(self):
        gym = WORLD.map("MAP_ALDERFIELDGYM")
        self.assertFalse(gym.walkable(4, 9))
        self.assertIsNone(mapdata.bfs(gym, (4, 14), {(4, 5)}))
        blocks = list(gym.blocks)
        blocks[9 * gym.width + 4] = 513  # setmetatile 4, 9, 513, FALSE
        live = gym.with_live_blocks(blocks)
        self.assertTrue(live.walkable(4, 9))
        self.assertIsNotNone(mapdata.bfs(live, (4, 14), {(4, 5)}))
        self.assertFalse(gym.walkable(4, 9))  # the static map is unchanged

    def test_map_route_and_unreachable_map(self):
        d = bare_driver()
        legs = d.map_route("MAP_SALTMEREHOME", "MAP_ALDERFIELDGYM")
        self.assertEqual(legs[0][0], "MAP_SALTMEREHOME")
        self.assertEqual(legs[-1][:2], ("MAP_ALDERFIELD", "warp"))
        with self.assertRaises(driver.Stuck):
            d.map_route("MAP_AVERONFIELDLAB", "MAP_SALTMERE")


class FakeGame:
    def __init__(self, flags):
        self.flags = flags

    def observation(self):
        return dict(flags=dict(self.flags), party=[], pokeBalls=[], berries=[])


class FakeEmu:
    def __init__(self, outdir):
        self.outdir = outdir
        self.n = 0

    def capture(self, label):
        self.n += 1
        path = self.outdir / f"{self.n:04d}-{label}.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"SYNTHETIC")
        return path


class FakeDriver:
    def __init__(self, outdir, flags):
        self.g = FakeGame(flags)
        self.e = FakeEmu(outdir)
        self.events = []

    def shot(self, label):
        return self.e.capture(label)

    def log(self, event, **data):
        self.events.append((event, data))


class ObserveTests(unittest.TestCase):
    def test_matching_expectation_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = FakeDriver(pathlib.Path(tmp), {"FLAG_BADGE01_GET": True})
            obs = run.observe(d, "badge", {"FLAG_BADGE01_GET": True})
            self.assertEqual(obs["problems"], [])

    def test_mismatch_fails_closed_and_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            d = FakeDriver(out, {"FLAG_BADGE01_GET": False})
            with self.assertRaises(run.ExpectationFailed):
                run.observe(d, "badge", {"FLAG_BADGE01_GET": True})
            state = json.loads((out / "state-badge.json").read_text())
            self.assertTrue(state["problems"])

    def test_missing_flag_is_a_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = FakeDriver(pathlib.Path(tmp), {})
            with self.assertRaises(run.ExpectationFailed):
                run.observe(d, "badge", {"FLAG_BADGE01_GET": True})


class TraceTests(unittest.TestCase):
    def test_every_key_transition_is_traced_with_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = emu.Emulator.__new__(emu.Emulator)
            sent = []
            e._key = lambda name, down: sent.append((name, down))
            frames = iter([100, 107])
            e.frame = lambda: next(frames)
            e.start_trace(pathlib.Path(tmp) / "inputs.jsonl", 0)
            e.key("A", True)
            e.key("A", False)
            e.trace.close()
            lines = [json.loads(l) for l in (pathlib.Path(tmp) / "inputs.jsonl").read_text().splitlines()]
            self.assertEqual(sent, [("A", True), ("A", False)])
            self.assertEqual([(l["key"], l["down"], l["frame"]) for l in lines],
                             [("A", True, 100), ("A", False, 107)])


def synthetic_run(root, name, *, source="a" * 40, rom="b" * 64, dirty=False,
                  problems=(), screenshot=True, trace=True):
    """SYNTHETIC run directory for harness tests only."""
    run_dir = root / name
    run_dir.mkdir(parents=True)
    (run_dir / "provenance-start.json").write_text(json.dumps(dict(
        source_sha=source, rom_sha256=rom, engine_dirty=dirty, synthetic=True)))
    if trace:
        (run_dir / "inputs.jsonl").write_text('{"key": "A", "down": true, "frame": 1}\n')
    if screenshot:
        (run_dir / "0001-badge.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"SYNTHETIC")
    (run_dir / "state-badge.json").write_text(json.dumps(dict(
        label="badge", screenshot="0001-badge.png", flags={"FLAG_BADGE01_GET": True},
        expected={"FLAG_BADGE01_GET": True}, problems=list(problems))))
    return run_dir


class EvidenceTests(unittest.TestCase):
    def test_complete_package_is_ready_for_review_not_pass(self):
        import qa_evidence_report
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1")
            manifest = evidence.build({"Q1": [("r1", ["badge"])]}, root)
            report = qa_evidence_report.inspect_package(manifest, root)
            status = report["cases"][0]["evidence_status"]
            self.assertEqual(status, "READY_FOR_INDEPENDENT_REVIEW")
            self.assertNotIn("PASS", status)

    def test_missing_pieces_fail_closed(self):
        cases = [dict(screenshot=False), dict(trace=False), dict(dirty=True),
                 dict(problems=["FLAG_BADGE01_GET: expected True, observed False"])]
        for kwargs in cases:
            with self.subTest(**{k: str(v) for k, v in kwargs.items()}):
                with tempfile.TemporaryDirectory() as tmp:
                    root = pathlib.Path(tmp)
                    synthetic_run(root, "r1", **kwargs)
                    with self.assertRaises(evidence.EvidenceError):
                        evidence.build({"Q1": [("r1", ["badge"])]}, root)

    def test_runs_from_different_builds_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1")
            synthetic_run(root, "r2", rom="c" * 64)
            with self.assertRaises(evidence.EvidenceError):
                evidence.build({"Q1": [("r1", ["badge"]), ("r2", ["badge"])]}, root)

    def test_missing_state_label_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1")
            with self.assertRaises(evidence.EvidenceError):
                evidence.build({"Q1": [("r1", ["badge", "reward"])]}, root)


if __name__ == "__main__":
    unittest.main()
