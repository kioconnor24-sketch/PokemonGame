#!/usr/bin/env python3
"""Audit trade evolutions for solo-play alternatives using REAL species source.

Finding an EVO_ITEM alternative does not prove that item is obtainable during
Averon or Sinnoh; that requires a separate item/shop/quest reachability audit.
"""
import argparse
import csv
import json
import re
from pathlib import Path

ENTRY = re.compile(r"^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{", re.M)
EVOLUTION = re.compile(
    r"\{\s*(EVO_[A-Z0-9_]+)\s*,\s*([A-Z0-9_]+|0|\d+)\s*,\s*(SPECIES_[A-Z0-9_]+)"
)
INCLUDE = re.compile(r'^\s*#\s*include\s+"species_info/(gen_[1-9]_families\.h)"', re.M)
OUTPUT = ("origin", "target", "trade_conditions", "solo_alternatives",
          "status", "source_file")


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def species_entries(text):
    source = strip_comments(text)
    for match in ENTRY.finditer(source):
        start, level, end = match.end(), 1, match.end()
        while end < len(source) and level:
            if source[end] == "{":
                level += 1
            elif source[end] == "}":
                level -= 1
            end += 1
        if level:
            raise ValueError("Unterminated species initializer " + match.group(1))
        yield match.group(1), source[start:end - 1]


def audit_family(filename, source):
    rows = []
    for origin, body in species_entries(source):
        paths = list(EVOLUTION.finditer(body))
        for match in paths:
            method, requirement, target = match.groups()
            if method != "EVO_TRADE":
                continue
            alternatives = sorted({
                f"{m.group(1)}: {m.group(2)}"
                for m in paths
                if m.group(3) == target and m.group(1) != "EVO_TRADE"
                and m.group(1) != "EVO_NONE"
            })
            rows.append({
                "origin": origin,
                "target": target,
                "trade_conditions": requirement,
                "solo_alternatives": "; ".join(alternatives),
                "status": ("SOURCE_ALTERNATIVE_FOUND" if alternatives
                           else "TRADE_ONLY_SOURCE"),
                "source_file": filename,
            })
    return rows


def audit(engine):
    root = engine / "src/data/pokemon"
    wrapper = (root / "species_info.h").read_text(encoding="utf-8")
    files = INCLUDE.findall(wrapper)
    if len(files) != 9:
        raise ValueError("Expected exactly the 9 generation family includes")
    rows = []
    for name in files:
        path = root / "species_info" / name
        if not path.is_file():
            raise FileNotFoundError(path)
        rows.extend(audit_family(name, path.read_text(encoding="utf-8")))
    return {
        "scope": "Source-defined EVO_TRADE destination alternatives; not item availability or runtime",
        "summary": {
            "trade_evolution_routes": len(rows),
            "trade_only_source_routes": sum(r["status"] == "TRADE_ONLY_SOURCE" for r in rows),
            "source_alternatives_present": sum(r["status"] == "SOURCE_ALTERNATIVE_FOUND" for r in rows),
        },
        "unresolved": [r for r in rows if r["status"] == "TRADE_ONLY_SOURCE"],
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", required=True, type=Path)
    ap.add_argument("--json", required=True, type=Path)
    ap.add_argument("--csv", required=True, type=Path)
    args = ap.parse_args()
    report = audit(args.engine)
    for path in (args.json, args.csv):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT)
        writer.writeheader()
        writer.writerows(report["rows"])
    print(json.dumps(report["summary"], indent=2))
    if not report["rows"]:
        raise SystemExit("No trade evolutions identified: likely parser breakage")


if __name__ == "__main__":
    main()
