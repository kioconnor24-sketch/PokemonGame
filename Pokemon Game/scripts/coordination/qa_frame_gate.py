#!/usr/bin/env python3
"""Fail-closed screenshot-change gate for existing mGBA QA workflows.

Uses ImageMagick 'convert' (already installed in the QA GitHub runner); no OCR,
new maps, saved flags, screenshots uploaded publicly, or game controls sent.
A changed frame does NOT by itself prove a quest or interaction succeeded.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess


def difference(first: bytes, second: bytes) -> float:
    """Normalized mean absolute RGB byte difference; deterministic synthetic tests."""
    if len(first) != len(second) or not first:
        raise ValueError("empty or differently sized RGB samples")
    return sum(abs(a - b) for a, b in zip(first, second)) / (255.0 * len(first))


def sample(path: Path, size: int = 64) -> bytes:
    """Extract a fixed-size RGB sample from a local PNG without saving an image."""
    result = subprocess.run(
        ["convert", str(path), "-resize", f"{size}x{size}!", "-depth", "8", "rgb:-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    if len(result.stdout) != size * size * 3:
        raise ValueError(f"unexpected image sample size from {path}")
    return result.stdout


def check(before: Path, after: Path, threshold: float, high: float = 1.0) -> tuple[bool, float]:
    value = difference(sample(before), sample(after))
    return threshold <= value <= high, value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--min-change", type=float, default=0.015)
    parser.add_argument("--max-change", type=float, default=1.0)
    args = parser.parse_args()
    if not (0 <= args.min_change <= args.max_change <= 1):
        parser.error("change thresholds must satisfy 0 <= min <= max <= 1")
    try:
        valid, score = check(args.before, args.after, args.min_change, args.max_change)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: screenshot gate cannot evaluate images: {exc}")
        return 2
    print(f"{'OBSERVABLE CHANGE' if valid else 'BLOCKED: no required change'}: "
          f"normalized frame difference={score:.5f}; "
          "this never constitutes interaction acceptance on its own")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
