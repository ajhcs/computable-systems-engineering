"""Behavioral tests for bounded revision impact and independent recheck scope."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.impact import analyze, inspect, snapshot_workflow, snapshot_native, snapshot_schema
from verifier.foundation import Invalid, digest
from verifier.workflow import empty_record, draft_model
from verifier.sysml import JAR


def snapshot():
    nodes = {key: {'kind': 'element', 'native_name': 'Demo::' + key, 'sha256': digest(key)} for key in 'ABCDE'}
    return {'version': 'impact-snapshot-1.0', 'revision': {'id': 'baseline', 'sha256': digest('model')},
            'nodes': nodes, 'dependencies': {
                'AB': {'kind': 'uses', 'dependent': 'B', 'dependency': 'A'},
                'BC': {'kind': 'derived_from', 'dependent': 'C', 'dependency': 'B'},
                'AD': {'kind': 'view_of', 'dependent': 'D', 'dependency': 'A'},
                'DC': {'kind': 'uses', 'dependent': 'C', 'dependency': 'D'}},
            'complete': True, 'unresolved': []}


def scope():
    return {'version': 'impact-scope-1.0', 'checks': {
        'Global': {'targets': [], 'global': True},
        'CCheck': {'targets': ['C'], 'global': False},
        'ECheck': {'targets': ['E'], 'global': False}}}


def changed():
    old = snapshot(); new = deepcopy(old)
    new['nodes']['A']['sha256'] = digest('new A')
    new['revision'] = {'id': 'candidate', 'sha256': digest('new model')}
    return old, new


class ImpactTests(unittest.TestCase):
    def test_reverse_dependency_closure_shortest_reason_and_selection(self):
        old, new = changed(); r = analyze(old, new, scope())
        self.assertEqual(r['status'], 'pass')
        self.assertEqual(set(r['impacted']), set('ABCD'))
        self.assertEqual(r['impacted']['C']['depth'], 2)
        self.assertEqual([hop['id'] for hop in r['impacted']['C']['path']], ['AB', 'BC'])
        self.assertEqual(set(r['selected_checks']), {'Global', 'CCheck'})
        self.assertEqual(r['unselected_checks'], ['ECheck'])
        self.assertEqual(r['required_review'], 'not_evaluated')
        self.assertEqual(r['execution'], 'not_run')

    def test_direction_is_not_silently_reversed(self):
        old = snapshot(); new = deepcopy(old); new['nodes']['C']['sha256'] = digest('new')
        r = analyze(old, new, scope())
        self.assertEqual(set(r['impacted']), {'C'})

    def test_removed_node_propagates_through_retained_old_graph(self):
        old = snapshot(); new = deepcopy(old)
        del new['nodes']['A']; del new['dependencies']['AB']; del new['dependencies']['AD']
        r = analyze(old, new, scope())
        self.assertEqual(r['status'], 'pass'); self.assertEqual(r['changed']['removed'], ['A'])
        self.assertEqual(set(r['impacted']), set('ABCD'))
        self.assertEqual(r['impacted']['C']['path'][0]['revision'], 'baseline')

    def test_removed_edge_seeds_both_historical_endpoints(self):
        old = snapshot(); new = deepcopy(old); del new['dependencies']['AB']
        r = analyze(old, new, scope())
        self.assertEqual(r['changed']['dependencies'], ['AB'])
        self.assertEqual(r['coverage']['changed_seeds'], ['A', 'B'])
        self.assertIn('C', r['impacted'])
        self.assertEqual(r['change_reasons']['B'], [{'kind': 'dependency_changed', 'id': 'AB', 'revision': 'baseline'}])

    def test_retargeted_edge_retains_old_and_new_dependency(self):
        old = snapshot(); new = deepcopy(old); new['dependencies']['AB']['dependency'] = 'E'
        r = analyze(old, new, scope())
        self.assertEqual(r['coverage']['changed_seeds'], ['A', 'B', 'E'])
        self.assertIn('ECheck', r['selected_checks'])

    def test_cycles_terminate_without_forbidding_dependency_cycles(self):
        old, new = changed()
        for s in (old, new): s['dependencies']['CA'] = {'kind': 'uses', 'dependency': 'C', 'dependent': 'A'}
        r = analyze(old, new, scope())
        self.assertEqual(r['status'], 'pass'); self.assertEqual(len(r['impacted']), 4)
        self.assertLess(r['work'], 100)

    def test_missing_endpoint_broadens_every_retained_check(self):
        old, new = changed(); new['dependencies']['BC']['dependency'] = 'Missing'
        r = analyze(old, new, scope())
        self.assertEqual(r['status'], 'unknown')
        self.assertEqual(set(r['selected_checks']), set(scope()['checks']))
        self.assertIn('missing_dependency', [f['rule'] for f in r['findings']])

    def test_incomplete_either_revision_or_unresolved_prevents_narrowing(self):
        for where, field, value in [('old', 'complete', False), ('new', 'unresolved', ['external model omitted'])]:
            old, new = changed(); (old if where == 'old' else new)[field] = value
            r = analyze(old, new, scope())
            self.assertEqual(r['status'], 'unknown')
            self.assertEqual(set(r['selected_checks']), set(scope()['checks']))

    def test_cap_preserves_partial_reasons_and_forces_broad_selection(self):
        old, new = changed(); r = analyze(old, new, scope(), max_work=1)
        self.assertEqual(r['status'], 'unknown')
        self.assertEqual(r['coverage']['selection'], 'all_retained_checks')
        self.assertIn('A', r['impacted']); self.assertLessEqual(r['work'], 1)

    def test_deleted_check_targets_remain_in_independent_scope(self):
        old = snapshot(); new = deepcopy(old); del new['nodes']['E']
        r = analyze(old, new, scope())
        self.assertEqual(r['status'], 'pass'); self.assertIn('ECheck', r['selected_checks'])
        self.assertEqual(r['selected_checks']['ECheck']['targets'], ['E'])

    def test_target_absent_in_both_revisions_is_unknown(self):
        old, new = changed(); manifest = scope(); manifest['checks']['Missing'] = {'targets': ['Gone'], 'global': False}
        r = analyze(old, new, manifest)
        self.assertEqual(r['status'], 'unknown'); self.assertEqual(len(r['selected_checks']), 4)

    def test_empty_or_malformed_scope_and_unknown_rule_never_pass(self):
        old, new = changed()
        manifest = scope(); manifest['checks'] = {}
        self.assertEqual(analyze(old, new, manifest)['status'], 'error')
        new['dependencies']['AB']['kind'] = 'execute_python'
        self.assertEqual(analyze(old, new, scope())['status'], 'error')
        self.assertEqual(analyze(old, old, scope(), max_work=True)['status'], 'error')

    def test_no_change_selects_global_and_reports_no_regression_execution(self):
        old = snapshot(); r = analyze(old, old, scope())
        self.assertEqual(r['status'], 'pass'); self.assertEqual(r['impacted'], {})
        self.assertEqual(set(r['selected_checks']), {'Global'})
        self.assertEqual(r['selected_checks']['Global']['execution'], 'not_run')

    def test_input_order_does_not_change_paths(self):
        old, new = changed(); expected = analyze(old, new, scope())
        for s in (old, new):
            for field in ('nodes', 'dependencies'): s[field] = dict(reversed(list(s[field].items())))
        self.assertEqual(analyze(old, new, scope()), expected)

    def test_scope_file_pin_and_duplicate_json_are_enforced(self):
        old, new = changed()
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as d:
            paths = [Path(d) / (label + '.json') for label in ('old', 'new', 'scope')]
            for path, record in zip(paths, (old, new, scope())): path.write_text(json.dumps(record))
            pin = sha256(paths[2].read_bytes()).hexdigest()
            self.assertEqual(inspect(*paths, pin)['status'], 'pass')
            paths[2].write_text(json.dumps({'version': 'impact-scope-1.0', 'checks': {}}))
            self.assertEqual(inspect(*paths, pin)['status'], 'error')
            paths[0].write_text('{"version":1,"version":2}')
            self.assertEqual(inspect(*paths, pin)['status'], 'error')

    def test_cli_requires_independent_scope_and_exits_nonzero_on_unknown(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as d:
            old, new = changed(); new['complete'] = False
            paths = [Path(d) / (label + '.json') for label in ('old', 'new', 'scope')]
            for path, record in zip(paths, (old, new, scope())): path.write_text(json.dumps(record))
            args = [sys.executable, str(ROOT / 'scripts/impact.py'), 'check', '--before', str(paths[0]), '--after', str(paths[1]), '--scope', str(paths[2])]
            p = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            p = subprocess.run(args + ['--scope-sha256', sha256(paths[2].read_bytes()).hexdigest(), '--json'], capture_output=True, text=True)
            self.assertEqual(p.returncode, 1); self.assertEqual(json.loads(p.stdout)['status'], 'unknown')


class AdapterTests(unittest.TestCase):
    def record(self):
        record = empty_record('Synthetic question', 'concept')
        for key in ('A', 'B'):
            record['elements'][key] = {'kind': 'element', 'native_name': 'Demo::' + key,
                'label': key, 'description': 'Synthetic', 'basis': None, 'status': 'proposed'}
        record['relations']['R'] = {'kind': 'supports', 'from': 'A', 'to': 'B', 'basis': None, 'label': ''}
        return record

    def test_unmapped_relation_direction_is_explicitly_incomplete(self):
        s = snapshot_workflow(self.record(), {'id': 'v1', 'sha256': digest('m')}, complete=True)
        self.assertTrue(s['unresolved']); self.assertEqual(s['nodes']['A']['native_name'], 'Demo::A')
        self.assertEqual(analyze(s, s, scope())['status'], 'unknown')

    def test_caller_declared_relation_direction_controls_propagation(self):
        record = self.record()
        old = snapshot_workflow(record, {'id': 'v1', 'sha256': digest('m')},
            complete=True, relation_directions={'supports': 'to_depends_on_from'})
        record['elements']['A']['description'] = 'Changed source premise'
        new = snapshot_workflow(record, {'id': 'v2', 'sha256': digest('n')},
            complete=True, relation_directions={'supports': 'to_depends_on_from'})
        r = analyze(old, new, {'version': 'impact-scope-1.0', 'checks': {'BCheck': {'targets': ['B'], 'global': False}}})
        self.assertEqual(r['status'], 'pass'); self.assertIn('BCheck', r['selected_checks'])
        self.assertEqual(r['impacted']['B']['path'][0]['id'], 'relation:R')

    def test_malformed_falsey_relation_directions_are_rejected(self):
        for directions in ([], False, '', 0):
            with self.subTest(directions=directions):
                self.assertRaises(Invalid, snapshot_workflow, self.record(),
                    {'id': 'v1', 'sha256': digest('m')}, relation_directions=directions)

    def test_workflow_context_is_hashed(self):
        record = self.record(); old = snapshot_workflow(record, {'id': 'v1', 'sha256': digest('m')})
        record['question']['text'] = 'Changed question'
        new = snapshot_workflow(record, {'id': 'v2', 'sha256': digest('n')})
        self.assertNotEqual(old['nodes']['workflow:context']['sha256'], new['nodes']['workflow:context']['sha256'])

    @unittest.skipUnless(JAR.is_file(), 'Pinned native parser is unavailable')
    def test_real_native_type_edit_changes_impact_snapshot_without_documentary_edit(self):
        record = self.record(); record['relations'] = {}
        record['workflows']['concept']['focus'] = ['A']
        base = 'package Demo { part def First; part def Second; part A : First; part B : Second; }'
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as d:
            before = Path(d) / 'before.sysml'; after = Path(d) / 'after.sysml'
            before.write_text(draft_model(record, 'Metadata', base))
            after.write_text(draft_model(record, 'Metadata', base.replace('A : First', 'A : Second')))
            old = snapshot_native([before], 'v1'); new = snapshot_native([after], 'v2')
            self.assertNotEqual(old['nodes']['A']['sha256'], new['nodes']['A']['sha256'])
            self.assertEqual(old['nodes']['B']['sha256'], new['nodes']['B']['sha256'])
            r = analyze(old, new, {'version': 'impact-scope-1.0', 'checks': {'BCheck': {'targets': ['B'], 'global': False}}})
            self.assertEqual(r['status'], 'unknown'); self.assertIn('A', r['changed']['modified'])
            self.assertIn('BCheck', r['selected_checks'])

    def test_native_adapter_uses_binding_facts_and_rejects_failed_capture(self):
        native = {'native_status': 'pass', 'input_stability': 'pass', 'record': self.record(),
                  'model_sha256': digest('model'), 'native_inventory': {},
                  'bindings': {'A': {'type': 'First'}, 'B': {'type': 'Second'}}}
        with patch('verifier.workflow.inspect_workflow', return_value=native):
            old = snapshot_native(['model.sysml'], 'v1')
            native['bindings']['A']['type'] = 'Changed'
            new = snapshot_native(['model.sysml'], 'v2')
            self.assertNotEqual(old['nodes']['A']['sha256'], new['nodes']['A']['sha256'])
            self.assertIn('native:bundle', old['nodes'])
            self.assertFalse(old['complete']); self.assertTrue(old['unresolved'])
            native['input_stability'] = 'error'
            self.assertRaises(Invalid, snapshot_native, ['model.sysml'], 'v3')


if __name__ == '__main__': unittest.main()
