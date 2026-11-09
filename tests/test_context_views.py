"""Adversarial controls for assembled existing-record context and its CLI."""
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
from verifier.context import assemble_context, assembled_context
from verifier.foundation import term_digest
from verifier.sysml import CLASSES, JAR, check_sysml
from verifier.views import view_sysml
from verifier.workflow import MARKER, empty_record


def fixture():
    """Authored synthetic bindings; this inventory is not native-parser evidence."""
    native = {'status': 'pass', 'model_sha256': 'a' * 64,
              'inventory': {group: [] for group in
                            ('parts', 'part_definitions', 'concerns', 'use_cases',
                             'actions', 'states', 'requirements', 'constraints',
                             'attributes', 'events', 'event_attributes', 'documents',
                             'ports', 'port_definitions', 'connections')}}
    inventory = native['inventory']
    inventory['actions'] = [{'qualified_name': 'Demo::' + name}
                            for name in ('handoff', 'send', 'ack', 'customs')]
    inventory['parts'] = [{'qualified_name': 'Demo::clinic', 'type': 'Demo::Clinic'}]
    inventory['part_definitions'] = [{'qualified_name': 'Demo::Clinic'}]
    inventory['attributes'] = [{'qualified_name': 'Demo::Clinic::elapsed', 'part_definition': 'Demo::Clinic'}]
    inventory['requirements'] = [{'qualified_name': 'Demo::Completion', 'id': 'R_COMPLETE'}]
    inventory['constraints'] = [{'qualified_name': 'Demo::Completion::rule', 'requirement': 'Demo::Completion'}]
    inventory['concerns'] = [{'qualified_name': 'Demo::workflowContext'}]
    profile = {'version': 'foundation-1.0', 'source_sha256': native['model_sha256'],
               'terms': {}, 'elements': {}, 'relations': [], 'use_cases': {},
               'allocations': {}, 'capabilities': {}}
    declared = [('S_HANDOFF', 'T_HANDOFF', 'scenario', 'handoff', 'handoff'),
                ('S_CUSTOMS', 'T_CUSTOMS', 'scenario', 'customs', 'handoff'),
                ('F_SEND', 'T_SEND', 'function', 'send', 'Send'),
                ('F_ACK', 'T_ACK', 'function', 'ack', 'Acknowledge'),
                ('R_CLINIC', 'T_CLINIC', 'resource', 'clinic', 'clinic'),
                ('A_CLINIC', 'T_ACTOR', 'actor', 'clinic', 'receiver')]
    for identity, term, kind, name, label in declared:
        profile['terms'][term] = {'namespace': 'Customs' if term == 'T_CUSTOMS' else 'Referral',
                                  'revision': '1', 'label': label, 'definition':
                                  'Receipt of acknowledgement defines completion.' if term == 'T_HANDOFF' else 'Authored ' + name,
                                  'kind': kind}
        profile['elements'][identity] = {'kind': kind, 'term': term, 'native_name': 'Demo::' + name}
    profile['relations'] = [{'kind': 'supports', 'from': 'R_CLINIC', 'to': 'F_ACK'}]
    profile['allocations'] = {'ACK_ALLOCATION': {
        'functions': ['F_ACK'], 'resources': ['R_CLINIC'],
        'pairs': [{'function': 'F_ACK', 'resource': 'R_CLINIC', 'rationale': 'Selected clinic.'}],
        'function_bounds': {'F_ACK': {'min': 1, 'max': 1}},
        'resource_bounds': {'R_CLINIC': {'min': 1, 'max': 1}}}}
    source = 'Wholly synthetic handoff basis.'
    record = empty_record('When is this handoff complete?', 'concept')
    record['question']['basis'] = 'SRC'
    record['sources'] = {'SRC': {'sha256': sha256(source.encode()).hexdigest(),
                                 'excerpt': source, 'kind': 'proposal'}}
    for identity, item in profile['elements'].items():
        kind = 'element' if item['kind'] == 'resource' else item['kind']
        record['elements'][identity] = {'kind': kind, 'native_name': item['native_name'],
                                        'label': identity, 'description': 'Authored meaning of ' + identity,
                                        'basis': 'SRC', 'status': 'proposed'}
    record['elements']['R_COMPLETE'] = {'kind': 'requirement', 'native_name': 'Demo::Completion',
                                        'label': 'Completion', 'description': 'Sending alone does not complete the handoff.',
                                        'basis': 'SRC', 'status': 'proposed'}
    for identity, kind, left, right in [('PARTICIPANT', 'participates_in', 'A_CLINIC', 'S_HANDOFF'),
                                        ('ALLOCATION', 'allocated_to', 'F_ACK', 'R_CLINIC'),
                                        ('REFERRAL', 'information_to', 'F_SEND', 'F_ACK'),
                                        ('COMPLETION', 'controls', 'R_COMPLETE', 'F_SEND')]:
        record['relations'][identity] = {'kind': kind, 'from': left, 'to': right,
                                         'basis': 'SRC', 'label': 'Authored ' + identity}
    record['workflows']['concept'] = {'focus': ['S_HANDOFF'], 'summary': 'Inspect completion.',
                                      'conditions': 'Same referral and selected clinic. No deadline is specified.',
                                      'outcome': 'Preserved completion meaning.', 'next_decision': 'Resolve transport mapping.'}
    record['questions']['Q'] = {'text': 'Which observation implements acknowledgement?',
                                 'affects': ['F_ACK'], 'blocking': False}
    record['evidence']['PLAN'] = {'target': 'S_HANDOFF', 'purpose': 'verification', 'mode': 'plan',
                                   'method': 'Future test', 'environment': 'Synthetic', 'basis': 'SRC',
                                   'result': 'not_run', 'limitations': 'Not observed.'}
    record['evidence']['REPORTED'] = {'target': 'F_ACK', 'purpose': 'analysis', 'mode': 'assessment',
                                       'method': 'Reported review', 'environment': 'Synthetic', 'basis': 'SRC',
                                       'result': 'supported', 'limitations': 'Not an executed check.'}
    inventory['documents'] = [{'owner': 'Demo::workflowContext', 'name': 'cseWorkflow',
                               'body': MARKER + '\n' + json.dumps(record)},
                              {'owner': 'Demo::Clinic::elapsed', 'name': 'cseType',
                               'body': 'CSE-TYPE/1.0\nrange 0 10 scale 1 unit second'},
                              {'owner': 'Demo::Completion::rule', 'name': 'cse',
                               'body': 'Existing completion clause.'}]
    evidence = {'SRC': {'status': 'pass', 'kind': 'proposal', 'detail': 'Synthetic source pin.'}}
    return native, profile, record, evidence, source


