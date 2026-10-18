"""Synthetic documentary projection, refusal, offline and native regeneration tests."""
from copy import deepcopy
from hashlib import sha256
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.visual_style import load_profile
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
        texts = [''.join(item.itertext()) for item in root.iter('{http://www.w3.org/2000/svg}text')]
        self.assertIn('Read <tag> & "quote"', texts)
        self.assertNotIn('<tag>', svg)
        self.assertNotIn('marker-end', svg)
        groups = [item for item in root.iter('{http://www.w3.org/2000/svg}g')]
        self.assertEqual([g.attrib['data-element'] for g in groups], [n['element'] for n in nodes])
        self.assertEqual(len(root.findall("{http://www.w3.org/2000/svg}path[@data-child]")), len(nodes)-1)
        for a, b in zip(ledger['geometry'], ledger['geometry'][1:]):
            self.assertTrue(a['y'] + a['height'] <= b['y'] or a['x'] + a['width'] <= b['x'] or b['x'] + b['width'] <= a['x'])

    def test_parsed_svg_preserves_title_body_roles_and_square_containers(self):
        nodes, inventory = fixture()
        root = ET.fromstring(render_function_tree(project(nodes, inventory), show_ids=True)[0])
        namespace = {'svg': 'http://www.w3.org/2000/svg'}
        title = root.find("svg:text[@data-role='title']",namespace)
        annotation = root.find("svg:text[@data-role='subtitle']",namespace)
        self.assertEqual(title.attrib['font-family'], 'Inter')
        self.assertEqual(annotation.attrib['font-family'], 'Space Grotesk')
        groups = root.findall('svg:g', namespace)
        self.assertEqual(len(groups), len(nodes))
        for group in groups:
            native_label = group.find("svg:text[@data-role='label']", namespace)
            metadata = group.find("svg:text[@data-role='metadata']", namespace)
            self.assertIn('level', metadata.text)
            self.assertEqual(metadata.attrib['font-family'], 'Space Grotesk')
            self.assertEqual(native_label.attrib['font-family'], 'Space Grotesk')
            rectangle = group.find('svg:rect', namespace)
            self.assertNotIn('rx', rectangle.attrib)
            self.assertNotIn('ry', rectangle.attrib)

    def test_content_fit_wrapping_and_attached_documentary_routes(self):
        nodes, inventory = fixture()
        projection = project(nodes, inventory)
        ns = {'svg':'http://www.w3.org/2000/svg'}
        for size in (20, 22, 24):
            profile = load_profile()
            profile['numeric_proposal']['body_size'] = size
            svg, ledger = render_function_tree(projection, profile=profile, show_ids=True, target_width=1600)
            tree = ET.fromstring(svg)
            boxes = {g.attrib['data-id']:g.find('svg:rect',ns).attrib for g in tree.findall('svg:g',ns)}
            self.assertEqual({(e['parent'],e['child']) for e in ledger['edges']}, {('F0','F1'),('F0','F2')})
            for group in tree.findall('svg:g',ns):
                self.assertLess(float(group.find('svg:rect',ns).attrib['width']), 450)
                label=group.find("svg:text[@data-role='label']",ns)
                self.assertEqual(float(label.attrib['font-size']),size)
            for edge in ledger['edges']:
                parent,child=boxes[edge['parent']],boxes[edge['child']]
                start,end=edge['points'][0],edge['points'][-1]
                self.assertEqual(start[1],float(parent['y'])+float(parent['height']))
                self.assertEqual(end[0],float(child['x']))
                self.assertEqual(end[1],float(child['y'])+float(child['height'])/2)
        projection['nodes'][1]['text']='A long native engineering name ' * 10
        before=deepcopy(projection)
        tree=ET.fromstring(render_function_tree(projection,target_width=1600)[0])
        label=tree.findall('svg:g',ns)[1].find("svg:text[@data-role='label']",ns)
        self.assertEqual(''.join(label.itertext()),projection['nodes'][1]['text'])
        self.assertGreater(len(label.findall('svg:tspan',ns)),2)
        self.assertEqual(projection,before)

    def test_wide_view_ids_wrap_without_truncation_and_small_targets_refuse(self):
        nodes,inventory=fixture()
        projection=project(nodes,inventory)
        projection['id']='W'*64
        svg,ledger=render_function_tree(projection,show_ids=True,target_width=1600)
        tree=ET.fromstring(svg)
        title=tree.find('{http://www.w3.org/2000/svg}text')
        self.assertEqual(''.join(title.itertext()),'W'*64+' - Function decomposition')
        self.assertGreater(len(title),1)
        for target in (320,400):
            with self.assertRaisesRegex(ValueError,'Target too small'):
                render_function_tree(projection,show_ids=True,target_width=target)

    def test_default_names_and_opt_in_metadata_preserve_semantics(self):
        nodes, inventory = fixture()
        # A legitimate native engineering identifier must not be stripped.
        inventory['actions'][0]['name'] = 'F0 Pump'
        projection = project(nodes, inventory)
        before = deepcopy(projection)
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        for show_ids in (False, True):
            with self.subTest(show_ids=show_ids):
                svg, ledger = render_function_tree(projection, show_ids=show_ids)
                tree = ET.fromstring(svg)
                title=tree.find("svg:text[@data-role='title']",ns)
                subtitle=tree.find("svg:text[@data-role='subtitle']",ns)
                self.assertEqual(''.join(title.itertext()), ('FT - ' if show_ids else '') + 'Function decomposition')
                self.assertEqual(subtitle.text, 'Documentary function hierarchy')
                for group, node in zip(tree.findall('svg:g', ns), projection['nodes']):
                    labels = group.findall("svg:text[@data-role='label']", ns)
                    self.assertEqual(''.join(labels[0].itertext()), node['text'])
                    metadata=group.findall("svg:text[@data-role='metadata']",ns)
                    self.assertEqual(bool(metadata),show_ids)
                    if show_ids:
                        self.assertEqual(''.join(t.text or '' for t in metadata), f"{node['id']} · level {node['level']}")
                    self.assertEqual(group.attrib['data-id'], node['id'])
                    self.assertEqual(group.attrib['data-level'], str(node['level']))
                    self.assertEqual(group.attrib['data-element'], node['element'])
                self.assertEqual(ledger['show_ids'], show_ids)
                self.assertIn('no behavioral or engineering acceptance claim', ledger['claim_scope'])
                self.assertEqual(projection, before)
        for invalid in ('false', 1, None):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'boolean'):
                render_function_tree(projection, show_ids=invalid)

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

    def test_shared_parent_trunk_is_single_neutral_route_with_explicit_child_drops(self):
        nodes,inventory=fixture();projection=project(nodes,inventory)
        svg,ledger=render_function_tree(projection)
        ns={'svg':'http://www.w3.org/2000/svg'};tree=ET.fromstring(svg)
        trunks=tree.findall("svg:path[@data-shared-parent='F0']",ns)
        self.assertEqual(len(trunks),1)
        self.assertEqual(trunks[0].attrib['stroke'],load_profile()['palette']['ink'])
        drops=tree.findall('svg:path[@data-child]',ns)
        self.assertEqual({p.attrib['data-child'] for p in drops},{'F1','F2'})
        self.assertTrue(all(p.attrib['data-parent']=='F0' for p in drops))
        self.assertEqual({e['child'] for e in ledger['edges']},{'F1','F2'})
        self.assertEqual(len(ledger['shared_routes']),1)

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

    def test_cli_default_and_opt_in_visibility_keep_exact_ledger_and_sources(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as temp:
            ledgers = []
            for show_ids in (False, True):
                output = Path(temp) / str(show_ids)
                command = [sys.executable, str(ROOT / 'scripts/sysml_present.py'), str(MODEL),
                           '--view', 'FT', '--output', str(output), '--target-width', '1600']
                if show_ids:
                    command.append('--show-ids')
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                tree = ET.parse(output / 'view.svg')
                texts = [t.text for t in tree.findall('.//{http://www.w3.org/2000/svg}text')]
                self.assertEqual(texts[:2], [('FT - ' if show_ids else '') + 'Function decomposition',
                                            'Documentary function hierarchy'])
                self.assertIn('ProcessSample', texts)
                self.assertEqual('F0 · level 0' in texts, show_ids)
                self.assertEqual((output / 'sources/model-1.sysml').read_bytes(), MODEL.read_bytes())
                ledgers.append((output / 'semantic-ledger.json').read_bytes())
                manifest = json.loads((output / 'manifest.json').read_text())
                self.assertEqual(manifest['show_ids'], show_ids)
                self.assertIn('no behavioral or engineering acceptance claim', manifest['claim_scope'])
                self.assertIn('no behavioral or engineering acceptance claim',
                              (output / 'index.html').read_text())
            self.assertEqual(*ledgers)

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
            labels = tree.findall(".//{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}text[@data-role='label']")
            self.assertTrue(labels)
            self.assertTrue(all(label.attrib['font-size'] == '23' for label in labels))
            self.assertEqual(profile_path.read_text(), json.dumps(profile))

    def test_native_wide_title_wraps_and_small_scale_refuses_without_output(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as folder:
            temp=Path(folder);view_id='W'*64;source=temp/'wide.sysml'
            source.write_text(MODEL.read_text().replace('"id": "FT"','"id": "'+view_id+'"'))
            with self.assertRaisesRegex(ValueError,'Target too small'):
                write_presentation(source,temp/'small',view_id=view_id,target_width=320,show_ids=True)
            self.assertFalse((temp/'small').exists())
            result=write_presentation(source,temp/'wide',view_id=view_id,target_width=1600,show_ids=True)
            self.assertEqual(result['status'],'pass')
            title=ET.parse(temp/'wide/view.svg').find('{http://www.w3.org/2000/svg}text')
            self.assertEqual(''.join(title.itertext()),view_id+' - Function decomposition')
            self.assertGreater(len(title),1)
            self.assertEqual((temp/'wide/sources/model-1.sysml').read_bytes(),source.read_bytes())

    def test_explicit_display_label_cli_sources_and_invalid_binding_refusal(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as folder:
            temp=Path(folder);model=ROOT/'examples/sysml/views/field-service-demo.sysml'
            labels=json.loads((ROOT/'examples/sysml/views/field-service-demo.labels.json').read_text())
            source=temp/'owned.sysml';source.write_bytes(model.read_bytes())
            label_path=temp/'labels.json';label_path.write_text(json.dumps(labels))
            cmd=[sys.executable,str(ROOT/'scripts/sysml_present.py'),str(source),'--view','FT_DEMO',
                 '--labels',str(label_path),'--target-width','1600','--output',str(temp/'first')]
            first=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stdout+first.stderr)
            ledger=(temp/'first/semantic-ledger.json').read_bytes()
            native=json.loads(ledger)
            self.assertIn('MaintainStation',[n['text'] for n in native['nodes']])
            self.assertNotIn('Maintain the inspection station',[n['text'] for n in native['nodes']])
            labels['labels'][0]['text']='Maintain the owned inspection station'
            label_path.write_text(json.dumps(labels));cmd[-1]=str(temp/'wording-edit')
            edited=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(edited.returncode,0,edited.stdout)
            self.assertEqual((temp/'wording-edit/semantic-ledger.json').read_bytes(),ledger)
            svg=ET.parse(temp/'wording-edit/view.svg')
            self.assertIn('Maintain the owned inspection station',[''.join(t.itertext()) for t in svg.findall('.//{http://www.w3.org/2000/svg}text')])
            source.write_text(source.read_text().replace('MaintainStation','MaintainOwnedStation'))
            cmd[-1]=str(temp/'stale-binding')
            failed=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(failed.returncode,1)
            self.assertIn('outside the selected native view',failed.stdout)
            self.assertFalse((temp/'stale-binding').exists())
            labels['labels'][0]['element']='FieldServiceDemo::MaintainOwnedStation'
            label_path.write_text(json.dumps(labels));cmd[-1]=str(temp/'source-edit')
            repaired=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(repaired.returncode,0,repaired.stdout)
            self.assertNotEqual((temp/'source-edit/semantic-ledger.json').read_bytes(),ledger)
            self.assertEqual((temp/'source-edit/sources/model-1.sysml').read_bytes(),source.read_bytes())
            self.assertEqual(json.loads((temp/'source-edit/display-labels.json').read_text()),labels)

    def test_label_file_changes_after_capture_cannot_change_bundle_companion(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as folder:
            temp=Path(folder);model=ROOT/'examples/sysml/views/field-service-demo.sysml'
            labels=json.loads((ROOT/'examples/sysml/views/field-service-demo.labels.json').read_text())
            path=temp/'labels.json';path.write_text(json.dumps(labels))
            real_render=render_function_tree
            def changed_after_render(*args,**kwargs):
                result=real_render(*args,**kwargs)
                changed=deepcopy(labels);changed['title']='Changed after render'
                changed['labels'][0]['element']='Unknown::Other'
                path.write_text(json.dumps(changed))
                return result
            with patch('verifier.visual_projection.render_function_tree',side_effect=changed_after_render):
                report=write_presentation(model,temp/'output',view_id='FT_DEMO',labels=path,target_width=1600)
            self.assertEqual(report['status'],'pass')
            saved=json.loads((temp/'output/display-labels.json').read_text())
            self.assertEqual(saved,labels)
            shown=json.loads((temp/'output/presentation.json').read_text())
            self.assertEqual(shown['display']['title'],labels['title'])
            self.assertEqual(shown['display']['bindings'],labels['labels'])
            self.assertNotEqual(json.loads(path.read_text()),saved)
            for name,digest in report['manifest']['files'].items():
                self.assertEqual(sha256((temp/'output'/name).read_bytes()).hexdigest(),digest)

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
