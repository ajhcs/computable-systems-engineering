"""Native source-edit controls, including Unicode, references and identity."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError, codepoint_index
from verifier.composition_records import rebind_json, rebind_document
from verifier.workflow import empty_record, draft_model


SOURCE = '''// 🛰 Sensor and sensor in a comment must survive byte-for-byte.
package Composition {
    part def Sensor;
    part def Base { part <SENSOR> sensor [2] : Sensor; }
    part def Assembly :> Base { part :>> sensor : Sensor; }
    part current : Assembly;
}
'''


class CoordinateTests(unittest.TestCase):
    def test_astral_character_and_invalid_boundaries(self):
        self.assertEqual(codepoint_index('a🛰b', 3), 2)
        for offset in (-1, True, 2, 5):
            with self.subTest(offset=offset), self.assertRaises(EditError):
                codepoint_index('a🛰b', offset)


class NativeEditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = CompositionDocument(SOURCE, project_id='42d0daa7-6464-40cc-b5c8-10f2717f3495')

    def identity(self, name):
        return next(key for key, value in self.document.registry.items() if value == name)

    def rename(self, old, new):
        return self.document.rename(self.identity(old), new,
                                    expected_source_sha256=self.document.revision)

    def test_definition_rename_changes_only_declaration_and_resolved_types(self):
        result = self.rename('Composition::Sensor', 'Detector')
        expected = SOURCE.replace('part def Sensor;', 'part def Detector;').replace(': Sensor;', ': Detector;')
        self.assertEqual(result.source, expected)
        self.assertEqual(set(result.registry), set(self.document.registry))
        self.assertEqual(result.registry[self.identity('Composition::Sensor')], 'Composition::Detector')
        self.assertEqual(self.document.source, SOURCE)

    def test_role_rename_preserves_short_id_and_resolves_redefinition(self):
        result = self.rename('Composition::Base::sensor', 'detector')
        self.assertIn('part <SENSOR> detector [2] : Sensor;', result.source)
        self.assertIn('part :>> detector : Sensor;', result.source)
        facts = next(x for x in result.inspect()['elements'] if x['qualified_name'] == 'Composition::Base::detector')
        self.assertEqual(facts['id'], 'SENSOR')
        self.assertEqual(facts['multiplicity'], {'status': 'literal', 'lower': 2, 'upper': 2})

    def test_container_rename_preserves_descendant_ids(self):
        result = self.rename('Composition::Base', 'Platform')
        self.assertIn('part def Assembly :> Platform', result.source)
        self.assertEqual(result.registry[self.identity('Composition::Base::sensor')],
                         'Composition::Platform::sensor')

    def test_registry_roundtrip_and_ambiguous_external_rename(self):
        restored = CompositionDocument(SOURCE, project_id=self.document.project_id,
                                       registry=self.document.registry)
        self.assertEqual(restored.registry, self.document.registry)
        with self.assertRaises(EditError) as error:
            CompositionDocument(SOURCE.replace('part current', 'part changed'),
                                project_id=self.document.project_id, registry=self.document.registry)
        self.assertEqual(error.exception.code, 'reconciliation')

    def test_stale_invalid_colliding_and_unknown_requests(self):
        cases = [(self.identity('Composition::Sensor'), 'Detector', 'stale'),
                 (self.identity('Composition::Sensor'), 'Base', self.document.revision),
                 ('missing', 'Detector', self.document.revision),
                 (self.identity('Composition::Sensor'), 'bad name', self.document.revision)]
        for identity, name, revision in cases:
            with self.subTest(name=name, revision=revision), self.assertRaises(EditError):
                self.document.rename(identity, name, expected_source_sha256=revision)
        self.assertEqual(self.document.source, SOURCE)

    def test_candidate_reparse_timeout_is_structured_and_preserves_original(self):
        with patch('verifier.composition_edit._parser_output', side_effect=subprocess.TimeoutExpired('pilot', 60)):
            with self.assertRaises(EditError) as error:
                self.rename('Composition::Sensor', 'Detector')
        self.assertEqual(error.exception.code, 'parser_timeout')
        self.assertEqual(self.document.source, SOURCE)

    def test_prose_documentation_is_preserved_verbatim(self):
        source = 'package Documentary { part def Sensor { doc /* Sensor narrative */ } }'
        document = CompositionDocument(source)
        candidate = document.rename(next(iter(document.registry)), 'Detector',
                                    expected_source_sha256=document.revision)
        self.assertEqual(candidate.source, source.replace('part def Sensor', 'part def Detector'))

    def test_unknown_computational_document_needs_a_typed_adapter(self):
        source = 'package Documentary { part def Sensor { doc cseUnknown /* CSE-UNKNOWN/1.0\n{} */ } }'
        document = CompositionDocument(source)
        with self.assertRaises(EditError) as error:
            document.rename(next(iter(document.registry)), 'Detector',
                            expected_source_sha256=document.revision)
        self.assertEqual(error.exception.code, 'linked_records')


FILES = {
    'types/library.sysml': '// 🛰 preserve comments and CRLF\r\npackage Library {\r\n'
        ' part def Sensor;\r\n part def Base { part <SENSOR> sensor [2] : Sensor; }\r\n'
        ' part def Assembly :> Base;\r\n}\r\n',
    'context.sysml': 'package Context { private import Library::*; part current : Assembly; }',
}

REFERENCE_SOURCE = (ROOT/'examples/workbench/composition/reference-names.sysml').read_text()
REFERENCE_SCOPE = {'version': 'configuration-1.0',
                   'root': {'native_name': 'ReferenceComposition::current', 'type': 'ReferenceComposition::Base'},
                   'selected_roles': {'Role': {'parent': '$root', 'native_name': 'ReferenceComposition::Base::role',
                                              'type': "ReferenceComposition::'Sénsor::unit'"}},
                   'open_alternatives': [], 'connections': []}


class ReferenceNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = CompositionDocument(REFERENCE_SOURCE, project_id='d6e6fc68-52f5-4a97-bbd7-2e5aaf6cc322')

    def rename(self, document, old, new):
        identity = next(k for k, value in document.registry.items() if value == old)
        result = document.rename(identity, new, expected_source_sha256=document.revision)
        self.assertEqual(set(result.registry), set(document.registry))
        self.assertEqual(document.registry[identity], old)
        return result

    def test_declared_name_short_ids_alias_names_and_alias_short_ids_have_native_bindings(self):
        selected = [r for r in self.document.parsed['reference_spans']
                    if r['text'].strip() in ["'Sénsor::unit'", 'S', 'DetectorAlias', 'AS']]
        self.assertTrue(selected)
        kinds = {r['name_binding']['segments'][-1]['kind'] for r in selected}
        self.assertEqual(kinds, {'name', 'short_name', 'alias_name', 'alias_short_name'})
        for ref in selected:
            self.assertEqual(ref['name_binding']['status'], 'resolved')
            self.assertEqual(ref['name_binding']['segments'][-1]['target'], ref['target'])

    def test_type_rename_preserves_alias_declarations_consumers_and_short_spellings(self):
        result = self.rename(self.document, "ReferenceComposition::'Sénsor::unit'", 'Detector')
        expected = REFERENCE_SOURCE.replace("part def <S> 'Sénsor::unit';", 'part def <S> Detector;')
        expected = expected.replace("for 'Sénsor::unit';", 'for Detector;')
        expected = expected.replace("part direct : 'Sénsor::unit';", 'part direct : Detector;')
        expected = expected.replace("ReferenceComposition::'Sénsor::unit'", 'ReferenceComposition::Detector')
        self.assertEqual(result.source, expected)
        self.assertIn("alias 'Sénsor::unit' for ReferenceComposition::Detector;", result.source)
        self.assertIn("part aliasConsumer : 'Sénsor::unit';", result.source)
        for name in ['S', 'DetectorAlias', 'AS']:
            self.assertIn(': '+name+';', result.source)

    def test_owner_prefix_updates_even_when_final_aliased_target_keeps_its_name(self):
        result = self.rename(self.document, 'ReferenceComposition::Outer', 'Platform')
        expected = REFERENCE_SOURCE.replace('part def <O> Outer {', 'part def <O> Platform {')
        expected = expected.replace('alias OuterAlias for Outer;', 'alias OuterAlias for Platform;')
        expected = expected.replace('part remote : Outer::Remote;', 'part remote : Platform::Remote;')
        expected = expected.replace('ReferenceComposition::Outer', 'ReferenceComposition::Platform')
        self.assertEqual(result.source, expected)
        self.assertIn('part shortPath : O::I;', result.source)
        before = next(r for r in self.document.parsed['reference_spans'] if r['text'].strip() == 'Outer::Remote')
        after = next(r for r in result.parsed['reference_spans'] if r['text'].strip() == 'Platform::Remote')
        self.assertEqual(before['target'], after['target'])

    def test_quoted_name_with_colons_keeps_source_trivia_and_mixed_short_path(self):
        result = self.rename(self.document, "ReferenceComposition::Outer::'Inner::device'", 'Module')
        expected = REFERENCE_SOURCE.replace("part def <I> 'Inner::device';", 'part def <I> Module;')
        expected = expected.replace("OuterAlias::'Inner::device';", 'OuterAlias::Module;')
        expected = expected.replace("ReferenceComposition::Outer::'Inner::device'", 'ReferenceComposition::Outer::Module')
        self.assertEqual(result.source, expected)
        self.assertIn('OuterAlias::Module; //* retain qualifier note */', result.source)
        self.assertIn('part shortPath : O::I;', result.source)

    def test_redefinition_by_short_id_survives_renamed_inherited_role(self):
        result = self.rename(self.document, 'ReferenceComposition::Base::role', 'detector')
        self.assertEqual(result.source, REFERENCE_SOURCE.replace('part <ROLE> role [2]', 'part <ROLE> detector [2]'))
        self.assertIn('part :>> ROLE : S;', result.source)
        self.assertIn('ReferenceComposition::Derived::detector', result.registry.values())

    def test_native_owner_handles_roots_and_quoted_namespace_colons(self):
        cases = [("part def <R> 'Root::frame'; part direct : 'Root::frame'; part byId : R;",
                  "'Root::frame'", 'part def <R> Detector; part direct : Detector; part byId : R;'),
                 ("package 'Pkg::box' { part def <R> 'Root::frame'; part direct : R; }",
                  "'Pkg::box'::'Root::frame'", "package 'Pkg::box' { part def <R> Detector; part direct : R; }")]
        for source, old, expected in cases:
            with self.subTest(old=old):
                document = CompositionDocument(source)
                result = self.rename(document, old, 'Detector')
                self.assertEqual(result.source, expected)

    def test_equal_declared_name_and_short_id_preserves_the_short_reference_spelling(self):
        source = 'package Equal { part def <Same> Same; alias First for Same; alias Second for First; part direct : Same; part chained : Second; }'
        document = CompositionDocument(source)
        result = self.rename(document, 'Equal::Same', 'Detector')
        self.assertEqual(result.source, source.replace('part def <Same> Same;', 'part def <Same> Detector;'))

    def test_root_identity_does_not_rewrite_equal_short_ids_local_names_or_literal_statuses(self):
        cases = [('part def <Same> Same; part usage [2] : Same;', 'Same',
                  'part def <Same> Detector; part usage [2] : Same;'),
                 ('part def literal; part usage [2] : literal;', 'literal',
                  'part def Detector; part usage [2] : Detector;'),
                 ('part def unsupported; part usage [1..*] : unsupported;', 'unsupported',
                  'part def Detector; part usage [1..*] : Detector;'),
                 ('part def role; part def Container { part role : $::role; }', 'role',
                  'part def Detector; part def Container { part role : $::Detector; }')]
        for source, old, expected in cases:
            with self.subTest(old=old):
                document = CompositionDocument(source)
                result = self.rename(document, old, 'Detector')
                self.assertEqual(result.source, expected)

    def test_unnamed_redefinition_chain_changes_names_but_named_redefinition_keeps_its_name(self):
        source = 'package Chain { part def <S> Sensor; part def Base { part <ROLE> role : S; } '
        source += 'part def Mid :> Base { part :>> ROLE : S; } part def Leaf :> Mid { part :>> role : S; } '
        source += 'part def Named :> Base { part explicit :>> ROLE : S; } }'
        document = CompositionDocument(source)
        result = self.rename(document, 'Chain::Base::role', 'detector')
        expected = source.replace('<ROLE> role :', '<ROLE> detector :').replace('part :>> role :', 'part :>> detector :')
        self.assertEqual(result.source, expected)
        for name in ['Chain::Mid::detector', 'Chain::Leaf::detector', 'Chain::Named::explicit']:
            self.assertIn(name, result.registry.values())

    def test_renamed_type_prefix_does_not_change_inherited_members_native_owner(self):
        source = 'package Inherited { part def Sensor; part def Base { part role : Sensor; } '
        source += 'part def Mid :> Base; alias Exposed for Mid::role; }'
        document = CompositionDocument(source)
        result = self.rename(document, 'Inherited::Mid', 'Middle')
        self.assertEqual(result.source, source.replace('part def Mid :>', 'part def Middle :>').replace('for Mid::role;', 'for Middle::role;'))
        before = next(r for r in document.parsed['reference_spans'] if r['text'].strip() == 'Mid::role')
        after = next(r for r in result.parsed['reference_spans'] if r['text'].strip() == 'Middle::role')
        self.assertEqual(before['target'], 'Inherited::Base::role')
        self.assertEqual(after['target'], before['target'])

    def test_multifile_crlf_and_unrelated_source_bytes_are_exact(self):
        source = REFERENCE_SOURCE.replace('\n', '\r\n')
        files = {'types.sysml': source, 'unrelated.sysml': '// untouched 🛰\r\npackage Unrelated;\r\n'}
        document = CompositionDocument(files)
        result = self.rename(document, "ReferenceComposition::Outer::'Inner::device'", 'Module')
        self.assertEqual(result.files['unrelated.sysml'], files['unrelated.sysml'])
        expected = source.replace("part def <I> 'Inner::device';", 'part def <I> Module;').replace("OuterAlias::'Inner::device';", 'OuterAlias::Module;')
        expected = expected.replace("ReferenceComposition::Outer::'Inner::device'", 'ReferenceComposition::Outer::Module')
        self.assertEqual(result.files['types.sysml'], expected)

    def test_affected_missing_native_binding_is_refused_without_changing_source(self):
        document = deepcopy(self.document)
        ref = next(r for r in document.parsed['reference_spans'] if r['target'] == "ReferenceComposition::'Sénsor::unit'")
        ref.pop('name_binding')
        with self.assertRaises(EditError) as error:
            self.rename(document, "ReferenceComposition::'Sénsor::unit'", 'Detector')
        self.assertEqual(error.exception.code, 'reference_form')
        self.assertEqual(document.source, REFERENCE_SOURCE)

    def test_native_segment_span_mismatch_cannot_edit_an_unrelated_token(self):
        document = deepcopy(self.document)
        ref = next(r for r in document.parsed['reference_spans'] if r['target'] == "ReferenceComposition::'Sénsor::unit'")
        ref['name_binding']['segments'][0]['text'] = 'unrelated token'
        with self.assertRaises(EditError) as error:
            self.rename(document, "ReferenceComposition::'Sénsor::unit'", 'Detector')
        self.assertEqual(error.exception.code, 'parser_contract')
        self.assertEqual(document.source, REFERENCE_SOURCE)

    def test_full_native_fingerprint_rejects_an_unrequested_semantic_delta(self):
        from verifier.composition_edit import parse as native_parse
        def changed_fact(source):
            result = native_parse(source)
            result['parts'][0]['is_composite'] = not result['parts'][0]['is_composite']
            return result
        with patch('verifier.composition_edit.parse', side_effect=changed_fact), self.assertRaises(EditError) as error:
            self.rename(self.document, "ReferenceComposition::Outer::'Inner::device'", 'Module')
        self.assertEqual(error.exception.code, 'semantic_delta')
        self.assertEqual(self.document.source, REFERENCE_SOURCE)

    def test_source_cli_matches_the_independently_expected_reference_edit(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as directory:
            path = Path(directory)/'source.sysml'
            path.write_text(REFERENCE_SOURCE)
            old = "ReferenceComposition::Outer::'Inner::device'"
            identity = next(k for k, v in self.document.registry.items() if v == old)
            result = subprocess.run([sys.executable, '-B', str(ROOT/'scripts/composition_edit.py'),
                'rename', str(path), '--project-id', self.document.project_id, '--element-id', identity,
                '--name', 'Module', '--expected-source-sha256', self.document.revision],
                capture_output=True, text=True, check=True)
            report = json.loads(result.stdout)
            expected = REFERENCE_SOURCE.replace("part def <I> 'Inner::device';", 'part def <I> Module;')
            expected = expected.replace("OuterAlias::'Inner::device';", 'OuterAlias::Module;')
            expected = expected.replace(old, 'ReferenceComposition::Outer::Module')
            self.assertEqual(report['source'], expected)
            self.assertEqual(report['registry'][identity], 'ReferenceComposition::Outer::Module')
            self.assertEqual(path.read_text(), REFERENCE_SOURCE)
            self.assertEqual(report['claim'], 'candidate_only_not_persisted')
SCOPE = {'version': 'configuration-1.0',
         'root': {'native_name': 'Context::current', 'type': 'Library::Assembly'},
         'selected_roles': {'SensorRole': {'parent': '$root', 'native_name': 'Library::Base::sensor',
                                           'type': 'Library::Sensor'}},
         'open_alternatives': [], 'connections': []}


def metadata():
    record = empty_record('Retain prose Library::Base::sensor verbatim.', 'architecture')
    record['elements']['ROLE'] = {'kind': 'element', 'native_name': 'Library::Base::sensor',
                                  'label': 'sensor', 'description': 'Library::Base::sensor',
                                  'basis': None, 'status': 'proposed'}
    return draft_model(record, 'Metadata', 'package MetadataNote { doc /* Library::Base::sensor */ }')


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {**FILES, 'notes/metadata.sysml': metadata()}
        cls.scope_text = json.dumps(SCOPE, indent=2) + '\n'
        cls.labels = '{"version":1,"view":"PC","title":"Library::Base::sensor","labels": [\n' \
                     ' { "element" : "Library::Base::sensor", "text" : "sensor" }\n]}\n'
        cls.linked = {'view.labels.json': {'kind': 'display_labels', 'text': cls.labels},
                      'scope.json': {'kind': 'retained_configuration', 'text': cls.scope_text}}
        cls.document = CompositionDocument(cls.files, linked_records=cls.linked,
                                           project_id='e15ced9c-7db0-4b29-b468-cff52bb49bb3')

    def role_id(self):
        return next(key for key, value in self.document.registry.items() if value == 'Library::Base::sensor')

    def test_multifile_rename_is_atomic_with_typed_documentary_bindings(self):
        before = self.document
        candidate = before.rename(self.role_id(), 'detector', expected_source_sha256=before.revision)
        self.assertEqual(candidate.files['types/library.sysml'],
                         self.files['types/library.sysml'].replace('sensor [2]', 'detector [2]'))
        self.assertEqual(candidate.files['context.sysml'], self.files['context.sysml'])
        self.assertIn('"native_name": "Library::Base::detector"', candidate.files['notes/metadata.sysml'])
        self.assertIn('"description": "Library::Base::sensor"', candidate.files['notes/metadata.sysml'])
        self.assertIn('doc /* Library::Base::sensor */', candidate.files['notes/metadata.sysml'])
        self.assertEqual(candidate.linked_records['view.labels.json']['text'],
                         self.labels.replace('"element" : "Library::Base::sensor"',
                                             '"element" : "Library::Base::detector"'))
        self.assertEqual(candidate.registry[self.role_id()], 'Library::Base::detector')
        self.assertEqual(before.files, self.files)
        self.assertEqual(before.linked_records, self.linked)

    def test_retained_scope_never_silently_changes_or_passes_after_rename(self):
        before = self.document
        self.assertEqual(before.configuration_reviews[0]['report']['status'], 'pass')
        candidate = before.rename(self.role_id(), 'detector', expected_source_sha256=before.revision)
        self.assertEqual(candidate.linked_records['scope.json']['text'], self.scope_text)
        self.assertNotEqual(candidate.configuration_reviews[0]['report']['status'], 'pass')
        item = candidate.reconciliation[0]
        self.assertEqual(item['status'], 'reconciliation_required')
        self.assertEqual(item['retained_sha256'], sha256(self.scope_text.encode()).hexdigest())
        self.assertEqual(item['changes'][0]['path'], ['selected_roles', 'SensorRole', 'native_name'])
        # Reopening derives the unresolved result again from the exact retained scope.
        restored = CompositionDocument(candidate.files, registry=candidate.registry,
                                       linked_records=candidate.linked_records, project_id=candidate.project_id)
        self.assertNotEqual(restored.configuration_reviews[0]['report']['status'], 'pass')

    def test_source_location_maps_back_to_original_file_and_line(self):
        role = next(row for row in self.document.inspect()['elements'] if row['element_id'] == self.role_id())
        location = role['source_location']
        self.assertEqual(location['file'], 'types/library.sysml')
        self.assertEqual(location['line'], 4)
        snippet = self.files[location['file']][location['offset']:location['offset']+location['length']]
        self.assertEqual(snippet, 'part <SENSOR> sensor [2] : Sensor;')

    def test_bundle_cli_matches_library_and_returns_retained_scope_reconciliation(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            directory = Path(directory)
            bundle = directory / 'bundle.json'
            bundle.write_text(json.dumps({'version': 'cse-composition-bundle-1', 'models': self.files,
                                          'linked_records': self.linked}))
            run = subprocess.run([sys.executable, str(ROOT/'scripts/composition_edit.py'), 'rename',
                                  '--bundle', str(bundle), '--project-id', self.document.project_id,
                                  '--element-id', self.role_id(), '--name', 'detector',
                                  '--expected-bundle-sha256', self.document.revision],
                                 cwd=directory, capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            report = json.loads(run.stdout)
            self.assertEqual(report['claim'], 'candidate_only_not_persisted')
            self.assertIn('detector [2]', report['files']['types/library.sysml'])
            self.assertEqual(report['linked_records']['scope.json']['text'], self.scope_text)
            self.assertEqual(report['reconciliation'][0]['status'], 'reconciliation_required')
            self.assertFalse((directory / 'types').exists(), 'Bundle paths must never be followed on disk')


    def test_bundle_digest_binds_names_and_retained_record_bytes(self):
        reordered = CompositionDocument(dict(reversed(list(self.files.items()))), linked_records=self.linked,
                                         project_id=self.document.project_id)
        self.assertEqual(reordered.revision, self.document.revision)
        changed = deepcopy(self.linked); changed['scope.json']['text'] += ' '
        other = CompositionDocument(self.files, linked_records=changed, project_id=self.document.project_id)
        self.assertNotEqual(other.revision, self.document.revision)
        with self.assertRaises(EditError):
            other.rename(self.role_id(), 'detector', expected_source_sha256=self.document.revision)


class MultiplicityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ('// 🛰 Keep the original UTF-16/codepoint boundary and CRLF.\r\n'
            'package Counts {\r\n part def Unit;\r\n attribute n : ScalarValues::Integer = 2;\r\n'
            ' part named [2 //* count note */] : Unit;\r\n'
            ' part ranger [1 // range note\r\n ..4] : Unit;\r\n'
            ' part expression [Counts::n //* reference note */ ..n] : Unit;\r\n'
            ' part unlimited [1..*] : Unit;\r\n part \'quoted name\' : Unit;\r\n'
            ' part def Base { part role [2] : Unit; }\r\n'
            ' part def Derived :> Base { part :>> role : Unit; }\r\n}\r\n')
        cls.document = CompositionDocument({'counts.sysml': cls.source, 'notes.sysml': 'package Notes { doc /* Keep counts 2 and 4. */ }'})

    def change(self, name, lower, upper, document=None):
        document = document or self.document
        identity = next(k for k, value in document.registry.items() if value == name)
        return document.set_multiplicity(identity, lower, upper, expected_source_sha256=document.revision)

    def test_exact_range_optional_and_suppressed_preserve_trivia_and_identity(self):
        for lower, upper in [(3, 3), (0, 1), (0, 0)]:
            candidate = self.change('Counts::named', lower, upper)
            spelling = str(lower) if lower == upper else f'{lower}..{upper}'
            self.assertEqual(candidate.files['counts.sysml'], self.source.replace('[2 //* count note */]', f'[{spelling} //* count note */]'))
            self.assertEqual(candidate.files['notes.sysml'], self.document.files['notes.sysml'])
            self.assertEqual(candidate.registry, self.document.registry)
        candidate = self.change('Counts::ranger', 2, 2)
        self.assertEqual(candidate.files['counts.sysml'], self.source.replace('[1 // range note\r\n ..4]', '[2 // range note\r\n ..2]'))

    def test_replacing_expression_or_infinity_removes_only_bound_references(self):
        candidate = self.change('Counts::expression', 1, 3)
        self.assertEqual(candidate.files['counts.sysml'], self.source.replace('[Counts::n //* reference note */ ..n]', '[1 //* reference note */ ..3]'))
        candidate = self.change('Counts::unlimited', 1, 2_147_483_647)
        self.assertEqual(candidate.files['counts.sysml'], self.source.replace('[1..*]', '[1..2147483647]'))

    def test_implicit_quoted_and_unnamed_inherited_override_are_local(self):
        candidate = self.change("Counts::'quoted name'", 0, 0)
        self.assertEqual(candidate.files['counts.sysml'], self.source.replace("part 'quoted name' :", "part 'quoted name' [0] :"))
        candidate = self.change('Counts::Derived::role', 2, 2)
        self.assertEqual(candidate.files['counts.sysml'], self.source.replace('part :>> role', 'part [2] :>> role'))
        self.assertEqual(candidate.registry, self.document.registry)

    def test_short_only_override_keeps_the_existing_import_identity_gap_explicit(self):
        # The native declaration is accepted, but has no qualified-name key in
        # the current registry contract. Do not fabricate one or omit the part.
        source=self.source.replace('part :>> role', 'part <OVERRIDE> :>> role')
        from verifier.composition_edit import parse
        parsed=parse(source)
        self.assertTrue(any(row.get('id')=='OVERRIDE' and row.get('qualified_name') is None for row in parsed['parts']))
        with self.assertRaises(EditError) as error:
            CompositionDocument({'counts.sysml':source})
        self.assertEqual(error.exception.code,'identity')

    def test_definition_unknown_stale_and_invalid_bounds_refuse(self):
        role = next(k for k,v in self.document.registry.items() if v == 'Counts::named')
        definition = next(k for k,v in self.document.registry.items() if v == 'Counts::Unit')
        for lower, upper in [(True, 2), (1, False), (1.0, 2), ('1', 2), (None, 2), (-1, 1), (2, 1), (0, 2_147_483_648)]:
            with self.subTest(lower=lower,upper=upper), self.assertRaises(EditError) as error:
                self.document.set_multiplicity(role, lower, upper, expected_source_sha256=self.document.revision)
            self.assertEqual(error.exception.code, 'multiplicity')
        for identity, revision, expected in [(definition, self.document.revision, 'element_kind'), ('missing', self.document.revision, 'identity'), (role, 'stale', 'stale_revision')]:
            with self.assertRaises(EditError) as error:
                self.document.set_multiplicity(identity, 1, 2, expected_source_sha256=revision)
            self.assertEqual(error.exception.code, expected)

    def test_configuration_scope_bytes_stay_fixed_and_status_is_recomputed(self):
        linked = {'scope.json': {'kind': 'retained_configuration', 'text': json.dumps(SCOPE, indent=2)+'\n'}}
        document = CompositionDocument(FILES, linked_records=linked)
        self.assertEqual(document.configuration_reviews[0]['report']['status'], 'pass')
        for lower, upper, status in [(0, 1, 'unknown'), (0, 0, 'fail'), (3, 3, 'pass')]:
            candidate = self.change('Library::Base::sensor', lower, upper, document)
            self.assertEqual(candidate.linked_records, linked)
            self.assertEqual(candidate.configuration_reviews[0]['report']['status'], status)

    def test_unadapted_computational_document_is_not_silently_bypassed(self):
        document = CompositionDocument('package Unknown { part role; doc cseUnknown /* CSE-UNKNOWN/1.0\n{} */ }')
        with self.assertRaises(EditError) as error:
            self.change('Unknown::role', 1, 2, document)
        self.assertEqual(error.exception.code, 'linked_records')

    def test_native_maximum_and_candidate_cli_preserve_the_explicit_bundle(self):
        expected=self.change('Counts::named',2147483647,2147483647)
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as name:
            bundle=Path(name)/'bundle.json'
            bundle.write_text(json.dumps({'version':'cse-composition-bundle-1','models':self.document.files,'linked_records':{}}))
            identity=next(k for k,v in self.document.registry.items() if v=='Counts::named')
            run=subprocess.run([sys.executable,str(ROOT/'scripts/composition_edit.py'),'set-multiplicity',
                '--bundle',str(bundle),'--project-id',self.document.project_id,'--element-id',identity,
                '--lower','2147483647','--upper','2147483647','--expected-bundle-sha256',self.document.revision],
                cwd=name,capture_output=True,text=True,timeout=60)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            report=json.loads(run.stdout)
            self.assertEqual(report['claim'],'candidate_only_not_persisted')
            self.assertEqual(report['files'],expected.files)
            self.assertEqual(report['registry'],self.document.registry)

    def test_native_coordinates_serialize_identically_across_parser_processes(self):
        from verifier.composition_edit import parse
        original=json.dumps(self.document.parsed,ensure_ascii=False)
        for _ in range(2):
            self.assertEqual(json.dumps(parse(self.document.source),ensure_ascii=False),original)


class RecordSafetyTests(unittest.TestCase):
    def mapped(self, value):
        return value.replace('Library::Base::sensor', 'Library::Base::detector') if value.startswith('Library::Base::sensor') else value

    def test_json_strings_are_edited_by_typed_path_not_prose_or_dictionary_key(self):
        text = '{"version":1,"view":"PC","title":"Library::Base::sensor", "labels":[' \
               '{"element":"Library::Base::sensor", "text":"Library::Base::sensor"}]}'
        rewritten, findings = rebind_json(text, 'display_labels', self.mapped)
        self.assertEqual(rewritten, text.replace('"element":"Library::Base::sensor"',
                                                '"element":"Library::Base::detector"'))
        self.assertEqual(len(findings), 1)

    def test_duplicate_keys_nonfinite_and_unknown_records_cannot_be_migrated(self):
        for text, kind in [('{"version":1,"version":1}', 'display_labels'),
                           ('{"x":NaN}', 'views'), ('{"x":1e999}', 'views'), ('{}', 'unknown')]:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                rebind_json(text, kind, self.mapped)

    def test_paths_are_not_disk_access_and_ambiguous_paths_refuse(self):
        for name in ['../escape.sysml', '/private/model.sysml', 'a//model.sysml', 'a/./model.sysml', 'C:\\model.sysml']:
            with self.subTest(name=name), self.assertRaises(EditError):
                CompositionDocument({name: 'package Safe;'}, project_id='e15ced9c-7db0-4b29-b468-cff52bb49bb3')



class RecordTests(unittest.TestCase):
    def mapped(self, text):
        return text.replace('Library::Base::sensor', 'Library::Base::detector')

    def test_json_escaped_binding_and_prose_have_distinct_ownership(self):
        source = '{"version":1,"view":"PC","title":"Library::Base::sensor", "labels":[' \
                 '{"element":"Library\\u003a\\u003aBase::sensor","text":"Library::Base::sensor"}]}'
        result, changes = rebind_json(source, 'display_labels', self.mapped)
        self.assertEqual(len(changes), 1)
        expected = source.replace('"Library\\u003a\\u003aBase::sensor"', '"Library::Base::detector"')
        self.assertEqual(result, expected)

    def test_duplicate_keys_and_unknown_record_kind_refuse(self):
        for text, kind in [('{"version":1,"version":1}', 'display_labels'), ('{}', 'unknown')]:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                rebind_json(text, kind, self.mapped)

    def test_unknown_view_binding_cannot_silently_remain_stale(self):
        record = {'views': [{'id': 'PC', 'kind': 'physical_composition', 'mode': 'usages',
                             'nodes': [], 'unknown_binding': 'Library::Base::sensor'}]}
        with self.assertRaises(ValueError):
            rebind_json(json.dumps(record), 'views', self.mapped)

    def test_all_existing_view_binding_paths_preserve_narrative_and_ids(self):
        body = '\nCSE-VIEWS/1.1\n'+json.dumps({'views':[
            {'id':'PC','kind':'physical_composition','mode':'usages','nodes':[
                {'id':'ROLE','element':'Library::Base::sensor','parent':None,'level':0,'edge':None}]},
            {'id':'SEQ','kind':'sequence','participants':[{'id':'P','element':'Library::Base::sensor'}],
             'exchanges':[{'id':'E','from':'P','to':'P','message':'Library::Base::sensor'}]},
        ]},indent=2)+'\n'
        result, findings = rebind_document(body, 'cseViews', self.mapped)
        self.assertEqual(len(findings), 2)
        record = json.loads(result.split('CSE-VIEWS/1.1',1)[1])
        self.assertEqual(record['views'][0]['nodes'][0]['element'], 'Library::Base::detector')
        self.assertEqual(record['views'][1]['exchanges'][0]['message'], 'Library::Base::sensor')


if __name__ == '__main__':
    unittest.main()
