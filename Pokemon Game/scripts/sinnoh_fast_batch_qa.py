#!/usr/bin/env python3
"""Opt-in lightweight map QA. The existing map_qa final runner is unchanged.

Usage:
  python3 scripts/sinnoh_fast_batch_qa.py --mode quick static --engine E --map MAP_A
  python3 scripts/sinnoh_fast_batch_qa.py --mode batch run --engine E --rom R --build normal --scratch S --out O --map MAP_A
  python3 scripts/sinnoh_fast_batch_qa.py --mode final run --engine E --rom R --build normal --scratch S --out O --map MAP_A

QUICK: static audit only. BATCH: exactly one actual two-way traversal of each
provably unique reciprocal warp pair, and one follower check per map/elevation
visited. All other run checks stay enabled. FINAL: entirely unmodified map_qa.
A successful quick/batch run is NOT production, save or visual acceptance.
"""
import argparse
import importlib.util
from pathlib import Path
import sys


def reciprocal_pair(world, plan, source, point):
    """Return an unordered pair only for unambiguous, two-way indexed warps.

    Any missing, external, shared-return or malformed warp gets tested normally.
    """
    dest = point.get("dest")
    try:
        i = int(point["index"])
        j = int(point["dest_warp"])
        if source not in plan or dest not in plan:
            return None
        a = world.map(source).warps
        b = world.map(dest).warps
        if not (0 <= i < len(a) and 0 <= j < len(b)):
            return None
        if a[i][2:] != (dest, j) or b[j][2:] != (source, i):
            return None
        # Multi-mat / shared-return doors can have different triggering rules.
        if sum(w[2:] == (dest, j) for w in a) != 1:
            return None
        if sum(w[2:] == (source, i) for w in b) != 1:
            return None
        return tuple(sorted(((source, i), (dest, j))))
    except (AttributeError, KeyError, IndexError, TypeError, ValueError):
        return None


def install_batch_mode(qa):
    """Narrow runtime-only patch of the imported common QA runner.

    Do not patch map_qa.py, its build fixtures, or the NORMAL/RELEASE ROM.
    """
    original_warp = qa.Runner.warp
    original_follower = qa.Runner.follower

    def warp(self, map_id, point):
        pair = reciprocal_pair(self.w, self.plan, map_id, point)
        tested = self.__dict__.setdefault("_sinnoh_batch_pairs", set())
        if pair is not None and pair in tested:
            return True  # the first successful round trip exercised both directions
        passed = original_warp(self, map_id, point)
        if passed and pair is not None:
            tested.add(pair)
        return passed

    def follower(self, label):
        mid, (x, y) = self.d.here()
        m = self.w.map(mid)
        # The static elevation, not an inferred visual layer, is this sampling key.
        key = (mid, m.elevation(x, y))
        tested = self.__dict__.setdefault("_sinnoh_batch_followers", set())
        if key in tested:
            return True
        passed = original_follower(self, label)
        if passed:
            tested.add(key)
        return passed

    qa.Runner.warp = warp
    qa.Runner.follower = follower


def load_common_qa():
    path = Path(__file__).resolve().parent / "claude_play" / "map_qa.py"
    spec = importlib.util.spec_from_file_location("sinnoh_fast_common_map_qa", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description="Opt-in Sinnoh construction QA")
    parser.add_argument("--mode", required=True, choices=("quick", "batch", "final"))
    opts, command = parser.parse_known_args(argv)
    if command[:1] == ["--"]:
        command = command[1:]
    expected = "static" if opts.mode == "quick" else "run"
    if not command or command[0] != expected:
        parser.error(f"{opts.mode} mode must use the {expected} map_qa command")
    qa = load_common_qa()
    if opts.mode == "batch":
        install_batch_mode(qa)
    return qa.main(command)


if __name__ == "__main__":
    raise SystemExit(main())
