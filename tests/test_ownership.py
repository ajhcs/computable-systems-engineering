"""Selected ownership, party identity, withdrawal and source-provenance controls."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verifier.ownership import inspect_ownership,MARKER
from verifier.concept_review import inspect_concept,schema as scope_schema
from verifier.sysml import JAR,CLASSES

EXAMPLE=ROOT/'examples/ownership-review';TEXT=(EXAMPLE/'concept.sysml').read_text()
SCOPE=json.loads((EXAMPLE/'scope.json').read_text())
RECORD=json.loads(TEXT.split('doc cseWorkflow /*CSE-WORKFLOW/1.0',1)[1].split('*/',1)[0])
REGISTER=json.loads(TEXT.split('doc cseOwnership /*'+MARKER,1)[1].split('*/',1)[0])
SELECTED={k:v for k,v in SCOPE['expectations'].items() if v['kind']=='ownership'}
PARSER=JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file()


def workflow(register=REGISTER,record=RECORD):
    return {'record':deepcopy(record),'sources':{'CASE':{'status':'pass'}},
        'native_inventory':{'concerns':[{'qualified_name':'OwnershipRegister::ownershipContext'}]},
        'supplemental_documents':{'cseOwnership':[{'owner':'OwnershipRegister::ownershipContext',
            'body':MARKER+'\n'+json.dumps(register)}]}}


def replace(text,name,marker,value):
    before,rest=text.split('doc '+name+' /*'+marker,1);_,after=rest.split('*/',1)
    payload=json.dumps(value,indent=2).replace('/*',r'\u002f*').replace('*/',r'*\u002f')
    return before+'doc '+name+' /*'+marker+'\n'+payload+'\n*/'+after


class OwnershipControls(unittest.TestCase):
    def test_proposed_roles_and_shared_interface_do_not_authenticate_commitments(self):
        result=inspect_ownership(workflow(),SELECTED)
        self.assertEqual(result['status'],'pass',result['findings'])
        self.assertEqual(result['items']['I_API']['roles']['change']['parties'],['ORG_ALPHA','ORG_BETA'])
        self.assertEqual(result['actual_commitments'],'not_authenticated')
        self.assertEqual(result['protected_authority'],'not_evaluated')

    def test_item_role_and_fact_removals_are_detected(self):
        for change in [lambda r:r['items'].pop('E_ALPHA'),
                       lambda r:r['items']['E_ALPHA']['roles'].pop('support'),
                       lambda r:r['items']['I_API']['facts'].pop('withdrawal')]:
            r=deepcopy(REGISTER);change(r)
            self.assertEqual(inspect_ownership(workflow(r),SELECTED)['status'],'fail')

    def test_party_identity_target_kind_and_interface_relation_are_checked(self):
        r=deepcopy(REGISTER);r['items']['E_ALPHA']['roles']['change']['parties']=['ORG_BETA']
        self.assertEqual(inspect_ownership(workflow(r),SELECTED)['status'],'fail')
        r=deepcopy(REGISTER);r['items']['I_API']['target_kind']='element'
        self.assertEqual(inspect_ownership(workflow(r),SELECTED)['status'],'fail')
        record=deepcopy(RECORD);record['relations'].pop('I_API')
        self.assertEqual(inspect_ownership(workflow(record=record),SELECTED)['status'],'fail')

    def test_unknown_and_withdrawn_selected_commitments_do_not_pass(self):
        for status,expected in [('unknown','unknown'),('withdrawn','fail')]:
            r=deepcopy(REGISTER);r['items']['I_API']['facts']['agreement']['status']=status
            self.assertEqual(inspect_ownership(workflow(r),SELECTED)['status'],expected)

    def test_unprovided_basis_and_relabelled_proposal_are_not_evidence(self):
        r=deepcopy(REGISTER);record=deepcopy(RECORD)
        record['sources']['UNREAD']={'kind':'reported_observation','sha256':'a'*64,'excerpt':'Not supplied'}
        r['items']['I_API']['facts']['agreement'].update(status='reported',basis='UNREAD')
        self.assertEqual(inspect_ownership(workflow(r,record),SELECTED)['status'],'unknown')
        r=deepcopy(REGISTER);r['items']['I_API']['facts']['agreement']['status']='reported'
        self.assertEqual(inspect_ownership(workflow(r),SELECTED)['status'],'fail')

    def test_project_can_select_fewer_roles_without_universal_funding_requirement(self):
        r=deepcopy(REGISTER);selected=deepcopy(SELECTED)
        for item in r['items'].values():item['roles']['fund'].update(status='unknown',basis=None)
        for expected in selected.values():expected['roles'].pop('fund')
        self.assertEqual(inspect_ownership(workflow(r),selected)['status'],'pass')

    def test_missing_register_bad_owner_duplicate_and_unknown_profile_are_refused(self):
        w=workflow();w['supplemental_documents']={}
        self.assertEqual(inspect_ownership(w,SELECTED)['status'],'fail')
        w=workflow();w['supplemental_documents']['cseOwnership']*=2
        self.assertEqual(inspect_ownership(w,SELECTED)['status'],'error')
        w=workflow();w['supplemental_documents']['cseOwnership'][0]['owner']='Absent'
        self.assertEqual(inspect_ownership(w,SELECTED)['status'],'error')
        r=deepcopy(REGISTER);r['version']='future'
        self.assertEqual(inspect_ownership(workflow(r),SELECTED)['status'],'unsupported')

    def test_old_scope_cannot_silently_admit_new_meaning(self):
        for version in ['concept-review-1.0','concept-review-1.1']:
            s=deepcopy(SCOPE);s['version']=version;self.assertRaises(ValueError,scope_schema,s)

    def test_bad_party_and_absent_source_are_structural_failures(self):
        r=deepcopy(REGISTER);r['items']['E_ALPHA']['roles']['operate']['parties']=['ABSENT']
        self.assertEqual(inspect_ownership(workflow(r),SELECTED)['status'],'fail')
        r=deepcopy(REGISTER);r['items']['E_ALPHA']['roles']['operate']['basis']='ABSENT'
        self.assertEqual(inspect_ownership(workflow(r),SELECTED)['status'],'fail')


@unittest.skipUnless(PARSER,'Install the pinned SysML parser')
class NativeOwnershipControls(unittest.TestCase):
    def inspect_variant(self,register=REGISTER,record=RECORD,model_text=None):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            model=Path(directory)/'model.sysml'
            text=replace(TEXT,'cseWorkflow','CSE-WORKFLOW/1.0',record)
            text=replace(text,'cseOwnership',MARKER,register) if model_text is None else model_text
            model.write_text(text)
            return inspect_concept(model,EXAMPLE/'scope.json',(EXAMPLE/'scope.sha256').read_text().strip(),{'CASE':EXAMPLE/'brief.md'})

    def test_native_baseline_and_whole_item_role_fact_omissions(self):
        base=self.inspect_variant();self.assertEqual(base['status'],'pass',base['findings'])
        for change in [lambda r:r['items'].pop('E_ALPHA'),lambda r:r['items']['E_ALPHA']['roles'].pop('support'),lambda r:r['items']['I_API']['facts'].pop('change_control')]:
            r=deepcopy(REGISTER);change(r);result=self.inspect_variant(r)
            self.assertEqual(result['workflow_status'],'pass')
            self.assertEqual(result['status'],'fail',result['findings'])

    def test_native_changed_authority_unknown_agreement_and_withdrawal(self):
        r=deepcopy(REGISTER);r['items']['I_API']['roles']['change']['parties']=['ORG_COORD']
        self.assertEqual(self.inspect_variant(r)['status'],'fail')
        r=deepcopy(REGISTER);r['items']['I_API']['facts']['agreement']['status']='unknown'
        self.assertEqual(self.inspect_variant(r)['status'],'unknown')
        r=deepcopy(REGISTER);r['items']['I_API']['roles']['support']['status']='withdrawn'
        self.assertEqual(self.inspect_variant(r)['status'],'fail')

    def test_unresolved_question_retains_responsibility_review_and_withdrawal(self):
        record=deepcopy(RECORD)
        record['questions']['Q_OPEN']={'text':'Constituent agreement remains proposed.','affects':['E_ALPHA'],'blocking':True}
        result=self.inspect_variant(record=record)
        self.assertEqual(result['workflow_status'],'unknown')
        self.assertEqual(result['status'],'unknown',result)
        self.assertEqual(result['ownership_status'],'pass')
        self.assertEqual(result['coverage']['not_run'],[])
        register=deepcopy(REGISTER);register['items']['I_API']['roles']['support']['status']='withdrawn'
        result=self.inspect_variant(register,record)
        self.assertEqual(result['status'],'fail',result)
        self.assertIn('ownership_withdrawn',{f['rule'] for f in result['findings']})

    def test_native_unprovided_claim_basis_and_missing_interface_do_not_pass(self):
        r=deepcopy(REGISTER);record=deepcopy(RECORD)
        record['sources']['UNREAD']={'kind':'reported_observation','sha256':'a'*64,'excerpt':'Unprovided native-control source'}
        r['items']['I_API']['facts']['agreement'].update(status='reported',basis='UNREAD')
        self.assertEqual(self.inspect_variant(r,record)['status'],'unknown')
        r=deepcopy(REGISTER);record=deepcopy(RECORD);record['relations'].pop('I_API')
        for item in r['items'].values():
            for fact in item['facts'].values():fact['refs']=[x for x in fact['refs'] if x!='I_API']
        result=self.inspect_variant(r,record)
        self.assertEqual(result['status'],'fail')
        self.assertIn('ownership_target',{x['rule'] for x in result['findings']})

    def test_native_missing_and_unsupported_ownership_registers_are_non_successful(self):
        self.assertEqual(self.inspect_variant(model_text=TEXT.split('package OwnershipRegister {')[0])['status'],'fail')
        r=deepcopy(REGISTER);r['version']='future';result=self.inspect_variant(r)
        self.assertEqual(result['status'],'unsupported')
        self.assertEqual(set(result['coverage']['not_run']),set(SELECTED))

    def test_actual_launcher_from_another_directory(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            r=subprocess.run([sys.executable,'-B',str(ROOT/'.agents/skills/develop-system-concept/scripts/cse.py'),
                'concept-review','check',str(EXAMPLE/'concept.sysml'),'--scope',str(EXAMPLE/'scope.json'),
                '--scope-sha256',(EXAMPLE/'scope.sha256').read_text().strip(),'--source','CASE='+str(EXAMPLE/'brief.md')],
                cwd=directory,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertIn('actual commitments not authenticated',r.stdout)


if __name__=='__main__':unittest.main()
