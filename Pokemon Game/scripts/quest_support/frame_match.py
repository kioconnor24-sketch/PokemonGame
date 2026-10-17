#!/usr/bin/env python3
"""Compare two same-size screenshots: share of identical pixels and mean difference.

Prints "same_pixels=S mean_abs_diff=D". Exit 0 when S >= --min, 1 when below,
2 when a frame is missing or the sizes differ. Used where no debugger is
attached (the no-debugger Continue relaunch); a score, never a verdict.
"""
import argparse
import os
import subprocess
import sys


def rgb(path):
    return subprocess.check_output(["convert", path, "-depth", "8", "RGB:-"])


def score(first, second):
    a, b = rgb(first), rgb(second)
    if len(a) != len(b):
        return None
    same = sum(a[i:i+3] == b[i:i+3] for i in range(0, len(a), 3)) / (len(a) // 3)
    return same, sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--min", type=float, default=0.70)
    parser.add_argument("first")
    parser.add_argument("second")
    args = parser.parse_args()
    if not (os.path.exists(args.first) and os.path.exists(args.second)):
        print("unavailable: missing frame")
        return 2
    result = score(args.first, args.second)
    if result is None:
        print("unavailable: frame sizes differ")
        return 2
    same, diff = result
    print(f"same_pixels={same:.3f} mean_abs_diff={diff:.2f}")
    return 0 if same >= args.min else 1


if __name__ == "__main__":
    sys.exit(main())
