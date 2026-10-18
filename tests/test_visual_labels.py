"""Presentation wording remains explicit, native-bound, and separate from models."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.visual_labels import apply_labels, load_labels
from verifier.sysml import CLASSES, JAR, check_sysml

MODEL = ROOT / 'examples/sysml/views/field-service-demo.sysml'
LABELS = MODEL.with_suffix('.labels.json')


def projection():
    return {'id': 'FT', 'kind': 'function_tree', 'nodes': [
        {'id': 'F0', 'element': 'Example::MaintainStation', 'text': 'MaintainStation', 'level': 0, 'parent': None},
        {'id': 'F1', 'element': 'Example::ReviewServiceRequest', 'text': 'ReviewServiceRequest', 'level': 1, 'parent': 'F0'}]}


def record():
    return {'version': 1, 'view': 'FT', 'title': 'Maintain the station',
            'labels': [{'element': 'Example::MaintainStation', 'text': 'Maintain the station'}]}


class VisualLabelTests(unittest.TestCase):
    def test_native_default_and_partial_explicit_wording_preserve_projection(self):
        model = projection()
        prior = deepcopy(model)
        self.assertIsNone(load_labels())
        default = apply_labels(model)
        self.assertEqual(default, {'title': 'Function decomposition', 'labels': {
            'F0': 'MaintainStation', 'F1': 'ReviewServiceRequest'}, 'bindings': []})
        explicit = record()
        saved = deepcopy(explicit)
        result = apply_labels(model, explicit)
        self.assertEqual(result['title'], 'Maintain the station')
        self.assertEqual(result['labels'], {'F0': 'Maintain the station', 'F1': 'ReviewServiceRequest'})
        self.assertEqual(result['bindings'], explicit['labels'])
        self.assertEqual(model, prior)
        self.assertEqual(explicit, saved)
        result['bindings'][0]['text'] = 'Changed output'
        self.assertEqual(explicit, saved)
        self.assertEqual(model, prior)

    def test_load_is_strict_and_rejects_unsupported_or_blank_wording(self):
        for change in (
            {'version': True}, {'version': 2}, {'view': 'wrong view'}, {'title': ''}, {'title': '   '},
            {'title': 'Unsupported \u2603'}, {'title': 'Line\nbreak'}, {'labels': {}},
            {'labels': [{'element': 'Example::MaintainStation', 'text': '  '}]},
            {'labels': [{'element': 'Example::MaintainStation', 'text': 'New text', 'status': 'accepted'}]},
            {'labels': [{'element': '', 'text': 'New text'}]}, {'authority': 'accepted'},
        ):
            with self.subTest(change=change):
                candidate = record()
                candidate.update(change)
                with self.assertRaises(ValueError): load_labels(candidate)
        for field in record():
            candidate = record()
            candidate.pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError): load_labels(candidate)
        candidate = record()
        candidate['title'] = 'Inspect · restore'
        self.assertEqual(load_labels(candidate)['title'], 'Inspect · restore')

    def test_native_bindings_cannot_target_other_views_or_unknown_or_repeated_elements(self):
        model = projection()
        other = record()
        other['view'] = 'Other'
        with self.assertRaisesRegex(ValueError, 'different view'): apply_labels(model, other)
        unknown = record()
        unknown['labels'][0]['element'] = 'Example::Absent'
        with self.assertRaisesRegex(ValueError, 'outside'): apply_labels(model, unknown)
        repeated = record()
        repeated['labels'].append(deepcopy(repeated['labels'][0]))
        with self.assertRaisesRegex(ValueError, 'Repeated'): apply_labels(model, repeated)
        for field in ('id', 'element'):
            ambiguous = projection()
            ambiguous['nodes'][1][field] = ambiguous['nodes'][0][field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'unique'):
                apply_labels(ambiguous, record())

    def test_file_loading_duplicate_keys_and_no_source_code_evaluation(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as temp:
            path = Path(temp) / 'labels.json'
            path.write_text(json.dumps(record()))
            self.assertEqual(load_labels(path), record())
            for content in (
                '{"version":1,"version":1,"view":"FT","title":"Title","labels":[]}',
                '{"version":1,"view":"FT","title":"Title","labels":[{"element":"X","text":"A","text":"B"}]}',
                '{"version":NaN,"view":"FT","title":"Title","labels":[]}',
            ):
                path.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError): load_labels(path)
            candidate = record()
            candidate['labels'][0]['text'] = "__import__('os').system('false')"
            path.write_text(json.dumps(candidate))
            self.assertEqual(apply_labels(projection(), path)['labels']['F0'], candidate['labels'][0]['text'])


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(), 'Pinned native parser unavailable')
class NativeLabelFixtureTests(unittest.TestCase):
    def test_original_demo_binds_thirteen_native_actions_and_exact_three_level_tree(self):
        report = check_sysml(MODEL, syntax_only=True)
        self.assertEqual(report['status'], 'pass', report)
        inventory = report['inventory']
        from verifier.visual_projection import project_function_tree
        model = project_function_tree(inventory, 'FT_DEMO')
        prior = deepcopy(model)
        self.assertEqual(len(model['nodes']), 13)
        self.assertEqual([sum(n['level'] == level for n in model['nodes']) for level in (0, 1, 2)], [1, 3, 9])
        for branch in (n for n in model['nodes'] if n['level'] == 1):
            self.assertEqual(sum(n['parent'] == branch['id'] for n in model['nodes']), 3)
        labels = load_labels(LABELS)
        result = apply_labels(model, labels)
        self.assertEqual(len(result['bindings']), 13)
        self.assertEqual(set(result['labels']), {n['id'] for n in model['nodes']})
        self.assertEqual(result['title'], 'Maintain the inspection station')
        self.assertEqual(apply_labels(model)['labels']['F0'], 'MaintainStation')
        self.assertEqual(model, prior)
        self.assertTrue(all(' ' in text for text in result['labels'].values()))


if __name__ == '__main__':
    unittest.main()
