"""Native item-specific deadline mapping and meaningful non-success controls."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verifier.sysml import check_sysml,JAR,CLASSES
EXAMPLE=ROOT/'examples/behavior-review'
TEXT=(EXAMPLE/'concept.sysml').read_text()
MANIFEST=json.loads((EXAMPLE/'manifest.json').read_text())
EVIDENCE=json.loads((EXAMPLE/'synthetic-evidence.json').read_text())

@unittest.skipUnless(JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file(),'Pinned parser unavailable')
class BehaviorReviewTests(unittest.TestCase):
    def check(self,**kwargs):
        return check_sysml(EXAMPLE/'concept.sysml',manifest=MANIFEST,evidence=kwargs.pop('evidence',deepcopy(EVIDENCE)),review=True,**kwargs)
    def modified(self,text):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            p=Path(d)/'concept.sysml';p.write_text(text)
            e=deepcopy(EVIDENCE);e['model_sha256']=sha256(p.read_bytes()).hexdigest()
            return check_sysml(p,manifest=MANIFEST,evidence=e,review=True)
    def test_native_identity_binding_and_inclusive_deadline(self):
        r=self.check();self.assertEqual(r['status'],'pass',r)
        self.assertEqual(r['coverage']['compiled'],['R_RECORD__recordingTime'])
        self.assertEqual(r['claim_scope'],'supplied_behavior_evidence')
    def test_late_and_wrong_item_do_not_discharge_obligation(self):
        for field,value in [('time','4.001'),('correlationId','C')]:
            with self.subTest(field=field):
                e=deepcopy(EVIDENCE);e['events'][-1][field]=value
                self.assertEqual(self.check(evidence=e)['status'],'fail')
    def test_one_response_cannot_cover_two_item_ids(self):
        e=deepcopy(EVIDENCE);e['events'].pop()
        self.assertEqual(self.check(evidence=e)['status'],'fail')
    def test_unfinished_capture_and_no_trigger_remain_unknown(self):
        e=deepcopy(EVIDENCE);e['events']=e['events'][:2];e['observed_until']['time']='2'
        self.assertEqual(self.check(evidence=e)['status'],'unknown')
        e=deepcopy(EVIDENCE);e['complete']=False
        self.assertEqual(self.check(evidence=e)['status'],'unknown')
        e['events']=[];e['complete']=True
        self.assertEqual(self.check(evidence=e)['status'],'unknown')
    def test_absent_evidence_and_manifest_cannot_be_required_pass(self):
        self.assertEqual(self.check(evidence=None)['status'],'unknown')
        r=check_sysml(EXAMPLE/'concept.sysml',evidence=EVIDENCE,review=True)
        self.assertEqual(r['status'],'unknown')
    def test_stale_evidence_and_event_budget_are_not_success(self):
        e=deepcopy(EVIDENCE);e['model_sha256']='0'*64
        self.assertNotEqual(self.check(evidence=e)['status'],'pass')
        self.assertEqual(self.check(observation_cap=1)['status'],'unknown')
    def test_clean_requirement_omission_is_retained_by_manifest(self):
        text=TEXT[:TEXT.index('    requirement <R_RECORD>')]+'}\n'
        r=self.modified(text);self.assertNotEqual(r['status'],'pass',r)
        self.assertIn('R_RECORD__recordingTime',r['coverage']['expected'])
    def test_unbounded_timing_and_unclassified_documentation_not_admitted(self):
        for text in [TEXT.replace('within 4 minutes','eventually'),TEXT.replace('CSE-EVENT/2.0','ORDINARY-DOC/1.0')]:
            with self.subTest(text=text[-180:]):self.assertNotEqual(self.modified(text)['status'],'pass')
    def test_syntax_cannot_be_requested_as_behavior_review(self):
        self.assertNotEqual(self.check(syntax_only=True)['status'],'pass')
    def test_actual_skill_launcher(self):
        cmd=[sys.executable,str(ROOT/'skills/develop-system-concept/scripts/cse.py'),'check',str(EXAMPLE/'concept.sysml'),'--manifest',str(EXAMPLE/'manifest.json'),'--evidence',str(EXAMPLE/'synthetic-evidence.json'),'--review','--json']
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertEqual(json.loads(r.stdout)['status'],'pass')

if __name__=='__main__':unittest.main()
