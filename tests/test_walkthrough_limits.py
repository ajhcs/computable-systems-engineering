"""Characterize limitations using only the public dummy fixtures.

These tests document current behavior, including known inadequacies. They are
not acceptance tests for independent holds or recovery. A future repair should
replace the affected characterization and update its documented claim boundary.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prototypes.repair_reuse import Store
from prototypes.repair_reuse_observer import observe
from verifier.sysml import CLASSES, JAR, check_sysml

EXAMPLE = ROOT / 'examples/prototype-evaluation'
MODELS = [EXAMPLE / 'harness.sysml', EXAMPLE / 'authorization.sysml']
MANIFEST = json.loads((EXAMPLE / 'strict-manifest.json').read_text())
PREFIX = 'DummyRehearsal::probe::'
PARSER = JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file()


@unittest.skipUnless(PARSER, 'Install the pinned SysML parser')
class WalkthroughLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        cls.compiled = check_sysml(MODELS, manifest=MANIFEST)
        if cls.compiled['status'] != 'pass':
            raise AssertionError(cls.compiled)
        cls.signals = {
            signal for result in cls.compiled['results'].values()
            for signal in result['binding'].values()
        }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'dummy.sqlite'
        self.store = Store(self.path, create=True)
        self.stock = self.store.session('STORES')
        self.tech = self.store.session('TECH')
        self.steward = self.store.session('STEWARD')

    def monitor(self):
        evidence = {
            'model_sha256': self.compiled['model_sha256'],
            'complete': True,
            'observations': [
                {key: value for key, value in observe(event).items()
                 if key in self.signals}
                for event in self.store.events()
            ],
        }
        return check_sysml(MODELS, manifest=MANIFEST, evidence=evidence, review=True)

    def clause(self, report, requirement):
        return report['results'][requirement + '__sampleRule']['check']

    def prepare_disposition(self):
        self.store.transact(self.steward, 'set_fixture_policy',
                            record='R-DISPOSE', not_before_tick=0)
        self.store.transact(self.steward, 'release_hold', record='R-DISPOSE')

    def test_reopen_and_inspect_before_retry_is_not_a_crash_or_full_scope_test(self):
        self.assertEqual(self.store.transact(
            self.tech, 'adjust', part='P-DEMO-001')['outcome'], 'denied')
        self.assertEqual(self.store.transact(
            self.stock, 'adjust', part='P-DEMO-001')['outcome'], 'committed')

        # Script a lost receipt after commit. No network loss or process crash.
        self.store = Store(self.path)
        count = self.store.transact(self.stock, 'count', part='P-DEMO-001')
        self.assertEqual((count['book'], count['physical']), (4, 4))
        retry = self.store.transact(self.stock, 'adjust', part='P-DEMO-001')
        self.assertEqual(retry['reason'], 'already_reconciled')
        with self.store.connection() as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM movements WHERE kind='adjust'"
            ).fetchone()[0], 1)
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM audit WHERE action='adjust'"
            ).fetchone()[0], 1)

        report = self.monitor()
        self.assertEqual(report['status'], 'unknown', report)
        self.assertEqual(self.clause(report, 'R_D_ADJUST_AUDIT')['status'], 'pass')
        revocation = self.clause(report, 'R_D_REVOKE')['results']['R_D_REVOKE__sampleRule']
        self.assertEqual(revocation['status'], 'unknown')
        self.assertEqual(revocation['coverage']['triggers'], 0)
        self.assertEqual(set(report['results']), set(self.compiled['results']))

    def test_boolean_hold_does_not_represent_two_independent_notices(self):
        # Two distinct notices exist only in this explicitly authored case.
        remaining_notices = {'SYNTHETIC-A', 'SYNTHETIC-B'}
        self.store.transact(self.steward, 'set_fixture_policy',
                            record='R-OTHER', not_before_tick=0)
        for _notice in sorted(remaining_notices):
            self.store.transact(self.steward, 'hold', record='R-OTHER')
        remaining_notices.remove('SYNTHETIC-A')
        self.store.transact(self.steward, 'release_hold', record='R-OTHER')

        # An adversarial probe bypasses the scripted stop for remaining B.
        self.assertEqual(self.store.transact(
            self.steward, 'dispose', record='R-OTHER')['outcome'], 'committed')
        event = self.store.events()[-1]
        self.assertEqual(remaining_notices, {'SYNTHETIC-B'})
        self.assertEqual(event['before']['record']['held'], 0)
        self.assertFalse(event['after']['record']['payload_present'])
        self.assertFalse(observe(event)[PREFIX + 'holdActive'])

        report = self.monitor()
        self.assertEqual(self.clause(report, 'R_D_HOLD')['status'], 'pass')
        self.assertEqual(report['status'], 'unknown', report)
        self.assertNotIn('fail', [value['check']['status']
                                  for value in report['results'].values()])
        # UNKNOWN here concerns unexercised clauses, not detection of notice B.
        self.assertEqual(self.store.transact(
            self.steward, 'restore', record='R-OTHER')['reason'], 'disposition_tombstone')

    def test_retry_does_not_repair_a_declared_export_left_by_fault(self):
        self.prepare_disposition()
        self.store = Store(self.path, faults=['leave_export'])
        self.store.transact(self.steward, 'dispose', record='R-DISPOSE')
        self.store = Store(self.path)
        self.assertEqual(self.store.transact(
            self.steward, 'dispose', record='R-DISPOSE')['reason'], 'already_disposed')
        self.assertEqual(self.store.events()[-1]['after']['copies'], [{'kind': 'export'}])
        report = self.monitor()
        self.assertEqual(report['status'], 'fail')
        counterexample = self.clause(report, 'R_D_COPIES')['results']['R_D_COPIES__sampleRule']
        self.assertEqual(counterexample['status'], 'fail')
        self.assertEqual(self.store.transact(
            self.steward, 'restore', record='R-DISPOSE')['reason'], 'disposition_tombstone')

    def test_retry_does_not_reconstruct_a_missing_adjustment_audit(self):
        self.store = Store(self.path, faults=['omit_adjustment_audit'])
        self.store.transact(self.stock, 'adjust', part='P-DEMO-001')
        self.store = Store(self.path)
        self.assertEqual(self.store.transact(
            self.stock, 'adjust', part='P-DEMO-001')['reason'], 'already_reconciled')
        with self.store.connection() as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM audit WHERE action='adjust'"
            ).fetchone()[0], 0)
        report = self.monitor()
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(self.clause(report, 'R_D_ADJUST_AUDIT')['status'], 'fail')

    def test_retry_does_not_reconstruct_a_missing_disposition_audit(self):
        self.prepare_disposition()
        self.store = Store(self.path, faults=['omit_disposition_audit'])
        self.store.transact(self.steward, 'dispose', record='R-DISPOSE')
        self.store = Store(self.path)
        self.assertEqual(self.store.transact(
            self.steward, 'dispose', record='R-DISPOSE')['reason'], 'already_disposed')
        self.assertEqual(self.store.events()[-1]['after']['copies'], [])
        with self.store.connection() as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM audit WHERE action='dispose'"
            ).fetchone()[0], 0)
        report = self.monitor()
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(self.clause(report, 'R_D_AUDIT')['status'], 'fail')


if __name__ == '__main__':
    unittest.main()
