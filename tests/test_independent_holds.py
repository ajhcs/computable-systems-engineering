"""Synthetic, bounded hold identities and independent observation checks."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prototypes.repair_reuse import DEFAULT_HOLD_ID, HOLD_LIMIT, Store
from prototypes.repair_reuse_observer import observe


class IndependentHoldTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.path = self.directory / 'dummy.sqlite'
        self.store = Store(self.path, create=True)
        self.steward = self.store.session('STEWARD')
        self.tech = self.store.session('TECH')

    def change(self, action, hold_id, record='R-OTHER', token=None):
        return self.store.transact(token or self.steward, action, record=record, hold_id=hold_id)

    def holds(self, record='R-OTHER'):
        with self.store.connection() as db:
            return dict(db.execute('SELECT hold_id,active FROM holds WHERE record_id=?', (record,)))

    def pair(self):
        for hold in ('A','B'):
            self.assertEqual(self.change('hold',hold)['outcome'],'committed')

    def test_disposition_blocked_until_last_named_hold_is_released(self):
        self.pair()
        self.store.transact(self.steward,'set_fixture_policy',record='R-OTHER',not_before_tick=0)
        self.change('release_hold','A')
        self.assertEqual(self.holds(),{'A':0,'B':1})
        self.assertEqual(self.store.transact(self.steward,'dispose',record='R-OTHER')['reason'],'retention_hold')
        self.change('release_hold','B')
        self.assertEqual(self.store.transact(self.steward,'dispose',record='R-OTHER')['outcome'],'committed')

    def test_legacy_release_names_only_default_hold(self):
        self.change('hold','EXTRA',record='R-DISPOSE')
        self.store.transact(self.steward,'release_hold',record='R-DISPOSE')
        self.assertEqual(self.holds('R-DISPOSE'),{DEFAULT_HOLD_ID:0,'EXTRA':1})

    def test_duplicate_apply_and_release_are_no_change_without_new_audit(self):
        self.change('hold','A')
        self.assertEqual(self.change('hold','A')['reason'],'already_held')
        self.change('release_hold','A')
        self.assertEqual(self.change('release_hold','A')['reason'],'already_released')
        self.assertEqual(self.change('hold','A')['reason'],'hold_id_reused')
        with self.store.connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM audit WHERE action IN ('hold','release_hold')").fetchone()[0],2)

    def test_unknown_and_wrong_record_release_preserve_all_holds(self):
        self.pair()
        self.assertEqual(self.change('release_hold','ABSENT')['reason'],'unknown_hold')
        self.assertEqual(self.change('release_hold','A',record='R-EMPTY')['reason'],'unknown_hold')
        self.assertEqual(self.holds(),{'A':1,'B':1})
        self.change('hold','A',record='R-EMPTY')
        self.change('release_hold','A',record='R-EMPTY')
        self.assertEqual(self.holds(),{'A':1,'B':1})

    def test_unpermitted_and_revoked_fixture_sessions_cannot_release_holds(self):
        self.pair()
        self.assertEqual(self.change('release_hold','A',token=self.tech)['outcome'],'denied')
        admin=self.store.session('ADMIN')
        self.store.transact(admin,'revoke',subject='STEWARD')
        self.assertEqual(self.change('release_hold','A')['outcome'],'denied')
        self.assertEqual(self.holds(),{'A':1,'B':1})

    def test_reopen_preserves_distinct_hold_states(self):
        self.pair();self.change('release_hold','A')
        self.store=Store(self.path)
        self.assertEqual(self.holds(),{'A':0,'B':1})
        self.assertEqual(self.change('release_hold','A')['reason'],'already_released')
        self.assertEqual(self.holds(),{'A':0,'B':1})

    def test_sql_audit_failure_rolls_back_release_and_capture(self):
        self.pair();count=len(self.store.events())
        with self.store.connection() as db:
            db.execute("CREATE TRIGGER fail_release BEFORE INSERT ON audit WHEN NEW.action='release_hold' BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.change('release_hold','A')
        self.assertEqual(self.holds(),{'A':1,'B':1})
        self.assertEqual(len(self.store.events()),count)

    def test_serialized_release_and_new_hold_preserve_remaining_hold(self):
        self.pair()
        def operation(action,hold):
            return Store(self.path).transact(self.steward,action,record='R-OTHER',hold_id=hold)
        with ThreadPoolExecutor(max_workers=2) as pool:
            release=pool.submit(operation,'release_hold','A')
            addition=pool.submit(operation,'hold','C')
            self.assertEqual(release.result()['outcome'],'committed')
            self.assertEqual(addition.result()['outcome'],'committed')
        self.assertEqual(self.holds(),{'A':0,'B':1,'C':1})

    def test_invalid_identity_cannot_create_a_transaction(self):
        for value in ['', ' ', 'A'*65, '\u00e9', True, 1, [], {}]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):self.change('hold',value)
        with self.assertRaises(ValueError):
            self.store.transact(self.steward,'read',record='R-OTHER',hold_id='A')
        self.assertEqual(self.store.events(),[])

    def test_bounded_history_does_not_reuse_released_notice_id(self):
        for i in range(HOLD_LIMIT):self.change('hold','H'+str(i))
        self.assertEqual(self.change('hold','OVER')['reason'],'hold_limit')
        self.change('release_hold','H0')
        self.assertEqual(self.change('hold','OVER')['reason'],'hold_limit')
        self.assertEqual(len(self.holds()),HOLD_LIMIT)
        self.assertTrue(observe(self.store.events()[-1])['DummyRehearsal::probe::unrelatedHoldsPreserved'])

    def test_old_database_is_refused_without_migration_or_mutation(self):
        old=self.directory/'old.sqlite'
        with sqlite3.connect(old) as db:
            db.execute('CREATE TABLE records(id TEXT, held INTEGER)')
            db.execute("INSERT INTO records VALUES('OLD',1)")
        before=old.read_bytes()
        with self.assertRaisesRegex(ValueError,'schema'):Store(old)
        self.assertEqual(old.read_bytes(),before)

    def test_complete_typed_hold_capture_is_required(self):
        self.pair();self.change('release_hold','A');event=self.store.events()[-1]
        changes=[lambda e:e.pop('hold_id'),lambda e:e['after'].pop('holds'),
                 lambda e:e.update(hold_id=None),lambda e:e['after']['holds'].append(deepcopy(e['after']['holds'][0])),
                 lambda e:e['after']['holds'][0].update(record_id='FOREIGN'),
                 lambda e:e['after']['holds'][0].update(active='unknown'),
                 lambda e:e['after']['record'].update(held=0)]
        for change in changes:
            broken=deepcopy(event);change(broken)
            with self.subTest(change=changes.index(change)):
                with self.assertRaises(ValueError):observe(broken)

    def test_faulty_release_remains_observable_in_typed_state(self):
        self.pair();self.store=Store(self.path,faults=['release_all_holds'])
        self.change('release_hold','A');event=self.store.events()[-1]
        self.assertEqual(self.holds(),{'A':0,'B':0})
        self.assertFalse(observe(event)['DummyRehearsal::probe::unrelatedHoldsPreserved'])


if __name__=='__main__':unittest.main()
