"""Preparation preserves selected meanings and produces reviewable mechanical edits."""
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
from verifier.foundation import digest
from verifier.terminology import check_english
from verifier.terminology_prepare import propose, prepare_profile
from verifier.sysml import JAR, CLASSES

EXAMPLE = ROOT/'examples/terminology'
PROFILE = json.loads((EXAMPLE/'shared-pump.english.json').read_text())
PARSER = JAR.is_file() and (CLASSES/'SysmlBridge.class').is_file()


def profile():
    result = deepcopy(PROFILE)
    result['english']['terms'].pop('T_ISOLATE')
    result['english']['views'].pop('V_ISOLATE')
    return result


def native(text='The pump moves water.', pin=None):
    return {'status': 'pass', 'model_sha256': pin or PROFILE['source_sha256'],
            'inventory': {'parts': [{'qualified_name': 'EnglishPump::pump'}],
                'actions': [{'qualified_name': 'EnglishPump::Isolate'}],
                'documents': [{'owner': 'EnglishPump::pump', 'name': 'description', 'body': text}]}}


def initial_selection():
    return {'version': 'english-selection-1.0', 'revision': 'draft-1',
        'rules': ['ASD-STE100-1.11', 'CSE-TERM-POS', 'CSE-PHRASES'],
        'terms': ['T_PUMP'], 'phrases': deepcopy(PROFILE['english']['phrases']),
        'views': {'V_PUMP': {'element': 'R_PUMP', 'document': 'description',
            'uses': [{'term': 'T_PUMP', 'slot': 'noun'}], 'preserved': []}}}


