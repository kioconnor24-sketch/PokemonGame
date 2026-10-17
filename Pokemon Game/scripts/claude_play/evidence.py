#!/usr/bin/env python3
"""Package one or more playthrough run directories for independent review.

  python3 evidence.py --case Q1=run12:gym1-result,q1-hiker,q1-reward \
      --root /private/evidence --out qa-evidence-input.json

Builds the input the manager's coordination/qa_evidence_report.py checks
(source/ROM SHA, input trace, screenshots, state observations) from files the
driver wrote during real runs: provenance-start.json, inputs.jsonl and
state-<label>.json (each with its screenshot and expectations). Nothing is
invented: a missing file, an unexpected SHA difference between runs, or a
state file whose recorded problems are not empty makes this exit non-zero.
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


def build(cases, root):
    """cases: {case_id: [(run_dir, [labels])]} with run dirs under root."""
    root = pathlib.Path(root)
    source = rom = None
    out_cases = []
    for case_id, parts in cases.items():
        screenshots, observations, traces = [], [], []
        for run_name, labels in parts:
            run = root / run_name
            prov_path = run / "provenance-start.json"
            if not prov_path.exists():
                raise EvidenceError(f"{run}: no provenance-start.json")
            prov = json.loads(prov_path.read_text())
            if prov.get("engine_dirty"):
                raise EvidenceError(f"{run}: engine tree was dirty")
            if source is None:
                source, rom = prov["source_sha"], prov["rom_sha256"]
            elif (source, rom) != (prov["source_sha"], prov["rom_sha256"]):
                raise EvidenceError(f"{run}: source/ROM differ from the first run")
            if not (run / "inputs.jsonl").is_file():
                raise EvidenceError(f"{run}: no inputs.jsonl")
            traces.append(f"{run_name}/inputs.jsonl")
            for label in labels:
                state = load_state(run, label)
                screenshots.append(f"{run_name}/{state['screenshot']}")
                for key, want in state.get("expected", {}).items():
                    if want == "check":
                        statement = f"{label}: {key} held after ordinary inputs"
                        observations.append(dict(statement=statement,
                                                 evidence_file=f"{run_name}/state-{label}.json"))
                    else:
                        observations.append(dict(
                            statement=f"{label}: {key}",
                            evidence_file=f"{run_name}/state-{label}.json",
                            expected=want, observed=observed_value(state, key)))
        out_cases.append(dict(case_id=case_id, input_trace=traces[0] if len(traces) == 1 else traces[-1],
                              input_traces=traces, screenshots=screenshots,
                              state_observations=observations))
    return dict(source_sha=source, rom_sha256=rom, cases=out_cases)


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
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cases = dict(parse_case(c) for c in a.case)
    try:
        manifest = build(cases, a.root)
    except EvidenceError as exc:
        print("EVIDENCE_INCOMPLETE", exc, file=sys.stderr)
        return 1
    pathlib.Path(a.out).write_text(json.dumps(manifest, indent=1))
    print("EVIDENCE_PACKAGED", len(manifest["cases"]), "case(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
