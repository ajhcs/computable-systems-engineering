"""Adversarial context, output-claim and synthetic implementation controls.

Interpretive cases are authored expectations, never computed semantic verdicts.
The native class parses the actual fixture; mutations of that in-memory inventory
exercise checker/assembly handling only. Implementation observers independently
compare received identities rather than reusing the application decision helper.
"""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.context import assemble_context, assembled_context
from verifier.foundation import check_profile
from verifier.language import check_document, check_repair
from verifier.sysml import CLASSES, JAR, check_sysml

EXAMPLE = ROOT / 'examples/meaning-context'
CORPUS = json.loads((EXAMPLE / 'cases.json').read_text())
PROFILE = json.loads((EXAMPLE / CORPUS['profile']).read_text())
EXPECTED = json.loads((EXAMPLE / CORPUS['sampled_manifest']).read_text())
CLAUSE = CORPUS['original_clause']
PROPERTIES = {name: {'type': 'bool', 'owner': owner} for name, owner in
              [('unit.active', 'input'), ('unit.complete', 'input'),
               ('unit.sent', 'controlled'), ('unit.request', 'input'), ('unit.acknowledged', 'controlled')]}
PROPERTIES['unit.elapsed'] = {'type': 'int', 'owner': 'controlled', 'min': 0,
                          'max': 100, 'scale': '1', 'unit': 'second'}
ACTORS = {'unit': {}}
CLOCK = {'period': '1', 'unit': 'second'}

# Fixed developer-selected test module. Corpus text never supplies a module path.
spec = importlib.util.spec_from_file_location('handoff_reference', EXAMPLE / 'reference.py')
REFERENCE = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = REFERENCE
spec.loader.exec_module(REFERENCE)


def cases(mode):
    return [case for case in CORPUS['cases'] if case['mode'] == mode]


def trace_document(rows, complete=True):
    return {'language_version': 1, 'clock': deepcopy(CLOCK), 'actors': deepcopy(ACTORS),
            'properties': deepcopy(PROPERTIES), 'requirements': {'R_COMPLETE': CLAUSE},
            'observations': deepcopy(rows), 'complete': complete}


def source_evidence():
    return {'SYN_HANDOFF': {'status': 'pass', 'kind': 'proposal',
                           'detail': 'Synthetic source bytes captured by this test.',
                           'actual_sha256': sha256((EXAMPLE / 'brief.txt').read_bytes()).hexdigest()}}


def workflow_record(native):
    document = next(row for row in native['inventory']['documents']
                    if row.get('name') == 'cseWorkflow')
    header, payload = document['body'].strip().split('\n', 1)
    return header, json.loads(payload)


def replace_workflow(native, change):
    result = deepcopy(native)
    header, record = workflow_record(result)
    change(record)
    document = next(row for row in result['inventory']['documents']
                    if row.get('name') == 'cseWorkflow')
    document['body'] = header + '\n' + json.dumps(record)
    return result


