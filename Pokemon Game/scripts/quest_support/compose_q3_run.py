#!/usr/bin/env python3
"""Compose the Q3 clinic support run from Playtest's unchanged QA step.

Reads the "Launch actual graphical mGBA" step of a pinned
averon-rendered-playtest.yml, keeps it verbatim up to the end of its Q3 block,
and appends q3_continuation.sh (observer, flash decode, Continue relaunch).
Playtest's files are read, never edited. Fails closed if the step or the Q3
end marker is not found exactly once, so a changed QA script is never cut at
a guessed place.
"""
import argparse
from pathlib import Path

import yaml

STEP = "Launch actual graphical mGBA and capture controller milestones"
Q3_END = ('  echo "QA_Q3_GYM_NOT_RUN: genuine gifted party prerequisite not proven"', "fi")


def q3_prefix(workflow_text):
    """The QA step's script up to and including the end of its Q3 block."""
    workflow = yaml.safe_load(workflow_text)
    steps = [step for job in workflow["jobs"].values() for step in job["steps"]
             if step.get("name") == STEP]
    if len(steps) != 1:
        raise ValueError(f"Expected one step named {STEP!r}, found {len(steps)}")
    if steps[0].get("shell") != "bash":
        raise ValueError("QA step is no longer a bash step")
    lines = steps[0]["run"].splitlines()
    ends = [n for n in range(len(lines) - 1) if (lines[n], lines[n + 1]) == Q3_END]
    if len(ends) != 1:
        raise ValueError(f"Expected one Q3 block end marker, found {len(ends)}")
    return lines[:ends[0] + 2], steps[0].get("env") or {}


def compose(workflow_text, continuation_text):
    prefix, env = q3_prefix(workflow_text)
    exports = [f"export {name}={value!s}" for name, value in sorted(env.items())]
    return "\n".join(exports + prefix + [continuation_text.rstrip("\n")]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--continuation", type=Path,
                        default=Path(__file__).with_name("q3_continuation.sh"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(compose(args.workflow.read_text(), args.continuation.read_text()))
    print(f"Composed {args.out} from {args.workflow} (Q3 prefix) + {args.continuation}")


if __name__ == "__main__":
    main()
