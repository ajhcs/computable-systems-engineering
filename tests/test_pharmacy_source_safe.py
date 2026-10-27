"""Public-package consistency and mutation checks; no original source required."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_pharmacy_source_safe import (
    BASE, check_bundle, check_file_names, check_view,
)


def inputs(view='HFFillSystem'):
    folder = BASE / view
    return {
        'ledger': json.loads((folder / 'semantic-ledger.json').read_text()),
        'facts': json.loads((folder / 'native.facts.json').read_text()),
        'model': (folder / 'model.sysml').read_text(),
        'supplementary': (folder / 'supplementary-full-direct-properties.sysml').read_bytes(),
        'svg': (folder / 'candidate.svg').read_text(),
        'drawio': (folder / 'candidate.drawio').read_text(),
        'puml': (folder / 'native.puml').read_text(),
    }


class PharmacySourceSafeTests(unittest.TestCase):
    def assert_rejected(self, values, message, view='HFFillSystem'):
        with self.assertRaisesRegex(ValueError, message):
            check_view(view, **values)

    def test_released_package_has_19_roles_with_two_references(self):
        result = check_bundle()
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(sum(row['selected_roles'] for row in result['views']), 19)
        self.assertEqual(sum(row['owned_parts'] for row in result['views']), 17)
        self.assertEqual(sum(row['referenced_resources'] for row in result['views']), 2)
        self.assertEqual(result['original_source_verification'], 'not_run')
        self.assertEqual(result['fresh_sysml_parse'], 'not_run')
        self.assertEqual(result['rendered_image_fidelity'], 'not_run')

    def test_reference_resource_cannot_become_native_owned_part(self):
        values = inputs()
        next(p for p in values['facts']['parts'] if p['name'] == 'VTS')['composite'] = True
        self.assert_rejected(values, 'native type/ownership/cardinality')

    def test_native_feature_cannot_move_to_another_owner(self):
        values = inputs()
        values['facts']['parts'][0]['owner_id'] = 'unrelated-owner'
        self.assert_rejected(values, 'native owner/identity')

    def test_native_type_cannot_silently_change(self):
        values = inputs()
        values['facts']['parts'][0]['definitions'][0]['name'] = 'DifferentSystem'
        self.assert_rejected(values, 'native type/ownership/cardinality')

    def test_selected_native_element_must_be_part_definition(self):
        values = inputs()
        values['facts']['selected']['kind'] = 'ActionDefinition'
        self.assert_rejected(values, 'native selected kind')

    def test_native_role_must_be_part_usage(self):
        values = inputs()
        values['facts']['parts'][0]['kind'] = 'ActionUsage'
        self.assert_rejected(values, 'native part kind')

    def test_native_role_type_must_be_part_definition(self):
        values = inputs()
        values['facts']['parts'][0]['definitions'][0]['kind'] = 'ItemDefinition'
        self.assert_rejected(values, 'native definition kind')

    def test_optional_role_cannot_become_required_in_model(self):
        values = inputs()
        values['model'] = values['model'].replace("::'AFrame' [0..*]", "::'AFrame' [1..*]")
        self.assert_rejected(values, 'model/ledger roles differ')

    def test_dispensing_finger_lower_bound_is_preserved(self):
        values = inputs('HSFillSystem')
        values['model'] = values['model'].replace("::'HSDispenseFinger' [1..*]", "::'HSDispenseFinger' [0..*]")
        self.assert_rejected(values, 'model/ledger roles differ', 'HSFillSystem')

    def test_ledger_cardinality_change_cannot_redefine_the_check(self):
        values = inputs()
        next(p for p in values['ledger']['properties'] if p['derived_name'] == 'autoUofU')['lower'] = 1
        self.assert_rejected(values, 'frozen cardinality')

    def test_unsupported_extra_model_construct_cannot_pass(self):
        values = inputs()
        values['model'] = values['model'].replace("part def 'HFFillSystem' {", "part def 'HFFillSystem' {\npublic attribute invented : Boolean;")
        self.assert_rejected(values, 'unsupported model body')

    def test_missing_or_duplicate_native_role_cannot_pass(self):
        values = inputs()
        values['facts']['parts'].pop()
        self.assert_rejected(values, 'native role set')
        values = inputs()
        values['facts']['parts'].append(deepcopy(values['facts']['parts'][0]))
        self.assert_rejected(values, 'duplicate name')

    def test_stale_supplementary_file_cannot_keep_old_receipt(self):
        values = inputs()
        values['supplementary'] += b'\n// changed derivative\n'
        self.assert_rejected(values, 'supplementary hash/count')

    def test_visible_cardinality_cannot_disagree_with_graph_metadata(self):
        values = inputs()
        values['svg'] = values['svg'].replace('Count: 0 or more', 'Count: 1', 1)
        self.assert_rejected(values, 'visible SVG role labels')

    def test_unnamed_owned_svg_role_cannot_claim_reference(self):
        values = inputs()
        root = ET.fromstring(values['svg'])
        card = next(e for e in root.iter() if e.get('id') == 'role-toteConveyor')
        texts = [e for e in card if e.tag.endswith('}text')]
        self.assertEqual(texts[-1].text, 'Unnamed source role; derived alias: toteConveyor')
        texts[-1].text = 'Referenced resource'
        values['svg'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'contradictory SVG relationship label')

    def test_unnamed_svg_alias_wording_must_remain_explicit(self):
        values = inputs()
        values['svg'] = values['svg'].replace(
            'Unnamed source role; derived alias: toteConveyor', 'Owned part')
        self.assert_rejected(values, 'SVG unnamed alias wording')

    def test_drawio_reference_label_cannot_claim_owned_part(self):
        values = inputs()
        root = ET.fromstring(values['drawio'])
        card = next(e for e in root.iter('object') if e.get('relationship') == 'reference')
        card.set('label', card.get('label') + '\nOwned part')
        values['drawio'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'contradictory draw.io relationship label')

    def test_svg_reference_cannot_add_owned_label_alongside_correct_label(self):
        values = inputs()
        root = ET.fromstring(values['svg'])
        card = next(e for e in root.iter() if e.get('id') == 'role-VTS')
        ET.SubElement(card, '{http://www.w3.org/2000/svg}text').text = 'Owned part'
        values['svg'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'contradictory SVG relationship label')

    def test_drawio_unnamed_alias_cannot_silently_change(self):
        values = inputs()
        values['drawio'] = values['drawio'].replace('Derived alias: toteConveyor', 'Derived alias: invented')
        self.assert_rejected(values, 'draw.io unnamed alias wording')

    def test_missing_svg_card_and_changed_identity_cannot_pass(self):
        values = inputs()
        root = ET.fromstring(values['svg'])
        for parent in root.iter():
            card = next((e for e in parent if e.get('data-relationship')), None)
            if card is not None:
                parent.remove(card)
                break
        values['svg'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'SVG role set')
        values = inputs()
        values['svg'] = values['svg'].replace('data-native-id="' + values['facts']['parts'][0]['id'], 'data-native-id="wrong-id')
        self.assert_rejected(values, 'SVG data-native-id')

    def test_reference_card_cannot_move_inside_owned_boundary(self):
        values = inputs()
        root = ET.fromstring(values['svg'])
        boundary = next(e for e in root.iter() if e.get('id') == 'system-boundary')
        for parent in root.iter():
            card = next((e for e in parent if e.tag.endswith('}g') and
                         e.get('data-relationship') == 'reference'), None)
            if card is not None:
                parent.remove(card)
                boundary.append(card)
                break
        values['svg'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'SVG containment')

    def test_reference_svg_transform_cannot_disguise_spatial_ownership(self):
        values = inputs()
        root = ET.fromstring(values['svg'])
        card = next(e for e in root.iter() if e.get('id') == 'role-VTS')
        rect = next(e for e in card if e.tag.endswith('}rect'))
        self.assertEqual(tuple(rect.get(k) for k in ('x', 'y', 'width', 'height')),
                         ('48', '778', '510', '112'))
        card.set('transform', 'translate(0,-600)')
        values['svg'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'unsupported SVG transform')

    def test_reference_rect_inside_boundary_fails_even_without_transform(self):
        values = inputs()
        root = ET.fromstring(values['svg'])
        boundary = next(e for e in root.iter() if e.get('id') == 'system-boundary')
        outer = next(e for e in boundary if e.tag.endswith('}rect'))
        self.assertEqual(tuple(outer.get(k) for k in ('x', 'y', 'width', 'height')),
                         ('30', '20', '1080', '648'))
        card = next(e for e in root.iter() if e.get('id') == 'role-VTS')
        next(e for e in card if e.tag.endswith('}rect')).set('y', '178')
        values['svg'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'referenced SVG card overlaps owned boundary')

    def test_owned_rect_cannot_move_outside_boundary(self):
        values = inputs()
        root = ET.fromstring(values['svg'])
        card = next(e for e in root.iter() if e.get('id') == 'role-toteConveyor')
        next(e for e in card if e.tag.endswith('}rect')).set('y', '778')
        values['svg'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'owned SVG card outside boundary')

    def test_transforms_on_relevant_ancestry_or_glyphs_are_unsupported(self):
        for target in ('root', 'boundary', 'boundary-rect', 'reference-group', 'card-rect', 'card-text'):
            with self.subTest(target=target):
                values = inputs()
                root = ET.fromstring(values['svg'])
                boundary = next(e for e in root.iter() if e.get('id') == 'system-boundary')
                card = next(e for e in root.iter() if e.get('id') == 'role-VTS')
                selected = {
                    'root': root, 'boundary': boundary,
                    'reference-group': next(e for e in root.iter() if e.get('id') == 'shared-references'),
                    'boundary-rect': next(e for e in boundary if e.tag.endswith('}rect')),
                    'card-rect': next(e for e in card if e.tag.endswith('}rect')),
                    'card-text': next(e for e in card if e.tag.endswith('}text')),
                }[target]
                selected.set('transform', 'translate(0,-600)')
                values['svg'] = ET.tostring(root, encoding='unicode')
                self.assert_rejected(values, 'unsupported SVG transform')

    def test_css_geometry_is_unsupported(self):
        for stylesheet in (False, True):
            with self.subTest(stylesheet=stylesheet):
                values = inputs()
                root = ET.fromstring(values['svg'])
                if stylesheet:
                    ET.SubElement(root, '{http://www.w3.org/2000/svg}style').text = (
                        '#role-VTS {transform: translate(0,-600px)}')
                else:
                    card = next(e for e in root.iter() if e.get('id') == 'role-VTS')
                    card.set('style', 'transform: translate(0,-600px)')
                values['svg'] = ET.tostring(root, encoding='unicode')
                self.assert_rejected(values, 'unsupported SVG (?:transform|geometry stylesheet)')

    def test_drawio_cannot_place_reference_inside_owned_boundary(self):
        values = inputs()
        root = ET.fromstring(values['drawio'])
        reference = next(e for e in root.iter('object') if e.get('relationship') == 'reference')
        reference.find('mxCell').set('parent', 'system')
        values['drawio'] = ET.tostring(root, encoding='unicode')
        self.assert_rejected(values, 'draw.io containment')

    def test_native_membership_cannot_lose_ownership_glyph(self):
        values = inputs()
        values['puml'] = values['puml'].replace('E1 *-- E2', 'E1 o-- E2')
        self.assert_rejected(values, 'retained native membership endpoints/glyphs')

    def test_native_membership_cannot_move_to_a_different_role(self):
        values = inputs()
        values['puml'] = values['puml'].replace('E1 *-- E2', 'E1 *-- E3')
        self.assert_rejected(values, 'retained native membership endpoints/glyphs')

    def test_visible_drawio_count_cannot_disagree_with_metadata(self):
        values = inputs()
        values['drawio'] = values['drawio'].replace('Count: 0 or more', 'Count: 1', 1)
        self.assert_rejected(values, 'visible draw.io labels')

    def test_historical_parser_issue_cannot_be_called_consistent(self):
        values = inputs()
        values['facts']['parse_has_errors'] = True
        self.assert_rejected(values, 'historical native parse issues')

    def test_raw_xml_or_parser_receipt_cannot_enter_allowlist(self):
        names = [p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file()]
        for forbidden in ['DemoCFP/original-native-diagram-layout.xml', 'DemoCFP/parser-receipt.json']:
            with self.subTest(forbidden=forbidden), self.assertRaisesRegex(ValueError, 'allowlist'):
                check_file_names(names + [forbidden])

    def test_truncated_source_notice_cannot_pass(self):
        original = Path.read_bytes

        def truncated(path):
            data = original(path)
            return data[:-1] if path.name == 'SOURCE-LICENSE.md' else data

        with mock.patch.object(Path, 'read_bytes', truncated):
            with self.assertRaisesRegex(ValueError, 'full pinned source license notice'):
                check_bundle()


if __name__ == '__main__':
    unittest.main()
