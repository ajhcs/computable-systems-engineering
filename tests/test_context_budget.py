"""Lossless context transport and actual public UTF-8 budget controls."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.context import assemble_context, render_context_json
from verifier.context_budget import (VERSION, compact_context, expand_context,
                                     render_compact_json)
from verifier.sysml import CLASSES, JAR
from verifier.views import view_sysml

spec = importlib.util.spec_from_file_location('context_budget_fixtures', ROOT / 'tests/test_context_views.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def source_report(limit=512):
    native, profile, _, evidence, _ = fixtures.fixture()
    profile['terms']['T_HANDOFF']['definition'] = (
        'Receipt of acknowledgement defines completion. Qualitative aim: reduce referral delay; '
        'no mandatory deadline is adopted. 定義')
    return assemble_context(native, profile=profile, element_id='S_HANDOFF',
                            limit=limit, source_evidence=evidence)


class CompactContextControls(unittest.TestCase):
    def test_round_trip_preserves_actual_meanings_roles_stages_and_omissions(self):
        for limit in (1, 512):
            with self.subTest(limit=limit):
                original = source_report(limit)
                before = deepcopy(original)
                package = compact_context(original)
                actual = expand_context(package)
                self.assertEqual(actual, original)
                self.assertEqual(original, before)
                self.assertEqual(package['status'], original['status'])
                self.assertEqual(actual['coverage'], original['coverage'])
                self.assertIn('reduce referral delay', actual['concepts']['T_HANDOFF']['definition'])
                self.assertEqual(actual['semantic_review'], 'not_run')
                self.assertEqual(actual['required_review'], 'not_evaluated')
                self.assertEqual(actual['acceptance'], 'not_evaluated')
                self.assertEqual(actual['checker_scope'], 'complete_supplied_model_unchanged')
                if limit == 512:
                    elements = actual['elements']['foundation']
                    self.assertEqual(elements['A_CLINIC']['native_name'], elements['R_CLINIC']['native_name'])
                    self.assertNotEqual(elements['A_CLINIC']['kind'], elements['R_CLINIC']['kind'])
                    self.assertEqual(actual['workflow_context']['evidence']['PLAN']['result'], 'not_run')
                    self.assertEqual(actual['workflow_context']['evidence']['REPORTED']['mode'], 'assessment')
                    self.assertTrue(any('unit second' in d['body'] for d in actual['native_context']['documents']))
                else:
                    self.assertFalse(actual['coverage']['complete'])
                    self.assertIn('workflow:R_COMPLETE', actual['coverage']['omitted_ids'])

    def test_complete_repeated_values_are_deduplicated_and_deterministic(self):
        report = source_report(1)
        report['duplicate_warning_records'] = [deepcopy(report['findings']) for _ in range(8)]
        a, b = compact_context(report), compact_context(report)
        self.assertEqual(a, b)
        self.assertTrue(a['records'])
        original_bytes = len(json.dumps(report, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
        self.assertLess(len(render_compact_json(a).encode()), original_bytes)
        self.assertEqual(expand_context(a), report)

    def test_exact_unicode_byte_boundary_includes_metadata_and_newline(self):
        report = source_report()
        report['unicode_source_note'] = '工程定義' * 600
        size = compact_context(report)['budget']['emitted_bytes']
        # The requested limit's shorter digit width can reduce its own encoding.
        for _ in range(4):
            package = compact_context(report, size)
            size = package['budget']['emitted_bytes']
        package = compact_context(report, size)
        raw = render_context_json(package).encode('utf-8')
        self.assertEqual(len(raw), size)
        self.assertEqual(package['budget']['emitted_bytes'], size)
        self.assertEqual(raw[-1:], b'\n')
        self.assertIn('工程定義'.encode(), raw)
        refused = compact_context(report, size - 1)
        self.assertEqual(refused['budget']['status'], 'refused')
        self.assertLessEqual(len(render_compact_json(refused).encode()), size - 1)
        self.assertNotIn('context', refused)
        self.assertNotIn('records', refused)
        self.assertFalse(refused['coverage']['complete'])

    def test_refusal_cannot_promote_failed_or_unreviewed_source_to_success(self):
        for status in ('pass', 'unknown', 'unsupported', 'fail', 'error'):
            with self.subTest(status=status):
                original = source_report()
                original['status'] = status
                refusal = compact_context(original, 1024)
                self.assertNotEqual(refusal['status'], 'pass')
                if status in ('unsupported', 'fail', 'error'):
                    self.assertEqual(refusal['status'], status)
                self.assertEqual(refusal['required_review'], 'not_evaluated')
                self.assertIn('independent required-check scope is unchanged', refusal['findings'][0]['detail'])
                self.assertLessEqual(len(render_context_json(refusal).encode()), 1024)

    def test_invalid_requested_limits_are_explicit_errors(self):
        for limit in (True, False, 0, 1023, 8_000_001, '12000', 2048.0):
            with self.subTest(limit=limit):
                package = compact_context(source_report(), limit)
                self.assertEqual(package['status'], 'error')
                self.assertEqual(package['budget']['status'], 'error')
                self.assertIsNone(package['budget']['max_bytes'])
                self.assertNotIn('context', package)

    def test_authored_marker_objects_are_escaped_not_interpreted(self):
        for value in ({'$ref': 'authored value'}, {'$literal': {'$ref': 'authored value'}}):
            original = {'status': 'unknown', 'authored': [value, value]}
            package = compact_context(original)
            self.assertEqual(expand_context(package), original)

    def test_expansion_rejects_missing_cyclic_and_digest_changed_references(self):
        base = compact_context(source_report(1))
        self.assertTrue(base['records'])
        for replacement in ({'$ref': 'absent'}, {'$ref': next(iter(base['records']))}):
            package = deepcopy(base)
            identity = next(iter(package['records']))
            package['records'][identity] = replacement
            with self.assertRaises(ValueError):
                expand_context(package)
        modified = deepcopy(base)
        modified['source_report_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            expand_context(modified)
        with self.assertRaises(ValueError):
            expand_context(compact_context(source_report(), 1024))

    def test_expansion_work_cap_rejects_without_partial_result(self):
        package = compact_context(source_report())
        with patch('verifier.context_budget.MAX_NODES', 8):
            with self.assertRaises(ValueError):
                expand_context(package)

    def test_public_api_only_packages_an_explicit_request(self):
        original = source_report(1)
        with patch('verifier.views.check_sysml', return_value={'status': 'not_run', 'findings': []}) as legacy:
            self.assertEqual(view_sysml('synthetic.sysml', 'R')['status'], 'not_run')
            legacy.assert_called_once()
        with patch('verifier.context.assembled_context', return_value=original) as assembled:
            self.assertEqual(view_sysml('synthetic.sysml', 'R', max_bytes=20000), original)
            self.assertEqual(assembled.call_args.kwargs['max_bytes'], 20000)
            self.assertIs(assembled.call_args.kwargs['compact'], False)
        native, profile, _, evidence, _ = fixtures.fixture()
        normal = assemble_context(native, profile=profile, element_id='S_HANDOFF', source_evidence=evidence)
        compact = assemble_context(native, profile=profile, element_id='S_HANDOFF',
                                   source_evidence=evidence, compact=True)
        self.assertEqual(normal['version'], 'assembled-context-1.0')
        self.assertEqual(compact['version'], VERSION)
        self.assertEqual(expand_context(compact), normal)


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(),
                     'Install the pinned parser for compact CLI integration controls')
class CompactContextCLIControls(unittest.TestCase):
    def invoke(self, *extra):
        args = [sys.executable, '-B', str(ROOT / 'scripts/sysml_view.py'),
                'examples/meaning-context/handoff.sysml', '--element', 'S_HANDOFF',
                '--profile', 'examples/meaning-context/handoff.english.json',
                '--source', 'SYN_HANDOFF=examples/meaning-context/brief.txt', *extra]
        return subprocess.run(args, cwd=ROOT, capture_output=True, timeout=90)

    def test_actual_cli_full_and_compact_payloads_round_trip(self):
        full = self.invoke()
        compact = self.invoke('--compact', '--max-bytes', '40000')
        self.assertEqual(full.returncode, 0, full.stderr.decode())
        self.assertEqual(compact.returncode, 0, compact.stderr.decode())
        original, package = json.loads(full.stdout), json.loads(compact.stdout)
        self.assertEqual(expand_context(package), original)
        self.assertEqual(len(compact.stdout), package['budget']['emitted_bytes'])
        self.assertLessEqual(len(compact.stdout), 40000)
        self.assertEqual(full.stdout.decode(), render_context_json(original))

    def test_actual_cli_budget_alone_enables_packaging_and_refuses_whole_view(self):
        actual = self.invoke('--max-bytes', '1024')
        self.assertEqual(actual.returncode, 1, actual.stderr.decode())
        package = json.loads(actual.stdout)
        self.assertEqual(package['version'], VERSION)
        self.assertEqual(package['budget']['status'], 'refused')
        self.assertLessEqual(len(actual.stdout), 1024)
        self.assertNotIn('context', package)


if __name__ == '__main__':
    unittest.main()
