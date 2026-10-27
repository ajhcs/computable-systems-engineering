"""Controls for retained C/D/E contracts and explicit rights holds."""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_ecosystem_references import BASE, validate
import check_ecosystem_references as checker
from cases import require_case
from presentation_check import validate_svg
from source_check import validate_source
from reference_media import inspect_svg


class EcosystemReferenceTests(unittest.TestCase):
    def load(self, key):
        return [key, json.loads((BASE / 'native' / (key + '.facts.json')).read_text()),
                json.loads((BASE / 'rendered' / (key + '.view.json')).read_text()),
                ET.parse(BASE / 'rendered' / (key + '.svg')).getroot(),
                json.loads((BASE / 'source/display-aliases.json').read_text())]

    def test_three_retained_scopes_have_honest_check_status(self):
        result = validate()
        self.assertEqual(result['views'], 3)
        self.assertEqual([v['nodes'] for v in result['presentations']], [11, 11, 6])
        self.assertEqual(result['fresh_browser_render'], 'not_run')
        self.assertEqual(result['fresh_parser_run'], 'not_run')

    def test_held_and_unknown_cases_fail_explicitly(self):
        for key in ('A-bank', 'B-healthcare', 'unknown'):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'held|Unsupported'):
                require_case(key)

    def copied(self):
        parent = ROOT / '.tmp'
        parent.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(temp.cleanup)
        dest = Path(temp.name) / 'reference'
        shutil.copytree(BASE, dest)
        return dest

    def test_missing_required_retained_case_is_not_skipped(self):
        dest = self.copied()
        (dest / 'rendered/D-smart-grid.png').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing required'):
            validate(dest)

    def test_held_payload_cannot_rejoin_silently(self):
        dest = self.copied()
        (dest / 'source/A-ledger.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Held case payload'):
            validate(dest)

    def test_wrong_visible_native_identity_rejected(self):
        case = self.load('C-maintenance')
        next(e for e in case[3].iter() if e.get('data-node')).set('data-native-id', 'wrong')
        with self.assertRaises(ValueError):
            validate_svg(*case)

    def test_allocation_direction_reversed_rejected(self):
        case = self.load('E-ape-allocation')
        next(e for e in case[3].iter() if e.tag.endswith('text') and e.get('data-label-owner', '').startswith('EA') and e.text == '→').text = '←'
        with self.assertRaises(ValueError):
            validate_svg(*case)

    def test_arrow_in_wrong_actual_cell_rejected(self):
        case = self.load('E-ape-allocation')
        arrow = next(e for e in case[3].iter() if e.tag.endswith('text') and e.get('data-label-owner', '').startswith('EA'))
        arrow.set('x', str(float(arrow.get('x')) + 175))
        with self.assertRaises(ValueError):
            validate_svg(*case)

    def test_readable_alias_lost_rejected(self):
        case = self.load('E-ape-allocation')
        next(e for e in case[3].iter() if e.tag.endswith('text') and e.text == 'Mirror control interface').text = 'Unrelated interface'
        with self.assertRaises(ValueError):
            validate_svg(*case)

    def test_undirected_electrical_link_cannot_gain_arrow(self):
        case = self.load('D-smart-grid')
        next(e for e in case[3].iter() if e.get('data-edge')).set('marker-end', 'url(#arrow)')
        with self.assertRaises(ValueError):
            validate_svg(*case)

    def test_empty_matrix_rejected(self):
        case = self.load('D-smart-grid')
        for element in case[3].iter():
            element.attrib.pop('data-relation', None)
        with self.assertRaises(ValueError):
            validate_svg(*case)

    def mutated_native(self, change):
        dest = self.copied()
        path = dest / 'native/C-maintenance.facts.json'
        facts = json.loads(path.read_text())
        change(facts)
        path.write_text(json.dumps(facts))
        with self.assertRaises(ValueError):
            validate_source(dest)

    def test_stale_native_model_binding_rejected(self):
        self.mutated_native(lambda facts: facts.update(source_sha256='0' * 64))

    def test_hour_quantity_cannot_be_reinterpreted_as_seconds(self):
        def change(facts):
            attr = next(e for e in facts['elements'] if e['kind'] == 'AttributeUsage' and e.get('value'))
            attr['value'][0]['arguments'][1]['referent']['qualified'] = 'SI::second'
        self.mutated_native(change)

    def test_duration_cannot_change_without_correspondence_failure(self):
        def change(facts):
            attr = next(e for e in facts['elements'] if e['kind'] == 'AttributeUsage' and e.get('value') and (e['qualified'] or '').endswith('::duration'))
            attr['value'][0]['arguments'][0]['value'] = 9
        self.mutated_native(change)

    def test_nonfont_embedded_payload_rejected(self):
        dest = self.copied()
        path = dest / 'rendered/C-maintenance.svg'
        path.write_text(path.read_text().replace('</svg>', '<image href="data:image/png;base64,aGVsbG8="/></svg>'))
        with self.assertRaisesRegex(ValueError, 'embedded data URI'):
            inspect_svg(path, dest / 'fonts/font-source.json', dest / 'fonts/LICENSE.txt', dest / 'fonts')

    def receipt_cli(self, path, curated, validation=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        result = {'status': 'pass', 'presentations': []}
        with mock.patch.object(checker, 'BASE', curated), mock.patch.object(checker, 'validate', side_effect=validation, return_value=result), mock.patch.object(sys, 'argv', ['check_ecosystem_references.py', '--receipt', str(path)]), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = checker.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_receipt_preserves_existing_output(self):
        curated = self.copied()
        receipt = curated.parent / 'existing-receipt.json'
        receipt.write_bytes(b'existing evidence\x00\xff')
        self.assertEqual(self.receipt_cli(receipt, curated)[0], 1)
        self.assertEqual(receipt.read_bytes(), b'existing evidence\x00\xff')

    def test_receipt_preserves_live_final_symlink_and_target(self):
        curated = self.copied()
        target, receipt = curated.parent / 'evidence.json', curated.parent / 'receipt-link.json'
        target.write_text('existing evidence')
        receipt.symlink_to(target.name)
        self.assertEqual(self.receipt_cli(receipt, curated)[0], 1)
        self.assertTrue(receipt.is_symlink())
        self.assertEqual(receipt.readlink(), Path(target.name))
        self.assertEqual(target.read_text(), 'existing evidence')

    def test_receipt_preserves_dangling_final_symlink(self):
        curated = self.copied()
        target, receipt = curated.parent / 'absent.json', curated.parent / 'dangling-receipt.json'
        receipt.symlink_to(target.name)
        self.assertEqual(self.receipt_cli(receipt, curated)[0], 1)
        self.assertTrue(receipt.is_symlink())
        self.assertEqual(receipt.readlink(), Path(target.name))
        self.assertFalse(target.exists())

    def test_receipt_parent_alias_cannot_write_curated_pack(self):
        curated = self.copied()
        alias = curated.parent / 'curated-alias'
        alias.symlink_to(curated, target_is_directory=True)
        self.assertEqual(self.receipt_cli(alias / 'new-receipt.json', curated)[0], 1)
        self.assertFalse((curated / 'new-receipt.json').exists())

    def test_receipt_preserves_output_created_during_validation(self):
        curated = self.copied()
        receipt = curated.parent / 'concurrent-receipt.json'
        def validation():
            receipt.write_text('another writer completed this evidence')
            return {'status': 'pass', 'presentations': []}
        self.assertEqual(self.receipt_cli(receipt, curated, validation)[0], 1)
        self.assertEqual(receipt.read_text(), 'another writer completed this evidence')

    def test_receipt_creates_new_external_file(self):
        curated = self.copied()
        receipt = curated.parent / 'new-receipt.json'
        self.assertEqual(self.receipt_cli(receipt, curated)[0], 0)
        self.assertEqual(json.loads(receipt.read_text())['status'], 'pass')

    def test_transformed_allocation_arrow_or_ancestor_rejected(self):
        for mode in ('arrow', 'ancestor', 'inline_css', 'stylesheet'):
            with self.subTest(mode=mode):
                case = self.load('E-ape-allocation')
                arrow = next(e for e in case[3].iter() if e.tag.endswith('text') and e.get('data-label-owner') == 'EA04' and e.get('x') == '650.5' and e.get('y') == '401')
                if mode == 'arrow':
                    arrow.set('transform', 'translate(175,0)')
                elif mode == 'ancestor':
                    next(e for e in case[3] if e.tag.endswith('g')).set('transform', 'translate(175,0)')
                elif mode == 'inline_css':
                    arrow.set('style', 'transform: translate(175px, 0px)')
                else:
                    style = ET.SubElement(case[3], '{http://www.w3.org/2000/svg}style')
                    style.text = '[data-label-owner="EA04"] { transform: translate(175px, 0px); }'
                with self.assertRaisesRegex(ValueError, 'transform'):
                    validate_svg(*case)

    def test_parse_success_requires_literal_boolean_false(self):
        for value in (None, 0, '', [], {}):
            with self.subTest(value=value):
                self.mutated_native(lambda facts: facts.update(parse_has_errors=value))

    def test_missing_parse_success_flag_is_rejected(self):
        self.mutated_native(lambda facts: facts.pop('parse_has_errors'))

    def test_renderer_loader_rejects_unknown_parser_status_without_rendering(self):
        dest = self.copied()
        path = dest / 'native/C-maintenance.facts.json'
        facts = json.loads(path.read_text())
        facts['parse_has_errors'] = None
        path.write_text(json.dumps(facts))
        spec = importlib.util.spec_from_file_location('ecosystem_renderer_check', BASE / 'tools/render.py')
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        with mock.patch.object(renderer, 'R', dest), self.assertRaisesRegex(ValueError, 'invalid native facts'):
            renderer.load('C-maintenance')


if __name__ == '__main__':
    unittest.main()
