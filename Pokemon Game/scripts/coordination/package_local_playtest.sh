#!/usr/bin/env bash
# Local OWNER-ONLY .gba package. Never upload/commit this output to GitHub.
set -Eeuo pipefail
project=$(cd "$(dirname "$0")/../.." && pwd)
root=$(git -C "$project" rev-parse --show-toplevel)
engine="$project/engine"
out="$project/build-output/local-playtest"
source_sha=$(git -C "$root" rev-parse HEAD)
short_sha=$(git -C "$root" rev-parse --short=12 HEAD)

# An unchanged, identifiable source checkout is essential for meaningful QA.
dirty=$(git -C "$root" status --porcelain -- "Pokemon Game/engine")
if [[ -n "$dirty" ]]; then
  echo "STOP: game engine has uncommitted/untracked source edits."
  echo "$dirty"
  echo "Use a clean, dedicated WSL worktree at a verified commit first."
  exit 2
fi

mkdir -p "$out"
file="Averon-DEV-$short_sha.gba"
git -C "$root" check-ignore -q "Pokemon Game/build-output/local-playtest/$file" || {
  echo "STOP: destination is not gitignored"; exit 2;
}

cd "$engine"
echo "Building CLEAN source $source_sha"
make -j4 -O all > "$out/build.log" 2>&1 || {
  tail -120 "$out/build.log"; exit 1;
}
test -s pokeemerald.gba
python3 "../scripts/check-averon-resource-budget.py" \
  --log "$out/build.log" --rom pokeemerald.gba \
  --json "$out/resource.json"
test -x tools/mgba/mgba-rom-test
make -j4 -O check TESTS=Averon > "$out/native.log" 2>&1 || {
  tail -110 "$out/native.log"; exit 1;
}
make -j4 -O check TESTS=test/save.c > "$out/save.log" 2>&1 || {
  tail -110 "$out/save.log"; exit 1;
}
python3 - "$out" "$source_sha" "$file" <<'PY'
import hashlib, importlib.util, json, pathlib, sys
out, sha, name = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
script = pathlib.Path("../scripts/coordination/verify_build_readiness.py").resolve()
spec = importlib.util.spec_from_file_location("readiness", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
native = module.parse_test_log((out / "native.log").read_text(errors="replace"), "Averon")
save = module.parse_test_log((out / "save.log").read_text(errors="replace"), "flash/save")
resource = json.loads((out / "resource.json").read_text())
actual = hashlib.sha256(pathlib.Path("pokeemerald.gba").read_bytes()).hexdigest()
if actual != resource["rom_artifact"]["sha256"]:
    raise ValueError("Local ROM digest mismatch")
manifest = {
    "status": "LOCAL_DEVELOPMENT_ROM_NOT_GRAPHICALLY_ACCEPTED",
    "source_sha": sha, "rom_filename": name, "rom_sha256": actual,
    "rom_bytes": resource["rom_artifact"]["size_bytes"],
    "native": native, "save": save, "memory": resource["memory"],
    "warning": "Owner-local only. No game scene or Delta iOS verification implied."
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("PASS:", manifest["status"], "native", native, "save", save)
PY
cp -f -- pokeemerald.gba "$out/$file"
sha256sum "$out/$file"
# Actual local compiler/tool/source provenance, separate from native and gameplay QA.
python3 "../scripts/coordination/toolchain_manifest.py" \\
  --repo "$root" --engine "$engine" --rom "$out/$file" \\
  --out "$out/toolchain.json" --strict
echo "Private ROM for owner playtest: $out/$file"
echo "Manifest: $out/manifest.json"
echo "Toolchain provenance: $out/toolchain.json"
echo "This has not been tested in Delta iOS or accepted for public distribution."
