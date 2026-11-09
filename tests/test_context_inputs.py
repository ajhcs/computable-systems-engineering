"""Captured-byte parsing, bounded snapshot integrity and native provenance."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.context_inputs import parse_captured
from verifier.foundation import Invalid
from verifier.sysml import CLASSES, JAR, _model_input, check_sysml
from verifier.workflow import capture_model_inputs


def parsed_snapshot(paths, **kwargs):
    _, files, _, digest = _model_input(paths)
    return {'status': 'pass', 'model_sha256': digest, 'model_files': files,
            'inventory': {}, 'findings': [], 'parser_issues': []}


class CapturedInputControls(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.model = self.base / 'model.sysml'
        self.model.write_text('package Snapshot { part def Unit; part unit : Unit; }')
        self.cache = self.base / 'cache'
        self.cache_patch = patch('verifier.context_inputs.CACHE', self.cache)
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)

    def capture(self):
        return capture_model_inputs(self.model)

    def test_original_can_be_removed_after_capture(self):
        captured, files, digest = self.capture()
        self.model.unlink()
        observed = []

        def parser(path, **kwargs):
            observed.append(path)
            self.assertTrue(path.is_relative_to(self.cache / 'context-scratch'))
            self.assertTrue(stat.S_ISREG(path.stat().st_mode))
            self.assertEqual(path.stat().st_mode & 0o077, 0)
            self.assertEqual(path.parent.stat().st_mode & 0o077, 0)
            self.assertEqual(path.read_bytes(), captured[0][1])
            self.assertEqual(kwargs, {'syntax_only': True, 'kind': None})
            return parsed_snapshot(path, **kwargs)

        result = parse_captured(captured, files, digest, parser=parser)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['model_sha256'], digest)
        self.assertEqual(result['model_files'], files)
        self.assertFalse(observed[0].exists())

    def test_bundle_digest_and_sources_return_to_original_labels(self):
        dependency = self.base / 'dependency.sysml'
        dependency.write_text('package Dependency {}')
        captured, files, digest = capture_model_inputs([self.model, dependency])
        before = deepcopy((captured, files))
        parser_reports = []

        def parser(paths, **kwargs):
            result = parsed_snapshot(paths, **kwargs)
            self.assertNotEqual(result['model_sha256'], digest)
            snapshot_files = result['model_files']
            result.update(inventory={'parts': [{'source': snapshot_files[0]['path'], 'line': 2}],
                                     'documents': [{'source': snapshot_files[1]['path'], 'line': 4}]},
                          parser_issues=[{'source': snapshot_files[1]['path'], 'line': 3,
                                          'column': 7, 'severity': 'WARNING', 'message': 'Retained warning'}],
                          findings=[{'source': snapshot_files[0]['path'], 'line': 1, 'detail': 'Retained finding'}])
            parser_reports.append(deepcopy(result))
            return result

        result = parse_captured(captured, files, digest, parser=parser)
        self.assertEqual(result['model_sha256'], digest)
        self.assertEqual(result['model_files'], files)
        self.assertEqual(result['snapshot_sha256'], parser_reports[0]['model_sha256'])
        self.assertEqual(result['inventory']['parts'][0]['source'], files[0]['path'])
        self.assertEqual(result['inventory']['documents'][0]['source'], files[1]['path'])
        self.assertEqual(result['findings'][0]['source'], files[0]['path'])
        self.assertEqual(result['parser_issues'][0]['source'], files[1]['path'])
        self.assertEqual(result['parser_issues'][0]['column'], 7)
        self.assertEqual((captured, files), before)

    def test_mismatched_parser_digest_is_an_input_error(self):
        def parser(paths, **kwargs):
            result = parsed_snapshot(paths, **kwargs)
            result['model_sha256'] = 'f' * 64
            return result

        with self.assertRaisesRegex(Invalid, 'snapshot revision'):
            parse_captured(*self.capture(), parser=parser)
        self.assertEqual(list((self.cache / 'context-scratch').iterdir()), [])

    def test_snapshot_drift_cannot_use_an_earlier_parser_digest(self):
        def parser(path, **kwargs):
            result = parsed_snapshot(path, **kwargs)
            path.write_text('package Changed {}')
            return result

        with self.assertRaisesRegex(Invalid, 'snapshot bytes changed'):
            parse_captured(*self.capture(), parser=parser)

    def test_snapshot_replacement_with_symlink_is_refused(self):
        def parser(path, **kwargs):
            result = parsed_snapshot(path, **kwargs)
            path.unlink()
            path.symlink_to(self.model)
            return result

        with self.assertRaises(OSError):
            parse_captured(*self.capture(), parser=parser)

    def test_missing_parser_retains_its_native_error(self):
        with patch('verifier.sysml.JAR', self.base / 'not-installed.jar'):
            result = parse_captured(*self.capture(), parser=check_sysml)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['model_sha256'], sha256(self.model.read_bytes()).hexdigest())
        self.assertIn('SysML pilot not installed', result['findings'][0]['detail'])

    def test_parser_exception_cleans_private_snapshots(self):
        parser = Mock(side_effect=RuntimeError('Parser stopped'))
        with self.assertRaisesRegex(RuntimeError, 'Parser stopped'):
            parse_captured(*self.capture(), parser=parser)
        self.assertEqual(list((self.cache / 'context-scratch').iterdir()), [])

    def test_snapshot_write_failure_cleans_private_directory(self):
        captured = self.capture()
        parser = Mock()
        with patch('verifier.context_inputs.Path.write_bytes', side_effect=OSError('No space left')):
            with self.assertRaisesRegex(OSError, 'No space left'):
                parse_captured(*captured, parser=parser)
        parser.assert_not_called()
        self.assertEqual(list((self.cache / 'context-scratch').iterdir()), [])

    def test_scratch_symlink_is_refused_before_parser(self):
        self.cache.mkdir()
        target = self.base / 'elsewhere'
        target.mkdir()
        (self.cache / 'context-scratch').symlink_to(target, target_is_directory=True)
        parser = Mock()
        with self.assertRaisesRegex(Invalid, 'must not be a symlink'):
            parse_captured(*self.capture(), parser=parser)
        parser.assert_not_called()
        self.assertEqual(list(target.iterdir()), [])

    def test_inconsistent_capture_metadata_is_refused_before_parser(self):
        captured, files, digest = self.capture()
        variants = [(captured, files, 'a' * 64),
                    ([(self.model, b'changed')], files, digest),
                    (captured, [], digest), ([], [], digest)]
        for arguments in variants:
            with self.subTest(arguments=arguments), self.assertRaises(Invalid):
                parse_captured(*arguments, parser=Mock(side_effect=AssertionError('Parser must not run')))

    def test_capture_byte_cap_is_retained(self):
        raw = b'x' * 5_000_001
        files = [{'path': 'oversized.sysml', 'sha256': sha256(raw).hexdigest()}]
        parser = Mock()
        with self.assertRaisesRegex(Invalid, 'exceeds 5 MB'):
            parse_captured([('oversized.sysml', raw)], files, files[0]['sha256'], parser=parser)
        parser.assert_not_called()


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(),
                     'Install the pinned SysML parser for native snapshot controls')
class NativeCapturedInputControls(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)

    def test_native_bundle_retains_original_file_and_record_provenance(self):
        base = ROOT / 'examples/configuration-review/connected'
        captured, files, digest = capture_model_inputs([base / 'current.sysml', base / 'library.sysml'])
        result = parse_captured(captured, files, digest, parser=check_sysml)
        self.assertEqual(result['status'], 'pass', result['findings'])
        self.assertEqual(result['model_files'], files)
        self.assertEqual(result['model_sha256'], digest)
        self.assertNotEqual(result['snapshot_sha256'], digest)
        original_labels = {entry['path'] for entry in files}
        for records in result['inventory'].values():
            for item in records:
                self.assertIn(item['source'], original_labels)
        connection = result['inventory']['connections'][0]
        self.assertEqual(connection['source'], str((base / 'current.sysml').relative_to(ROOT)))
        self.assertEqual(connection['line'], 7)

    def test_native_parser_failure_keeps_original_diagnostic_locations(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as temporary:
            good, bad = Path(temporary) / 'a.sysml', Path(temporary) / 'b.sysml'
            good.write_text('package Good {}\n')
            bad.write_text('package Bad {\nwhoops invalid syntax\n}\n')
            captured, files, digest = capture_model_inputs([bad, good])
            result = parse_captured(captured, files, digest, parser=check_sysml)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['model_files'], files)
        self.assertEqual(result['model_sha256'], digest)
        errors = [issue for issue in result['parser_issues'] if issue['severity'] == 'ERROR']
        self.assertTrue(errors)
        self.assertTrue(all(issue['source'] == files[1]['path'] for issue in errors))
        self.assertTrue(any(issue['line'] == 2 for issue in errors))

    def test_real_fifo_replacement_after_capture_does_not_block_parser(self):
        program = '''from pathlib import Path
import json, os, sys
from verifier.context_inputs import parse_captured
from verifier.foundation import read_regular
from verifier.sysml import check_sysml
from verifier.workflow import capture_model_inputs
model = Path(sys.argv[1])
captured, files, digest = capture_model_inputs(model)
model.unlink()
os.mkfifo(model)
result = parse_captured(captured, files, digest, parser=check_sysml)
try:
    read_regular(model, 5_000_000)
except ValueError:
    stability = 'refused_nonregular'
else:
    stability = 'unexpected_pass'
print(json.dumps({'status': result['status'], 'model_sha256': result['model_sha256'], 'stability': stability}))
'''
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as temporary:
            model = Path(temporary) / 'model.sysml'
            model.write_text('package FifoProbe { part def Unit; part unit : Unit; }')
            digest = sha256(model.read_bytes()).hexdigest()
            completed = subprocess.run([sys.executable, '-B', '-c', program, str(model)],
                                       cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                                       text=True, capture_output=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result, {'status': 'pass', 'model_sha256': digest,
                                  'stability': 'refused_nonregular'})


if __name__ == '__main__':
    unittest.main()
