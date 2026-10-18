"""Synthetic documentary projection, refusal, offline and native regeneration tests."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import CLASSES, JAR
from verifier.visual_projection import PresentationError, project_function_tree, render_function_tree, write_presentation

MODEL = ROOT / 'examples/sysml/views/sample-handling.sysml'


def fixture():
    nodes = [{'id': 'F0', 'element': 'Example::Process', 'level': 0, 'parent': None},
             {'id': 'F1', 'element': 'Example::Read', 'level': 1, 'parent': 'F0'},
             {'id': 'F2', 'element': 'Example::Store', 'level': 1, 'parent': 'F0'}]
    inventory = {'actions': [{'qualified_name': n['element'], 'name': name} for n, name in
                            zip(nodes, ['Process item', 'Read <tag> & "quote"', 'Store item'])], 'parts': [],
                 'documents': [{'name': 'cseViews', 'owner_kind': 'Package', 'body': ''}]}
    return nodes, inventory


def project(nodes, inventory):
    inventory['documents'][0]['body'] = 'CSE-VIEWS/1.0\n' + json.dumps({'views': [{'id': 'FT', 'kind': 'function_tree', 'nodes': nodes}]})
    return project_function_tree(inventory, 'FT')


class ProjectionTests(unittest.TestCase):
    def test_exact_identity_text_xml_and_determinism(self):
        nodes, inventory = fixture()
        expected = deepcopy(nodes)
        projection = project(nodes, inventory)
        self.assertEqual(nodes, expected)
        for n, original in zip(projection['nodes'], expected):
            self.assertEqual({k: n[k] for k in original}, original)
        svg, ledger = render_function_tree(projection)
        self.assertEqual((svg, ledger), render_function_tree(projection))
        root = ET.fromstring(svg)
        texts = [item.text for item in root.iter('{http://www.w3.org/2000/svg}text')]
        self.assertIn('Read <tag> & "quote"', texts)
        self.assertNotIn('<tag>', svg)
        self.assertNotIn('marker-end', svg)
        groups = [item for item in root.iter('{http://www.w3.org/2000/svg}g')]
        self.assertEqual([g.attrib['data-element'] for g in groups], [n['element'] for n in nodes])
        self.assertEqual(len(list(root.iter('{http://www.w3.org/2000/svg}path'))), len(nodes)-1)
        for a, b in zip(ledger['geometry'], ledger['geometry'][1:]):
            self.assertLessEqual(a['y'] + a['height'], b['y'])

    def test_parsed_svg_preserves_title_body_roles_and_square_containers(self):
        nodes, inventory = fixture()
        root = ET.fromstring(render_function_tree(project(nodes, inventory))[0])
        namespace = {'svg': 'http://www.w3.org/2000/svg'}
        title, annotation = root.findall('svg:text', namespace)
        self.assertEqual(title.attrib['font-family'], 'Inter')
        self.assertEqual(annotation.attrib['font-family'], 'Space Grotesk')
        groups = root.findall('svg:g', namespace)
        self.assertEqual(len(groups), len(nodes))
        for group in groups:
            metadata, native_label = group.findall('svg:text', namespace)
            self.assertIn('level', metadata.text)
            self.assertEqual(metadata.attrib['font-family'], 'Space Grotesk')
            self.assertEqual(native_label.attrib['font-family'], 'Space Grotesk')
            rectangle = group.find('svg:rect', namespace)
            self.assertNotIn('rx', rectangle.attrib)
            self.assertNotIn('ry', rectangle.attrib)

    def test_invalid_structure_bindings_and_requested_views_refused(self):
        for defect in ('cycle', 'orphan', 'level', 'binding', 'duplicate', 'missing', 'kind'):
            nodes, inventory = fixture()
            if defect == 'cycle':
                nodes[1]['parent'] = 'F2'; nodes[2]['parent'] = 'F1'
            elif defect == 'orphan': nodes[1]['parent'] = 'MISSING'
            elif defect == 'level': nodes[1]['level'] = 4
            elif defect == 'binding': nodes[1]['element'] = 'Absent'
            elif defect == 'duplicate': nodes.append(deepcopy(nodes[1]))
            with self.subTest(defect=defect):
                if defect in ('missing', 'kind'):
                    project(nodes, inventory)
                    if defect == 'missing': inventory['documents'] = []
                    else: inventory['documents'][0]['body'] = 'CSE-VIEWS/1.0\n' + json.dumps({'views': [{'id': 'FT', 'kind': 'unrecognized'}]})
                    with self.assertRaises(PresentationError): project_function_tree(inventory, 'FT')
                else:
                    with self.assertRaises(PresentationError): project(nodes, inventory)

    def test_render_revalidates_direct_projection_and_bounds(self):
        nodes, inventory = fixture()
        projection = project(nodes, inventory)
        projection['nodes'][1]['parent'] = 'Absent'
        with self.assertRaises(PresentationError): render_function_tree(projection)
        projection = project(nodes, inventory)
        for width in (0, float('nan'), True, 9000):
            with self.subTest(width=width), self.assertRaises(ValueError):
                render_function_tree(projection, target_width=width)
        projection['nodes'][0]['text'] = 'Unsupported \u2603'
        with self.assertRaises(ValueError): render_function_tree(projection)

    def test_failed_native_acquisition_creates_no_output(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as temp:
            output = Path(temp) / 'output'
            for status in ('fail', 'unknown', 'error', 'unsupported'):
                report = {'status': status, 'findings': [{'code': 'input_or_parser', 'detail': 'SysML pilot not installed'}]}
                with patch('verifier.visual_projection.check_sysml', return_value=report):
                    self.assertEqual(write_presentation([MODEL], output, view_id='FT'), report)
                    self.assertFalse(output.exists())


@unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(), 'Pinned native parser unavailable')
class NativePresentationTests(unittest.TestCase):
    def test_native_offline_hashes_sources_exclusive_output_and_regeneration(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as temp:
            temp = Path(temp)
            source = temp / 'model.sysml'
            source.write_bytes(MODEL.read_bytes())
            before = source.read_bytes()
            report = write_presentation(source, temp / 'one', view_id='FT')
            self.assertEqual(report['status'], 'pass', report)
            self.assertEqual(source.read_bytes(), before)
            write_presentation(source, temp / 'two', view_id='FT')
            for file in (temp / 'one').rglob('*'):
                if file.is_file(): self.assertEqual(file.read_bytes(), (temp / 'two' / file.relative_to(temp / 'one')).read_bytes())
            manifest = json.loads((temp / 'one/manifest.json').read_text())
            for name, digest in manifest['files'].items():
                self.assertEqual(sha256((temp / 'one' / name).read_bytes()).hexdigest(), digest)
            self.assertEqual((temp / 'one/sources/model-1.sysml').read_bytes(), before)
            svg = (temp / 'one/view.svg').read_text()
            html = (temp / 'one/index.html').read_text()
            self.assertIn(svg, html)
            self.assertIn('data:font/', html)
            self.assertNotIn('<script', html)
            self.assertNotRegex(html, r'''url\([\"']?https?://''')
            with self.assertRaises(FileExistsError): write_presentation(source, temp / 'one', view_id='FT')
            source.write_text(source.read_text().replace('CaptureSample', 'CollectSample'))
            changed = write_presentation(source, temp / 'three', view_id='FT')
            self.assertEqual(changed['status'], 'pass', changed)
            self.assertNotEqual(report['manifest']['model_sha256'], changed['manifest']['model_sha256'])
            self.assertIn('CollectSample', (temp / 'three/view.svg').read_text())
            source.write_text(source.read_text().replace('"parent": "F0"', '"parent": "Absent"'))
            failed = write_presentation(source, temp / 'bad', view_id='FT')
            self.assertNotEqual(failed['status'], 'pass')
            self.assertFalse((temp / 'bad').exists())

    def test_native_cli_accepts_nondefault_profile_and_preserves_provisional_status(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as temp:
            temp = Path(temp)
            profile = json.loads((ROOT / 'assets/diagram-style/profile.json').read_text())
            profile['numeric_proposal']['body_size'] = 23
            profile_path = temp / 'profile.json'
            profile_path.write_text(json.dumps(profile))
            output = temp / 'custom-profile'
            result = subprocess.run([
                sys.executable, str(ROOT / 'scripts/sysml_present.py'), str(MODEL),
                '--view', 'FT', '--output', str(output), '--profile', str(profile_path),
                '--body', 'tint'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'pass')
            presentation = json.loads((output / 'presentation.json').read_text())
            self.assertEqual(presentation['style']['body_size'], 23)
            self.assertEqual(presentation['style']['body_status'], 'provisional')
            self.assertEqual(presentation['body'], 'tint')
            tree = ET.parse(output / 'view.svg')
            labels = tree.findall('.//{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}text')
            self.assertTrue(labels)
            self.assertTrue(all(label.attrib['font-size'] == '23' for label in labels))
            self.assertEqual(profile_path.read_text(), json.dumps(profile))

    def test_cli_invalid_view_and_missing_parser_diagnostics(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as temp:
            output = Path(temp) / 'invalid'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/sysml_present.py'), str(MODEL), '--view', 'Missing', '--output', str(output)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotEqual(json.loads(result.stdout)['status'], 'pass')
            self.assertFalse(output.exists())
            with patch('verifier.sysml.JAR', Path(temp) / 'absent.jar'):
                report = write_presentation(MODEL, output, view_id='FT')
            self.assertEqual(report['status'], 'error')
            self.assertIn('not installed', report['findings'][0]['detail'])
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
