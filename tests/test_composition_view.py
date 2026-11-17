"""Physical source/diagram correspondence, saved geometry and original artwork."""
from copy import deepcopy
from hashlib import sha256
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError
from verifier.composition_project import CompositionProject
from verifier import composition_view as view
from verifier import kit_templates

SOURCE = '// 🛰 Preserve Unicode before native ranges.\n' + (ROOT/'examples/workbench/composition/diagram-model.sysml').read_text()
PROJECT = '18eaecb4-a089-47c1-9288-630083464bed'
SCOPE = {'version': 'configuration-1.0',
         'root': {'native_name': 'DiagramComposition::current', 'type': 'DiagramComposition::Assembly'},
         'selected_roles': {'Left': {'parent': '$root', 'native_name': 'DiagramComposition::current::left',
                                     'type': 'DiagramComposition::Device'}},
         'open_alternatives': [], 'connections': []}
NS = {'s': 'http://www.w3.org/2000/svg'}


def keyed_definition(document, legend):
    projection = view.project(document, 'PC_DEFINITION')
    appearance = {'version': 'cse-diagram-appearance-2.0', 'kit': 'engineering-palette-complete-05',
                  'view': 'PC_DEFINITION',
                  'nodes': {key: {'template': view.RECT, 'fill': 'N0', 'stroke': 'N100',
                                  'text': 'N100', 'align': 'center'} for key in projection['nodes']},
                  'edges': {}, 'legend': legend}
    root = next(key for key, node in projection['nodes'].items() if node['parent'] is None)
    appearance['nodes'][root].update(template='palette-rectangle-white-dots', fill='C18-L92')
    return CompositionDocument(document.files, project_id=document.project_id, registry=document.registry,
        linked_records={**document.linked_records,
                        'appearance.json': {'kind': 'composition_appearance', 'text': json.dumps(appearance)}})


def footer_detour(layout, y):
    result = deepcopy(layout)
    result['edges']['OwnModule']['points'] = [[416, 205], [446, 205], [446, y],
                                            [480, y], [480, 355], [496, 355]]
    return result


def crossing_example():
    parents = {'R': None, 'A': 'R', 'B': 'R', 'C': 'A', 'D': 'B'}
    names = {'R': 'Cross::R', 'A': 'Cross::R::A', 'B': 'Cross::R::B',
             'C': 'Cross::R::A::C', 'D': 'Cross::R::B::D'}
    nodes = [{'id': key, 'element': names[key], 'parent': parent, 'level': 0 if parent is None else 1 if parent == 'R' else 2,
              'edge': None if parent is None else 'E'+key} for key, parent in parents.items()]
    source = 'package Cross { part def R { part def A { part def C; } part def B { part def D; } } '
    source += 'doc cseViews /* CSE-VIEWS/1.1\n'+json.dumps({'views': [{'id': 'CROSS', 'kind': 'physical_composition', 'mode': 'definitions', 'nodes': nodes}]})+' */ }'
    d = CompositionDocument({'model.sysml': source})
    layout = {'version': 'cse-diagram-layout-1.0', 'view': 'CROSS', 'width': 1000, 'height': 900,
              'nodes': {key: {'x': x, 'y': y, 'width': 200, 'height': 90}
                        for key, x, y in [('R', 40, 160), ('A', 400, 160), ('B', 40, 600), ('C', 700, 400), ('D', 700, 300)]},
              'edges': {'EA': {'points': [[240, 205], [400, 205]]},
                        'EB': {'points': [[40, 205], [10, 205], [10, 645], [40, 645]]},
                        'EC': {'points': [[500, 250], [500, 445], [700, 445]]},
                        'ED': {'points': [[240, 645], [650, 645], [650, 345], [700, 345]]}}}
    return d, layout


class NativeViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        optional = deepcopy(SCOPE)
        optional['selected_roles']['Left']['native_name'] = 'DiagramComposition::current::optional'
        cls.linked = {'left.scope.json': {'kind': 'retained_configuration', 'text': json.dumps(SCOPE)},
                      'optional.scope.json': {'kind': 'retained_configuration', 'text': json.dumps(optional)}}
        cls.document = CompositionDocument({'model.sysml': SOURCE}, project_id=PROJECT, linked_records=cls.linked)

    def test_real_bounds_native_owners_and_scope_findings_are_not_conflated(self):
        rendered = view.render(self.document, 'PC_USAGE')
        p = rendered['projection']
        self.assertEqual(p['nodes']['Left']['native']['source_multiplicity'], '[2]')
        self.assertEqual(p['nodes']['Unbounded']['native']['source_multiplicity'], '[1..*]')
        self.assertEqual(p['nodes']['Left']['native']['owner'], 'DiagramComposition::current')
        self.assertEqual(p['edges']['OwnLeft'], {'source': 'Root', 'target': 'Left', 'kind': 'native_ownership',
                                               'directed': True, 'arrowheads': False})
        self.assertEqual({r['report']['status'] for r in p['configuration_reviews']}, {'pass', 'unknown'})
        optional_review = next(r for r in p['configuration_reviews'] if r['file'] == 'optional.scope.json')
        self.assertEqual(optional_review['retained_scope']['selected_roles']['Left']['native_name'],
                         'DiagramComposition::current::optional')
        self.assertEqual(optional_review['report']['view']['selected_roles'], {})
        doc = ET.fromstring(rendered['svg'])
        text = [el.text for el in doc.findall('.//s:text', NS)]
        for label in ['[2]', '[0..1]', '[0]', '[1..*]']:
            self.assertIn(label, text)
        unbounded = doc.find('.//s:g[@data-node-id="Unbounded"]', NS)
        self.assertIsNotNone(unbounded)
        self.assertIn('multiplicity: unsupported', ''.join(unbounded.itertext()))
        self.assertEqual(p['nodes']['Unbounded']['native']['multiplicity'], {'status': 'unsupported'})
        self.assertIn('DiagramComposition::current::peer', [r['element'] for r in p['omitted_elements']])
        self.assertIn('DiagramComposition::Base::inherited', [r['element'] for r in p['omitted_elements']])
        self.assertNotIn('marker-end', rendered['svg'])
        self.assertNotIn('marker-start', rendered['svg'])

    def test_definitions_retain_their_separate_hierarchy_and_native_kind(self):
        rendered = view.render(self.document, 'PC_DEFINITION')
        p = rendered['projection']
        self.assertEqual(p['mode'], 'definitions')
        self.assertEqual({n['kind'] for n in p['nodes'].values()}, {'PartDefinition'})
        self.assertEqual(p['nodes']['Module']['native']['owner'], 'DiagramComposition::Catalog')
        self.assertIn('Physical definition hierarchy', rendered['svg'])
        self.assertNotIn('Declared physical usage composition', rendered['svg'])

    def test_inherited_members_references_and_wrong_native_kinds_are_not_owned_children(self):
        for source, message in [
            (SOURCE.replace('"DiagramComposition::current::left"', '"DiagramComposition::Base::inherited"'), 'native declaring owner'),
            (SOURCE.replace('"DiagramComposition::current::left"', '"DiagramComposition::current::peer"'), 'Referenced resources'),
            (SOURCE.replace('"mode": "usages"', '"mode": "definitions"'), 'selected native kind')]:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                view.render(CompositionDocument({'model.sysml': source}), 'PC_USAGE')

    def test_saved_masters_fonts_editable_labels_and_baselines_match_the_kit(self):
        rendered = view.render(self.document, 'PC_USAGE')
        root = ET.fromstring(rendered['svg'])
        paper = root.find('s:rect', NS)
        self.assertIsNotNone(paper)
        self.assertEqual(paper.get('fill'), '#FFFFFF')
        self.assertEqual((float(paper.get('width')), float(paper.get('height'))),
                         (rendered['layout']['width'], rendered['layout']['height']))
        ids = [e.get('id') for e in root.iter() if e.get('id')]
        self.assertEqual(len(ids), len(set(ids)))
        for group in root.findall('s:g', NS):
            if not group.get('data-node-id'):
                continue
            frame = group.find('s:g', NS)
            master = ROOT / 'assets/engineering-library/components' / (frame.get('data-kit-template')+'.svg')
            self.assertEqual(frame.get('data-kit-sha256'), sha256(master.read_bytes()).hexdigest())
            self.assertEqual(len(frame.findall('s:use', NS)), 2)
            labels = group.findall('s:text', NS)
            for previous, current in zip(labels, labels[1:]):
                self.assertGreaterEqual(float(current.get('y'))-float(previous.get('y')),
                                        1.4*max(float(previous.get('font-size')), float(current.get('font-size'))))
        self.assertNotIn('Rectangle Plain White', ''.join(root.itertext()))
        self.assertTrue(all(t.get('font-family') in ('DejaVu Sans', 'DejaVu Sans Mono') for t in root.findall('.//s:text', NS)))
        self.assertEqual(set(rendered['kit_usage']['components']), {view.RECT, kit_templates.FIGURE_HEADING})

    def test_geometry_cannot_hide_a_binding_change_or_detach_a_native_endpoint(self):
        rendered = view.render(self.document, 'PC_USAGE')
        for change in ('omit', 'detach', 'overlap', 'overflow', 'text', 'nonfinite'):
            layout = deepcopy(rendered['layout'])
            if change == 'omit': del layout['nodes']['Left']
            if change == 'detach': layout['edges']['OwnLeft']['points'][-1][0] += 10
            if change == 'overlap': layout['nodes']['Left'].update(x=56, y=160)
            if change == 'overflow': layout['nodes']['Left']['x'] = layout['width']
            if change == 'text': layout['nodes']['Unbounded']['height'] = 50
            if change == 'nonfinite': layout['nodes']['Left']['x'] = float('nan')
            with self.subTest(change=change), self.assertRaises(ValueError):
                view.render(self.document, 'PC_USAGE', layout_override=layout)

    def test_alias_is_independent_of_native_identity_and_literal_quantity(self):
        labels = {'version': 1, 'view': 'PC_USAGE', 'title': 'Physical parts',
                  'labels': [{'element': 'DiagramComposition::current::left', 'text': 'Sensor bank'}]}
        d = CompositionDocument({'model.sysml': SOURCE}, project_id=PROJECT,
            linked_records={**self.linked, 'labels.json': {'kind': 'display_labels', 'text': json.dumps(labels)}})
        rendered = view.render(d, 'PC_USAGE')
        text = [t.text for t in ET.fromstring(rendered['svg']).findall('.//s:text', NS)]
        self.assertIn('Sensor bank', text)
        self.assertIn('[2]', text)
        self.assertEqual(rendered['projection']['nodes']['Left']['element'], 'DiagramComposition::current::left')
        self.assertEqual(d.files, {'model.sysml': SOURCE})

    def test_maximum_literal_range_stays_whole_and_saved_narrow_frames_refuse(self):
        identity=next(k for k,v in self.document.registry.items() if v=='DiagramComposition::current::left')
        candidate=self.document.set_multiplicity(identity,2147483646,2147483647,
            expected_source_sha256=self.document.revision)
        rendered=view.render(candidate,'PC_USAGE')
        group=ET.fromstring(rendered['svg']).find('.//s:g[@data-node-id="Left"]',NS)
        notation='[2147483646..2147483647]'
        self.assertIn(notation,[t.text for t in group.findall('s:text',NS)])
        self.assertGreater(rendered['layout']['nodes']['Left']['width'],360)
        old_layout=view.render(self.document,'PC_USAGE')['layout']
        with self.assertRaisesRegex(ValueError,'Multiplicity notation does not fit'):
            view.render(candidate,'PC_USAGE',layout_override=old_layout)
        enlarged=deepcopy(old_layout)
        enlarged['nodes']['Left']['width']=rendered['layout']['nodes']['Left']['width']
        self.assertIn(notation,view.render(candidate,'PC_USAGE',layout_override=enlarged)['svg'])

    def test_one_wide_bound_does_not_expand_every_level_of_a_depth_16_view(self):
        for all_wide in (False, True):
            names=['Deep::'+'::'.join(f'p{j}' for j in range(i+1)) for i in range(17)]
            nodes=[{'id':f'N{i}','element':name,'parent':None if i==0 else f'N{i-1}',
                    'level':i,'edge':None if i==0 else f'E{i}'} for i,name in enumerate(names)]
            source='package Deep { '+''.join(f'part p{i}'+(' [2147483646..2147483647]' if all_wide or i==16 else '')+' { ' for i in range(17))+'} '*17
            source+='doc cseViews /* CSE-VIEWS/1.1\n'+json.dumps({'views':[{'id':'DEEP','kind':'physical_composition','mode':'usages','nodes':nodes}]})+' */ }'
            rendered=view.render(CompositionDocument({'deep.sysml':source}),'DEEP')
            with self.subTest(all_wide=all_wide):
                self.assertLessEqual(rendered['layout']['width'],8192)
                if not all_wide:self.assertEqual(rendered['layout']['width'],7555)
                self.assertTrue(all(b['x']+b['width']<=rendered['layout']['width']-32 for b in rendered['layout']['nodes'].values()))
                root=ET.fromstring(rendered['svg'])
                literal=root.find('.//s:g[@data-node-id="N16"]/s:text[2]',NS)
                self.assertEqual(literal.text,'[2147483646..2147483647]')

    def test_saved_pattern_and_swatches_are_preserved_and_invisible_patterns_are_refused(self):
        projection = view.project(self.document, 'PC_USAGE')
        appearance = {'version': 'cse-diagram-appearance-2.0', 'kit': 'engineering-palette-complete-05',
                      'view': 'PC_USAGE', 'nodes': {key: {'template': view.RECT, 'fill': 'N0', 'stroke': 'C18-L36',
                                                       'text': 'N100', 'align': 'center'} for key in projection['nodes']},
                      'edges': {}, 'legend': ['Dots: decorative root field.']}
        appearance['nodes']['Root'].update(template='palette-rectangle-white-dots', fill='C18-L92')
        records = {**self.linked, 'appearance.json': {'kind': 'composition_appearance', 'text': json.dumps(appearance)}}
        d = CompositionDocument(self.document.files, project_id=PROJECT, linked_records=records)
        root = ET.fromstring(view.render(d, 'PC_USAGE')['svg'])
        pattern = root.find('.//s:pattern', NS)
        self.assertIsNotNone(pattern)
        self.assertIsNotNone(root.find('.//s:rect[@data-role="label-backing"]', NS))
        self.assertIn('#004167', view.render(d, 'PC_USAGE')['svg'])
        bad = deepcopy(appearance)
        bad['nodes']['Root'].update(fill='N50', text='N100', stroke='N100')
        with self.assertRaisesRegex(ValueError, 'pattern loses visibility'):
            view.validate_companion(bad, 'composition_appearance')
        bad = deepcopy(appearance)
        bad['nodes']['Root']['template'] = 'palette-circle-white-plain'
        with self.assertRaisesRegex(ValueError, 'rectangle master'):
            view.validate_companion(bad, 'composition_appearance')

    def test_nonconnecting_crossing_uses_the_saved_gap_master(self):
        d, layout = crossing_example()
        rendered = view.render(d, 'CROSS', layout_override=layout)
        gaps = [r for r in rendered['kit_usage']['adaptations'] if r.get('role') == 'nonconnecting crossing']
        self.assertEqual([(r['under'], r['over'], r['x'], r['y']) for r in gaps], [('EC', 'ED', 650, 445)])
        self.assertIn(kit_templates.GAP, rendered['kit_usage']['components'])
        self.assertIn('data-kit-template="'+kit_templates.GAP+'"', rendered['svg'])
        self.assertEqual(rendered['layout'], layout)

    def test_unrelated_collinear_routes_cannot_create_an_apparent_shared_junction(self):
        projection = {'edges': {'a': {'source': 'A'}, 'b': {'source': 'B'}}}
        layout = {'nodes': {}, 'edges': {'a': {'points': [[0, 200], [300, 200]]}, 'b': {'points': [[100, 200], [400, 200]]}}}
        with self.assertRaisesRegex(ValueError, 'overlap'):
            view.crossings(projection, layout)

    def test_independent_routes_keep_fifteen_units_of_visible_ink_clearance(self):
        projection = {'edges': {'a': {'source': 'A'}, 'b': {'source': 'B'}}}
        # Independently expected centreline clearance is 15 + 1.25 + 1.25.
        cases = [
            ([[0, 200], [300, 200]], [[100, 204], [400, 204]], False),
            ([[0, 200], [300, 200]], [[100, 217.49], [400, 217.49]], False),
            ([[0, 200], [300, 200]], [[100, 217.5], [400, 217.5]], True),
            ([[0, 200], [0, 400]], [[17.5, 200], [17.5, 400]], True),
            ([[0, 200], [200, 400]], [[0, 224], [200, 424]], False),
            ([[0, 200], [200, 400]], [[0, 225], [200, 425]], True),
            ([[0, 200], [100, 200]], [[117, 200], [200, 200]], False),
            ([[0, 200], [100, 200]], [[117.5, 200], [200, 200]], True),
            ([[0, 200], [100, 200]], [[104, 204], [104, 300]], False),
        ]
        for a, b, accepted in cases:
            layout = {'nodes': {}, 'edges': {'a': {'points': a}, 'b': {'points': b}}}
            with self.subTest(a=a, b=b):
                if accepted:
                    self.assertEqual(view.crossings(projection, layout), [])
                else:
                    with self.assertRaisesRegex(ValueError, 'ink clearance'):
                        view.crossings(projection, layout)
        # Fanout from one native parent retains its intentional shared trunk.
        projection['edges']['b']['source'] = 'A'
        layout['edges'] = {'a': {'points': [[0, 200], [100, 200], [100, 300]]},
                           'b': {'points': [[0, 200], [100, 200], [100, 400]]}}
        self.assertEqual(view.crossings(projection, layout), [])

    def test_crossing_gap_cannot_erase_a_nearby_endpoint_or_bend(self):
        projection = {'edges': {'a': {'source': 'A'}, 'b': {'source': 'B'}}}
        layout = {'nodes': {}, 'edges': {'a': {'points': [[0, 200], [300, 200]]},
                                         'b': {'points': [[150, 190], [150, 300]]}}}
        with self.assertRaisesRegex(ValueError, 'clearance from route bends and endpoints'):
            view.crossings(projection, layout)

    def test_local_key_reuses_the_original_ruled_legend_with_source_bound_text(self):
        lines = ['Pattern distinguishes selected scope.', 'Color carries no material meaning.']
        document = keyed_definition(self.document, lines)
        rendered = view.render(document, 'PC_DEFINITION')
        root = ET.fromstring(rendered['svg'])
        key = root.find('.//s:g[@data-role="local-key"]', NS)
        self.assertEqual(key.get('data-view-id'), 'PC_DEFINITION')
        self.assertEqual([text.text for text in key.findall('s:text', NS)], ['Local key', *lines])
        self.assertIsNotNone(key.find('s:g[@data-kit-template="'+kit_templates.LEGEND+'"]', NS))
        self.assertEqual(rendered['kit_usage']['components'][kit_templates.LEGEND],
                         kit_templates.source_record(kit_templates.LEGEND)['sha256'])
        self.assertEqual(json.loads(document.linked_records['appearance.json']['text'])['legend'], lines)
        self.assertTrue(all(row.get('role') != 'local key' for row in
                            view.render(self.document, 'PC_DEFINITION')['kit_usage']['adaptations']))

    def test_routes_cannot_cross_or_encroach_on_the_authored_local_key(self):
        # Independently supplied route passes native endpoints/node obstacles,
        # but y=495 enters the one-line legend table beginning at y=478.
        document = keyed_definition(self.document, ['Pattern distinguishes selected scope.'])
        layout = view.render(self.document, 'PC_DEFINITION')['layout']
        layout['height'] = 628
        for y in (495, 450, 446):
            candidate = footer_detour(layout, y)
            projection = view.project(document, 'PC_DEFINITION')
            view.geometry(projection, candidate, view.labels(document, projection))
            with self.subTest(y=y), self.assertRaisesRegex(ValueError, 'reserved local key area'):
                view.render(document, 'PC_DEFINITION', layout_override=candidate)
        clear = footer_detour(layout, 445)
        self.assertIn('Pattern distinguishes selected scope.',
                      view.render(document, 'PC_DEFINITION', layout_override=clear)['svg'])
        # Two lines start 34 units earlier and need correspondingly more space.
        two_lines = keyed_definition(self.document, ['Pattern distinguishes selected scope.', 'A second local key line.'])
        with self.assertRaisesRegex(ValueError, 'reserved local key area'):
            view.render(two_lines, 'PC_DEFINITION', layout_override=clear)
        taller = footer_detour(layout, 495)
        taller['height'] = 728
        self.assertEqual(view.render(two_lines, 'PC_DEFINITION', layout_override=taller)['layout'], taller)
        # There is no key to collide with in a plain view. Authored appearance
        # cannot bypass key requirements by supplying an empty list.
        detour = footer_detour(layout, 495)
        self.assertEqual(view.render(self.document, 'PC_DEFINITION', layout_override=detour)['layout'], detour)
        with self.assertRaisesRegex(EditError, 'needs its local key'):
            keyed_definition(self.document, [])


    def test_reader_preserves_literal_alias_text_without_executing_model_markup(self):
        alias = 'A < B & </script><script>throw 1</script>'
        labels = {'version': 1, 'view': 'PC_USAGE', 'title': 'Physical parts',
                  'labels': [{'element': 'DiagramComposition::current::left', 'text': alias}]}
        d = CompositionDocument(self.document.files, project_id=PROJECT,
            linked_records={'labels.json': {'kind': 'display_labels', 'text': json.dumps(labels)}})
        files = view.artifact_files({'document': d, 'revision': 1, 'commit': '0'*40}, 'PC_USAGE')
        html = files['index.html'].decode('utf-8')
        payload = re.search(r'<script id="cse-data" type="application/json">(.*?)</script>', html, re.S).group(1)
        self.assertNotIn('<', payload)
        self.assertEqual(json.loads(payload)['display_labels']['Left'], alias)
        self.assertNotIn('<script>throw 1</script>', html)