def with_record(native, record):
    result = deepcopy(native)
    result['inventory']['documents'][0]['body'] = MARKER + '\n' + json.dumps(record)
    return result


def trade_fixture():
    """Explicit native-bound alternatives/criteria; no inferred trade relations."""
    native, profile, record, evidence, _ = fixture()
    for identity, kind, name in [('ALT_A', 'concept', 'Alpha'),
                                  ('ALT_B', 'concept', 'Beta'),
                                  ('CRIT_C', 'criterion', 'Cost'),
                                  ('ALT_OTHER', 'concept', 'Other'),
                                  ('CRIT_OTHER', 'criterion', 'OtherCost')]:
        native_name = 'Demo::' + name
        native['inventory']['concerns'].append({'qualified_name': native_name})
        record['elements'][identity] = {'kind': kind, 'native_name': native_name,
                                        'label': name, 'description': 'Authored ' + name,
                                        'basis': 'SRC', 'status': 'proposed'}
        term = 'T_' + identity
        profile['terms'][term] = {'namespace': 'Trade', 'revision': '1', 'label': name,
                                   'definition': 'Authored ' + name, 'kind': 'objective'}
        profile['elements'][identity] = {'kind': 'objective', 'term': term,
                                        'native_name': native_name}
    record['workflows']['trade-study'] = {
        'focus': ['ALT_A'], 'summary': 'Compare the authored alternatives.',
        'conditions': 'Under the supplied synthetic assumptions.',
        'outcome': 'Retain the criterion and reported assessments.',
        'next_decision': 'Collect independently qualifying evidence.'}
    for identity, alternatives, criterion in [('CHOICE', ['ALT_A', 'ALT_B'], 'CRIT_C'),
                                               ('OTHER_CHOICE', ['ALT_OTHER'], 'CRIT_OTHER')]:
        record['trade_studies'][identity] = {
            'question': 'Which authored candidate?', 'alternatives': alternatives,
            'criteria': {criterion: {'kind': 'constraint', 'measure': 'Cost', 'unit': 'USD',
                                      'weight': None, 'basis': 'SRC'}},
            'assessments': {alternative: {criterion: {'finding': 'supported', 'value': '5',
                                                        'basis': 'SRC', 'uncertainty': 'Synthetic only.'}}
                            for alternative in alternatives},
            'method': 'qualitative', 'preference_basis': None, 'recommendation': 'No selection.'}
    return with_record(native, record), profile, evidence


