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


def event_identifier_contract(maps, template_capacity):
    """mapjson emits object IDs i+1 and warp IDs i into one global header."""
    identifiers = {}
    maximum_objects = maximum_warps = 0
    for data in maps:
        for key, limit, first, symbol in (("object_events", template_capacity, 1, "local_id"),
                                           ("warp_events", 128, 0, "warp_id")):
            events = data.get(key)
            if not isinstance(events, list) or len(events) > limit:
                raise ValueError(key + " exceeds native saved-template/signed-warp capacity")
            if key == "object_events":
                maximum_objects = max(maximum_objects, len(events))
            else:
                maximum_warps = max(maximum_warps, len(events))
            for index, event in enumerate(events, first):
                if not isinstance(event, dict):
                    raise ValueError("invalid event record")
                if symbol not in event:
                    continue
                name = event[symbol]
                if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
                    raise ValueError("invalid generated event macro")
                if name in identifiers and identifiers[name] != index:
                    raise ValueError("conflicting generated event identifier: " + name)
                identifiers[name] = index
    return maximum_objects, maximum_warps


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
        cls.maps = [json.loads((ENGINE / "data/maps" / name / "map.json").read_text())
                    for name in AVERON_ORDER]
        cls.constants = {name: data["id"] for name, data in zip(AVERON_ORDER, cls.maps)}
        capacity = re.search(r"^#define\s+OBJECT_EVENT_TEMPLATES_COUNT\s+(\d+)\s*$",
                             (ENGINE / "include/constants/global.h").read_text(), re.M)
        if not capacity:
            raise ValueError("saved object-template capacity needs source review")
        cls.template_capacity = int(capacity[1])

    def test_existing_event_identifiers_fit_engine_storage(self):
        objects, warps = event_identifier_contract(self.maps, self.template_capacity)
        print(f"Existing Averon16 maps: max objects={objects}/{self.template_capacity}, max warps={warps}/128")

    def test_static_objects_use_saved_capacity_not_active_sprite_count(self):
        for count in (0, 16, 17, self.template_capacity):
            data = {"object_events": [{} for _ in range(count)], "warp_events": []}
            self.assertEqual(event_identifier_contract([data], self.template_capacity), (count, 0))
        data["object_events"].append({})
        with self.assertRaises(ValueError):
            event_identifier_contract([data], self.template_capacity)

    def test_warp_event_index127_fits_but128_does_not(self):
        data = {"object_events": [], "warp_events": [{} for _ in range(128)]}
        data["warp_events"][-1]["warp_id"] = "WARP_BOUNDARY"
        self.assertEqual(event_identifier_contract([data], 64), (0, 128))
        data["warp_events"].append({"warp_id": "WARP_OVERFLOW"})
        with self.assertRaises(ValueError):
            event_identifier_contract([data], 64)

    def test_conflicting_event_macros_across_maps_and_kinds_are_rejected(self):
        a = {"object_events": [{"local_id": "SYMBOL"}], "warp_events": []}
        for b in ({"object_events": [{}, {"local_id": "SYMBOL"}], "warp_events": []},
                  {"object_events": [], "warp_events": [{"warp_id": "SYMBOL"}]}):
            with self.assertRaises(ValueError):
                event_identifier_contract([a, b], 64)
        # Repeated identical numeric macros are legal in the generated header.
        self.assertEqual(event_identifier_contract([a, copy.deepcopy(a)], 64), (1, 0))

    def test_bad_event_macro_names_and_records_are_rejected(self):
        for value in ("", "1LOCAL", "bad-name", 1, True, None):
            data = {"object_events": [{"local_id": value}], "warp_events": []}
            with self.subTest(value=value), self.assertRaises(ValueError):
                event_identifier_contract([data], 64)
        for value in (None, {}, [None]):
            data = {"object_events": [], "warp_events": value}
            with self.subTest(value=value), self.assertRaises(ValueError):
                event_identifier_contract([data], 64)

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
