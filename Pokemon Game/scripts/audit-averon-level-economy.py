#!/usr/bin/env python3
"""Source-grounded Pokémon Averon EXP economy inventory.

Read Emerald Expansion's actual trainers.party, enabled species families and
growth formula source. Never confuse compiled trainer definitions with reachable
encounters or base EXP yields with actual awarded battle EXP.
"""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

HEADER = re.compile(r"^===\s+(TRAINER_[A-Z0-9_]+)\s+===\s*$", re.M)
MON = re.compile(r"^\s*(?:([^(]+?)\s+\()?(?:SPECIES_)?([A-Za-z0-9_. -]+?)\)?(?:\s+\([MF]\))?(?:\s+@\s+.+)?\s*$")
SPECIES_ENTRY = re.compile(r"^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{", re.M)
FAMILY_INCLUDE = re.compile(r'^\s*#\s*include\s+"species_info/([^"]+)"', re.M)
FIELD = re.compile(r"\.(speciesName|expYield|growthRate|natDexNum)\s*=\s*([^,\n]+)")
OUTPUT_FIELDS = ("trainer", "name", "species", "level", "default_level",
                 "species_source_id", "growth_rate", "exp_yield_source",
                 "exp_yield_numeric")


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def species_initializers(source):
    """Nested-brace-aware species record parsing."""
    clean = strip_comments(source)
    for match in SPECIES_ENTRY.finditer(clean):
        start, depth, i = match.end(), 1, match.end()
        while i < len(clean) and depth:
            if clean[i] == "{":
                depth += 1
            elif clean[i] == "}":
                depth -= 1
            i += 1
        if depth:
            raise ValueError("Unterminated species initializer " + match.group(1))
        yield match.group(1), clean[start:i - 1]


def load_species_data(engine):
    root = engine / "src/data/pokemon"
    wrapper = (root / "species_info.h").read_text(encoding="utf-8")
    # Explicitly read every locally included Gen 1-9 family file.
    included = FAMILY_INCLUDE.findall(wrapper)
    if len(included) < 9:
        raise ValueError("Expected Gen 1-9 family includes in source")
    index = {}
    for filename in included:
        safe = (root / "species_info" / filename).resolve()
        if not safe.is_relative_to((root / "species_info").resolve()):
            raise ValueError("Species include path escaped repository")
        for species_id, body in species_initializers(safe.read_text(encoding="utf-8")):
            fields = dict(FIELD.findall(body))
            label = re.search(r'_\("([^"]+)"\)', fields.get("speciesName", ""))
            if not label:
                continue
            name = label.group(1)
            growth = fields.get("growthRate", "")
            expression = fields.get("expYield", "").strip()
            numeric = int(expression) if re.fullmatch(r"\d+", expression) else None
            # Multiple forms can share a display name; retain all possibilities.
            key = name.casefold()
            index.setdefault(key, []).append({
                "source_id": species_id, "name": name, "growth_rate": growth,
                "exp_yield_source": expression, "exp_yield_numeric": numeric,
                "nat_dex": fields.get("natDexNum", ""),
            })
    return index


def parse_party_data(source):
    """Parse trainerproc source blocks without fabricating omitted default levels."""
    clean = strip_comments(source)
    matches = list(HEADER.finditer(clean))
    results = []
    for i, match in enumerate(matches):
        trainer = match.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(clean)
        block = clean[match.end():end]
        pieces = [p.strip() for p in re.split(r"\n\s*\n", block) if p.strip()]
        metadata = {}
        party = []
        for piece in pieces:
            lines = [line.strip() for line in piece.splitlines() if line.strip()]
            if not lines:
                continue
            first = lines[0]
            if first.startswith(("Name:", "Class:", "Pic:", "Gender:", "Music:",
                                 "Items:", "Battle Type:", "AI:", "Mugshot:",
                                 "Starting Status:", "Double Battle:", "Multi Party:")):
                for line in lines:
                    key, colon, value = line.partition(":")
                    if colon and key not in metadata:
                        metadata[key.strip()] = value.strip()
                continue
            # Pokemon blocks are separated by blank lines, which is documented
            # in trainerproc's own file header.
            raw_species = re.sub(r"\s+@\s+.*$", "", first).strip()
            raw_species = re.sub(r"^.+?\((SPECIES_[A-Z0-9_]+)\)(?:\s+\([MF]\))?$",
                                 r"\1", raw_species)
            if raw_species.startswith("SPECIES_"):
                species = raw_species[8:].replace("_", " ").title()
            else:
                species = re.sub(r"\s+\([MF]\)$", "", raw_species)
            level_line = next((line for line in lines if line.startswith("Level:")), None)
            level = 100 if level_line is None else int(level_line.split(":", 1)[1].strip())
            if not 1 <= level <= 100:
                raise ValueError(f"Out-of-range level for {trainer}: {level}")
            party.append({"species": species, "level": level,
                          "default_level": level_line is None})
        if party:
            results.append({"trainer": trainer, "name": metadata.get("Name", ""),
                            "class": metadata.get("Class", ""),
                            "pokemon": party})
    return results


