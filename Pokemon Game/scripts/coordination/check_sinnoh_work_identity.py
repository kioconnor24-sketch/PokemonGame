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


def map_files(pr: dict, *, added_only: bool = False,
              definitions_only: bool = False) -> set[str]:
    ids = set()
    for entry in pr.get("files", []):
        if isinstance(entry, str):
            path, status = entry, "modified"
        else:
            path, status = entry.get("filename", ""), entry.get("status", "")
        if status == "removed" or (added_only and status != "added"):
            continue
        if definitions_only and not path.endswith("/map.json"):
            continue
        found = map_from_path(path)
        if found:
            ids.add(found)
    return ids


def adds_identity(row: dict) -> bool:
    # GitHub reports a moved map definition as "renamed", not "added".
    # Renaming a file inside the same map remains an ordinary repair.
    path = row.get("filename", "")
    previous = row.get("previous_filename") or ""
    return row.get("status") in {"added", "copied"} or (
        row.get("status") == "renamed"
        and (map_from_path(previous) != map_from_path(path)
             or previous.startswith(ENGINE_MAPS) != path.startswith(ENGINE_MAPS)))


def new_definitions(pr: dict, prefix: str) -> set[str]:
    # Supporting files and modified return doors do not allocate map identities.
    return {
        map_from_path(row["filename"]) for row in pr.get("files", [])
        if isinstance(row, dict) and adds_identity(row)
        and row.get("filename", "").startswith(prefix)
        and row["filename"].endswith("/map.json")
    } - {None}


def added_payload_maps(pr: dict, prefix: str) -> set[str]:
    """Map identities touched by added/moved files, including partial payloads."""
    return {
        map_from_path(row["filename"]) for row in pr.get("files", [])
        if isinstance(row, dict) and adds_identity(row)
        and row.get("filename", "").startswith(prefix)
    } - {None}


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
    added_staged = new_definitions(pr, SOURCE)
    added_engine = new_definitions(pr, ENGINE_MAPS)
    staged_payloads = added_payload_maps(pr, SOURCE)
    engine_payloads = added_payload_maps(pr, ENGINE_MAPS)
    existing = {canonical(m) for m in snapshot.get("main_maps", [])}
    production = {canonical(m) for m in snapshot.get("main_engine_maps", [])}
    cited_source, cited_engine = set(), set()
    for peer in snapshot.get("other_open_prs", []):
        if int(peer["number"]) == number or f"#{peer['number']}" not in spec["sources"]:
            continue
        cited_source |= map_files(peer, definitions_only=True)
        engine_only = {"files": [
            row for row in peer.get("files", [])
            if (row if isinstance(row, str) else row.get("filename", "")).startswith(ENGINE_MAPS)
        ]}
        cited_engine |= map_files(engine_only, definitions_only=True)
    # A new directory cannot evade classification by omitting map.json.
    # A supporting file for a real main/cited definition remains a repair.
    new_engine_payloads = engine_payloads - production - cited_engine
    if mode != "integrate" and (added_engine or new_engine_payloads):
        errors.append("added engine map output requires integrate mode")
    if mode == "repair" and (added_staged or staged_payloads - existing - cited_source):
        errors.append("repair cannot introduce new staged maps; use construct or source-backed reuse")
    if mode == "reuse" and staged_payloads:
        # A claimed upstream must actually contain each reused identity. A mere
        # Sinnoh-Sources label is not evidence that geometry already exists.
        proved = cited_source | (existing if "main" in spec["sources"] else set())
        missing = staged_payloads - proved
        if missing:
            errors.append("reuse source does not contain staged maps: " + ", ".join(sorted(missing)))
    if mode == "construct":
        new_maps = added_staged
        if not new_maps:
            errors.append("construct requires added staged map outputs; scripts/plans are not constructed maps")
        if new_maps - maps:
            errors.append("undeclared newly staged map identities: " + ", ".join(sorted(new_maps - maps)))
        conflict = new_maps & existing
        if conflict:
            errors.append("already on main; reuse rather than reconstruct: " + ", ".join(sorted(conflict)))
        for peer in snapshot.get("other_open_prs", []):
            if int(peer["number"]) == number:
                continue
            occupied = map_files(peer)
            peer_spec, peer_errors = claim(peer.get("body", ""))
            if not peer_errors and peer_spec["mode"] in {"construct", "integrate"}:
                occupied |= peer_spec["maps"]
            shared = new_maps & occupied
            if shared:
                errors.append("map identity already in open PR #{}: {}".format(
                    peer["number"], ", ".join(sorted(shared))))
    elif mode == "integrate":
        if not added_engine:
            errors.append("integrate requires actual engine/data/maps output; a DEV scene is not production")
        already_production = added_engine & production
        if already_production:
            errors.append("already installed in production: " + ", ".join(sorted(already_production)))
        # Two independently open production installs for the same map are not
        # disjoint work. A child repair uses the explicit 'repair' mode instead.
        for peer in snapshot.get("other_open_prs", []):
            if int(peer["number"]) == number:
                continue
            old_engine = new_definitions(peer, ENGINE_MAPS)
            peer_spec, peer_errors = claim(peer.get("body", ""))
            if not peer_errors and peer_spec["mode"] == "integrate":
                old_engine |= peer_spec["maps"] - production
            shared = added_engine & old_engine
            if shared:
                errors.append("production registration already proposed in PR #{}: {}".format(
                    peer["number"], ", ".join(sorted(shared))))
    return errors


