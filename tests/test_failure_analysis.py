"""Behavior and counterexamples for bounded Boolean failure analysis."""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.failure_analysis import analyze


def model():
    return {'version': 'failure-analysis-1.0', 'id': 'SharedFailure', 'revision': 'synthetic-1',
            'basis': 'Synthetic Boolean example; all events refer to the same mission.',
            'events': {key: {'description': key+' failure', 'basis': 'Synthetic exact probability', 'probability': probability}
                       for key, probability in [('A', '1/100'), ('B', '1/200'), ('C', '1/500')]},
            'gates': {'AB': {'operator': 'and', 'inputs': ['A', 'B']},
                      'AC': {'operator': 'and', 'inputs': ['A', 'C']},
                      'Top': {'operator': 'or', 'inputs': ['AB', 'AC']}},
            'top_event': 'Top', 'probability': {'assumption': 'mutually_independent',
                                              'basis': 'Explicit synthetic assumption', 'mission': 'One synthetic mission'},
            'fmea': {}}


def fmea():
    return {'component': 'Pump', 'failure_mode': 'Does not start', 'event': 'A',
            'local_effect': 'Pump delivers no flow', 'system_effect': 'One modeled path is unavailable',
            'detection': 'Explicit synthetic flow observation', 'basis': 'Synthetic example only'}