class CorpusCatalogTests(unittest.TestCase):
    def test_named_cases_keep_review_expectations_separate_from_check_results(self):
        self.assertEqual(CORPUS['version'], 'meaning-context-evaluation-1.0')
        identifiers = [case['id'] for case in CORPUS['cases']]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        tags = {tag for case in CORPUS['cases'] for tag in case['tags']}
        required = {'completion', 'applicability', 'goal', 'obligation', 'evidence',
                    'scoped_identity', 'multiple_roles', 'relation_direction', 'units',
                    'definition_drift', 'native_drift', 'missing_mapping', 'truncation',
                    'unsupported', 'implementation', 'valid_control'}
        self.assertTrue(required <= tags, required - tags)
        self.assertEqual(len(cases('interpretive')), 11)
        for case in cases('interpretive'):
            with self.subTest(case=case['id']):
                self.assertEqual(case['computed_verdict'], 'not_run')
                self.assertEqual(case['oracle']['kind'], 'authored_review_expectation')
                self.assertIn(case['oracle']['candidate'], ('conflict', 'essential_omission'))
                for role in ('candidate', 'control'):
                    path = EXAMPLE / case[role]
                    self.assertEqual(path.parent, EXAMPLE / 'outputs')
                    self.assertTrue(path.is_file())
                    self.assertTrue(path.read_text().strip())
                self.assertNotEqual(case['candidate'], case['control'])

    def test_native_and_sampled_obligation_scopes_are_independent_of_view_limits(self):
        manifest = json.loads((EXAMPLE / CORPUS['native_manifest']).read_text())
        self.assertEqual(EXPECTED, {'version': 1, 'required': ['R_COMPLETE']})
        self.assertEqual(manifest['expected'], [{'id': 'R_COMPLETE',
                         'constraint': 'completionMeaning', 'source': 'SYN-HANDOFF-1'}])
        for case in cases('context'):
            self.assertNotIn('required', case)
            self.assertNotIn('manifest', case)

    def test_example_profile_is_pinned_to_actual_native_bytes(self):
        self.assertEqual(PROFILE['source_sha256'],
                         sha256((EXAMPLE / CORPUS['model']).read_bytes()).hexdigest())


class ExistingCheckCorpusTests(unittest.TestCase):
    def test_controlled_repairs_use_existing_meaning_comparison(self):
        for case in cases('controlled_repair'):
            with self.subTest(case=case['id']):
                report = check_repair(case['before'], case['after'], ACTORS,
                                      PROPERTIES, CLOCK, requirement_id=case.get('requirement_id', 'R_COMPLETE'))
                self.assertEqual(report['status'], case['expected_status'], report)
                self.assertEqual(report['acceptance'], 'not_evaluated')

    def test_sampled_cases_keep_waiting_and_incomplete_evidence_unresolved(self):
        for case in cases('sampled_trace'):
            with self.subTest(case=case['id']):
                report = check_document(trace_document(case['observations'], case['complete']),
                                        review=True, expected=EXPECTED)
                self.assertEqual(report['status'], case['expected_status'], report)
                self.assertEqual(report['scope']['required'], EXPECTED['required'])
                self.assertTrue(report['required_review'])

    def test_implementation_controls_have_independent_identity_observations(self):
        variants = {'reference': REFERENCE.Handoff,
                    'completes_on_send': REFERENCE.CompletesOnSend,
                    'accepts_any_ack': REFERENCE.AcceptsAnyAcknowledgement}
        for case in cases('implementation'):
            with self.subTest(case=case['id']):
                handoff = variants[case['variant']]('REF-1', 'CLINIC-A')
                if case['sent']:
                    handoff.send_referral()
                for ack in case['acknowledgements']:
                    handoff.receive_acknowledgement(REFERENCE.Acknowledgement(**ack))
                # This observer uses received identities, not the implementation's
                # acknowledged flag or its identity comparison helper.
                matched = any(ack.referral_id == 'REF-1' and ack.clinic_id == 'CLINIC-A'
                              for ack in handoff.received)
                row = {'unit.active': True, 'unit.sent': handoff.sent,
                       'unit.complete': handoff.complete, 'unit.acknowledged': matched}
                self.assertEqual(handoff.complete, case['expected_complete'])
                report = check_document(trace_document([row]), review=True, expected=EXPECTED)
                self.assertEqual(report['status'], case['expected_monitor_status'], report)
                if case['variant'] != 'reference':
                    self.assertEqual(report['results']['R_COMPLETE']['counterexample']['index'], 0)

    def test_completion_monitor_does_not_prove_the_implementation_complete(self):
        # A false completion result satisfies neither a liveness claim nor proof
        # of the reverse implication. Only the explicitly authored invariant is checked.
        row = {'unit.active': True, 'unit.complete': False,
               'unit.acknowledged': True, 'unit.sent': True}
        report = check_document(trace_document([row]), review=True, expected=EXPECTED)
        self.assertEqual(report['status'], 'unknown')
        self.assertEqual(report['results']['R_COMPLETE']['coverage']['triggers'], 0)


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(),
                     'Run scripts/install_sysml_parser.py to enable actual native context cases')
class NativeContextCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = check_sysml(EXAMPLE / 'handoff.sysml', syntax_only=True)
        if cls.native['status'] != 'pass':
            raise AssertionError(cls.native)
        checked = check_profile(PROFILE, cls.native)
        if checked['status'] != 'pass':
            raise AssertionError(checked)

    def assemble(self, native=None, profile=None, **kwargs):
        return assemble_context(deepcopy(self.native if native is None else native),
                                profile=deepcopy(PROFILE if profile is None else profile),
                                element_id=kwargs.pop('element_id', 'S_HANDOFF'),
                                source_evidence=kwargs.pop('source_evidence', source_evidence()),
                                **kwargs)

    def test_corpus_context_cases(self):
        for case in cases('context'):
            with self.subTest(case=case['id']):
                profile, native, kwargs = deepcopy(PROFILE), deepcopy(self.native), {}
                variant = case['variant']
                if variant == 'roles':
                    kwargs['element_id'] = 'R_CLINIC'
                elif variant == 'customs':
                    kwargs['element_id'] = 'S_CUSTOMS'
                elif variant == 'reversed_relation':
                    def reverse(record):
                        edge = record['relations']['REL_SEND_ALLOCATION']
                        edge['from'], edge['to'] = edge['to'], edge['from']
                    native = replace_workflow(native, reverse)
                elif variant == 'definition_drift':
                    profile['terms']['T_HANDOFF']['definition'] = 'Sending alone completes a handoff.'
                elif variant == 'native_drift':
                    native['model_sha256'] = '0' * 64
                elif variant == 'evidence_promotion':
                    native = replace_workflow(native,
                        lambda record: record['evidence']['E_PLAN'].update(result='supported'))
                elif variant == 'missing_definition':
                    del profile['elements']['S_HANDOFF']
                    del profile['english']['views']['V_HANDOFF']
                    del profile['english']['terms']['T_HANDOFF']
                elif variant == 'evidence_drift':
                    evidence = source_evidence()
                    evidence['SYN_HANDOFF'].update(status='fail', detail='Changed source bytes cannot bind the retained source revision.')
                    kwargs['source_evidence'] = evidence
                elif variant == 'cutoff':
                    kwargs['limit'] = 1
                report = self.assemble(native, profile, **kwargs)
                self.assertEqual(report['status'], case['expected_status'], report)
                self.assertEqual(report['semantic_review'], 'not_run')
                self.assertEqual(report['required_review'], 'not_evaluated')
                if variant == 'roles':
                    self.assertEqual({'R_CLINIC', 'A_CLINIC'} & set(report['elements']['foundation']),
                                     {'R_CLINIC', 'A_CLINIC'})
                elif variant == 'customs':
                    self.assertIn('T_CUSTOMS', report['concepts'])
                    self.assertNotIn('T_HANDOFF', report['concepts'])
                    self.assertIsNone(report['workflow_context']['workflow'])
                    self.assertEqual(report['workflow_context']['workflow_applicability']['status'], 'unknown')
                    self.assertFalse(report['coverage']['complete'])
                elif variant == 'cutoff':
                    self.assertFalse(report['coverage']['complete'])
                    self.assertTrue(report['coverage']['omitted_ids'])
                elif variant == 'missing_definition':
                    self.assertTrue(report['coverage']['unresolved'])

    def test_assembled_view_retains_defining_conditions_roles_relations_and_stages(self):
        report = self.assemble()
        self.assertEqual(report['status'], 'pass', report['findings'])
        self.assertTrue(report['coverage']['complete'])
        self.assertIn('T_HANDOFF', report['concepts'])
        self.assertNotIn('T_CUSTOMS', report['concepts'])
        self.assertEqual(report['concepts']['T_HANDOFF']['definition'],
                         PROFILE['terms']['T_HANDOFF']['definition'])
        conditions = report['workflow_context']['workflow']['conditions']
        self.assertIn('Active handoffs only.', conditions)
        self.assertIn('No deadline is specified.', conditions)
        allocation = report['relations']['workflow']['REL_SEND_ALLOCATION']
        self.assertEqual((allocation['from'], allocation['to']), ('F_SEND', 'R_DESK'))
        evidence = report['workflow_context']['evidence']
        self.assertEqual((evidence['E_PLAN']['mode'], evidence['E_PLAN']['result']), ('plan', 'not_run'))
        self.assertEqual(evidence['E_REPORTED']['mode'], 'assessment')
        self.assertEqual(report['checker_scope'], 'complete_supplied_model_unchanged')
        self.assertEqual(report['acceptance'], 'not_evaluated')

    def test_lexical_pass_does_not_claim_completion_meaning_review(self):
        # Deliberate synthetic mutation of an inventory and its selected text pin.
        # The real file wrapper never accepts an externally supplied inventory.
        native, profile = deepcopy(self.native), deepcopy(PROFILE)
        text = (EXAMPLE / 'outputs/completion-bad.txt').read_text().strip()
        document = next(row for row in native['inventory']['documents']
                        if row.get('owner') == 'HandoffStudy::Handoff'
                        and row.get('name') == 'description')
        document['body'] = text
        selected = profile['english']['views']['V_HANDOFF']
        selected['text_sha256'] = sha256(text.encode()).hexdigest()
        selected['uses'][0].update(start=text.index('handoff'),
                                   end=text.index('handoff') + len('handoff'))
        report = self.assemble(native, profile)
        self.assertEqual(report['profile_check']['english']['status'], 'pass')
        self.assertEqual(report['semantic_review'], 'not_run')
        self.assertEqual(report['concepts']['T_HANDOFF']['definition'],
                         PROFILE['terms']['T_HANDOFF']['definition'])

    def test_actual_native_file_profile_source_and_cli_smoke(self):
        report = assembled_context([EXAMPLE / 'handoff.sysml'],
                    profile_path=EXAMPLE / 'handoff.english.json', element_id='S_HANDOFF',
                    sources={'SYN_HANDOFF': EXAMPLE / 'brief.txt'})
        self.assertEqual(report['status'], 'pass', report['findings'])
        self.assertEqual(report['provenance']['input_stability'], 'pass')
        command = [sys.executable, '-B', str(ROOT / 'scripts/sysml_view.py'),
                   str(EXAMPLE / 'handoff.sysml'), '--profile', str(EXAMPLE / 'handoff.english.json'),
                   '--element', 'S_HANDOFF', '--source', 'SYN_HANDOFF=' + str(EXAMPLE / 'brief.txt')]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        delivered = json.loads(result.stdout)
        self.assertEqual(delivered['concepts'], report['concepts'])
        self.assertEqual(delivered['selection'], report['selection'])
        self.assertEqual(delivered['semantic_review'], 'not_run')

    def test_native_clause_matches_authored_corpus_and_preserves_independent_manifest(self):
        doc = next(row for row in self.native['inventory']['documents']
                   if row.get('owner') == 'HandoffStudy::CompletionRequiresAcknowledgement::completionMeaning'
                   and row.get('name') == 'cse')
        body = doc['body'].strip().split('\n', 1)[1]
        self.assertEqual(' '.join(body.split()), CLAUSE)
        manifest = json.loads((EXAMPLE / 'manifest.json').read_text())
        evidence = {'model_sha256': self.native['model_sha256'], 'complete': True,
                    'observations': [{'HandoffStudy::desk::active': True,
                                      'HandoffStudy::desk::complete': True,
                                      'HandoffStudy::desk::acknowledged': False}]}
        report = check_sysml(EXAMPLE / 'handoff.sysml', manifest=manifest,
                             evidence=evidence, review=True)
        self.assertEqual(report['status'], 'fail', report)
        self.assertEqual(report['coverage']['expected'], ['R_COMPLETE__completionMeaning'])


if __name__ == '__main__':
    unittest.main()
