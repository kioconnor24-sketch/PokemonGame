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
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

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
    added_staged = {
        map_from_path(row["filename"]) for row in pr.get("files", [])
        if isinstance(row, dict) and row.get("status") == "added"
        and row.get("filename", "").startswith(SOURCE)
        and "/staged/" in row["filename"]
    } - {None}
    if mode == "repair" and added_staged:
        errors.append("repair cannot introduce new staged maps; use construct or source-backed reuse")
    if mode == "reuse" and added_staged:
        # A claimed upstream must actually contain each reused identity. A mere
        # Sinnoh-Sources label is not evidence that geometry already exists.
        proved = set()
        if "main" in spec["sources"]:
            proved |= {canonical(m) for m in snapshot.get("main_maps", [])}
        for peer in snapshot.get("other_open_prs", []):
            if f"#{peer['number']}" in spec["sources"]:
                # Proof needs a real map file in that PR, not an unverified
                # map name listed in its description.
                proved |= map_files(peer)
        missing = added_staged - proved
        if missing:
            errors.append("reuse source does not contain staged maps: " + ", ".join(sorted(missing)))
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
        engine_maps = {
            map_from_path(row["filename"]) for row in pr.get("files", [])
            if isinstance(row, dict) and row.get("status") != "removed"
            and row.get("filename", "").startswith(ENGINE_MAPS)
        } - {None}
        if not engine_maps:
            errors.append("integrate requires actual engine/data/maps output; a DEV scene is not production")
        already_production = maps & {
            canonical(m) for m in snapshot.get("main_engine_maps", [])
        }
        if already_production:
            errors.append("already installed in production: " + ", ".join(sorted(already_production)))
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


def fetch_live(path: str) -> object:
    """Public GitHub API; GH_TOKEN/GITHUB_TOKEN raises the public rate limit."""
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "sinnoh-identity-preflight"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request("https://api.github.com/repos/kioconnor24-sketch/PokemonGame/" + path,
                  headers=headers)
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def pages(path: str) -> list[dict]:
    items = []
    for page in range(1, 30):
        separator = "&" if "?" in path else "?"
        part = fetch_live(path + f"{separator}per_page=100&page={page}")
        if not isinstance(part, list):
            raise ValueError("unexpected GitHub pagination response")
        items.extend(part)
        if len(part) < 100:
            return items
    raise ValueError("GitHub pagination limit reached; refusing incomplete claims")


def preflight(mode: str, maps: str, sources: str) -> dict:
    """Run before new map work, rather than wasting time writing a duplicate PR."""
    names = [n.strip() for n in maps.split(",") if n.strip()]
    root = SOURCE + "_preflight/staged/"
    if mode == "integrate":
        files = [{"filename": ENGINE_MAPS + n + "/map.json", "status": "added"} for n in names]
    else:
        files = [{"filename": root + n + "/map.json",
                  "status": "added" if mode == "construct" else "modified"} for n in names]
    candidate = {"number": CUTOFF + 1, "files": files,
                 "body": f"Sinnoh-Work: {mode}\nSinnoh-Maps: {maps}\nSinnoh-Sources: {sources}\n"}
    snapshot = {"candidate": candidate, "main_maps": [], "main_engine_maps": [],
                "other_open_prs": []}
    tree = fetch_live("git/trees/main?recursive=1")
    if tree.get("truncated"):
        raise ValueError("main tree truncated; map ownership cannot be checked")
    snapshot["main_maps"] = [
        name for row in tree["tree"] if row["type"] == "blob"
        if row["path"].endswith("/map.json")
        for name in [map_from_path(row["path"])] if name
    ]
    snapshot["main_engine_maps"] = [
        row["path"][len(ENGINE_MAPS):].split("/")[0]
        for row in tree["tree"] if row["type"] == "blob"
        and row["path"].startswith(ENGINE_MAPS) and row["path"].endswith("/map.json")
    ]
    if mode in {"construct", "integrate", "reuse"}:
        for peer in pages("pulls?state=open"):
            file_rows = pages(f"pulls/{peer['number']}/files")
            snapshot["other_open_prs"].append({
                "number": peer["number"], "body": peer.get("body", ""),
                "files": [{"filename": f["filename"], "status": f["status"]} for f in file_rows],
            })
        # There is no pull request for this CLI proposal. Give it a number
        # outside the current live PR inventory, not an existing PR's number.
        candidate["number"] = max([CUTOFF] + [
            int(peer["number"]) for peer in snapshot["other_open_prs"]]) + 1
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path, nargs="?")
    parser.add_argument("--preflight", choices=sorted(MODES))
    parser.add_argument("--maps", default="")
    parser.add_argument("--sources", default="")
    args = parser.parse_args()
    if args.preflight:
        try:
            snapshot = preflight(args.preflight, args.maps, args.sources)
        except Exception as err:
            print("FAIL: live GitHub preflight unavailable; do not start duplicate work:", err)
            return 1
    elif args.snapshot:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    else:
        parser.error("supply a trusted snapshot or --preflight with --maps")
    errors = validate(snapshot)
    for e in errors:
        print("FAIL:", e)
    if errors:
        return 1
    print("PASS: unique Sinnoh work identity / explicit source reuse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
