#!/usr/bin/env python3
"""Audit source-level engine readiness for the Pokémon Averon requirements.

No claim about game runtime behavior is made from these configuration checks.
This tool reads an existing Emerald Expansion checkout; it never changes it.
"""
import argparse
import json
import re
from pathlib import Path

EXPECTED = [
    *[(f"species_enabled.h", f"P_GEN_{n}_POKEMON", "TRUE", "Gen I–IX species compile configuration") for n in range(1, 10)],
    ("species_enabled.h", "P_MEGA_EVOLUTIONS", "TRUE", "Mega Evolution species support"),
    ("species_enabled.h", "P_PRIMAL_REVERSIONS", "FALSE", "No Primal Reversion forms"),
    ("species_enabled.h", "P_ULTRA_BURST_FORMS", "FALSE", "No Ultra Burst forms"),
    ("item.h", "I_EXP_SHARE_ITEM", "GEN_5", "Held-item EXP Share"),
    ("item.h", "I_EXP_SHARE_FLAG", "0", "No party-wide EXP Share flag"),
    ("overworld.h", "OW_POKEMON_OBJECT_EVENTS", "TRUE", "Pokémon overworld object events"),
    ("overworld.h", "OW_FOLLOWERS_ENABLED", "TRUE", "Following Pokémon enabled"),
    ("caps.h", "B_EXP_CAP_TYPE", "EXP_CAP_HARD", "Hard EXP cap"),
    ("caps.h", "B_LEVEL_CAP_TYPE", "LEVEL_CAP_FLAG_LIST", "Badge/flag level-cap progression"),
    ("caps.h", "B_RARE_CANDY_CAP", "TRUE", "Rare Candy respects cap"),
    ("battle.h", "B_FLAG_DYNAMAX_BATTLE", "0", "Dynamax trainer-battle flag disabled"),
    ("battle.h", "B_FLAG_TERA_ORB_CHARGED", "0", "No Tera Orb charge flag"),
    ("battle.h", "B_TERA_ORB_ALWAYS_CHARGED", "FALSE", "No always-charged Tera Orb"),
    ("general.h", "GEN_LATEST", "GEN_9", "Current base generation"),
]
WARN_IF_ENABLED = [
    ("species_enabled.h", "P_GIGANTAMAX_FORMS", "Gigantamax form data may remain compiled; verify battle activation stays impossible"),
    ("species_enabled.h", "P_TERA_FORMS", "Terastal form data may remain compiled; verify no Tera battle access"),
]
RUNTIME = [
    "Actual Gen I–IX species, moves, abilities, graphics and form correctness",
    "Fairy typing and physical/special damage execution",
    "Set-style no-free-switch prompt in real wild, trainer and boss battles",
    "Held-item-only EXP behavior for parties of 1–6 and at cap",
    "Level-cap bypasses, experience overflow and Rare Candy edge cases",
    "Mega Evolution battle activation and battle-only asset load",
    "Excluded gimmicks inaccessible through menus, items, AI and scripts",
    "Follower collision, transitions, bikes, Surf, cutscenes and missing sprites",
    "Native save/menu/reset, full Gym badge and quest persistence",
    "All supported species attainable without trades or outside events",
    "Field abilities usable without mandatory battle move slots",
    "Region travel, Sinnoh transition and separate badges",
    "Scripted losses, gauntlets, reward retries, one-time legendary captures",
    "All planned maps and event flags are reachable and collision safe",
    "Real mGBA walkthrough and separate Delta iOS acceptance",
]


def remove_block_comments(source):
    return re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group().count("\n"), source, flags=re.S)


def parse_config(source):
    """Return live object-like #defines, duplicate names and suspicious comments."""
    definitions = {}
    duplicates = []
    suspicious = []
    for lineno, line in enumerate(remove_block_comments(source).splitlines(), 1):
        live, sep, comment = line.partition("//")
        found = re.match(r"^\s*#\s*define\s+([A-Z][A-Z0-9_]*)\s+(.+?)\s*$", live)
        if found:
            name, value = found.groups()
            # Function-like macros have '(' immediately after the macro name.
            if value.lstrip().startswith("(") and re.search(r"^\s*#\s*define\s+" + re.escape(name) + r"\(", live):
                continue
            definitions.setdefault(name, []).append({"value": value.strip(), "line": lineno})
            if len(definitions[name]) > 1:
                duplicates.append({"macro": name, "line": lineno,
                                   "previous_line": definitions[name][0]["line"]})
        if sep and "#define" in comment:
            suspicious.append({"line": lineno, "comment": comment.strip()[:180]})
    return definitions, duplicates, suspicious


