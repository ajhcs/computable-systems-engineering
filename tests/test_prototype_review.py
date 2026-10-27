"""Evidence origin, integrity, observation correspondence and claim-boundary checks."""
from copy import deepcopy
from hashlib import sha256
import json,os
from pathlib import Path
import subprocess,sys,tempfile,unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verifier.prototype_review import inspect_prototype
from verifier.sysml import JAR,CLASSES,CACHE
from scripts.prototype_demo import generate_run

@unittest.skipUnless(JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file(),'Pinned native parser unavailable')
class PrototypeReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.tmp');cls.base=Path(cls.temp.name)
        cls.report=generate_run(cls.base/'baseline')
        assert cls.report['status']=='pass',cls.report['findings']
        cls.run_record=json.loads((cls.base/'baseline/run-record.json').read_text())
        cls.evidence=json.loads((cls.base/'baseline/observations.json').read_text())
        cls.invocation=json.loads((cls.base/'baseline/invocation.json').read_text())

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        self.temp_case=tempfile.TemporaryDirectory(dir=ROOT/'.tmp');self.directory=Path(self.temp_case.name)
        self.record=deepcopy(self.run_record);self.observations=deepcopy(self.evidence)
        self.paths=dict(self.invocation['artifacts']);self.native=deepcopy(self.report['native_check'])

    def tearDown(self):self.temp_case.cleanup()

    def check(self,side_effect=None,digest=None):
        evidence=self.directory/'observations.json';evidence.write_text(json.dumps(self.observations)+'\n')
        self.paths['OBSERVATIONS']=str(evidence)
        self.record['artifacts']['OBSERVATIONS']['sha256']=sha256(evidence.read_bytes()).hexdigest()
        run=self.directory/'run.json';run.write_text(json.dumps(self.record)+'\n')
        with patch('verifier.prototype_review.check_sysml',side_effect=side_effect,return_value=self.native) as checker:
            r=inspect_prototype(self.invocation['models'],self.invocation['manifest'],digest or self.invocation['retained_manifest_sha256'],evidence,run,self.paths)
        return r,checker

    def test_pass_is_verification_of_selected_prototype_trace_not_validation(self):
        r,_=self.check();self.assertEqual(r['status'],'pass',r['findings'])
        self.assertEqual(r['validation'],'not_performed');self.assertEqual(r['standards_conformity'],'not_assessed')
        self.assertEqual(r['decision_authentication'],'not_provided')

    def test_retained_manifest_drift_blocks_before_native_review(self):
        r,checker=self.check(digest='0'*64);self.assertEqual(r['status'],'error');checker.assert_not_called()

    def test_artifact_bytes_changed_fail_even_if_monitor_passes(self):
        self.record['artifacts']['IMPLEMENTATION']['sha256']='0'*64
        self.assertEqual(self.check()[0]['status'],'fail')

    def test_missing_observer_and_synthetic_origin_cannot_pass(self):
        self.paths.pop('OBSERVER');self.assertEqual(self.check()[0]['status'],'unknown')
        self.paths=dict(self.invocation['artifacts']);self.record['evidence_origin']='authored_synthetic_trace'
        self.assertEqual(self.check()[0]['status'],'unknown')

    def test_failed_execution_cannot_be_overridden_by_passing_trace(self):
        self.record['run']['exit_code']=1
        self.assertEqual(self.check()[0]['status'],'error')

    def test_unresolved_selected_condition_stays_unknown(self):
        self.record['unresolved'].append({'id':'NEEDED','description':'Required capture is unavailable.','scope':'blocks_selected_scope'})
        self.assertEqual(self.check()[0]['status'],'unknown')

    def test_standard_conformity_claim_is_not_admitted(self):
        self.record['standards_basis'][0]['conformity_assessment']='certified'
        self.assertEqual(self.check()[0]['status'],'unsupported')

    def test_run_cannot_drop_a_selected_obligation(self):
        self.record['selected_obligations'].pop()
        self.assertEqual(self.check()[0]['status'],'fail')

    def test_projection_cannot_replace_actual_transaction_outcome(self):
        self.observations['observations'][0]['DummyRehearsal::probe::issueCommitted']=True
        r,_=self.check();self.assertEqual(r['status'],'fail')
        self.assertIn('observation_correspondence',{f['rule'] for f in r['findings']})

    def test_missing_observation_is_unknown_not_an_assumed_false(self):
        self.observations['observations'][0].pop('DummyRehearsal::probe::issueCommitted')
        self.assertEqual(self.check()[0]['status'],'unknown')

    def test_dropped_transaction_is_detected_even_with_updated_artifact_hash(self):
        original=Path(self.paths['TRANSACTIONS']).read_text().splitlines()
        capture=self.directory/'capture.jsonl';capture.write_text('\n'.join(original[1:])+'\n')
        self.paths['TRANSACTIONS']=str(capture);self.record['artifacts']['TRANSACTIONS']['sha256']=sha256(capture.read_bytes()).hexdigest()
        r,_=self.check();self.assertEqual(r['status'],'fail')
        self.assertIn('capture_sequence',{f['rule'] for f in r['findings']})

    def test_observer_adapter_revision_cannot_silently_reinterpret_capture(self):
        observer=self.directory/'observer.py';observer.write_text('# a different observer\n')
        self.paths['OBSERVER']=str(observer);self.record['artifacts']['OBSERVER']['sha256']=sha256(observer.read_bytes()).hexdigest()
        self.assertEqual(self.check()[0]['status'],'unknown')

    def test_transaction_sequence_is_not_an_admitted_physical_clock(self):
        self.record['observation_mode']='physical_clock'
        self.assertEqual(self.check()[0]['status'],'unsupported')

    def test_temporal_clause_is_refused_for_transaction_index_projection(self):
        result=next(iter(self.native['results'].values()))
        result['compiled_clause']='Upon unit.stockMismatch = true, unit shall within 2 seconds satisfy unit.issueCommitted = false.'
        self.assertEqual(self.check()[0]['status'],'unsupported')

    def test_unknown_adapter_does_not_load_model_supplied_code(self):
        self.record['adapter']='arbitrary.py'
        self.assertEqual(self.check()[0]['status'],'unsupported')

    def test_malformed_capture_cannot_escape_as_a_success_or_traceback(self):
        capture=self.directory/'bad.jsonl';capture.write_text('[]\n')
        self.paths['TRANSACTIONS']=str(capture)
        self.record['artifacts']['TRANSACTIONS']['sha256']=sha256(capture.read_bytes()).hexdigest()
        self.assertEqual(self.check()[0]['status'],'error')

    def test_input_change_during_review_revokes_success(self):
        source=self.directory/'implementation.py';source.write_bytes(Path(self.paths['IMPLEMENTATION']).read_bytes())
        self.paths['IMPLEMENTATION']=str(source)
        def change(*args,**kwargs):source.write_text('changed during review');return self.native
        r,_=self.check(side_effect=change)
        self.assertEqual(r['status'],'error');self.assertFalse(r['results_usable'])

    def test_native_failure_remains_failure(self):
        self.native['status']='fail';self.assertEqual(self.check()[0]['status'],'fail')

    def test_actual_cli_from_another_directory_uses_explicit_artifact_paths(self):
        args=[sys.executable,str(ROOT/'scripts/prototype_review.py'),*self.invocation['models'],
            '--manifest',self.invocation['manifest'],'--manifest-sha256',self.invocation['retained_manifest_sha256'],
            '--evidence',self.invocation['evidence'],'--run-record',self.invocation['run_record'],'--json']
        for key,path in self.invocation['artifacts'].items():args+=['--artifact',key+'='+path]
        r=subprocess.run(args,cwd=self.directory,capture_output=True,text=True,
            env=dict(os.environ,CSE_SYSML_CACHE=str(CACHE)))
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertEqual(json.loads(r.stdout)['status'],'pass')


    def test_mandatory_metadata_rejects_truthy_non_text_values(self):
        original=deepcopy(self.record)
        mutations=[lambda r:r['run'].update(id=['not text']),
            lambda r:r['run'].update(capture_boundary={'not':'text'}),
            lambda r:r['run'].update(start_utc=123),
            lambda r:next(iter(r['signal_definitions'].values())).update(meaning=['not text']),
            lambda r:r['standards_basis'][0].update(reference={'not':'text'}),
            lambda r:r['standards_basis'][0].update(application=3),
            lambda r:r['unresolved'][0].update(id=['not text']),
            lambda r:r['unresolved'][0].update(description={'not':'text'})]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.record=deepcopy(original);mutation(self.record)
                self.assertEqual(self.check()[0]['status'],'error')

    def test_legacy_observer_is_explicitly_unsupported(self):
        self.record['adapter']='repair_reuse_sqlite_v2'
        self.assertEqual(self.check()[0]['status'],'unsupported')

    def test_rehashed_malformed_capture_cannot_pass_a_passing_monitor(self):
        events=[json.loads(line) for line in Path(self.paths['TRANSACTIONS']).read_text().splitlines()]
        mutations=[lambda e:e['result'].pop('returned_payload_present'),
                   lambda e:e['result'].update(returned_payload_present=1),
                   lambda e:e['result'].update(returned_payload_present=False)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                broken=deepcopy(events);served=next(e for e in broken if e['result']['outcome']=='served');mutate(served)
                capture=self.directory/'broken.jsonl';capture.write_text(''.join(json.dumps(e)+'\n' for e in broken))
                self.paths['TRANSACTIONS']=str(capture)
                self.record['artifacts']['TRANSACTIONS']['sha256']=sha256(capture.read_bytes()).hexdigest()
                self.assertEqual(self.check()[0]['status'],'error')

    def test_actual_fault_cannot_be_hidden_by_a_contradictory_return_capture(self):
        output=self.directory/'actual-fault';fault=generate_run(output,faults=['ignore_read_scope'])
        self.assertEqual(fault['status'],'fail')
        inv=json.loads((output/'invocation.json').read_text());record=json.loads(Path(inv['run_record']).read_text())
        evidence=json.loads(Path(inv['evidence']).read_text())
        events=[json.loads(line) for line in Path(inv['artifacts']['TRANSACTIONS']).read_text().splitlines()]
        for event,row in zip(events,evidence['observations']):
            if event['result']['outcome']=='served':event['result']['returned_payload_present']=False
            row['DummyRehearsal::probe::readServed']=False
        capture=self.directory/'contradiction.jsonl';capture.write_text(''.join(json.dumps(e)+'\n' for e in events))
        observed=self.directory/'forged-observations.json';observed.write_text(json.dumps(evidence))
        paths=dict(inv['artifacts']);paths.update(TRANSACTIONS=str(capture),OBSERVATIONS=str(observed))
        for key in ('TRANSACTIONS','OBSERVATIONS'):record['artifacts'][key]['sha256']=sha256(Path(paths[key]).read_bytes()).hexdigest()
        run=self.directory/'contradiction-run.json';run.write_text(json.dumps(record))
        result=inspect_prototype(inv['models'],inv['manifest'],inv['retained_manifest_sha256'],observed,run,paths)
        self.assertEqual(result['monitor_status'],'not_run')
        self.assertEqual(result['status'],'error');self.assertFalse(result['results_usable'])


    def test_actual_foreign_audit_rows_do_not_clear_a_missing_audit_fault(self):
        from prototypes.repair_reuse_observer import observe
        for fault,action,target,signal in [
                ('omit_adjustment_audit','adjust','UNRELATED-PART','adjustmentAuditRecorded'),
                ('omit_disposition_audit','dispose','UNRELATED-RECORD','dispositionAuditRecorded')]:
            with self.subTest(fault=fault):
                output=self.directory/fault;review=generate_run(output,faults=[fault]);self.assertEqual(review['status'],'fail')
                inv=json.loads((output/'invocation.json').read_text());record=json.loads(Path(inv['run_record']).read_text())
                evidence=json.loads(Path(inv['evidence']).read_text())
                events=[json.loads(line) for line in Path(inv['artifacts']['TRANSACTIONS']).read_text().splitlines()]
                event=next(e for e in events if e['action']==action and e['result']['outcome']=='committed')
                event['after']['audit'].append({'txn':event['sequence'],'actor':event['actor'],'action':action,'target':target})
                self.assertFalse(observe(event)['DummyRehearsal::probe::'+signal])
                evidence['observations']=[observe(e) for e in events]
                capture=self.directory/(fault+'.jsonl');capture.write_text(''.join(json.dumps(e)+'\n' for e in events))
                observed=self.directory/(fault+'.json');observed.write_text(json.dumps(evidence))
                paths=dict(inv['artifacts']);paths.update(TRANSACTIONS=str(capture),OBSERVATIONS=str(observed))
                for key in ('TRANSACTIONS','OBSERVATIONS'):record['artifacts'][key]['sha256']=sha256(Path(paths[key]).read_bytes()).hexdigest()
                run=self.directory/(fault+'-run.json');run.write_text(json.dumps(record))
                result=inspect_prototype(inv['models'],inv['manifest'],inv['retained_manifest_sha256'],observed,run,paths)
                self.assertEqual(result['status'],'fail');self.assertEqual(result['monitor_status'],'fail')


if __name__=='__main__':unittest.main()
