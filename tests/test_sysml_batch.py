"""Checked parser reuse preserves monitor verdicts, scopes, limits and freshness."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verifier import sysml
from verifier.sysml_batch import inspect_batch
from verifier.sysml_batch_context import PARSE_SESSION

MODEL=ROOT/'examples/sysml/ack.sysml';MANIFEST=ROOT/'examples/sysml/ack-manifest.json'
EVIDENCE=json.loads((ROOT/'examples/sysml/ack-evidence.json').read_text())
DIGEST=sha256(MANIFEST.read_bytes()).hexdigest()

class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.tmp');self.path=Path(self.temp.name)
        self.model=self.path/'model.sysml';self.model.write_bytes(MODEL.read_bytes())
        self.evidence=self.path/'evidence.json';self.evidence.write_text(json.dumps(EVIDENCE))
        self.cases={'CASE':self.evidence}
    def tearDown(self):self.temp.cleanup()
    def mocked(self,**kwargs):
        with patch('verifier.sysml_batch.runtime_identity',return_value={'runtime':'same'}),\
             patch('verifier.sysml_batch.sysml.check_sysml',return_value={'status':'pass'}) as check:
            result=inspect_batch([self.model],MANIFEST,DIGEST,self.cases,**kwargs)
            return result,check.call_count
    def test_empty_excessive_and_invalid_case_ids_cannot_succeed(self):
        for cases in ({},{'BAD-ID':self.evidence},{'C'+str(i):self.evidence for i in range(65)}):
            self.cases=cases;result,calls=self.mocked()
            self.assertEqual(result['status'],'error');self.assertEqual(calls,0)
    def test_scope_drift_is_blocked_before_parser(self):
        with patch('verifier.sysml_batch.sysml.check_sysml') as check:
            result=inspect_batch([self.model],MANIFEST,'0'*64,self.cases)
            self.assertEqual(result['status'],'error');check.assert_not_called()
    def test_duplicate_nonfinite_and_symlink_input_refused(self):
        for raw in ('{"complete":true,"complete":false}','{"x":NaN}'):
            self.evidence.write_text(raw);result,calls=self.mocked()
            self.assertEqual(result['status'],'error');self.assertEqual(calls,0)
        self.evidence.unlink();self.evidence.symlink_to(ROOT/'examples/sysml/ack-evidence.json')
        result,calls=self.mocked();self.assertEqual(result['status'],'error');self.assertEqual(calls,0)
    def test_changed_runtime_invalidates_all_results_and_clears_session(self):
        with patch('verifier.sysml_batch.runtime_identity',side_effect=[{'runtime':'old'},{'runtime':'new'}]),\
             patch('verifier.sysml_batch.sysml.check_sysml',return_value={'status':'pass'}):
            result=inspect_batch([self.model],MANIFEST,DIGEST,self.cases)
        self.assertEqual(result['status'],'error');self.assertFalse(result['results_usable'])
        self.assertIsNone(PARSE_SESSION.get())
    def test_changed_model_or_evidence_invalidates_all_results(self):
        for target in (self.model,self.evidence):
            original=target.read_bytes()
            def check(*args,**kwargs):target.write_bytes(original+b' ');return {'status':'pass'}
            with patch('verifier.sysml_batch.runtime_identity',return_value={'r':'same'}),\
                 patch('verifier.sysml_batch.sysml.check_sysml',side_effect=check):
                result=inspect_batch([self.model],MANIFEST,DIGEST,self.cases)
            self.assertEqual(result['status'],'error');self.assertFalse(result['results_usable'])
            target.write_bytes(original)
    def test_each_non_success_remains_non_success(self):
        for state in ('fail','unknown','unsupported','error','not_run'):
            with patch('verifier.sysml_batch.runtime_identity',return_value={'r':'same'}),\
                 patch('verifier.sysml_batch.sysml.check_sysml',return_value={'status':state}):
                result=inspect_batch([self.model],MANIFEST,DIGEST,self.cases)
            self.assertEqual(result['status'],state)
    def test_nested_sessions_are_refused_and_outer_context_preserved(self):
        outer=lambda *args:None;token=PARSE_SESSION.set(outer)
        try:
            result,_=self.mocked();self.assertEqual(result['status'],'error');self.assertIs(PARSE_SESSION.get(),outer)
        finally:PARSE_SESSION.reset(token)
    def test_exception_cannot_leave_a_reuse_session_active(self):
        with patch('verifier.sysml_batch.runtime_identity',return_value={'r':'same'}),\
             patch('verifier.sysml_batch.sysml.check_sysml',side_effect=RuntimeError('execution error')):
            result=inspect_batch([self.model],MANIFEST,DIGEST,self.cases)
        self.assertEqual(result['status'],'error');self.assertIsNone(PARSE_SESSION.get())

@unittest.skipUnless(sysml.JAR.is_file() and (sysml.CLASSES/'SysmlBridge.class').is_file(),'Install pinned parser')
class NativeBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'.tmp');cls.path=Path(cls.temp.name)
        late=deepcopy(EVIDENCE);late['observations'][3]['AckExample::controller::acknowledged']=False
        prefix=deepcopy(EVIDENCE);prefix['observations']=prefix['observations'][:3]
        stale=deepcopy(EVIDENCE);stale['model_sha256']='0'*64
        cls.values={'NORMAL':EVIDENCE,'LATE':late,'PREFIX':prefix,'STALE':stale};cls.cases={}
        for key,value in cls.values.items():
            path=cls.path/(key+'.json');path.write_text(json.dumps(value));cls.cases[key]=path
        cls.report=inspect_batch([MODEL],MANIFEST,DIGEST,cls.cases)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_native_batch_uses_one_parse_and_keeps_counterexample_unknown_error(self):
        self.assertTrue(self.report['results_usable'],self.report['findings'])
        self.assertEqual({k:r['status'] for k,r in self.report['results'].items()},
                         {'NORMAL':'pass','LATE':'fail','PREFIX':'unknown','STALE':'error'})
        self.assertEqual(self.report['parser_calls'],1)
        self.assertEqual(self.report['parser_reuses'],2)
        self.assertIsNone(PARSE_SESSION.get())
    def test_exact_reports_match_existing_single_trace_checks(self):
        manifest=json.loads(MANIFEST.read_text())
        for key,value in self.values.items():
            single=sysml.check_sysml([MODEL],manifest=manifest,evidence=value,review=True)
            self.assertEqual(single,self.report['results'][key])
    def test_caps_apply_per_case_without_a_cached_success(self):
        result=inspect_batch([MODEL],MANIFEST,DIGEST,{'NORMAL':self.cases['NORMAL']},observation_cap=1)
        self.assertEqual(result['status'],'unknown')
        self.assertEqual(result['results']['NORMAL']['limits']['observation_cap'],1)
    def test_existing_launcher_can_run_the_batch_from_another_directory(self):
        result=subprocess.run([sys.executable,'-B',str(ROOT/'skills/develop-system-concept/scripts/cse.py'),
            'check',str(MODEL),'--manifest',str(MANIFEST),'--manifest-sha256',DIGEST,
            '--evidence-case','NORMAL='+str(self.cases['NORMAL']),'--evidence-case','LATE='+str(self.cases['LATE'])],
            cwd=self.path,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['results']['LATE']['status'],'fail')

if __name__=='__main__':
    (ROOT/'.tmp').mkdir(exist_ok=True);unittest.main()
