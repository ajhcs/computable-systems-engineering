"""Original independent expectations for the admitted engineering profile."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.foundation import check_profile, inspect, execute, load_profile, Invalid, MAX_BYTES
from verifier.sysml import check_sysml, JAR

PROFILE = json.loads((ROOT/'examples/foundation/profile.json').read_text())
MODEL = ROOT/'examples/foundation/cse-self-model.sysml'
# Synthetic adapter snapshot for unit cases; actual native coverage is exercised in test_concept_review.py.
NATIVE = {'status':'pass', 'model_sha256':sha256(MODEL.read_bytes()).hexdigest(), 'inventory':{
 'parts':[{'qualified_name':'CSEFoundation::'+n} for n in ('system','engineer','assistant','checker','simulator')],
 'actions':[{'qualified_name':'CSEFoundation::'+n} for n in ('ReviewSource','CheckCandidate','DraftScenario')],
 'concerns':[{'qualified_name':'CSEFoundation::TraceableImprovement'}],
 'use_cases':[{'qualified_name':'CSEFoundation::ReviewChange',
              'subjects':[{'name':'unit','target':'CSEFoundation::system'}],
              'actors':[{'name':'owner','target':'CSEFoundation::engineer'},
                        {'name':'drafter','target':'CSEFoundation::assistant'}]}]}}


def result(change=lambda p:None, native=None):
    profile=deepcopy(PROFILE);change(profile)
    return check_profile(profile,deepcopy(NATIVE if native is None else native))


def rules(report): return {x['rule'] for x in report['findings']}


class FoundationTests(unittest.TestCase):
    def test_original_expected_self_model(self):
        r=result();self.assertEqual(r['status'],'pass');self.assertEqual(r['behavior'],'not_run')
        self.assertEqual(r['required_review'],'not_evaluated');self.assertEqual(r['acceptance'],'not_evaluated')
        self.assertFalse(r['capabilities']['SIMULATE']['available'])

    def test_scoped_conflicting_labels_do_not_merge(self):
        def change(p):
            t=deepcopy(p['terms']['T_FUNCTION']);t.update(namespace='Other',definition='Different source meaning.')
            p['terms']['OTHER_FUNCTION']=t
        self.assertEqual(result(change)['status'],'pass')

    def test_ambiguous_same_scope_definition_refused(self):
        def change(p): p['terms']['OTHER_FUNCTION']=deepcopy(p['terms']['T_FUNCTION'])
        self.assertIn('term_scope',rules(result(change)))

    def test_wrong_definition_kind(self):
        self.assertIn('term_binding',rules(result(lambda p:p['elements']['F_SOURCE'].update(term='T_ACTOR'))))

    def test_missing_native_element(self):
        self.assertIn('native_binding',rules(result(lambda p:p['elements']['F_SOURCE'].update(native_name='CSEFoundation::Absent'))))

    def test_wrong_relation_endpoint(self):
        self.assertEqual(result(lambda p:p['relations'].append({'kind':'supports','from':'A_ENGINEER','to':'F_SOURCE'}))['status'],'fail')

    def test_unsupported_relation_cannot_pass(self):
        r=result(lambda p:p['relations'].append({'kind':'equivalent_to','from':'F_SOURCE','to':'F_CHECK'}))
        self.assertEqual(r['status'],'unsupported')

    def test_duplicate_relation(self):
        self.assertIn('relation_duplicate',rules(result(lambda p:p['relations'].append(deepcopy(p['relations'][0])))))

    def test_hierarchy_cycle_and_wrong_kind(self):
        def cycle(p): p['relations'] += [{'kind':'decomposes','from':'F_SOURCE','to':'F_CHECK'},{'kind':'decomposes','from':'F_CHECK','to':'F_SOURCE'}]
        self.assertIn('hierarchy_cycle',rules(result(cycle)))
        self.assertIn('decomposition_kind',rules(result(lambda p:p['relations'].append({'kind':'decomposes','from':'F_SOURCE','to':'R_CHECKER'}))))

    def test_missing_actor_role_and_goal_are_unknown(self):
        def change(p):
            p['use_cases']['UC_REVIEW']['goal']=None
            p['use_cases']['UC_REVIEW']['actors']['A_ENGINEER'].update(role='unknown',invokes=None)
        r=result(change);self.assertEqual(r['status'],'unknown');self.assertIn('goal_missing',rules(r))
        self.assertIn('role_unknown',rules(r))

    def test_role_is_scoped_to_case(self):
        def change(p):
            a=p['use_cases']['UC_REVIEW']['actors'];a['A_ENGINEER'].update(role='secondary',invokes=False)
            a['A_ASSISTANT'].update(role='primary',invokes=True)
        self.assertEqual(result(change)['status'],'pass')

    def test_role_invocation_disagreement(self):
        self.assertIn('role_invocation',rules(result(lambda p:p['use_cases']['UC_REVIEW']['actors']['A_ENGINEER'].update(invokes=False))))

    def test_boundary_disagreement_and_unknown(self):
        self.assertIn('actor_boundary',rules(result(lambda p:p['use_cases']['UC_REVIEW']['actors']['A_ENGINEER'].update(boundary='internal'))))
        self.assertEqual(result(lambda p:p['use_cases']['UC_REVIEW']['actors']['A_ENGINEER'].update(boundary='unknown'))['status'],'unknown')

    def test_internal_actor_containment(self):
        p=deepcopy(PROFILE);n=deepcopy(NATIVE)
        p['elements']['A_ASSISTANT']['native_name']='CSEFoundation::system::worker'
        p['use_cases']['UC_REVIEW']['actors']['A_ASSISTANT']['boundary']='internal'
        n['inventory']['parts'].append({'qualified_name':'CSEFoundation::system::worker'})
        n['inventory']['use_cases'][0]['actors'][1]['target']='CSEFoundation::system::worker'
        self.assertEqual(check_profile(p,n)['status'],'pass')

    def test_missing_subject_remains_unknown(self):
        r=result(lambda p:p['use_cases']['UC_REVIEW'].update(subject=None))
        self.assertEqual(r['status'],'unknown')
        self.assertIn('subject_missing',rules(r));self.assertNotIn('native_subject',rules(r))

    def test_duplicate_native_actor_identity_refuses_contradictory_roles(self):
        def change(p):
            p['elements']['A_ALIAS']=deepcopy(p['elements']['A_ASSISTANT'])
            role=deepcopy(p['use_cases']['UC_REVIEW']['actors']['A_ASSISTANT'])
            role.update(role='primary',invokes=True)
            p['use_cases']['UC_REVIEW']['actors']['A_ALIAS']=role
        r=result(change);self.assertEqual(r['status'],'fail')
        self.assertIn('actor_identity',rules(r));self.assertIn('native_actors',rules(r))

    def test_duplicate_actor_identical_role_is_still_one_participant(self):
        def change(p):
            p['elements']['A_ALIAS']=deepcopy(p['elements']['A_ASSISTANT'])
            p['use_cases']['UC_REVIEW']['actors']['A_ALIAS']=deepcopy(p['use_cases']['UC_REVIEW']['actors']['A_ASSISTANT'])
        self.assertIn('actor_identity',rules(result(change)))

    def test_same_native_actor_can_have_distinct_roles_across_cases(self):
        p=deepcopy(PROFILE);n=deepcopy(NATIVE)
        p['elements']['UC_EDIT']=dict(p['elements']['UC_REVIEW'],native_name='CSEFoundation::EditChange')
        p['elements']['A_OTHER_ROLE']=deepcopy(p['elements']['A_ASSISTANT'])
        case=deepcopy(p['use_cases']['UC_REVIEW'])
        case['actors']['A_ENGINEER'].update(role='secondary',invokes=False)
        case['actors']['A_OTHER_ROLE']=case['actors'].pop('A_ASSISTANT');case['actors']['A_OTHER_ROLE'].update(role='primary',invokes=True)
        p['use_cases']['UC_EDIT']=case
        p['relations'].append({'kind':'scenario_of','from':'S_DRAFT','to':'UC_EDIT'})
        native=deepcopy(n['inventory']['use_cases'][0]);native['qualified_name']='CSEFoundation::EditChange';n['inventory']['use_cases'].append(native)
        self.assertEqual(check_profile(p,n)['status'],'pass')

    def test_explicit_wrong_subject_is_fail_not_unknown(self):
        def change(p):
            p['elements']['SYS_WRONG']={'kind':'subject','term':'T_SUBJECT','native_name':'CSEFoundation::checker'}
            p['use_cases']['UC_REVIEW']['subject']='SYS_WRONG'
        r=result(change);self.assertEqual(r['status'],'fail');self.assertIn('native_subject',rules(r))

    def test_duplicate_native_resource_cannot_fake_redundancy(self):
        def change(p):
            p['elements']['R_ALIAS']=deepcopy(p['elements']['R_CHECKER'])
            a=p['allocations']['ALT_REVIEW'];a['resources'].append('R_ALIAS')
            a['resource_bounds']['R_ALIAS']={'min':1,'max':1}
            a['function_bounds']['F_CHECK']['max']=3
            a['pairs'].append({'function':'F_CHECK','resource':'R_ALIAS','rationale':'Claimed additional checking resource.'})
        r=result(change);self.assertEqual(r['status'],'fail');self.assertIn('allocation_identity',rules(r))

    def test_native_actor_omission_and_subject_change(self):
        self.assertIn('native_actors',rules(result(lambda p:p['use_cases']['UC_REVIEW']['actors'].pop('A_ASSISTANT'))))
        n=deepcopy(NATIVE);n['inventory']['use_cases'][0]['subjects'][0]['target']='CSEFoundation::checker'
        self.assertIn('native_subject',rules(result(native=n)))

    def test_declared_use_case_contract_cannot_be_deleted(self):
        self.assertIn('use_case_coverage',rules(result(lambda p:p['use_cases'].clear())))

    def test_multiplicity_boundary_and_bool_refusal(self):
        self.assertEqual(result(lambda p:p['use_cases']['UC_REVIEW']['actors']['A_ASSISTANT'].update(instances=2))['status'],'pass')
        self.assertIn('multiplicity',rules(result(lambda p:p['use_cases']['UC_REVIEW']['actors']['A_ASSISTANT'].update(instances=3))))
        self.assertEqual(result(lambda p:p['use_cases']['UC_REVIEW']['actors']['A_ASSISTANT'].update(instances=True))['status'],'error')

    def test_included_semantics_not_inferred(self):
        self.assertEqual(result(lambda p:p['use_cases']['UC_REVIEW'].update(category='included'))['status'],'unsupported')

    def test_scenario_trace_required(self):
        self.assertIn('scenario_trace',rules(result(lambda p:p['relations'].pop(0))))

    def test_many_to_many_and_intentional_unused_resource(self):
        r=result();self.assertEqual(r['status'],'pass')
        # Two resources for F_CHECK, two functions for R_ASSISTANT; simulator intentionally unused.
        self.assertEqual(len(PROFILE['allocations']['ALT_REVIEW']['pairs']),3)

    def test_unallocated_function_and_illegal_bounds(self):
        self.assertIn('allocation_cardinality',rules(result(lambda p:p['allocations']['ALT_REVIEW']['pairs'].pop(0))))
        self.assertEqual(result(lambda p:p['allocations']['ALT_REVIEW']['function_bounds']['F_SOURCE'].update(min=2,max=1))['status'],'error')

    def test_duplicate_pair_and_omitted_scope(self):
        self.assertIn('allocation_pair',rules(result(lambda p:p['allocations']['ALT_REVIEW']['pairs'].append(deepcopy(p['allocations']['ALT_REVIEW']['pairs'][0])))))
        self.assertIn('allocation_scope',rules(result(lambda p:p['allocations']['ALT_REVIEW']['function_bounds'].pop('F_SOURCE'))))

    def test_unknown_executor_and_embedded_command_refused(self):
        self.assertEqual(result(lambda p:p['capabilities']['VALIDATE'].update(executor='sh -c anything'))['status'],'unsupported')
        self.assertEqual(result(lambda p:p['capabilities']['VALIDATE'].update(command='anything'))['status'],'error')

    def test_claimed_available_simulator_requires_executor(self):
        self.assertEqual(result(lambda p:p['capabilities']['SIMULATE'].update(state='available'))['status'],'unsupported')

    def test_stale_revision_and_native_error(self):
        self.assertIn('source_revision',rules(result(lambda p:p.update(source_sha256='0'*64))))
        n=deepcopy(NATIVE);n['status']='error';self.assertEqual(result(native=n)['status'],'error')

    def test_malformed_nested_records_and_bounds(self):
        for change in (lambda p:p['terms'].update(BAD=[]), lambda p:p.update(elements=[]),
                       lambda p:p['relations'].append(None),lambda p:p['terms']['T_ACTOR'].update(kind=[]),
                       lambda p:p['use_cases']['UC_REVIEW']['actors']['A_ENGINEER'].update(bounds={'min':False,'max':1})):
            self.assertEqual(result(change)['status'],'error')

    def test_duplicate_json_nonfinite_size_symlink_fifo(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            p=Path(d)/'profile.json'
            for text in ('{"version":1,"version":2}', '{"bad":NaN}', '{'*2000):
                p.write_text(text)
                with self.assertRaises(ValueError):load_profile(p)
            p.write_bytes(b' '*(MAX_BYTES+1))
            with self.assertRaises(ValueError):load_profile(p)
            link=Path(d)/'link';link.symlink_to(p)
            with self.assertRaises(OSError):load_profile(link)
            fifo=Path(d)/'fifo';os.mkfifo(fifo)
            with self.assertRaises(ValueError):load_profile(fifo)

    def test_profile_change_during_parse_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            p=Path(d)/'profile.json';p.write_text(json.dumps(PROFILE))
            def parse(_model,**kwargs):p.write_text(json.dumps(PROFILE)+' ');return deepcopy(NATIVE)
            with patch('verifier.foundation.check_sysml',side_effect=parse):
                _,r=inspect(p,MODEL)
            self.assertEqual(r['status'],'error');self.assertIn('source_changed',rules(r))

    def test_empty_scope_is_unknown(self):
        p=deepcopy(PROFILE)
        for key in ('terms','elements','use_cases','allocations','capabilities'):p[key]={}
        p['relations']=[]
        self.assertEqual(check_profile(p,NATIVE)['status'],'unknown')

    def test_admitted_next_operates_on_incomplete_draft_without_inventing(self):
        r=result(lambda p:p['use_cases']['UC_REVIEW'].update(goal=None))
        with patch('verifier.foundation.inspect',return_value=(deepcopy(PROFILE),r)):
            q=execute('ignored','ignored','ELICIT')
        self.assertEqual(q['status'],'unknown');self.assertEqual(q['next']['rule'],'goal_missing')
        self.assertEqual(q['acceptance'],'not_evaluated')

    def test_unavailable_dispatch_cannot_execute(self):
        with patch('verifier.foundation.inspect',return_value=(deepcopy(PROFILE),result())):
            r=execute('ignored','ignored','SIMULATE')
        self.assertEqual(r['status'],'unsupported');self.assertIn('capability_unavailable',rules(r))

if __name__ == "__main__":
    unittest.main()
