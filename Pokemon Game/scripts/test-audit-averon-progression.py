"""Focused tests for designed region progression; no emulator required."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name('audit-averon-progression.py')
spec = importlib.util.spec_from_file_location('progress_audit', SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ProgressionTests(unittest.TestCase):
    def setUp(self):
        self.locations = [{'name': n} for n in [
            'Saltmere', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'Victory Isle', 'Silverwatch Summit']]
        self.gyms = [{'number': str(i), 'city': chr(ord('A') + i-1)} for i in range(1, 9)]
        self.routes = [{'id': 'R01', 'from': 'Saltmere', 'to': 'A', 'unlock': 'start'}]
        for i in range(1, 8):
            self.routes.append({'id': f'R{i+1:02d}', 'from': chr(ord('A')+i-1),
                                'to': chr(ord('A')+i), 'unlock': f'badge_{i}'})
        self.routes.append({'id': 'R09', 'from': 'H', 'to': 'Victory Isle', 'unlock': 'badge_8'})

    def test_no_badge_can_access_first_gym(self):
        reached, path = audit.walk(self.routes)
        self.assertEqual(reached, {'Saltmere', 'A'})
        self.assertEqual(path['A']['route'], 'R01')

    def test_gate_prevents_premature_access(self):
        reached, _ = audit.walk(self.routes, 2)
        self.assertEqual(reached, {'Saltmere', 'A', 'B', 'C'})
        self.assertNotIn('D', reached)

    def test_full_design_complete(self):
        report = audit.create_report(self.locations, self.routes, self.gyms)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(len(report['badge_checkpoints']), 9)
        self.assertTrue(all(row['next_objective_reachable'] for row in report['badge_checkpoints']))
        self.assertEqual(report['badge_checkpoints'][-1]['next_objective_path'][-1]['to'], 'Victory Isle')
        self.assertNotIn('Silverwatch Summit', report['planned_unreachable_locations'])

    def test_new_route_id_must_be_unique(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate route ID'):
            audit.create_report(self.locations, self.routes + [self.routes[0]], self.gyms)

    def test_missing_gym_route_detected(self):
        report = audit.create_report(self.locations, self.routes[:2], self.gyms)
        self.assertEqual(report['status'], 'FAILED DESIGN GRAPH')
        self.assertIn('Before Badge 3', report['issues'][0])

    def test_badge_progression_starts_at_previous_badge(self):
        self.routes[0]['unlock'] = 'badge_1'
        report = audit.create_report(self.locations, self.routes, self.gyms)
        self.assertFalse(report['badge_checkpoints'][0]['next_objective_reachable'])

    def test_typo_in_unlock_fails(self):
        self.routes[0]['unlock'] = 'badge9'
        with self.assertRaisesRegex(ValueError, 'unrecognized unlock'):
            audit.create_report(self.locations, self.routes, self.gyms)

    def test_invalid_scenario_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown scenario abilities'):
            audit.walk(self.routes, 4, {'teleport'})

    def test_ability_unlock_loop(self):
        self.routes.append({'id': 'R10', 'from': 'Saltmere', 'to': 'F', 'unlock': 'field_cut'})
        self.assertNotIn('F', audit.walk(self.routes, 0)[0])
        self.assertIn('F', audit.walk(self.routes, 0, {'field_cut'})[0])


if __name__ == '__main__':
    unittest.main()
