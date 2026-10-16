"""Read-only map-ID/warp-encoding contract; never authors maps or geometry.

Run with --generated-header ENGINE/include/constants/map_groups.h from an
actual existing build. Layout/collision QA is check-averon-maps.py's concern.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import unittest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--generated-header", type=Path, required=True)
args, unittest_args = parser.parse_known_args()

# Existing published map identities, not new map content or allocations.
AVERON_ORDER = ["Saltmere", "SaltmereGreenhouse", "SaltmereWorkshop", "SaltmereHarbor", "SaltmereHome",
                "CoastalMeadow", "Windrow", "WindrowCooperative", "OrchardLane", "Alderfield",
                "AlderfieldGym", "AlderfieldClinic", "AlderfieldSupply", "CoastalBluffs",
                "AveronFieldLab", "AveronFieldLabUnderwater"]


def registry(groups):
    order = groups.get("group_order")
    if not isinstance(order, list) or not order or len(order) > 128:
        raise ValueError("group_order must fit signed-byte warp group IDs")
    if any(not isinstance(g, str) for g in order) or len(set(order)) != len(order):
        raise ValueError("duplicate or invalid group identity")
    if set(order) != {name for name in groups if name.startswith("gMapGroup_")}:
        raise ValueError("group_order must list each declared group exactly once")
    bindings = {}
    for group_id, group in enumerate(order):
        names = groups.get(group)
        if not isinstance(names, list) or not names or len(names) > 128:
            raise ValueError("map numbers must fit signed-byte warp IDs")
        for number, name in enumerate(names):
            if not isinstance(name, str) or not name or name in bindings:
                raise ValueError("duplicate or invalid map identity")
            bindings[name] = (group_id, number)
    return bindings


def stable_averon(bindings):
    for number, name in enumerate(AVERON_ORDER):
        if bindings.get(name) != (75, number):
            raise ValueError("existing saved/QA map identity changed: " + name)


def generated_contract(groups, header, constants):
    bindings = registry(groups)
    stable_averon(bindings)
    declared = re.search(r"^#define\s+MAP_GROUPS_COUNT\s+(\d+)\s*$", header, re.M)
    if not declared or int(declared[1]) != len(groups["group_order"]):
        raise ValueError("generated group count disagrees with source")
    matches = re.findall(r"^\s*(MAP_\w+)\s*=\s*\((\d+)\s*\|\s*\((\d+)\s*<<\s*8\)\),", header, re.M)
    generated = {}
    for macro, number, group in matches:
        if macro in generated:
            raise ValueError("duplicate generated map constant")
        generated[macro] = (int(group), int(number))
    if len(generated) != len(bindings) or set(generated.values()) != set(bindings.values()):
        raise ValueError("generated bindings missing, duplicated or out of source range")
    for name, macro in constants.items():
        if generated.get(macro) != bindings[name]:
            raise ValueError("generated Averon constant disagrees with source: " + macro)


class MapRegistryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups = json.loads((ENGINE / "data/maps/map_groups.json").read_text())
        cls.header = args.generated_header.read_text()
        # Read only the already-published Averon identities, not every map's
        # geometry/events or the old unrelated reference/design documents.
        cls.constants = {name: json.loads((ENGINE / "data/maps" / name / "map.json").read_text())["id"]
                         for name in AVERON_ORDER}

    def test_live_registry_and_generated_header(self):
        generated_contract(self.groups, self.header, self.constants)

    def test_existing_averon_identities_are_stable(self):
        stable_averon(registry(self.groups))

    def test_duplicate_group_rejected(self):
        groups = copy.deepcopy(self.groups)
        groups["group_order"][1] = groups["group_order"][0]
        with self.assertRaises(ValueError):
            registry(groups)

    def test_duplicate_map_across_groups_rejected(self):
        groups = copy.deepcopy(self.groups)
        a, b = groups["group_order"][:2]
        groups[b][0] = groups[a][0]
        with self.assertRaises(ValueError):
            registry(groups)

    def test_unlisted_group_rejected(self):
        groups = copy.deepcopy(self.groups)
        groups["group_order"].pop()
        with self.assertRaises(ValueError):
            registry(groups)

    def test_invalid_map_identity_rejected(self):
        for value in (None, "", 13, []):
            groups = copy.deepcopy(self.groups)
            groups[groups["group_order"][0]][0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                registry(groups)

    def test_signed_group_boundary_and_overflow(self):
        order = ["gMapGroup_Test" + str(i) for i in range(128)]
        groups = {name: ["Symbol" + str(i)] for i, name in enumerate(order)}
        groups["group_order"] = order
        self.assertEqual(registry(groups)["Symbol127"], (127, 0))
        groups["gMapGroup_Overflow"] = ["Overflow"]
        groups["group_order"].append("gMapGroup_Overflow")
        with self.assertRaises(ValueError):
            registry(groups)

    def test_signed_map_number_boundary_and_overflow(self):
        groups = {"group_order": ["gMapGroup_Test"], "gMapGroup_Test": ["Symbol" + str(i) for i in range(128)]}
        self.assertEqual(registry(groups)["Symbol127"], (0, 127))
        groups["gMapGroup_Test"].append("Overflow")
        with self.assertRaises(ValueError):
            registry(groups)

    def test_moving_averon_group_is_detected(self):
        groups = copy.deepcopy(self.groups)
        group = groups["group_order"].pop(75)
        groups["group_order"].insert(0, group)
        with self.assertRaises(ValueError):
            stable_averon(registry(groups))

    def test_reordering_existing_averon_maps_is_detected(self):
        groups = copy.deepcopy(self.groups)
        maps = groups["gMapGroup_AveronOpening"]
        maps[0], maps[1] = maps[1], maps[0]
        with self.assertRaises(ValueError):
            stable_averon(registry(groups))

    def test_wrong_generated_count_is_detected(self):
        changed = re.sub(r"(#define\s+MAP_GROUPS_COUNT\s+)\d+", r"\g<1>127", self.header)
        with self.assertRaises(ValueError):
            generated_contract(self.groups, changed, self.constants)

    def test_missing_generated_map_is_detected(self):
        changed = re.sub(r"^\s*MAP_SALTMERE\s*=.*$", "", self.header, flags=re.M)
        with self.assertRaises(ValueError):
            generated_contract(self.groups, changed, self.constants)


if __name__ == "__main__":
    unittest.main(argv=[__file__, *unittest_args], verbosity=2)