class PreparationControls(unittest.TestCase):
    def refresh(self, text, *, old_profile=None, previous=None, **extra):
        return propose(old_profile or profile(), native(text, 'b'*64),
                       before_native=previous or native(), revision='draft-2', **extra)

    def test_refresh_relocates_exact_use_and_updates_hashes_in_separate_candidate(self):
        original = profile(); frozen = deepcopy(original)
        text = 'First, the pump moves water.'
        report, candidate = self.refresh(text, old_profile=original)
        self.assertEqual(report['operation'], 'candidate_generated')
        self.assertEqual((report['status'], report['language_status']), ('pass', 'pass'))
        self.assertEqual(candidate['english']['views']['V_PUMP']['uses'][0]['start'], text.index('pump'))
        self.assertEqual(candidate['english']['views']['V_PUMP']['text_sha256'], sha256(text.encode()).hexdigest())
        self.assertEqual(candidate['source_sha256'], 'b'*64)
        self.assertEqual(candidate['terms'], original['terms'])
        self.assertEqual(candidate['english']['terms'], original['english']['terms'])
        self.assertEqual(original, frozen)
        self.assertTrue(report['text_changes'])

    def test_old_required_review_fingerprint_is_not_advanced_by_preparation(self):
        old = profile(); retained = digest(old['english'])
        report, candidate = self.refresh('First, the pump moves water.', old_profile=old)
        self.assertEqual(report['before_scope_sha256'], retained)
        self.assertEqual(report['retained_scope'], 'not_advanced')
        self.assertNotEqual(report['candidate_scope_sha256'], retained)
        checked = check_english(candidate, native('First, the pump moves water.', 'b'*64),
                                review=True, retained_scope_sha256=retained)
        self.assertNotEqual(checked['status'], 'pass')

    def test_changed_source_requires_the_actual_retained_before_revision(self):
        for before in (None, native(pin='c'*64)):
            report, candidate = propose(profile(), native(pin='b'*64), before_native=before, revision='draft-2')
            self.assertEqual(report['status'], 'error')
            self.assertIsNone(candidate)

    def test_unchanged_source_can_prepare_without_an_extra_before_model(self):
        report, candidate = propose(profile(), native(), revision='draft-2')
        self.assertEqual(report['status'], 'pass')
        self.assertIsNotNone(candidate)

    def test_unchanged_selected_text_retains_valid_explicit_subset_after_unrelated_source_edit(self):
        old = profile(); text = 'The pump moves water. Another pump waits.'
        old['english']['views']['V_PUMP']['text_sha256'] = sha256(text.encode()).hexdigest()
        report, candidate = self.refresh(text, old_profile=old, previous=native(text))
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(candidate['english']['views'], old['english']['views'])
        self.assertEqual(candidate['source_sha256'], 'b'*64)

    def test_stale_term_definition_or_preexisting_wrong_use_cannot_be_rebound_away(self):
        changed = profile(); changed['terms']['T_PUMP']['definition'] = 'A different meaning.'
        report, candidate = self.refresh('The pump moves water.', old_profile=changed)
        self.assertEqual(report['status'], 'fail'); self.assertIsNone(candidate)
        old = profile()
        bad_text = 'The device moves water. The pump is elsewhere.'
        view = old['english']['views']['V_PUMP']
        view.update(text_sha256=sha256(bad_text.encode()).hexdigest())
        view['uses'][0].update(start=4, end=10)
        report, candidate = self.refresh('The pump moves water.', old_profile=old, previous=native(bad_text))
        self.assertEqual(report['status'], 'fail'); self.assertIsNone(candidate)

    def test_missing_and_ambiguous_exact_forms_remain_unresolved(self):
        for text in ('The device moves water.', 'The pump moves water. Another pump waits.'):
            report, candidate = self.refresh(text)
            self.assertEqual(report['status'], 'unknown', report)
            self.assertIsNone(candidate)
            self.assertEqual(report['findings'][0]['rule'], 'preparation_use_match')

    def test_word_prefix_is_not_a_selected_term_occurrence(self):
        report, candidate = self.refresh('The pumpstation moves water.')
        self.assertEqual(report['status'], 'unknown'); self.assertIsNone(candidate)

    def test_explicit_repeated_uses_preserve_cardinality_without_guessing_elements(self):
        old = profile(); text = 'The pump moves water. Other pumps wait.'
        view = old['english']['views']['V_PUMP']
        view['text_sha256'] = sha256(text.encode()).hexdigest()
        view['uses'].append({'term': 'T_PUMP', 'slot': 'noun', 'start': text.index('pumps'), 'end': text.index('pumps')+5})
        report, candidate = self.refresh('First, '+text, old_profile=old, previous=native(text))
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(len(candidate['english']['views']['V_PUMP']['uses']), 2)
        old['elements']['R_OTHER'] = {'kind': 'resource', 'term': 'T_PUMP', 'native_name': 'EnglishPump::backup'}
        view['uses'][1]['element'] = 'R_OTHER'
        before = native(text); before['inventory']['parts'].append({'qualified_name': 'EnglishPump::backup'})
        current = native('First, '+text, 'b'*64); current['inventory']['parts'].append({'qualified_name': 'EnglishPump::backup'})
        report, candidate = propose(old, current, before_native=before, revision='draft-2')
        self.assertEqual(report['status'], 'unknown'); self.assertIsNone(candidate)

    def test_a_language_pass_does_not_claim_that_changed_prose_meaning_is_equivalent(self):
        report, candidate = self.refresh('The pump does not move water.')
        self.assertEqual(report['language_status'], 'pass')
        self.assertEqual(report['meaning_equivalence'], 'not_evaluated')
        self.assertEqual(report['acceptance'], 'not_evaluated')
        self.assertIn('+The pump does not move water.', report['text_changes'][0]['diff'])

    def test_preserved_literal_is_retained_and_excluded_from_authored_use_matching(self):
        old = profile(); text = '"pump" is a literal. The pump moves water.'
        view = old['english']['views']['V_PUMP']
        start = text.rindex('pump')
        view.update(text_sha256=sha256(text.encode()).hexdigest(),
            preserved=[{'start': 0, 'end': 6, 'text': '"pump"', 'kind': 'interface_literal', 'basis': 'Synthetic literal'}])
        view['uses'][0].update(start=start, end=start+4)
        new = 'First, '+text
        report, candidate = self.refresh(new, old_profile=old, previous=native(text))
        self.assertEqual(report['status'], 'pass', report)
        result = candidate['english']['views']['V_PUMP']
        self.assertEqual(result['preserved'][0]['text'], '"pump"')
        self.assertEqual(result['preserved'][0]['start'], 7)
        self.assertEqual(result['uses'][0]['start'], new.rindex('pump'))

    def test_missing_or_ambiguous_preserved_source_cannot_be_rewritten_or_dropped(self):
        old = profile(); text = 'Original note. The pump moves water.'
        view = old['english']['views']['V_PUMP']
        view.update(text_sha256=sha256(text.encode()).hexdigest(),
            preserved=[{'start': 0, 'end': 14, 'text': 'Original note.', 'kind': 'original_note', 'basis': 'Synthetic note'}])
        start = text.index('pump'); view['uses'][0].update(start=start, end=start+4)
        for new in ('Edited note. The pump moves water.', 'Original note. Original note. The pump moves water.'):
            report, candidate = self.refresh(new, old_profile=old, previous=native(text))
            self.assertEqual(report['status'], 'unknown'); self.assertIsNone(candidate)

    def test_required_phrase_failure_survives_successful_mechanical_preparation(self):
        report, candidate = self.refresh('The pump moves water as appropriate.')
        self.assertEqual(report['operation'], 'candidate_generated')
        self.assertEqual((report['status'], report['language_status']), ('fail', 'fail'))
        self.assertIsNotNone(candidate)
        self.assertIn('CSE-PHRASE/P_VAGUE', {item['rule'] for item in report['language_findings']})

    def test_quoted_phrase_is_preserved_without_becoming_a_selected_authored_use(self):
        old = profile(); text = '"as appropriate" is quoted. The pump moves water.'
        view = old['english']['views']['V_PUMP']
        view.update(text_sha256=sha256(text.encode()).hexdigest(), preserved=[{
            'start': 0, 'end': 16, 'text': '"as appropriate"', 'kind': 'quotation', 'basis': 'Synthetic exact quotation'}])
        start = text.index('pump'); view['uses'][0].update(start=start, end=start+4)
        report, candidate = self.refresh('First, '+text, old_profile=old, previous=native(text))
        self.assertEqual(report['status'], 'pass', report)
        self.assertTrue(any(item['rule'] == 'CSE-PHRASE/P_VAGUE' and item['status'] == 'preserved'
                            for item in report['language_findings']))

    def test_initial_offset_free_selection_prepares_only_explicit_existing_concepts(self):
        catalog = profile(); catalog.pop('english')
        selection = initial_selection(); frozen = deepcopy(selection)
        report, candidate = propose(catalog, native(), selection=selection)
        self.assertEqual(report['status'], 'pass', report)
        self.assertEqual(candidate['english']['views']['V_PUMP']['uses'][0],
                         {'term': 'T_PUMP', 'slot': 'noun', 'start': 4, 'end': 8})
        self.assertEqual(selection, frozen)
        selection['views']['V_PUMP']['uses'][0]['slot'] = 'verb'
        report, candidate = propose(catalog, native(), selection=selection)
        self.assertEqual(report['language_status'], 'fail')
        self.assertEqual(candidate['english']['views']['V_PUMP']['uses'][0]['slot'], 'verb')

    def test_existing_selection_and_required_rules_cannot_be_replaced_during_refresh(self):
        report, candidate = propose(profile(), native(), selection=initial_selection(), revision='draft-2')
        self.assertEqual(report['status'], 'error'); self.assertIsNone(candidate)
        report, candidate = propose(profile(), native())
        self.assertEqual(report['status'], 'error'); self.assertIsNone(candidate)

    def test_invalid_native_binding_bad_input_and_work_limit_cannot_generate_success(self):
        selected = profile(); selected['elements']['R_PUMP']['native_name'] = 'Missing::pump'
        report, candidate = self.refresh('The pump moves water.', old_profile=selected)
        self.assertNotEqual(report['status'], 'pass'); self.assertIsNone(candidate)
        for value in (None, [], {}):
            report, candidate = propose(value, native(), revision='draft-2')
            self.assertEqual(report['status'], 'error'); self.assertIsNone(candidate)
        with patch('verifier.terminology_prepare.MATCH_CAP', 1):
            report, candidate = self.refresh('First, the pump moves water.')
        self.assertEqual(report['status'], 'unknown'); self.assertIsNone(candidate)

    def test_malformed_parser_report_is_an_error_without_an_output_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as temporary:
            work = Path(temporary); model = work/'model.sysml'; old = work/'profile.json'; output = work/'candidate.json'
            model.write_bytes((EXAMPLE/'shared-pump.sysml').read_bytes())
            old.write_bytes((EXAMPLE/'shared-pump.english.json').read_bytes())
            with patch('verifier.terminology_prepare.check_sysml', return_value=[]):
                report = prepare_profile(model, old, output, revision='draft-2')
            self.assertEqual(report['status'], 'error'); self.assertFalse(output.exists())


