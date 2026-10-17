#!/usr/bin/env bash
# Disposable, read-only to GitHub: no pushes, releases, ROM or save uploads.
set -Eeuo pipefail
action="$1"
folder="$RUNNER_TEMP/averon-integration"
mkdir -p "$folder"
engine="Pokemon Game/engine"

case "$action" in
  prepare)
    first="$FIRST_PR"; second="$SECOND_PR"
    [[ "$first" =~ ^(0|[1-9][0-9]*)$ ]] || { echo "Bad first PR"; exit 1; }
    [[ "$second" =~ ^(0|[1-9][0-9]*)$ ]] || { echo "Bad second PR"; exit 1; }
    if [[ "$first" == 0 && "$second" == 0 ]]; then
      mode=main
    elif [[ "$first" != 0 && "$second" != 0 && "$first" != "$second" ]]; then
      mode=combined
    else
      echo "Select two distinct PRs or 0/0 for main-only"; exit 1
    fi
    base=$(git rev-parse HEAD)
    [[ "$base" =~ ^[0-9a-f]{40}$ ]] || exit 1
    : > "$folder/pr-heads.tsv"
    if [[ "$mode" == combined ]]; then
      for number in "$first" "$second"; do
        gh api "repos/$GITHUB_REPOSITORY/pulls/$number" > "$folder/pr-$number.json"
        jq -e --arg repo "$GITHUB_REPOSITORY" \
          '.state=="open" and .head.repo.full_name==$repo and .base.repo.full_name==$repo' \
          "$folder/pr-$number.json" > /dev/null || {
            echo "Only open PRs from this repository are allowed"; exit 1;
          }
        expected=$(jq -r '.head.sha' "$folder/pr-$number.json")
        [[ "$expected" =~ ^[0-9a-f]{40}$ ]] || exit 1
        git fetch --no-tags origin \
          "+refs/pull/$number/head:refs/remotes/origin/combined-$number"
        actual=$(git rev-parse "refs/remotes/origin/combined-$number")
        [[ "$actual" == "$expected" ]] || {
          echo "PR head changed during fetch; abort stale integration"; exit 1;
        }
        printf '%s\t%s\n' "$number" "$actual" >> "$folder/pr-heads.tsv"
        git -c user.name="Averon Disposable Builder" \
          -c user.email="builder@users.noreply.github.com" \
          -c core.hooksPath=/dev/null merge --no-ff --no-edit \
          "refs/remotes/origin/combined-$number"
        git diff --check "$base"...HEAD
      done
    fi
    MAIN_SHA="$base" MODE="$mode" python3 - <<'PY'
import json, os, subprocess
from pathlib import Path
folder = Path(os.environ["RUNNER_TEMP"]) / "averon-integration"
prs = []
for line in (folder / "pr-heads.tsv").read_text().splitlines():
    number, sha = line.split("\t")
    prs.append({"number": int(number), "sha": sha})
source = {
    "mode": os.environ["MODE"], "main_sha": os.environ["MAIN_SHA"],
    "pull_requests": prs,
    "combined_local_sha": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip()
}
(folder / "source-pins.json").write_text(json.dumps(source, indent=2) + "\n")
print("PINNED COMBINED BUILD:", json.dumps(source))
PY
    python3 "Pokemon Game/scripts/coordination/check_integration_contract.py" \
      --engine "$engine"
    echo "No remote branch altered; local text merge != gameplay acceptance."
    ;;
  test)
    cd "$engine"
    make -j4 -O all > "$folder/build.log" 2>&1 || {
      tail -160 "$folder/build.log"; exit 1;
    }
    test -s pokeemerald.gba
    python3 "../scripts/check-averon-resource-budget.py" \
      --log "$folder/build.log" --rom pokeemerald.gba \
      --json "$folder/resource.json"
    sha256sum pokeemerald.gba
    tail -18 "$folder/build.log"
    test -x tools/mgba/mgba-rom-test || {
      echo "No executable bundled native test runner"; exit 1;
    }
    make -j4 -O check TESTS=Averon > "$folder/native.log" 2>&1 || {
      tail -120 "$folder/native.log"; exit 1;
    }
    tail -23 "$folder/native.log"
    make -j4 -O check TESTS=test/save.c > "$folder/save.log" 2>&1 || {
      tail -120 "$folder/save.log"; exit 1;
    }
    tail -23 "$folder/save.log"
    ;;
  smoke)
    export DISPLAY=:99
    Xvfb :99 -screen 0 1024x768x24 -nolisten tcp \
      > "$folder/xvfb.log" 2>&1 &
    display_pid=$!
    sleep 2
    openbox > "$folder/window-manager.log" 2>&1 &
    manager_pid=$!
    mgba -2 "$engine/pokeemerald.gba" > "$folder/mgba.log" 2>&1 &
    emulator_pid=$!
    cleanup() { kill "$emulator_pid" "$manager_pid" "$display_pid" 2>/dev/null || true; }
    trap cleanup EXIT
    window=""
    for i in $(seq 1 25); do
      window=$(xdotool search --onlyvisible --name "mGBA" 2>/dev/null | head -1 || true)
      [[ -n "$window" ]] && break
      kill -0 "$emulator_pid" 2>/dev/null || { cat "$folder/mgba.log"; exit 1; }
      sleep 1
    done
    [[ -n "$window" ]] || { echo "mGBA graphical window not found"; exit 1; }
    xdotool windowactivate "$window" || true
    sleep 9
    import -window "$window" "$folder/boot.png"
    xdotool key --clearmodifiers Return
    sleep 4
    import -window "$window" "$folder/after-start.png"
    for file in "$folder/boot.png" "$folder/after-start.png"; do
      identify "$file"
      colors=$(identify -format '%k' "$file")
      [[ "$colors" -ge 16 ]] || { echo "Blank/low-information frame"; exit 1; }
    done
    kill -0 "$emulator_pid"
    echo "BOOT_SMOKE: graphical mGBA alive; two nonblank frames, NOT Q1-Q5 verification."
    ;;
  report)
    cd "$engine"
    python3 "../scripts/coordination/verify_build_readiness.py" \
      --rom pokeemerald.gba \
      --native-log "$folder/native.log" --save-log "$folder/save.log" \
      --resource-json "$folder/resource.json" \
      --source-json "$folder/source-pins.json" \
      --out "$folder/readiness.json"
    python3 - "$folder/readiness.json" >> "$GITHUB_STEP_SUMMARY" <<'PY'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
print("## Averon disposable GBA integration readiness")
print("Main SHA:", r["source"]["main_sha"])
print("Pinned PR heads:", r["source"]["pull_requests"])
print("Ephemeral ROM SHA256:", r["rom"]["sha256"])
print("Averon native:", str(r["native"]["passed"]) + "/" + str(r["native"]["total"]))
print("Native save:", str(r["save"]["passed"]) + "/" + str(r["save"]["total"]))
print("Limited graphical boot screenshot included only when enabled.")
print("**No ROM or save distributed; no feature/QA/Delta acceptance or merge.**")
PY
    ;;
  *)
    echo "Usage: $0 prepare|test|smoke|report"; exit 2
    ;;
esac
