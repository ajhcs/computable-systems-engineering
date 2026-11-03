"""Selected controlled English during drafting, preserved sources and harmful repairs."""
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
from verifier.foundation import check_profile, digest, term_digest
from verifier.language import check_repair
from verifier.sysml import JAR
from verifier.terminology import check_english, inspect, apply_drafting_profiles, text_digest, render_text

EXAMPLE = ROOT/'examples/terminology'
PROFILE = json.loads((EXAMPLE/'shared-pump.english.json').read_text())
LANGUAGE = json.loads((ROOT/'examples/language/valid.json').read_text())
# Unit cases use a synthetic adapter snapshot. Separate CLI cases exercise the
# actual native model/parser and the independent/drafting skill launchers.
NATIVE = {'status': 'pass', 'model_sha256': PROFILE['source_sha256'], 'inventory': {
    'parts': [{'qualified_name': 'EnglishPump::pump'}],
    'actions': [{'qualified_name': 'EnglishPump::Isolate'}],
    'documents': [{'owner': 'EnglishPump::pump', 'name': 'description', 'body': 'The pump moves water.'},
                  {'owner': 'EnglishPump::Isolate', 'name': 'description', 'body': 'Isolate the pump.'}]}}


def checked(profile=None, native=None, **kwargs):
    return check_english(deepcopy(PROFILE if profile is None else profile),
                         deepcopy(NATIVE if native is None else native), **kwargs)


def rules(report):
    return {finding['rule'] for finding in report['findings']}


def edited_text(text, *, word='pump'):
    profile, native = deepcopy(PROFILE), deepcopy(NATIVE)
    native['inventory']['documents'][0]['body'] = text
    start = text.index(word)
    profile['english']['views']['V_PUMP'].update(text_sha256=text_digest(text),
        uses=[{'term': 'T_PUMP', 'slot': 'noun', 'start': start, 'end': start+len(word)}])
    return profile, native