def inspect(engine):
    root = Path(engine) / "include" / "config"
    files = {}
    issues = []
    for filename, _, _, _ in EXPECTED:
        if filename not in files:
            path = root / filename
            if not path.is_file():
                issues.append({"severity": "blocker", "file": filename,
                               "detail": "Required configuration file is missing"})
                files[filename] = None
            else:
                files[filename] = parse_config(path.read_text(encoding="utf-8"))
    checks = []
    for filename, name, expected, rationale in EXPECTED:
        record = files.get(filename)
        matching = [] if record is None else record[0].get(name, [])
        actual = matching[-1]["value"] if matching else None
        good = len(matching) == 1 and actual == expected
        checks.append({"file": filename, "macro": name, "expected": expected,
                       "actual": actual, "passed": good, "reason": rationale,
                       "line": matching[-1]["line"] if matching else None})
        if not good:
            issues.append({"severity": "blocker", "file": filename, "macro": name,
                           "detail": f"Expected one definition '{expected}'; found {len(matching)} with latest '{actual}'"})
    for filename, record in files.items():
        if record is None:
            continue
        for duplicate in record[1]:
            issues.append({"severity": "warning", "file": filename,
                           "detail": "Duplicate object-like macro definition", **duplicate})
        for suspicious in record[2]:
            # Commented code can be intentional; report for human review, not failure.
            issues.append({"severity": "warning", "file": filename,
                           "detail": "Comment contains #define; inspect for accidental run-on", **suspicious})
    for filename, macro, reason in WARN_IF_ENABLED:
        record = files.get(filename)
        if record:
            definitions = record[0].get(macro, [])
            if definitions and definitions[-1]["value"] == "TRUE":
                issues.append({"severity": "warning", "file": filename,
                               "macro": macro, "detail": reason})
    blockers = sum(issue["severity"] == "blocker" for issue in issues)
    return {
        "scope": "Static configuration only; engine compilation and runtime not inferred",
        "source": str(root),
        "checks": checks,
        "issues": issues,
        "summary": {"passed": sum(x["passed"] for x in checks),
                    "total": len(checks), "blockers": blockers,
                    "warnings": sum(x["severity"] == "warning" for x in issues)},
        "runtime_acceptance_not_proven_by_this_audit": RUNTIME,
    }


def render_markdown(report):
    summary = report["summary"]
    lines = ["# Averon engine readiness — static source check", "",
             f"Configuration rules passing: **{summary['passed']}/{summary['total']}**; "
             f"blockers: **{summary['blockers']}**; warnings: **{summary['warnings']}**.", "",
             "This is **not** a compilation, emulator or National Pokédex verification.", "",
             "| Setting | Actual | Required | Result |", "|---|---|---|---|"]
    for check in report["checks"]:
        lines.append(f"| {check['file']} / \`{check['macro']}\` | "
                     f"\`{check['actual']}\` | \`{check['expected']}\` | "
                     f"{'PASS' if check['passed'] else 'BLOCKED'} |")
    lines += ["", "## Issues", ""]
    for issue in report["issues"]:
        lines.append(f"- **{issue['severity'].upper()}** {issue['file']}: {issue['detail']}"
                     + (f" ({issue.get('macro')})" if issue.get("macro") else ""))
    if not report["issues"]:
        lines.append("No issues detected by these checks.")
    lines += ["", "## Still requires actual code/build/runtime evidence", ""]
    lines += ["- " + requirement for requirement in report["runtime_acceptance_not_proven_by_this_audit"]]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", type=Path, required=True)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--markdown", type=Path)
    args = ap.parse_args()
    report = inspect(args.engine)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(f"Config source checks: {report['summary']['passed']}/{report['summary']['total']} passing; "
          f"{report['summary']['blockers']} blockers; "
          f"{report['summary']['warnings']} warnings")
    for issue in report["issues"]:
        print(f"  [{issue['severity']}] {issue['file']}: {issue['detail']}")
    return 1 if report["summary"]["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
