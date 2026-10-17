#!/usr/bin/env python3
"""Prevent silent omission of saved object-event capacity checks on header-only PRs.

Lightweight source-only CI regression: no ROM, new maps, or GitHub API access.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/averon-source-checks.yml"
HEADER = "Pokemon Game/engine/include/constants/global.h"
MAP_TEST = "test_averon_map_event_capacity.py"
TRIGGER_TEST = "test_averon_source_check_trigger.py"


def event_path_blocks(source: str) -> dict[str, str]:
    """Extract explicit workflow event sections; reject missing/reordered gates."""
    events = ("pull_request", "push", "workflow_dispatch")
    markers = [f"  {event}:\n" for event in events]
    if any(source.count(marker) != 1 for marker in markers):
        raise ValueError("Expected exactly one pull_request, push, workflow_dispatch")
    start = source.index(markers[0])
    end = source.index(markers[2])
    if not start < source.index(markers[1]) < end:
        raise ValueError("Event path sections changed order")
    return {
        "pull_request": source.split(markers[0], 1)[1].split(markers[1], 1)[0],
        "push": source.split(markers[1], 1)[1].split(markers[2], 1)[0],
    }


def trigger_errors(source: str) -> list[str]:
    errors = []
    try:
        blocks = event_path_blocks(source)
    except ValueError as exc:
        return [str(exc)]
    target = re.compile(
        r'^\s*-\s*"' + re.escape(HEADER) + r'"(?:\s+#.*)?\s*$',
        re.MULTILINE,
    )
    for event, block in blocks.items():
        if not re.search(r"(?m)^    paths:\s*$", block):
            errors.append(f"{event}: no paths filter")
        if len(target.findall(block)) != 1:
            errors.append(f"{event}: expected exact one {HEADER} path trigger")
    if MAP_TEST not in source or "python3 -m unittest discover" not in source:
        errors.append("capacity checker no longer executed in source workflow")
    if TRIGGER_TEST not in source:
        errors.append("trigger regression test no longer executed in source workflow")
    return errors


class SourceTriggerTests(unittest.TestCase):
    def test_live_workflow_covers_header_in_both_events(self):
        self.assertEqual(trigger_errors(WORKFLOW.read_text()), [])

    def test_missing_pull_request_header_fails(self):
        src = WORKFLOW.read_text()
        first = src.index(f'"{HEADER}"')
        mutated = src[:first] + src[first:].replace(f'"{HEADER}"', '"wrong/path.h"', 1)
        self.assertIn("pull_request: expected exact one", "\n".join(trigger_errors(mutated)))

    def test_missing_main_push_header_fails(self):
        src = WORKFLOW.read_text()
        second = src.index(f'"{HEADER}"', src.index(f'"{HEADER}"') + 1)
        mutated = src[:second] + src[second:].replace(f'"{HEADER}"', '"wrong/path.h"', 1)
        self.assertIn("push: expected exact one", "\n".join(trigger_errors(mutated)))

    def test_capacity_test_cannot_be_removed(self):
        src = WORKFLOW.read_text().replace(MAP_TEST, "test_missing_safety_gate.py")
        self.assertIn("capacity checker no longer executed", "\n".join(trigger_errors(src)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
