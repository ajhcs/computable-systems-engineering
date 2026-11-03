"""Stale computation and drawing files cannot qualify a retained bundle."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import artifacts as a


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = {'version': a.VERSION, 'id': 'SyntheticDrawing', 'revision': '1',
                     'inputs': {'Model': 'model.txt', 'Generator': 'generator.py'},
                     'outputs': {'Figure': 'run/figure.svg', 'Checks': 'run/checks.json'}}
        (self.root / 'model.txt').write_text('Torque = K * current\n')
        (self.root / 'generator.py').write_text('# synthetic generator identity\n')
        self.path = self.root / 'plan.json'
        self.save_plan()

    def save_plan(self):
        self.path.write_text(json.dumps(self.plan) + '\n')
        self.digest = sha256(self.path.read_bytes()).hexdigest()

    def produce(self):
        (self.root / 'run').mkdir(exist_ok=True)
        (self.root / 'run/figure.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>K i</text></svg>\n')
        (self.root / 'run/checks.json').write_text('{"status":"fail","id":"ExampleLimit"}\n')

    def complete(self):
        start = a.begin(self.root, self.plan, self.digest)
        self.produce()
        return a.finish(self.root, self.plan, self.digest, start)

    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/artifacts.py'), *args,
                               '--root', str(self.root), '--plan', str(self.path)],
                              cwd=self.root, capture_output=True, text=True)

    def test_complete_bundle_is_fresh_without_upgrading_failed_engineering_check(self):
        receipt = self.complete()
        result = a.check(self.root, self.plan, self.digest, receipt)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['claim_scope'], 'declared_file_freshness_only')
        self.assertEqual(json.loads((self.root / 'run/checks.json').read_text())['status'], 'fail')

    def test_begin_rejects_old_output_even_when_its_content_is_plausible(self):
        self.produce()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            a.begin(self.root, self.plan, self.digest)

    def test_source_change_during_generation_prevents_completion(self):
        start = a.begin(self.root, self.plan, self.digest)
        self.produce()
        (self.root / 'model.txt').write_text('Torque = K * speed\n')
        with self.assertRaisesRegex(ValueError, 'Source changed'):
            a.finish(self.root, self.plan, self.digest, start)

    def test_every_declared_input_and_output_change_is_detected(self):
        receipt = self.complete()
        for name in [*self.plan['inputs'].values(), *self.plan['outputs'].values()]:
            path = self.root / name
            old = path.read_bytes()
            path.write_bytes(old + b'changed\n')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Stale'):
                a.check(self.root, self.plan, self.digest, receipt)
            path.write_bytes(old)
        self.assertEqual(a.check(self.root, self.plan, self.digest, receipt)['status'], 'pass')

    def test_missing_or_empty_output_cannot_complete(self):
        start = a.begin(self.root, self.plan, self.digest)
        with self.assertRaises(OSError):
            a.finish(self.root, self.plan, self.digest, start)
        self.produce()
        (self.root / 'run/checks.json').write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            a.finish(self.root, self.plan, self.digest, start)

    def test_receipt_cannot_omit_or_retarget_output(self):
        receipt = self.complete()
        for operation in ('remove', 'retarget'):
            bad = copy.deepcopy(receipt)
            if operation == 'remove':
                del bad['outputs']['Checks']
            else:
                bad['outputs']['Checks']['path'] = 'run/figure.svg'
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                a.check(self.root, self.plan, self.digest, bad)

    def test_started_receipt_cannot_be_used_as_completion(self):
        start = a.begin(self.root, self.plan, self.digest)
        self.produce()
        with self.assertRaisesRegex(ValueError, 'phase'):
            a.check(self.root, self.plan, self.digest, start)

    def test_invalid_scope_paths_and_duplicate_aliases_are_rejected(self):
        for path in ('../escape', '/absolute', 'a/../b', './model.txt', 'run//out', 'C:\\out', 'run/\nfile'):
            bad = copy.deepcopy(self.plan)
            bad['outputs']['Figure'] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                a.begin(self.root, bad, self.digest)
        for field in ('inputs', 'outputs'):
            bad = copy.deepcopy(self.plan)
            bad[field]['Alias'] = 'model.txt'
            with self.assertRaises(ValueError):
                a.begin(self.root, bad, self.digest)

    def test_symlink_leaf_and_parent_are_rejected(self):
        (self.root / 'alias').symlink_to(self.root / 'model.txt')
        (self.root / 'linked').symlink_to(self.root, target_is_directory=True)
        for name in ('alias', 'linked/model.txt'):
            bad = copy.deepcopy(self.plan)
            bad['inputs']['Model'] = name
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Symlink'):
                a.begin(self.root, bad, self.digest)

    def test_schema_and_resource_limits_fail_closed(self):
        for change in (lambda p: p.update(outputs={}), lambda p: p.update(version='future'),
                       lambda p: p.update(extra=True), lambda p: p.update(id=[])):
            bad = copy.deepcopy(self.plan)
            change(bad)
            with self.assertRaises(ValueError):
                a.begin(self.root, bad, self.digest)
        with patch.dict(a.LIMITS, file_bytes=3), self.assertRaises(ValueError):
            a.begin(self.root, self.plan, self.digest)
        with patch.dict(a.LIMITS, total_bytes=3), self.assertRaises(ValueError):
            a.begin(self.root, self.plan, self.digest)

    def test_duplicate_json_keys_are_refused(self):
        self.path.write_text('{"id":"One","id":"Two"}')
        with self.assertRaisesRegex(ValueError, 'duplicate JSON'):
            a.load(self.path)

    def test_cli_checks_are_read_only_and_receipts_are_never_overwritten(self):
        start, final = self.root / 'started.json', self.root / 'complete.json'
        result = self.cli('begin', '--out', str(start))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.produce()
        result = self.cli('finish', '--receipt', str(start), '--plan-sha256', self.digest, '--out', str(final))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        before = (final.read_bytes(), final.stat().st_mtime_ns)
        result = self.cli('check', '--receipt', str(final), '--plan-sha256', self.digest)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.cli('finish', '--receipt', str(start), '--plan-sha256', self.digest, '--out', str(final))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((final.read_bytes(), final.stat().st_mtime_ns), before)

    def test_cli_scope_narrowing_and_failed_finish_create_no_receipt(self):
        start, final = self.root / 'started.json', self.root / 'complete.json'
        self.assertEqual(self.cli('begin', '--out', str(start)).returncode, 0)
        result = self.cli('finish', '--receipt', str(start), '--plan-sha256', self.digest, '--out', str(final))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(final.exists())
        retained = self.digest
        del self.plan['outputs']['Checks']
        self.save_plan()
        result = self.cli('finish', '--receipt', str(start), '--plan-sha256', retained, '--out', str(final))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('retained digest', result.stdout)
        self.assertFalse(final.exists())

    def test_receipt_path_cannot_occupy_declared_output(self):
        (self.root / 'run').mkdir()
        result = self.cli('begin', '--out', str(self.root / 'run/checks.json'))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'run/checks.json').exists())


if __name__ == '__main__':
    unittest.main()
