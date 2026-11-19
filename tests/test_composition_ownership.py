"""Native source and affected-view obligations of one explicit owner change."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError, elements
from verifier.composition_ownership import _move_source, destinations
from verifier.composition_ownership_views import reparent, consequences
from verifier.composition_records import embedded_json
from verifier.composition_view import render, find_view
from verifier.composition_project import CompositionProject, request_digest
from verifier.composition_session import CompositionSession


def identity(document, name):
    return next(key for key, value in document.registry.items() if value == name)


def target(document, name):
    return next(row['target'] for row in destinations(document) if row['native_name'] == name)


def tree(identifier, rows):
    return {'id': identifier, 'kind': 'physical_composition', 'mode': 'usages', 'nodes': [
        {'id': key, 'element': element, 'parent': parent, 'level': level, 'edge': edge}
        for key, element, parent, level, edge in rows]}


class OwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        main = tree('PC_OWN', [
            ('Root', 'P::current', None, 0, None),
            ('Left', 'P::current::left', 'Root', 1, 'OwnLeft'),
            ('Sensor', 'P::current::left::sensor', 'Left', 2, 'OwnSensor'),
            ('Leaf', 'P::current::left::sensor::leaf', 'Sensor', 3, 'OwnLeaf'),
            ('Right', 'P::current::right', 'Root', 1, 'OwnRight')])
        detail = tree('PC_DETAIL_LEFT', [
            ('Left', 'P::current::left', None, 0, None),
            ('Sensor', 'P::current::left::sensor', 'Left', 1, 'OwnSensor'),
            ('Leaf', 'P::current::left::sensor::leaf', 'Sensor', 2, 'OwnLeaf')])
        source = ('// Synthetic ownership case 🍀\npackage P { part def T;\n'
                  ' part current { part left : T {\n // Preceding note stays here.\n'
                  ' part <SENSOR> sensor [2] : T { part leaf : T; }\n'
                  ' } part right : T; }\n'
                  ' doc cseViews /* CSE-VIEWS/1.1\n'+embedded_json({'views': [main, detail]}, indent=2)+'\n*/\n}\n')
        cls.document = CompositionDocument({'model.sysml': source})
        cls.subject = identity(cls.document, 'P::current::left::sensor')

    def effects(self):
        layout = render(self.document, 'PC_OWN')['layout']
        owner, child = layout['nodes']['Right'], layout['nodes']['Sensor']
        x, y = owner['x']+owner['width'], owner['y']+owner['height']/2
        points = [[x, y], [x+30, y], [x+30, child['y']+child['height']/2], [child['x'], child['y']+child['height']/2]]
        return [{'view_id': 'PC_OWN', 'action': 'reparent', 'parent_node': 'Right', 'points': points},
                {'view_id': 'PC_DETAIL_LEFT', 'action': 'remove_occurrences'}]

    def test_same_identity_and_all_views_change_together_with_exact_old_geometry(self):
        before = self.document
        effects = self.effects()
        after = reparent(before, self.subject, target(before, 'P::current::right'), None, effects,
                         expected_source_sha256=before.revision)
        self.assertEqual(set(before.registry), set(after.registry))
        self.assertEqual(after.registry[self.subject], 'P::current::right::sensor')
        self.assertEqual(after.registry[identity(before, 'P::current::left::sensor::leaf')], 'P::current::right::sensor::leaf')
        main_before, main_after = render(before, 'PC_OWN'), render(after, 'PC_OWN')
        self.assertEqual(main_after['layout']['nodes'], main_before['layout']['nodes'])
        self.assertEqual(main_after['layout']['edges']['OwnSensor']['points'], effects[0]['points'])
        self.assertEqual(main_after['projection']['edges']['OwnSensor']['source'], 'Right')
        for name, route in main_before['layout']['edges'].items():
            if name != 'OwnSensor':
                self.assertEqual(main_after['layout']['edges'][name], route)
        self.assertEqual(find_view(after, 'PC_DETAIL_LEFT')['nodes'], [find_view(before, 'PC_DETAIL_LEFT')['nodes'][0]])
        self.assertEqual(render(after, 'PC_DETAIL_LEFT')['layout']['nodes']['Left'], render(before, 'PC_DETAIL_LEFT')['layout']['nodes']['Left'])
        self.assertIn('// Preceding note stays here.\n \n } part right', after.files['model.sysml'])
        self.assertEqual(before.files, self.document.files)

    def test_missing_extra_duplicate_or_invalid_view_consequences_refuse_whole_candidate(self):
        before, effects = self.document, self.effects()
        invalid = [[], effects[:1], effects+[effects[0]],
                   [{**effects[0], 'parent_node': 'Left'}, effects[1]],
                   [{**effects[0], 'points': [[0, 0], [1, 1]]}, effects[1]],
                   [effects[0], {'view_id': 'PC_DETAIL_LEFT', 'action': 'preserve_structure'}]]
        for selected in invalid:
            with self.subTest(effect=selected), self.assertRaises(EditError):
                reparent(before, self.subject, target(before, 'P::current::right'), None, selected,
                         expected_source_sha256=before.revision)
        self.assertEqual(before.registry[self.subject], 'P::current::left::sensor')
        self.assertEqual(render(before, 'PC_OWN')['projection']['edges']['OwnSensor']['source'], 'Left')

    def test_native_owner_kinds_composition_and_subtree_context(self):
        for form, root_kind in [('part Subject [2] : P::T { part leaf : P::T; }', 'parts'),
                                ('ref part Subject [2] : P::T { part leaf : P::T; }', 'parts'),
                                ('part def Subject { part leaf : P::T; }', 'part_definitions')]:
            for destination in ('P::B', 'P', None):
                with self.subTest(form=form, destination=destination):
                    document = CompositionDocument({'model.sysml': 'package P { part def T; part def A { '+form+' } part def B; }\n'})
                    element = identity(document, 'P::A::Subject')
                    expected = root_kind == 'parts' and not form.startswith('ref') and destination == 'P::B'
                    ack = {'before': True, 'after': False} if root_kind == 'parts' and not form.startswith('ref') and not expected else None
                    after = _move_source(document, element, target(document, destination), ack, expected_source_sha256=document.revision)
                    native = elements(after.parsed)[after.registry[element]]
                    leaf = elements(after.parsed)[after.registry[identity(document, 'P::A::Subject::leaf')]]
                    if root_kind == 'parts':
                        self.assertEqual(native['is_composite'], expected)
                        self.assertEqual(native.get('part_definition'), 'P::B' if destination == 'P::B' else None)
                        self.assertEqual(leaf.get('part_definition'), 'P::B' if destination == 'P::B' else None)
                    else:
                        self.assertEqual(leaf['part_definition'], after.registry[element])
                    self.assertTrue(leaf['is_composite'])
                    self.assertEqual(set(document.registry), set(after.registry))

    def test_source_unicode_comments_aliases_cross_file_and_reference_targets(self):
        files = {'a.sysml': "// 🛰 exact\r\npackage P { part def Device; part def A {\r\n // remains A\r\n part def 'rôle' { part leaf : Device; }\r\n } alias chosen for A::'rôle'; part watcher : chosen; }\r\n",
                 'b.sysml': '/* exact second source */\npackage Q { part def Device; part def B; }\n'}
        document = CompositionDocument(files)
        subject = identity(document, "P::A::'rôle'")
        after = _move_source(document, subject, target(document, 'Q::B'), None, expected_source_sha256=document.revision)
        self.assertEqual(set(document.registry), set(after.registry))
        self.assertIn('// remains A\r\n \r\n }', after.files['a.sysml'])
        self.assertIn("part def 'rôle' { part leaf : P::Device; }", after.files['b.sysml'])
        self.assertEqual(elements(after.parsed)['P::watcher']['type'], "Q::B::'rôle'")
        self.assertIn('/* exact second source */\npackage Q { part def Device; part def B {', after.files['b.sysml'])

    def test_cycles_same_owner_stale_bad_span_collision_and_unacknowledged_transition_refuse(self):
        document = self.document
        requests = [target(document, 'P::current::left'), target(document, 'P::current::left::sensor'),
                    target(document, 'P::current::left::sensor::leaf')]
        for owner in requests:
            with self.subTest(owner=owner), self.assertRaises(EditError):
                _move_source(document, self.subject, owner, None, expected_source_sha256=document.revision)
        with self.assertRaises(EditError) as caught:
            _move_source(document, self.subject, target(document, 'P'), None, expected_source_sha256=document.revision)
        self.assertEqual(caught.exception.code, 'composition_transition')
        for digest in ('stale', None):
            with self.assertRaises(EditError):
                _move_source(document, self.subject, target(document, 'P::current::right'), None, expected_source_sha256=digest)
        bad = deepcopy(document)
        bad.parsed['reference_spans'][0]['source_tokens'][0]['offset'] = 0
        with self.assertRaises(EditError) as caught:
            _move_source(bad, self.subject, target(bad, 'P::current::right'), None, expected_source_sha256=bad.revision)
        self.assertEqual(caught.exception.code, 'source_span')

    def test_namespace_locator_is_bound_to_original_bundle_after_unrelated_revision(self):
        before = self.document
        captured = target(before, 'P')
        after = before.rename(identity(before, 'P::T'), 'Other', expected_source_sha256=before.revision)
        with self.assertRaises(EditError) as caught:
            _move_source(after, self.subject, captured, {'before': True, 'after': False}, expected_source_sha256=after.revision)
        self.assertEqual(caught.exception.code, 'stale_revision')

    def test_retained_inherited_scope_reports_new_failure_without_silent_acceptance(self):
        fixture = json.loads((ROOT/'tests/fixtures/composition-role-inspection.json').read_text())
        case = fixture['cases'][0]
        models = {name:text.replace('part def Sensor;', 'part def Sensor; part def Other;') for name,text in case['models'].items()}
        linked = {'scope.json': {'kind': 'retained_configuration', 'text': case['retained_scope_text']}}
        before = CompositionDocument(models, project_id=fixture['project_id'], linked_records=linked)
        subject = identity(before, 'Composition::Base::sensor')
        self.assertEqual(consequences(before, subject), [])
        after = before.reparent(subject, target(before, 'Composition::Other'), None, [], expected_source_sha256=before.revision)
        self.assertEqual(before.configuration_reviews[0]['report']['status'], 'pass')
        self.assertEqual(after.configuration_reviews[0]['report']['status'], 'fail')
        self.assertEqual(after.linked_records['scope.json'], before.linked_records['scope.json'])
        self.assertEqual(set(before.registry), set(after.registry))
        for view in ('PC_CONTEXT', 'PC_DECLARATION'):
            self.assertEqual(render(before, view)['svg'], render(after, view)['svg'])

    def test_checked_git_preview_receipt_exact_retry_stale_refusal_and_monotonic_restore(self):
        before = self.document
        with tempfile.TemporaryDirectory() as temporary:
            project, initial = CompositionProject.create(Path(temporary)/'project.git', before.files,
                project_id=before.project_id, request_id=str(uuid4()), linked_records=before.linked_records)
            request = {'operation': 'reparent', 'request_id': str(uuid4()), 'expected_revision': 1,
                       'element_id': self.subject, 'destination': target(before, 'P::current::right'),
                       'composition_transition': None, 'view_effects': self.effects(), 'checked_bundle_sha256': None}
            request['view_effects'][0]['points'] = [
                [float(value) for value in point] for point in request['view_effects'][0]['points']]
            with self.assertRaises(EditError) as caught:
                project.transact(request)
            self.assertEqual(caught.exception.code, 'checked_candidate')
            self.assertEqual(project.head(), initial['commit'])
            session = CompositionSession(project, 'PC_OWN')
            context = session.ownership_context(element_id=self.subject, expected_revision=1,
                expected_bundle_sha256=before.revision, offset=0, limit=1, view_id='PC_DETAIL_LEFT')
            self.assertEqual(len(context['destinations']), 1)
            self.assertEqual(context['next_offset'], 1)
            self.assertEqual(context['view_detail']['subject_node'], 'Sensor')
            preview = session.preview(request)
            checked = preview['checked_request']
            self.assertTrue(any(type(value) is int for point in checked['view_effects'][0]['points'] for value in point))
            self.assertEqual(checked['checked_bundle_sha256'], preview['candidate_bundle_sha256'])
            self.assertEqual(preview['request_sha256'], request_digest(checked))
            self.assertEqual(project.head(), initial['commit'])
            detail = session.preview_view(checked, 'PC_DETAIL_LEFT')
            self.assertEqual(detail['candidate_bundle_sha256'], checked['checked_bundle_sha256'])
            self.assertEqual(detail['request_sha256'], request_digest(checked))
            changed = {**checked, 'checked_bundle_sha256': '0'*64, 'request_id': str(uuid4())}
            with self.assertRaises(EditError) as caught:
                project.transact(changed)
            self.assertEqual(caught.exception.code, 'checked_candidate')
            self.assertEqual(project.head(), initial['commit'])
            saved = session.apply(checked)['receipt']
            self.assertEqual(saved['revision'], 2)
            self.assertEqual(project.lookup_receipt(checked)['receipt'], saved)
            float_spelling = {**request, 'checked_bundle_sha256': checked['checked_bundle_sha256']}
            self.assertEqual(project.lookup_receipt(float_spelling)['receipt'], saved)
            self.assertEqual(project.transact(float_spelling), saved)
            self.assertEqual(project.transact(checked), saved)
            restored = project.transact({'operation': 'restore', 'request_id': str(uuid4()), 'expected_revision': 2, 'target_revision': 1})
            self.assertEqual(restored['revision'], 3)
            self.assertEqual(project.transact(checked), saved)
            stale = {**checked, 'request_id': str(uuid4())}
            with self.assertRaises(EditError) as caught:
                project.transact(stale)
            self.assertEqual(caught.exception.code, 'stale_revision')
            reopened = CompositionProject(project.repository).snapshot()
            self.assertEqual(reopened['revision'], 3)
            self.assertEqual(reopened['document'].files, before.files)
            self.assertEqual(reopened['document'].registry, before.registry)
            self.assertEqual(len(project.history()), 3)


if __name__ == '__main__':
    unittest.main()
