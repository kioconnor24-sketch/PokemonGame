"""Positive/negative temporary fixtures; no maps, codebook or schema written."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from averon_origin_demand import origin_demand, read_area_register

SCRIPT = SCRIPTS / "audit-averon-mapsec-namespace.py"
spec = importlib.util.spec_from_file_location("origin_inventory", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
ENGINE = SCRIPTS.parent / "engine"
REGISTER = SCRIPTS.parent / "Averon_Codex_Handoff/development/SINNOH_AREA_REGISTER.csv"


def area(key, name):
    return {"TrackerKey": key, "LocationOrZone": name}


def section(ident="MAPSEC_SANDGEM_TOWN", name="SANDGEM TOWN", value=216, region="REGION_SINNOH"):
    return dict(id=ident, name=name, value=value, region=region)


class OriginDemandTests(unittest.TestCase):
    def test_fixed_pool_never_reclaims_legacy_holes_none_or_specials(self):
        result = origin_demand([area("A", "New town")], [])
        self.assertEqual(result["available_values"], list(range(216, 253)))
        self.assertEqual(result["remaining_ordinary_codes"], 37)
        self.assertFalse(result["inventory_complete"])
        self.assertEqual(result["production_allocations"], [])

    def test_counts_names_not_maps_or_case_and_whitespace(self):
        rows = [area("A", "Sandgem Town"), area("B", " SANDGEM  TOWN ")]
        result = origin_demand(rows, [section()])
        self.assertEqual(result["registered_areas"], 2)
        self.assertEqual(result["distinct_proposed_names"], 1)
        self.assertEqual(result["new_names_required"], 0)
        self.assertEqual(result["already_allocated_sinnoh_names"][0]["value"], 216)

    def test_same_legacy_name_from_another_region_is_not_reused(self):
        legacy = section("MAPSEC_VICTORY_ROAD", "VICTORY ROAD", 0, "REGION_HOENN")
        result = origin_demand([area("A", "Victory Road")], [legacy])
        self.assertEqual(result["new_names_required"], 1)
        self.assertEqual(result["already_allocated_sinnoh_names"], [])
        self.assertEqual(result["legacy_same_name_not_reused"][0]["legacy_ids"], [legacy["id"]])

    def test_other_region_additions_consume_the_same_pool(self):
        future = section("MAPSEC_NEW_AVERON", "New Averon", 218, "REGION_HOENN")
        result = origin_demand([area("A", "Sandgem Town")], [section(), future])
        self.assertEqual(result["remaining_ordinary_codes"], 35)
        self.assertNotIn(218, result["available_values"])

    def test_nameless_legacy_dynamic_identity_is_preserved_not_reclaimed(self):
        result = origin_demand([area("A", "New town")], [{"id": "MAPSEC_DYNAMIC", "value": 88}])
        self.assertEqual(result["remaining_ordinary_codes"], 37)
        self.assertNotIn(88, result["available_values"])

    def test_explicit_aliases_share_only_proposed_names(self):
        rows = [area("A", "Unbuilt place A"), area("B", "Unbuilt place B")]
        result = origin_demand(rows, [], aliases={"A": "Candidate group", "B": "Candidate group"})
        self.assertEqual(result["new_names_required"], 1)
        self.assertEqual(result["name_groups"][0]["area_keys"], ["A", "B"])

    def test_frozen_sinnoh_origin_cannot_be_regrouped(self):
        with self.assertRaisesRegex(ValueError, "cannot regroup"):
            origin_demand([area("A", "Sandgem Town")], [section()], {"A": "Candidate group"})

    def test_frozen_sinnoh_name_cannot_silently_expand_to_another_area(self):
        with self.assertRaisesRegex(ValueError, "cannot expand"):
            origin_demand([area("A", "Different town")], [section()], {"A": "Sandgem Town"})

    def test_unknown_alias_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "registered areas"):
            origin_demand([area("A", "Place")], [], {"TYPO": "Group"})

    def test_duplicate_area_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate area"):
            origin_demand([area("A", "One"), area("A", "Two")], [])

    def test_empty_area_inventory_or_names_are_rejected(self):
        for rows in ([], [area("", "Town")], [area("A", " ")], [area("A", 12)]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                origin_demand(rows, [])

    def test_reserved_values_and_non_integer_values_are_rejected(self):
        for value in (215, 253, 254, 255, 256, -1, True, "216"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                origin_demand([area("A", "Town")], [section(value=value)])

    def test_duplicate_or_reserved_section_identities_are_rejected(self):
        for entries in ([section(), section()], [section(ident="MAPSEC_NONE")],
                        [section(), section(ident="OTHER", value=216)],
                        [section(), section(value=217)], [None]):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                origin_demand([area("A", "Town")], entries)

    def test_ambiguous_existing_sinnoh_names_are_not_collapsed(self):
        entries = [section(), section(ident="SECOND", value=217)]
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            origin_demand([area("A", "Sandgem Town")], entries)

    def test_exact_fit_and_one_name_overflow_are_distinct(self):
        rows = [area(str(i), f"Candidate {i}") for i in range(37)]
        fit = origin_demand(rows, [])
        self.assertTrue(fit["fits_current_byte_pool"])
        self.assertEqual(fit["shortfall"], 0)
        over = origin_demand(rows + [area("extra", "Extra")], [])
        self.assertFalse(over["fits_current_byte_pool"])
        self.assertEqual(over["shortfall"], 1)

    def test_allocating_a_planned_origin_does_not_change_the_forecast_gap(self):
        # In-memory codebook fixtures only, not production identities.
        rows = [area(str(i), f"Candidate {i}") for i in range(48)]
        before = origin_demand(rows, [])
        after = origin_demand(rows, [section(name="Candidate 0")])
        self.assertEqual((before["new_names_required"], before["remaining_ordinary_codes"]), (48, 37))
        self.assertEqual((after["new_names_required"], after["remaining_ordinary_codes"]), (47, 36))
        self.assertEqual((before["shortfall"], after["shortfall"]), (11, 11))

    def test_allocating_an_excluded_lake_increases_the_filtered_forecast_gap(self):
        rows = [area(str(i), f"Candidate {i}") for i in range(48)]
        after = origin_demand(rows, [section(name="Excluded lake")])
        self.assertEqual(after["new_names_required"], 48)
        self.assertEqual(after["remaining_ordinary_codes"], 36)
        self.assertEqual(after["shortfall"], 12)
        self.assertFalse(after["fits_current_byte_pool"])
        self.assertEqual(after["production_allocations"], [])

    def test_extra_child_names_and_future_averon_reserve_are_explicit(self):
        result = origin_demand([area("A", "Town")], [], additional=["Town", "New child"], reserve=36)
        self.assertEqual(result["distinct_proposed_names"], 2)
        self.assertEqual(result["shortfall"], 1)

    def test_invalid_optional_inputs_are_rejected(self):
        for kwargs in ({"reserve": -1}, {"reserve": True}, {"aliases": []},
                       {"additional": "not a list"}, {"additional": [None]}, {"aliases": {"A": None}}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                origin_demand([area("A", "Town")], [], **kwargs)

    def test_inputs_are_not_modified(self):
        rows, entries, aliases = [area("A", "Sandgem Town")], [section()], {}
        expected = copy.deepcopy((rows, entries, aliases))
        origin_demand(rows, entries, aliases)
        self.assertEqual((rows, entries, aliases), expected)

    def test_temporary_csv_requires_columns_and_unique_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "areas.csv"
            for text in ("Bad,Header\na,b\n", "TrackerKey,LocationOrZone\nA,One\nA,Two\n"):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    read_area_register(path)
            path.write_text('TrackerKey,LocationOrZone\nA,"Two words"\n')
            self.assertEqual(len(read_area_register(path)), 1)

    def test_current_complete_register_is_a_scenario_not_full_submap_demand(self):
        rows = read_area_register(REGISTER)
        result = origin_demand(rows, audit.sections(ENGINE))
        self.assertEqual(result["registered_areas"], 87)
        self.assertEqual(result["distinct_proposed_names"], 87)
        self.assertEqual(result["shortfall"], 50)
        self.assertFalse(result["inventory_complete"])

    def test_current_cli_overflow_writes_evidence_and_returns_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            run = subprocess.run([sys.executable, str(SCRIPT), "--engine", str(ENGINE),
                "--planned-area-register", str(REGISTER), "--json", str(out)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertIn("PLANNING BUDGET EXCEEDED", run.stdout)
            self.assertEqual(json.loads(out.read_text())["planned_origin_demand"]["shortfall"], 50)

    def test_cli_optional_origin_inputs_require_a_register(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "--origin-reserve", "1"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn("require --planned-area-register", run.stderr)

    def test_main_settlement_and_route_names_alone_exceed_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report.json"
            run = subprocess.run([sys.executable, str(SCRIPT), "--engine", str(ENGINE),
                "--planned-area-register", str(REGISTER), "--origin-kinds", "SETTLEMENT,POSTGAME_HUB,ROUTE",
                "--json", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, run.stderr)
            demand = json.loads(output.read_text())["planned_origin_demand"]
            self.assertEqual(demand["registered_areas"], 48)
            self.assertEqual(demand["distinct_proposed_names"], 48)
            # An allocated lake/cave outside this filtered scenario still
            # consumes the same byte pool. Lake Verity made the old fixed11
            # assertion stale; future approved off-scenario origins also count.
            kinds = {"SETTLEMENT", "POSTGAME_HUB", "ROUTE"}
            names = {" ".join(row["LocationOrZone"].upper().split())
                     for row in read_area_register(REGISTER) if row["Kind"] in kinds}
            excluded_allocations = sum(
                1 for entry in audit.sections(ENGINE)
                if 216 <= entry["value"] <= 252 and not (
                    entry.get("region") == "REGION_SINNOH"
                    and " ".join(entry.get("name", "").upper().split()) in names))
            self.assertEqual(demand["shortfall"], len(names) - 37 + excluded_allocations)
            self.assertEqual(demand["source_register_areas"], 87)

    def test_unknown_or_empty_kind_filter_cannot_report_false_capacity(self):
        for kinds in ("TYPO", ",", "ROUTE,TYPO"):
            with self.subTest(kinds=kinds):
                run = subprocess.run([sys.executable, str(SCRIPT), "--engine", str(ENGINE),
                    "--planned-area-register", str(REGISTER), "--origin-kinds", kinds], capture_output=True, text=True)
                self.assertEqual(run.returncode, 2)
                self.assertIn("existing register Kind", run.stderr)

    def test_cli_fitting_temporary_named_scenario_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            register = Path(tmp) / "areas.csv"
            register.write_text("TrackerKey,LocationOrZone\nA,Sandgem Town\n")
            output = Path(tmp) / "report.json"
            run = subprocess.run([sys.executable, str(SCRIPT), "--engine", str(ENGINE),
                "--planned-area-register", str(register), "--json", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(output.read_text())["planned_origin_demand"]["new_names_required"], 0)

    def test_cli_frozen_name_alias_returns_two_without_allocations(self):
        with tempfile.TemporaryDirectory() as tmp:
            register = Path(tmp) / "areas.csv"
            register.write_text("TrackerKey,LocationOrZone\nA,Sandgem Town\n")
            aliases = Path(tmp) / "aliases.json"
            aliases.write_text(json.dumps({"A": "Different name"}))
            run = subprocess.run([sys.executable, str(SCRIPT), "--engine", str(ENGINE),
                "--planned-area-register", str(register), "--origin-aliases", str(aliases)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("cannot regroup", run.stderr)

    def test_cli_same_name_as_legacy_victory_road_still_requires_a_new_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            register = Path(tmp) / "areas.csv"
            register.write_text("TrackerKey,LocationOrZone\nA,Victory Road\n")
            output = Path(tmp) / "report.json"
            run = subprocess.run([sys.executable, str(SCRIPT), "--engine", str(ENGINE),
                "--planned-area-register", str(register), "--json", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            demand = json.loads(output.read_text())["planned_origin_demand"]
            self.assertEqual(demand["new_names_required"], 1)
            self.assertTrue(demand["legacy_same_name_not_reused"])

    def test_current_cli_without_scenario_retains_legacy_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            run = subprocess.run([sys.executable, str(SCRIPT), "--engine", str(ENGINE),
                "--check-pins", "--json", str(out)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertNotIn("planned_origin_demand", json.loads(out.read_text()))


if __name__ == "__main__":
    unittest.main()
