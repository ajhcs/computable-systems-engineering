"""Negative controls for independent execution and finite exploration limits."""
import copy
import json
import subprocess
import tempfile
from hashlib import sha256
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import load_json, verify


class CompletionTests(unittest.TestCase):
    def model(self):
        return copy.deepcopy(load_json(ROOT / 'examples/verifier/valid.json'))

    def test_unsupported_consistency_does_not_skip_broken_scenario(self):
        model = self.model()
        model['statements']['R1']['when'] = {'ref': 'speed', 'op': '==', 'value': 1, 'unit': 'm/s'}
        model['scenarios']['S1']['steps']['T1'].pop('produces')
        result = verify(model, review=True)
        self.assertEqual(result['obligations']['consistency'], 'unsupported')
        self.assertEqual(result['obligations']['scenarios'], 'fail')
        self.assertNotIn('scenarios', result['completed_obligations'])
        self.assertTrue(any(f['rule'] == 'step-reachability' for f in result['findings']))

    def test_supported_scenario_runs_with_unsupported_consistency(self):
        model = self.model()
        model['statements']['R1']['when'] = {'ref': 'speed', 'op': '==', 'value': 1, 'unit': 'm/s'}
        result = verify(model, review=True)
        self.assertEqual(result['obligations']['scenarios'], 'pass')
        self.assertEqual(result['status'], 'unsupported')

    def test_definite_dead_end_survives_later_branch_limit(self):
        model = self.model()
        scenario = model['scenarios']['S1']
        scenario.update(start='start', external_at=[], require_completion=False,
                        steps={'A': {'from': 'start', 'to': 'dead'},
                               'B': {'from': 'start', 'to': 'branch'},
                               'C': {'from': 'branch', 'to': 'next'},
                               'D': {'from': 'next', 'to': 'done'}})
        # Four initial input contexts, each branches. All dead states are
        # inspected before the branch expansion exceeds the transition cap.
        result = verify(model, review=True, state_cap=14)
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any(f['rule'] == 'dead-end' and f['evidence']['node'] == 'dead'
                            for f in result['findings']))
        self.assertTrue(any(f['status'] == 'unknown' for f in result['findings']))
        self.assertNotIn('scenarios', result['completed_obligations'])

    def test_invalid_library_caps_are_reported_without_execution(self):
        for cap in (0, -1, True, 1.5, '2', None):
            for name in ('assignment_cap', 'state_cap'):
                with self.subTest(cap=cap, name=name):
                    result = verify(self.model(), review=True, **{name: cap})
                    self.assertEqual(result['status'], 'error')
                    self.assertEqual(result['obligations']['scenarios'], 'not_run')
                    self.assertEqual(result['completed_obligations'], [])

    def test_cap_alone_remains_unknown(self):
        result = verify(self.model(), review=True, state_cap=4)
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(any(f['rule'] == 'step-reachability' for f in result['findings']))


