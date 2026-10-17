#!/usr/bin/env python3
"""Read-only provenance for a privately built Averon ROM.

Records actual source and tool versions; it never builds, tests, distributes a
ROM, or asserts gameplay/QA acceptance. A dirty engine is *not* reproducible.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROM_LIMIT = 32 * 1024 * 1024


def run_output(argv: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            timeout=12, check=True)
    return result.stdout.strip()


def command_info(name: str, version_args: list[str] | None = None) -> dict:
    resolved = shutil.which(name)
    if not resolved:
        return {"available": False, "version": None}
    try:
        raw = run_output([name, *(version_args or ["--version"])])
        first = raw.splitlines()[0] if raw else None
        return {"available": True, "version": first}
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired, IndexError):
        return {"available": True, "version": None}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(root: Path, engine: Path, rom: Path | None = None) -> dict:
    root, engine = root.resolve(), engine.resolve()
    # Only inspect a real git checkout and its genuine engine subtree.
    sha = run_output(["git", "rev-parse", "HEAD"], root)
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("Git HEAD must be a complete hexadecimal commit SHA")
    rel_engine = engine.relative_to(root)
    if not (engine / "Makefile").is_file():
        raise ValueError("Engine Makefile missing; cannot identify actual build input")
    source_tree = run_output(["git", "rev-parse", f"HEAD:{rel_engine.as_posix()}"], root)
    changes = run_output(["git", "status", "--porcelain", "--untracked-files=all",
                          "--", rel_engine.as_posix()], root)
    versions = {
        "arm_gcc": command_info("arm-none-eabi-gcc"),
        "arm_ld": command_info("arm-none-eabi-ld"),
        "make": command_info("make"),
        "python": {"available": True, "version": sys.version.splitlines()[0]},
        "git": command_info("git"),
        "mgba": command_info("mgba"),
    }
    artifact = None
    if rom is not None:
        rom = rom.resolve()
        if not rom.is_file():
            raise FileNotFoundError(f"ROM not found: {rom.name}")
        size = rom.stat().st_size
        if size == 0 or size > ROM_LIMIT:
            raise ValueError("ROM must be nonempty and <= 32 MiB")
        artifact = {"filename": rom.name, "bytes": size, "sha256": sha256_file(rom)}
    problems = []
    if changes:
        problems.append("Engine has uncommitted/untracked source; source cannot be reproduced from commit alone")
    for required in ("arm_gcc", "make", "git"):
        if not versions[required]["available"] or not versions[required]["version"]:
            problems.append(f"Required tool version unavailable: {required}")
    if rom is None:
        problems.append("No ROM supplied; only source/toolchain provenance recorded")
    return {
        "schema": "averon-toolchain-provenance-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": sha,
        "engine_tree_sha": source_tree,
        "engine_clean": not bool(changes),
        "engine_status_lines": len(changes.splitlines()) if changes else 0,
        "tools": versions,
        "rom": artifact,
        "status": "COMPLETE_BUILD_PROVENANCE_NOT_GAMEPLAY_ACCEPTANCE" if not problems
                  else "INCOMPLETE_PROVENANCE",
        "problems": problems,
        "limitations": [
            "Recording versions is not proof of a successful build or deterministic binary reproduction",
            "Native tests, emulator gameplay, independent QA and Delta iOS remain separate evidence",
            "No binary ROM is stored in this manifest",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--strict", action="store_true",
                        help="fail if source dirty, tools unknown or ROM absent")
    args = parser.parse_args()
    try:
        result = collect(args.repo, args.engine, args.rom)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"INCOMPLETE PROVENANCE: {exc}", file=sys.stderr)
        return 2
    print(f"{result['status']}: source={result['source_sha']}; no gameplay acceptance implied")
    return 2 if args.strict and result["status"] != "COMPLETE_BUILD_PROVENANCE_NOT_GAMEPLAY_ACCEPTANCE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
