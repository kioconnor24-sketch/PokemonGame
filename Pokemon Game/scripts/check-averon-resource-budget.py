#!/usr/bin/env python3
"""Parse real Emerald Expansion linker memory budgets after native make.

All usage numbers come from the linker's --print-memory-usage output. The
generated report is informational; it never assumes future Sinnoh content fits.
Optional comparisons require the same caller-labeled build profile and memory
capacities. Profile/revision labels do not verify how either build was made.
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
REGIONS = {"ROM", "EWRAM", "IWRAM"}
REPORT_SCOPE = "Native build and linker footprints, not game runtime"
LABEL_SCOPE = "Caller-supplied labels; build configuration and source revision are not verified"


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


def build_labels(profile=None, source_revision=None):
    labels = {}
    for name, value in (("profile", profile), ("source_revision", source_revision)):
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty caller-supplied label")
            labels[name] = value.strip()
    if labels:
        labels["scope"] = LABEL_SCOPE
    return labels


def compare_baseline(current, baseline):
    """Compare linker usage only, rejecting incomplete/incompatible reports."""
    profile = current.get("build_labels", {}).get("profile")
    if not profile:
        raise ValueError("Baseline comparison requires a nonempty current profile")
    if not isinstance(baseline, dict) or baseline.get("scope") != REPORT_SCOPE:
        raise ValueError("Malformed baseline: expected a resource-budget report object")
    labels = baseline.get("build_labels")
    if not isinstance(labels, dict):
        raise ValueError("Baseline comparison requires a nonempty baseline profile")
    baseline_labels = build_labels(labels.get("profile"), labels.get("source_revision"))
    if not baseline_labels.get("profile"):
        raise ValueError("Baseline comparison requires a nonempty baseline profile")
    if baseline_labels["profile"] != profile:
        raise ValueError("Baseline profile differs from current profile")
    memory = baseline.get("memory")
    if not isinstance(memory, dict) or set(memory) != REGIONS:
        raise ValueError("Malformed baseline: expected ROM, EWRAM and IWRAM memory regions")
    changes = {}
    for name, current_row in current["memory"].items():
        row = memory[name]
        if not isinstance(row, dict):
            raise ValueError(f"Malformed baseline: invalid {name} memory row")
        for field in ("used_bytes", "capacity_bytes", "remaining_bytes"):
            if type(row.get(field)) is not int:
                raise ValueError(f"Malformed baseline: {name} {field} must be an integer")
        used, capacity = row["used_bytes"], row["capacity_bytes"]
        if capacity <= 0 or not 0 <= used <= capacity or row["remaining_bytes"] != capacity - used:
            raise ValueError(f"Malformed baseline: inconsistent {name} memory bytes")
        for field in ("used_percent", "linker_reported_percent"):
            value = row.get(field)
            if (type(value) not in (int, float) or not 0 <= value <= 100
                    or abs(round(100 * used / capacity, 2) - value) > .02):
                raise ValueError(f"Malformed baseline: inconsistent {name} {field}")
        if capacity != current_row["capacity_bytes"]:
            raise ValueError(f"Baseline {name} capacity differs from current capacity")
        changes[name] = {"baseline_used_bytes": used,
                         "used_bytes_delta": current_row["used_bytes"] - used}
    return {"scope": "Signed linker used-byte changes; ROM artifact padding is excluded",
            "baseline_labels": baseline_labels, "memory": changes}


def report(log_text, rom=None, *, profile=None, source_revision=None, baseline=None):
    metadata = {"scope": REPORT_SCOPE,
                "memory": parse_memory(log_text)}
    labels = build_labels(profile, source_revision)
    if labels:
        metadata["build_labels"] = labels
    if baseline is not None:
        metadata["comparison"] = compare_baseline(metadata, baseline)
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
    ap.add_argument("--profile", help="Caller label for the exact build configuration; not verified")
    ap.add_argument("--source-revision", help="Caller source revision label; not verified")
    ap.add_argument("--baseline", type=Path,
                    help="Previous JSON report with matching nonempty profile and capacities")
    args = ap.parse_args()
    try:
        baseline = None
        if args.baseline is not None:
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
            if baseline is None:
                raise ValueError("Malformed baseline: expected a resource-budget report object")
        result = report(args.log.read_text(encoding="utf-8", errors="replace"), args.rom,
                        profile=args.profile, source_revision=args.source_revision, baseline=baseline)
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name, row in result["memory"].items():
        print(f"{name}: {row['used_bytes']} / {row['capacity_bytes']} bytes "
              f"({row['used_percent']:.2f}% used, {row['remaining_bytes']} bytes free)")
    if "rom_artifact" in result:
        print("ROM SHA-256: " + result["rom_artifact"]["sha256"])
    if "build_labels" in result:
        print(LABEL_SCOPE)
    if "comparison" in result:
        for name, row in result["comparison"]["memory"].items():
            print(f"{name}: linked usage change {row['used_bytes_delta']:+d} bytes")


if __name__ == "__main__":
    main()
