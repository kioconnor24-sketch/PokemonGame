#!/usr/bin/env python3
"""Check local inline Markdown links in the small set of active Averon entry points.

Read-only and standard-library-only. Deliberately ignores remote URLs, anchors,
reference-style links and fenced code blocks. It does not touch game source.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ACTIVE_DOCS = (
    "README.md",
    "AGENTS.md",
    "Pokemon Game/AGENTS.md",
    "Pokemon Game/Averon_Codex_Handoff/START_HERE.md",
    "Pokemon Game/Averon_Codex_Handoff/development/INDEX.md",
    "Pokemon Game/Averon_Codex_Handoff/development/ROADMAP.md",
    "Pokemon Game/Averon_Codex_Handoff/development/TASKS.md",
    "Pokemon Game/Averon_Codex_Handoff/development/WORKFLOW.md",
    "Pokemon Game/Averon_Codex_Handoff/development/AGENT_ROLES.md",
)

INLINE_LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\((<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def validate(root: Path, docs: tuple[str, ...] = ACTIVE_DOCS) -> list[str]:
    """Return actionable missing/escaping-file diagnostics, without writing files."""
    root = root.resolve()
    problems: list[str] = []
    for relative in docs:
        document = root / relative
        if not document.is_file():
            problems.append(f"{relative}: entry-point document is missing")
            continue
        in_fence = False
        fence_char = ""
        for number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            marker = FENCE.match(line)
            if marker:
                char = marker.group(1)[0]
                if not in_fence:
                    in_fence = True
                    fence_char = char
                elif char == fence_char:
                    in_fence = False
                continue
            if in_fence:
                continue
            for match in INLINE_LINK.finditer(line):
                link = match.group(1).strip("<>")
                if link.startswith("#"):
                    continue
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue  # Remote link or same-document fragment.
                decoded = unquote(parsed.path)
                if decoded.startswith("/"):
                    problems.append(f"{relative}:{number}: absolute local link: {link}")
                    continue
                target = (document.parent / decoded).resolve()
                if not target.is_relative_to(root):
                    problems.append(f"{relative}:{number}: link escapes repository: {link}")
                elif not target.exists():
                    problems.append(f"{relative}:{number}: missing local target: {link}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    problems = validate(args.root)
    for item in problems:
        print("FAIL:", item)
    if problems:
        print(f"FAIL: {len(problems)} invalid local documentation link(s).")
        return 1
    print(f"PASS: local inline links in {len(ACTIVE_DOCS)} active entry-point docs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
