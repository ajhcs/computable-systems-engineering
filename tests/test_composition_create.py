"""Native/model/view/Git acceptance controls for owned definition creation."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError, fingerprint
from verifier.composition_project import CompositionProject
from verifier.composition_session import CompositionSession
from verifier.composition_view import render
from tests.test_composition_edit import REFERENCE_SOURCE, REFERENCE_SCOPE


class CreationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = {'kind': 'retained_configuration', 'text': json.dumps(REFERENCE_SCOPE, indent=2)+'\n'}
        cls.document = CompositionDocument({'model.sysml': REFERENCE_SOURCE,
            'untouched.sysml': '// exact 🛰\r\npackage Untouched;\r\n'}, linked_records={'scope.json': cls.scope})
        cls.owner = next(k for k,v in cls.document.registry.items() if v == 'ReferenceComposition::Outer')

    def create(self, document=None, **changes):
        d = document or self.document
        options = {'owner_id': self.owner, 'element_id': str(uuid4()), 'new_name': "Sénsor's spare", 'short_id': 'SPARE',
                   'view_id': 'PC_REFERENCE', 'placement': None, 'expected_source_sha256': d.revision}
        options.update(changes)
        return d.create_definition(**options), options

    def test_native_definition_occurrence_registry_and_retained_scope_are_one_candidate(self):
        before = render(self.document, 'PC_REFERENCE')
        result, request = self.create()
        name = "ReferenceComposition::Outer::'Sénsor\\'s spare'"
        self.assertEqual(result.registry[request['element_id']], name)
        self.assertEqual({k:v for k,v in result.registry.items() if k != request['element_id']}, self.document.registry)
        self.assertEqual(result.files['untouched.sysml'], self.document.files['untouched.sysml'])
        self.assertEqual(result.linked_records['scope.json'], self.scope)
        self.assertEqual(result.configuration_reviews[0]['report']['status'], 'pass')
        self.assertIn("part def <SPARE> 'Sénsor\\'s spare';", result.source)
        drawing = render(result, 'PC_REFERENCE')
        new = next(node for node in drawing['projection']['nodes'].values() if node['element_id'] == request['element_id'])
        self.assertEqual((new['native']['owner'], new['native']['name'], new['native']['id']),
                         ('ReferenceComposition::Outer', "Sénsor's spare", 'SPARE'))
        self.assertEqual(new['parent'], 'Outer')
        self.assertEqual(new['level'], 1)
        self.assertEqual(drawing['projection']['edges'][new['edge']]['target'], new['id'])
        for kind in ('nodes', 'edges'):
            self.assertEqual({k:drawing['layout'][kind][k] for k in before['layout'][kind]}, before['layout'][kind])
        self.assertEqual(render(result, 'PC_SENSOR')['svg'], render(self.document, 'PC_SENSOR')['svg'])

    def test_semicolon_owner_crlf_keyword_and_literal_trivia_are_preserved(self):
        source = '// 🛰 keep exact\r\npackage P {\r\n    part def Owner; // retain trailing note\r\n    doc cseViews /* CSE-VIEWS/1.1\r\n{"views":[{"id":"PC","kind":"physical_composition","mode":"definitions","nodes":[{"id":"Owner","element":"P::Owner","parent":null,"level":0,"edge":null}]}]}\r\n*/\r\n}\r\n'
        d = CompositionDocument(source)
        result, request = self.create(d, owner_id=next(iter(d.registry)), new_name='part', short_id=None, view_id='PC')
        self.assertIn("    part def Owner {\r\n        part def 'part';\r\n    } // retain trailing note\r\n", result.source)
        self.assertTrue(result.source.startswith('// 🛰 keep exact\r\n'))
        self.assertEqual(result.registry[request['element_id']], 'P::Owner::part')
        self.assertEqual(result.source.count('\n'), result.source.count('\r\n'))

    def test_alias_short_name_identity_and_invalid_input_collisions_refuse(self):
        cases = [{'new_name':'Remote'}, {'short_id':'I'}, {'new_name':'Inner::device'},
                 {'element_id':self.owner}, {'element_id':'invalid'}, {'new_name':''}, {'new_name':'bad\nname'},
                 {'short_id':''}, {'view_id':'PC_SENSOR'}, {'expected_source_sha256':'stale'},
                 {'placement':{'box':{'x':56,'y':160,'width':360,'height':90},'points':[[416,205],[56,205]]}},
                 {'new_name':'🛰 spare'}]
        for request in cases:
            with self.subTest(request=request), self.assertRaises(EditError):
                self.create(**request)
        self.assertEqual(self.document.files['model.sysml'], REFERENCE_SOURCE)

    def test_native_boundary_corruption_cannot_edit_outside_the_owner(self):
        d = deepcopy(self.document)
        owner = next(row for row in d.parsed['part_definitions'] if row['qualified_name'] == 'ReferenceComposition::Outer')
        owner['source_span']['namespace_end_offset'] = 0
        with self.assertRaises(EditError) as error:
            self.create(d)
        self.assertEqual(error.exception.code, 'source_span')

    def test_manual_placement_and_authored_appearance_preserve_old_treatments(self):
        d = self.document
        before = render(d, 'PC_REFERENCE')
        appearance = {'version':'cse-diagram-appearance-2.0','kit':'engineering-palette-complete-05','view':'PC_REFERENCE',
            'nodes':{key:{'template':'palette-rectangle-white-plain','fill':'N0','stroke':'N100','text':'N100','align':'center'} for key in before['projection']['nodes']},
            'edges':{},'legend':['Frames show native owned definitions.']}
        records = {**d.linked_records,'appearance.json':{'kind':'composition_appearance','text':json.dumps(appearance)}}
        d = CompositionDocument(d.files, project_id=d.project_id, registry=d.registry, linked_records=records)
        placement = {'box':{'x':496,'y':520,'width':380,'height':110},'points':[[416,205],[446,205],[446,575],[496,575]]}
        result, request = self.create(d, placement=placement)
        drawing = render(result, 'PC_REFERENCE')
        key = next(k for k,v in drawing['projection']['nodes'].items() if v['element_id'] == request['element_id'])
        self.assertEqual(drawing['layout']['nodes'][key], placement['box'])
        saved = json.loads(result.linked_records['appearance.json']['text'])
        self.assertEqual({k:saved['nodes'][k] for k in appearance['nodes']}, appearance['nodes'])
        self.assertEqual(saved['legend'], appearance['legend'])

    def test_source_cli_returns_all_model_and_presentation_candidates(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as folder:
            p = Path(folder)/'bundle.json'
            p.write_text(json.dumps({'version':'cse-composition-bundle-1','models':self.document.files,'linked_records':self.document.linked_records}))
            element = str(uuid4())
            run = subprocess.run([sys.executable,'-B',str(ROOT/'scripts/composition_edit.py'),'create-definition','--bundle',str(p),
                '--project-id',self.document.project_id,'--owner-id',self.owner,'--element-id',element,'--name','SpareModule',
                '--view-id','PC_REFERENCE','--expected-bundle-sha256',self.document.revision],capture_output=True,text=True,check=True)
            report = json.loads(run.stdout)
            self.assertEqual(report['registry'][element], 'ReferenceComposition::Outer::SpareModule')
            self.assertIn('presentation/PC_REFERENCE.layout.json', report['linked_records'])
            self.assertEqual(json.loads(p.read_text())['models'], self.document.files)

    def test_session_preview_atomic_save_retry_reopen_and_restore(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as folder:
            project,_ = CompositionProject.create(Path(folder)/'project.git', self.document.files,
                project_id=self.document.project_id,request_id=str(uuid4()),linked_records=self.document.linked_records)
            session = CompositionSession(project,'PC_REFERENCE')
            initial = project.snapshot()
            request = {'operation':'create_definition','request_id':str(uuid4()),'expected_revision':1,'owner_id':self.owner,
                       'element_id':str(uuid4()),'new_name':'SpareModule','short_id':None,'view_id':'PC_REFERENCE','placement':None}
            preview = session.preview(request)
            self.assertIn('SpareModule', preview['candidate_svg'])
            self.assertEqual(preview['created_element']['element_id'], request['element_id'])
            self.assertEqual(project.head(), initial['commit'])
            first = session.apply(request)['receipt']
            self.assertEqual(session.apply(request)['receipt'], first)
            saved = CompositionProject(project.repository).snapshot()
            self.assertEqual(saved['revision'], 2)
            self.assertEqual(saved['document'].registry[request['element_id']], 'ReferenceComposition::Outer::SpareModule')
            self.assertEqual(saved['document'].linked_records['scope.json'], self.scope)
            with self.assertRaises(EditError):
                project.transact({**request,'request_id':str(uuid4()),'element_id':str(uuid4())})
            renamed = session.apply({'operation':'rename','request_id':str(uuid4()),'expected_revision':2,
                'element_id':request['element_id'],'new_name':'ModuleRenamed'})['receipt']
            self.assertEqual(renamed['revision'], 3)
            self.assertEqual(project.snapshot()['document'].registry[request['element_id']], 'ReferenceComposition::Outer::ModuleRenamed')
            restored = session.apply({'operation':'restore','request_id':str(uuid4()),'expected_revision':3,'target_revision':1})['receipt']
            self.assertEqual(restored['revision'], 4)
            final = CompositionProject(project.repository).snapshot()
            self.assertEqual(final['document'].files, initial['document'].files)
            self.assertEqual(final['document'].registry, initial['document'].registry)
            self.assertEqual(final['document'].linked_records, initial['document'].linked_records)
            self.assertEqual(session.apply(request)['receipt'], first)
            self.assertEqual(project.snapshot()['revision'], 4)

    def test_concurrent_exact_creation_retry_publishes_one_identity_and_receipt(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as folder:
            project,_ = CompositionProject.create(Path(folder)/'project.git',self.document.files,
                project_id=self.document.project_id,request_id=str(uuid4()),linked_records=self.document.linked_records)
            request = {'operation':'create_definition','request_id':str(uuid4()),'expected_revision':1,'owner_id':self.owner,
                       'element_id':str(uuid4()),'new_name':'ConcurrentSpare','short_id':None,'view_id':'PC_REFERENCE','placement':None}
            with ThreadPoolExecutor(max_workers=2) as workers:
                results = list(workers.map(lambda _:CompositionProject(project.repository).transact(request), range(2)))
            self.assertEqual(results[0], results[1])
            saved = project.snapshot()
            self.assertEqual(saved['revision'], 2)
            self.assertEqual(len(project.history()), 2)
            self.assertEqual(len(saved['document'].registry), len(self.document.registry)+1)
            self.assertEqual(saved['document'].registry[request['element_id']], 'ReferenceComposition::Outer::ConcurrentSpare')


if __name__ == '__main__':
    unittest.main()
