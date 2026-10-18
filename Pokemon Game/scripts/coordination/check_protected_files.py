#!/usr/bin/env python3
"""Fail closed on unapproved shared source writes, collisions and frozen maps.

This check never modifies files or PRs. Configure it as a *required status check*
in GitHub branch protection to prevent unsafe merges; otherwise it only fails CI.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REPO = "kioconnor24-sketch/PokemonGame"
SENSITIVE = (
    "engine/include/config/battle.h",
    "engine/data/event_scripts.s",
    "engine/include/constants/flags.h",
    "engine/include/constants/vars.h",
    "engine/include/global.h",
    "engine/src/save.c",
    "engine/src/overworld.c",
    "engine/src/heal_location.c",
    "engine/src/region_map.c",
)
FROZEN_MAP_SEGMENTS = ("/engine/data/maps/", "/engine/data/layouts/",
                       "/engine/data/tilesets/", "/Averon_Codex_Handoff/reference_maps/")
ALLOWED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
# Historical, already-reviewed QUEST feature was authored before this gate.
GRANDFATHERED_PR = {14}


def normalize(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def protected(path: str) -> bool:
    path = normalize(path)
    return any(path.endswith("/" + suffix) for suffix in SENSITIVE)


def frozen_map(path: str) -> bool:
    return any(segment in "/" + normalize(path) + "/" for segment in FROZEN_MAP_SEGMENTS)


def validate(snapshot: dict) -> tuple[list[str], list[str]]:
    own = snapshot["pull_request"]
    number = int(own["number"])
    paths = {normalize(f["filename"]) for f in own["files"] if f.get("status") != "removed"}
    failures, warnings = [], []
    for peer in snapshot.get("other_open_prs", []):
        peer_paths = {normalize(x) for x in peer.get("files", [])}
        collisions = paths.intersection(peer_paths)
        shared = sorted(x for x in collisions if protected(x))
        if shared:
            failures.append(f"PR #{number} overlaps PR #{peer['number']} on protected: {', '.join(shared)}")
        elif collisions:
            warnings.append(f"PR #{number} shares paths with PR #{peer['number']}: {', '.join(sorted(collisions)[:5])}")
    if number not in GRANDFATHERED_PR:
        # Phase 2 permits owner-approved permanent map construction, but ONLY
        # for exact PR/file paths in a signed Issue #15 handoff. No prefix or
        # global map waiver: old and new assets are treated identically.
        protected_paths = {x for x in paths if protected(x)}
        frozen_paths = {x for x in paths if frozen_map(x)}
        valid_approvals = set()
        for approval in snapshot.get("handoffs", []):
            if int(approval.get("pr", -1)) != number:
                continue
            if approval.get("association") not in ALLOWED_ASSOCIATIONS:
                continue
            valid_approvals.update(map(normalize, approval.get("paths", [])))
        uncovered = sorted(protected_paths.difference(valid_approvals))
        if uncovered:
            failures.append("Exclusive shared-file handoff NOT recorded in #15: " + ", ".join(uncovered))
        unapproved_maps = sorted(frozen_paths.difference(valid_approvals))
        if unapproved_maps:
            failures.append("Map-file freeze: exact PR/file handoff NOT recorded in #15: "
                            + ", ".join(unapproved_maps))
    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    errors, warnings = validate(snapshot)
    for message in warnings:
        print("WARNING:", message)
    for message in errors:
        print("FAIL:", message)
    if errors:
        print(f"FAIL: {len(errors)} protected-source conflict(s).")
        return 1
    print(f"PASS: no unapproved shared-file or frozen-map changes; {len(warnings)} warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
