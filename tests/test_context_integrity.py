"""Public context boundaries found by independent adversarial review."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import context
from verifier.sysml import CLASSES, JAR

spec = importlib.util.spec_from_file_location('context_review_fixtures', ROOT / 'tests/test_context_views.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class EmittedContextControls(unittest.TestCase):
    def test_unicode_and_indentation_count_against_the_actual_output_budget(self):
        native, profile, _, evidence, _ = fixtures.fixture()
        profile['terms']['T_HANDOFF']['definition'] = '定義' * 700
        result = context.assemble_context(native, profile=profile, element_id='S_HANDOFF',
                                          source_evidence=evidence)
        compact_size = len(json.dumps(result, ensure_ascii=False).encode())
        limit = compact_size + 100
        self.assertGreater(len((json.dumps(result, sort_keys=True, indent=2) + '\n').encode()), limit)
        with patch('verifier.context.MAX_OUTPUT_BYTES', limit):
            refused = context.assemble_context(native, profile=profile, element_id='S_HANDOFF',
                                               source_evidence=evidence)
        self.assertEqual(refused['status'], 'error')
        self.assertEqual(refused['findings'][0]['rule'], 'context_output')
        self.assertLessEqual(len(context.render_context_json(refused).encode()), limit)


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(),
                     'Install the pinned parser for public context integrity controls')
class PublicContextControls(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_cli_unicode_output_is_refused_at_the_advertised_byte_cap(self):
        model = self.directory / 'unicode.sysml'
        model.write_text('package UnicodeProbe { part def Unit; part unit : Unit { '
                         'doc description /*' + '中' * 1_400_000 + '*/ } }', encoding='utf-8')
        profile = {'version': 'foundation-1.0', 'source_sha256': sha256(model.read_bytes()).hexdigest(),
                   'terms': {'T': {'namespace': 'Synthetic', 'revision': '1', 'label': 'unit',
                                   'definition': 'A synthetic resource.', 'kind': 'resource'}},
                   'elements': {'R': {'kind': 'resource', 'term': 'T', 'native_name': 'UnicodeProbe::unit'}},
                   'relations': [], 'use_cases': {}, 'allocations': {}, 'capabilities': {}}
        selected = self.directory / 'profile.json'
        selected.write_text(json.dumps(profile))
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/sysml_view.py'),
                                 str(model), '--profile', str(selected), '--element', 'R'],
                                cwd=self.directory, capture_output=True, timeout=90)
        self.assertEqual(result.returncode, 1, result.stderr.decode())
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'error')
        self.assertEqual(report['findings'][0]['rule'], 'context_output')
        self.assertLessEqual(len(result.stdout), context.MAX_OUTPUT_BYTES)

    def test_invalid_native_input_keeps_diagnostics_with_source_arguments(self):
        model = self.directory / 'broken.sysml'
        model.write_text('package Broken { requirement <R> Invalid { whoops invalid syntax } }')
        alone = context.assembled_context(model, short_id='R')
        extra = context.assembled_context(model, short_id='R',
                    sources={'SRC': ROOT / 'examples/meaning-context/brief.txt'})
        self.assertEqual(alone['status'], 'error')
        self.assertEqual(extra['status'], 'error')
        self.assertTrue(alone['parser_issues'])
        self.assertEqual(extra['parser_issues'], alone['parser_issues'])
        self.assertEqual(extra['findings'], alone['findings'])

    def test_public_entrypoint_refuses_replaced_fifo_without_blocking(self):
        model = self.directory / 'swap.sysml'
        model.write_text('package Swap { part def Unit; part unit : Unit; }')
        worker = '''import json,os,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
from verifier import context
real = context.capture_model_inputs
model = Path(sys.argv[2])
def replace(paths):
    captured = real(paths)
    model.unlink()
    os.mkfifo(model)
    return captured
with patch('verifier.context.capture_model_inputs', side_effect=replace):
    print(json.dumps(context.assembled_context(model, native_name='Swap::unit')))
'''
        try:
            result = subprocess.run([sys.executable, '-B', '-c', worker, str(ROOT), str(model)],
                                    cwd=self.directory, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['status'], 'error')
            self.assertEqual(report['provenance']['input_stability'], 'error')
            self.assertEqual(report['concepts'], {})
        finally:
            if model.exists():
                model.unlink()

    def test_authored_package_clock_is_retained_with_its_requirement(self):
        example = ROOT / 'examples/meaning-context'
        report = context.assembled_context(example / 'handoff.sysml',
                    profile_path=example / 'handoff.english.json', element_id='S_HANDOFF',
                    sources={'SYN_HANDOFF': example / 'brief.txt'})
        self.assertEqual(report['status'], 'pass', report['findings'])
        clocks = [doc for doc in report['native_context']['documents'] if doc.get('name') == 'cseClock']
        self.assertEqual(len(clocks), 1)
        self.assertEqual(clocks[0]['owner'], 'HandoffStudy')
        self.assertIn('period 1 second', clocks[0]['body'])
        self.assertEqual(report['semantic_review'], 'not_run')


if __name__ == '__main__':
    unittest.main()