class FailureAnalysisTests(unittest.TestCase):
    def temporary_workspace(self):
        parent = ROOT/'.tmp'
        parent.mkdir(exist_ok=True)
        workspace = TemporaryDirectory(dir=parent)
        self.addCleanup(workspace.cleanup)
        return Path(workspace.name)

    def test_shared_event_exact_probability_and_minimal_sets(self):
        result = analyze(model())
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['checks']['fault_tree']['minimal_cut_sets'], [['A', 'B'], ['A', 'C']])
        self.assertEqual(result['checks']['fault_tree']['completed_assignments'], 8)
        p, q, r = Fraction('1/100'), Fraction('1/200'), Fraction('1/500')
        self.assertEqual(Fraction(result['checks']['probability']['probability']), p*(q+r-q*r))
        self.assertEqual(result['checks']['probability']['probability'], '699/10000000')

    def test_scram_published_boolean_control(self):
        record = model()
        record['gates']['AC']['inputs'] = ['B', 'C']
        for key, probability in [('A', '1/10'), ('B', '1/5'), ('C', '3/10')]:
            record['events'][key]['probability'] = probability
        result = analyze(record)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['checks']['probability']['probability'], '37/500')
        self.assertEqual(result['checks']['fault_tree']['minimal_cut_sets'], [['A', 'B'], ['B', 'C']])

    def test_idempotence_and_absorption(self):
        record = model()
        record['gates']['AB']['inputs'] = ['A', 'A']
        result = analyze(record)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['checks']['fault_tree']['minimal_cut_sets'], [['A']])
        self.assertEqual(result['checks']['probability']['probability'], '1/100')

    def test_shared_cause_is_explicit_single_event(self):
        record = model()
        record['gates'] = {'Top': {'operator': 'or', 'inputs': ['A', 'A']}}
        result = analyze(record)
        self.assertEqual(result['checks']['probability']['probability'], '1/100')
        self.assertEqual(result['checks']['fault_tree']['events'], ['A'])
        self.assertEqual(result['checks']['fault_tree']['unused_events'], ['B', 'C'])

    def test_qualitative_model_needs_no_inferred_probabilities(self):
        record = model(); record['probability'] = None
        for event in record['events'].values(): event['probability'] = None
        result = analyze(record)
        self.assertEqual(result['status'], 'pass')
        self.assertNotIn('probability', result['checks'])
        result = analyze(record, ['fault_tree', 'probability'])
        self.assertEqual(result['status'], 'fail')
        self.assertIn('probability', result['expected_checks'])

    def test_missing_basis_or_probability_never_numeric_success(self):
        for field in ('basis', 'probability'):
            record = model(); record['events']['A'][field] = None
            result = analyze(record)
            self.assertEqual(result['status'], 'unknown')
            self.assertIsNone(result['checks']['probability']['probability'])
        for field in ('basis', 'mission'):
            record = model(); record['probability'][field] = None
            self.assertEqual(analyze(record)['status'], 'unknown')

    def test_no_missing_scope_or_empty_success(self):
        self.assertEqual(analyze(model(), [])['status'], 'error')
        self.assertEqual(analyze(model(), ['fmea'])['status'], 'fail')
        self.assertEqual(analyze(model(), ['bogus'])['status'], 'error')
        record = model(); record['events'] = {}; record['gates'] = {}
        self.assertEqual(analyze(record)['status'], 'fail')
        result = analyze({}, ['fault_tree', 'probability', 'fmea'])
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['expected_checks'], ['fault_tree', 'fmea', 'probability'])
        self.assertTrue(all(check['status'] == 'not_run' for check in result['checks'].values()))

    def test_fmea_completeness_reference_and_no_scores(self):
        record = model(); record['fmea']['Row'] = fmea()
        result = analyze(record)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['checks']['fmea']['severity_ranking'], 'not_evaluated')
        record['fmea']['Row']['detection'] = None
        self.assertEqual(analyze(record)['status'], 'unknown')
        record['fmea']['Row']['event'] = 'Top'
        self.assertEqual(analyze(record)['status'], 'fail')

    def test_fmea_duplicate_pair_and_unknown_modes(self):
        record = model(); record['fmea'] = {'Row': fmea(), 'Row2': fmea()}
        self.assertEqual(analyze(record)['status'], 'fail')
        for row in record['fmea'].values(): row['failure_mode'] = None
        self.assertEqual(analyze(record)['status'], 'unknown')

    def test_cycles_and_bad_unused_content(self):
        for invalid in [{'operator': 'and', 'inputs': ['Missing']},
                        {'operator': 'or', 'inputs': ['Unused']},
                        {'operator': 'and', 'inputs': []},
                        {'operator': 'not', 'inputs': ['A']}]:
            record = model(); record['gates']['Unused'] = invalid
            self.assertNotEqual(analyze(record)['status'], 'pass')
        record = model(); record['events']['Unused'] = {'description':'Unused','basis':'Known','probability':'2'}
        self.assertEqual(analyze(record)['status'], 'fail')

    def test_strict_types_and_unsupported_semantics(self):
        for probability in (0.1, True, '-1', '1/0', 'NaN', 'lambda: 0'):
            record = model(); record['events']['A']['probability'] = probability
            self.assertEqual(analyze(record)['status'], 'error')
        record = model(); record['probability']['assumption'] = 'pairwise_independent'
        self.assertEqual(analyze(record)['status'], 'unsupported')
        record = model(); record['gates']['Top']['operator'] = 'kofn'
        self.assertEqual(analyze(record)['status'], 'unsupported')
        record = model(); record['fmea']['Row'] = fmea(); record['fmea']['Row']['severity'] = 4
        self.assertEqual(analyze(record)['status'], 'error')

    def test_enumeration_and_output_limits_do_not_return_partial_cuts(self):
        record = model(); record['events'] = {f'E{i}': {'description':'Failure','basis':'Synthetic','probability':None} for i in range(13)}
        record['gates'] = {'Top': {'operator':'or', 'inputs':sorted(record['events'])}}
        record['probability'] = None
        result = analyze(record)
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(result['checks']['fault_tree']['cut_sets_complete'])
        self.assertNotIn('minimal_cut_sets', result['checks']['fault_tree'])

    def test_full_twelve_event_domain_matches_binomial_control(self):
        record = model()
        record['events'] = {f'E{i:02d}': {'description':'Synthetic failure','basis':'Synthetic independent coin','probability':'1/2'} for i in range(12)}
        keys = sorted(record['events'])
        expected = [list(pair) for pair in combinations(keys, 2)]
        record['gates'] = {f'Pair{i:02d}': {'operator':'and','inputs':pair} for i,pair in enumerate(expected)}
        for group in range(3):
            record['gates'][f'Group{group}'] = {'operator':'or','inputs':[f'Pair{i:02d}' for i in range(22*group,22*(group+1))]}
        record['gates']['Top'] = {'operator':'or','inputs':['Group0','Group1','Group2']}
        result = analyze(record)
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['checks']['fault_tree']['completed_assignments'], 4096)
        self.assertEqual(result['checks']['fault_tree']['minimal_cut_sets'], expected)
        self.assertEqual(result['checks']['probability']['probability'], '4083/4096')

    def test_real_large_antichain_cannot_pass_as_truncated_success(self):
        # AND/OR expansion of "at least six of twelve" has C(12,6)=924
        # minimal cuts. Voting operators remain outside the model grammar.
        record = model();record['probability']=None
        record['events'] = {f'E{i}': {'description':'Failure','basis':'Synthetic','probability':None} for i in range(1,13)}
        record['gates'] = {}
        for i in range(1,13):
            for k in range(1,min(i,6)+1):
                inputs = [f'E{j}' for j in range(1,i+1)]
                if k == 1:
                    gate = {'operator':'or','inputs':inputs}
                elif k == i:
                    gate = {'operator':'and','inputs':inputs}
                else:
                    joined = f'J{i}_{k}'
                    record['gates'][joined] = {'operator':'and','inputs':[f'E{i}',f'T{i-1}_{k-1}']}
                    gate = {'operator':'or','inputs':[f'T{i-1}_{k}',joined]}
                record['gates'][f'T{i}_{k}'] = gate
        record['top_event'] = 'T12_6'
        result = analyze(record)
        self.assertEqual(result['status'], 'unknown', result)
        self.assertFalse(result['checks']['fault_tree']['cut_sets_complete'])
        self.assertNotIn('minimal_cut_sets', result['checks']['fault_tree'])

    def test_depth_limit_is_independent_of_sorted_visit_order(self):
        record = model(); record['gates'] = {}
        for i in range(66):
            record['gates'][f'G{i:02d}'] = {'operator':'or','inputs':['A' if i == 0 else f'G{i-1:02d}']}
        record['top_event'] = 'G65'
        self.assertEqual(analyze(record)['status'], 'unsupported')

    def test_probability_zero_and_one(self):
        record = model(); record['top_event'] = 'A'
        for p in ('0', '1'):
            record['events']['A']['probability'] = p
            self.assertEqual(analyze(record)['checks']['probability']['probability'], p)

    def test_zero_denominators_are_structured_errors_in_library_and_cli(self):
        workspace = self.temporary_workspace()
        target = workspace/'zero-denominator.json'
        for probability in ('1/0', '0/0'):
            with self.subTest(probability=probability):
                record = model()
                record['events']['A']['probability'] = probability
                result = analyze(record, ['fault_tree', 'probability'])
                self.assertEqual(result['status'], 'error')
                self.assertEqual(result['findings'][0]['rule'], 'failure_probability')
                self.assertEqual(result['completed_checks'], [])
                self.assertEqual(result['checks']['probability']['status'], 'not_run')
                target.write_text(json.dumps(record))
                cli = subprocess.run([sys.executable, '-B', str(ROOT/'scripts/failure_analysis.py'), str(target)],
                                     cwd=workspace, capture_output=True, text=True)
                self.assertEqual(cli.returncode, 1)
                self.assertEqual(json.loads(cli.stdout)['status'], 'error')
                self.assertEqual(cli.stderr, '')

    def test_deterministic_report_under_map_and_input_permutations(self):
        record = model(); other = deepcopy(record)
        other['events'] = dict(reversed(list(other['events'].items())))
        other['gates'] = dict(reversed(list(other['gates'].items())))
        self.assertEqual(analyze(record), analyze(other))
        other['gates']['Top']['inputs'].reverse()
        a,b=analyze(record),analyze(other)
        for r in (a,b):r.pop('artifact_sha256')
        self.assertEqual(a,b)

    def test_cli_from_other_directory_and_strict_json(self):
        workspace = self.temporary_workspace()
        path = ROOT/'examples/failure-analysis/shared-event.json'
        cmd = [sys.executable, '-B', str(ROOT/'scripts/failure_analysis.py'), str(path)]
        result = subprocess.run(cmd, cwd=workspace, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'pass')
        target = workspace/'invalid.json'
        for text in ('{"version":1,"version":2}', '{"x":NaN}'):
            target.write_text(text)
            run = subprocess.run(cmd[:-1]+[str(target)], cwd=workspace, text=True, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)['status'], 'error')


if __name__ == '__main__':
    unittest.main()
