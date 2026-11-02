#!/usr/bin/env python3
"""Reuse only a successful, identical-input full native run; otherwise run it.

The workflow calls the selector from trusted main before executing PR code.
Proofs are data, never downloaded code. Current builds/budgets still execute.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

WORKFLOW = ".github/workflows/averon-native-build.yml"
HELPER = "Pokemon Game/scripts/native-test-evidence.py"
ARTIFACT = "averon-native-build-log"
PROOF = "averon-native-evidence.json"
SHA = re.compile(r"[0-9a-f]{40}\Z")


def git(*args):
    return subprocess.check_output(["git", *args], text=True,
                                   stderr=subprocess.DEVNULL, timeout=15).strip()


def object_id(ref, path, optional=False):
    try:
        return git("rev-parse", "--verify", f"{ref}:{path}")
    except subprocess.CalledProcessError:
        if optional:
            return None
        raise


def ensure_commit(ref):
    if not SHA.fullmatch(ref):
        raise ValueError("invalid source revision")
    try:
        git("cat-file", "-e", ref + "^{commit}")
    except subprocess.CalledProcessError:
        git("fetch", "--no-tags", "--depth=1", "origin", ref)


def toolchain():
    commands = {
        "arm_gcc": ["arm-none-eabi-gcc", "-dumpfullversion"],
        "host_gcc": ["cc", "-dumpfullversion"],
        "arm_ld": ["arm-none-eabi-ld", "--version"],
        "packages": ["dpkg-query", "-W", "gcc-arm-none-eabi",
                     "binutils-arm-none-eabi", "libnewlib-arm-none-eabi", "libpng-dev",
                     "libc6", "libstdc++6", "zlib1g", "make", "python3"],
    }
    result = {name: subprocess.check_output(command, text=True).strip()
              for name, command in commands.items()}
    result["image"] = os.environ.get("ImageVersion", "unknown")
    result["machine"] = subprocess.check_output(["uname", "-m"], text=True).strip()
    flags = {k: os.environ.get(k, "") for k in (
        "CC", "CXX", "CPP", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS",
        "MAKEFLAGS", "MODERN", "TESTS", "CRIES", "RELEASE", "CI",
        "GITHUB_ACTIONS", "GITHUB_REPOSITORY_OWNER")}
    result["build_environment_sha256"] = hashlib.sha256(
        json.dumps(flags, sort_keys=True).encode()).hexdigest()
    return result


def inputs(ref, compiler):
    return {
        "engine": object_id(ref, "Pokemon Game/engine"),
        # Conservative: include every validation/tooling script, not only the
        # currently selected native helper imports.
        "scripts": object_id(ref, "Pokemon Game/scripts"),
        "workflow": object_id(ref, WORKFLOW),
        "attributes": object_id(ref, ".gitattributes", optional=True),
        "submodules": object_id(ref, ".gitmodules", optional=True),
        "toolchain": compiler,
    }


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def unchanged_worktree(ref):
    paths = ["Pokemon Game/engine", "Pokemon Game/scripts", WORKFLOW,
             ".gitattributes", ".gitmodules"]
    changed = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--no-textconv", "--quiet", ref, "--", *paths],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15).returncode
    extra = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z", "--", *paths], timeout=15)
    return changed == 0 and not extra


def eligible_run(run, *, repo, branch, source_head, current_run, success_only=True):
    conclusions = {"success"} if success_only else {"success", "failure", "timed_out", "action_required", "startup_failure"}
    if (run.get("id") == current_run or run.get("conclusion") not in conclusions
            or run.get("path") != WORKFLOW
            or (run.get("head_repository") or {}).get("full_name") != repo
            or not SHA.fullmatch(run.get("head_sha", ""))):
        return False
    if run.get("event") == "push":
        return run.get("head_branch") == "main"
    if run.get("event") not in ("pull_request", "workflow_dispatch"):
        return False
    if run.get("event") == "workflow_dispatch" and run.get("head_branch") == "main":
        return True
    # On protected main, a merged PR head may supply the proof. For PRs use
    # only the current in-repository branch's own previous revisions.
    if branch != "main" and run.get("head_branch") != branch:
        return False
    return True


def valid_proof(proof, run, current, source_inputs, trusted_blobs):
    """Validate a downloaded receipt against immutable Git/API metadata."""
    if not isinstance(proof, dict):
        return False
    counts = proof.get("native", {})
    if not isinstance(counts, dict):
        return False
    return (
        type(proof.get("schema")) is int and proof["schema"] == 1
        and type(proof.get("run_id")) is int and proof["run_id"] == run["id"]
        and type(proof.get("run_attempt")) is int
        and proof["run_attempt"] == run.get("run_attempt", 1)
        and proof.get("source_head") == run["head_sha"]
        and proof.get("executed") is True
        and proof.get("reusable") is True
        and bool(SHA.fullmatch(proof.get("checkout", "")))
        and bool(re.fullmatch(r"[0-9a-f]{64}", proof.get("native_log_sha256", "")))
        and proof.get("inputs") == current == source_inputs
        and proof.get("source_inputs") == source_inputs
        and type(counts.get("passed")) is int and counts["passed"] > 0
        and type(counts.get("total")) is int
        and counts.get("total") == counts["passed"]
        and type(counts.get("failed")) is int and counts["failed"] == 0
        and type(counts.get("skipped")) is int and counts["skipped"] == 0
        and set(trusted_blobs) == {WORKFLOW, HELPER} and all(trusted_blobs.values())
    )


class StripCrossOriginAuth(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != "https":
            raise ValueError("evidence redirect requires HTTPS")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and urllib.parse.urlsplit(req.full_url).netloc != urllib.parse.urlsplit(newurl).netloc:
            redirected.remove_header("Authorization")
        return redirected


class GitHub:
    def __init__(self, repo):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("invalid repository")
        self.base = "https://api.github.com/repos/" + repo
        self.opener = urllib.request.build_opener(StripCrossOriginAuth())

    def get(self, path, *, binary=False):
        req = urllib.request.Request(self.base + path, headers={
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with self.opener.open(req, timeout=8) as response:
            data = response.read(8 * 1024 * 1024 + 1)
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("evidence response too large")
        return data if binary else json.loads(data)

    def proof(self, run_id, attempt=1):
        artifacts = self.get(f"/actions/runs/{run_id}/artifacts")["artifacts"]
        names = {ARTIFACT, f"{ARTIFACT}-attempt-{attempt}"}
        artifact = next((a for a in artifacts if a["name"] in names and not a["expired"]), None)
        if not artifact:
            return None
        data = self.get(f"/actions/artifacts/{artifact['id']}/zip", binary=True)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            matches = [i for i in archive.infolist() if i.filename == PROOF]
            logs = [i for i in archive.infolist() if i.filename == "averon-native-tests.log"]
            if (len(matches) != 1 or matches[0].file_size > 65536
                    or len(logs) != 1 or logs[0].file_size > 16 * 1024 * 1024):
                return None
            proof = json.loads(archive.read(matches[0]))
            log = archive.read(logs[0])
            if (hashlib.sha256(log).hexdigest() != proof.get("native_log_sha256")
                    or native_counts(log.decode()) != proof.get("native")):
                return None
            return proof


def select(args, compiler):
    if args.run_attempt > 1:
        return None, "rerun attempts require fresh native execution"
    current = inputs(args.checkout, compiler)
    ensure_commit(args.source_head)
    source = inputs(args.source_head, compiler)
    trusted = {p: object_id(args.trusted_main, p, optional=True) for p in (WORKFLOW, HELPER)}
    if not all(trusted.values()) or any(object_id(args.checkout, p) != oid for p, oid in trusted.items()):
        return None, "workflow or selector is not the deployed trusted version"
    if current != source:
        return None, "combined-base inputs differ from the PR head"
    api = GitHub(args.repo)
    runs = api.get("/actions/workflows/averon-native-build.yml/runs?per_page=20")["workflow_runs"]
    runs = sorted(runs, key=lambda r: r.get("updated_at", r.get("created_at", "")), reverse=True)
    deadline = time.monotonic() + 30
    for run in runs:
        if time.monotonic() > deadline:
            break
        if not eligible_run(run, repo=args.repo, branch=args.branch,
                            source_head=args.source_head, current_run=args.run_id,
                            success_only=False):
            continue
        try:
            ensure_commit(run["head_sha"])
            if any(object_id(run["head_sha"], p, optional=True) != oid for p, oid in trusted.items()):
                continue
            previous = inputs(run["head_sha"], compiler)
            if previous != current:
                continue
            if run["event"] != "push" and run.get("head_branch") != "main":
                # Checkout is shallow. Use immutable GitHub commit metadata,
                # not a shallow merge-base result or a mutable branch ref.
                comparison = api.get(f"/compare/{run['head_sha']}...{args.source_head}")
                if comparison.get("status") not in ("ahead", "identical"):
                    continue
            if run["conclusion"] != "success":
                return None, "a newer matching-input run failed; fresh native execution required"
            proof = api.proof(run["id"], run.get("run_attempt", 1))
            if proof and valid_proof(proof, run, current, previous, trusted):
                # Independently verify the receipt's checked-out source too.
                ensure_commit(proof["checkout"])
                if inputs(proof["checkout"], compiler) == current:
                    return run["id"], "identical inputs and successful full native execution"
        except Exception:
            # An unavailable lookup may hide a newer matching failure. It
            # cannot justify accepting an older success whose freshness is
            # now unproven; cache uncertainty means real native execution.
            return None, "evidence lookup incomplete; fresh native execution required"
    return None, "no matching successful full native proof"


def native_counts(text):
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    passed = re.findall(r"- Tests PASSED:\s+(\d+)", text)
    total = re.findall(r"- Tests TOTAL:\s+(\d+)", text)
    if not passed or not total or int(passed[-1]) == 0 or passed[-1] != total[-1]:
        raise ValueError("native log does not prove a nonzero wholly passing suite")
    if any(int(n) for n in re.findall(r"- Tests (?:FAILED|SKIPPED):\s+(\d+)", text)):
        raise ValueError("native log contains failures or skips")
    return {"passed": int(passed[-1]), "total": int(total[-1]), "failed": 0, "skipped": 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("select", "confirm", "record"))
    p.add_argument("--checkout", required=True)
    p.add_argument("--source-head", required=True)
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--run-attempt", type=int, default=1)
    p.add_argument("--repo", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--trusted-main", default="origin/main")
    p.add_argument("--native-log", type=Path)
    p.add_argument("--fingerprint", default="")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    outputs = {}
    try:
        compiler = toolchain()
        if args.mode == "select":
            run, reason = select(args, compiler)
            result = {"reused": bool(run), "source_run": run, "reason": reason}
            outputs = {"reused": "true" if run else "false", "source_run": str(run or ""),
                       "fingerprint": digest(inputs(args.checkout, compiler)) if run else ""}
        elif args.mode == "confirm":
            # Candidate compilation/validation has now run. It must not have
            # changed tracked inputs, introduced source files or changed flags.
            good = args.run_attempt == 1 and bool(re.fullmatch(r"[0-9a-f]{64}", args.fingerprint))
            good = good and unchanged_worktree(args.checkout)
            good = good and digest(inputs(args.checkout, compiler)) == args.fingerprint
            result = {"reused": good, "reason": "post-build input confirmation"}
            outputs = {"reused": "true" if good else "false"}
        else:
            ensure_commit(args.checkout)
            ensure_commit(args.source_head)
            current, source = inputs(args.checkout, compiler), inputs(args.source_head, compiler)
            log = args.native_log.read_bytes()
            result = {"schema": 1, "executed": True, "reusable": current == source,
                      "run_id": args.run_id, "checkout": args.checkout,
                      "run_attempt": args.run_attempt,
                      "source_head": args.source_head, "inputs": current,
                      "source_inputs": source, "native": native_counts(log.decode()),
                      "native_log_sha256": hashlib.sha256(log).hexdigest()}
    except Exception:
        # An unavailable cache must never hold up or replace native execution.
        result = {"reused": False, "reason": "evidence unavailable; full native run required"}
        if args.mode in ("select", "confirm"):
            outputs = {"reused": "false"}
        else:
            raise
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    for key, value in outputs.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
