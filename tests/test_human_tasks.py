"""Task facts, role coverage, project tailoring and real native-backed checks."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from verifier.human_tasks import inspect_tasks, schema, MARKER
from verifier.concept_review import schema as scope_schema, inspect_concept, render_text
from verifier.sysml import JAR,CLASSES

EXAMPLE=ROOT/'examples/human-task-review'
TEXT=(EXAMPLE/'concept.sysml').read_text()
SCOPE=json.loads((EXAMPLE/'scope.json').read_text())
REGISTER=json.loads(TEXT.split('doc cseHumanTasks /*'+MARKER,1)[1].split('*/',1)[0])
RECORD=json.loads(TEXT.split('doc cseWorkflow /*CSE-WORKFLOW/1.0',1)[1].split('*/',1)[0])
SELECTED={k:v for k,v in SCOPE['expectations'].items() if v['kind']=='human_task'}
PARSER=JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file()


def workflow(register=REGISTER,record=RECORD):
    """Unit-only native boundary snapshot; actual parsing is tested below."""
    return {'record':deepcopy(record),'sources':{'CASE':{'status':'pass'}},
        'native_inventory':{'concerns':[{'qualified_name':'TaskRegister::humanTaskContext'}]},
        'supplemental_documents':{'cseHumanTasks':[{'owner':'TaskRegister::humanTaskContext',
            'body':MARKER+'\n'+json.dumps(register)}]}}


def replace_document(text,name,marker,value):
    before,remaining=text.split('doc '+name+' /*'+marker,1)
    _,after=remaining.split('*/',1)
    payload=json.dumps(value,indent=2).replace('/*',r'\u002f*').replace('*/',r'*\u002f')
    return before+'doc '+name+' /*'+marker+'\n'+payload+'\n*/'+after


class TaskControls(unittest.TestCase):
    def test_proposed_four_contexts_are_documentary_not_staffing_evidence(self):
        result=inspect_tasks(workflow(),SELECTED)
        self.assertEqual(result['status'],'pass',result['findings'])
        self.assertEqual(set(result['tasks']),{'T_NORMAL','T_PEAK','T_ABSENCE','T_RECOVERY'})
        self.assertEqual(result['staffing_adequacy'],'not_evaluated')
        self.assertEqual(result['performance_qualification'],'not_evaluated')

    def test_selected_task_and_selected_fact_deletions_detected(self):
        for key in ['T_NORMAL','T_ABSENCE','T_RECOVERY']:
            r=deepcopy(REGISTER);r['tasks'].pop(key)
            self.assertEqual(inspect_tasks(workflow(r),SELECTED)['status'],'fail')
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts'].pop('training')
        result=inspect_tasks(workflow(r),SELECTED)
        self.assertIn('task_fact_missing',{x['rule'] for x in result['findings']})

    def test_unknown_skill_does_not_become_a_pass(self):
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['skills'].update(status='unknown',basis=None)
        self.assertEqual(inspect_tasks(workflow(r),SELECTED)['status'],'unknown')

    def test_project_may_select_a_smaller_fact_scope(self):
        r=deepcopy(REGISTER)
        for t in r['tasks'].values():t['facts']['training'].update(status='unknown',basis=None)
        selected=deepcopy(SELECTED)
        for e in selected.values():e['fields'].remove('training')
        self.assertEqual(inspect_tasks(workflow(r),selected)['status'],'pass')

    def test_reported_observation_cannot_come_from_a_proposal(self):
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['duration']['status']='reported'
        result=inspect_tasks(workflow(r),SELECTED)
        self.assertEqual(result['status'],'fail')
        self.assertIn('task_observation_basis',{x['rule'] for x in result['findings']})

    def test_synthetic_reported_source_is_attributed_without_qualifying_performance(self):
        r=deepcopy(REGISTER);record=deepcopy(RECORD)
        record['sources']['SYN_OBS']={'kind':'reported_observation','sha256':'a'*64,'excerpt':'Synthetic unit control only.'}
        r['tasks']['T_NORMAL']['facts']['duration'].update(status='reported',basis='SYN_OBS')
        w=workflow(r,record);w['sources']['SYN_OBS']={'status':'pass'}
        result=inspect_tasks(w,SELECTED)
        self.assertEqual(result['status'],'pass')
        self.assertEqual(result['performance_qualification'],'not_evaluated')

    def test_declared_but_unprovided_fact_basis_remains_unknown(self):
        r=deepcopy(REGISTER);record=deepcopy(RECORD)
        record['sources']['UNREAD']={'kind':'reported_observation','sha256':'a'*64,'excerpt':'Unprovided unit-control source'}
        r['tasks']['T_NORMAL']['facts']['duration'].update(status='reported',basis='UNREAD')
        result=inspect_tasks(workflow(r,record),SELECTED)
        self.assertEqual(result['status'],'unknown')
        self.assertIn('task_source_unchecked',{x['rule'] for x in result['findings']})

    def test_expected_context_and_responsibilities_are_retained(self):
        for change in [lambda t:t.update(function='F_RECOVER'),
                       lambda t:t.update(scenario='S_PEAK'),
                       lambda t:t['performers'][0].update(element='R_BACKUP'),
                       lambda t:t['performers'][0].update(role='monitor'),
                       lambda t:t['performers'][0].update(allocation='automation')]:
            r=deepcopy(REGISTER);change(r['tasks']['T_NORMAL'])
            self.assertEqual(inspect_tasks(workflow(r),SELECTED)['status'],'fail')

    def test_task_responsibility_requires_an_existing_function_allocation(self):
        record=deepcopy(RECORD)
        record['relations']={k:r for k,r in record['relations'].items() if not (r['kind']=='allocated_to' and r['from']=='F_REVIEW' and r['to']=='R_CLERK')}
        result=inspect_tasks(workflow(record=record),SELECTED)
        self.assertIn('task_allocation_missing',{x['rule'] for x in result['findings']})

    def test_missing_equipment_and_unrelated_evaluation_are_detected(self):
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['equipment']['refs']=['ABSENT']
        self.assertEqual(inspect_tasks(workflow(r),SELECTED)['status'],'fail')
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['evaluation']['refs']=['E_PEAK']
        self.assertIn('task_evaluation_binding',{x['rule'] for x in inspect_tasks(workflow(r),SELECTED)['findings']})

    def test_empty_dependency_is_unknown_and_not_a_technical_adequacy_claim(self):
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['procedure']['refs']=[]
        self.assertEqual(inspect_tasks(workflow(r),SELECTED)['status'],'unknown')

    def test_durations_are_exact_nonnegative_and_units_are_bounded(self):
        for value in [-1,0.1,'-1','1e100']:
            r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['duration']['value']=value
            self.assertRaises(ValueError,schema,r)
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['duration']['unit']='fortnight'
        self.assertEqual(inspect_tasks(workflow(r),SELECTED)['status'],'unsupported')
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['duration']['value']=None
        self.assertEqual(inspect_tasks(workflow(r),SELECTED)['status'],'unknown')

    def test_missing_duplicate_and_wrong_owner_registers_cannot_pass(self):
        w=workflow();w['supplemental_documents']={}
        self.assertEqual(inspect_tasks(w,SELECTED)['status'],'fail')
        w=workflow();w['supplemental_documents']['cseHumanTasks']*=2
        self.assertEqual(inspect_tasks(w,SELECTED)['status'],'error')
        w=workflow();w['supplemental_documents']['cseHumanTasks'][0]['owner']='NotAConcern'
        self.assertEqual(inspect_tasks(w,SELECTED)['status'],'error')

    def test_unknown_profile_and_duplicate_json_cannot_pass(self):
        r=deepcopy(REGISTER);r['version']='future'
        self.assertEqual(inspect_tasks(workflow(r),SELECTED)['status'],'unsupported')
        w=workflow();w['supplemental_documents']['cseHumanTasks'][0]['body']=MARKER+'\n{"version":1,"version":1,"tasks":{}}'
        self.assertEqual(inspect_tasks(w,SELECTED)['status'],'error')

    def test_task_expectations_require_the_new_explicit_scope_version(self):
        scope=deepcopy(SCOPE);scope['version']='concept-review-1.0'
        self.assertRaises(ValueError,scope_schema,scope)
        scope=deepcopy(SCOPE);scope['expectations']['TASK_NORMAL']['fields']=['fatigue']
        self.assertRaises(ValueError,scope_schema,scope)

    def test_automation_only_task_does_not_invent_a_human_or_training_obligation(self):
        r=deepcopy(REGISTER);selected=deepcopy(SELECTED)
        for key,task in r['tasks'].items():task['performers']=[p for p in task['performers'] if p['allocation']=='automation']
        for e in selected.values():
            e['performers']=[p for p in e['performers'] if p['allocation']=='automation']
            e['fields']=['entry','completion']
        self.assertEqual(inspect_tasks(workflow(r),selected)['status'],'pass')


@unittest.skipUnless(PARSER,'Install the pinned SysML parser')
class NativeTaskControls(unittest.TestCase):
    def run_variant(self,register=REGISTER,record=RECORD,scope=SCOPE,model_text=None):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            d=Path(directory)
            text=replace_document(TEXT,'cseWorkflow','CSE-WORKFLOW/1.0',record)
            text=replace_document(text,'cseHumanTasks',MARKER,register) if model_text is None else model_text
            model=d/'model.sysml';model.write_text(text)
            s=d/'scope.json';s.write_text(json.dumps(scope,indent=2)+'\n')
            return inspect_concept(model,s,sha256(s.read_bytes()).hexdigest(),{'CASE':EXAMPLE/'brief.md'})

    def test_unresolved_question_retains_selected_task_checks_and_omissions(self):
        record=deepcopy(RECORD)
        record['questions']['Q_OPEN']={'text':'Training observations remain unavailable.','affects':['F_REVIEW'],'blocking':True}
        result=self.run_variant(record=record)
        self.assertEqual(result['workflow_status'],'unknown')
        self.assertEqual(result['status'],'unknown',result)
        self.assertEqual(result['human_task_status'],'pass')
        self.assertEqual(result['coverage']['not_run'],[])
        register=deepcopy(REGISTER);register['tasks']['T_NORMAL']['facts'].pop('training')
        result=self.run_variant(register,record)
        self.assertEqual(result['status'],'fail',result)
        self.assertIn('task_fact_missing',{f['rule'] for f in result['findings']})

    def test_actual_four_context_register_and_human_view(self):
        result=self.run_variant()
        self.assertEqual(result['status'],'pass',result['findings'])
        self.assertEqual(result['human_task_status'],'pass')
        self.assertEqual(len(result['human_tasks']['tasks']),4)
        self.assertEqual(result['coverage']['not_run'],[])
        self.assertIn('Primary clerk',render_text(result))
        self.assertEqual(result['human_tasks']['staffing_adequacy'],'not_evaluated')

    def test_native_omissions_and_wrong_role_do_not_hide_behind_generic_counts(self):
        for case in ['task','training','performer','allocation']:
            with self.subTest(case=case):
                register=deepcopy(REGISTER);record=deepcopy(RECORD)
                if case=='task':register['tasks'].pop('T_NORMAL')
                if case=='training':register['tasks']['T_NORMAL']['facts'].pop('training')
                if case=='performer':register['tasks']['T_NORMAL']['performers'][0]['element']='R_BACKUP'
                if case=='allocation':record['relations']={k:r for k,r in record['relations'].items() if not (r['kind']=='allocated_to' and r['from']=='F_REVIEW' and r['to']=='R_CLERK')}
                result=self.run_variant(register,record)
                self.assertEqual(result['workflow_status'],'pass',result['findings'])
                self.assertEqual(result['allocation_status'],'pass')
                self.assertEqual(result['status'],'fail',result['findings'])

    def test_native_unknown_skill_and_unsupported_duration_do_not_pass(self):
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['skills'].update(status='unknown',basis=None)
        self.assertEqual(self.run_variant(r)['status'],'unknown')
        r=deepcopy(REGISTER);r['tasks']['T_NORMAL']['facts']['duration']['unit']='fortnight'
        self.assertEqual(self.run_variant(r)['status'],'unsupported')

    def test_missing_native_register_and_unknown_protocol_are_refused(self):
        without=TEXT.split('package TaskRegister {')[0]
        result=self.run_variant(model_text=without)
        self.assertEqual(result['status'],'fail')
        r=deepcopy(REGISTER);r['version']='future'
        result=self.run_variant(r)
        self.assertEqual(result['status'],'unsupported')
        self.assertEqual(result['coverage']['not_run'],sorted(SELECTED))

    def test_actual_scenario_shape_and_launcher_from_another_directory(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            launcher=ROOT/'.agents/skills/develop-operational-scenarios/scripts/cse.py'
            cmd=[sys.executable,'-B',str(launcher),'concept-review','check',str(EXAMPLE/'concept.sysml'),'--scope',str(EXAMPLE/'scope.json'),'--scope-sha256',(EXAMPLE/'scope.sha256').read_text().strip(),'--source','CASE='+str(EXAMPLE/'brief.md'),'--json']
            r=subprocess.run(cmd,cwd=directory,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertEqual(json.loads(r.stdout)['human_task_status'],'pass')
            shape=subprocess.run([sys.executable,'-B',str(launcher),'check',str(EXAMPLE/'concept.sysml'),'--syntax-only','--kind','scenario','--json'],cwd=directory,capture_output=True,text=True)
            self.assertEqual(shape.returncode,0,shape.stdout+shape.stderr)

    def test_native_declared_but_unprovided_task_source_is_unknown(self):
        r=deepcopy(REGISTER);record=deepcopy(RECORD)
        record['sources']['UNREAD']={'kind':'reported_observation','sha256':'a'*64,'excerpt':'Unprovided native-control source'}
        r['tasks']['T_NORMAL']['facts']['duration'].update(status='reported',basis='UNREAD')
        result=self.run_variant(r,record)
        self.assertEqual(result['workflow_status'],'pass')
        self.assertEqual(result['status'],'unknown')
        self.assertIn('task_source_unchecked',{x['rule'] for x in result['findings']})


if __name__=='__main__':unittest.main()
