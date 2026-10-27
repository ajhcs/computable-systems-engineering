"""Opt-in documentary composition retains global and cross-view omission checks."""
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
from verifier.workflow import schema as workflow_schema, draft_model
from verifier.concept_review import schema, compare, inspect_concept, scope_diff
from verifier.evidence_actions import next_evidence
from verifier.sysml import JAR,CLASSES

BASE=ROOT/'examples/concept-review/lending'
TEXT=(BASE/'concept.sysml').read_text()
RECORD=json.loads(TEXT.split('doc cseWorkflow /*CSE-WORKFLOW/1.0',1)[1].split('*/',1)[0])
SCOPE=json.loads((BASE/'scope.json').read_text())

def composed():
    r=deepcopy(RECORD);s=deepcopy(SCOPE)
    r['version']='workflow-1.1'
    for key,e in r['elements'].items():e['native_name']='Composed::'+key
    for i in range(70-len(r['elements'])):
        key='F_DETAIL_'+str(i)
        r['elements'][key]={'kind':'function','native_name':'Composed::'+key,'label':'Detailed support activity '+str(i),
            'description':'Proposed synthetic decomposition for bounded composition testing.','basis':'SYN','status':'proposed'}
        r['relations']['DETAIL_'+str(i)]={'kind':'decomposes','from':'F_RESTORE','to':key,'basis':'SYN','label':'Support refinement'}
        s['expectations']['DETAIL_'+str(i)]={'topic':'support','kind':'element','element':key,'element_kind':'function','native_name':'Composed::'+key}
    keys=list(r['elements']);r['views']={'OPERATIONS':{'label':'Operations','elements':keys[:60]},
                                      'SUPPORT':{'label':'Detailed support','elements':keys[60:]+['R_TECH']}}
    r['relations']['CROSS_ALLOC']={'kind':'allocated_to','from':keys[-1],'to':'R_TECH','basis':'SYN','label':'Shared maintainer duty'}
    s['expectations']['CROSS_ALLOC']={'topic':'support','kind':'relation','relation_kind':'allocated_to','from':keys[-1],'to':'R_TECH'}
    for e in s['expectations'].values():
        if e['kind']=='element':e['native_name']=r['elements'][e['element']]['native_name']
    s.update(version='concept-review-1.3',views={k:v['elements'][:] for k,v in r['views'].items()})
    return r,s

class CompositionTests(unittest.TestCase):
    def test_legacy_cap_and_contract_are_unchanged(self):
        r,s=composed();r['version']='workflow-1.0';r.pop('views')
        self.assertRaises(ValueError,workflow_schema,r)
        schema(SCOPE);workflow_schema(RECORD)

    def test_composed_record_scope_and_cross_view_relation(self):
        r,s=composed();workflow_schema(r);schema(s)
        self.assertEqual(compare(s,r)[0],[])
        r['relations'].pop('CROSS_ALLOC')
        self.assertIn('missing_scoped_relation',{x['rule'] for x in compare(s,r)[0]})

    def test_unmapped_or_oversized_views_are_refused(self):
        r,_=composed();r['views']['ALL']={'label':'Too much','elements':list(r['elements'])}
        self.assertRaises(ValueError,workflow_schema,r)
        r,_=composed();r['views']['SUPPORT']['elements'].pop(0)
        self.assertRaises(ValueError,workflow_schema,r)

    def test_clean_view_removal_and_membership_drift_cannot_pass(self):
        r,s=composed();r['views'].pop('SUPPORT')
        findings,_=compare(s,r)
        self.assertIn('composition_views_changed',{x['rule'] for x in findings})
        r,s=composed();r['views']['SUPPORT']['elements'].pop()
        self.assertIn('composition_members_changed',{x['rule'] for x in compare(s,r)[0]})

    def test_new_record_requires_explicit_composed_scope(self):
        r,_=composed()
        self.assertIn('composition_scope_missing',{x['rule'] for x in compare(SCOPE,r)[0]})
        _,s=composed()
        self.assertIn('composition_record_missing',{x['rule'] for x in compare(s,RECORD)[0]})

    def test_scope_diff_exposes_view_membership(self):
        _,s=composed();t=deepcopy(s);t['views']['SUPPORT'].pop()
        self.assertTrue(scope_diff(s,t)['views_changed'])

    def test_global_count_is_still_bounded(self):
        r,_=composed()
        for i in range(300):r['elements']['EXTRA_'+str(i)]=deepcopy(next(iter(r['elements'].values())))
        self.assertRaises(ValueError,workflow_schema,r)

    def test_draft_uses_matching_explicit_marker(self):
        r,_=composed();text=draft_model(r,'Composed')
        self.assertIn('doc cseWorkflow /*CSE-WORKFLOW/1.1',text)