class ControlledEnglishTests(unittest.TestCase):
    def test_selected_english_noun_and_verb_share_native_concept_identities(self):
        report = checked()
        self.assertEqual(report['status'], 'pass', report)
        self.assertFalse(report['required_review'])
        self.assertEqual(report['checked_views'], ['V_ISOLATE', 'V_PUMP'])
        self.assertEqual(report['selected_terms'], ['T_ISOLATE', 'T_PUMP'])
        self.assertEqual(check_profile(PROFILE, NATIVE)['english']['status'], 'pass')

    def test_same_label_in_different_namespaces_is_not_equated(self):
        profile = deepcopy(PROFILE)
        term = deepcopy(profile['terms']['T_PUMP'])
        term.update(namespace='Other.Domain', definition='A different explicitly scoped concept.')
        profile['terms']['T_OTHER'] = term
        report = checked(profile)
        self.assertEqual(report['status'], 'pass')
        self.assertNotIn('T_OTHER', report['selected_terms'])

    def test_ambiguous_same_scope_label_fails_even_with_different_definition(self):
        profile = deepcopy(PROFILE)
        term = deepcopy(profile['terms']['T_PUMP']); term['definition'] = 'A different item with the same label.'
        profile['terms']['T_OTHER'] = term
        report = checked(profile)
        finding = next(x for x in report['findings'] if x['rule'] == 'term_scope')
        self.assertEqual(report['status'], 'fail'); self.assertEqual(finding['phrase'], 'pump')
        self.assertEqual(set(finding['ids']), {'T_PUMP', 'T_OTHER'})

    def test_approved_form_collision_and_unicode_normalization_do_not_hide_ambiguity(self):
        profile = deepcopy(PROFILE)
        profile['terms']['T_PUMP']['approved_forms'].append('café')
        term = deepcopy(profile['terms']['T_PUMP']); term.update(label='cafe\u0301', approved_forms=['cafe\u0301'])
        profile['terms']['T_OTHER'] = term
        self.assertIn('term_scope', rules(checked(profile)))

    def test_wrong_concept_or_wrong_kind_binding_fails(self):
        for field, value in [('term', 'T_ISOLATE'), ('kind', 'actor')]:
            with self.subTest(field=field):
                profile = deepcopy(PROFILE); profile['elements']['R_PUMP'][field] = value
                self.assertIn('CSE-TERM-BINDING', rules(checked(profile)))

    def test_undefined_term_is_not_inferred_from_matching_text(self):
        profile = deepcopy(PROFILE)
        profile['english']['views']['V_PUMP']['uses'][0]['term'] = 'T_MISSING'
        report = checked(profile)
        self.assertIn('CSE-CONCEPT', rules(report)); self.assertNotEqual(report['status'], 'pass')

    def test_exact_synonym_diagnostic_includes_ids_phrase_rule_and_repair(self):
        profile, native = edited_text('The water mover moves water.', word='water mover')
        report = checked(profile, native)
        finding = next(x for x in report['findings'] if x['rule'] == 'ASD-STE100-1.11')
        self.assertEqual(finding['ids'], ['V_PUMP', 'R_PUMP', 'T_PUMP'])
        self.assertEqual(finding['phrase'], 'water mover'); self.assertIn("'pump'", finding['repair'])
        self.assertEqual(report['status'], 'fail')

    def test_declared_noun_and_verb_roles_are_enforced_during_drafting(self):
        profile = deepcopy(PROFILE)
        profile['english']['views']['V_PUMP']['uses'][0]['slot'] = 'verb'
        self.assertIn('CSE-TERM-POS', rules(checked(profile)))
        profile = deepcopy(PROFILE)
        profile['english']['views']['V_ISOLATE']['uses'][0]['slot'] = 'noun'
        self.assertIn('CSE-TERM-POS', rules(checked(profile)))

    def test_unapproved_technical_verb_form_fails(self):
        profile, native = deepcopy(PROFILE), deepcopy(NATIVE)
        text = 'Separate the pump.'
        native['inventory']['documents'][1]['body'] = text
        view = profile['english']['views']['V_ISOLATE']; view['text_sha256'] = text_digest(text)
        view['uses'][0].update(end=8); view['uses'][1].update(start=13, end=17)
        self.assertIn('CSE-TERM-FORM', rules(checked(profile, native)))

    def test_explicit_inflection_is_supported_but_word_prefix_is_not(self):
        profile, native = edited_text('The pumps move water.', word='pumps')
        self.assertEqual(checked(profile, native)['status'], 'pass')
        profile, native = edited_text('The pumpkin moves water.')
        self.assertIn('ASD-STE100-1.11', rules(checked(profile, native)))

    def test_definition_approved_form_and_grammatical_class_edits_invalidate_pin(self):
        for field, value in [('definition', 'A changed definition.'), ('approved_forms', ['pump']), ('part_of_speech', 'verb')]:
            with self.subTest(field=field):
                profile = deepcopy(PROFILE); profile['terms']['T_PUMP'][field] = value
                self.assertIn('CSE-TERM-REVISION', rules(checked(profile)))

    def test_namespace_and_revision_are_bound_even_when_labels_match(self):
        for field, value in [('namespace', 'Other.Domain'), ('revision', '2')]:
            with self.subTest(field=field):
                profile = deepcopy(PROFILE); profile['terms']['T_PUMP'][field] = value
                self.assertIn('CSE-TERM-REVISION', rules(checked(profile)))

    def test_legacy_noun_defaults_have_same_explicit_digest(self):
        term = deepcopy(PROFILE['terms']['T_PUMP']); del term['approved_forms']; del term['part_of_speech']
        explicit = term | {'approved_forms': ['pump'], 'part_of_speech': 'noun'}
        self.assertEqual(term_digest(term), term_digest(explicit))

    def test_required_review_cannot_drop_rules_or_uses_to_pass(self):
        original_pin = digest(PROFILE['english'])
        profile = deepcopy(PROFILE); del profile['english']['views']['V_ISOLATE']
        report = checked(profile, review=True, retained_scope_sha256=original_pin)
        self.assertIn('CSE-SCOPE', rules(report)); self.assertIn('CSE-USE-COVERAGE', rules(report))
        self.assertNotEqual(report['status'], 'pass')

    def test_required_review_without_retained_scope_is_unknown(self):
        self.assertEqual(checked(review=True)['status'], 'unknown')
        self.assertEqual(checked(review=True, retained_scope_sha256=digest(PROFILE['english']))['status'], 'pass')

    def test_missing_profile_or_empty_selection_cannot_be_called_conforming(self):
        profile = deepcopy(PROFILE); del profile['english']
        self.assertEqual(checked(profile)['status'], 'unknown')
        profile = deepcopy(PROFILE); profile['english']['terms'] = {}; profile['english']['views'] = {}
        self.assertNotEqual(checked(profile)['status'], 'pass')

    def test_unknown_standard_rule_and_incomplete_analysis_cannot_pass(self):
        profile = deepcopy(PROFILE); profile['english']['rules'].append('ASD-STE100-1.2')
        self.assertEqual(checked(profile)['status'], 'unsupported')
        self.assertEqual(checked(phrase_work_cap=1)['status'], 'unknown')

    def test_colliding_view_and_definition_ids_cannot_hide_a_required_phrase(self):
        profile, native = deepcopy(PROFILE), deepcopy(NATIVE)
        profile['terms']['T_PUMP']['definition'] = 'A resource that moves water as appropriate.'
        profile['english']['terms']['T_PUMP'] = term_digest(profile['terms']['T_PUMP'])
        profile['elements']['definition'] = profile['elements'].pop('R_PUMP')
        view = profile['english']['views'].pop('V_PUMP')
        view['element'] = 'definition'
        profile['english']['views']['T_PUMP'] = view
        profile['english']['views']['V_ISOLATE']['uses'][1]['element'] = 'definition'
        result = checked(profile, native, review=True, retained_scope_sha256=digest(profile['english']))
        self.assertEqual(result['status'], 'fail')
        phrase = next(f for f in result['findings'] if f['rule'] == 'CSE-PHRASE/P_VAGUE')
        self.assertEqual(phrase['ids'], ['T_PUMP', 'definition'])
        self.assertEqual(phrase['phrase'], 'as appropriate')
        # Only the view ID changes. Definition analysis and work remain identical.
        renamed = deepcopy(profile)
        renamed['english']['views']['V_RENAMED'] = renamed['english']['views'].pop('T_PUMP')
        control = checked(renamed, native, review=True, retained_scope_sha256=digest(renamed['english']))
        self.assertEqual(control['status'], result['status'])
        self.assertEqual(control['findings'], result['findings'])
        self.assertEqual(control['phrase_work_units'], result['phrase_work_units'])

    def test_preserved_view_text_does_not_waive_colliding_definition_text(self):
        profile, native = deepcopy(PROFILE), deepcopy(NATIVE)
        profile['terms']['T_PUMP']['definition'] = 'A resource that moves water as appropriate.'
        profile['english']['terms']['T_PUMP'] = term_digest(profile['terms']['T_PUMP'])
        profile['elements']['definition'] = profile['elements'].pop('R_PUMP')
        view = profile['english']['views'].pop('V_PUMP')
        view['element'] = 'definition'
        text = 'The pump moves water. Quote: as appropriate.'
        native['inventory']['documents'][0]['body'] = text
        view['text_sha256'] = text_digest(text)
        start = text.index('as appropriate')
        view['preserved'] = [{'start': start, 'end': start+14, 'text': 'as appropriate',
                              'kind': 'quotation', 'basis': 'Synthetic source wording'}]
        profile['english']['views']['T_PUMP'] = view
        profile['english']['views']['V_ISOLATE']['uses'][1]['element'] = 'definition'
        result = checked(profile, native, review=True, retained_scope_sha256=digest(profile['english']))
        self.assertEqual(result['status'], 'fail')
        phrases = [f for f in result['findings'] if f['rule'] == 'CSE-PHRASE/P_VAGUE']
        self.assertEqual(sorted(f['status'] for f in phrases), ['fail', 'preserved'])
        self.assertTrue(all(f['ids'] == ['T_PUMP', 'definition'] for f in phrases))

    def test_malformed_native_adapter_shapes_return_error_reports(self):
        native_cases = [None, [], 'native', 1, {'status': 'pass', 'inventory': []}]
        for category in ('parts', 'documents'):
            for malformed in (None, {}, [None], ['entry']):
                native = deepcopy(NATIVE); native['inventory'][category] = malformed
                native_cases.append(native)
        native = deepcopy(NATIVE); native['inventory']['documents'][0]['body'] = 3
        native_cases.append(native)
        for native in native_cases:
            with self.subTest(native=native):
                result = check_english(deepcopy(PROFILE), native)
                self.assertEqual(result['status'], 'error')
                self.assertIn('CSE-SCHEMA', rules(result))
                json.dumps(result)
        report = inspect(EXAMPLE/'shared-pump.sysml', EXAMPLE/'shared-pump.english.json', native=[])
        self.assertEqual(report['status'], 'error')
        self.assertIn('CSE-SCHEMA', rules(report))

    def test_native_failure_or_source_text_drift_cannot_pass(self):
        for status in ('error', 'unknown', 'unsupported', 'not_run'):
            with self.subTest(status=status):
                native = deepcopy(NATIVE); native['status'] = status
                self.assertNotEqual(checked(native=native)['status'], 'pass')
        native = deepcopy(NATIVE); native['model_sha256'] = '0'*64
        self.assertIn('CSE-SOURCE-REVISION', rules(checked(native=native)))
        native = deepcopy(NATIVE); native['inventory']['documents'][0]['body'] = 'The pump moves clean water.'
        self.assertIn('CSE-VIEW-REVISION', rules(checked(native=native)))

    def test_required_phrase_fails_but_contextual_advice_stays_visible(self):
        profile, native = edited_text('The pump moves water As Appropriate.')
        report = checked(profile, native)
        self.assertEqual(report['status'], 'fail')
        self.assertTrue(any(x['phrase'] == 'As Appropriate' for x in report['findings']))
        profile, native = edited_text('The pump is suitable.')
        report = checked(profile, native)
        self.assertEqual(report['status'], 'pass'); self.assertEqual(report['advisory_count'], 1)
        self.assertIn('CSE-PHRASE/P_SUITABLE', render_text(report))

    def test_selected_term_labels_and_definitions_are_checked(self):
        profile = deepcopy(PROFILE)
        profile['terms']['T_PUMP']['definition'] += ' Use as appropriate.'
        profile['english']['terms']['T_PUMP'] = term_digest(profile['terms']['T_PUMP'])
        report = checked(profile)
        self.assertIn('CSE-PHRASE/P_VAGUE', rules(report)); self.assertEqual(report['status'], 'fail')

    def test_source_quotation_and_interface_literal_stay_verbatim(self):
        text = 'The pump source says "as appropriate"; the button is "etc.".'
        profile, native = edited_text(text)
        for phrase, kind in [('as appropriate', 'quotation'), ('etc.', 'interface_literal')]:
            start = text.index(phrase)
            profile['english']['views']['V_PUMP']['preserved'].append({'start': start, 'end': start+len(phrase),
                'text': phrase, 'kind': kind, 'basis': 'Exact source wording retained; explain separately.'})
        report = checked(profile, native)
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(sum(x['status'] == 'preserved' for x in report['findings']), 2)
        self.assertEqual(native['inventory']['documents'][0]['body'], text)
        profile['english']['views']['V_PUMP']['preserved'][0]['text'] = 'changed quote'
        self.assertIn('CSE-SOURCE-LITERAL', rules(checked(profile, native)))
        source = profile['english']['views']['V_PUMP']['preserved'][1]
        source['end'] = len(text)+1
        self.assertIn('CSE-SOURCE-LITERAL', rules(checked(profile, native)))

    def test_source_span_cannot_waive_approved_terms_or_count_as_authored_use(self):
        profile, native = edited_text('The water mover moves water.', word='water mover')
        profile['english']['views']['V_PUMP']['preserved'] = [{'start': 4, 'end': 15, 'text': 'water mover',
            'kind': 'quotation', 'basis': 'Preserved source name.'}]
        # Another authored pump use exists in V_ISOLATE, but this proposed authored
        # use is still unresolved instead of becoming a noun-consistency pass.
        self.assertEqual(checked(profile, native)['status'], 'unknown')

    def test_phrase_rules_cannot_be_silently_deselected(self):
        profile, native = edited_text('The pump moves water as appropriate.')
        profile['english']['rules'].remove('CSE-PHRASES')
        self.assertNotEqual(checked(profile, native)['status'], 'pass')

    def test_bad_fields_slots_spans_and_forms_return_errors(self):
        for change in [lambda p: p['terms']['T_PUMP'].update(approved_forms=[]),
                       lambda p: p['terms']['T_PUMP'].update(part_of_speech='adjective'),
                       lambda p: p['english']['views']['V_PUMP']['uses'][0].update(end=True),
                       lambda p: p['english']['views']['V_PUMP']['uses'][0].update(slot='anything'),
                       lambda p: p['english']['views']['V_PUMP']['uses'].append(deepcopy(p['english']['views']['V_PUMP']['uses'][0]))]:
            profile = deepcopy(PROFILE); change(profile)
            self.assertEqual(checked(profile)['status'], 'error')

    def test_diagnostics_are_deterministic_and_default_output_is_bounded(self):
        profile = deepcopy(PROFILE); profile['terms']['T_PUMP']['definition'] += ' Revised.'
        first = checked(profile); profile['terms'] = dict(reversed(list(profile['terms'].items())))
        self.assertEqual(first, checked(profile))
        first['findings'] *= 20
        self.assertLessEqual(len(render_text(first).splitlines()), 14)

    def test_concurrent_profile_edit_during_parser_run_is_rejected(self):
        temporary = ROOT/'.tmp'; temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary) as work:
            work = Path(work); model = work/'model.sysml'; profile = work/'model.english.json'
            model.write_bytes((EXAMPLE/'shared-pump.sysml').read_bytes()); profile.write_text(json.dumps(PROFILE))
            def parse(*args, **kwargs):
                profile.write_text(json.dumps(PROFILE)+' ')
                return deepcopy(NATIVE)
            with patch('verifier.sysml.check_sysml', side_effect=parse):
                report = inspect(model, profile)
            self.assertEqual(report['status'], 'error'); self.assertIn('CSE-INPUT-CHANGED', rules(report))

    def test_auto_profile_errors_and_multifile_selection_cannot_be_skipped(self):
        temporary = ROOT/'.tmp'; temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary) as work:
            model = Path(work)/'model.sysml'; model.write_text('package Test;')
            model.with_suffix('.english.json').write_text('{}')
            report = apply_drafting_profiles(deepcopy(NATIVE), [model])
            self.assertEqual(report['status'], 'error')
            report = apply_drafting_profiles(deepcopy(NATIVE), [model, model])
            self.assertEqual(report['status'], 'unsupported')

    @unittest.skipUnless(JAR.is_file(), 'Pinned native SysML parser unavailable')
    def test_independent_language_skill_and_drafting_launchers_use_actual_native_model(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT/'skills/check-engineering-language/scripts/cse.py'),
            'check', str(EXAMPLE/'shared-pump.sysml'), '--profile', str(EXAMPLE/'shared-pump.english.json'), '--json'],
            text=True, capture_output=True, cwd=ROOT, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'pass')
        for skill in ('develop-system-concept', 'develop-conops', 'develop-operational-scenarios'):
            with self.subTest(skill=skill):
                result = subprocess.run([sys.executable, '-B', str(ROOT/f'skills/{skill}/scripts/cse.py'),
                    'check', str(EXAMPLE/'shared-pump.sysml'), '--syntax-only', '--json'],
                    text=True, capture_output=True, cwd=ROOT, timeout=90)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                self.assertEqual(json.loads(result.stdout)['english']['status'], 'pass')

    @unittest.skipUnless(JAR.is_file(), 'Pinned native SysML parser unavailable')
    def test_normal_drafting_check_rejects_selected_violation_without_review_optin(self):
        temporary = ROOT/'.tmp'; temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary) as work:
            work = Path(work); model = work/'model.sysml'; profile_path = work/'model.english.json'
            source = (EXAMPLE/'shared-pump.sysml').read_text().replace('The pump moves water.', 'The water mover moves water.')
            profile, _ = edited_text('The water mover moves water.', word='water mover')
            profile['source_sha256'] = sha256(source.encode()).hexdigest()
            model.write_text(source); profile_path.write_text(json.dumps(profile))
            for skill in ('develop-system-concept', 'develop-conops', 'develop-operational-scenarios'):
                result = subprocess.run([sys.executable, '-B', str(ROOT/f'skills/{skill}/scripts/cse.py'),
                    'check', str(model), '--syntax-only', '--json'], text=True, capture_output=True, cwd=ROOT, timeout=90)
                self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['english']['status'], 'fail'); self.assertIn('ASD-STE100-1.11', rules(report['english']))


