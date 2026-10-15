#!/usr/bin/env python3
"""Detect numeric collision risks in Averon story flags and event variables.

Evaluates only simple integer aliases/arithmetic in preprocessor defines. Unknown
expressions are explicitly unverified; never assume an ID is available.
"""
import argparse
import ast
import json
import re
from pathlib import Path

DEFINE = re.compile(r"^\s*#\s*define\s+((?:FLAG|VAR)_[A-Z0-9_]+)\s+(.+?)\s*$")


def definitions(source):
    result = {}
    for line_number, line in enumerate(source.splitlines(), 1):
        line = line.split("//", 1)[0].strip()
        match = DEFINE.match(line)
        if not match:
            continue
        key, expression = match.groups()
        result.setdefault(key, []).append((expression.strip(), line_number))
    return result


def evaluate(expr, known, trail=()):
    """Restricted parser: only literals, references, parentheses, + and -."""
    node = ast.parse(expr, mode="eval").body

    def walk(n):
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return n.value
        if isinstance(n, ast.Name):
            if n.id in trail or n.id not in known or len(known[n.id]) != 1:
                raise ValueError("Unknown, ambiguous or cyclic alias: " + n.id)
            return evaluate(known[n.id][0][0], known, trail + (n.id,))
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)):
            a, b = walk(n.left), walk(n.right)
            return a + b if isinstance(n.op, ast.Add) else a - b
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            value = walk(n.operand)
            return value if isinstance(n.op, ast.UAdd) else -value
        raise ValueError("Unsupported expression: " + expr)
    return walk(node)


def scan(source, namespace, occupied_prefix):
    found = definitions(source)
    all_resolved = {}
    unresolved = []
    for key, defs in found.items():
        if len(defs) != 1:
            unresolved.append({"name": key, "reason": "Multiple live definitions",
                               "lines": [line for _, line in defs]})
            continue
        expr, line = defs[0]
        try:
            # Macro aliases may refer to simple integer helper macros not
            # beginning with FLAG_/VAR_. We only resolve known identifiers,
            # and report other expressions as unverified.
            value = evaluate(expr, found, (key,))
            all_resolved[key] = value
        except (ValueError, SyntaxError, RecursionError) as error:
            unresolved.append({"name": key, "line": line,
                               "reason": str(error)})
    chosen = {key: number for key, number in all_resolved.items()
              if key.startswith(occupied_prefix)}
    by_number = {}
    for name, number in all_resolved.items():
        by_number.setdefault(number, []).append(name)
    issues = []
    for key, value in chosen.items():
        candidates = sorted(name for name in by_number[value]
                            if name.startswith(namespace) and name != key)
        if candidates:
            issues.append({"severity": "blocker", "name": key,
                           "value": hex(value), "detail": "Same-value Averon alias: " + ", ".join(candidates)})
        others = sorted(name for name in by_number[value]
                        if not name.startswith(namespace) and name != key)
        if others:
            issues.append({"severity": "warning", "name": key,
                           "value": hex(value), "detail": "Shared ID with non-Averon definitions (may be intentional): " + ", ".join(others)})
    unresolved_averon = [x for x in unresolved if x["name"].startswith(occupied_prefix)]
    for x in unresolved_averon:
        issues.append({"severity": "blocker", "name": x["name"],
                       "detail": "Could not establish unique ID: " + x["reason"]})
    return {"namespace": namespace, "registered": chosen,
            "resolved_count": len(all_resolved),
            "unresolved_averon": unresolved_averon,
            "issues": issues}


def audit(engine):
    base = Path(engine) / "include" / "constants"
    outputs = {}
    for name, prefix in (("flags", "FLAG_"), ("vars", "VAR_")):
        path = base / (name + ".h")
        if not path.is_file():
            raise FileNotFoundError("Missing native " + name + " header: " + str(path))
        outputs[name] = scan(path.read_text(encoding="utf-8"),
                             prefix, prefix + "AVERON_")
    blockers = sum(x["severity"] == "blocker"
                   for section in outputs.values() for x in section["issues"])
    warnings = sum(x["severity"] == "warning"
                   for section in outputs.values() for x in section["issues"])
    return {"scope": "Static native flag/var namespace only; scripts and runtime remain unverified",
            "flags": outputs["flags"], "vars": outputs["vars"],
            "summary": {"blockers": blockers, "warnings": warnings}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engine", type=Path, required=True)
    p.add_argument("--json", type=Path)
    args = p.parse_args()
    report = audit(args.engine)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Persistent namespace: "
          f"{len(report['flags']['registered'])} Averon flags, "
          f"{len(report['vars']['registered'])} Averon vars; "
          f"{report['summary']['blockers']} blockers, "
          f"{report['summary']['warnings']} warnings")
    for section in (report["flags"], report["vars"]):
        for issue in section["issues"]:
            print(f"[{issue['severity']}] {issue['name']}: {issue['detail']}")
    return 1 if report["summary"]["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