class PersistenceViews(unittest.TestCase):
    def setUp(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'.tmp')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.project, _ = CompositionProject.create(self.work/'project.git', {'model.sysml': SOURCE},
                                                    project_id=PROJECT, request_id=str(uuid4()))

    def test_close_independent_routes_refuse_atomically_and_separated_routes_reopen(self):
        document, layout = crossing_example()
        layout['nodes']['D']['y'] = 600
        layout['edges']['ED']['points'] = [[240, 645], [650, 645], [650, 449],
                                          [690, 449], [690, 645], [700, 645]]
        # These four-unit-separated routes still have correct native endpoints
        # and miss all node interiors. Their visible ink is only 1.5 apart.
        projection = view.project(document, 'CROSS')
        view.geometry(projection, layout, view.labels(document, projection))
        project, _ = CompositionProject.create(self.work/'clearance.git', document.files,
            project_id=PROJECT, request_id=str(uuid4()))
        first = project.snapshot()
        request = {'operation': 'set_layout', 'request_id': str(uuid4()),
                   'expected_revision': 1, 'layout': layout}
        objects = project._git('count-objects', '-v').stdout
        for action in (project.preview, project.transact):
            with self.subTest(action=action.__name__), self.assertRaisesRegex(ValueError, 'ink clearance'):
                action(request)
            self.assertEqual(project.head(), first['commit'])
            self.assertEqual(project._git('count-objects', '-v').stdout, objects)
        request['layout']['edges']['ED']['points'][2][1] = 520
        request['layout']['edges']['ED']['points'][3][1] = 520
        preview = project.preview(request)
        receipt = project.transact(request)
        self.assertEqual(project.transact(request), receipt)
        saved = CompositionProject(project.repository).snapshot()
        self.assertEqual(saved['document'].files, document.files)
        self.assertEqual(saved['document'].registry, first['document'].registry)
        self.assertEqual(view.render(saved['document'], 'CROSS')['svg'],
                         view.render(preview['document'], 'CROSS')['svg'])

    def test_key_collision_is_refused_before_preview_or_publication_and_safe_routes_reopen(self):
        original = self.project.snapshot()['document']
        keyed = keyed_definition(original, ['Pattern distinguishes selected scope.'])
        project, _ = CompositionProject.create(self.work/'keyed.git', keyed.files,
            project_id=PROJECT, request_id=str(uuid4()), linked_records=keyed.linked_records)
        first = project.snapshot()
        layout = view.render(original, 'PC_DEFINITION')['layout']
        layout['height'] = 628
        request = {'operation': 'set_layout', 'request_id': str(uuid4()),
                   'expected_revision': 1, 'layout': footer_detour(layout, 495)}
        objects = project._git('count-objects', '-v').stdout
        for action in (project.preview, project.transact):
            with self.subTest(action=action.__name__), self.assertRaisesRegex(ValueError, 'reserved local key area'):
                action(request)
            self.assertEqual(project.head(), first['commit'])
            self.assertEqual(project._git('count-objects', '-v').stdout, objects)
        request['layout'] = footer_detour(layout, 445)
        preview = project.preview(request)
        receipt = project.transact(request)
        self.assertEqual(receipt['revision'], 2)
        self.assertEqual(project.transact(request), receipt)
        reopened = CompositionProject(project.repository).snapshot()
        self.assertEqual(reopened['document'].files, original.files)
        self.assertEqual(reopened['document'].registry, original.registry)
        self.assertEqual(reopened['document'].linked_records['appearance.json'], keyed.linked_records['appearance.json'])
        self.assertEqual(view.render(reopened['document'], 'PC_DEFINITION')['svg'],
                         view.render(preview['document'], 'PC_DEFINITION')['svg'])

    def test_move_resize_rename_and_restart_preserve_model_identity_and_saved_geometry(self):
        first = self.project.snapshot()
        drawing = view.render(first['document'], 'PC_USAGE')
        layout = deepcopy(drawing['layout'])
        layout['nodes']['Left']['x'] += 20
        layout['nodes']['Left']['height'] += 40
        route = layout['edges']['OwnLeft']['points']
        route[-1][0] += 20
        route[-1][1] += 20
        route[-2][1] += 20
        request = {'operation': 'set_layout', 'request_id': str(uuid4()), 'expected_revision': 1, 'layout': layout}
        receipt = self.project.transact(request)
        self.assertEqual(receipt['revision'], 2)
        self.assertEqual(self.project.transact(request), receipt)
        second = CompositionProject(self.project.repository).snapshot()
        self.assertEqual(second['document'].files, first['document'].files)
        self.assertEqual(second['document'].registry, first['document'].registry)
        self.assertEqual(view.render(second['document'], 'PC_USAGE')['layout'], layout)
        element_id = drawing['projection']['nodes']['Left']['element_id']
        self.project.transact({'operation': 'rename', 'request_id': str(uuid4()), 'expected_revision': 2,
                               'element_id': element_id, 'new_name': 'detector'})
        third = self.project.snapshot()
        rendered = view.render(third['document'], 'PC_USAGE')
        self.assertEqual(rendered['layout'], layout)
        self.assertEqual(rendered['projection']['nodes']['Left']['element_id'], element_id)
        self.assertEqual(rendered['projection']['nodes']['Left']['element'], 'DiagramComposition::current::detector')
        self.assertIn('detector', rendered['svg'])
        self.assertEqual(third['document'].linked_records['presentation/PC_USAGE.layout.json']['text'],
                         second['document'].linked_records['presentation/PC_USAGE.layout.json']['text'])
        self.project.transact({'operation': 'restore', 'request_id': str(uuid4()), 'expected_revision': 3, 'target_revision': 1})
        undone = self.project.snapshot()
        self.assertEqual(undone['revision'], 4)
        self.assertEqual(view.render(undone['document'], 'PC_USAGE')['layout'], drawing['layout'])
        self.assertEqual(undone['document'].registry, first['document'].registry)
        self.project.transact({'operation': 'restore', 'request_id': str(uuid4()), 'expected_revision': 4, 'target_revision': 3})
        redone = self.project.snapshot()
        self.assertEqual(redone['revision'], 5)
        self.assertEqual(view.render(redone['document'], 'PC_USAGE')['layout'], layout)
        self.assertEqual(redone['document'].registry[element_id], 'DiagramComposition::current::detector')
        with self.assertRaises(EditError) as error:
            self.project.transact({**request, 'request_id': str(uuid4())})
        self.assertEqual(error.exception.code, 'stale_revision')

    def test_invalid_layout_and_rename_that_clips_saved_labels_never_advance_the_head(self):
        first = self.project.snapshot()
        drawing = view.render(first['document'], 'PC_USAGE')
        self.project.transact({'operation': 'set_layout', 'request_id': str(uuid4()), 'expected_revision': 1,
                               'layout': drawing['layout']})
        head = self.project.head()
        layout = deepcopy(drawing['layout'])
        layout['nodes']['Left']['x'] = -1
        with self.assertRaises(ValueError):
            self.project.transact({'operation': 'set_layout', 'request_id': str(uuid4()), 'expected_revision': 2, 'layout': layout})
        with self.assertRaises(EditError) as error:
            self.project.transact({'operation': 'rename', 'request_id': str(uuid4()), 'expected_revision': 2,
                                   'element_id': drawing['projection']['nodes']['Left']['element_id'], 'new_name': 'W'*64})
        self.assertEqual(error.exception.code, 'presentation_conflict')
        self.assertEqual(self.project.head(), head)

    def test_exports_bind_exact_revision_sources_and_original_masters_and_reject_staleness(self):
        snapshot = self.project.snapshot()
        target = self.work/'artifacts'
        view.write_artifacts(snapshot, 'PC_USAGE', target)
        self.assertEqual((target/'sources/model.sysml').read_bytes(), SOURCE.encode('utf-8'))
        for path in (target/'artwork').glob('*.svg'):
            self.assertEqual(path.read_bytes(), (ROOT/'assets/engineering-library/components'/path.name).read_bytes())
        view.check_artifacts(snapshot, 'PC_USAGE', target)
        with self.assertRaisesRegex(ValueError, 'existing artifact'):
            view.write_artifacts(snapshot, 'PC_USAGE', target)
        (target/'view.svg').write_text((target/'view.svg').read_text().replace('[2]', '[3]'))
        with self.assertRaisesRegex(ValueError, 'Stale or changed'):
            view.check_artifacts(snapshot, 'PC_USAGE', target)

    def test_cli_render_uses_the_same_saved_project_and_detects_changed_source(self):
        output = self.work/'cli-artifacts'
        def cli(command):
            return subprocess.run([sys.executable, str(ROOT/'scripts/composition_project.py'), command,
                                   '--project', str(self.project.repository), '--view-id', 'PC_USAGE', '--output', str(output)],
                                  cwd=ROOT, text=True, capture_output=True)
        result = cli('render')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertEqual(cli('check-render').returncode, 0)
        first = self.project.snapshot()
        element_id = next(key for key, name in first['document'].registry.items() if name == 'DiagramComposition::current::left')
        self.project.transact({'operation': 'rename', 'request_id': str(uuid4()), 'expected_revision': 1,
                               'element_id': element_id, 'new_name': 'detector'})
        self.assertNotEqual(cli('check-render').returncode, 0)


if __name__ == '__main__':
    unittest.main()