@unittest.skipUnless(PARSER, 'Install the pinned SysML parser')
class NativePreparationControls(unittest.TestCase):
    def test_actual_cli_prepares_relocated_bindings_without_overwriting_inputs_or_retained_scope(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as temporary:
            work = Path(temporary); before = work/'before.sysml'; model = work/'edited.sysml'
            before.write_bytes((EXAMPLE/'shared-pump.sysml').read_bytes())
            model.write_text(before.read_text().replace('The pump moves water.', 'First, the pump moves water.'))
            old = work/'before.english.json'; old.write_bytes((EXAMPLE/'shared-pump.english.json').read_bytes())
            output = work/'candidate.english.json'
            source_snapshot, profile_snapshot = model.read_bytes(), old.read_bytes()
            cmd = [sys.executable, str(ROOT/'skills/check-engineering-language/scripts/cse.py'), 'prepare',
                str(model), '--profile', str(old), '--before-model', str(before), '--revision', 'draft-2', '--output', str(output)]
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report['operation'], 'candidate_generated')
            self.assertEqual(report['retained_scope'], 'not_advanced')
            self.assertEqual(model.read_bytes(), source_snapshot)
            self.assertEqual(old.read_bytes(), profile_snapshot)
            check = subprocess.run([sys.executable, str(ROOT/'scripts/terminology.py'), 'check', str(model),
                                    '--profile', str(output), '--json'], capture_output=True, text=True, timeout=60)
            self.assertEqual(check.returncode, 0, check.stdout+check.stderr)
            repeated = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(json.loads(repeated.stdout)['operation'], 'not_generated')

    def test_model_changed_during_native_preparation_writes_no_candidate(self):
        from verifier.terminology_prepare import check_sysml as actual_check
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as temporary:
            work = Path(temporary); model = work/'model.sysml'; old = work/'profile.json'; output = work/'candidate.json'
            model.write_bytes((EXAMPLE/'shared-pump.sysml').read_bytes())
            old.write_bytes((EXAMPLE/'shared-pump.english.json').read_bytes())
            def mutate(path, **kwargs):
                native_result = actual_check(path, **kwargs)
                model.write_text(model.read_text()+'\n')
                return native_result
            with patch('verifier.terminology_prepare.check_sysml', side_effect=mutate):
                report = prepare_profile(model, old, output, revision='draft-2')
            self.assertEqual(report['status'], 'error'); self.assertFalse(output.exists())


if __name__ == '__main__':
    (ROOT/'.tmp').mkdir(exist_ok=True)
    unittest.main()
