#!/usr/bin/env python3
"""Audit *completeness*, not truth, of authentic-emulator QA evidence packages.

An input trace, screenshots, source/ROM hashes and observed state are required
for review-ready gameplay cases. This NEVER authorizes a Playtest PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
CASE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,40}$")
PNG = b"\x89PNG\r\n\x1a\n"


def file_evidence(root: Path, name: object, kind: str, issues: list[str]) -> dict | None:
    if not isinstance(name, str) or not name.strip():
        issues.append(f"{kind}: missing evidence path")
        return None
    # Allow only files under the explicitly supplied evidence directory.
    root = root.resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root) or path == root:
        issues.append(f"{kind}: path outside evidence root")
        return None
    if not path.is_file() or not path.stat().st_size:
        issues.append(f"{kind}: empty or nonexistent evidence: {name}")
        return None
    if kind == "screenshot":
        with path.open("rb") as handle:
            if handle.read(8) != PNG:
                issues.append(f"{kind}: not a PNG: {name}")
                return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return {"path": name, "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def inspect_package(source: dict, root: Path) -> dict:
    if not isinstance(source, dict):
        raise ValueError("Evidence manifest must be a JSON object")
    sha = source.get("source_sha")
    rom = source.get("rom_sha256")
    common = []
    if not isinstance(sha, str) or not SHA40.fullmatch(sha):
        common.append("missing/invalid full source SHA")
    if not isinstance(rom, str) or not SHA64.fullmatch(rom):
        common.append("missing/invalid ROM SHA-256")
    cases = source.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty array")
    results = []
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each case must be an object")
        label = case.get("case_id")
        if not isinstance(label, str) or not CASE.fullmatch(label):
            raise ValueError(f"invalid case_id: {label!r}")
        if label in ids:
            raise ValueError(f"duplicate case_id: {label}")
        ids.add(label)
        issues = list(common)
        files = []
        trace = file_evidence(root, case.get("input_trace"), "input_trace", issues)
        if trace:
            files.append(trace)
        frames = case.get("screenshots")
        if not isinstance(frames, list) or not frames:
            issues.append("no screenshot frames supplied")
        else:
            for name in frames:
                f = file_evidence(root, name, "screenshot", issues)
                if f:
                    files.append(f)
        assertions = case.get("state_observations")
        if not isinstance(assertions, list) or not assertions:
            issues.append("no game-state observations supplied")
        else:
            for ix, assertion in enumerate(assertions):
                if not isinstance(assertion, dict):
                    issues.append(f"state observation {ix}: not an object")
                    continue
                if not isinstance(assertion.get("statement"), str) or not assertion["statement"].strip():
                    issues.append(f"state observation {ix}: missing statement")
                evidence = file_evidence(root, assertion.get("evidence_file"),
                                         f"state observation {ix}", issues)
                if evidence:
                    files.append(evidence)
                # Equal expected and observed are not independently validated,
                # and mismatches are never silently promoted to PASS.
                if "expected" in assertion and "observed" in assertion:
                    if assertion["expected"] != assertion["observed"]:
                        issues.append(f"state observation {ix}: recorded expected/observed mismatch")
        # Case-specific limits are explicit. A screenshot change is not a badge,
        # reward, heal, Save->Continue or full-party truth oracle.
        results.append({
            "case_id": label,
            "evidence_status": "READY_FOR_INDEPENDENT_REVIEW" if not issues
                               else "INCOMPLETE_OR_CONTRADICTORY",
            "issues": issues,
            "files": files,
            "independent_playtest_verdict": "NOT_GRANTED_BY_THIS_TOOL",
        })
    return {
        "schema": "averon-qa-evidence-audit-v1",
        "source_sha": sha, "rom_sha256": rom,
        "cases": results,
        "ready_for_review": sum(x["evidence_status"] == "READY_FOR_INDEPENDENT_REVIEW"
                                for x in results),
        "total_cases": len(results),
        "independent_playtest_verdict": "NOT_GRANTED_BY_THIS_TOOL",
        "limitations": [
            "File presence and hashes cannot establish genuine player inputs or game-state truth",
            "Fixture/instrumentation must be disclosed and independently reviewed",
            "Only authorized Playtest can assign actual Q1-Q5 acceptance",
        ],
    }


def classify_checks(checks: list[dict]) -> dict:
    """Conservative GitHub Actions classification: don't infer why a job failed."""
    if not isinstance(checks, list):
        raise ValueError("checks must be a list")
    output = []
    for c in checks:
        if not isinstance(c, dict) or not isinstance(c.get("name"), str):
            raise ValueError("each check needs a name")
        status, conclusion = c.get("status"), c.get("conclusion")
        if status != "completed":
            classification = "PENDING_OR_NOT_EXECUTED"
        elif conclusion in ("failure", "timed_out", "action_required", "cancelled"):
            classification = "FAILURE_REQUIRES_LOG_REVIEW"
        elif conclusion == "success":
            classification = "CHECK_SUCCEEDED_NOT_GAMEPLAY_ACCEPTANCE"
        else:
            classification = "SKIPPED_OR_INCONCLUSIVE"
        output.append({"name": c["name"], "status": status,
                       "conclusion": conclusion, "classification": classification})
    return {"checks": output, "requires_review": any(
        v["classification"] in ("FAILURE_REQUIRES_LOG_REVIEW", "PENDING_OR_NOT_EXECUTED")
        for v in output), "limitations":
        "A failed workflow is not automatically a game regression; logs and source SHA must be inspected"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)
    qa = sub.add_parser("qa")
    qa.add_argument("--input", type=Path, required=True)
    qa.add_argument("--evidence-root", type=Path, required=True)
    qa.add_argument("--out", type=Path, required=True)
    checks = sub.add_parser("checks")
    checks.add_argument("--input", type=Path, required=True)
    checks.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        raw = json.loads(args.input.read_text())
        if args.mode == "qa":
            result = inspect_package(raw, args.evidence_root)
        else:
            result = classify_checks(raw)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(("READY_FOR_REVIEW " + str(result["ready_for_review"]) + "/" + str(result["total_cases"]))
              if args.mode == "qa" else ("CHECKS_REVIEW_REQUIRED" if result["requires_review"] else
                                         "NO_CHECK_FAILURE_OBSERVED"))
        return 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"INVALID EVIDENCE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