class ScopeManifestTests(unittest.TestCase):
    model = CompletionTests.model
    def manifest(self):
        return {'version': 1, 'source_revision': 'synthetic-review-1',
                'requirements': ['R1', 'R2'], 'scenarios': ['S1']}

    def test_exact_scope_adds_completed_obligation_and_dependency(self):
        report = verify(self.model(), review=True, manifest=self.manifest())
        self.assertEqual(report['status'], 'pass')
        self.assertIn('scope', report['completed_obligations'])
        self.assertEqual(report['analyzed_scenarios'], ['S1'])
        self.assertEqual(report['review_manifest']['source_revision'], 'synthetic-review-1')
        self.assertEqual(len(report['dependencies']['manifest_sha256']), 64)
        self.assertEqual(report['limits'], {'assignment_cap': 100000, 'state_cap': 100000})

    def test_deletion_reclassification_and_new_unclassified_obligations(self):
        for mode in ('delete', 'reclassify', 'add'):
            model = self.model()
            if mode == 'delete':
                del model['statements']['R2']
                model['traces'] = [t for t in model['traces'] if t['from'] != 'R2']
            elif mode == 'reclassify':
                model['statements']['R2'] = {'category': 'goal', 'subject': 'System', 'text': 'Changed'}
                model['traces'] = [t for t in model['traces'] if t['from'] != 'R2']
            else:
                model['statements']['R3'] = copy.deepcopy(model['statements']['R2'])
                model['traces'].append({'from': 'R3', 'to': 'N1', 'kind': 'justifies'})
            with self.subTest(mode=mode):
                # Mutation remains structurally executable without external scope.
                self.assertEqual(verify(model, review=True)['status'], 'pass')
                report = verify(model, review=True, manifest=self.manifest())
                self.assertEqual(report['obligations']['scope'], 'fail')
                self.assertNotIn('scope', report['completed_obligations'])

    def test_bad_manifest_shapes_duplicates_and_wrong_kinds(self):
        variants = [[], {}, {**self.manifest(), 'version': True},
                    {**self.manifest(), 'source_revision': ' '},
                    {**self.manifest(), 'extra': True},
                    {**self.manifest(), 'requirements': ['R1', 'R1', 'R2']},
                    {**self.manifest(), 'requirements': ['R1', {}]},
                    {**self.manifest(), 'requirements': ['N1', 'R2']},
                    {**self.manifest(), 'scenarios': ['R1']},
                    {**self.manifest(), 'scenarios': []}]
        for manifest in variants:
            with self.subTest(manifest=manifest):
                report = verify(self.model(), review=True, manifest=manifest)
                self.assertIn(report['obligations']['scope'], ('error', 'fail'))
                self.assertNotEqual(report['status'], 'pass')
                self.assertEqual(report['limits']['state_cap'], 100000)

    def test_focus_keeps_global_scope_and_requirement_consistency(self):
        model = self.model()
        model['scenarios']['S2'] = {'start': 'abort', 'initial': {'speed': 0},
                                    'terminal': {'abort': 'intentional'}, 'steps': {}}
        model['traces'].append({'from': 'S2', 'to': 'R2', 'kind': 'addresses'})
        manifest = self.manifest()
        manifest['scenarios'].append('S2')
        report = verify(model, review=True, selected=['S1'], manifest=manifest)
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['analyzed_scenarios'], ['S1'])
        self.assertEqual(report['review_manifest']['scenarios'], ['S1', 'S2'])
        model['statements']['R2']['when'] = copy.deepcopy(model['statements']['R1']['when'])
        self.assertEqual(verify(model, review=True, selected=['S1'], manifest=manifest)['status'], 'fail')
        del model['scenarios']['S2']
        model['traces'].pop()
        report = verify(model, review=True, selected=['S1'], manifest=manifest)
        self.assertEqual(report['obligations']['scope'], 'fail')

    def test_scope_and_digest_are_order_independent_but_cli_binds_bytes(self):
        model = self.model()
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            path = Path(directory) / 'manifest.json'
            path.write_text(json.dumps(self.manifest(), indent=2), encoding='utf-8')
            command = [sys.executable, '-B', str(ROOT / 'scripts/verify.py'),
                       str(ROOT / 'examples/verifier/valid.json'), '--manifest', str(path), '--review', '--json']
            first = subprocess.run(command, text=True, capture_output=True, check=True)
            report = json.loads(first.stdout)
            self.assertEqual(report['dependencies']['manifest_file_sha256'], sha256(path.read_bytes()).hexdigest())
            path.write_text(json.dumps(self.manifest(), sort_keys=True), encoding='utf-8')
            second = json.loads(subprocess.run(command, text=True, capture_output=True, check=True).stdout)
            self.assertEqual(report['dependencies']['manifest_sha256'], second['dependencies']['manifest_sha256'])
            self.assertNotEqual(report['dependencies']['manifest_file_sha256'], second['dependencies']['manifest_file_sha256'])


if __name__ == '__main__':
    unittest.main()
