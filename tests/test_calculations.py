"""Behavioral controls for exact arithmetic, retained scope and optional SymPy."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.calculations import analyze, LIMITS


def number(value, unit=None):
    return {'number': value, 'unit': unit or {}}


def ref(key):
    return {'ref': key}


def op(name, *args, **extra):
    return {'op': name, 'args': list(args), **extra}


def record(lhs, rhs, variables=None, kind='forall', relation='eq'):
    return {'version': 'calculations-1.0', 'id': 'SyntheticAnalysis', 'revision': 'synthetic-1',
            'variables': variables or {}, 'assumptions': {},
            'checks': {'C': {'kind': kind, 'relation': relation, 'lhs': lhs, 'rhs': rhs, 'assumptions': []}}}


def variable(values, unit=None, domain='rational'):
    return {'domain': domain, 'values': values, 'unit': unit or {}, 'basis': 'Synthetic authored input'}


class ExactArithmetic(unittest.TestCase):
    def test_rational_and_decimal_are_exact(self):
        report = analyze(record(op('add', number('0.1'), number('1/5')), number('3/10')))
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['checks']['C']['example']['lhs'], '3/10')

    def test_energy_budget_preserves_units_and_returns_counterexample(self):
        r = record(op('mul', ref('power'), ref('duration')), number('9', {'Wh': 1}),
            {'power': variable(['2', '4'], {'Wh': 1, 'hour': -1}),
             'duration': variable(['2', '3'], {'hour': 1})}, relation='le')
        report = analyze(r)
        self.assertEqual(report['status'], 'fail')
        check = report['checks']['C']
        self.assertEqual(check['completed_valuations'], 4)
        self.assertEqual(check['counterexample']['lhs'], '12')
        self.assertEqual(check['counterexample']['assignment'], {'duration': '3', 'power': '4'})
        self.assertEqual(check['counterexample']['unit'], {'Wh': 1})

    def test_healthcare_mean_arithmetic_has_no_queueing_or_staffing_claim(self):
        r = record(op('div', ref('patients'), ref('hours')), number('3/2', {'patient': 1, 'hour': -1}),
                   {'patients': variable(['3'], {'patient': 1}), 'hours': variable(['2'], {'hour': 1})})
        report = analyze(r)
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['applicability_validation'], 'not_evaluated')
        self.assertEqual(report['acceptance'], 'not_evaluated')

    def test_equation_finds_a_witness_only_in_explicit_finite_domain(self):
        r = record(op('pow', ref('speed'), exponent=2), number('4'),
                   {'speed': variable(['-2', '0', '2'])}, kind='exists')
        report = analyze(r)
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['checks']['C']['satisfying_valuations'], 2)
        self.assertEqual(report['checks']['C']['witness']['assignment'], {'speed': '-2'})
        self.assertEqual(report['checks']['C']['completed_valuations'], 3)
        self.assertEqual(report['checks']['C']['solution_set_scope'], 'only_the_explicit_finite_domain')

    def test_empty_solution_is_failure_only_after_complete_enumeration(self):
        r = record(ref('x'), number('3'), {'x': variable(['1', '2'])}, kind='exists')
        report = analyze(r)
        self.assertEqual(report['status'], 'fail')
        self.assertIsNone(report['checks']['C']['witness'])
        self.assertEqual(report['checks']['C']['satisfying_valuations'], 0)
        r['variables']['x']['values'] = []
        self.assertEqual(analyze(r)['status'], 'unknown')

    def test_all_relations_negation_subtraction_and_negative_powers(self):
        cases = [('eq', '2', '2', 'pass'), ('ne', '2', '2', 'fail'),
                 ('lt', '1', '2', 'pass'), ('le', '2', '2', 'pass'),
                 ('gt', '2', '1', 'pass'), ('ge', '1', '2', 'fail')]
        for relation, lhs, rhs, expected in cases:
            self.assertEqual(analyze(record(number(lhs), number(rhs), relation=relation))['status'], expected)
        lhs = op('neg', op('sub', op('pow', number('2'), exponent=-2), number('1')))
        self.assertEqual(analyze(record(lhs, number('3/4')))['status'], 'pass')

    def test_unit_mismatches_and_unrequested_conversion_fail(self):
        for lhs, rhs in [(number('1', {'m': 1}), number('100', {'cm': 1})),
                         (op('add', number('1', {'second': 1}), number('1', {'hour': 1})), number('2'))]:
            self.assertEqual(analyze(record(lhs, rhs))['status'], 'fail')

    def test_original_equation_pole_is_retained_even_when_other_witness_exists(self):
        r = record(op('div', ref('x'), ref('x')), number('1'),
                   {'x': variable(['1', '0'])}, kind='exists')
        report = analyze(r)
        self.assertEqual(report['status'], 'unknown')
        self.assertEqual(report['checks']['C']['completed_valuations'], 1)
        self.assertEqual(report['checks']['C']['rule'], 'calculation_undefined')

    def test_zero_negative_power_and_zero_to_zero_are_unknown(self):
        for exponent in (-1, 0):
            self.assertEqual(analyze(record(op('pow', number('0'), exponent=exponent), number('1')))['status'], 'unknown')

    def test_required_scope_deletion_fails_and_does_not_hide_other_failures(self):
        report = analyze(record(number('1'), number('1')), ['C', 'ExpectedOtherCheck'])
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(report['expected_checks'], ['C', 'ExpectedOtherCheck'])
        self.assertEqual(report['findings'][0]['ids'], ['ExpectedOtherCheck'])

    def test_unknown_basis_and_assumptions_are_not_success(self):
        r = record(ref('x'), number('1'), {'x': variable(['1'])})
        r['variables']['x']['basis'] = None
        self.assertEqual(analyze(r)['status'], 'unknown')
        r['variables']['x']['basis'] = 'Declared synthetic input'
        r['assumptions']['A'] = {'text': 'Input applies within the selected boundary', 'basis': None}
        r['checks']['C']['assumptions'] = ['A']
        self.assertEqual(analyze(r)['status'], 'unknown')
        r['assumptions']['A']['basis'] = 'Explicit synthetic assumption, not observed evidence'
        report = analyze(r)
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['assumptions'], r['assumptions'])

    def test_unavailable_semantics_and_unbound_symbols_are_explicit(self):
        self.assertEqual(analyze(record({'op': 'sin', 'args': [number('0')]}, number('0')))['status'], 'unsupported')
        self.assertEqual(analyze(record(ref('missing'), number('0')))['status'], 'fail')
        r = record(ref('x'), number('1'), {'x': variable(None)})
        self.assertEqual(analyze(r)['status'], 'unknown')

    def test_limits_and_rational_bit_cap_prevent_success(self):
        r = record(op('mul', ref('x'), ref('y')), number('0'),
                   {'x': variable([str(x) for x in range(64)]), 'y': variable([str(x) for x in range(64)]),
                    'z': variable(['1', '2'])})
        r['checks']['C']['lhs'] = op('mul', r['checks']['C']['lhs'], ref('z'))
        self.assertEqual(analyze(r)['status'], 'unknown')
        expr = number('9'*80)
        for _ in range(3):
            expr = op('pow', expr, exponent=8)
        self.assertEqual(analyze(record(expr, number('1')))['status'], 'unknown')
        self.assertEqual(analyze(record(op('pow', number('2'), exponent=9), number('1')))['status'], 'unsupported')

    def test_float_code_injection_unknown_fields_and_duplicate_values_are_rejected(self):
        for bad in (0.1, '__import__("os").system("touch /bad")', 'NaN', '1e999999'):
            self.assertEqual(analyze(record(number(bad), number('0')))['status'], 'error')
        r = record(number('1'), number('1')); r['code'] = 'anything'
        self.assertEqual(analyze(r)['status'], 'error')
        r = record(ref('x'), number('1'), {'x': variable(['1', '1.0'])})
        self.assertEqual(analyze(r)['status'], 'error')

    def test_malformed_nested_inputs_never_escape_or_pass(self):
        for value in (None, [], {}, {'version': 'old'}):
            self.assertNotEqual(analyze(value)['status'], 'pass')
        r = record(number('1'), number('1')); r['checks']['C']['assumptions'] = [[]]
        self.assertEqual(analyze(r)['status'], 'error')

    def test_identity_optional_dependency_failure_and_timeout_cannot_pass(self):
        r = polynomial_record()
        with patch('verifier.calculations.subprocess.run', side_effect=subprocess.TimeoutExpired('worker', 5)):
            self.assertEqual(analyze(r)['status'], 'unknown')
        child = subprocess.CompletedProcess([], 0, json.dumps({'status': 'unsupported', 'rule': 'calculation_dependency', 'detail': 'SymPy unavailable'}), '')
        with patch('verifier.calculations.subprocess.run', return_value=child):
            self.assertEqual(analyze(r)['status'], 'unsupported')
        child = subprocess.CompletedProcess([], 1, '', 'worker failed')
        with patch('verifier.calculations.subprocess.run', return_value=child):
            self.assertEqual(analyze(r)['status'], 'error')

    def test_malformed_or_incomplete_worker_outcomes_cannot_pass(self):
        outputs = ['not JSON', '[]', 'null', '1', 'true', '"pass"',
                   '{"status":true}', '{"status":"bogus","difference":"0"}',
                   '{"status":"pass"}', '{"status":"pass","status":"fail"}',
                   '{"status":"unknown","rule":[],"detail":"Missing calculation"}']
        for output in outputs:
            child = subprocess.CompletedProcess([], 0, output, '')
            with self.subTest(output=output), patch('verifier.calculations.subprocess.run', return_value=child):
                report = analyze(polynomial_record())
                self.assertEqual(report['status'], 'error', report)
                self.assertEqual(report['checks']['C']['status'], 'error')
                self.assertEqual(report['completed_checks'], [])
        child = subprocess.CompletedProcess([], 0, '{"status":"not_run","difference":"unavailable"}', '')
        r = polynomial_record()
        r['checks']['A'] = record(number('1'), number('1'))['checks']['C']
        with patch('verifier.calculations.subprocess.run', return_value=child):
            report = analyze(r, ['A', 'C'])
        self.assertEqual(report['status'], 'unknown')
        self.assertEqual(report['checks']['A']['status'], 'pass')
        self.assertEqual(report['checks']['C']['status'], 'unknown')
        self.assertEqual(report['completed_checks'], ['A'])

    def test_worker_identity_payload_must_be_complete_and_consistent(self):
        payload = {'status': 'pass', 'backend': 'sympy', 'backend_version': 'synthetic-test',
                   'claim_scope': 'polynomial_identity_over_declared_rational_or_real_domains',
                   'coefficient_count': 1, 'difference': '0'}
        for change in (lambda p: p.pop('backend_version'),
                       lambda p: p.update(backend='other'),
                       lambda p: p.update(backend_version=[]),
                       lambda p: p.update(coefficient_count=True),
                       lambda p: p.update(coefficient_count=LIMITS['symbolic_terms']+1),
                       lambda p: p.update(difference='x'),
                       lambda p: p.update(status='fail'),
                       lambda p: p.update(claim_scope='some_unchecked_claim')):
            malformed = deepcopy(payload); change(malformed)
            child = subprocess.CompletedProcess([], 0, json.dumps(malformed), '')
            with patch('verifier.calculations.subprocess.run', return_value=child):
                self.assertEqual(analyze(polynomial_record())['status'], 'error')
        # A complete false identity remains a mathematical failure, not a worker error.
        payload.update(status='fail', difference='x')
        child = subprocess.CompletedProcess([], 0, json.dumps(payload), '')
        with patch('verifier.calculations.subprocess.run', return_value=child):
            report = analyze(polynomial_record())
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(report['completed_checks'], ['C'])
        self.assertEqual(report['checks']['C']['difference'], 'x')

    def test_symbolic_contract_rejects_variable_denominators_domain_narrowing_and_growth(self):
        for change in (lambda r: r['checks']['C'].update(lhs=op('div', ref('x'), ref('x'))),
                       lambda r: r['variables']['x'].update(values=['1']),
                       lambda r: r['checks']['C'].update(lhs=op('pow', ref('x'), exponent=0)),
                       lambda r: r['checks']['C'].update(lhs=op('pow', op('add', op('add', ref('x'), number('1')), number('2')), exponent=8))):
            r = polynomial_record(); change(r)
            self.assertEqual(analyze(r)['status'], 'unsupported')

    def test_symbolic_constant_growth_is_rejected_before_worker_invocation(self):
        r = polynomial_record()
        expr = number('9'*80)
        for _ in range(8):
            expr = op('pow', expr, exponent=8)
        r['checks']['C']['lhs'] = expr
        with patch('verifier.calculations.subprocess.run') as worker:
            self.assertEqual(analyze(r)['status'], 'unsupported')
            worker.assert_not_called()

    def test_cli_pass_fail_input_errors_duplicate_keys_and_external_required_scope(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as tmp:
            model = Path(tmp)/'model.json'
            model.write_text(json.dumps(record(number('1'), number('1'))))
            def run(*extra):
                return subprocess.run([sys.executable, str(ROOT/'scripts/analyze.py'), 'calculations', str(model), *extra], capture_output=True, text=True)
            completed = run()
            self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result['input_path'], str(model.resolve()))
            self.assertEqual(run('--required', 'Removed').returncode, 1)
            model.write_text('{"version":1,"version":2}')
            completed = run()
            self.assertEqual(completed.returncode, 2)
            self.assertIn('duplicate JSON key', json.loads(completed.stdout)['detail'])

    def test_each_independent_launcher_dispatches_both_analyses_from_another_directory(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as tmp:
            for name in ('develop-system-concept', 'develop-conops', 'develop-operational-scenarios'):
                launcher = ROOT/'skills'/name/'scripts/cse.py'
                for kind, model in (('calculations', ROOT/'examples/calculations/energy-budget.json'),
                                    ('functional-graph', ROOT/'examples/function-flow/library-return.json')):
                    completed = subprocess.run([sys.executable, '-B', str(launcher), 'analyze', kind, str(model)],
                                               cwd=tmp, capture_output=True, text=True)
                    self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
                    self.assertEqual(json.loads(completed.stdout)['status'], 'pass')

    def test_synthetic_fixture_results_and_optional_identity_refusal_are_explicit(self):
        for name in ('energy-budget', 'care-throughput'):
            value = json.loads((ROOT/'examples/calculations'/(name+'.json')).read_text())
            self.assertEqual(analyze(value)['status'], 'pass')
        motion = json.loads((ROOT/'examples/calculations/motion-identity.json').read_text())
        expected = 'pass' if importlib.util.find_spec('sympy') else 'unsupported'
        self.assertEqual(analyze(motion)['status'], expected)


def polynomial_record():
    return record(op('pow', op('add', ref('x'), number('1')), exponent=2),
                  op('add', op('add', op('pow', ref('x'), exponent=2), op('mul', number('2'), ref('x'))), number('1')),
                  {'x': variable(None, domain='real')}, kind='polynomial_identity')


@unittest.skipUnless(importlib.util.find_spec('sympy'), 'Optional SymPy is unavailable in this interpreter')
class SymbolicControls(unittest.TestCase):
    def test_expansion_over_real_domain_is_proved_by_polynomial_coefficients(self):
        report = analyze(polynomial_record())
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(report['checks']['C']['backend'], 'sympy')
        self.assertEqual(report['checks']['C']['difference'], '0')

    def test_false_identity_and_multivariate_rational_identity(self):
        r = polynomial_record(); r['checks']['C']['rhs'] = number('1')
        self.assertEqual(analyze(r)['status'], 'fail')
        r = polynomial_record()
        r['variables']['y'] = variable(None)
        r['checks']['C'].update(lhs=op('mul', ref('x'), op('add', ref('y'), number('1/3'))),
                              rhs=op('add', op('mul', ref('x'), ref('y')), op('div', ref('x'), number('3'))))
        self.assertEqual(analyze(r)['status'], 'pass')

    def test_zero_constant_denominator_and_zero_power_remain_undefined(self):
        r = polynomial_record()
        r['checks']['C']['lhs'] = op('div', ref('x'), op('sub', number('1'), number('1')))
        self.assertEqual(analyze(r)['status'], 'unknown')
        r['checks']['C']['lhs'] = op('pow', number('0'), exponent=0)
        self.assertEqual(analyze(r)['status'], 'unknown')


if __name__ == '__main__':
    (ROOT/'.tmp').mkdir(exist_ok=True)
    unittest.main()
