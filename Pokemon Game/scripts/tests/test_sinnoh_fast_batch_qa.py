"""Behavioral and negative checks for the opt-in Sinnoh fast QA runner."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock

PATH = Path(__file__).resolve().parents[1] / "sinnoh_fast_batch_qa.py"
spec = importlib.util.spec_from_file_location("sinnoh_fast_batch_qa", PATH)
fast = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fast)


class FakeWorld:
    def __init__(self, warps=None):
        self.warps = warps or {
            "A": [(2, 3, "B", 0)],
            "B": [(4, 5, "A", 0)],
        }

    def map(self, name):
        return SimpleNamespace(
            warps=self.warps[name],
            elevation=lambda x, y: 4 if y >= 10 else 3,
        )


class FakeDriver:
    current = ("A", (2, 3))

    def here(self):
        return self.current


class OriginalRunner:
    def __init__(self, world=None):
        self.w = world or FakeWorld()
        self.d = FakeDriver()
        self.plan = {name: {} for name in self.w.warps}
        self.warps_run = []
        self.followers_run = []
        self.next_warp_result = True
        self.next_follower_result = True

    def warp(self, source, point):
        self.warps_run.append((source, point["index"]))
        return self.next_warp_result

    def follower(self, label):
        self.followers_run.append(label)
        return self.next_follower_result


class FastBatchTests(TestCase):
    def setup_runner(self, world=None):
        class Runner(OriginalRunner):
            pass
        qa = SimpleNamespace(Runner=Runner)
        fast.install_batch_mode(qa)
        return qa.Runner(world)

    def test_unique_reciprocal_pair_is_traversed_once(self):
        runner = self.setup_runner()
        self.assertTrue(runner.warp("A", {"index": 0, "dest": "B", "dest_warp": 0}))
        self.assertTrue(runner.warp("B", {"index": 0, "dest": "A", "dest_warp": 0}))
        self.assertEqual(runner.warps_run, [("A", 0)])

    def test_failed_first_round_trip_does_not_suppress_retry(self):
        runner = self.setup_runner()
        runner.next_warp_result = False
        self.assertFalse(runner.warp("A", {"index": 0, "dest": "B", "dest_warp": 0}))
        runner.next_warp_result = True
        self.assertTrue(runner.warp("B", {"index": 0, "dest": "A", "dest_warp": 0}))
        self.assertEqual(runner.warps_run, [("A", 0), ("B", 0)])

    def test_nonreciprocal_or_out_of_batch_warp_is_never_skipped(self):
        bad = FakeWorld({"A": [(2, 3, "B", 0)], "B": [(4, 5, "A", 99)]})
        runner = self.setup_runner(bad)
        for _ in range(2):
            runner.warp("A", {"index": 0, "dest": "B", "dest_warp": 0})
        self.assertEqual(len(runner.warps_run), 2)
        self.assertIsNone(fast.reciprocal_pair(bad, {"A": {}}, "A",
                                              {"index": 0, "dest": "B", "dest_warp": 0}))

    def test_shared_return_mats_remain_individually_tested(self):
        world = FakeWorld({"A": [(2, 3, "B", 0), (2, 4, "B", 0)],
                           "B": [(4, 5, "A", 0)]})
        runner = self.setup_runner(world)
        runner.warp("A", {"index": 0, "dest": "B", "dest_warp": 0})
        runner.warp("B", {"index": 0, "dest": "A", "dest_warp": 0})
        self.assertEqual(len(runner.warps_run), 2)

    def test_follower_sampling_rechecks_distinct_map_and_elevation(self):
        runner = self.setup_runner()
        self.assertTrue(runner.follower("first"))
        self.assertTrue(runner.follower("duplicate"))
        runner.d.current = ("A", (2, 12))
        self.assertTrue(runner.follower("upper bridge"))
        runner.d.current = ("B", (4, 5))
        self.assertTrue(runner.follower("new map"))
        self.assertEqual(runner.followers_run, ["first", "upper bridge", "new map"])

    def test_follower_failure_is_not_cached_as_success(self):
        runner = self.setup_runner()
        runner.next_follower_result = False
        self.assertFalse(runner.follower("bad"))
        runner.next_follower_result = True
        self.assertTrue(runner.follower("retest"))
        self.assertEqual(runner.followers_run, ["bad", "retest"])

    def test_modes_enforce_full_unchanged_final_runner(self):
        for mode, command in [("quick", "static"), ("batch", "run"), ("final", "run")]:
            class Runner(OriginalRunner):
                pass
            qa = SimpleNamespace(Runner=Runner, main=mock.Mock(return_value=0))
            with self.subTest(mode=mode), mock.patch.object(fast, "load_common_qa", return_value=qa):
                self.assertEqual(fast.main(["--mode", mode, command, "--map", "A"]), 0)
                qa.main.assert_called_once_with([command, "--map", "A"])
                self.assertEqual(qa.Runner.warp is Runner.__bases__[0].warp, mode != "batch")
        with self.assertRaises(SystemExit):
            fast.main(["--mode", "quick", "run", "--map", "A"])
