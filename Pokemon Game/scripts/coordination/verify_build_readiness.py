#!/usr/bin/env python3
"""Evidence-only build readiness report. A booted ROM is not accepted gameplay."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ANSI = re.compile(r"\x1b\[[0-9;]*m")
COUNT = re.compile(r"-\s*Tests\s+(PASSED|FAILED|TOTAL)\s*:\s*(\d+)", re.I)
SHA = re.compile(r"^[a-f0-9]{40}$")
ROM_LIMIT = 32 * 1024 * 1024


def parse_test_log(contents: str, name: str) -> dict[str, int]:
    clean = ANSI.sub("", contents)
    if re.search(r"No tests found|0 tests (run|executed)", clean, re.I):
        raise ValueError(f"{name}: no native tests executed")
    counts: dict[str, int] = {}
    for kind, value in COUNT.findall(clean):
        counts[kind.upper()] = int(value)
    if "PASSED" not in counts or "TOTAL" not in counts:
        raise ValueError(f"{name}: missing actual runner PASSED/TOTAL summary")
    if counts["TOTAL"] <= 0 or counts["PASSED"] != counts["TOTAL"] or counts.get("FAILED", 0):
        raise ValueError(f"{name}: incomplete or failed tests: {counts}")
    return {"passed": counts["PASSED"], "total": counts["TOTAL"],
            "failed": counts.get("FAILED", 0)}


def compute(rom: Path, native: str, save: str, budget: dict, source: dict) -> dict:
    if source.get("mode") not in ("main", "combined"):
        raise ValueError("Invalid source build mode")
    if not isinstance(source.get("main_sha"), str) or not SHA.fullmatch(source["main_sha"]):
        raise ValueError("Missing immutable main SHA")
    heads = source.get("pull_requests")
    if not isinstance(heads, list) or len(heads) != (2 if source["mode"] == "combined" else 0):
        raise ValueError("Wrong number of pinned PR heads")
    for head in heads:
        if not isinstance(head, dict) or not isinstance(head.get("number"), int) or head["number"] < 1:
            raise ValueError("Bad PR number")
        if not isinstance(head.get("sha"), str) or not SHA.fullmatch(head["sha"]):
            raise ValueError("Unverified PR SHA")
    digest = hashlib.sha256()
    size = 0
    with rom.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    if size <= 0 or size > ROM_LIMIT:
        raise ValueError("ROM size outside GBA maximum")
    recorded = budget.get("rom_artifact", {})
    if recorded.get("size_bytes") != size or recorded.get("sha256") != digest.hexdigest():
        raise ValueError("ROM SHA/size does not match independent resource-budget evidence")
    if set(budget.get("memory", {})) != {"ROM", "IWRAM", "EWRAM"}:
        raise ValueError("Missing memory budget evidence")
    return {
        "status": "BUILT_AND_NATIVE_SAVE_TESTED_NOT_GRAPHICALLY_ACCEPTED",
        "source": source,
        "rom": {"bytes": size, "sha256": digest.hexdigest(),
                "distributed": False},
        "native": parse_test_log(native, "Averon"),
        "save": parse_test_log(save, "save compatibility"),
        "memory": budget["memory"],
        "evidence_scope": [
            "GBA compile and checksum",
            "Real executed native Averon tests",
            "Real executed native save tests",
            "Actual linker resource report",
        ],
        "unverified": [
            "Normal gameplay across new features",
            "QUEST graphical Q1-Q5 acceptance",
            "Scripted-battle player-facing scenes",
            "Real old-save import compatibility beyond named tests",
            "Delta iOS compatibility",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--native-log", type=Path, required=True)
    parser.add_argument("--save-log", type=Path, required=True)
    parser.add_argument("--resource-json", type=Path, required=True)
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = compute(
        args.rom,
        args.native_log.read_text(errors="replace"),
        args.save_log.read_text(errors="replace"),
        json.loads(args.resource_json.read_text()),
        json.loads(args.source_json.read_text()),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {report['status']} — Averon {report['native']['passed']}/"
          f"{report['native']['total']}, save {report['save']['passed']}/"
          f"{report['save']['total']}; ROM SHA256={report['rom']['sha256']}")
    print("No ROM distributed. Build/native/save evidence is NOT graphical or Delta acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
