"""Independent controls for the preservation defects found in Astra review."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError, bounds
from verifier.composition_ownership import _move_source, destinations
from verifier.composition_ownership_views import consequences
from verifier.composition_project import CompositionProject
from verifier.composition_records import embedded_json
from verifier.composition_view import render


def identity(document, name):
    return next(key for key, value in document.registry.items() if value == name)


def target(document, name):
    return next(row['target'] for row in destinations(document) if row['native_name'] == name)


class OwnershipPreservationTests(unittest.TestCase):
    def test_relocation_keeps_an_existing_name_longer_than_new_name_authoring_limit(self):
        name = 'Existing'+'LongName'*10
        before = CompositionDocument('package P { part def A { part '+name+'; } part def B; }')
        after = before.reparent(identity(before, 'P::A::'+name), target(before, 'P::B'), None, [],
                                expected_source_sha256=before.revision)
        self.assertIn('P::B::'+name, after.registry.values())
        self.assertIn('part '+name+';', after.source)

    def test_same_scope_native_and_alias_reference_spellings_stay_exact(self):
        for type_text in ('T', 'TypeAlias', '// hidden type note\n TypeAlias'):
            with self.subTest(type_text=type_text):
                fragment = 'part <SUBJ> Subject [2] : '+type_text+' { part leaf : TypeAlias; }'
                before = CompositionDocument('package P { part def T; alias TypeAlias for T; part def A { '+fragment+' } part def B; }')
                after = _move_source(before, identity(before, 'P::A::Subject'), target(before, 'P::B'), None,
                                     expected_source_sha256=before.revision)
                self.assertIn(fragment, after.source)
                self.assertEqual(after.ownership_change['repaired_reference_count'], 0)
                self.assertNotIn(': P::T', after.source)

    def test_repair_alias_declaration_before_preserving_its_consumers(self):
        before = CompositionDocument({'a.sysml': 'package P { part def T; part def A { part def Subject { alias Local for T; part leaf : Local; } } }\n',
                                      'b.sysml': 'package Q { part def T; part def B; }\n'})
        after = _move_source(before, identity(before, 'P::A::Subject'), target(before, 'Q::B'), None,
                             expected_source_sha256=before.revision)
        self.assertIn('alias Local for P::T; part leaf : Local;', after.files['b.sysml'])
        self.assertEqual(after.ownership_change['repaired_reference_count'], 1)
        self.assertEqual(after.ownership_change['reference_repair_rounds'], 1)

    def test_alias_dependency_chain_retains_unchanged_alias_tokens(self):
        before = CompositionDocument({'a.sysml': 'package P { part def T; part def A { part def Subject { alias First for T; alias Second for First; part leaf : Second; } } }\n',
                                      'b.sysml': 'package Q { part def T; part def B; }\n'})
        after = _move_source(before, identity(before, 'P::A::Subject'), target(before, 'Q::B'), None,
                             expected_source_sha256=before.revision)
        self.assertIn('alias First for P::T; alias Second for First; part leaf : Second;', after.files['b.sysml'])
        self.assertEqual(after.ownership_change['repaired_reference_count'], 1)

    def test_library_alias_spans_never_use_library_offsets_in_the_user_source(self):
        fragment = 'part def Subject { attribute x : Attributes::AttributeValue; }'
        before = CompositionDocument('package P { part def A { '+fragment+' } part def B; }')
        segment = next(segment for ref in before.parsed['reference_spans'] for segment in ref['name_binding']['segments']
                       if segment.get('kind') == 'alias_name')
        self.assertTrue(segment['alias_is_external'])
        self.assertNotIn('alias_source_span', segment)
        after = before.reparent(identity(before, 'P::A::Subject'), target(before, 'P::B'), None, [],
                                expected_source_sha256=before.revision)
        self.assertIn(fragment, after.source)
        self.assertEqual(after.ownership_change['repaired_reference_count'], 0)

    def test_external_alias_lost_from_local_import_is_repaired_without_moving_import(self):
        source = 'package P { part def A { private import Attributes::*; part def Subject { attribute x : AttributeValue; } } part def B; }'
        before = CompositionDocument(source)
        after = before.reparent(identity(before, 'P::A::Subject'), target(before, 'P::B'), None, [],
                                expected_source_sha256=before.revision)
        self.assertIn('private import Attributes::*;', after.source)
        self.assertIn('attribute x : Attributes::AttributeValue;', after.source)
        self.assertEqual(after.ownership_change['repaired_reference_count'], 1)

    def test_equal_target_alias_shadow_preserves_original_alias_membership(self):
        source = ('package P { part def T; part def U; '
                  'part def A { alias Pick for P::T; part Subject : Pick; } '
                  'part def B { alias Pick for P::T; } }')
        before = CompositionDocument(source)
        after = before.reparent(identity(before, 'P::A::Subject'), target(before, 'P::B'), None, [],
                                expected_source_sha256=before.revision)
        self.assertIn('part Subject : P::A::Pick;', after.source)
        self.assertEqual(after.ownership_change['repaired_reference_count'], 1)
        altered = after.source.replace('part def B { alias Pick for P::T;', 'part def B { alias Pick for P::U;')
        reparsed = CompositionDocument(altered)
        subject = next(row for row in reparsed.parsed['parts'] if row['qualified_name'] == 'P::B::Subject')
        self.assertEqual(subject['types'], ['P::T'])

    def root_document(self):
        record = {'views': [{'id': 'PC_ROOT', 'kind': 'physical_composition', 'mode': 'usages', 'nodes': [
            {'id': 'Subject', 'element': 'P::A::Subject', 'parent': None, 'level': 0, 'edge': None},
            {'id': 'Leaf', 'element': 'P::A::Subject::leaf', 'parent': 'Subject', 'level': 1, 'edge': 'OwnLeaf'}]}]}
        # Whitespace before commas is intentional authored source.
        payload = embedded_json(record, separators=('  ,\n', ' : '))
        return CompositionDocument({'model.sysml': 'package P { part def A { part Subject { part leaf; } } part def B; doc cseViews /* CSE-VIEWS/1.1\n'+payload+'\n*/ }\n'})

    def test_root_boundary_preserves_default_or_authored_layout_and_source_trivia(self):
        for authored in (False, True):
            with self.subTest(authored=authored):
                before = self.root_document()
                layout = render(before, 'PC_ROOT')['layout']
                if authored:
                    text = json.dumps(dict(reversed(list(layout.items()))), separators=(' , ', ' : '))+'\n\n'
                    before = CompositionDocument(before.files, project_id=before.project_id, registry=before.registry,
                        linked_records={'author-layout.json': {'kind': 'composition_layout', 'text': text}})
                old_doc = next(row for row in before.parsed['documents'] if row.get('name') == 'cseViews')
                old_token = before.source[slice(*bounds(before.source, old_doc['source_span'], 'body_'))]
                after = before.reparent(identity(before, 'P::A::Subject'), target(before, 'P::B'), None,
                    [{'view_id': 'PC_ROOT', 'action': 'preserve_structure'}], expected_source_sha256=before.revision)
                new_doc = next(row for row in after.parsed['documents'] if row.get('name') == 'cseViews')
                new_token = after.source[slice(*bounds(after.source, new_doc['source_span'], 'body_'))]
                self.assertEqual(new_token, old_token.replace('P::A::Subject', 'P::B::Subject'))
                self.assertEqual(after.linked_records, before.linked_records)
                self.assertEqual(render(after, 'PC_ROOT')['layout'], layout)

    def test_absent_views_allow_empty_effects_but_malformed_declared_views_refuse(self):
        before = CompositionDocument('package P { part def A { part Subject; } part def B; }')
        self.assertEqual(consequences(before, identity(before, 'P::A::Subject')), [])
        after = before.reparent(identity(before, 'P::A::Subject'), target(before, 'P::B'), None, [],
                                expected_source_sha256=before.revision)
        self.assertEqual(set(after.registry), set(before.registry))
        self.assertIn('P::B::Subject', after.registry.values())
        malformed = CompositionDocument('package P { part def A { part Subject; } part def B; doc cseViews /* CSE-VIEWS/1.1\n{"views":"invalid"}\n*/ }')
        with self.assertRaises(EditError):
            malformed.reparent(identity(malformed, 'P::A::Subject'), target(malformed, 'P::B'), None, [],
                               expected_source_sha256=malformed.revision)

    def test_legacy_import_without_views_keeps_checked_transaction_contract(self):
        models = {'model.sysml': 'package P { part def T; part def A { part Subject : T; } part def B; }\n'}
        with tempfile.TemporaryDirectory() as temporary:
            project, first = CompositionProject.create(Path(temporary)/'legacy.git', models,
                project_id=str(uuid4()), request_id=str(uuid4()))
            before = project.snapshot()['document']
            request = {'operation': 'reparent', 'request_id': str(uuid4()), 'expected_revision': 1,
                       'element_id': identity(before, 'P::A::Subject'), 'destination': target(before, 'P::B'),
                       'composition_transition': None, 'view_effects': [], 'checked_bundle_sha256': None}
            preview = project.preview(request)
            self.assertEqual(project.head(), first['commit'])
            saved = project.transact(preview['checked_request'])
            self.assertEqual(saved['revision'], 2)
            self.assertEqual(project.transact(preview['checked_request']), saved)
            self.assertEqual(project.snapshot()['document'].linked_records, {})


if __name__ == '__main__':
    unittest.main()