class ContextControls(unittest.TestCase):
    def view(self, native=None, profile=None, **kwargs):
        n, p, record, evidence, _ = fixture()
        return assemble_context(n if native is None else native, profile=p if profile is None else profile,
                                element_id=kwargs.pop('element_id', 'S_HANDOFF'),
                                source_evidence=kwargs.pop('source_evidence', evidence), **kwargs)

    def test_join_reaches_completion_condition_and_preserves_roles(self):
        result = self.view()
        self.assertEqual(result['status'], 'pass')
        self.assertIn('T_HANDOFF', result['concepts'])
        self.assertNotIn('T_CUSTOMS', result['concepts'])
        self.assertEqual(result['concepts']['T_HANDOFF']['term_digest'], term_digest(fixture()[1]['terms']['T_HANDOFF']))
        self.assertEqual(result['elements']['foundation']['A_CLINIC']['native_name'],
                         result['elements']['foundation']['R_CLINIC']['native_name'])
        self.assertIn('COMPLETION', result['relations']['workflow'])
        self.assertIn('No deadline', result['workflow_context']['workflow']['conditions'])
        self.assertEqual(result['workflow_context']['evidence']['PLAN']['result'], 'not_run')
        self.assertEqual(result['workflow_context']['evidence']['REPORTED']['mode'], 'assessment')
        self.assertEqual(result['semantic_review'], 'not_run')
        self.assertEqual(result['required_review'], 'not_evaluated')
        self.assertEqual(result['acceptance'], 'not_evaluated')

    def test_exact_scoped_selection_does_not_merge_same_label(self):
        result = self.view(element_id='S_CUSTOMS')
        self.assertIn('T_CUSTOMS', result['concepts'])
        self.assertNotIn('T_HANDOFF', result['concepts'])
        self.assertEqual(result['concepts']['T_CUSTOMS']['namespace'], 'Customs')
        self.assertEqual(result['status'], 'unknown')
        self.assertIsNone(result['workflow_context']['workflow'])
        self.assertIsNone(result['workflow_context']['question'])
        self.assertEqual(result['workflow_context']['workflow_applicability']['status'], 'unknown')

    def test_truncated_connected_focus_retains_workflow_conditions(self):
        result = self.view(element_id='F_ACK', limit=1)
        self.assertEqual(result['status'], 'unknown')
        self.assertIn('No deadline', result['workflow_context']['workflow']['conditions'])
        self.assertEqual(result['workflow_context']['workflow_applicability']['status'], 'pass')

    def test_ambiguous_ids_need_source_qualification(self):
        n, p, record, evidence, _ = fixture()
        record['elements']['S_HANDOFF']['native_name'] = 'Demo::customs'
        record['elements'].pop('S_CUSTOMS')
        n = with_record(n, record)
        result = self.view(native=n, profile=p)
        self.assertEqual(result['status'], 'error')
        result = self.view(native=n, profile=p, element_id='foundation:S_HANDOFF')
        self.assertEqual(result['selection']['root'], 'actions:Demo::handoff')

    def test_native_selector_and_missing_definition(self):
        n, p, _, evidence, _ = fixture()
        result = assemble_context(n, profile=p, native_name='Demo::send', source_evidence=evidence)
        self.assertEqual(result['status'], 'pass')
        result = assemble_context(n, short_id='R_COMPLETE', source_evidence=evidence)
        self.assertEqual(result['status'], 'unknown')
        self.assertTrue(result['coverage']['unresolved'])

    def test_unknown_and_multiple_selectors_refuse(self):
        n, p, _, evidence, _ = fixture()
        for kwargs in ({'element_id': 'Absent'}, {'short_id': 'R_COMPLETE', 'element_id': 'S_HANDOFF'},
                       {'native_name': ''}, {}):
            self.assertEqual(assemble_context(n, profile=p, source_evidence=evidence, **kwargs)['status'], 'error')

    def test_relation_direction_is_retained_and_wrong_direction_fails(self):
        n, p, record, evidence, _ = fixture()
        result = self.view()
        edge = result['relations']['workflow']['COMPLETION']
        self.assertEqual((edge['from'], edge['to']), ('R_COMPLETE', 'F_SEND'))
        self.assertTrue(edge['directed'])
        record['relations']['ALLOCATION'].update({'from': 'R_CLINIC', 'to': 'F_ACK'})
        result = self.view(native=with_record(n, record))
        self.assertEqual(result['status'], 'fail')

    def test_documentary_interfaces_and_native_connections_are_adjacency(self):
        n, p, record, _, _ = fixture()
        record['relations']['ADJACENT'] = {'kind': 'interfaces_with', 'from': 'R_CLINIC',
                                           'to': 'R_CLINIC', 'label': '', 'basis': 'SRC'}
        result = self.view(native=with_record(n, record))
        self.assertEqual(result['status'], 'pass')
        self.assertIs(result['relations']['workflow']['ADJACENT']['directed'], False)
        self.assertIs(result['native_context']['connection_semantics']['directed'], False)

    def test_unsupported_relation_never_becomes_pass(self):
        n, p, record, _, _ = fixture()
        record['relations']['COMPLETION']['kind'] = 'magically_completes'
        self.assertEqual(self.view(native=with_record(n, record))['status'], 'unsupported')
        p['relations'][0]['kind'] = 'is_a'
        self.assertEqual(self.view(profile=p)['status'], 'unsupported')

    def test_limit_discloses_omissions_and_bounds_both_returned_views(self):
        full, small = self.view(limit=512), self.view(limit=1)
        self.assertEqual(full['status'], 'pass')
        self.assertEqual(small['status'], 'unknown')
        self.assertFalse(small['coverage']['complete'])
        self.assertEqual(small['coverage']['returned_elements'], 1)
        self.assertGreater(small['coverage']['total_elements'], 1)
        self.assertIn('workflow:R_COMPLETE', small['coverage']['omitted_ids'])
        self.assertEqual(set(small['workflow_context']['elements']), {'S_HANDOFF'})
        self.assertEqual(small['workflow_context']['relations'], {})
        self.assertIn('No deadline', small['workflow_context']['workflow']['conditions'])
        self.assertNotIn('native_inventory', small['workflow_check'])
        self.assertNotIn('record', small['workflow_check'])
        self.assertNotIn('cseWorkflow', {item['name'] for item in full['native_context']['documents']})

    def test_units_native_constraints_and_allocations_remain_explicit(self):
        result = self.view()
        self.assertIn('ACK_ALLOCATION', result['allocations'])
        self.assertTrue(any(item['name'] == 'cseType' and 'unit second' in item['body']
                            for item in result['native_context']['documents']))
        self.assertEqual(result['native_context']['constraints'][0]['requirement'], 'Demo::Completion')

    def test_unpaired_function_is_allocation_context_without_an_assignment(self):
        native, profile, record, evidence, _ = fixture()
        allocation = profile['allocations']['ACK_ALLOCATION']
        allocation['functions'].append('F_SEND')
        allocation['function_bounds']['F_SEND'] = {'min': 0, 'max': 1}
        original_pairs = deepcopy(allocation['pairs'])
        record['relations'] = {}
        record['workflows']['concept']['focus'] = ['F_ACK']
        native = with_record(native, record)
        for selected in ('F_ACK', 'F_SEND'):
            with self.subTest(selected=selected):
                result = assemble_context(native, profile=profile, element_id=selected,
                                          source_evidence=evidence, limit=512)
                self.assertEqual(result['status'], 'pass', result['findings'])
                self.assertTrue(result['coverage']['complete'])
                self.assertTrue({'F_ACK', 'F_SEND', 'R_CLINIC'} <= set(result['elements']['foundation']))
                self.assertEqual(result['allocations']['ACK_ALLOCATION']['pairs'], original_pairs)
        small = assemble_context(native, profile=profile, element_id='F_ACK',
                                 source_evidence=evidence, limit=1)
        self.assertEqual(small['status'], 'unknown')
        self.assertIn('foundation:F_SEND', small['coverage']['omitted_ids'])
        self.assertEqual(small['allocations']['ACK_ALLOCATION']['pairs'], original_pairs)

    def test_trade_dependencies_retain_definitions_without_inventing_relations(self):
        native, profile, evidence = trade_fixture()
        for selected in ('ALT_A', 'ALT_B', 'CRIT_C'):
            with self.subTest(selected=selected):
                result = assemble_context(native, profile=profile, element_id=selected,
                                          source_evidence=evidence, workflow='trade-study', limit=512)
                self.assertEqual(result['status'], 'pass', result['findings'])
                self.assertTrue(result['coverage']['complete'])
                self.assertEqual(set(result['elements']['workflow']), {'ALT_A', 'ALT_B', 'CRIT_C'})
                self.assertEqual(set(result['concepts']), {'T_ALT_A', 'T_ALT_B', 'T_CRIT_C'})
                self.assertEqual(set(result['workflow_context']['trade_studies']), {'CHOICE'})
                self.assertEqual(result['relations']['workflow'], {})
                self.assertEqual(result['relations']['foundation'], [])
                self.assertEqual(result['workflow_context']['trade_studies']['CHOICE']['selection'], 'not_made')

    def test_limited_trade_discloses_all_referenced_omissions(self):
        native, profile, evidence = trade_fixture()
        result = assemble_context(native, profile=profile, element_id='ALT_A',
                                  source_evidence=evidence, workflow='trade-study', limit=1)
        self.assertEqual(result['status'], 'unknown')
        self.assertFalse(result['coverage']['complete'])
        self.assertEqual(result['coverage']['returned_elements'], 1)
        self.assertEqual(result['coverage']['total_elements'], 3)
        self.assertEqual(set(result['elements']['workflow']), {'ALT_A'})
        self.assertTrue({'foundation:ALT_B', 'workflow:ALT_B',
                         'foundation:CRIT_C', 'workflow:CRIT_C'} <= set(result['coverage']['omitted_ids']))
        rows = result['workflow_context']['trade_studies']['CHOICE']['rows']
        self.assertEqual({row['alternative'] for row in rows}, {'ALT_A', 'ALT_B'})
        self.assertEqual({row['criterion'] for row in rows}, {'CRIT_C'})

    def test_trade_dependencies_apply_only_to_selected_trade_workflow(self):
        native, profile, evidence = trade_fixture()
        result = assemble_context(native, profile=profile, element_id='ALT_A',
                                  source_evidence=evidence, workflow='concept', limit=512)
        self.assertEqual(set(result['elements']['workflow']), {'ALT_A'})
        self.assertEqual(result['workflow_context']['trade_studies'], {})
        self.assertEqual(result['coverage']['total_elements'], 1)

    def test_source_and_blocking_questions_remain_unknown(self):
        result = self.view(source_evidence={})
        self.assertEqual(result['status'], 'unknown')
        self.assertIn('conditions', result['workflow_context']['workflow'])
        n, p, record, _, _ = fixture()
        record['questions']['Q']['blocking'] = True
        self.assertEqual(self.view(native=with_record(n, record))['status'], 'unknown')
        self.assertEqual(self.view(source_evidence={'SRC': {'status': 'fail', 'detail': 'stale'}})['status'], 'fail')

    def test_stale_profile_cannot_supply_authoritative_meaning(self):
        n, p, _, _, _ = fixture()
        p['source_sha256'] = 'b' * 64
        result = self.view(profile=p)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['concepts'], {})
        self.assertEqual(result['retrieval_status'], 'pass')

    def test_term_pin_and_multifile_english_refused(self):
        n, p, _, evidence, _ = fixture()
        text = 'The handoff waits.'
        n['inventory']['documents'].append({'owner': 'Demo::handoff', 'name': 'description', 'body': text})
        p['english'] = {'version': 'english-1.0', 'revision': '1',
                        'rules': ['ASD-STE100-1.11', 'CSE-TERM-POS'],
                        'terms': {'T_HANDOFF': term_digest(p['terms']['T_HANDOFF'])},
                        'views': {'V': {'element': 'S_HANDOFF', 'document': 'description',
                                        'text_sha256': sha256(text.encode()).hexdigest(),
                                        'uses': [{'term': 'T_HANDOFF', 'slot': 'noun', 'start': 4, 'end': 11}],
                                        'preserved': []}}, 'phrases': {}}
        self.assertEqual(self.view(native=n, profile=p)['status'], 'pass')
        p['terms']['T_HANDOFF']['definition'] = 'Sending alone completes it.'
        self.assertEqual(self.view(native=n, profile=p)['status'], 'fail')
        p['english']['terms']['T_HANDOFF'] = term_digest(p['terms']['T_HANDOFF'])
        n['model_files'] = [{'path': 'one.sysml'}, {'path': 'two.sysml'}]
        self.assertEqual(self.view(native=n, profile=p)['status'], 'unsupported')

    def test_native_failure_retains_diagnostics(self):
        n, _, _, _, _ = fixture()
        n.update(status='error', findings=[{'code': 'parse', 'detail': 'Native syntax failed'}],
                 parser_issues=[{'severity': 'ERROR', 'line': 2, 'message': 'Unexpected token'}])
        result = self.view(native=n)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['parser_issues'][0]['line'], 2)
        self.assertEqual(result['findings'][0]['detail'], 'Native syntax failed')

    def test_successful_native_warnings_are_visible(self):
        n, _, _, _, _ = fixture()
        n['parser_issues'] = [{'severity': 'WARNING', 'line': 2, 'message': 'Historical declaration warning'}]
        result = self.view(native=n)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['parser_issues'], n['parser_issues'])

    def test_output_cap_refuses_without_retaining_large_check_payloads(self):
        with patch('verifier.context.MAX_OUTPUT_BYTES', 4000):
            result = self.view()
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['findings'][0]['rule'], 'context_output')
        self.assertEqual(result['concepts'], {})
        self.assertNotIn('checks', result['workflow_check'])
        self.assertLess(len(json.dumps(result)), 4000)

    def test_final_wrapper_provenance_is_included_in_byte_cap(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            model = Path(directory) / 'm.sysml'
            model.write_text('Synthetic cap input')
            native = {'status': 'error', 'model_sha256': sha256(model.read_bytes()).hexdigest()}
            stub = {'status': 'pass', 'retrieval_status': 'pass', 'provenance': {}, 'padding': ''}
            stub['padding'] = 'x' * (3990 - len(json.dumps(stub)))
            with patch('verifier.context.check_sysml', return_value=native), \
                 patch('verifier.context.assemble_context', return_value=stub), \
                 patch('verifier.context.MAX_OUTPUT_BYTES', 4000):
                result = assembled_context(model, short_id='R')
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['findings'][0]['rule'], 'context_output')
            self.assertNotIn('padding', result)

    def test_invalid_limit_and_work_cap_never_pass(self):
        for limit in (0, 513, True, '2'):
            self.assertEqual(self.view(limit=limit)['status'], 'error')
        n, _, _, _, _ = fixture()
        n['inventory']['states'] = [{'qualified_name': 'State' + str(i)} for i in range(10001)]
        self.assertEqual(self.view(native=n)['status'], 'error')

    def test_immutable_and_deterministic(self):
        n, p, _, evidence, _ = fixture()
        before = deepcopy((n, p, evidence))
        first = self.view(native=n, profile=p, source_evidence=evidence)
        self.assertEqual(first, self.view(native=n, profile=p, source_evidence=evidence))
        self.assertEqual((n, p, evidence), before)

    def test_legacy_api_keeps_its_shape(self):
        n, _, _, _, _ = fixture()
        with patch('verifier.views.check_sysml', return_value=n):
            result = view_sysml('synthetic.sysml', 'R_COMPLETE')
        self.assertEqual(result['claim_scope'], 'parsed_context_view')
        self.assertNotIn('concepts', result)
        self.assertEqual(result['selected_id'], 'R_COMPLETE')

    def test_input_file_drift_clears_context(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        for mutate in ('model', 'profile', 'source'):
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
                n, p, _, evidence, source = fixture()
                model, profile, basis = (Path(directory) / name for name in ('m.sysml', 'p.json', 's.txt'))
                model.write_text('Captured synthetic native input')
                n['model_sha256'] = p['source_sha256'] = sha256(model.read_bytes()).hexdigest()
                profile.write_text(json.dumps(p))
                basis.write_text(source)

                def parse(paths, **kwargs):
                    {'model': model, 'profile': profile, 'source': basis}[mutate].write_text('Changed input')
                    return n

                with patch('verifier.context.check_sysml', side_effect=parse):
                    result = assembled_context(model, profile_path=profile, element_id='S_HANDOFF', sources={'SRC': basis})
                self.assertEqual(result['status'], 'error' if mutate != 'source' else 'fail')
                if mutate != 'source':
                    self.assertEqual(result['concepts'], {})
                    self.assertEqual(result['provenance']['input_stability'], 'error')

    def test_duplicate_profile_keys_and_undeclared_source_paths_refused(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            model, profile = Path(directory) / 'm.sysml', Path(directory) / 'p.json'
            model.write_text('Captured synthetic native input')
            profile.write_text('{"version":"foundation-1.0","version":"foundation-1.0"}')
            result = assembled_context(model, profile_path=profile, element_id='S_HANDOFF')
            self.assertEqual(result['status'], 'error')
            n, p, _, _, _ = fixture()
            n['model_sha256'] = p['source_sha256'] = sha256(model.read_bytes()).hexdigest()
            profile.write_text(json.dumps(p))
            with patch('verifier.context.check_sysml', return_value=n):
                result = assembled_context(model, profile_path=profile, element_id='S_HANDOFF', sources={'UNDECLARED': model})
            self.assertEqual(result['status'], 'error')


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(),
                     'Install the pinned SysML parser to exercise actual context assembly')
class NativeContextControls(unittest.TestCase):
    def test_actual_native_short_id_and_exact_binding(self):
        result = assembled_context(ROOT / 'examples/foundation/cse-self-model.sysml',
                                   profile_path=ROOT / 'examples/foundation/profile.json', element_id='F_CHECK')
        self.assertEqual(result['status'], 'pass', result['findings'])
        self.assertIn('T_FUNCTION', result['concepts'])
        self.assertEqual(result['provenance']['input_stability'], 'pass')
        self.assertEqual(result['workflow_check']['status'], 'not_run')

    def test_native_english_cross_element_use_retains_its_definition_or_omission(self):
        paths = {'profile_path': ROOT / 'examples/terminology/shared-pump.english.json',
                 'element_id': 'F_ISOLATE'}
        model = ROOT / 'examples/terminology/shared-pump.sysml'
        full = assembled_context(model, **paths, limit=512)
        self.assertEqual(full['status'], 'pass', full['findings'])
        self.assertTrue(full['coverage']['complete'])
        self.assertIn('R_PUMP', full['elements']['foundation'])
        self.assertIn('T_PUMP', full['concepts'])
        self.assertEqual(full['concepts']['T_PUMP']['definition'],
                         'A resource that moves water through the selected circuit.')
        self.assertEqual(full['relations']['foundation'], [])
        target = assembled_context(model, profile_path=paths['profile_path'],
                                   element_id='R_PUMP', limit=512)
        self.assertEqual(target['status'], 'pass', target['findings'])
        self.assertNotIn('F_ISOLATE', target['elements']['foundation'])
        self.assertNotIn('V_ISOLATE', target['english_context']['views'])
        small = assembled_context(model, **paths, limit=1)
        self.assertEqual(small['status'], 'unknown')
        self.assertFalse(small['coverage']['complete'])
        self.assertIn('foundation:R_PUMP', small['coverage']['omitted_ids'])
        self.assertNotIn('R_PUMP', small['elements']['foundation'])
        uses = small['english_context']['views']['V_ISOLATE']['uses']
        self.assertTrue(any(use.get('element') == 'R_PUMP' for use in uses))

    def test_native_zero_bound_allocation_member_retains_exclusion_or_omission(self):
        model = ROOT / 'examples/foundation/cse-self-model.sysml'
        paths = {'profile_path': ROOT / 'examples/foundation/profile.json', 'element_id': 'F_CHECK'}
        full = assembled_context(model, **paths, limit=512)
        self.assertEqual(full['status'], 'pass', full['findings'])
        self.assertTrue(full['coverage']['complete'])
        self.assertIn('R_SIMULATOR', full['elements']['foundation'])
        self.assertIn('T_RESOURCE', full['concepts'])
        self.assertIn('SIMULATE', full['capabilities'])
        self.assertEqual(full['capabilities']['SIMULATE']['state'], 'unavailable')
        self.assertFalse(full['capabilities']['SIMULATE']['executor_admission']['available'])
        allocation = full['allocations']['ALT_REVIEW']
        self.assertEqual(allocation['resource_bounds']['R_SIMULATOR'], {'min': 0, 'max': 0})
        self.assertFalse(any(pair['resource'] == 'R_SIMULATOR' for pair in allocation['pairs']))
        small = assembled_context(model, **paths, limit=1)
        self.assertEqual(small['status'], 'unknown')
        self.assertFalse(small['coverage']['complete'])
        self.assertIn('foundation:R_SIMULATOR', small['coverage']['omitted_ids'])
        self.assertNotIn('R_SIMULATOR', small['elements']['foundation'])
        self.assertEqual(small['allocations']['ALT_REVIEW'], allocation)

    def test_cli_old_new_and_structured_refusal(self):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        commands = [(['examples/sysml/quantity.sysml', '--id', 'R_DURATION'], 0, 'parsed_context_view'),
                    (['examples/foundation/cse-self-model.sysml', '--element', 'F_CHECK', '--profile',
                      'examples/foundation/profile.json'], 0, 'assembled_existing_record_context'),
                    (['examples/foundation/cse-self-model.sysml', '--element', 'F_CHECK', '--profile',
                      'examples/foundation/profile.json', '--limit', '0'], 1, 'assembled_existing_record_context')]
        for args, code, scope in commands:
            completed = subprocess.run([sys.executable, '-B', 'scripts/sysml_view.py', *args],
                                       cwd=ROOT, env=environment, text=True, capture_output=True)
            self.assertEqual(completed.returncode, code, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)['claim_scope'], scope)


if __name__ == '__main__':
    unittest.main()
