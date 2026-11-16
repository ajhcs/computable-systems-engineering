"""Native source-edit controls, including Unicode, references and identity."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError, codepoint_index


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

    def test_documentary_binding_is_not_silently_lost(self):
        source = 'package Documentary { part def Sensor { doc /* Sensor narrative */ } }'
        document = CompositionDocument(source)
        with self.assertRaises(EditError) as error:
            document.rename(next(iter(document.registry)), 'Detector',
                            expected_source_sha256=document.revision)
        self.assertEqual(error.exception.code, 'linked_records')


if __name__ == '__main__':
    unittest.main()
