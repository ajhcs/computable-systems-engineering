"""Bounded function graph correspondence; synthetic domains and exceptions."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.core import digest
from verifier.function_flow import analyze, VERSION


def fixture(domain='library-return'):
    return json.loads((ROOT / 'examples/function-flow' / (domain + '.json')).read_text())


def evaluate(change=lambda r: None, domain='library-return', rebind=True):
    record = fixture(domain)
    change(record)
    if rebind:
        record['finite_model_sha256'] = digest(record['finite_model'])
    return analyze(record)


class FunctionFlowControls(unittest.TestCase):
    def test_multiple_domains_reuse_the_same_explicit_contract_and_engine(self):
        for domain in ('library-return', 'water-treatment', 'order-fulfillment'):
            result = analyze(fixture(domain))
            self.assertEqual(result['status'], 'pass', result)
            self.assertEqual(result['completed_obligations'], result['expected_obligations'])
            self.assertEqual(result['finite_analysis']['status'], 'pass')
            self.assertEqual(result['native_sysml_execution'], 'unsupported')
            self.assertEqual(result['transformation_correctness'], 'not_evaluated')
            self.assertIn('Handle', result['topology']['nodes'])

    def test_repeat_reports_are_deterministic_and_model_linked(self):
        record = fixture()
        self.assertEqual(analyze(record), analyze(deepcopy(record)))
        self.assertEqual(analyze(record)['dependencies']['finite_model_sha256'], digest(record['finite_model']))
        def stale(r): r['finite_model']['scenarios']['Routine']['initial_data'] = []
        result = evaluate(stale, rebind=False)
        self.assertEqual(result['status'], 'fail')
        self.assertNotIn('finite_analysis', result)
        self.assertEqual(result['obligations']['scenarios'], 'not_run')

    def test_performers_and_accountability_have_separate_selected_policies(self):
        self.assertEqual(len(fixture()['functions']['Prepare']['performers']), 2)
        def multiple(r): r['functions']['Prepare']['accountable'] = ['Clerk', 'System']
        self.assertEqual(evaluate(multiple)['status'], 'fail')
        def allowed(r):
            multiple(r); r['policy']['accountable'] = 'at_least_one'
        self.assertEqual(evaluate(allowed)['status'], 'pass')
        def not_selected(r):
            r['policy']['accountable'] = 'not_selected'
            r['policy']['performers_required'] = False
            r['functions']['Prepare'].update(accountable=[], performers=[])
        self.assertEqual(evaluate(not_selected)['status'], 'pass')
        for field in ('accountable', 'performers'):
            self.assertEqual(evaluate(lambda r: r['functions']['Prepare'].update({field: []}))['status'], 'unknown')
            self.assertEqual(evaluate(lambda r: r['functions']['Prepare'].update({field: ['Missing']}))['status'], 'fail')

    def test_unknown_transformation_is_not_executed_or_completed(self):
        self.assertEqual(evaluate(lambda r: r['functions']['Prepare'].update(transformation=None))['status'], 'unknown')
        # Arbitrary text remains text and cannot run as Python.
        result = evaluate(lambda r: r['functions']['Prepare'].update(transformation="raise RuntimeError('must remain documentary')"))
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['transformation_correctness'], 'not_evaluated')

    def test_port_types_units_identity_and_direction_are_checked(self):
        for field, value in [('type', 'int'), ('unit', 'minutes'), ('data', 'Missing')]:
            result = evaluate(lambda r: r['functions']['Complete']['inputs']['ready'].update({field: value}))
            self.assertEqual(result['status'], 'fail', result)
        result = evaluate(lambda r: r['functions']['Complete']['inputs']['ready'].update(type='continuous'))
        self.assertTrue(any(f['rule'] == 'port_type' and f['status'] == 'unsupported' for f in result['findings']))
        self.assertEqual(evaluate(lambda r: r['flows']['Handover'].update(output='request'))['status'], 'fail')

    def test_scenario_function_io_and_guard_must_correspond_exactly(self):
        self.assertEqual(evaluate(lambda r: r['finite_model']['scenarios']['Routine']['steps']['SComplete'].update(consumes=[]))['status'], 'fail')
        self.assertEqual(evaluate(lambda r: r['functions']['Complete'].update(enabling=None))['status'], 'fail')
        self.assertEqual(evaluate(lambda r: r['step_bindings']['Routine'].pop('SComplete'))['status'], 'fail')
        self.assertEqual(evaluate(lambda r: r['step_bindings'].update(Absent={}))['status'], 'fail')

    def test_topology_never_substitutes_for_executable_data_availability(self):
        result = evaluate(lambda r: r['finite_model']['scenarios']['Routine'].update(initial_data=[]))
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['topology']['edges'], 1)
        self.assertTrue(any(f['rule'] == 'finite.step-reachability' and 'data unavailable' in f['detail'] for f in result['findings']))

    def test_disabled_guard_and_reachable_dead_end_keep_engine_counterexample(self):
        def disabled(r):
            r['finite_model']['scenarios']['Routine']['steps']['SPrepare']['effects'] = {'Enabled': False}
        result = evaluate(disabled)
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any(f['rule'] == 'finite.dead-end' and f['evidence']['path'] == ['SPrepare'] for f in result['findings']))

    def test_a_producer_on_one_branch_does_not_supply_data_on_another(self):
        def bypass(r):
            r['functions']['Bypass'] = deepcopy(r['functions']['Prepare'])
            r['functions']['Bypass']['outputs'] = {}
            scenario = r['finite_model']['scenarios']['Routine']
            scenario['steps']['SBypass'] = deepcopy(scenario['steps']['SPrepare'])
            scenario['steps']['SBypass']['produces'] = []
            r['step_bindings']['Routine']['SBypass'] = 'Bypass'
            decomp = r['decompositions']['Breakdown']
            decomp['children'].append('Bypass')
            decomp['inputs'].append({'parent_port': 'request', 'child': 'Bypass', 'child_port': 'request'})
        result = evaluate(bypass)
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any(f['rule'] == 'finite.dead-end' and f['evidence']['path'] == ['SBypass'] for f in result['findings']))

    def test_external_inputs_and_terminal_outputs_need_no_invented_producer_consumer(self):
        result = analyze(fixture())
        self.assertEqual(result['status'], 'pass')
        self.assertNotIn('request', [f['output'] for f in fixture()['flows'].values()])
        self.assertNotIn('result', [f['input'] for f in fixture()['flows'].values()])

    def test_feedback_loop_and_multiple_steps_per_function_are_legitimate(self):
        def loop(r):
            r['functions']['Complete']['outputs']['retry'] = dict(r['functions']['Prepare']['inputs']['request'])
            r['flows']['Feedback'] = {'from': 'Complete', 'output': 'retry', 'to': 'Prepare', 'input': 'request'}
            r['finite_model']['scenarios']['Routine']['steps']['SComplete']['produces'].append('Request')
            r['finite_model']['scenarios']['Routine']['terminal'] = {}
            r['finite_model']['scenarios']['Routine']['completion'] = []
            r['finite_model']['scenarios']['Routine']['require_completion'] = False
            r['finite_model']['scenarios']['Routine']['steps']['SComplete']['to'] = 'start'
        self.assertEqual(evaluate(loop)['status'], 'pass')

    def test_explicit_external_wait_and_mutually_exclusive_modes_reuse_finite_semantics(self):
        def wait(r):
            r['finite_model']['properties']['Released'] = {'type': 'bool', 'owner': 'input'}
            guard = {'ref': 'Released', 'op': '==', 'value': True}
            r['functions']['Prepare']['enabling'] = guard
            scenario = r['finite_model']['scenarios']['Routine']
            scenario['external_at'] = ['start']
            scenario['steps']['SPrepare']['guard'] = deepcopy(guard)
        self.assertEqual(evaluate(wait)['status'], 'pass')
        def modes(r):
            wait(r)
            scenario = r['finite_model']['scenarios']['Routine']
            scenario['external_at'] = []
            r['functions']['Alternate'] = deepcopy(r['functions']['Prepare'])
            r['functions']['Alternate']['enabling']['value'] = False
            scenario['steps']['SAlternate'] = deepcopy(scenario['steps']['SPrepare'])
            scenario['steps']['SAlternate']['guard']['value'] = False
            r['step_bindings']['Routine']['SAlternate'] = 'Alternate'
            r['flows']['AlternateHandover'] = {'from': 'Alternate', 'output': 'ready', 'to': 'Complete', 'input': 'ready'}
            decomp = r['decompositions']['Breakdown']
            decomp['children'].append('Alternate')
            decomp['inputs'].append({'parent_port': 'request', 'child': 'Alternate', 'child_port': 'request'})
        self.assertEqual(evaluate(modes)['status'], 'pass')

    def test_parent_and_child_boundary_coverage_and_direction_are_explicit(self):
        for direction in ('inputs', 'outputs'):
            def missing(r): r['decompositions']['Breakdown'][direction] = []
            result = evaluate(missing)
            self.assertEqual(result['status'], 'fail')
            self.assertTrue(any(f['rule'] == 'parent_boundary_missing' for f in result['findings']))
        def wrong_child(r): r['decompositions']['Breakdown']['inputs'][0]['child'] = 'Handle'
        self.assertEqual(evaluate(wrong_child)['status'], 'fail')
        def wrong_port(r): r['decompositions']['Breakdown']['outputs'][0]['child_port'] = 'ready'
        self.assertEqual(evaluate(wrong_port)['status'], 'fail')
        def orphan(r): r['flows'] = {}
        self.assertTrue(any(f['rule'] == 'child_boundary_missing' for f in evaluate(orphan)['findings']))

    def test_decomposition_cycles_are_not_confused_with_feedback_flows(self):
        def cyclic(r):
            r['decompositions']['Back'] = {'parent': 'Prepare', 'children': ['Handle'], 'inputs': [], 'outputs': []}
        result = evaluate(cyclic)
        self.assertEqual(result['status'], 'fail')
        finding = next(f for f in result['findings'] if f['rule'] == 'decomposition_cycle')
        self.assertEqual(finding['ids'], ['Handle', 'Prepare'])
        self.assertNotIn('Complete', finding['evidence']['cycle'])

    def test_repeated_function_use_and_source_sink_contracts(self):
        def repeat(r):
            scenario = r['finite_model']['scenarios']['Routine']
            scenario['steps']['SPrepareAgain'] = deepcopy(scenario['steps']['SPrepare'])
            scenario['steps']['SPrepareAgain'].update({'from': 'ready', 'to': 'again'})
            scenario['steps']['SComplete']['from'] = 'again'
            r['step_bindings']['Routine']['SPrepareAgain'] = 'Prepare'
        self.assertEqual(evaluate(repeat)['status'], 'pass')
        def source_sink(r):
            r['functions']['Prepare']['inputs'] = {}
            r['functions']['Complete']['outputs'] = {}
            r['functions']['Handle'].update(inputs={}, outputs={})
            r['decompositions']['Breakdown'].update(inputs=[], outputs=[])
            scenario = r['finite_model']['scenarios']['Routine']
            scenario['initial_data'] = []
            scenario['steps']['SPrepare']['consumes'] = []
            scenario['steps']['SComplete']['produces'] = []
        self.assertEqual(evaluate(source_sink)['status'], 'pass')

    def test_invalid_duplicate_boundary_maps_and_unexecuted_child(self):
        def duplicate(r):
            maps = r['decompositions']['Breakdown']['inputs']
            maps.append(deepcopy(maps[0]))
        self.assertEqual(evaluate(duplicate)['status'], 'error')
        def unexecuted(r):
            r['functions']['Spare'] = deepcopy(r['functions']['Prepare'])
            r['decompositions']['Breakdown']['children'].append('Spare')
        result = evaluate(unexecuted)
        self.assertTrue(any(f['rule'] == 'function_unexercised' and f['ids'] == ['Spare'] for f in result['findings']))
        def undefined(r): r['decompositions']['Breakdown']['children'].append('Absent')
        self.assertEqual(evaluate(undefined)['status'], 'fail')

    def test_finite_engine_limits_and_unsupported_semantics_cannot_pass(self):
        self.assertEqual(evaluate(lambda r: r['limits'].update(state_cap=1))['status'], 'unknown')
        def unsupported(r):
            r['functions']['Complete']['enabling']['op'] = 'approximately'
            r['finite_model']['scenarios']['Routine']['steps']['SComplete']['guard']['op'] = 'approximately'
        self.assertEqual(evaluate(unsupported)['status'], 'unsupported')
        def assignment_limit(r):
            r['finite_model']['properties']['Context'] = {'type': 'bool', 'owner': 'input'}
            r['limits']['assignment_cap'] = 1
        self.assertEqual(evaluate(assignment_limit)['status'], 'unknown')
        for limit in (0, True, 100001):
            self.assertEqual(evaluate(lambda r: r['limits'].update(state_cap=limit))['status'], 'error')

    def test_missing_scenarios_and_unexercised_leaf_stay_unknown(self):
        def absent(r): r['finite_model']['scenarios'] = {}; r['step_bindings'] = {}
        self.assertEqual(evaluate(absent)['status'], 'unknown')
        def spare(r): r['functions']['Spare'] = deepcopy(r['functions']['Prepare'])
        self.assertEqual(evaluate(spare)['status'], 'unknown')

    def test_malformed_types_duplicates_oversize_and_unknown_profile_refuse(self):
        for value in (None, [], 'text', {'version': VERSION}):
            self.assertEqual(analyze(value)['status'], 'error')
        self.assertEqual(evaluate(lambda r: r.update(version='future'))['status'], 'unsupported')
        for change in [lambda r: r['functions']['Prepare'].update(performers=['Clerk', 'Clerk']),
                       lambda r: r['functions']['Prepare'].update(inputs=[]),
                       lambda r: r['functions']['Prepare'].update(extra=True),
                       lambda r: r['finite_model'].update(data=[]),
                       lambda r: r['functions']['Prepare'].update(label='a' * 4097)]:
            result = evaluate(change)
            self.assertEqual(result['status'], 'error', result)
            self.assertNotEqual(result['obligations']['scenarios'], 'pass')


if __name__ == '__main__':
    unittest.main()
