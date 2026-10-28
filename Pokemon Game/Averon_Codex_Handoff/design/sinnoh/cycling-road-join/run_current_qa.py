"""W25 source-qualified traversal using the existing rendered map_qa runner.

Route207's stock muddy slope is a one-way foot drop. Test its northern ports
before descending; do not claim a bike return or remove any portal checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[3] / "scripts/claude_play"
sys.path.insert(0, str(SCRIPTS))
import map_qa as qa
import driver  # Load the same source tree's driver before the engine wrapper.

MAPS = ("MAP_ETERNA_CITY", "MAP_ROUTE211_WEST", "MAP_ROUTE206_NORTH", "MAP_ROUTE206",
        "MAP_ROUTE206_SOUTH", "MAP_ROUTE207", "MAP_OREBURGH_CITY", "MAP_OREBURGH_GATE_1F",
        "MAP_OREBURGH_GATE_B1F", "MAP_OREBURGH_MINE_B1F", "MAP_OREBURGH_MINE_B2F")


def ordered_points(points):
    """Stable permutation only: no check or destination is discarded."""
    return sorted(points, key=lambda p: 0 if p["kind"] == "connection" and p["direction"] == "up" else 1)


def validate(engine, receipt):
    engine = Path(engine).resolve()
    if not (engine / ".map_qa_throwaway").is_file():
        raise ValueError("marked disposable source required")
    if len(receipt["files"]) not in (61, 63):
        raise ValueError("exact W25 source receipt required")
    for path, expected in receipt["files"].items():
        p = Path(path)
        target = engine / p
        if p.is_absolute() or ".." in p.parts or not target.resolve().is_relative_to(engine):
            raise ValueError("source path escapes engine")
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError("source differs: " + path)
    if len(receipt["files"]) == 63:
        # Keep supported legacy31/39-map scenes; padding a post-C receipt must
        # not route it around the stricter post-C contract.
        groups_file = engine / "data/maps/map_groups.json"
        if groups_file.is_file():
            groups = json.loads(groups_file.read_text())["gMapGroup_Sinnoh"]
            if len(groups) not in (31, 39):
                raise ValueError("legacy63 receipt has an unsupported scene prefix")
    if len(receipt["files"]) == 61:
        # Post-packet-C retains production City's scripts/border and overlays only
        # its header/blocks. Accept this explicit contract, not any smaller receipt.
        groups_path = "data/maps/map_groups.json"
        city_path = "data/maps/OreburghCity/map.json"
        required = {groups_path, city_path, "data/layouts/OreburghCity/map.bin"}
        retained = {"data/maps/OreburghCity/scripts.inc", "data/layouts/OreburghCity/border.bin"}
        if not required <= receipt["files"].keys() or retained & receipt["files"].keys():
            raise ValueError("post-C production City preservation contract differs")
        contract = json.loads((HERE / "post-c-qa-contract.json").read_text())
        if set(receipt["files"]) != set(contract["payload_paths"]):
            raise ValueError("post-C source path set differs")
        try:
            document = json.loads((engine / groups_path).read_text())
            groups = document["gMapGroup_Sinnoh"]
            city = json.loads((engine / city_path).read_text())
            suffix = ["EternaCity", "Route206_North", "Route206", "Route206_South", "Route211_West",
                      "Route207", "OreburghMine_B1F", "OreburghMine_B2F"]
            valid = (len(groups) == 49 and groups[:41] == contract["production_prefix"]
                     and groups[30] == "OreburghCity"
                     and groups.count("OreburghCity") == 1 and groups[41:] == suffix
                     and city["region_map_section"] == "MAPSEC_OREBURGH_CITY"
                     and len(city["warp_events"]) == 15)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid post-C source metadata") from error
        if not valid:
            raise ValueError("post-C production City identity contract differs")
        # Bind the whole reconstructed baseline to the existing immutable profile
        # pin, rather than trusting a prefix or digest supplied by the receipt.
        profiles = json.loads((HERE / "current-runtime-base-pins.json").read_text())["profiles"]
        matching = [p for p in profiles if p["engine_tree"] == contract["engine_tree"]]
        if len(matching) != 1:
            raise ValueError("post-C pinned profile missing or ambiguous")
        document["gMapGroup_Sinnoh"] = groups[:41]
        baseline = (json.dumps(document, indent=2) + "\n").encode()
        if hashlib.sha256(baseline).hexdigest() != matching[0]["files"][groups_path]:
            raise ValueError("post-C full production registry pin differs")


class W25Runner(qa.Runner):
    def go(self, map_id, tile, _depth=0):
        ok = super().go(map_id, tile, _depth)
        if ok:
            self.d.settle()
        return ok and self.d.here() == (map_id, tuple(tile))

    def run_map(self, map_id):
        if map_id == "MAP_ROUTE207":
            self.plan[map_id]["points"] = ordered_points(self.plan[map_id]["points"])
        super().run_map(map_id)
        if map_id == "MAP_ROUTE207":
            # Actual input must return the walking player below the source mud.
            self.blocked(map_id, "18", "16", "up")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("engine", "receipt", "scratch", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--profile", choices=("normal", "release"), required=True)
    parser.add_argument("--expect", type=Path)
    args = parser.parse_args()
    engine, scratch, out = args.engine.resolve(), args.scratch.resolve(), args.out.resolve()
    validate(engine, json.loads(args.receipt.read_text()))
    if scratch.is_relative_to(engine) or out.is_relative_to(engine) or out == scratch:
        raise ValueError("external distinct scratch and evidence directories required")
    if not (scratch / "game.sav").is_file():
        raise ValueError("source-qualified private flash fixture required")
    qa.Runner = W25Runner
    rom = engine / ("pokeemerald-cries-off" + ("-release" if args.profile == "release" else "") + ".gba")
    config = argparse.Namespace(engine=str(engine), rom=str(rom), scratch=str(scratch), out=str(out),
                                build=args.profile, map=list(MAPS), expect=str(args.expect) if args.expect else None,
                                save="w25-current", blocked=None, region_ui=None, region_ui_map=None,
                                whiteout=None, whiteout_npc=None)
    code = qa.cmd_run(config)
    provenance = dict(scope="Directed source traversal; no ordinary bike acquisition or reciprocal foot climb claim",
                      host_probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      mapdata_sha256=hashlib.sha256((SCRIPTS / "mapdata.py").read_bytes()).hexdigest(),
                      map_qa_sha256=hashlib.sha256((SCRIPTS / "map_qa.py").read_bytes()).hexdigest(),
                      driver_sha256=hashlib.sha256((SCRIPTS / "driver.py").read_bytes()).hexdigest(),
                      source_maps=MAPS, source_gate="Route207 muddy slope requires bike speed northward")
    (out / "scenario.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
