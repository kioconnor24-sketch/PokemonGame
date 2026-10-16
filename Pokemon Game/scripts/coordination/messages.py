"""Conservative human-readable agent message and acknowledgment routing.

Structured comments are *advisory communications*, NEVER approval to merge,
allocate a flag, bypass QA, hand off a shared file, or execute AI work.
Only trusted GitHub collaborators' comments from the configured issues/PRs.
"""
from __future__ import annotations

import re

TARGETS = {"codex", "claude", "playtest", "all"}
KINDS = {"QUESTION", "ANSWER", "HANDOFF", "BLOCKER", "QA", "FYI"}
ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
ROOT = "https://github.com/kioconnor24-sketch/PokemonGame/"
HEADER = re.compile(
    r"^AGENT_MESSAGE TO=(codex|claude|playtest|all) "
    r"KIND=(QUESTION|ANSWER|HANDOFF|BLOCKER|QA|FYI) "
    r"TASK=([A-Za-z0-9_-]{1,64})(?: PR=#([0-9]{1,9}))?\s*$"
)
ACK = re.compile(r"^AGENT_ACK ID=([0-9]{1,18}) BY=(codex|claude|playtest)\s*$")


def parse(comments: list[dict]) -> list[dict]:
    """Parse first-line exact message envelopes and optional later ACK comments."""
    notes = {}
    acknowledgments: set[tuple[int, str]] = set()
    for comment in comments:
        if comment.get("author_association") not in ASSOCIATIONS:
            continue
        body = (comment.get("body") or "").replace("\r\n", "\n")
        lines = body.split("\n")
        if not lines:
            continue
        top = lines[0].strip()
        ack = ACK.fullmatch(top)
        if ack:
            if len([x for x in lines[1:] if x.strip()]) == 0:
                acknowledgments.add((int(ack.group(1)), ack.group(2)))
            continue
        header = HEADER.fullmatch(top)
        if header is None:
            continue
        ident = comment.get("id")
        if not isinstance(ident, int) or ident <= 0:
            continue
        url = comment.get("html_url") or ""
        if not url.startswith(ROOT) or "#issuecomment-" not in url:
            continue
        fields: dict[str, str] = {}
        for line in lines[1:]:
            for key in ("SUMMARY", "NEXT"):
                if line.startswith(key + ": "):
                    fields[key] = line[len(key) + 2:].strip()
        if not fields.get("SUMMARY") or not fields.get("NEXT"):
            continue
        notes[ident] = {
            "id": ident,
            "to": header.group(1),
            "kind": header.group(2),
            "task": header.group(3),
            "pr": int(header.group(4)) if header.group(4) else None,
            "summary": fields["SUMMARY"][:350],
            "next": fields["NEXT"][:350],
            "url": url,
            "date": str(comment.get("created_at") or "")[:19],
        }
    ordered = sorted(notes.values(), key=lambda n: (n["date"], n["id"]), reverse=True)
    for note in ordered:
        note["acknowledged_by"] = sorted(agent for (ident, agent) in acknowledgments
                                      if ident == note["id"])
    return ordered


def for_agent(messages: list[dict], agent: str, limit: int = 6) -> list[dict]:
    if agent not in TARGETS - {"all"}:
        raise ValueError("unknown agent")
    relevant = [msg for msg in messages if msg["to"] in {agent, "all"}]
    # Prioritize unread communication while leaving recent acknowledgments visible.
    unread = [msg for msg in relevant if agent not in msg["acknowledged_by"]]
    read = [msg for msg in relevant if agent in msg["acknowledged_by"]]
    return (unread + read)[:limit]


def markdown(messages: list[dict], agent: str, limit: int = 6) -> str:
    output = []
    for msg in for_agent(messages, agent, limit=limit):
        acked = agent in msg["acknowledged_by"]
        state = "ACK REPORTED" if acked else "AWAITING ACK"
        ref = f" PR #{msg['pr']}" if msg["pr"] else ""
        clean = lambda value: str(value).replace("\r", " ").replace("\n", " ")\
            .replace("<", "&lt;").replace(">", "&gt;").replace("[", "\\[").replace("]", "\\]")
        output.append(
            f"- **{state} — {msg['kind']} / {clean(msg['task'])}{ref}:** "
            f"{clean(msg['summary'])} "
            f"**Next:** {clean(msg['next'])} "
            f"([source comment]({msg['url']}), ID {msg['id']})"
        )
    return "\n".join(output) if output else (
        "No new structured messages addressed to this agent. "
        "Check your claimed PR's latest HANDOFF and #15/#23 for unstructured updates."
    )
