"""Independent exact numerical controls and invalid observation contracts."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.validation import analyze, load, LIMITS


def fixture():
    return json.loads((ROOT / 'examples/validation/synthetic-observations.json').read_text())


class ObservationValidationTests(unittest.TestCase):
    def test_exact_numerical_controls(self):
        report = analyze(fixture(), ['Intervals', 'Weighted', 'Tail'])
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['completed_checks'], ['Intervals', 'Tail', 'Weighted'])
        interval = report['checks']['Intervals']['metrics']
        self.assertEqual(interval['coverage'], '2/3')
        self.assertEqual(interval['mean_width'], '5/3')
        self.assertEqual(interval['coverage_minus_nominal'], '1/6')
        # Hand calculation: widths 2,2,1; one upper miss of 1 costs 4.
        self.assertEqual(interval['mean_interval_score'], '3')
        weighted = report['checks']['Weighted']['metrics']
        self.assertEqual(weighted['mean'], '5/2')
        self.assertEqual(weighted['population_variance'], '3/4')
        self.assertEqual(weighted['weight_effective_size'], '8/5')
        self.assertEqual(weighted['variance_unit'], {'second': 2})
        self.assertEqual(report['checks']['Tail']['metrics']['tail_probability'], '5/16')
        for field in ('acceptance', 'source_truth', 'simulation_fidelity', 'assumption_truth'):
            self.assertEqual(report[field], 'not_evaluated')
        self.assertEqual(report['future_coverage'], 'not_established')

    def test_darts_winkler_control(self):
        record = fixture()
        rows = record['checks']['Intervals']['rows']
        for row in rows:
            row.update(lower='7/4', upper='17/4')
        report = analyze(record)
        # Scores 19/2, 5/2, 19/2, matching inspected Darts source control.
        self.assertEqual(report['checks']['Intervals']['metrics']['mean_interval_score'], '43/6')

    def test_closed_endpoints_and_degenerate_interval(self):
        record = fixture()
        record['checks']['Intervals']['rows'] = [
            {'id': 'Lower', 'actual': '0', 'lower': '0', 'upper': '2'},
            {'id': 'Upper', 'actual': '2', 'lower': '0', 'upper': '2'},
            {'id': 'Point', 'actual': '1', 'lower': '1', 'upper': '1'}]
        metrics = analyze(record)['checks']['Intervals']['metrics']
        self.assertEqual(metrics['coverage'], '1')
        self.assertEqual(metrics['mean_width'], '4/3')
        self.assertEqual(metrics['mean_interval_score'], '4/3')

    def test_interval_misses_on_both_sides(self):
        record = fixture()
        record['checks']['Intervals']['rows'] = [
            {'id': 'Low', 'actual': '-1', 'lower': '0', 'upper': '2'},
            {'id': 'High', 'actual': '3', 'lower': '0', 'upper': '2'}]
        metrics = analyze(record)['checks']['Intervals']['metrics']
        self.assertEqual(metrics['coverage'], '0')
        self.assertEqual(metrics['mean_interval_score'], '6')
        self.assertEqual(metrics['below_ids'], ['Low'])
        self.assertEqual(metrics['above_ids'], ['High'])

    def test_training_cannot_be_held_out_validation(self):
        for role in ('training', 'calibration', 'simulation', None):
            record = fixture(); record['dataset']['role'] = role
            report = analyze(record)
            self.assertEqual(report['status'], 'unknown')
            self.assertEqual(report['checks']['Intervals']['status'], 'unknown')
            self.assertIn('metrics', report['checks']['Intervals'])
            self.assertIn('Intervals', report['computed_checks'])
            self.assertNotIn('Intervals', report['completed_checks'])

    def test_training_descriptive_summaries_can_compute(self):
        record = fixture(); record['dataset']['role'] = 'training'
        record['checks']['Intervals']['purpose'] = 'descriptive'
        record['checks']['Intervals']['assumptions'].remove('Separate')
        self.assertEqual(analyze(record)['status'], 'pass')

    def test_applicability_and_basis_are_required(self):
        for key in ('Aligned', 'Central', 'Separate'):
            record = fixture(); record['checks']['Intervals']['assumptions'].remove(key)
            self.assertEqual(analyze(record)['status'], 'unknown')
        for key in ('Weights', 'Independent', 'Common', 'Binary'):
            record = fixture(); record['assumptions'][key]['basis'] = None
            self.assertEqual(analyze(record)['status'], 'unknown')

    def test_required_scope_cannot_disappear(self):
        record = fixture(); del record['checks']['Intervals']
        report = analyze(record, ['Intervals', 'Tail', 'Weighted'])
        self.assertEqual(report['status'], 'fail')
        self.assertTrue(any(f['rule'] == 'validation_required_missing' for f in report['findings']))

    def test_empty_or_duplicate_scope_and_checks(self):
        for required in ([], ['Tail', 'Tail'], ['bad id'], 'Tail', {'Tail': True}):
            self.assertEqual(analyze(fixture(), required)['status'], 'error')
        record = fixture(); record['checks'] = {}
        self.assertEqual(analyze(record)['status'], 'error')

    def test_reversed_empty_duplicate_and_nonexact_rows(self):
        for rows in ([], [{'id': 'Bad', 'actual': '1', 'lower': '2', 'upper': '0'}],
                     [{'id': 'Bad', 'actual': 1.0, 'lower': '0', 'upper': '2'}],
                     [{'id': 'Bad', 'actual': 'NaN', 'lower': '0', 'upper': '2'}]):
            record = fixture(); record['checks']['Intervals']['rows'] = rows
            self.assertEqual(analyze(record)['status'], 'error')
        record = fixture(); record['checks']['Intervals']['rows'] *= 2
        self.assertEqual(analyze(record)['status'], 'error')

    def test_alpha_domain(self):
        for alpha in ('0', '1', '-1', '2', 0.5, True):
            record = fixture(); record['checks']['Intervals']['alpha'] = alpha
            self.assertEqual(analyze(record)['status'], 'error')

    def test_weight_zero_negative_and_scale_invariance(self):
        record = fixture(); rows = record['checks']['Weighted']['rows']
        rows.append({'id': 'NoMass', 'value': '999', 'weight': '0'})
        baseline = analyze(record)['checks']['Weighted']['metrics']
        self.assertEqual(baseline['mean'], '5/2')
        self.assertEqual(baseline['positive_weight_rows'], 2)
        for row in rows:
            row['weight'] = str(Fraction(row['weight']) * 7)
        changed = analyze(record)['checks']['Weighted']['metrics']
        for key in ('mean', 'population_variance', 'weight_effective_size'):
            self.assertEqual(changed[key], baseline[key])
        for weight in ('0', '-1'):
            record = fixture()
            for row in record['checks']['Weighted']['rows']:
                row['weight'] = weight
            self.assertEqual(analyze(record)['status'], 'error')

    def test_singleton_weight_is_population_zero_variance(self):
        record = fixture(); record['checks']['Weighted']['rows'] = [
            {'id': 'Only', 'value': '9', 'weight': '2'}]
        result = analyze(record)['checks']['Weighted']['metrics']
        self.assertEqual(result['population_variance'], '0')
        self.assertEqual(result['weight_effective_size'], '1')
        self.assertEqual(result['independent_sample_size'], 'not_established')

    def test_binomial_enumerated_oracle_and_endpoints(self):
        for n in range(1, 9):
            # Enumerate all fair-coin outcomes independently of the formula.
            counts = [bits.bit_count() for bits in range(2 ** n)]
            for k in range(n + 1):
                for tail in ('le', 'ge'):
                    record = fixture(); record['checks'] = {'Tail': record['checks']['Tail']}
                    record['checks']['Tail'].update(n=n, k=k, tail=tail)
                    expected = Fraction(sum(c <= k if tail == 'le' else c >= k for c in counts), 2 ** n)
                    self.assertEqual(analyze(record)['checks']['Tail']['metrics']['tail_probability'], str(expected))
        for p, k, tail, expected in [('0', 0, 'le', '1'), ('0', 1, 'ge', '0'),
                                      ('1', 3, 'le', '0'), ('1', 4, 'ge', '1')]:
            record = fixture(); record['checks']['Tail'].update(probability=p, k=k, tail=tail)
            self.assertEqual(analyze(record)['checks']['Tail']['metrics']['tail_probability'], expected)

    def test_binomial_bounds_and_growth(self):
        for edits in ({'n': True}, {'n': 0}, {'n': 257}, {'k': -1}, {'k': 5}, {'probability': '2'}, {'tail': 'gt'}):
            record = fixture(); record['checks']['Tail'].update(edits)
            self.assertEqual(analyze(record)['status'], 'error')
        record = fixture(); record['checks']['Tail'].update(n=256, probability='1/' + '9' * 70)
        self.assertEqual(analyze(record)['status'], 'unknown')
        self.assertNotIn('Tail', analyze(record)['completed_checks'])

    def test_unsupported_unknown_and_missing_reference_never_pass(self):
        record = fixture(); record['checks']['Intervals']['kind'] = 'fit_forecaster'
        self.assertEqual(analyze(record)['status'], 'unsupported')
        record = fixture(); record['version'] = 'future-1'
        self.assertEqual(analyze(record)['status'], 'unsupported')
        record = fixture(); record['dataset']['population'] = None
        self.assertEqual(analyze(record)['status'], 'unknown')
        record = fixture(); record['unknowns'] = [{'field': 'source', 'question': 'Which source applies?'}]
        self.assertEqual(analyze(record)['status'], 'unknown')
        record = fixture(); record['checks']['Tail']['assumptions'].append('Missing')
        self.assertEqual(analyze(record)['status'], 'fail')

    def test_schema_and_unit_limits(self):
        record = fixture(); record['unexpected'] = 'ignored?'
        self.assertEqual(analyze(record)['status'], 'error')
        record = fixture(); record['measure']['unit'] = {'second': 0}
        self.assertEqual(analyze(record)['status'], 'error')
        record = fixture(); record['checks']['Intervals']['rows'] *= LIMITS['rows_per_check']
        self.assertEqual(analyze(record)['status'], 'error')

    def test_diagnostic_saturation_preserves_every_check_verdict(self):
        record = fixture()
        check = copy.deepcopy(record['checks']['Intervals'])
        check['assumptions'] = ['Missing' + str(i) for i in range(32)]
        record['checks'] = {'Check' + str(i).zfill(2): copy.deepcopy(check) for i in range(32)}
        report = analyze(record)
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(len(report['findings']), LIMITS['findings'])
        self.assertEqual(len(report['checks']), 32)
        self.assertTrue(all(result['status'] == 'fail' for result in report['checks'].values()))
        self.assertEqual(report['findings'][-1]['rule'], 'validation_diagnostic_limit')

    def test_loader_and_cli_refuse_bad_files(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as tmp:
            path = Path(tmp) / 'record.json'
            for text in ('{"a":1,"a":2}', '{"a":NaN}', '[]', '{'):
                path.write_text(text)
                process = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_observations.py'), str(path)], capture_output=True, text=True)
                self.assertEqual(process.returncode, 2)
                self.assertEqual(json.loads(process.stdout)['status'], 'error')
            path.write_text(json.dumps(fixture()))
            linked = Path(tmp) / 'linked.json'; linked.symlink_to(path)
            with self.assertRaises(OSError):
                load(linked)
            path.write_bytes(b'x' * (LIMITS['input_bytes'] + 1))
            with self.assertRaises(ValueError):
                load(path)

    def test_cli_required_scope_and_hash(self):
        path = ROOT / 'examples/validation/synthetic-observations.json'
        command = [sys.executable, str(ROOT / 'scripts/validate_observations.py'), str(path)]
        good = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0)
        self.assertEqual(len(json.loads(good.stdout)['inputs'][0]['sha256']), 64)
        missing = subprocess.run(command + ['--required', 'Missing'], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 1)
        self.assertEqual(json.loads(missing.stdout)['status'], 'fail')


if __name__ == '__main__':
    unittest.main()
