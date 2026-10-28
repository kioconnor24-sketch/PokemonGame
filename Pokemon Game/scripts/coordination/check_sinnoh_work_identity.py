#!/usr/bin/env python3
"""Read-only, fail-closed preflight for *new* Sinnoh geography claims.

The trusted workflow supplies live PR metadata and main's actual map tree.
No PR code is executed, no branches/claims are changed, and pre-existing
PRs (<=354) retain their existing contract. A repair or source reuse is not
new geometry; it must cite its actual upstream source.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CUTOFF = 354  # PRs already open when the identity contract was introduced
ROOT = "Pokemon Game/"
SOURCE = ROOT + "Averon_Codex_Handoff/design/sinnoh/"
ENGINE_MAPS = ROOT + "engine/data/maps/"
ENGINE_LAYOUTS = ROOT + "engine/data/layouts/"
MODES = {"construct", "reuse", "integrate", "repair"}
MAP_SEGMENT = re.compile(r"/staged/([^/]+)/")
LABEL = re.compile(r"(?im)^(Sinnoh-(?:Work|Maps|Sources)):[ \t]*(.*?)[ \t]*$")


def canonical(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.removesuffix("-dev-overlay").lower())


def map_from_path(path: str) -> str | None:
    if path.startswith(SOURCE):
        m = MAP_SEGMENT.search(path)
        return canonical(m.group(1)) if m else None
    if path.startswith(ENGINE_MAPS):
        parts = path[len(ENGINE_MAPS):].split("/")
        return canonical(parts[0]) if len(parts) >= 2 else None
    return None


def map_files(pr: dict, *, added_only: bool = False) -> set[str]:
    ids = set()
    for entry in pr.get("files", []):
        if isinstance(entry, str):
            path, status = entry, "modified"
        else:
            path, status = entry.get("filename", ""), entry.get("status", "")
        if status == "removed" or (added_only and status != "added"):
            continue
        found = map_from_path(path)
        if found:
            ids.add(found)
    return ids


def is_geography(pr: dict) -> bool:
    for entry in pr.get("files", []):
        name = entry if isinstance(entry, str) else entry.get("filename", "")
        if name.startswith((ENGINE_MAPS, ENGINE_LAYOUTS)):
            return True
        if name.startswith(SOURCE) and (
            "/staged/" in name
            or name.endswith((".py", "source-pins.json"))
        ):
            return True
    return False


def claim(body: str) -> tuple[dict, list[str]]:
    matches: dict[str, list[str]] = {}
    for key, val in LABEL.findall(body or ""):
        matches.setdefault(key.lower(), []).append(val.strip())
    errors = [f"duplicate {key} field" for key, vals in matches.items() if len(vals) > 1]
    values = {key: vals[0] for key, vals in matches.items()}
    mode = values.get("sinnoh-work", "").lower()
    if mode not in MODES:
        errors.append("set Sinnoh-Work: construct|reuse|integrate|repair")
    raw_maps = [v.strip() for v in values.get("sinnoh-maps", "").split(",") if v.strip()]
    if not raw_maps or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", m) for m in raw_maps):
        errors.append("set Sinnoh-Maps: comma-separated canonical map names")
    names = [canonical(m) for m in raw_maps]
    if len(names) != len(set(names)):
        errors.append("duplicate map in Sinnoh-Maps")
    sources = [s.strip() for s in values.get("sinnoh-sources", "").split(",") if s.strip()]
    if mode in {"reuse", "integrate", "repair"} and (
        not sources or any(not re.fullmatch(r"main|#[1-9][0-9]*", s, re.I) for s in sources)
    ):
        errors.append("reuse/integrate/repair must cite Sinnoh-Sources: main or #PR")
    return {"mode": mode, "maps": set(names), "sources": sources}, errors


def validate(snapshot: dict) -> list[str]:
    pr = snapshot["candidate"]
    number = int(pr["number"])
    if number <= CUTOFF or not is_geography(pr):
        return []
    spec, errors = claim(pr.get("body", ""))
    if errors:
        return errors
    mode, maps = spec["mode"], spec["maps"]
    touched = map_files(pr)
    unknown = touched - maps
    if unknown:
        errors.append("changed map identities missing from Sinnoh-Maps: " + ", ".join(sorted(unknown)))
    if mode == "construct":
        new_maps = map_files(pr, added_only=True)
        if not new_maps:
            errors.append("construct requires added staged map outputs; scripts/plans are not constructed maps")
        if new_maps - maps:
            errors.append("undeclared newly staged map identities: " + ", ".join(sorted(new_maps - maps)))
        existing = {canonical(m) for m in snapshot.get("main_maps", [])}
        conflict = maps & existing
        if conflict:
            errors.append("already on main; reuse rather than reconstruct: " + ", ".join(sorted(conflict)))
        for peer in snapshot.get("other_open_prs", []):
            if int(peer["number"]) == number:
                continue
            occupied = map_files(peer)
            peer_spec, peer_errors = claim(peer.get("body", ""))
            if not peer_errors and peer_spec["mode"] in {"construct", "integrate"}:
                occupied |= peer_spec["maps"]
            shared = maps & occupied
            if shared:
                errors.append("map identity already in open PR #{}: {}".format(
                    peer["number"], ", ".join(sorted(shared))))
    elif mode == "integrate":
        # Two independently open production installs for the same map are not
        # disjoint work. A child repair uses the explicit 'repair' mode instead.
        for peer in snapshot.get("other_open_prs", []):
            if int(peer["number"]) == number:
                continue
            old_engine = {
                map_from_path(f["filename"] if isinstance(f, dict) else f)
                for f in peer.get("files", [])
                if (f["filename"] if isinstance(f, dict) else f).startswith(ENGINE_MAPS)
            }
            peer_spec, peer_errors = claim(peer.get("body", ""))
            if not peer_errors and peer_spec["mode"] == "integrate":
                old_engine |= peer_spec["maps"]
            shared = maps & (old_engine - {None})
            if shared:
                errors.append("production registration already proposed in PR #{}: {}".format(
                    peer["number"], ", ".join(sorted(shared))))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    errors = validate(json.loads(args.snapshot.read_text(encoding="utf-8")))
    for e in errors:
        print("FAIL:", e)
    if errors:
        return 1
    print("PASS: unique Sinnoh work identity / explicit source reuse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