def required_experience(growth_rate, level):
    """C-expression-equivalent EXP total for relevant Emerald growth groups.

    Derived directly from src/data/pokemon/experience_tables.h. EXP total is
    distinct from experience *awarded* for winning a trainer battle.
    """
    if not 1 <= level <= 100:
        raise ValueError("Level outside 1..100")
    n = level
    n3 = n * n * n
    formulas = {
        "GROWTH_MEDIUM_FAST": lambda: n3,
        "GROWTH_FAST": lambda: 4 * n3 // 5,
        "GROWTH_SLOW": lambda: 5 * n3 // 4,
        "GROWTH_MEDIUM_SLOW": lambda: max(0, 6 * n3 // 5 - 15 * n * n + 100 * n - 140),
        "GROWTH_ERRATIC": lambda:
            ((100 - n) * n3 // 50 if n <= 50
             else (150 - n) * n3 // 100 if n <= 68
             else ((1911 - 10 * n) // 3) * n3 // 500 if n <= 98
             else (160 - n) * n3 // 100),
        "GROWTH_FLUCTUATING": lambda:
            (((n + 1) // 3 + 24) * n3 // 50 if n <= 15
             else (n + 14) * n3 // 50 if n <= 36
             else (n // 2 + 32) * n3 // 50),
    }
    if growth_rate not in formulas:
        raise ValueError("Unknown growth group " + growth_rate)
    return formulas[growth_rate]()


def collect(engine, prefix="TRAINER_AVERON_"):
    index = load_species_data(engine)
    entries = [t for t in parse_party_data(
        (engine / "src/data/trainers.party").read_text(encoding="utf-8"))
        if t["trainer"].startswith(prefix)]
    rows = []
    missing = []
    for trainer in entries:
        for mon in trainer["pokemon"]:
            variants = index.get(mon["species"].casefold(), [])
            unique = variants[0] if len(variants) == 1 else None
            if unique is None:
                missing.append({"trainer": trainer["trainer"],
                                "species": mon["species"],
                                "issue": ("unknown species display name" if not variants
                                          else "ambiguous display name / multiple forms")})
            rows.append({
                "trainer": trainer["trainer"], "name": trainer["name"],
                "species": mon["species"], "level": mon["level"],
                "default_level": mon["default_level"],
                "species_source_id": unique["source_id"] if unique else "",
                "growth_rate": unique["growth_rate"] if unique else "",
                "exp_yield_source": unique["exp_yield_source"] if unique else "",
                "exp_yield_numeric": unique["exp_yield_numeric"] if unique and unique["exp_yield_numeric"] is not None else "",
            })
    totals = {
        "trainer_definitions": len(entries),
        "pokemon_party_records": len(rows),
        "highest_defined_opponent_level": max((m["level"] for m in rows), default=None),
        "defaulted_to_level_100": sum(bool(m["default_level"]) for m in rows),
        "unresolved_species_form_references": len(missing),
    }
    # This is a *reference curve*, not a projection of an actual playthrough.
    growth = ["GROWTH_FAST", "GROWTH_MEDIUM_FAST", "GROWTH_MEDIUM_SLOW",
              "GROWTH_SLOW", "GROWTH_ERRATIC", "GROWTH_FLUCTUATING"]
    benchmarks = [30, 40, 50, 55, 60, 65, 70, 76, 80, 90, 100]
    requirements = {str(lvl): {g: required_experience(g, lvl) for g in growth}
                    for lvl in benchmarks}
    return {
        "source": "Native trainers.party and src/data/pokemon/species_info/gen_*_families.h",
        "scope": "DEFINED trainers with prefix; not guaranteed accessible encounters",
        "caution": "EXP yield is a source reference; no player EXP award or route pacing inferred",
        "summary": totals,
        "trainer_aces": [
            {"trainer": t["trainer"], "name": t["name"], "ace_level":
             max(mon["level"] for mon in t["pokemon"]),
             "party_size": len(t["pokemon"])}
            for t in entries],
        "unresolved": missing,
        "pokemon": rows,
        "cumulative_exp_required_by_growth_group": requirements,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--prefix", default="TRAINER_AVERON_")
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    report = collect(args.engine, args.prefix)
    for path in (args.json, args.csv):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(report["pokemon"])
    print(json.dumps(report["summary"], indent=2))
    if report["summary"]["trainer_definitions"] == 0:
        raise SystemExit("No matching trainer definitions; check prefix and branch")


if __name__ == "__main__":
    main()
