#!/usr/bin/env python3
"""Validate one-line SCRIPTED-BATTLE registration split in a DISPOSABLE worktree.

This never edits a real PR, approves a protected-source handoff, or accepts
gameplay. It runs only after PR #25 is merged into an ephemeral main worktree.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

REGISTRY = Path("Pokemon Game/engine/data/event_scripts.s")
REGISTRATION = b'\t.include "data/scripts/averon_scripted_battle.inc"\n'
SHA = re.compile(r"[0-9a-f]{40}\Z")


class StageError(ValueError):
    pass


def strip_registration(merged_registry: bytes, main_registry: bytes) -> bytes:
    """Accept only the single expected registration edit; no generic deletion."""
    count = merged_registry.count(REGISTRATION)
    if count != 1:
        raise StageError(f"Expected exactly one macro-registration line; found {count}")
    # The line must stand alone (not injected into a string or another directive).
    if not any(line == REGISTRATION.rstrip(b"\n") for line in merged_registry.splitlines()):
        raise StageError("Expected a standalone, exact macro-registration line")
    staged = merged_registry.replace(REGISTRATION, b"", 1)
    if staged != main_registry:
        raise StageError(
            "event_scripts.s still differs from main after stripping registration; "
            "a new shared-file change needs an explicit owner review"
        )
    return staged


def verify_core_files(worktree: Path) -> None:
    """Ensure the nonregistered staged build actually contains its prerequisites."""
    engine = worktree / "Pokemon Game/engine"
    required = (
        "src/averon_scripted_battle.c",
        "include/averon_scripted_battle.h",
        "data/scripts/averon_scripted_battle.inc",
        "test/averon_scripted_battle.c",
        "test/averon_scripted_battle_engine.c",
    )
    missing = [path for path in required if not (engine / path).is_file()]
    if missing:
        raise StageError("Missing staged core source/native test(s): " + ", ".join(missing))
    macro = (engine / "data/scripts/averon_scripted_battle.inc").read_text()
    config = (engine / "include/config/battle.h").read_text()
    if not all(re.search(r"(?m)^\s*\.macro\s+" + name + r"\b", macro)
               for name in ("averon_scripted_battle", "averon_recover_in_place", "averon_respawn")):
        raise StageError("Staged macro definitions are missing")
    if not re.search(
        r"(?m)^\s*#define\s+B_FLAG_NO_WHITEOUT\s+FLAG_SPECIAL_FLAG_UNUSED_0x4003\b",
        config,
    ):
        raise StageError("Staged core is missing approved RAM-only whiteout flag mapping")
    # Zero production callers is an essential prerequisite for omitting the include.
    # Ignore the macro definition file itself, where the name occurs as a definition.
    for script in (engine / "data").rglob("*.inc"):
        if script.name == "averon_scripted_battle.inc":
            continue
        code = "\n".join(line.split("@", 1)[0] for line in script.read_text(errors="replace").splitlines())
        if re.search(r"(?m)^\s*averon_(?:scripted_battle|recover_in_place|respawn)\b", code):
            raise StageError(f"Real script invokes unregistered macro: {script.relative_to(engine)}")


def prepare(worktree: Path, base_sha: str, output: Path) -> dict:
    if not SHA.fullmatch(base_sha):
        raise StageError("Base must be an exact lowercase 40-character commit SHA")
    if not (worktree / REGISTRY).is_file():
        raise StageError("Missing staged engine registry")
    main = subprocess.check_output(
        ["git", "show", f"{base_sha}:{REGISTRY.as_posix()}"],
        cwd=worktree,
    )
    path = worktree / REGISTRY
    staged = strip_registration(path.read_bytes(), main)
    verify_core_files(worktree)
    # Only now, after ALL preflight safety checks, change this disposable copy.
    path.write_bytes(staged)
    report = {
        "kind": "STAGED_SCRIPTED_CORE_REHEARSAL_ONLY",
        "base_sha": base_sha,
        "registration_removed_in_disposable_worktree": True,
        "event_registry_matches_main": True,
        "staged_native_core_present": True,
        "actual_quest_qa_accepted": False,
        "actual_event_registration_merged": False,
        "protected_file_handoff_or_merge_approval": False,
        "gameplay_and_delta_accepted": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--worktree", type=Path, required=True)
    p.add_argument("--base-sha", required=True)
    p.add_argument("--json", type=Path, required=True)
    args = p.parse_args()
    try:
        result = prepare(args.worktree.resolve(), args.base_sha, args.json)
    except (StageError, OSError, subprocess.CalledProcessError) as exc:
        p.exit(2, f"FAIL CLOSED: {exc}\n")
    print(f"PASS: exact one-line core-only rehearsal at main {result['base_sha']}; "
          "NO merge/QA/registration approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
