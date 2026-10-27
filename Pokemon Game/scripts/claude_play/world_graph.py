#!/usr/bin/env python3
"""Sinnoh world link graph (C41 tracker): which production and staged maps are joined, and which groups are apart.

Nodes are the production gMapGroup_Sinnoh maps plus every staged map of the given checkouts
(design/sinnoh/*/staged/<Map>/map.json, and the source_headers of a family's *recipe*.json); `<Map>-dev-overlay`
headers add their warps and connections to the map they overlay. An edge is a warp or connection whose destination
is a known node. Read-only: nothing is written but the report.

  world_graph.py ROOT [ROOT ...] [--json OUT]      ROOT: a repository checkout (main first, then branch worktrees)
"""
import argparse
import collections
import json
import pathlib

ENGINE = "Pokemon Game/engine"
DESIGN = "Pokemon Game/Averon_Codex_Handoff/design/sinnoh"


def load(roots):
    """{map id: source label}, {map id: set of destination ids}."""
    nodes, edges = {}, collections.defaultdict(set)

    def add(h, label, overlay=False):
        if not overlay:
            nodes.setdefault(h["id"], label)
        for w in h.get("warp_events") or []:
            if w.get("dest_map"):
                edges[h["id"]].add(w["dest_map"])
        for c in h.get("connections") or []:
            edges[h["id"]].add(c["map"])

    engine = pathlib.Path(roots[0]) / ENGINE
    for name in json.loads((engine / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]:
        add(json.loads((engine / f"data/maps/{name}/map.json").read_text()), "production")
    for root in roots:
        for path in sorted((pathlib.Path(root) / DESIGN).glob("*/*recipe*.json")):
            headers = json.loads(path.read_text()).get("source_headers")
            if isinstance(headers, dict):
                for h in headers.values():
                    if isinstance(h, dict) and "id" in h:
                        add(h, path.parts[-2])
        for path in sorted((pathlib.Path(root) / DESIGN).glob("*/staged/*/map.json")):
            try:
                h = json.loads(path.read_text())
            except ValueError:
                continue
            if "id" in h:
                add(h, path.parts[-4], overlay=path.parts[-2].endswith("-dev-overlay"))
    return nodes, edges


def components(nodes, edges):
    adj = collections.defaultdict(set)
    for a, dests in edges.items():
        for b in dests:
            if a in nodes and b in nodes and a != b:
                adj[a].add(b)
                adj[b].add(a)
    seen, out = set(), []
    for n in sorted(nodes):
        if n in seen:
            continue
        comp, stack = set(), [n]
        while stack:
            x = stack.pop()
            if x not in comp:
                comp.add(x)
                stack.extend(adj[x] - comp)
        seen |= comp
        out.append(sorted(comp))
    out.sort(key=lambda c: (-len(c), c))
    links = sum(len(v) for v in adj.values()) // 2
    return out, links


def report(roots):
    nodes, edges = load(roots)
    comps, links = components(nodes, edges)
    return {"maps": len(nodes), "production": sum(v == "production" for v in nodes.values()), "links": links,
            "components": [{"size": len(c), "production": sum(nodes[m] == "production" for m in c),
                            "sources": dict(collections.Counter(nodes[m] for m in c).most_common()),
                            "maps": c} for c in comps]}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("roots", nargs="+", type=pathlib.Path)
    p.add_argument("--json", type=pathlib.Path)
    a = p.parse_args()
    r = report(a.roots)
    if a.json:
        a.json.write_text(json.dumps(r, indent=2) + "\n")
    print(f"{r['maps']} maps ({r['production']} production), {r['links']} links, {len(r['components'])} components")
    for c in r["components"]:
        print(f"  {c['size']:4d} maps, {c['production']:2d} production: "
              + ", ".join(f"{k} {v}" for k, v in list(c["sources"].items())[:6])
              + ("" if c["size"] > 8 else "  [" + ", ".join(c["maps"]) + "]"))
