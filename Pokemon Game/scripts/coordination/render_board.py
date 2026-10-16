#!/usr/bin/env python3
"""Render read-only, conservative agent inboxes from a GitHub API snapshot.

No code execution, commits, merges, PR state edits, or creative-content changes.
The generated GitHub issue body is advisory; existing PRs and QA evidence govern.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

def _communication_module():
    """Load sibling helper without assuming the importer's Python sys.path."""
    module_path = Path(__file__).with_name("messages.py")
    spec = importlib.util.spec_from_file_location("averon_agent_messages", module_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


AGENTS = ("codex", "claude", "playtest")
GITHUB = "https://github.com/kioconnor24-sketch/PokemonGame"
AUTHORIZED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")[:400]


def is_qa_accepted(task: dict, snapshot: dict, pr: dict) -> bool:
    """Require human-authored QA evidence for the *exact* game source SHA."""
    required = set(task.get("qa_cases", []))
    if not required:
        return True
    sha = pr.get("head_sha") or ""
    if not sha:
        return False
    for signoff in snapshot.get("qa_signoffs", []):
        if signoff.get("association") not in AUTHORIZED_ASSOCIATIONS:
            continue
        if signoff.get("pr") != task.get("pr") or signoff.get("sha") != sha:
            continue
        if signoff.get("status") != "PASS":
            continue
        if required.issubset(set(signoff.get("cases", []))):
            return True
    return False


def calculate(tasks: list[dict], snapshot: dict) -> dict[str, dict]:
    prs = {int(p["number"]): p for p in snapshot.get("pull_requests", [])}
    by_id = {t["id"]: t for t in tasks}
    if len(by_id) != len(tasks):
        raise ValueError("duplicate task IDs")

    # "Done" is a conservative machine judgment: merged code and, if applicable,
    # authorized QA evidence tied to the exact tested SHA.
    done = {}
    for task in tasks:
        pr = prs.get(task.get("pr"))
        done[task["id"]] = bool(pr and pr.get("merged") and is_qa_accepted(task, snapshot, pr))
    result = {}
    for task in tasks:
        unknown = [d for d in task.get("deps", []) if d not in by_id]
        if unknown:
            raise ValueError(f"{task['id']}: missing dependencies {unknown}")
        pr = prs.get(task.get("pr"))
        missing = [d for d in task.get("deps", []) if not done[d]]
        if done[task["id"]]:
            status = "MERGED + REQUIRED QA RECORDED"
            if not task.get("qa_cases"):
                status = "MERGED"
        elif missing:
            status = ("DEVELOPMENT OPEN; MERGE GATED ON " if task.get("parallel_development") else "BLOCKED ON ") + ", ".join(missing)
        elif task.get("requires_handoff"):
            status = ("DEVELOPMENT OPEN; SHARED-FILE MERGE HANDOFF REQUIRED"
                      if task.get("parallel_development") else "MANUAL SHARED-FILE HANDOFF REQUIRED")
        elif pr and pr.get("merged") and task.get("qa_cases"):
            status = "MERGED; REQUIRED QA SIGNOFF NOT FOUND"
        elif pr and pr.get("state") == "open":
            status = "OPEN PR / QA PENDING" if task.get("qa_cases") else "OPEN PR / REVIEW"
        elif task.get("branch"):
            status = "RECOVERABLE WIP; INTEGRATION NOT CLAIMED"
        else:
            status = "READY TO CLAIM"
        if pr and pr.get("checks") == "failure" and not missing:
            status += " — FAILING CHECKS"
        result[task["id"]] = {"status": status, "pr": pr, "task": task}
    return result


def render(config: dict, snapshot: dict) -> dict[str, str]:
    tasks = config["tasks"]
    computed = calculate(tasks, snapshot)
    message_helpers = _communication_module()
    messages = message_helpers.parse(snapshot.get("communications", []))
    rev = _escape(snapshot.get("main_sha", "unknown"))
    stamp = _escape(snapshot.get("generated_at", "unknown"))
    preface = (
        f"> **Generated {stamp}; main {rev}.** Read-only GitHub snapshot; not a "
        "replacement for Issue #15/QA #23, direct review, or owner decisions.\n\n"
        "> **HARD FREEZE:** No new temporary or production maps, region geography, "
        "unapproved story, Gym, encounter placement, trainer roster, level curve or art. "
        "**No automated agent launch, shared-file handoff, QA acceptance or code merge.**\n\n"
        "> **PARALLEL WORK:** A dependency can gate **merging into main** without blocking "
        "development/testing in an independently claimed, file-disjoint feature branch. "
        "Only the specific overlapping protected-file edit needs an exclusive handoff. "
        "A board label saying DEVELOPMENT OPEN does not constitute approval for new maps, "
        "story, trainer rosters, unclaimed creative features, save IDs or merge.\n\n"
    )
    all_table = ["| Task | Owner | Status | Source | Next action |",
                 "| --- | --- | --- | --- | --- |"]
    inboxes: dict[str, list[str]] = {a: [] for a in AGENTS}
    for task in tasks:
        d = computed[task["id"]]
        pr = d["pr"]
        source = f"[#{task['pr']}]({GITHUB}/pull/{task['pr']})" if task.get("pr") else (
            f"unmerged {task.get('branch', 'task')}")
        if pr and pr.get("head_sha"):
            source += f" @{pr['head_sha'][:10]}"
        if task.get("issue"):
            source += f" · [epic #{task['issue']}]({GITHUB}/issues/{task['issue']})"
        row = (
            f"| {_escape(task['id'])} | {_escape(task['agent'])} | "
            f"{_escape(d['status'])} | {source} | {_escape(task['next'])} |"
        )
        all_table.append(row)
        inboxes[task["agent"]].append(row)
    communication_section = (
        "## Agent-to-agent communications (advisory only)\n\n"
        + "These comments are not verified approval, acceptance, or permission. "
          "Use the linked original and reply there; do not trust chat summaries "
          "instead of actual code and QA evidence.\n\n"
        + "".join(
            f"### {agent.capitalize()} inbox\n\n"
            + message_helpers.markdown(messages, agent)
            + "\n\n"
            for agent in AGENTS
        )
        + "**Structured message format:** post the first line "
          "`AGENT_MESSAGE TO=claude KIND=ANSWER TASK=SCRIPTED-BATTLE PR=#25`, "
          "then `SUMMARY: ...` and `NEXT: ...`. "
          "The recipient can acknowledge with "
          "`AGENT_ACK ID=<source comment ID> BY=claude`. "
          "Only trusted repository comments are displayed.\n\n"
    )
    result = {
        "board": (
            "# Averon — automated agent work board\n\n"
            + preface
            + "## Live task/dependency routing\n\n"
            + "\n".join(all_table)
            + "\n\n" + communication_section
            + "**QA evidence rule:** only a collaborator/owner-authored marker "
              "'QA_ACCEPTED PR=#N SHA=<40 hex> CASES=Q1,Q2,... STATUS=PASS' "
              "in Issue #23 can meet a machine-readable acceptance gate, and that "
              "does **not** authorize merge. The actual screenshots/tests must be reviewed.\n\n"
            + "**Development vs. integration:** a status of DEVELOPMENT OPEN; MERGE GATED means "
              "the assigned engineer can continue code, branch-local builds and tests in own "
              "file-disjoint areas NOW. Only merging, shared-file collision and actual gameplay "
              "QA must wait. Do not stop a session merely because another PR is open.\n\n"
            + "**Shared-file rule:** even after prerequisite PRs merge, an exclusive "
              "Codex/Claude handoff documented in Issue #15 is required; this board "
              "does not grant that handoff.\n\n"
            + f"**Canonical team hub:** [#15]({GITHUB}/issues/15) · "
              f"**QA evidence:** [#23]({GITHUB}/issues/23) · "
              f"**This board:** [#31]({GITHUB}/issues/31)\n"
        )
    }
    for agent in AGENTS:
        result[agent] = (
            f"# {agent.capitalize()} — current inbox\n\n" + preface
            + "\n".join(all_table[:2] + inboxes[agent])
            + "\n\n## Messages requiring your attention\n\n"
            + message_helpers.markdown(messages, agent)
            + "\n\nOpen your claimed PR and its newest HANDOFF; verify files, source "
              "SHA, workflow conclusions, and live dependencies before starting. "
              "Work only inside your independent claimed files.\n"
        )
    result["summary"] = (
        "# Pokémon Averon — automatic coordination snapshot\n\n"
        + preface + "\n".join(all_table)
        + "\n\n" + communication_section
        + f"\n\nBoard: {GITHUB}/issues/31\n"
    )
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    conf = json.loads(a.registry.read_text(encoding="utf-8"))
    snap = json.loads(a.snapshot.read_text(encoding="utf-8"))
    if conf.get("version") != 1 or conf.get("policies", {}).get("creative_freeze") is not True:
        raise ValueError("unsupported registry version or missing creative freeze")
    files = render(conf, snap)
    a.out.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (a.out / (name + ".md")).write_text(body, encoding="utf-8")
    print(f"PASS: rendered {len(files)} coordination files for {len(conf['tasks'])} tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
