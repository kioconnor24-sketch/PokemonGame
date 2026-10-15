#!/usr/bin/env python3
"""Parse real Emerald Expansion linker memory budgets after native make.

All usage numbers come from the linker's --print-memory-usage output. The
generated report is informational; it never assumes future Sinnoh content fits.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MEMORY = re.compile(
    r"^\s*(EWRAM|IWRAM|ROM):\s+(\d+)\s+B\s+(\d+)\s+(KB|MB)\s+([\d.]+)%\s*$",
    re.M,
)


def parse_memory(log_text):
    entries = MEMORY.findall(log_text)
    latest = {}
    for name, used, capacity, unit, reported_percent in entries:
        maximum = int(capacity) * (1024 if unit == "KB" else 1024 * 1024)
        value = int(used)
        if value < 0 or maximum <= 0 or value > maximum:
            raise ValueError(f"Out-of-bounds {name} usage: {value}/{maximum}")
        latest[name] = {
            "used_bytes": value,
            "capacity_bytes": maximum,
            "remaining_bytes": maximum - value,
            "used_percent": round(100 * value / maximum, 2),
            "linker_reported_percent": float(reported_percent),
        }
    if set(latest) != {"ROM", "EWRAM", "IWRAM"}:
        raise ValueError("Missing real linker memory regions: " +
                         ", ".join(sorted(set(("ROM", "EWRAM", "IWRAM")) - set(latest))))
    for name, values in latest.items():
        if abs(values["used_percent"] - values["linker_reported_percent"]) > .02:
            raise ValueError("Inconsistent linker usage percentage for " + name)
    return latest


def report(log_text, rom=None):
    metadata = {"scope": "Native build and linker footprints, not game runtime",
                "memory": parse_memory(log_text)}
    if rom is not None:
        path = Path(rom)
        digest = hashlib.sha256()
        length = 0
        with path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(1024 * 1024), b""):
                digest.update(chunk)
                length += len(chunk)
        if length <= 0 or length > metadata["memory"]["ROM"]["capacity_bytes"]:
            raise ValueError("ROM binary size outside GBA address space")
        metadata["rom_artifact"] = {"size_bytes": length, "sha256": digest.hexdigest()}
    return metadata


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--json", required=True, type=Path)
    args = ap.parse_args()
    result = report(args.log.read_text(encoding="utf-8", errors="replace"), args.rom)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name, row in result["memory"].items():
        print(f"{name}: {row['used_bytes']} / {row['capacity_bytes']} bytes "
              f"({row['used_percent']:.2f}% used, {row['remaining_bytes']} bytes free)")
    if "rom_artifact" in result:
        print("ROM SHA-256: " + result["rom_artifact"]["sha256"])


if __name__ == "__main__":
    main()