class MeaningPreservingRepairTests(unittest.TestCase):
    def repair(self, before, after):
        return check_repair(before, after, LANGUAGE['actors'], LANGUAGE['properties'], LANGUAGE['clock'], requirement_id='R_ack')

    def test_equivalent_exact_time_units_preserve_supported_meaning(self):
        before = LANGUAGE['requirements']['R_ack']
        self.assertEqual(self.repair(before, before.replace('2 seconds', '2000 milliseconds'))['status'], 'pass')

    def test_shall_weakening_is_rejected(self):
        before = LANGUAGE['requirements']['R_ack']
        report = self.repair(before, before.replace(' shall ', ' should '))
        self.assertEqual(report['status'], 'fail'); self.assertEqual(report['ids'], ['R_ack'])

    def test_negation_and_numeric_unit_changes_are_rejected(self):
        before = LANGUAGE['requirements']['R_ack'].replace('acknowledged = true', 'acknowledged != true')
        for after in (before.replace('acknowledged != true', 'acknowledged = true'),
                      before.replace('2 seconds', '2 milliseconds'), before.replace('2 seconds', '3 seconds')):
            self.assertEqual(self.repair(before, after)['status'], 'fail')

    def test_scope_and_trigger_changes_are_rejected(self):
        before = LANGUAGE['requirements']['R_ack']
        for after in (before.replace('request = true', 'request = false'), before.replace('mode = active', 'mode = inactive')):
            self.assertEqual(self.repair(before, after)['status'], 'fail')

    def test_free_prose_has_no_deterministic_equivalence_verdict(self):
        self.assertEqual(self.repair('The pump must not operate.', 'The pump can operate.')['status'], 'unsupported')


if __name__ == '__main__':
    unittest.main()