class EvidenceTests(unittest.TestCase):
    def test_question_links_existing_plan_without_closing_it(self):
        r=deepcopy(RECORD);r['questions']['Q_REAL']={'text':'Actual competence unknown','affects':['F_RESTORE',r['evidence']['E_READY']['target']],'blocking':True}
        review={'status':'unknown','workflow':{'record':r},'findings':[{'rule':'blocking_question','status':'unknown','ids':['Q_REAL'],'detail':'Actual competence unknown'}]}
        result=next_evidence(review)
        self.assertEqual(result['status'],'unknown')
        self.assertIn('F_RESTORE',result['actions'][0]['affected_ids'])
        self.assertTrue(result['unexecuted_plans'])
        self.assertIn('E_READY',result['actions'][0]['existing_plans'])
        self.assertTrue(all(p['result']=='not_run' for p in result['unexecuted_plans'].values()))
        self.assertIsNone(result['actions'][0]['responsible_party'])
        self.assertEqual(review['workflow']['record'],r)

    def test_tool_failure_stays_a_failure_and_precedes_evidence(self):
        review={'status':'error','findings':[{'rule':'need','status':'unknown','ids':[],'detail':'Need evidence'},
                                            {'rule':'parser','status':'error','ids':[],'detail':'Parser unavailable'}]}
        result=next_evidence(review)
        self.assertEqual(result['status'],'error')
        self.assertEqual(result['actions'][0]['rule'],'parser')
        self.assertEqual(result['validation'],'not_performed')

    def test_pass_does_not_claim_no_real_gaps_and_plans_remain_unrun(self):
        result=next_evidence({'status':'pass','workflow':{'record':RECORD},'findings':[]})
        self.assertEqual(result['actions'],[]);self.assertTrue(result['unexecuted_plans'])
        self.assertEqual(result['acceptance'],'not_evaluated')

@unittest.skipUnless(JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file(),'Install pinned parser')
class NativeCompositionTests(unittest.TestCase):
    def review(self,r,s):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as temp:
            temp=Path(temp);m=temp/'model.sysml';m.write_text(draft_model(r,'Composed'))
            p=temp/'scope.json';p.write_text(json.dumps(s))
            return inspect_concept(m,p,sha256(p.read_bytes()).hexdigest(),{'SYN':BASE/'brief.md'})

    def test_seventy_bound_elements_and_retained_boundary_are_checked(self):
        r,s=composed();report=self.review(r,s)
        self.assertEqual(report['status'],'pass',report['findings'])
        self.assertEqual(len(report['workflow']['bindings']),70)
        self.assertTrue(report['composed_views']['OPERATIONS']['boundary_relations'])
        self.assertEqual(report['behavior'],'not_run')

    def test_cross_view_cycle_is_not_hidden_by_views(self):
        r,s=composed();last=list(r['elements'])[-1]
        r['relations']['BACK']={'kind':'decomposes','from':last,'to':'F_RESTORE','basis':'SYN','label':'Bad reverse link'}
        report=self.review(r,s)
        self.assertEqual(report['status'],'fail')
        self.assertIn('decomposition_cycle',{x['rule'] for x in report['findings']})

    def test_header_record_mismatch_cannot_be_reinterpreted(self):
        r,s=composed()
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as temp:
            temp=Path(temp);m=temp/'model.sysml';m.write_text(draft_model(r,'Composed').replace('CSE-WORKFLOW/1.1','CSE-WORKFLOW/1.0'))
            p=temp/'scope.json';p.write_text(json.dumps(s))
            report=inspect_concept(m,p,sha256(p.read_bytes()).hexdigest(),{'SYN':BASE/'brief.md'})
            self.assertEqual(report['status'],'error')

    def test_next_evidence_route_works_through_existing_launcher(self):
        result=subprocess.run([sys.executable,'-B',str(ROOT/'skills/develop-conops/scripts/cse.py'),
            'concept-review','next-evidence',str(BASE/'concept.sysml'),'--scope',str(BASE/'scope.json'),
            '--scope-sha256',(BASE/'scope.sha256').read_text().strip(),'--source','SYN='+str(BASE/'brief.md')],
            cwd=ROOT/'.tmp',capture_output=True,text=True,timeout=45)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue(json.loads(result.stdout)['unexecuted_plans'])

if __name__=='__main__':
    (ROOT/'.tmp').mkdir(exist_ok=True);unittest.main()
