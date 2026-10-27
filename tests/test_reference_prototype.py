"""Transaction behavior of the optional dummy reference application."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sys,tempfile,unittest
import sqlite3
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prototypes.repair_reuse import Store,observe,exercise


class ReferencePrototypeTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.tmp')
        self.path=Path(self.temp.name)/'dummy.sqlite'
        self.store=Store(self.path,create=True)
        self.stock=self.store.session('STORES');self.tech=self.store.session('TECH')
        self.admin=self.store.session('ADMIN');self.steward=self.store.session('STEWARD')

    def tearDown(self):self.temp.cleanup()

    def part(self,name='P-DEMO-001'):
        with self.store.connection() as db:return dict(db.execute('SELECT * FROM parts WHERE id=?',(name,)).fetchone())

    def prepare_disposition(self):
        self.store.transact(self.steward,'set_fixture_policy',record='R-DISPOSE',not_before_tick=0)
        self.store.transact(self.steward,'release_hold',record='R-DISPOSE')

    def test_discrepancy_blocks_issue_and_authorized_adjustment_is_audited(self):
        r=self.store.transact(self.stock,'issue',part='P-DEMO-001',quantity=1)
        self.assertEqual(r['reason'],'stock_discrepancy');self.assertEqual(self.part()['book'],5)
        r=self.store.transact(self.stock,'adjust',part='P-DEMO-001')
        self.assertEqual(r['outcome'],'committed');self.assertEqual(self.part()['book'],4)
        event=self.store.events()[-1];signals=observe(event)
        self.assertTrue(signals['DummyRehearsal::probe::stockMismatch'])
        self.assertTrue(signals['DummyRehearsal::probe::adjustmentAuditRecorded'])
        self.assertEqual(event['after']['movements'][0]['quantity'],-1)

    def test_unapproved_adjustment_does_not_change_stock(self):
        r=self.store.transact(self.tech,'adjust',part='P-DEMO-001')
        self.assertEqual(r['outcome'],'denied');self.assertEqual(self.part()['book'],5)
        self.assertFalse(observe(self.store.events()[-1])['DummyRehearsal::probe::adjustmentCommitted'])

    def test_reservation_and_issue_preserve_quantity_and_available_bounds(self):
        self.store.transact(self.stock,'adjust',part='P-DEMO-001')
        self.store.transact(self.stock,'reserve',part='P-DEMO-001',quantity=3)
        self.assertEqual(self.store.transact(self.tech,'issue',part='P-DEMO-001',quantity=2)['reason'],'insufficient_available')
        self.store.transact(self.stock,'issue_reserved',part='P-DEMO-001',quantity=2)
        self.assertEqual(self.part(),{'id':'P-DEMO-001','book':2,'physical':2,'reserved':1})

    def test_invalid_quantities_are_rejected_without_transaction_or_mutation(self):
        for quantity in [0,-1,1.2,True,'1']:
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):self.store.transact(self.stock,'issue',part='P-RACE',quantity=quantity)
        self.assertEqual(self.part('P-RACE')['book'],1);self.assertEqual(self.store.events(),[])

    def test_idempotent_request_replay_and_conflicting_payload(self):
        self.store.transact(self.stock,'issue',part='P-RACE',quantity=1,request_id='REQ')
        self.assertEqual(self.store.transact(self.stock,'issue',part='P-RACE',quantity=1,request_id='REQ')['outcome'],'replay')
        self.assertEqual(self.store.transact(self.stock,'issue',part='P-RACE',quantity=2,request_id='REQ')['reason'],'request_id_conflict')
        self.assertEqual(self.part('P-RACE')['book'],0)
        self.assertFalse(observe(self.store.events()[1])['DummyRehearsal::probe::issueCommitted'])

    def test_concurrent_connections_cannot_issue_the_same_last_unit_twice(self):
        def issue(i):return Store(self.path).transact(self.stock,'issue',part='P-RACE',quantity=1,request_id='R'+str(i))
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(issue,range(2)))
        self.assertEqual(sum(r['outcome']=='committed' for r in results),1)
        self.assertEqual(self.part('P-RACE')['physical'],0)
        self.assertEqual([e['sequence'] for e in self.store.events()],[1,2])

    def test_revocation_and_regrant_do_not_revalidate_an_old_session(self):
        self.assertIn('payload',self.store.transact(self.tech,'read',record='R-DEMO-001'))
        self.store.transact(self.admin,'revoke',subject='TECH')
        self.assertNotIn('payload',self.store.transact(self.tech,'read',record='R-DEMO-001'))
        self.assertTrue(observe(self.store.events()[-1])['DummyRehearsal::probe::revocationEffective'])
        self.store.transact(self.admin,'grant_read',subject='TECH',scope='workshop')
        self.assertNotIn('payload',self.store.transact(self.tech,'read',record='R-DEMO-001'))
        fresh=self.store.session('TECH')
        self.assertIn('payload',self.store.transact(fresh,'read',record='R-DEMO-001'))
        self.assertEqual(self.store.transact(fresh,'issue',part='P-RACE',quantity=1)['outcome'],'denied')

    def test_record_class_scope_and_empty_payload_are_observed_correctly(self):
        self.assertNotIn('payload',self.store.transact(self.tech,'read',record='R-OTHER'))
        result=self.store.transact(self.tech,'read',record='R-EMPTY')
        self.assertEqual(result['payload'],'')
        self.assertTrue(observe(self.store.events()[-1])['DummyRehearsal::probe::readServed'])

    def test_hold_overrides_known_fixture_basis_and_authority(self):
        self.store.transact(self.steward,'set_fixture_policy',record='R-DISPOSE',not_before_tick=0)
        result=self.store.transact(self.steward,'dispose',record='R-DISPOSE')
        self.assertEqual(result['reason'],'retention_hold')
        signals=observe(self.store.events()[-1]);self.assertTrue(signals['DummyRehearsal::probe::retentionBasisKnown'])
        self.assertFalse(signals['DummyRehearsal::probe::dispositionCommitted'])

    def test_unknown_basis_and_early_fixture_eligibility_block_disposition(self):
        self.assertEqual(self.store.transact(self.steward,'dispose',record='R-OTHER')['reason'],'retention_basis_unknown')
        self.store.transact(self.steward,'set_fixture_policy',record='R-DISPOSE',not_before_tick=100)
        self.store.transact(self.steward,'release_hold',record='R-DISPOSE')
        self.assertEqual(self.store.transact(self.steward,'dispose',record='R-DISPOSE')['reason'],'fixture_eligibility_not_reached')

    def test_only_authorized_actor_can_dispose_and_all_declared_copies_are_removed(self):
        self.prepare_disposition()
        self.assertEqual(self.store.transact(self.stock,'dispose',record='R-DISPOSE')['outcome'],'denied')
        self.assertEqual(self.store.transact(self.steward,'dispose',record='R-DISPOSE')['outcome'],'committed')
        event=self.store.events()[-1];signals=observe(event)
        self.assertTrue(signals['DummyRehearsal::probe::dispositionCommitted'])
        self.assertTrue(signals['DummyRehearsal::probe::dispositionAuditRecorded'])
        self.assertTrue(signals['DummyRehearsal::probe::copiesAccounted'])
        self.assertFalse(event['after']['record']['payload_present']);self.assertEqual(event['after']['copies'],[])
        self.assertEqual(self.store.transact(self.steward,'restore',record='R-DISPOSE')['reason'],'disposition_tombstone')

    def test_fault_injected_audit_and_copy_failures_are_visible_in_actual_state(self):
        self.prepare_disposition();bad=Store(self.path,faults=['omit_disposition_audit','leave_export'])
        bad.transact(self.steward,'dispose',record='R-DISPOSE');event=bad.events()[-1];values=observe(event)
        self.assertTrue(values['DummyRehearsal::probe::dispositionCommitted'])
        self.assertFalse(values['DummyRehearsal::probe::dispositionAuditRecorded'])
        self.assertFalse(values['DummyRehearsal::probe::copiesAccounted'])
        self.assertEqual(event['after']['copies'],[{'kind':'export'}])

    def test_partial_disposition_sql_failure_rolls_back_content_copies_and_receipts(self):
        self.prepare_disposition();count=len(self.store.events())
        with self.store.connection() as db:
            db.execute("CREATE TRIGGER fail_copy_receipt BEFORE INSERT ON copy_dispositions WHEN NEW.kind='export' BEGIN SELECT RAISE(ABORT,'dummy failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.transact(self.steward,'dispose',record='R-DISPOSE')
        with self.store.connection() as db:
            self.assertIsNotNone(db.execute("SELECT payload FROM records WHERE id='R-DISPOSE'").fetchone()[0])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM copies WHERE record_id='R-DISPOSE'").fetchone()[0],3)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM tombstones").fetchone()[0],0)
        self.assertEqual(len(self.store.events()),count)

    def test_capture_does_not_retain_record_payloads_after_logical_disposition(self):
        with self.store.connection() as db:
            payloads=[r[0] for r in db.execute('SELECT payload FROM records WHERE payload IS NOT NULL')]
        events=exercise(self.store)
        import json
        serialized=json.dumps(events)
        for payload in payloads:
            if payload:self.assertNotIn(payload,serialized)
        with self.store.connection() as db:
            stored='\n'.join(r[0] for r in db.execute('SELECT event FROM transactions'))
        for payload in payloads:
            if payload:self.assertNotIn(payload,stored)
        served=[e for e in events if e['result']['outcome']=='served']
        self.assertTrue(served)
        self.assertTrue(all(e['result']['returned_payload_present'] for e in served))

    def test_missing_scope_permission_is_distinct_from_revocation(self):
        bad=Store(self.path,faults=['ignore_read_scope'])
        bad.transact(self.tech,'read',record='R-OTHER');values=observe(bad.events()[-1])
        self.assertFalse(values['DummyRehearsal::probe::revocationEffective'])
        self.assertFalse(values['DummyRehearsal::probe::readAuthorized'])
        self.assertTrue(values['DummyRehearsal::probe::readServed'])

    def test_observer_does_not_reuse_a_faulty_application_permission_decision(self):
        with patch.object(Store,'permitted',return_value=True):
            self.store.transact(self.tech,'read',record='R-OTHER')
        values=observe(self.store.events()[-1])
        self.assertTrue(values['DummyRehearsal::probe::readServed'])
        self.assertFalse(values['DummyRehearsal::probe::readAuthorized'])

    def test_unknown_session_is_denied_and_fault_names_are_bounded(self):
        self.assertNotIn('payload',self.store.transact('NOT_A_SESSION','read',record='R-DEMO-001'))
        self.assertNotIn('book',self.store.transact('NOT_A_SESSION','count',part='P-DEMO-001'))
        self.assertEqual(self.store.transact(self.stock,'count',part='P-DEMO-001')['book'],5)
        with self.assertRaises(ValueError):Store(self.path,faults=['arbitrary_code'])

    def test_reopen_preserves_state_and_exclusive_create_does_not_reset_it(self):
        self.store.transact(self.stock,'issue',part='P-RACE',quantity=1)
        reopened=Store(self.path);self.assertEqual(len(reopened.events()),1)
        with self.assertRaises(FileExistsError):Store(self.path,create=True)
        self.assertEqual(self.part('P-RACE')['book'],0)

    def test_complete_driver_executes_transactions_and_observer_emits_only_booleans(self):
        events=exercise(self.store)
        self.assertEqual(len(events),26)
        self.assertEqual([e['sequence'] for e in events],list(range(1,27)))
        self.assertTrue(any(e['result'].get('reason')=='disposition_tombstone' for e in events))
        for event in events:
            values=observe(event);self.assertEqual(len(values),15)
            self.assertTrue(all(type(value) is bool for value in values.values()))


    def test_bad_read_presence_cannot_hide_a_served_unauthorized_read(self):
        bad=Store(self.path,faults=['ignore_read_scope'])
        bad.transact(self.tech,'read',record='R-OTHER');event=bad.events()[-1]
        self.assertTrue(observe(event)['DummyRehearsal::probe::readServed'])
        self.assertFalse(observe(event)['DummyRehearsal::probe::readAuthorized'])
        for value in ('missing',1,False,'true',None):
            with self.subTest(value=value):
                broken=deepcopy(event)
                if value=='missing':broken['result'].pop('returned_payload_present')
                else:broken['result']['returned_payload_present']=value
                with self.assertRaises(ValueError):observe(broken)

    def test_bad_stock_and_hold_fields_cannot_become_false_inputs(self):
        bad=Store(self.path,faults=['issue_on_mismatch'])
        bad.transact(self.stock,'issue',part='P-DEMO-001',quantity=1)
        event=bad.events()[-1]
        self.assertTrue(observe(event)['DummyRehearsal::probe::stockMismatch'])
        broken=deepcopy(event);broken['before']['part'].update(book='unknown',physical='unknown')
        with self.assertRaises(ValueError):observe(broken)
        broken=deepcopy(event);broken['after']['movements']=[]
        with self.assertRaises(ValueError):observe(broken)
        self.store.transact(self.steward,'set_fixture_policy',record='R-DISPOSE',not_before_tick=0)
        bad=Store(self.path,faults=['ignore_hold']);bad.transact(self.steward,'dispose',record='R-DISPOSE')
        event=bad.events()[-1]
        self.assertTrue(observe(event)['DummyRehearsal::probe::holdActive'])
        self.assertTrue(observe(event)['DummyRehearsal::probe::dispositionCommitted'])
        for field,value in [('held',[]),('payload_present','unknown')]:
            broken=deepcopy(event);broken['before']['record'][field]=value
            with self.assertRaises(ValueError):observe(broken)
        broken=deepcopy(event);broken['after']['dispositions']=[]
        with self.assertRaises(ValueError):observe(broken)

    def test_complete_capture_preserves_denials_empty_content_and_unknown_sessions(self):
        self.store.transact(self.tech,'read',record='R-EMPTY')
        event=self.store.events()[-1]
        self.assertTrue(observe(event)['DummyRehearsal::probe::readServed'])
        self.store.transact('UNKNOWN','read',record='R-EMPTY')
        event=self.store.events()[-1]
        self.assertFalse(observe(event)['DummyRehearsal::probe::readServed'])
        self.assertFalse(observe(event)['DummyRehearsal::probe::readAuthorized'])
        broken=deepcopy(event);broken['before']['security']['grants']=[{'permission':True,'scope':'*'}]
        with self.assertRaises(ValueError):observe(broken)


    def test_audit_rows_must_match_the_operation_target_and_actor(self):
        bad=Store(self.path,faults=['omit_adjustment_audit'])
        bad.transact(self.stock,'adjust',part='P-DEMO-001');event=bad.events()[-1]
        for target,actor in [('UNRELATED-PART',event['actor']),('P-DEMO-001','UNRELATED-ACTOR')]:
            broken=deepcopy(event);broken['after']['audit'].append({'txn':event['sequence'],'actor':actor,'action':'adjust','target':target})
            self.assertFalse(observe(broken)['DummyRehearsal::probe::adjustmentAuditRecorded'])
        self.prepare_disposition();bad=Store(self.path,faults=['omit_disposition_audit'])
        bad.transact(self.steward,'dispose',record='R-DISPOSE');event=bad.events()[-1]
        for target,actor in [('UNRELATED-RECORD',event['actor']),('R-DISPOSE','UNRELATED-ACTOR')]:
            broken=deepcopy(event);broken['after']['audit'].append({'txn':event['sequence'],'actor':actor,'action':'dispose','target':target})
            self.assertFalse(observe(broken)['DummyRehearsal::probe::dispositionAuditRecorded'])

    def test_capture_references_bind_movement_policy_actor_and_tombstone(self):
        events=exercise(self.store)
        movement=next(e for e in events if e['after']['movements'])
        broken=deepcopy(movement);broken['after']['movements'][0]['part']='UNRELATED-PART'
        with self.assertRaises(ValueError):observe(broken)
        policy=next(e for e in events if e['before']['policy'])
        broken=deepcopy(policy);broken['before']['policy']['id']='UNRELATED-POLICY'
        with self.assertRaises(ValueError):observe(broken)
        broken=deepcopy(events[0]);broken['actor']='UNRELATED-ACTOR'
        with self.assertRaises(ValueError):observe(broken)
        tombstone=next(e for e in events if e['after']['tombstone'])
        broken=deepcopy(tombstone);broken['after']['tombstone']['record_id']='UNRELATED-RECORD'
        with self.assertRaises(ValueError):observe(broken)


if __name__=='__main__':unittest.main()
