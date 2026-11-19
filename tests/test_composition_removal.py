"""Native removal tests with independent source and binding expectations."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError, elements
from verifier.composition_removal import delete_source, inspect_removal


class RemovalTests(unittest.TestCase):
    def test_exact_typed_removal_retains_surviving_tokens_and_comment(self):
        before = {
            'parts.sysml': 'package P { part def First; part def Last; part def Retire; }\r\n',
            'use.sysml': 'package Q { // 🧪\r\npart active : P::First, P::Retire, // before last\r\n P::Last; }\r\n',
        }
        document = CompositionDocument(before)
        identity = self.identity(document, 'P::Retire')
        impact = inspect_removal(document, identity, expected_source_sha256=document.revision)
        reference, = impact['incoming']
        self.assertEqual(reference['spelling'], 'P::Retire')
        self.assertEqual(reference['typing_owner_id'], self.identity(document, 'Q::active'))
        self.assertEqual(reference['location']['file'], 'use.sysml')
        effect = {'location': reference['location'], 'replacement_id': None}
        after, _ = delete_source(document, identity, [effect], expected_source_sha256=document.revision)
        self.assertEqual(after.files, {
            'parts.sysml': before['parts.sysml'].replace('part def Retire;', ''),
            'use.sysml': before['use.sysml'].replace(', P::Retire,', ' ,'),
        })
        self.assertEqual(elements(after.parsed)['Q::active']['types'], ['P::First', 'P::Last'])
        self.assertEqual(set(document.registry) - set(after.registry), {identity})
        self.assertEqual(document.files, before)
        for invalid in ([], [effect,effect], [{**effect,'replacement_id':identity}],
                        [{**effect,'location':{**effect['location'],'offset': reference['location']['offset']+1}}]):
            with self.subTest(invalid=invalid), self.assertRaises(EditError) as caught:
                delete_source(document, identity, invalid, expected_source_sha256=document.revision)
            self.assertEqual(caught.exception.code, 'explicit_effects')
        with self.assertRaises(EditError) as caught:
            inspect_removal(document, identity, expected_source_sha256='stale')
        self.assertEqual(caught.exception.code, 'stale_revision')

    def test_resolve_one_affected_binding_with_exact_replacement(self):
        text = ('package P { part def Replacement; part def Retire; '
                'part installed : // preserve this note\nP::Retire; part untouched : P::Replacement; }')
        document = CompositionDocument(text)
        identity = self.identity(document, 'P::Retire')
        impact = inspect_removal(document, identity, expected_source_sha256=document.revision)
        reference, = impact['incoming']
        after, _ = delete_source(document, identity,
                                 [{'location':reference['location'],'replacement_id':self.identity(document,'P::Replacement')}],
                                 expected_source_sha256=document.revision)
        self.assertEqual(after.source, text.replace('part def Retire;', '').replace('P::Retire','P::Replacement'))

    def test_anonymous_owned_item_is_reported_with_its_native_source(self):
        text = 'package P { part def Drop { item; } part def Leave; }'
        document = CompositionDocument(text)
        identity = self.identity(document, 'P::Drop')
        impact = inspect_removal(document, identity, expected_source_sha256=document.revision)
        blocker, = impact['owned_blockers']
        self.assertEqual(blocker['member_kinds'], ['ItemUsage'])
        loc = blocker['source_location']
        self.assertEqual(text[loc['offset']:loc['offset']+loc['length']], 'item;')
        with self.assertRaises(EditError) as caught:
            delete_source(document, identity, [], expected_source_sha256=document.revision)
        self.assertEqual(caught.exception.code, 'owned_members')

    def test_identical_terminal_type_does_not_hide_path_through_removed_alias(self):
        text = ('package P { part def T; part def Drop { alias Alternate for P::T; } '
                'part affected : P::Drop::Alternate; part retained : P::T; }')
        document = CompositionDocument(text)
        identity = self.identity(document, 'P::Drop')
        impact = inspect_removal(document, identity, expected_source_sha256=document.revision)
        incoming, = impact['incoming']
        self.assertEqual(incoming['target'], 'P::T')
        self.assertEqual(incoming['spelling'], 'P::Drop::Alternate')
        self.assertEqual(incoming['reasons'], ['path_segment', 'local_alias'])

    def test_exact_view_candidate_refuses_float_reference_locators(self):
        from verifier.composition_removal_views import delete_element, model_removal_impact
        document = CompositionDocument('package P { part def Drop; part installed : P::Drop; }')
        identity = self.identity(document,'P::Drop')
        impact = model_removal_impact(document,identity,expected_source_sha256=document.revision)
        reference, = impact['incoming']
        locator = {**reference['location'],'offset':float(reference['location']['offset'])}
        with self.assertRaises(EditError) as caught:
            delete_element(document,identity,[{'location':locator,'replacement_id':None}],[],
                           expected_source_sha256=document.revision)
        self.assertEqual(caught.exception.code,'explicit_effects')

    def test_partial_or_inconsistent_name_path_cannot_authorize_deletion(self):
        from copy import deepcopy
        original = CompositionDocument('package P { part def T; part def Drop; part installed : P::T; }')
        selected = self.identity(original,'P::Drop')
        for status, count in (('unsupported',1), ('error',1), ('resolved',1)):
            with self.subTest(status=status):
                document = deepcopy(original)
                ref, = document.parsed['reference_spans']
                ref['name_binding']['status'] = status
                ref['name_binding']['segments'] = ref['name_binding']['segments'][:count]
                with self.assertRaises(EditError) as error:
                    inspect_removal(document, selected, expected_source_sha256=document.revision)
                self.assertEqual(error.exception.code,'reference_form')

    def test_retained_configuration_changes_finding_with_svg_bytes_intact(self):
        from verifier.composition_view import render
        fixture = json.loads((ROOT/'tests/fixtures/composition-role-inspection.json').read_text())
        case = fixture['cases'][0]
        linked = {'scope.json': {'kind': 'retained_configuration', 'text': case['retained_scope_text']}}
        document = CompositionDocument(case['models'], project_id=fixture['project_id'], linked_records=linked)
        identity = self.identity(document, 'Composition::Base::sensor')
        after, _ = delete_source(document, identity, [], expected_source_sha256=document.revision)
        self.assertEqual(after.linked_records, linked)
        self.assertEqual(document.configuration_reviews[0]['report']['status'], 'pass')
        self.assertEqual(after.configuration_reviews[0]['report']['findings'][0]['rule'], 'native_identity')
        for view in ('PC_CONTEXT', 'PC_DECLARATION'):
            self.assertEqual(render(document, view)['svg'], render(after, view)['svg'])

    def test_last_view_can_close_with_exact_native_source_and_no_orphan_companions(self):
        from test_composition_ownership import tree
        from verifier.composition_removal_views import occurrence_removal_impact, remove_occurrence
        from verifier.composition_view import render
        context = tree('PC_ROOT', [('Root','P::root',None,0,None)])
        source = ('package P { part root; // Original view note\n'
                  + 'doc cseViews /* CSE-VIEWS/1.1\n'+json.dumps({'views':[context]})+'\n*/\n}\n')
        document = CompositionDocument(source)
        layout = {'root.layout.json': {'kind':'composition_layout','text':json.dumps(render(document,'PC_ROOT')['layout'])}}
        document = CompositionDocument(source, project_id=document.project_id, linked_records=layout)
        impact = occurrence_removal_impact(document, 'PC_ROOT','Root',expected_source_sha256=document.revision)
        effect = {key:impact['views'][0][key] for key in ('view_id','action','node_ids','edge_ids')}
        self.assertEqual(effect, {'view_id':'PC_ROOT','action':'close_view','node_ids':['Root'],'edge_ids':[]})
        result, _ = remove_occurrence(document,'PC_ROOT','Root',[effect],expected_source_sha256=document.revision)
        self.assertEqual(result.source, 'package P { part root; // Original view note\n\n}\n')
        self.assertEqual(result.registry, document.registry)
        self.assertEqual(result.linked_records, {})

    def test_removing_declared_redefinition_keeps_inherited_declaration(self):
        fixture = json.loads((ROOT/'tests/fixtures/composition-role-inspection.json').read_text())
        case = next(row for row in fixture['cases'] if row['id']=='explicit_override')
        linked = {'scope.json': {'kind': 'retained_configuration', 'text': case['retained_scope_text']}}
        document = CompositionDocument(case['models'], project_id=fixture['project_id'], linked_records=linked)
        identity = self.identity(document, 'Composition::current::sensor')
        after, _ = delete_source(document, identity, [], expected_source_sha256=document.revision)
        self.assertIn(self.identity(document, 'Composition::Base::sensor'), after.registry)
        self.assertNotIn(identity, after.registry)
        self.assertEqual(after.linked_records, linked)
        self.assertEqual(document.configuration_reviews[0]['report']['status'], 'pass')
        self.assertEqual(after.configuration_reviews[0]['report']['status'], 'fail')

    def test_closed_active_view_has_explicit_preview_and_durable_acknowledgement(self):
        from test_composition_ownership import tree
        from verifier.composition_project import CompositionProject
        from verifier.composition_session import CompositionSession
        entry = tree('PC_ROOT', [('Root','P::root',None,0,None)])
        src = 'package P { part root; doc cseViews /* CSE-VIEWS/1.1\n'+json.dumps({'views':[entry]})+'\n*/\n}'
        with TemporaryDirectory() as folder:
            project, first = CompositionProject.create(Path(folder)/'project.git', {'model.sysml':src},
                                                        project_id=str(uuid4()), request_id=str(uuid4()))
            session = CompositionSession(project,'PC_ROOT')
            request = {'operation':'remove_occurrence','request_id':str(uuid4()),'expected_revision':1,
                       'view_id':'PC_ROOT','node_id':'Root','checked_bundle_sha256':None,
                       'view_effects':[{'view_id':'PC_ROOT','action':'close_view','node_ids':['Root'],'edge_ids':[]}]}
            preview = session.preview(request)
            self.assertTrue(preview['current_view_closed'])
            self.assertIsNone(preview['candidate_svg'])
            checked = preview['checked_request']
            target = session.preview_view(checked,'PC_ROOT')
            self.assertTrue(target['closed'])
            self.assertIsNone(target['candidate_svg'])
            self.assertEqual(project.head(), first['commit'])
            applied = session.apply(checked)
            self.assertIsNone(applied['state'])
            self.assertEqual(applied['view_closed'], {'view_id':'PC_ROOT','available_views':[],
                                                     'revision':2,'commit':applied['receipt']['commit']})
            self.assertEqual(CompositionSession(CompositionProject(project.repository),'PC_ROOT').apply(checked),
                             applied)

    def test_cli_git_receipts_capture_view_only_delete_close_restore_and_original_artwork(self):
        from test_composition_ownership import OwnershipTests
        from verifier.composition_project import CompositionProject
        from verifier.composition_view import render
        OwnershipTests.setUpClass()
        initial = OwnershipTests.document
        main, detail = 'PC_OWN', 'PC_DETAIL_LEFT'
        authored = render(initial, main)
        frame = {'template':'palette-rectangle-white-plain', 'fill':'N0', 'stroke':'N100', 'text':'N100', 'align':'center'}
        appearance = {'version':'cse-diagram-appearance-2.0', 'kit':'engineering-palette-complete-05',
                      'view':main, 'nodes':{key:dict(frame) for key in authored['layout']['nodes']},
                      'edges':{}, 'legend':['Dotted frame: authored category']}
        appearance['nodes']['Left']['template'] = 'palette-rectangle-white-dots'
        layout = authored['layout']
        layout['height'] += 180
        linked = {'appearance.json':{'kind':'composition_appearance','text':json.dumps(appearance)},
                  'main.layout.json':{'kind':'composition_layout','text':json.dumps(layout)},
                  'detail.layout.json':{'kind':'composition_layout','text':json.dumps(render(initial,detail)['layout'])}}
        with TemporaryDirectory() as folder:
            root = Path(folder)
            escaped = initial.files['model.sysml'].replace('"views"', r'"\u0076iews"', 1)
            self.assertIn(r'"\u0076iews"', escaped)
            project, first = CompositionProject.create(root/'p.git', {'model.sysml':escaped}, project_id=initial.project_id,
                                                       request_id=str(uuid4()), linked_records=linked)

            def cli(command, payload):
                request_file = root/'request.json'
                request_file.write_text(json.dumps(payload))
                result = subprocess.check_output([sys.executable, '-B', str(ROOT/'scripts/composition_project.py'),
                                          command, '--project', str(project.repository), '--request', str(request_file)])
                return json.loads(result)

            def effects(impact):
                return [{key: row[key] for key in ('view_id','action','node_ids','edge_ids')} for row in impact['views']]

            def groups(svg):
                return {row.attrib['data-node-id']:ElementTree.tostring(row) for row in ElementTree.fromstring(svg).iter()
                        if 'data-node-id' in row.attrib}

            original = project.snapshot()['document']
            before_main = render(original,main)
            before_detail = render(original,detail)
            revision = {'expected_revision':1,'expected_bundle_sha256':original.revision}
            impact = cli('inspect-removal', {**revision,'view_id':main,'node_id':'Sensor'})['removal']
            self.assertEqual(impact['element_id'], self.identity(original,'P::current::left::sensor'))
            self.assertEqual(effects(impact), [{'view_id':main,'action':'remove_occurrences',
                                                'node_ids':['Leaf','Sensor'],'edge_ids':['OwnLeaf','OwnSensor']}])
            remove = {'operation':'remove_occurrence','request_id':str(uuid4()),'expected_revision':1,
                      'view_id':main,'node_id':'Sensor','view_effects':effects(impact),'checked_bundle_sha256':None}
            preview = cli('preview',remove)['preview']
            self.assertEqual(project.head(), first['commit'])
            receipt = cli('apply',preview['checked_request'])['receipt']
            self.assertEqual(receipt['revision'], 2)
            after_diagram = CompositionProject(project.repository).snapshot()['document']
            self.assertEqual(after_diagram.registry, original.registry)
            self.assertEqual(render(after_diagram,detail)['svg'], before_detail['svg'])
            self.assertEqual(after_diagram.linked_records['detail.layout.json'], linked['detail.layout.json'])

            selection = self.identity(after_diagram,'P::current::left')
            impact = cli('inspect-removal', {'expected_revision':2,
                 'expected_bundle_sha256':after_diagram.revision,'element_id':selection})['removal']
            self.assertEqual([row['action'] for row in impact['views']], ['remove_occurrences','close_view'])
            self.assertEqual(impact['views'][0]['removed_templates'], ['palette-rectangle-white-dots'])
            self.assertEqual(impact['views'][0]['retained_authored_legend'], ['Dotted frame: authored category'])
            delete = {'operation':'delete','request_id':str(uuid4()),'expected_revision':2,
                      'element_id':selection,'reference_effects':[],'view_effects':effects(impact),
                      'checked_bundle_sha256':None}
            with self.assertRaises(EditError) as caught:
                project.transact(delete)
            self.assertEqual(caught.exception.code, 'checked_candidate')
            checked = cli('preview',delete)['preview']['checked_request']
            receipt = cli('apply',checked)['receipt']
            self.assertEqual(receipt['revision'], 3)
            self.assertEqual(cli('apply',checked)['receipt'], receipt)
            self.assertEqual(cli('receipt',checked)['receipt'], receipt)
            with self.assertRaises(EditError) as stale:
                project.transact({**checked,'request_id':str(uuid4())})
            self.assertEqual(stale.exception.code, 'stale_revision')
            self.assertEqual(project.head(), receipt['commit'])
            final = project.snapshot()['document']
            self.assertEqual(set(original.registry)-set(final.registry), set(impact['part_ids']))
            self.assertNotIn('detail.layout.json', final.linked_records)
            with self.assertRaisesRegex(ValueError,'Selected physical view is unavailable'):
                render(final,detail)
            remaining = render(final,main)
            self.assertEqual(groups(remaining['svg']), {key:value for key,value in groups(before_main['svg']).items()
                                                        if key in ('Root','Right')})
            self.assertIn('Dotted frame', remaining['svg'])
            self.assertIn(r'"\u0076iews"', final.files['model.sysml'])
            restored = cli('apply',{'operation':'restore','request_id':str(uuid4()),'expected_revision':3,'target_revision':1})
            self.assertEqual(restored['receipt']['revision'], 4)
            latest = CompositionProject(project.repository).snapshot()['document']
            self.assertEqual(latest.files, original.files)
            self.assertEqual(latest.linked_records, original.linked_records)
            self.assertEqual(latest.registry, original.registry)
            self.assertEqual(render(latest,main)['svg'], before_main['svg'])
            self.assertEqual(render(latest,detail)['svg'], before_detail['svg'])

    @staticmethod
    def identity(document, native_name):
        return next(identity for identity, name in document.registry.items() if name == native_name)


if __name__ == '__main__':
    unittest.main()
