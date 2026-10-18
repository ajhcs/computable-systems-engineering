"""Cross-process parser serialization and portable native invocation contracts."""
from contextlib import contextmanager, ExitStack
from hashlib import sha256
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import verifier.sysml as engine


def hold_lock(path, ready, release):
    deadline = time.monotonic() + 8
    with engine._parser_lock(path, deadline, ['lock-worker'], 8):
        ready.write_text('locked', encoding='utf-8')
        while not release.exists():
            if time.monotonic() >= deadline:
                raise RuntimeError('Test lock holder exceeded its deadline')
            time.sleep(0.01)


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.tmp', prefix='portable-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.sequence = 0

    @contextmanager
    def holder(self, path):
        self.sequence += 1
        ready = self.base / ('ready' + str(self.sequence))
        release = self.base / ('release' + str(self.sequence))
        child = subprocess.Popen([sys.executable, '-B', str(Path(__file__)), '--hold-lock',
                                  str(path), str(ready), str(release)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 encoding='utf-8')
        try:
            deadline = time.monotonic() + 5
            while not ready.exists():
                if child.poll() is not None:
                    self.fail('Lock worker exited: ' + child.communicate()[1])
                if time.monotonic() >= deadline:
                    self.fail('Lock worker did not acquire the lock')
                time.sleep(0.01)
            yield
        finally:
            release.write_text('release', encoding='utf-8')
            try:
                _, errors = child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill(); child.communicate()
                self.fail('Lock worker did not stop')
            self.assertEqual(child.returncode, 0, errors)

    @contextmanager
    def parser_cache(self):
        cache = self.base / 'parser cache with spaces'
        classes = cache / 'classes'; classes.mkdir(parents=True)
        (classes / 'SysmlBridge.class').write_bytes(b'compiled fixture')
        source = cache / 'bridge.java'; source.write_bytes(b'fixture source')
        stamp = classes / 'SysmlBridge.source.sha256'
        stamp.write_text(sha256(source.read_bytes()).hexdigest(), encoding='utf-8')
        jar = cache / 'parser jar.jar'; jar.write_bytes(b'fixture jar')
        library = cache / 'library'; library.mkdir()
        values = dict(CACHE=cache, CLASSES=classes, JAR=jar, LIBRARY=library,
                      BRIDGE_SOURCE=source, BRIDGE_STAMP=stamp)
        with ExitStack() as stack:
            for key, value in values.items():
                stack.enter_context(patch.object(engine, key, value))
            yield values

    def test_actual_process_exclusion_timeout_and_later_acquisition(self):
        path = self.base / 'parser.lock'
        with self.holder(path):
            start = time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired):
                with engine._parser_lock(path, start + 0.15, ['java'], 0.15):
                    self.fail('Concurrent parser entered the critical section')
            self.assertGreaterEqual(time.monotonic() - start, 0.12)
        with engine._parser_lock(path, time.monotonic() + 2, ['java'], 2):
            pass

    def test_lock_content_survives_and_exception_releases_other_process(self):
        path = self.base / 'parser.lock'; path.write_bytes(b'preserve existing contents')
        with self.assertRaisesRegex(RuntimeError, 'inside parser'):
            with engine._parser_lock(path, time.monotonic() + 2, ['java'], 2):
                raise RuntimeError('inside parser')
        with self.holder(path):
            pass
        self.assertEqual(path.read_bytes(), b'preserve existing contents')

    def test_expired_deadline_does_not_enter_critical_section(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            with engine._parser_lock(self.base / 'parser.lock', time.monotonic() - 1, ['java'], 1):
                self.fail('Expired acquisition entered the parser')

    def test_lock_contention_never_launches_java(self):
        with self.parser_cache() as values, self.holder(values['CACHE'] / 'parser.lock'):
            with patch.object(engine.subprocess, 'run') as run:
                with self.assertRaises(subprocess.TimeoutExpired):
                    engine._parser_output('package Example {}', 0.1)
                run.assert_not_called()

    def test_command_preserves_space_paths_utf8_and_remaining_budget(self):
        with self.parser_cache() as values:
            completed = subprocess.CompletedProcess(['java'], 0,
                '{"text":"caf\u00e9 \u00b7 \u03b1"}'.encode('utf-8'), b'')
            with patch.object(engine.subprocess, 'run', return_value=completed) as run:
                result = engine._parser_output('package Example { /* caf\u00e9 \u00b7 \u03b1 */ }', 2)
            command = run.call_args.args[0]; kwargs = run.call_args.kwargs
            self.assertEqual(command[command.index('-cp') + 1],
                             str(values['CLASSES']) + os.pathsep + str(values['JAR']))
            self.assertIn('-Dstdout.encoding=UTF-8', command)
            self.assertIn('-Dstderr.encoding=UTF-8', command)
            self.assertNotIn('text', kwargs)
            self.assertNotIn('encoding', kwargs)
            self.assertEqual(kwargs['input'], 'package Example { /* caf\u00e9 \u00b7 \u03b1 */ }'.encode('utf-8'))
            self.assertEqual(result['text'], 'caf\u00e9 \u00b7 \u03b1')
            self.assertGreater(kwargs['timeout'], 0)
            self.assertLessEqual(kwargs['timeout'], 2)
            self.assertFalse(kwargs.get('shell', False))

    def test_malformed_transport_is_a_structured_error_on_zero_and_nonzero_exit(self):
        cases = [(None, b''), (b'{}', None), (b'\xe9', b''),
                 (b'{}', b'\xe9'), ('{}', b''), (b'{}', '')]
        with self.parser_cache():
            path = self.base / 'input.sysml'
            path.write_text('package Example {}', encoding='utf-8')
            for code in (0, 1):
                for stdout, stderr in cases:
                    with self.subTest(code=code, stdout=stdout, stderr=stderr):
                        completed = subprocess.CompletedProcess(['java'], code, stdout, stderr)
                        with patch.object(engine.subprocess, 'run', return_value=completed):
                            report = engine.check_sysml(path, syntax_only=True)
                        self.assertEqual(report['status'], 'error', report)
                        self.assertEqual(report['findings'][0]['code'], 'input_or_parser')

    def test_invalid_json_and_parser_exit_are_structured_errors(self):
        cases = [(0, b'not JSON', b''), (0, b'[]', b''),
                 (1, b'{}', 'caf\u00e9 \u00b7 \u03b1'.encode('utf-8'))]
        with self.parser_cache():
            path = self.base / 'input.sysml'
            path.write_text('package Example {}', encoding='utf-8')
            for code, stdout, stderr in cases:
                with self.subTest(code=code, stdout=stdout):
                    completed = subprocess.CompletedProcess(['java'], code, stdout, stderr)
                    with patch.object(engine.subprocess, 'run', return_value=completed):
                        report = engine.check_sysml(path, syntax_only=True)
                    self.assertEqual(report['status'], 'error', report)
                    self.assertEqual(report['findings'][0]['code'], 'input_or_parser')
                    if code:
                        self.assertIn('caf\u00e9 \u00b7 \u03b1', report['findings'][0]['detail'])

    @unittest.skipUnless(engine.JAR.is_file() and (engine.CLASSES / 'SysmlBridge.class').is_file(),
                         'Install the pinned SysML parser')
    def test_actual_java_stdout_and_stderr_use_utf8(self):
        # Obtain the production launch options, then exercise both real JVM pipes.
        with self.parser_cache():
            with patch.object(engine.subprocess, 'run', return_value=
                              subprocess.CompletedProcess(['java'], 0, b'{}', b'')) as run:
                engine._parser_output('package Example {}', 2)
            options = run.call_args.args[0][1:run.call_args.args[0].index('-cp')]
        source = self.base / 'Utf8Probe.java'
        source.write_text('public class Utf8Probe { public static void main(String[] args) { '
                          'System.out.print("caf\u00e9 \u00b7 \u03b1"); System.err.print("caf\u00e9 \u00b7 \u03b1"); }}',
                          encoding='utf-8')
        compile_result = subprocess.run(['javac', '--release', '21', '-encoding', 'UTF-8', str(source)],
                                        capture_output=True, timeout=30, check=False)
        self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
        result = subprocess.run(['java', *options, '-cp', str(self.base), 'Utf8Probe'],
                                capture_output=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = 'caf\u00e9 \u00b7 \u03b1'.encode('utf-8')
        self.assertEqual(result.stdout, expected)
        self.assertEqual(result.stderr, expected)

    def test_java_timeout_releases_lock_to_another_process(self):
        with self.parser_cache() as values:
            with patch.object(engine.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['java'], 1)):
                with self.assertRaises(subprocess.TimeoutExpired):
                    engine._parser_output('package Example {}', 1)
            with self.holder(values['CACHE'] / 'parser.lock'):
                pass

    def test_windows_byte_zero_nonblocking_busy_and_fatal_error_contract(self):
        backend = SimpleNamespace(LK_NBLCK=2, LK_UNLCK=0, locking=Mock())
        lock = SimpleNamespace(seek=Mock(), fileno=lambda: 42)
        with patch.dict(sys.modules, {'msvcrt': backend}), patch.object(engine.os, 'name', 'nt'):
            self.assertTrue(engine._try_parser_lock(lock))
            lock.seek.assert_called_with(0)
            backend.locking.assert_called_with(42, 2, 1)
            engine._release_parser_lock(lock)
            backend.locking.assert_called_with(42, 0, 1)
            backend.locking.side_effect = OSError(errno.EACCES, 'busy')
            self.assertFalse(engine._try_parser_lock(lock))
            backend.locking.side_effect = OSError(errno.EBADF, 'bad descriptor')
            with self.assertRaises(OSError): engine._try_parser_lock(lock)

    def test_module_import_does_not_require_posix_fcntl(self):
        result = subprocess.run([sys.executable, '-B', '-c',
            "import sys;sys.modules['fcntl']=None;import verifier.sysml"],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(engine.JAR.is_file() and (engine.CLASSES / 'SysmlBridge.class').is_file(),
                         'Install the pinned SysML parser')
    def test_actual_native_utf8_document_in_space_path(self):
        path = self.base / 'native model with spaces.sysml'
        path.write_text('package UnicodeCase { doc /* caf\u00e9 \u00b7 \u03b1 */ part def Equipment; part unit : Equipment; }',
                        encoding='utf-8')
        report = engine.check_sysml(path, syntax_only=True)
        self.assertEqual(report['status'], 'pass', report)
        self.assertTrue(any('caf\u00e9 \u00b7 \u03b1' in d.get('body', '') for d in report['inventory']['documents']))


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--hold-lock':
        hold_lock(*(Path(p) for p in sys.argv[2:]))
    else:
        unittest.main()
