"""Definition drift, incomplete meanings and bounded input are observable defects."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.measures import FIELDS, LIMITS, check, compare


def fixture():
    return json.loads((ROOT/'examples/measurement-definitions/request-duration-v1.json').read_text())


class MeasureDefinitions(unittest.TestCase):
    def test_complete_synthetic_definition_has_only_scoped_claims(self):
        result = check(fixture())
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['observation_comparability'], 'not_evaluated')
        self.assertEqual(result['formula_evaluation'], 'not_run')
        self.assertEqual(result['meaning_validation'], 'not_evaluated')
        self.assertEqual(result['acceptance'], 'not_evaluated')

    def test_all_meaning_fields_break_equivalence(self):
        for field in FIELDS:
            before, after = fixture(), fixture()
            after['revision'] = 'synthetic-2'
            value = after['definition'][field]
            if field == 'scale':
                after['definition'][field] = 'ordinal'
            elif field == 'inputs':
                value['handling']['quantity'] += '; revised boundary'
            elif field == 'formula':
                value['op'] = 'sub'
            elif field == 'unit':
                value['second'] = 2
            elif field == 'aggregation':
                value['method'] = 'median'
            elif type(value) is str:
                after['definition'][field] += '; revised meaning'
            else:
                value.append('New explicit exclusion or condition')
            result = compare(before, after)
            with self.subTest(field=field):
                self.assertNotEqual(result['status'], 'pass', result)
                self.assertEqual(result['definition_equivalence'], 'different', result)
                self.assertIn(field, result['changed_meaning_fields'])

    def test_metadata_revision_and_key_order_do_not_change_meaning(self):
        before, after = fixture(), fixture()
        after['revision'] = 'synthetic-2'; after['label'] = 'Display label revised'
        after['sources']['SyntheticSpec']['revision'] = 'synthetic-2'
        after['links'] = [{'kind':'question', 'id':'QuestionA', 'revision':'draft-1'}]
        result = compare(before, after)
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['definition_equivalence'], 'equal')
        self.assertEqual(result['changed_metadata_fields'], ['label','sources','links'])
        self.assertEqual(result['before']['definition_sha256'], result['after']['definition_sha256'])
        self.assertNotEqual(result['before']['record_sha256'], result['after']['record_sha256'])
        after['definition'] = dict(reversed(list(after['definition'].items())))
        self.assertEqual(compare(before, after)['status'], 'pass')

    def test_changed_record_cannot_reuse_revision_or_identity(self):
        before, after = fixture(), fixture(); after['label'] += ' revised'
        self.assertIn('measure_revision_reused', [f['rule'] for f in compare(before, after)['findings']])
        after = fixture(); after['id'] = 'AnotherMeasure'
        self.assertEqual(compare(before, after)['status'], 'fail')
        self.assertEqual(compare(before, after)['definition_equivalence'], 'unknown')

    def test_every_null_meaning_field_and_open_question_prevents_success(self):
        for field in FIELDS:
            record = fixture(); record['definition'][field] = None
            with self.subTest(field=field):
                self.assertEqual(check(record)['status'], 'unknown')
                self.assertNotEqual(compare(record, deepcopy(record))['status'], 'pass')
        for change in (lambda r:r.update(sources={}),
                       lambda r:r['sources']['SyntheticSpec'].update(basis=None),
                       lambda r:r.update(unknowns=[{'field':'sampling','question':'Does this sampling frame apply?'}]),
                       lambda r:r['definition']['inputs']['handling'].update(unit=None),
                       lambda r:r['definition']['aggregation'].update(basis=None)):
            record = fixture(); change(record)
            self.assertEqual(check(record)['status'], 'unknown')

    def test_formula_unit_reference_scale_and_code_defects(self):
        changes = [lambda r:r['definition']['formula']['args'][0].update(ref='Missing'),
                   lambda r:r['definition'].update(unit={'minute':1}),
                   lambda r:r['definition']['inputs']['handling'].update(scale='ordinal'),
                   lambda r:r['definition'].update(formula='__import__("os").system("false")'),
                   lambda r:r['definition'].update(formula={'op':'python','args':[]}),
                   lambda r:r['definition']['aggregation'].update(method='free_form_expression')]
        for change in changes:
            record = fixture(); change(record)
            self.assertNotEqual(check(record)['status'], 'pass')
        record = fixture(); record['definition']['formula'] = {'ref':'handling'}
        self.assertEqual(check(record)['status'], 'pass')
        record['definition']['scale'] = 'interval'
        self.assertEqual(check(record)['status'], 'fail')

    def test_ratio_has_explicit_numerator_denominator_without_evaluation(self):
        record = fixture()
        record['definition'].update(formula={'op':'div','args':[{'ref':'handling'},{'ref':'completion'}]},
                                    unit={}, aggregation={'method':'mean','basis':'Mean of per-request ratios'})
        result = check(record)
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['formula_evaluation'], 'not_run')

    def test_category_identity_supported_but_category_arithmetic_not_supported(self):
        record = fixture(); d = record['definition']
        d.update(scale='nominal', inputs={'code':{'quantity':'Request category','unit':{},'scale':'nominal'}},
                 formula={'ref':'code'}, unit={}, aggregation={'method':'mode','basis':'Most frequent code; retain ties'})
        self.assertEqual(check(record)['status'], 'pass')
        d['aggregation']['method'] = 'mean'
        self.assertEqual(check(record)['status'], 'unsupported')

    def test_reordered_lists_are_conservative_meaning_changes(self):
        before, after = fixture(), fixture(); after['revision'] = 'synthetic-2'
        after['definition']['conditions'].reverse()
        result = compare(before, after)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['changed_meaning_fields'], ['conditions'])

    def test_malformed_and_bounded_definitions_cannot_pass(self):
        for value in (None, [], {}, {'version':'other'}, True):
            self.assertEqual(check(value)['status'], 'error')
        record = fixture(); record['version'] = 'future'
        self.assertEqual(check(record)['status'], 'unsupported')
        for change in (lambda r:r.update(extra='unknown field'),
                       lambda r:r['definition'].update(quantity='x'*(LIMITS['text_characters']+1)),
                       lambda r:r['definition'].update(exclusions=['x']*65),
                       lambda r:r['definition'].update(unit={'second':True}),
                       lambda r:r['definition'].update(exclusions=['same','same'])):
            record = fixture(); change(record)
            self.assertEqual(check(record)['status'], 'error')
        record = fixture(); record['unknowns'] = [{'field':'quantity','question':'Unknown?'}]*64
        record['definition']['quantity'] = None
        result = check(record)
        self.assertEqual(len(result['findings']), LIMITS['findings'])
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['findings'][-1]['rule'], 'measure_diagnostic_limit')

    def test_incomplete_meaning_change_is_visible_but_never_successful(self):
        before, after = fixture(), fixture(); after['revision'] = 'synthetic-2'
        after['definition']['sampling'] = None
        result = compare(before, after)
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['definition_equivalence'], 'different')
        self.assertEqual(result['changed_meaning_fields'], ['sampling'])

    def test_broken_formula_still_reports_changed_definition(self):
        before, after = fixture(), fixture(); after['revision'] = 'synthetic-2'
        after['definition']['formula']['args'][0]['ref'] = 'Missing'
        result = compare(before, after)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['definition_equivalence'], 'different')
        self.assertEqual(result['changed_meaning_fields'], ['formula'])

    def test_formula_limits_input_count_tree_depth_and_node_limits(self):
        record = fixture()
        record['definition']['inputs'] = {f'X{i}':{'quantity':'Synthetic duration', 'unit':{'second':1},'scale':'ratio'} for i in range(33)}
        self.assertEqual(check(record)['status'], 'error')
        record = fixture(); expression = {'ref':'handling'}
        for _ in range(17):
            expression = {'op':'neg','args':[expression]}
        record['definition']['formula'] = expression
        self.assertNotEqual(check(record)['status'], 'pass')
        record = fixture(); expression = {'ref':'handling'}
        for _ in range(7):
            expression = {'op':'add','args':[deepcopy(expression),deepcopy(expression)]}
        record['definition']['formula'] = expression
        self.assertEqual(check(record)['status'], 'unsupported')

    def test_external_cwd_launchers_json_input_errors_and_no_mutation(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as tmp:
            tmp = Path(tmp); path = tmp/'measure.json'
            original = json.dumps(fixture()); path.write_text(original)
            launchers = [ROOT/'scripts/measures.py', ROOT/'skills/define-engineering-measures/scripts/measures.py']
            def run(launcher, *args):
                return subprocess.run([sys.executable, '-B', str(launcher), *map(str,args)],
                                      cwd=tmp, capture_output=True, text=True)
            for launcher in launchers:
                child = run(launcher, 'check', path)
                self.assertEqual(child.returncode, 0, child.stdout+child.stderr)
                self.assertEqual(json.loads(child.stdout)['status'], 'pass')
                self.assertEqual(run(launcher, 'compare', path, path).returncode, 0)
                self.assertIn('not evaluated', run(launcher, 'check', path, '--format', 'text').stdout)
            self.assertEqual(path.read_text(), original)
            for raw in ('{"version":1,"version":2}', '{bad', '{"version":NaN}', 'null', '\udcff'):
                path.write_bytes(raw.encode('utf-8', errors='surrogatepass'))
                child = run(launchers[0], 'check', path)
                self.assertEqual(child.returncode, 2, child.stdout+child.stderr)
                self.assertEqual(json.loads(child.stdout)['status'], 'error')
            path.write_bytes(b' '*(LIMITS['input_bytes']+1))
            self.assertEqual(run(launchers[0], 'check', path).returncode, 2)
            target = tmp/'target.json'; target.write_text(original)
            link = tmp/'link.json'; link.symlink_to(target)
            self.assertEqual(run(launchers[0], 'check', link).returncode, 2)


if __name__ == '__main__':
    unittest.main()
