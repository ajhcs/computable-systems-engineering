"""Native correspondence uses real parser facts and preserves finite failures."""
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
from verifier.core import digest
from verifier.function_native import inspect, _correspondence, schema
from verifier.sysml import check_sysml, JAR, CLASSES
from verifier.workflow import capture_model_inputs

EXAMPLE = ROOT/'examples/function-native'
FLOW = json.loads((EXAMPLE/'handoff-functions.json').read_text())
BINDING = json.loads((EXAMPLE/'handoff-bindings.json').read_text())
PARSER = JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file()


@unittest.skipUnless(PARSER, 'Pinned native parser is unavailable')
class NativeCorrespondence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = check_sysml(EXAMPLE/'handoff.sysml', syntax_only=True)
        cls.workflow_native = check_sysml(EXAMPLE/'handoff-workflow.sysml', syntax_only=True)
        assert cls.native['status'] == 'pass', cls.native
        assert cls.workflow_native['status'] == 'pass', cls.workflow_native

    def evaluate(self, change=lambda f, b, n: None):
        flow, binding, native = deepcopy(FLOW), deepcopy(BINDING), deepcopy(self.native)
        change(flow, binding, native)
        flow['finite_model_sha256'] = digest(flow['finite_model'])
        binding['function_flow_sha256'] = digest(flow)
        def parsed(paths, **kwargs):
            _, _, revision = capture_model_inputs(paths)
            native['model_sha256'] = revision
            return native
        with patch('verifier.function_native.check_sysml', side_effect=parsed):
            return inspect(flow, binding, EXAMPLE/'handoff.sysml')

    def cli(self, directory, *, source=None, flow=None, binding=None, launcher=False, extra=()):
        d = Path(directory)
        model = d/'case.sysml'; model.write_text((EXAMPLE/'handoff.sysml').read_text() if source is None else source)
        f = deepcopy(FLOW if flow is None else flow); b = deepcopy(BINDING if binding is None else binding)
        f['finite_model_sha256'] = digest(f['finite_model'])
        b['function_flow_sha256'] = digest(f); b['native_model_sha256'] = sha256(model.read_bytes()).hexdigest()
        fp = d/'functions.json'; fp.write_text(json.dumps(f)); bp = d/'binding.json'; bp.write_text(json.dumps(b))
        command = [sys.executable, '-B', str(ROOT/'skills/develop-system-concept/scripts/cse.py'), 'analyze'] if launcher else [sys.executable, '-B', str(ROOT/'scripts/analyze.py')]
        command += ['functional-graph', str(fp), '--native-model', str(model), '--native-bindings', str(bp), *extra]
        completed = subprocess.run(command, cwd=d, capture_output=True, text=True)
        return completed, json.loads(completed.stdout)

    def test_direct_native_identity_boolean_types_need_no_workflow_metadata(self):
        report = self.evaluate()
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(report['native_binding']['status'], 'pass')
        self.assertEqual(report['native_binding']['summary']['functions'], 3)
        self.assertEqual(report['native_binding']['summary']['steps'], 2)
        self.assertEqual(report['native_binding']['native_execution'], 'unsupported')
        self.assertNotIn('inventory', report['native_binding'])

    def test_real_cli_and_shared_launcher_accept_explicit_positive_mapping(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            completed, report = self.cli(d, launcher=True)
            self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
            self.assertEqual(report['status'], 'pass')
            self.assertEqual(len(report['native_binding']['mapping']), 12)

    def test_real_cli_deleted_renamed_and_wrong_native_category_are_rejected(self):
        original = (EXAMPLE/'handoff.sysml').read_text()
        variants = [original.replace('    action def Prepare;\n', ''),
                    original.replace('action def Prepare;', 'action def Renamed;'),
                    original.replace('action def Prepare;', 'part Prepare : Person;')]
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            for source in variants:
                completed, report = self.cli(d, source=source)
                self.assertEqual(completed.returncode, 1, completed.stdout+completed.stderr)
                self.assertEqual(report['native_binding']['parser_status'], 'pass')
                self.assertTrue(any(f['rule'] == 'native_target' for f in report['findings']))
                self.assertEqual(report['finite_execution'], 'not_run')

    def test_actual_stale_native_revision_blocks_before_parser_or_finite_execution(self):
        binding = deepcopy(BINDING); binding['native_model_sha256'] = '0'*64
        with patch('verifier.function_native.check_sysml') as parser:
            result = inspect(FLOW, binding, EXAMPLE/'handoff.sysml')
        parser.assert_not_called()
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['findings'][0]['rule'], 'native_source_revision')
        self.assertEqual(result['finite_execution'], 'not_run')

    def test_real_cli_explicit_model_bundle_retains_existing_bundle_identity(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            extra = Path(d)/'extra.sysml'; extra.write_text('package NativeExtra { part def Unused; }\n')
            models = [EXAMPLE/'handoff.sysml', extra]
            _, files, model_hash = capture_model_inputs(models)
            binding = deepcopy(BINDING); binding['native_model_sha256'] = model_hash
            bp = Path(d)/'binding.json'; bp.write_text(json.dumps(binding))
            command = [sys.executable, str(ROOT/'scripts/analyze.py'), 'functional-graph', str(EXAMPLE/'handoff-functions.json'),
                       '--native-bindings', str(bp), '--native-model', str(models[0]), '--native-model', str(extra)]
            completed = subprocess.run(command, capture_output=True, text=True)
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
            self.assertEqual(report['native_binding']['model_sha256'], model_hash)
            self.assertEqual(report['native_binding']['model_files'], files)
            # The same source cannot count as two independent bundle members.
            command += ['--native-model', str(extra)]
            completed = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(json.loads(completed.stdout)['status'], 'error')

    def test_actual_cli_stale_source_and_incomplete_mapping_are_non_successes(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            model = Path(d)/'case.sysml'; model.write_text((EXAMPLE/'handoff.sysml').read_text()+'\n// revised\n')
            bp = Path(d)/'binding.json'; bp.write_text(json.dumps(BINDING))
            command = [sys.executable, str(ROOT/'scripts/analyze.py'), 'functional-graph', str(EXAMPLE/'handoff-functions.json'), '--native-model', str(model), '--native-bindings', str(bp)]
            completed = subprocess.run(command, capture_output=True, text=True)
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(report['findings'][0]['rule'], 'native_source_revision')
            binding = deepcopy(BINDING); del binding['steps']['Routine']['SComplete']
            completed, report = self.cli(d, binding=binding)
            self.assertEqual(completed.returncode, 1)
            self.assertTrue(any(f['rule'] == 'native_mapping_missing' for f in report['findings']))

    def test_complete_scope_is_checked_for_every_mapped_finite_group(self):
        for group, key in [('functions', 'Prepare'), ('parties', 'Clerk'), ('scenarios', 'Routine'),
                           ('steps', 'Routine'), ('data', 'Request'), ('properties', 'Enabled')]:
            def missing(f, b, n): b[group].pop(key)
            result = self.evaluate(missing)
            self.assertEqual(result['status'], 'fail', (group, result))
            self.assertEqual(result['finite_execution'], 'not_run')
        result = self.evaluate(lambda f, b, n: b['functions'].update(Absent=deepcopy(b['functions']['Prepare'])))
        self.assertEqual(result['status'], 'fail')

    def test_mapping_changed_function_flow_record_must_be_reconciled(self):
        flow = deepcopy(FLOW); flow['functions']['Prepare']['transformation'] = 'Changed proposal.'
        with patch('verifier.function_native.check_sysml') as parser:
            result = inspect(flow, BINDING, EXAMPLE/'handoff.sysml')
        parser.assert_not_called()
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['findings'][0]['rule'], 'native_finite_revision')

    def test_finite_failure_is_preserved_with_related_native_identity(self):
        result = self.evaluate(lambda f, b, n: f['finite_model']['scenarios']['Routine'].update(initial_data=[]))
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['native_binding']['status'], 'pass')
        dead_end = next(f for f in result['findings'] if f['rule'] == 'finite.dead-end')
        self.assertEqual(dead_end['evidence']['path'], [])
        self.assertIn('NativeHandoff::Routine', dead_end['related_native_ids'])
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            flow = deepcopy(FLOW); flow['finite_model']['scenarios']['Routine']['initial_data'] = []
            completed, report = self.cli(d, flow=flow)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(report['native_binding']['status'], 'pass')
            self.assertTrue(any(f['rule'] == 'finite.dead-end' for f in report['findings']))

    def test_native_property_direction_and_unbound_attribute_fail(self):
        result = self.evaluate(lambda f, b, n: n['inventory']['attributes'][-1].update(direction='in'))
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any(f['rule'] == 'native_property_direction' for f in result['findings']))
        result = self.evaluate(lambda f, b, n: b['data']['Ready'].update(attribute='NativeHandoff::DeskData::missing'))
        self.assertEqual(result['status'], 'fail')

    def test_quantity_specialization_multiplicity_and_native_values_are_unsupported(self):
        changes = [lambda f, b, n: n['inventory']['attributes'][0].update(type='ScalarValues::Integer'),
                   lambda f, b, n: n['inventory']['attributes'][0].update(has_native_value=True),
                   lambda f, b, n: n['inventory']['attributes'][0].update(is_variation=True),
                   lambda f, b, n: n['inventory']['attributes'][0].update(is_variant=True),
                   lambda f, b, n: n['inventory']['attributes'][0].pop('is_variation'),
                   lambda f, b, n: n['inventory']['attributes'][0].pop('multiplicity'),
                   lambda f, b, n: n['inventory']['attributes'][0].update(types=[]),
                   lambda f, b, n: n['inventory']['attributes'][0].update(types=['ScalarValues::String']),
                   lambda f, b, n: n['inventory']['part_definitions'][-1].update(has_specialization=True),
                   lambda f, b, n: n['inventory']['part_definitions'][-1].update(is_variation=True),
                   lambda f, b, n: n['inventory']['parts'][-1]['multiplicity'].update(upper=2)]
        for change in changes:
            result = self.evaluate(change)
            self.assertEqual(result['status'], 'unsupported', result)
            self.assertEqual(result['finite_execution'], 'not_run')

    def test_actual_native_boolean_array_and_optional_attribute_are_not_scalar_data(self):
        original = (EXAMPLE/'handoff.sysml').read_text()
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            for multiplicity in ('[2]', '[0..1]'):
                source = original.replace('ready : Boolean;', 'ready : Boolean'+multiplicity+';')
                completed, report = self.cli(d, source=source)
                self.assertEqual(report['native_binding']['parser_status'], 'pass', report)
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(report['status'], 'unsupported')
                self.assertTrue(any(f['rule'] == 'native_attribute_semantics' for f in report['findings']))
                self.assertEqual(report['finite_execution'], 'not_run')
            source = original.replace('ready : Boolean;', 'ready : Boolean[1];')
            completed, report = self.cli(d, source=source)
            self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
            source = original.replace('part def DeskData', 'variation part def DeskData')
            completed, report = self.cli(d, source=source)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(report['finite_execution'], 'not_run')

    def test_distinct_finite_identities_cannot_silently_alias_one_native_identity(self):
        result = self.evaluate(lambda f, b, n: b['functions'].update(Complete=deepcopy(b['functions']['Prepare'])))
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any(f['rule'] == 'native_mapping_alias' for f in result['findings']))

    def test_function_valued_step_mapping_must_match_its_explicit_finite_function(self):
        result = self.evaluate(lambda f, b, n: b['steps']['Routine'].update(SPrepare=deepcopy(b['functions']['Prepare'])))
        self.assertEqual(result['status'], 'pass', result)
        result = self.evaluate(lambda f, b, n: b['steps']['Routine'].update(SPrepare=deepcopy(b['functions']['Complete'])))
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any(f['rule'] == 'native_step_function' for f in result['findings']))
        self.assertEqual(result['finite_execution'], 'not_run')

    def test_optional_existing_workflow_ids_and_selected_relations_use_real_inventory(self):
        binding = json.loads((EXAMPLE/'handoff-workflow-bindings.json').read_text())
        findings, resolved = _correspondence(FLOW, binding, self.workflow_native['inventory'])
        self.assertEqual(findings, [])
        wrong = deepcopy(binding); wrong['functions']['Prepare']['element'] = 'R_SYSTEM'
        self.assertTrue(any(f['rule'] == 'native_workflow_identity' for f in _correspondence(FLOW, wrong, self.workflow_native['inventory'])[0]))
        wrong = deepcopy(binding); wrong['relations']['L_ORDER']['to'] = 'T_PREPARE'
        self.assertTrue(any(f['rule'] == 'native_relation_changed' for f in _correspondence(FLOW, wrong, self.workflow_native['inventory'])[0]))
        wrong = deepcopy(binding); wrong['relations']['L_ORDER']['kind'] = 'arbitrary_native_execution'
        self.assertTrue(any(f['status'] == 'unsupported' for f in _correspondence(FLOW, wrong, self.workflow_native['inventory'])[0]))
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            completed, report = self.cli(d, source=(EXAMPLE/'handoff-workflow.sysml').read_text(), binding=binding)
            self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
            self.assertEqual(report['native_binding']['summary']['relations'], 4)

    def test_selected_decomposition_can_retain_a_legitimate_empty_documentary_label(self):
        binding = json.loads((EXAMPLE/'handoff-workflow-bindings.json').read_text())
        native = deepcopy(self.workflow_native)
        document = next(d for d in native['inventory']['documents'] if d.get('name') == 'cseWorkflow')
        marker, payload = document['body'].strip().split('\n', 1)
        record = json.loads(payload)
        record['relations']['L_PARENT_PREPARE']['label'] = ''
        document['body'] = marker + '\n' + json.dumps(record)
        binding['relations']['L_PARENT_PREPARE']['label'] = ''
        schema(binding)
        self.assertEqual(_correspondence(FLOW, binding, native['inventory'])[0], [])

    def test_native_input_drift_or_mismatched_parser_receipt_cannot_pass(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            path = Path(d)/'case.sysml'; path.write_bytes((EXAMPLE/'handoff.sysml').read_bytes())
            def parsed(paths, **kwargs):
                _, _, revision = capture_model_inputs(paths)
                native = deepcopy(self.native); native['model_sha256'] = revision
                path.write_text(path.read_text()+'\n// changed\n')
                return native
            with patch('verifier.function_native.check_sysml', side_effect=parsed):
                result = inspect(FLOW, BINDING, path)
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['finite_execution'], 'not_run')
        with patch('verifier.function_native.check_sysml', return_value=self.native | {'model_sha256': '0'*64}):
            result = inspect(FLOW, BINDING, EXAMPLE/'handoff.sysml')
        self.assertEqual(result['status'], 'error')

    def test_malformed_binding_unsupported_profile_and_partial_cli_options_refuse(self):
        for binding in (None, [], {}, BINDING | {'functions': []}, BINDING | {'extra': True}):
            result = inspect(FLOW, binding, EXAMPLE/'handoff.sysml')
            self.assertNotEqual(result['status'], 'pass')
        self.assertEqual(inspect(FLOW, BINDING | {'version': 'future'}, EXAMPLE/'handoff.sysml')['status'], 'unsupported')
        completed = subprocess.run([sys.executable, str(ROOT/'scripts/analyze.py'), 'functional-graph', str(EXAMPLE/'handoff-functions.json'), '--native-model', str(EXAMPLE/'handoff.sysml')], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)['status'], 'error')


if __name__ == '__main__':
    (ROOT/'.tmp').mkdir(exist_ok=True)
    unittest.main()
