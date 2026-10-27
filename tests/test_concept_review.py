"""Project tailoring, omission detection, refusals and actual skill-launcher use."""
from copy import deepcopy
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
from verifier.concept_review import (schema, starter, compare, allocation_profile,
    inspect_concept, scope_diff, render_text)
from verifier.workflow import draft_model
from verifier.sysml import JAR, CLASSES

EXAMPLE = ROOT/'examples/concept-review/lending'
SOFTWARE = ROOT/'examples/concept-review/software'
SCOPE = json.loads((EXAMPLE/'scope.json').read_text())
MODEL_TEXT = (EXAMPLE/'concept.sysml').read_text()
BASE, PAYLOAD = MODEL_TEXT.split("package 'LendingMetadata' {", 1)
RECORD = json.loads(PAYLOAD.split('doc cseWorkflow /*CSE-WORKFLOW/1.0',1)[1].split('*/',1)[0])
PARSER = JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file()


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n')
    return sha256(path.read_bytes()).hexdigest()


class ScopeTests(unittest.TestCase):
    def test_complete_scope_has_no_coverage_findings(self):
        schema(SCOPE)
        self.assertEqual(compare(SCOPE,RECORD)[0],[])

    def test_empty_project_stays_incomplete(self):
        scope=starter('SMALL','Small project')
        findings,_=compare(scope,RECORD)
        self.assertIn('scope_empty',{x['rule'] for x in findings})
        self.assertTrue(all(x['status']=='unknown' for x in findings))

    def test_exclusions_need_reasons_and_cannot_disable_existing_checks(self):
        s=deepcopy(SCOPE);s['topics']['support']['applicability']='excluded'
        self.assertRaises(ValueError,schema,s)
        s=deepcopy(SCOPE);s['topics']['procurement_disposal']['rationale']=''
        self.assertIn('scope_applicability_unknown',{x['rule'] for x in compare(s,RECORD)[0]})

    def test_unresolved_topics_cannot_produce_a_pass(self):
        s=deepcopy(SCOPE);s['topics']['support']['applicability']='unresolved'
        self.assertIn('unknown',{x['status'] for x in compare(s,RECORD)[0]})

    def test_included_topic_without_expectations_is_unknown(self):
        s=deepcopy(SCOPE);s['topics']['new_work']={'applicability':'included','rationale':'New relevant work'}
        self.assertIn('topic_expectations_missing',{x['rule'] for x in compare(s,RECORD)[0]})

    def test_role_identity_is_checked_and_readable_alias_is_free(self):
        r=deepcopy(RECORD);r['elements']['R_TECH']['label']='Service partner'
        self.assertEqual(compare(SCOPE,r)[0],[])
        r['elements']['R_TECH']['native_name']='LendingExample::checkoutApp'
        self.assertIn('scoped_identity_changed',{x['rule'] for x in compare(SCOPE,r)[0]})

    def test_undirected_interface_endpoint_order_does_not_create_false_omission(self):
        r=deepcopy(RECORD)
        for relation in r['relations'].values():
            if relation['kind']=='interfaces_with':relation['from'],relation['to']=relation['to'],relation['from']
        self.assertEqual(compare(SCOPE,r)[0],[])

    def test_evaluation_plan_cannot_be_relabelled_as_observed_support(self):
        r=deepcopy(RECORD);r['evidence']['E_READY'].update(mode='assessment',result='supported')
        self.assertIn('evaluation_meaning_changed',{x['rule'] for x in compare(SCOPE,r)[0]})

    def test_counts_are_selected_and_no_default_minimum_is_invented(self):
        software=json.loads((SOFTWARE/'scope.json').read_text())
        self.assertIsNone(allocation_profile(software,RECORD,'a'*64))
        s=deepcopy(SCOPE);s['allocation_bounds']['functions']['F_RESTORE']={'min':2,'max':4}
        profile=allocation_profile(s,RECORD,'a'*64)
        key=next(k for k,v in profile['elements'].items() if v['native_name']=='LendingExample::MaintainTool')
        self.assertEqual(profile['allocations']['PROJECT']['function_bounds'][key],{'min':2,'max':4})

    def test_invalid_scope_fields_versions_and_boolean_bounds_refused(self):
        for change in [lambda s:s.update(extra=True),lambda s:s.update(version='future'),
                       lambda s:s['allocation_bounds']['functions']['F_RESTORE'].update(min=True),
                       lambda s:s['expectations']['LINK_01'].update(relation_kind='executes')]:
            s=deepcopy(SCOPE);change(s);self.assertRaises(ValueError,schema,s)

    def test_scope_diff_exposes_removed_expectations_and_changed_bounds(self):
        changed=deepcopy(SCOPE);changed['expectations'].pop('EXPECT_R_TECH')
        changed['allocation_bounds']['functions']['F_RESTORE']['min']=0
        diff=scope_diff(SCOPE,changed)
        self.assertEqual(diff['changes']['expectations']['removed'],['EXPECT_R_TECH'])
        self.assertTrue(diff['allocation_bounds_changed']);self.assertEqual(diff['acceptance'],'not_evaluated')

    def test_changed_scope_refused_before_native_check(self):
        with patch('verifier.concept_review.inspect_workflow') as native:
            report=inspect_concept(EXAMPLE/'concept.sysml',EXAMPLE/'scope.json','0'*64,{'SYN':EXAMPLE/'brief.md'})
        self.assertEqual(report['status'],'error');native.assert_not_called()

    def test_missing_or_wrong_source_ids_cannot_pass(self):
        digest=(EXAMPLE/'scope.sha256').read_text().strip()
        for sources in [{},{'OTHER':EXAMPLE/'brief.md'}]:
            with patch('verifier.concept_review.inspect_workflow') as native:
                result=inspect_concept(EXAMPLE/'concept.sysml',EXAMPLE/'scope.json',digest,sources)
            self.assertEqual(result['status'],'error');native.assert_not_called()

    def test_duplicate_json_and_symlink_scope_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            d=Path(directory);duplicate=d/'duplicate.json';duplicate.write_text('{"version":1,"version":1}')
            link=d/'link.json';link.symlink_to(EXAMPLE/'scope.json')
            for path in [duplicate,link]:
                result=inspect_concept(EXAMPLE/'concept.sysml',path,sha256(path.read_bytes()).hexdigest(),{})
                self.assertEqual(result['status'],'error')

    def test_initialization_never_overwrites_and_does_not_claim_coverage(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            cmd=[sys.executable,'-B',str(ROOT/'scripts/concept_review.py'),'init-scope',str(Path(directory)/'scope.json'),'--project','SMALL','--name','Small slice']
            first=subprocess.run(cmd,capture_output=True,text=True);second=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(first.returncode,0);self.assertEqual(json.loads(first.stdout)['status'],'unknown')
            self.assertNotEqual(second.returncode,0)


@unittest.skipUnless(PARSER,'Install the pinned SysML parser')
class NativeReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=inspect_concept(EXAMPLE/'concept.sysml',EXAMPLE/'scope.json',
            (EXAMPLE/'scope.sha256').read_text().strip(),{'SYN':EXAMPLE/'brief.md'})

    def test_baseline_native_counts_and_coverage(self):
        self.assertEqual(self.baseline['status'],'pass',self.baseline['findings'])
        self.assertEqual(self.baseline['workflow_status'],'pass')
        self.assertEqual(self.baseline['allocation_status'],'pass')
        self.assertEqual(self.baseline['acceptance'],'not_evaluated')
        self.assertIn('not executable',render_text(self.baseline))

    def inspect_variant(self,record,base=BASE,scope=SCOPE,source=None):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            d=Path(directory);model=d/'model.sysml';model.write_text(draft_model(record,'LendingMetadata',base))
            contract=d/'scope.json';digest=write_json(contract,scope)
            path=EXAMPLE/'brief.md'
            if source is not None:path=d/'brief.md';path.write_text(source)
            return inspect_concept(model,contract,digest,{'SYN':path})

    def test_seven_clean_omissions_against_the_original_scope(self):
        cases=['maintainer','procedure','lifecycle','kit','evaluation_plan','interface','need_trace']
        for case in cases:
            with self.subTest(case=case):
                r=deepcopy(RECORD);base=BASE
                remove={'procedure':['R_PROC'],'lifecycle':['S_MAINT','F_RESTORE','F_QUALIFY'],'kit':['R_KIT']}.get(case,[])
                for key in remove:
                    e=r['elements'].pop(key);name=e['native_name'].split('::')[-1]
                    base='\n'.join(line for line in base.splitlines() if not (line.strip().startswith('part '+name+' :') or line.strip()=='action def '+name+';'))+'\n'
                    r['relations']={k:x for k,x in r['relations'].items() if key not in (x['from'],x['to'])}
                    r['evidence']={k:x for k,x in r['evidence'].items() if x['target']!=key}
                    r['questions']={k:x for k,x in r['questions'].items() if key not in x['affects']}
                    for w in r['workflows'].values():w['focus']=[x for x in w['focus'] if x!=key]
                triples={'maintainer':('allocated_to','F_RESTORE','R_TECH'),
                    'interface':('interfaces_with','R_APP','R_STORE'),'need_trace':('addresses','F_ISSUE','N_ACCESS')}
                if case in triples:r['relations']={k:x for k,x in r['relations'].items() if (x['kind'],x['from'],x['to'])!=triples[case]}
                if case=='evaluation_plan':r['evidence'].pop('E_READY')
                report=self.inspect_variant(r,base)
                self.assertEqual(report['workflow_status'],'pass',report['findings'])
                self.assertEqual(report['status'],'fail',report['findings'])
                self.assertTrue(any(x['rule'].startswith(('missing_scoped','missing_evaluation')) for x in report['findings']))
                if case=='maintainer':self.assertEqual(report['allocation_status'],'pass')

    def test_unknown_unsupported_and_stale_input_cannot_pass(self):
        r=deepcopy(RECORD);r['evidence']['E_READY']['method']=''
        unknown=self.inspect_variant(r)
        self.assertEqual(unknown['status'],'unknown')
        self.assertEqual(unknown['coverage']['checked'],sorted(SCOPE['expectations']))
        self.assertEqual(unknown['coverage']['not_run'],[])
        self.assertEqual(unknown['workflow_status'],'unknown')
        r=deepcopy(RECORD);r['relations']['UNSUPPORTED']={'kind':'simulates','from':'F_RESTORE','to':'R_TECH','basis':'SYN','label':'not admitted'}
        self.assertEqual(self.inspect_variant(r)['status'],'unsupported')
        changed=(EXAMPLE/'brief.md').read_text()+'Unreviewed source revision.\n'
        self.assertEqual(self.inspect_variant(RECORD,source=changed)['status'],'fail')

    def test_project_ids_with_hyphens_keep_their_identity_through_allocation_checks(self):
        def rename(value):
            if type(value) is dict:return {rename(k):rename(v) for k,v in value.items()}
            if type(value) is list:return [rename(x) for x in value]
            return 'F-RESTORE' if value=='F_RESTORE' else value
        report=self.inspect_variant(rename(RECORD),scope=rename(SCOPE))
        self.assertEqual(report['status'],'pass',report['findings'])
        self.assertIn('F-RESTORE',report['allocation']['source_id_by_compiler_id'].values())

    def test_input_change_during_check_is_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            d=Path(directory);scope=d/'scope.json';digest=write_json(scope,SCOPE)
            def mutate(*args,**kwargs):
                scope.write_text('{}')
                return deepcopy(self.baseline['workflow'])
            with patch('verifier.concept_review.inspect_workflow',side_effect=mutate):
                result=inspect_concept(EXAMPLE/'concept.sysml',scope,digest,{'SYN':EXAMPLE/'brief.md'})
            self.assertEqual(result['status'],'error')
            self.assertIn('input_changed',{x['rule'] for x in result['findings']})

    def test_independent_launchers_and_software_tailoring_from_another_directory(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            for skill in ['develop-system-concept','develop-conops','develop-operational-scenarios']:
                launcher=ROOT/'.agents/skills'/skill/'scripts/cse.py'
                result=subprocess.run([sys.executable,'-B',str(launcher),'concept-review','fingerprint',str(SOFTWARE/'scope.json')],cwd=directory,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([sys.executable,'-B',str(ROOT/'.agents/skills/develop-system-concept/scripts/cse.py'),'concept-review','check',str(SOFTWARE/'concept.sysml'),'--scope',str(SOFTWARE/'scope.json'),'--scope-sha256',(SOFTWARE/'scope.sha256').read_text().strip(),'--source','BRIEF='+str(SOFTWARE/'brief.md'),'--source','CHECKS='+str(SOFTWARE/'checks.md'),'--json'],cwd=directory,capture_output=True,text=True)
            report=json.loads(result.stdout)
            self.assertEqual(result.returncode,0,report)
            self.assertEqual(report['allocation_status'],'not_run')
            self.assertEqual(report['status'],'pass')
            self.assertFalse(any('maintainer' in x['detail'].lower() for x in report['findings']))


    def test_native_parse_failure_is_a_report_with_diagnostics(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            model=Path(directory)/'invalid.sysml';model.write_text('package Broken { concern <N broken> Invalid; }')
            r=inspect_concept(model,EXAMPLE/'scope.json',(EXAMPLE/'scope.sha256').read_text().strip(),{'SYN':EXAMPLE/'brief.md'})
            self.assertEqual(r['status'],'error',r)
            self.assertTrue(any(f['rule']=='native_parser' for f in r['findings']),r)
            self.assertTrue(r['workflow']['parser_issues'])
            text=render_text(r)
            self.assertIn('native_parser',text)
            self.assertIn(str(model),text)
            self.assertLessEqual(text.count(' error native_parser '),8)
            if sum(f['rule']=='native_parser' for f in r['findings'])>8:
                self.assertIn('use --json for complete details',text)
            cmd=[sys.executable,str(ROOT/'skills/develop-system-concept/scripts/cse.py'),'concept-review','check',str(model),'--scope',str(EXAMPLE/'scope.json'),'--scope-sha256',(EXAMPLE/'scope.sha256').read_text().strip(),'--source','SYN='+str(EXAMPLE/'brief.md'),'--json']
            out=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(out.returncode,1,out.stderr+out.stdout)
            report=json.loads(out.stdout)
            self.assertTrue(any(f['rule']=='native_parser' for f in report['findings']),report)


if __name__=='__main__':
    unittest.main()
