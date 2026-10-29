#!/usr/bin/env python3
"""Independent controls for bounded workflow record/source/native semantics."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verifier.foundation import Invalid
from verifier.workflow import (schema,analyze,inspect_workflow,render_text,draft_model,write_draft,empty_record,JOBS,MARKER,capture_model_inputs)
ROOT=Path(__file__).resolve().parents[1]


def fixture():
    r=empty_record('Compare two system concepts','concept');text='Explicit invented basis for these controls.'
    r['question']['basis']='SRC';r['sources']={'SRC':{'sha256':sha256(text.encode()).hexdigest(),'excerpt':text,'kind':'proposal'}}
    def element(kind,name):return {'kind':kind,'native_name':'Demo::'+name,'label':name,'description':'Explicit synthetic '+name,'basis':'SRC','status':'proposed'}
    r['elements']={'N':element('need','Need'),'F':element('function','Function'),'P':element('element','Part'),'A':element('concept','Alpha'),'B':element('concept','Beta'),'C':element('criterion','Cost')}
    r['relations']={'R':{'kind':'addresses','from':'F','to':'N','basis':'SRC','label':'responds to need'}}
    for job in JOBS:r['workflows'][job]={'focus':['F'],'summary':'Consider explicit synthetic work','conditions':'Under stated synthetic conditions','outcome':'A useful bounded draft','next_decision':'Collect qualifying evidence'}
    native={'status':'pass','model_sha256':'a'*64,'parser':{'name':'control'},'inventory':{'concerns':[{'qualified_name':'Demo::Need'},{'qualified_name':'Demo::Alpha'},{'qualified_name':'Demo::Beta'},{'qualified_name':'Demo::Cost'}],'actions':[{'qualified_name':'Demo::Function'}],'parts':[{'qualified_name':'Demo::Part'}],'requirements':[],'documents':[]}}
    evidence={'SRC':{'status':'pass','detail':'Synthetic matching bytes','kind':'proposal'}}
    return r,native,evidence,text


class WorkflowControls(unittest.TestCase):
    def inspect(self,r=None,native=None,evidence=None,job='concept',**kw):
        a,b,c,_=fixture();return analyze(a if r is None else r,b if native is None else native,c if evidence is None else evidence,workflow=job,**kw)
    def test_valid_scoped_draft_and_no_acceptance(self):
        r=self.inspect();self.assertEqual(r['status'],'pass');self.assertEqual(r['acceptance'],'not_evaluated');self.assertEqual(r['required_review'],'not_evaluated');self.assertEqual(r['conditional_analysis'],'not_run')
    def test_endpoint_closure_does_not_walk_whole_graph(self):
        a,b,c,_=fixture();a['relations']['X']={'kind':'interfaces_with','from':'P','to':'P','basis':'SRC','label':''};r=self.inspect(a,b,c)
        self.assertEqual(set(r['view']['elements']),{'F','N'});self.assertEqual(r['view']['boundary_ids'],['N']);self.assertNotIn('P',r['selected_ids']);self.assertIn('P',r['view']['omitted_ids'])
    def test_immutable_record_and_report(self):
        a,b,c,_=fixture();before=deepcopy((a,b,c));r=self.inspect(a,b,c);self.assertEqual((a,b,c),before);r['record']['question']['text']='changed';self.assertEqual((a,b,c),before)
    def test_wrong_native_kind(self):
        a,b,c,_=fixture();a['elements']['F']['native_name']='Demo::Part';r=self.inspect(a,b,c);self.assertEqual(r['status'],'fail');self.assertEqual(r['view'],{})
    def test_missing_native_identity(self):
        a,b,c,_=fixture();b['inventory']['actions']=[];self.assertEqual(self.inspect(a,b,c)['status'],'fail')
    def test_ambiguous_native_identity(self):
        a,b,c,_=fixture();b['inventory']['actions']*=2;self.assertEqual(self.inspect(a,b,c)['status'],'fail')
    def test_duplicate_role_alias(self):
        a,b,c,_=fixture();a['elements']['F2']=deepcopy(a['elements']['F']);self.assertEqual(self.inspect(a,b,c)['status'],'fail')
    def test_distinct_roles_do_not_invent_instances(self):
        a,b,c,_=fixture();a['elements']['PERSON']=deepcopy(a['elements']['P']);a['elements']['PERSON']['kind']='actor';self.assertEqual(self.inspect(a,b,c)['status'],'pass')
    def test_dangling_relation(self):
        a,b,c,_=fixture();a['relations']['R']['to']='Absent';self.assertEqual(self.inspect(a,b,c)['status'],'fail')
    def test_typed_relation_refuses_wrong_direction(self):
        a,b,c,_=fixture();a['relations']['R'].update({'from':'N','to':'F'});self.assertEqual(self.inspect(a,b,c)['status'],'fail')
    def test_unsupported_relation_not_generic_graph(self):
        a,b,c,_=fixture();a['relations']['R']['kind']='executes_guard';r=self.inspect(a,b,c);self.assertEqual(r['status'],'unsupported');self.assertEqual(r['view'],{})
    def test_decomposition_cycle(self):
        a,b,c,_=fixture();a['elements']['P2']=deepcopy(a['elements']['P']);a['elements']['P2']['native_name']='Demo::Part2';b['inventory']['parts'].append({'qualified_name':'Demo::Part2'});a['relations']={'D1':{'kind':'decomposes','from':'P','to':'P2','basis':'SRC','label':''},'D2':{'kind':'decomposes','from':'P2','to':'P','basis':'SRC','label':''}};self.assertEqual(self.inspect(a,b,c)['status'],'fail')
    def test_unrelated_blocking_question_not_in_scope(self):
        a,b,c,_=fixture();a['questions']['Q']={'text':'Unrelated question','affects':['P'],'blocking':True};self.assertEqual(self.inspect(a,b,c)['status'],'pass')
    def test_relevant_blocking_question_unknown(self):
        a,b,c,_=fixture();a['questions']['Q']={'text':'Resolve relevant condition','affects':['F'],'blocking':True};self.assertEqual(self.inspect(a,b,c)['status'],'unknown')
    def test_missing_source_unknown(self):self.assertEqual(self.inspect(evidence={})['status'],'unknown')
    def test_stale_source_fails(self):self.assertEqual(self.inspect(evidence={'SRC':{'status':'fail','detail':'Stale'}})['status'],'fail')
    def test_incomplete_start(self):
        a=empty_record('What next?','concept');_,b,_,_=fixture();r=self.inspect(a,b,{});self.assertEqual(r['status'],'unknown');self.assertEqual(r['view']['elements'],{})
    def test_review_is_unsupported_not_success(self):self.assertEqual(self.inspect(review=True)['status'],'unsupported')
    def test_received_invalid_selection_not_validated(self):
        r=self.inspect(ids=['Absent']);self.assertEqual(r['status'],'error');self.assertEqual(r['request']['ids'],['Absent']);self.assertEqual(r['view'],{})
    def test_unknown_fields_and_global_id_collision(self):
        a,_,_,_=fixture();a['execute']='anything';self.assertRaises(Invalid,schema,a)
        a,_,_,_=fixture();a['questions']['F']={'text':'Q','affects':[],'blocking':False};self.assertRaises(Invalid,schema,a)
    def test_documentary_hyphen_id_native_emission_separate(self):
        a,_,_,_=fixture();a['questions']['Q-1']={'text':'Q','affects':[],'blocking':False};schema(a);self.assertRaises(Invalid,draft_model,a,'bad-package')
    def test_plan_cannot_be_observed_result(self):
        a,_,_,_=fixture();a['evidence']['E']={'target':'F','purpose':'verification','mode':'plan','method':'Inspection','environment':'Lab','basis':'SRC','result':'supported','limitations':'Synthetic'};self.assertRaises(Invalid,schema,a)
    def test_assessment_does_not_become_verified(self):
        a,b,c,_=fixture();a['evidence']['E']={'target':'F','purpose':'validation','mode':'assessment','method':'Interview','environment':'Hypothetical','basis':'SRC','result':'supported','limitations':'Reported only'};r=self.inspect(a,b,c);self.assertEqual(r['status'],'pass');self.assertEqual(r['acceptance'],'not_evaluated');self.assertIn('reported result supported',render_text(r))
    def test_native_refusal_keeps_diagnostic_shape(self):
        a,b,c,_=fixture();b.update(status='error',findings=[{'code':'native_error','detail':'Native refused'}]);r=self.inspect(a,b,c);self.assertEqual(r['status'],'error');self.assertEqual(r['view'],{});self.assertIn('Native refused',render_text(r,True))
    def test_json_and_human_views_same_status_unknowns(self):
        r=self.inspect(evidence={});text=render_text(r);expert=render_text(r,True);self.assertIn('Declared draft checks: unknown',text);self.assertIn('Declared draft checks: unknown',expert)
        for f in r['findings']:self.assertIn(f['detail'],text);self.assertIn(f['detail'],expert)
    def trade(self):
        a,b,c,_=fixture();a['workflows']['trade-study']['focus']=['A','B','C'];a['trade_studies']['T']={'question':'Which candidate?', 'alternatives':['A','B'],'criteria':{'C':{'kind':'constraint','measure':'Cost','unit':'USD','weight':None,'basis':'SRC'}},'assessments':{'A':{'C':{'finding':'supported','value':'5','basis':'SRC','uncertainty':'Hypothetical'}},'B':{'C':{'finding':'unknown','value':None,'basis':None,'uncertainty':'Unmeasured'}}},'method':'qualitative','preference_basis':None,'recommendation':'No selection'};return a,b,c
    def test_trade_missing_assessment_not_favorable_default(self):
        a,b,c=self.trade();r=self.inspect(a,b,c,job='trade-study');self.assertEqual(r['status'],'unknown');self.assertEqual(r['view']['trade_studies']['T']['selection'],'not_made')
    def test_trade_no_weighted_numeric_guess(self):
        a,b,c=self.trade();a['trade_studies']['T']['method']='weighted_sum';r=self.inspect(a,b,c,job='trade-study');self.assertEqual(r['status'],'unsupported');self.assertEqual(r['conditional_analysis'],'not_run')
    def test_trade_constraint_cannot_be_offset(self):
        a,b,c=self.trade();a['trade_studies']['T']['assessments']['A']['C']['finding']='contradicted';self.assertEqual(self.inspect(a,b,c,job='trade-study')['status'],'fail')
    def test_exact_decimal_no_float_or_nonfinite(self):
        a,b,c=self.trade();a['trade_studies']['T']['criteria']['C']['weight']=0.5;self.assertRaises(Invalid,schema,a)
    def test_draft_base_preserved_and_never_overwritten(self):
        a=empty_record('Use current system','concept');base='package Original { part def Unit; }\n';text=draft_model(a,'Meta',base);self.assertTrue(text.startswith(base));self.assertIn(MARKER,text)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            path=Path(d)/'draft.sysml';write_draft(path,text);self.assertRaises(FileExistsError,write_draft,path,text)
    def test_doc_delimiter_is_encoded(self):
        a=empty_record('A */ delimiter /* stays data','concept');text=draft_model(a,'Meta');self.assertIn(r'*\u002f',text);self.assertIn(r'\u002f*',text)
    def test_native_draft_member_scope_is_explicit(self):
        a,_,_,_=fixture();self.assertRaises(Invalid,draft_model,a,'Different')
    def definitions(self):
        a,b,c,_=fixture();a['relations']={}
        for key,name in [('D1','Assembly'),('D2','Component')]:
            a['elements'][key]={'kind':'element_definition','native_name':'Demo::'+name,'label':name,'description':'Source definition','basis':'SRC','status':'proposed'}
        b['inventory']['part_definitions']=[{'qualified_name':'Demo::Assembly'},{'qualified_name':'Demo::Component'}]
        a['relations']['DD']={'kind':'decomposes','from':'D1','to':'D2','basis':'SRC','label':'documentary definition reading'}
        a['workflows']['architecture']['focus']=['D1'];return a,b,c
    def test_addresses_admitted_design_trace_preserves_no_satisfaction_claim(self):
        for left in ['function','system','element']:
            for right in ['need','requirement']:
                a,b,c,_=fixture();a['elements']['P']['kind']=left
                if left=='function':a['elements']['P']['native_name']='Demo::Design';b['inventory']['actions'].append({'qualified_name':'Demo::Design'})
                a['elements']['N']['kind']=right
                if right=='requirement':b['inventory']['requirements'].append({'qualified_name':'Demo::Need'})
                a['relations']['R']['from']='P';a['workflows']['architecture']['focus']=['P']
                r=self.inspect(a,b,c,job='architecture');self.assertEqual(r['status'],'pass');self.assertEqual(r['conditional_analysis'],'not_run');self.assertEqual(r['acceptance'],'not_evaluated')

    def test_definition_binding_and_human_scope(self):
        a,b,c=self.definitions();r=self.inspect(a,b,c,job='architecture');self.assertEqual(r['status'],'pass')
        self.assertEqual(r['bindings']['D1']['native_category'],'part_definitions');self.assertEqual(r['view']['elements']['D1']['kind'],'element_definition');self.assertIn('Definition-level documentary hierarchy',render_text(r))
    def test_definition_not_usage_and_usage_not_definition(self):
        for kind in ['element','system','actor']:
            a,b,c=self.definitions();a['elements']['D1']['kind']=kind;r=self.inspect(a,b,c,job='architecture');self.assertEqual(r['status'],'fail')
        a,b,c=self.definitions();a['elements']['P']['kind']='element_definition';self.assertEqual(self.inspect(a,b,c)['status'],'fail')
    def test_definition_endpoint_not_silently_instance(self):
        for kind in ['addresses','allocated_to','interfaces_with','information_to','controls','participates_in','precedes','scenario_of','derives_from']:
            a,b,c=self.definitions();a['relations']['DD']['kind']=kind;self.assertEqual(self.inspect(a,b,c,job='architecture')['status'],'fail')
        a,b,c=self.definitions();a['relations']['DD']['to']='P';self.assertEqual(self.inspect(a,b,c,job='architecture')['status'],'fail')
    def test_emitter_preserves_keyword_names_and_definition_kind(self):
        a=empty_record('Keyword name control','architecture')
        a['elements']={'D':{'kind':'element_definition','native_name':'interface::part','label':'Source definition','description':'Definition','basis':None,'status':'proposed'}}
        text=draft_model(a,'interface');self.assertIn("package 'interface' {",text);self.assertIn("part def 'part';",text);self.assertNotIn("part 'part'",text)

    def mock_native(self,record,path):
        _,n,_,_=fixture();n['model_sha256']=sha256(path.read_bytes()).hexdigest();n['inventory']['concerns'].append({'qualified_name':'Demo::workflowContext'});n['inventory']['documents']=[{'name':'cseWorkflow','owner':'Demo::workflowContext','body':MARKER+'\n'+json.dumps(record)}];return n
    def test_inspection_captured_source_and_unique_excerpt(self):
        a,_,_,text=fixture()
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            model=Path(d)/'m.sysml';model.write_text('Captured native control');source=Path(d)/'source.md';source.write_text(text)
            with patch('verifier.workflow.check_sysml',side_effect=lambda p,**kw:self.mock_native(a,p)):
                r=inspect_workflow(model,{'SRC':source})
            self.assertEqual(r['status'],'pass');self.assertEqual(r['input_stability'],'pass');self.assertEqual(r['model_sha256'],sha256(model.read_bytes()).hexdigest())
    def test_digest_mismatch_clears_view(self):
        a,_,_,text=fixture()
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            model=Path(d)/'m.sysml';model.write_text('Captured');source=Path(d)/'s.md';source.write_text(text)
            def native(path,**kw):n=self.mock_native(a,path);n['model_sha256']='b'*64;return n
            with patch('verifier.workflow.check_sysml',side_effect=native):r=inspect_workflow(model,{'SRC':source})
            self.assertEqual(r['status'],'error');self.assertEqual(r['view'],{});self.assertEqual(r['model_sha256'],sha256(model.read_bytes()).hexdigest())
    def test_model_changed_during_parse(self):
        a,_,_,text=fixture()
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            model=Path(d)/'m.sysml';model.write_text('Before');source=Path(d)/'s.md';source.write_text(text)
            def native(path,**kw):n=self.mock_native(a,path);model.write_text('After');return n
            with patch('verifier.workflow.check_sysml',side_effect=native):r=inspect_workflow(model,{'SRC':source})
            self.assertEqual(r['status'],'error');self.assertEqual(r['input_stability'],'error');self.assertEqual(r['view'],{})
    def test_nonregular_model_refused_before_parser(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            real=Path(d)/'real';real.write_text('content');link=Path(d)/'link';link.symlink_to(real)
            with patch('verifier.workflow.check_sysml') as parser:r=inspect_workflow(link)
            self.assertEqual(r['status'],'error');parser.assert_not_called()
    def test_explicit_bundle_identity_matches_native_and_is_order_independent(self):
        from verifier.sysml import _model_input
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            a=Path(d)/'a.sysml';b=Path(d)/'b.sysml'
            a.write_text('package Alpha {}');b.write_text('package Beta {}')
            _, files, digest = capture_model_inputs([b,a])
            self.assertEqual((files,digest), _model_input([a,b])[1::2])
            self.assertEqual(capture_model_inputs([a])[2], sha256(a.read_bytes()).hexdigest())
            old=digest;b.write_text('package Changed {}')
            self.assertNotEqual(old,capture_model_inputs([a,b])[2])
            for invalid in ([a,a], [], [a]*129):
                with self.assertRaises(ValueError): capture_model_inputs(invalid)

    def test_bundle_captures_remaps_and_detects_dependency_mutation(self):
        from verifier.sysml import _model_input
        record,_,_,text=fixture()
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            a=Path(d)/'a.sysml';b=Path(d)/'b.sysml';source=Path(d)/'s.md'
            a.write_text('package Alpha {}');b.write_text('package Beta {}');source.write_text(text)
            def native(paths,**kw):
                _, files, _, digest = _model_input(paths)
                _, n, _, _ = fixture();n['model_sha256']=digest
                n['inventory']['concerns'].append({'qualified_name':'Demo::workflowContext'})
                n['inventory']['documents']=[{'source':files[1]['path'],'name':'cseWorkflow','owner':'Demo::workflowContext','body':MARKER+'\n'+json.dumps(record)}]
                n['inventory']['parts'][0]['source']=files[0]['path']
                return n
            with patch('verifier.workflow.check_sysml',side_effect=native):
                report=inspect_workflow([b,a],{'SRC':source})
            self.assertEqual(report['status'],'pass',report['findings'])
            self.assertEqual(len(report['model_files']),2)
            self.assertEqual(report['native_inventory']['parts'][0]['source'],str(a))
            def mutate(paths,**kw):
                n=native(paths,**kw);b.write_text('package Unexpected {}');return n
            with patch('verifier.workflow.check_sysml',side_effect=mutate):
                report=inspect_workflow([a,b],{'SRC':source})
            self.assertEqual(report['status'],'error');self.assertEqual(report['view'],{})
            self.assertIn('inputs_changed',{x['rule'] for x in report['findings']})
            def mutate_source(paths,**kw):
                n=native(paths,**kw);source.write_text(text+' changed');return n
            with patch('verifier.workflow.check_sysml',side_effect=mutate_source):
                report=inspect_workflow([a,b],{'SRC':source})
            # Sources are acquired after native parsing; a changed source must
            # fail its retained provenance rather than receive a successful review.
            self.assertEqual(report['status'],'fail')
            self.assertTrue(any(f['rule'].startswith('source_') for f in report['findings']))

    def test_bundle_diagnostics_preserve_original_dependency_file(self):
        from verifier.sysml import _model_input
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            a=Path(d)/'a.sysml';b=Path(d)/'b.sysml'
            a.write_text('package Alpha {}');b.write_text('invalid')
            def native(paths,**kw):
                _, files, _, digest = _model_input(paths)
                return {'status':'error','model_sha256':digest,'findings':[],
                    'parser_issues':[{'source':files[1]['path'],'line':3,'severity':'ERROR','message':'Invalid dependency'}]}
            with patch('verifier.workflow.check_sysml',side_effect=native):r=inspect_workflow([a,b])
            self.assertEqual(r['status'],'error');self.assertEqual(r['parser_issues'][0]['source'],str(b))
            self.assertEqual(r['parser_issues'][0]['line'],3)

    def test_scratch_uses_configured_cache_and_cleans_up_on_parser_exception(self):
        record,_,_,text=fixture()
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            model=Path(d)/'m.sysml';model.write_text('captured');cache=Path(d)/'private-cache'
            def refuse(path,**kw):
                self.assertTrue(path.is_relative_to(cache))
                self.assertEqual(path.stat().st_mode & 0o077,0)
                raise RuntimeError('parser stopped')
            with patch('verifier.workflow.CACHE',cache), patch('verifier.workflow.check_sysml',side_effect=refuse):
                result=inspect_workflow(model)
            self.assertEqual(result['status'],'error')
            self.assertEqual(result['view'],{})
            self.assertEqual(list((cache/'workflow-scratch').iterdir()),[])

    def test_duplicate_json_keys_refused(self):
        a,_,_,_=fixture()
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            model=Path(d)/'m.sysml';model.write_text('Captured')
            def native(path,**kw):n=self.mock_native(a,path);n['inventory']['documents'][0]['body']=MARKER+'\n'+json.dumps(a).replace('"version": "workflow-1.0"','"version": "workflow-1.0", "version": "workflow-1.0"');return n
            with patch('verifier.workflow.check_sysml',side_effect=native):r=inspect_workflow(model)
            self.assertEqual(r['status'],'error');self.assertEqual(r['view'],{})


if __name__=='__main__':
    (ROOT/'.tmp').mkdir(exist_ok=True)
    unittest.main()