def guard_snapshot(data: dict, main_root: Path) -> dict:
    """Reuse the required file guard's read-only metadata and trusted checkout.

    The legacy file guard retains its own snapshot fields and validator. Raw
    identity metadata comes from the same already-fetched GitHub file rows;
    source definitions are inventoried only from the trusted-main checkout.
    """
    def metadata(pr: dict, *, head: bool = False) -> dict:
        if (not isinstance(pr, dict) or type(pr.get("number")) is not int
                or pr["number"] <= 0 or not isinstance(pr.get("body"), str)
                or not isinstance(pr.get("files"), list)):
            raise ValueError("required guard identity metadata is missing or malformed")
        if head and not re.fullmatch(r"[a-f0-9]{40}", pr.get("head_sha", "")):
            raise ValueError("required guard is missing the exact PR head")
        for row in pr["files"]:
            if (not isinstance(row, dict) or not isinstance(row.get("filename"), str)
                    or not row["filename"] or row.get("status") not in {
                        "added", "removed", "modified", "renamed", "copied", "changed", "unchanged"}
                    or (row["status"] == "renamed" and not row.get("previous_filename"))
                    or (row.get("previous_filename") is not None
                        and not isinstance(row["previous_filename"], str))):
                raise ValueError("required guard file status/rename metadata is incomplete")
        return pr

    own = metadata(data["pull_request"], head=True)
    peers = data["identity_peers"]
    if not isinstance(peers, list):
        raise ValueError("required guard identity peer inventory is missing")
    peers = [metadata(peer) for peer in peers]
    peer_numbers = [peer["number"] for peer in peers]
    legacy_peers = data["other_open_prs"]
    if (not isinstance(legacy_peers, list) or len(peer_numbers) != len(set(peer_numbers))
            or set(peer_numbers) != {peer["number"] for peer in legacy_peers}):
        raise ValueError("required guard identity peer inventory is incomplete")
    for peer in peers:
        legacy = next(p for p in legacy_peers if p["number"] == peer["number"])
        if set(legacy["files"]) != {
                row["filename"] for row in peer["files"] if row["status"] != "removed"}:
            raise ValueError("required guard peer file inventory is incomplete")

    main_root = main_root.resolve()
    definitions = []
    for relative in (SOURCE, ENGINE_MAPS):
        directory = main_root / relative
        if not directory.is_dir():
            raise ValueError("trusted-main geography directory is missing: " + relative)
        definitions.extend(p.relative_to(main_root).as_posix()
                           for p in directory.rglob("map.json") if p.is_file())
    return {
        "candidate": own, "other_open_prs": peers,
        "main_maps": [name for p in definitions for name in [map_from_path(p)] if name],
        "main_engine_maps": [map_from_path(p) for p in definitions if p.startswith(ENGINE_MAPS)],
    }


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
                  "status": "added" if mode in {"construct", "reuse"} else "modified"} for n in names]
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
    if mode in MODES:
        open_prs = pages("pulls?state=open")
        cited = {ref.strip() for ref in sources.split(",")}
        for peer in open_prs:
            if mode == "repair" and f"#{peer['number']}" not in cited:
                continue
            file_rows = pages(f"pulls/{peer['number']}/files")
            snapshot["other_open_prs"].append({
                "number": peer["number"], "body": peer.get("body", ""),
                "files": [{"filename": f["filename"], "status": f["status"],
                           "previous_filename": f.get("previous_filename")} for f in file_rows],
            })
        # There is no pull request for this CLI proposal. Give it a number
        # outside the current live PR inventory, not an existing PR's number.
        candidate["number"] = max([CUTOFF] + [
            int(peer["number"]) for peer in open_prs]) + 1
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path, nargs="?")
    parser.add_argument("--guard-snapshot", type=Path,
                        help="reuse required file-guard metadata with this trusted-main checkout")
    parser.add_argument("--preflight", choices=sorted(MODES))
    parser.add_argument("--maps", default="")
    parser.add_argument("--sources", default="")
    args = parser.parse_args()
    if sum(bool(x) for x in (args.snapshot, args.guard_snapshot, args.preflight)) > 1:
        parser.error("choose one snapshot, --guard-snapshot or --preflight")
    if args.preflight:
        try:
            snapshot = preflight(args.preflight, args.maps, args.sources)
        except Exception as err:
            print("FAIL: live GitHub preflight unavailable; do not start duplicate work:", err)
            return 1
    elif args.guard_snapshot:
        try:
            snapshot = guard_snapshot(json.loads(args.guard_snapshot.read_text(encoding="utf-8")),
                                      Path(__file__).resolve().parents[3])
        except (OSError, ValueError, KeyError, TypeError) as err:
            print("FAIL: required guard identity snapshot unavailable:", err)
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

