#!/usr/bin/env python3
"""Package one or more playthrough run directories for independent review.

  python3 evidence.py --case Q1=run12:gym1-result,q1-hiker,q1-reward \
      --root /private/evidence --out qa-evidence-input.json

Builds the input the manager's coordination/qa_evidence_report.py checks
(source/ROM SHA, input trace, screenshots, state observations) from files the
driver wrote during real runs: provenance-start.json, inputs.jsonl,
events.jsonl and state-<label>.json (each with its screenshot and
expectations). Nothing is invented: a missing file, a source/ROM/ELF
difference between runs, a played ROM that is not the engine's build, or a
state file whose recorded problems are not empty makes this exit non-zero.
Every case that used the debug menu is marked scope DEV_FIXTURE and each of
its statements names the fixture; each run's driver commit and dirty state is
listed.
"""
import argparse
import json
import pathlib
import sys


class EvidenceError(RuntimeError):
    pass


def load_state(run, label):
    path = run / f"state-{label}.json"
    if not path.exists():
        raise EvidenceError(f"{path}: missing state file")
    state = json.loads(path.read_text())
    if state.get("problems"):
        raise EvidenceError(f"{path}: recorded problems {state['problems']}")
    if not (run / state.get("screenshot", "")).is_file():
        raise EvidenceError(f"{path}: screenshot {state.get('screenshot')!r} missing")
    return state


def observed_value(state, key):
    if key.startswith("FLAG_"):
        return state["flags"].get(key)
    return state.get(key)


def dev_fixtures(run):
    """Debug-menu uses recorded in the run's events.jsonl (dev_only=true)."""
    path = run / "events.jsonl"
    if not path.is_file():
        raise EvidenceError(f"{run}: no events.jsonl")
    uses = []
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if event.get("dev_only"):
            uses.append(event.get("label") or event.get("event"))
    return uses


def build(cases, root):
    """cases: {case_id: [(run_dir, [labels])]} with run dirs under root."""
    root = pathlib.Path(root)
    source = rom = elf = None
    out_cases = []
    for case_id, parts in cases.items():
        screenshots, observations, traces, fixtures, drivers = [], [], [], [], []
        for run_name, labels in parts:
            run = root / run_name
            prov_path = run / "provenance-start.json"
            if not prov_path.exists():
                raise EvidenceError(f"{run}: no provenance-start.json")
            prov = json.loads(prov_path.read_text())
            if prov.get("engine_dirty"):
                raise EvidenceError(f"{run}: engine tree was dirty")
            if prov.get("engine_rom_sha256") not in (None, prov["rom_sha256"]):
                raise EvidenceError(f"{run}: played ROM is not the engine's build")
            if source is None:
                source, rom, elf = prov["source_sha"], prov["rom_sha256"], prov["elf_sha256"]
            elif (source, rom, elf) != (prov["source_sha"], prov["rom_sha256"], prov["elf_sha256"]):
                raise EvidenceError(f"{run}: source/ROM/ELF differ from the first run")
            if not (run / "inputs.jsonl").is_file():
                raise EvidenceError(f"{run}: no inputs.jsonl")
            traces.append(f"{run_name}/inputs.jsonl")
            drivers.append(dict(run=run_name, driver_sha=prov.get("driver_sha"),
                                driver_dirty=prov.get("driver_dirty")))
            used = dev_fixtures(run)
            fixtures += [f"{run_name}: {u}" for u in used]
            how = (f"after ordinary inputs and DEV-ONLY debug fixture(s) {used} in this run"
                   if used else "after ordinary inputs")
            for label in labels:
                state = load_state(run, label)
                screenshots.append(f"{run_name}/{state['screenshot']}")
                for key, want in state.get("expected", {}).items():
                    if want == "check":
                        observations.append(dict(statement=f"{label}: {key} held {how}",
                                                 evidence_file=f"{run_name}/state-{label}.json"))
                    else:
                        observations.append(dict(
                            statement=f"{label}: {key} ({how})",
                            evidence_file=f"{run_name}/state-{label}.json",
                            expected=want, observed=observed_value(state, key)))
        out_cases.append(dict(case_id=case_id, input_trace=traces[0] if len(traces) == 1 else traces[-1],
                              input_traces=traces, screenshots=screenshots,
                              state_observations=observations,
                              dev_fixtures=fixtures, scope="DEV_FIXTURE" if fixtures else "ORDINARY_PLAY",
                              drivers=drivers))
    return dict(source_sha=source, rom_sha256=rom, elf_sha256=elf, cases=out_cases)


def mark_external_fixture(case, desc):
    """A fixture the run's own events cannot show (applied before the run)."""
    case["dev_fixtures"].append(f"external: {desc}")
    case["scope"] = "DEV_FIXTURE"
    for o in case["state_observations"]:
        o["statement"] += f" [fixture: {desc}]"


def parse_case(text):
    case_id, rest = text.split("=", 1)
    parts = []
    for chunk in rest.split(";"):
        run, labels = chunk.split(":", 1)
        parts.append((run, [l for l in labels.split(",") if l]))
    return case_id, parts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", action="append", required=True,
                    help="ID=run:label,label[;run2:label,...]")
    ap.add_argument("--fixture", action="append", default=[],
                    help="ID=description of a fixture applied outside the game "
                         "(e.g. a deliberately damaged save copy); marks the case")
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cases = dict(parse_case(c) for c in a.case)
    try:
        manifest = build(cases, a.root)
        for spec in a.fixture:
            case_id, desc = spec.split("=", 1)
            case = next((c for c in manifest["cases"] if c["case_id"] == case_id), None)
            if case is None:
                raise EvidenceError(f"--fixture names unknown case {case_id}")
            mark_external_fixture(case, desc)
    except EvidenceError as exc:
        print("EVIDENCE_INCOMPLETE", exc, file=sys.stderr)
        return 1
    pathlib.Path(a.out).write_text(json.dumps(manifest, indent=1))
    print("EVIDENCE_PACKAGED", len(manifest["cases"]), "case(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
