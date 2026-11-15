"""Request isolation and existing-verdict preservation at the public adapter boundary."""
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile
import signal
import subprocess
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hosted import runtime as rt


class HostedRuntimeTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        env = patch.dict(os.environ, CSE_JOB_ROOT=str(self.base / 'jobs'))
        env.start()
        self.addCleanup(env.stop)

    def fixture(self, name):
        return json.loads((ROOT / 'examples' / name).read_text())

    def synthetic_script(self, source):
        repo = self.base / 'synthetic-runtime'
        (repo / 'scripts').mkdir(parents=True)
        (repo / 'hosted').mkdir()
        (repo / 'hosted/job.py').write_bytes((ROOT / 'hosted/job.py').read_bytes())
        (repo / 'scripts/prose.py').write_text(source)
        return repo

    def test_queue_retains_existing_result_and_required_failure(self):
        model = self.fixture('queueing/service-pool.json')
        result = rt.record_check('queues', model, ['Replay', 'Stationary'])
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['report']['acceptance'], 'not_evaluated')
        missing = rt.record_check('queues', model, ['Missing'])
        self.assertNotEqual(missing['status'], 'pass')
        self.assertFalse((self.base / 'jobs/request').exists())

    def test_measures_and_failure_records_use_existing_checkers(self):
        for operation, fixture in [('measures', 'measurement-definitions/request-duration-v1.json'),
                                   ('failures', 'failure-analysis/qualitative.json')]:
            with self.subTest(operation=operation):
                result = rt.record_check(operation, self.fixture(fixture))
                self.assertEqual(result['status'], 'pass', result)
                self.assertEqual(result['acceptance'], 'not_evaluated')

    def test_untrusted_paths_arguments_and_nonfinite_records_refuse(self):
        for name in ['../private.json', '/etc/passwd', '--help', 'a/b.json', 'a\\b.json', 'a..json']:
            with self.subTest(name=name):
                self.assertEqual(rt.run('prose.py', {name: '{}'}, [])['status'], 'error')
        self.assertEqual(rt.run('sh', {'record.json': '{}'}, [])['status'], 'error')
        self.assertEqual(rt.record_check('queues', {'number': float('nan')})['status'], 'error')
        self.assertEqual(rt.record_check('queues', {}, ['--help'])['status'], 'error')

    def test_oversized_input_refuses_before_writing(self):
        result = rt.run('prose.py', {'report.txt': 'x' * (rt.MAX_INPUT + 1)}, [])
        self.assertEqual(result['status'], 'error')
        self.assertFalse((self.base / 'jobs/request').exists())

    def test_public_reference_reader_is_scoped_and_complete(self):
        self.assertEqual(len(rt.SKILLS), 11)
        for name in rt.SKILLS:
            self.assertEqual(rt.guidance(name)['status'], 'pass')
        for path in ['../LICENSE', '/etc/passwd', 'plugin.json', 'docs/../LICENSE', 'skills/nope.md']:
            self.assertEqual(rt.references(path)['status'], 'error')

    def test_concurrent_job_cannot_read_another_request(self):
        with rt.workspace() as (job, _):
            (job / 'private.txt').write_text('Retained only during the first request.')
            result = rt.run('prose.py', {'report.txt': 'A sentence.'}, [])
            self.assertEqual(result['error']['code'], 'busy')
            self.assertTrue((job / 'private.txt').exists())
        self.assertFalse(job.exists())

    def test_service_crash_cannot_release_an_active_jobs_isolation_lock(self):
        repo = self.synthetic_script("from pathlib import Path\nimport os,time\nPath('.ready').write_text(str(os.getpid()))\ntime.sleep(10)\n")
        code = ("from pathlib import Path;from hosted import runtime as rt;"
                f"rt.ROOT=Path({str(repo)!r});rt.run('prose.py',{{'report.txt':'test'}},[],timeout=15)")
        service = subprocess.Popen([sys.executable, '-c', code], cwd=ROOT,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        job_pid = None
        try:
            marker = self.base / 'jobs/request/.ready'
            for _ in range(200):
                if marker.exists():
                    job_pid = int(marker.read_text())
                    break
                time.sleep(0.01)
            self.assertIsNotNone(job_pid, 'Synthetic isolated job did not start')
            service.kill()
            service.wait(timeout=2)
            result = rt.run('prose.py', {'report.txt': 'A separate request.'}, [])
            self.assertEqual(result['error']['code'], 'busy')
        finally:
            if service.poll() is None:
                service.kill()
                service.wait(timeout=2)
            if job_pid is not None:
                try:
                    os.killpg(job_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_timeout_does_not_pass_and_removes_request_files(self):
        repo = self.synthetic_script("import time\ntime.sleep(10)\nprint('{\"status\":\"pass\"}')\n")
        with patch.object(rt, 'ROOT', repo):
            result = rt.run('prose.py', {'report.txt': 'input'}, [], timeout=0.05)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['error']['code'], 'time_limit')
        self.assertFalse((self.base / 'jobs/request').exists())

    def test_unusable_or_oversized_output_never_passes(self):
        for source in ["print('not json')", "print('{\"status\":\"pass\"}');raise SystemExit(1)",
                       "import json;print(json.dumps({'status':'pass','large':'x'*1900000}))"]:
            repo = self.base / 'synthetic-runtime'
            if repo.exists():
                import shutil
                shutil.rmtree(repo)
            repo = self.synthetic_script(source)
            with patch.object(rt, 'ROOT', repo):
                result = rt.run('prose.py', {'report.txt': 'input'}, [])
            self.assertNotEqual(result['status'], 'pass', source[:50])

    def test_input_hashes_are_exact_and_stable_across_requests(self):
        files = {'report.txt': 'An exact source.\n'}
        args = ['report.txt', '--kind', 'description', '--json', '--document-words', '50']
        first = rt.run('prose.py', files, args)
        second = rt.run('prose.py', files, args)
        self.assertEqual(first, second)
        self.assertEqual(first['inputs']['report.txt'], sha256(files['report.txt'].encode()).hexdigest())
        self.assertEqual(first['report']['file'], str(self.base / 'jobs/request/report.txt'))

    def test_rendered_artifacts_return_bytes_without_retaining_files(self):
        repo = self.synthetic_script("from pathlib import Path\nimport json\nPath('output').mkdir()\nPath('output/diagram.svg').write_text('<svg/>')\nprint(json.dumps({'status':'pass'}))\n")
        with patch.object(rt, 'ROOT', repo):
            result = rt.run('prose.py', {'report.txt': 'input'}, [], artifacts=True)
        self.assertEqual(result['files'][0]['content'], '<svg/>')
        self.assertFalse((self.base / 'jobs/request').exists())


if __name__ == '__main__':
    unittest.main()
