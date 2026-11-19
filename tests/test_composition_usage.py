"""Source, ownership/type, presentation and durable-history controls for usages."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
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


class UsageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT/'tests/fixtures/composition-role-inspection.json').read_text())
        cls.case = next(c for c in cls.fixture['cases'] if c['id'] == 'inherited')
        cls.records = {'scope.json': {'kind': 'retained_configuration', 'text': cls.case['retained_scope_text']}}
        cls.document = CompositionDocument(cls.case['models'], project_id=cls.fixture['project_id'], linked_records=cls.records)

    def identity(self, name, document=None):
        return next(k for k, v in (document or self.document).registry.items() if v == name)

    def options(self, document=None, **changes):
        d = document or self.document
        result = dict(owner_id=self.identity('Composition::current', d), element_id=str(uuid4()),
            new_name='spare', short_id='SPARE', type_id=self.identity('Composition::Sensor', d),
            is_composite=True, multiplicity=None, view_id='PC_CONTEXT', placement=None,
            expected_source_sha256=d.revision)
        result.update(changes)
        return result

    def test_composite_usage_adds_one_declaration_frame_and_original_kit_route(self):
        d = self.document; options = self.options(); before = render(d, 'PC_CONTEXT')
        candidate = d.create_usage(**options); drawing = render(candidate, 'PC_CONTEXT')
        row = next(r for r in candidate.inspect()['elements'] if r['element_id'] == options['element_id'])
        self.assertEqual((row['owner'], row['owner_kind'], row['type'], row['is_composite']),
                         ('Composition::current', 'PartUsage', 'Composition::Sensor', True))
        self.assertEqual(row['multiplicity'], {'status':'default', 'lower':1, 'upper':1})
        self.assertEqual(candidate.linked_records['scope.json'], self.records['scope.json'])
        self.assertEqual(candidate.configuration_reviews[0]['report']['checked'], ['$root', 'Sensor'])
        new = next(n for n in drawing['projection']['nodes'].values() if n['element_id'] == options['element_id'])
        self.assertEqual(new['parent'], 'Current')
        self.assertFalse(drawing['projection']['edges'][new['edge']]['arrowheads'])
        for kind in ('nodes', 'edges'):
            self.assertEqual({k:drawing['layout'][kind][k] for k in before['layout'][kind]}, before['layout'][kind])
        self.assertEqual(render(candidate, 'PC_DECLARATION')['svg'], render(d, 'PC_DECLARATION')['svg'])
        self.assertEqual({k:v for k,v in candidate.registry.items() if k != options['element_id']}, d.registry)

    def test_reference_definition_owned_and_unframed_owner_remain_declaration_rows(self):
        for changes in ({'is_composite':False},
                        {'owner_id':self.identity('Composition::Base'), 'view_id':'PC_DECLARATION'},
                        {'owner_id':self.identity('Composition::Base::sensor')}):
            with self.subTest(changes=changes):
                options = self.options(**changes); before = render(self.document, options['view_id'])
                candidate = self.document.create_usage(**options); drawing = render(candidate, options['view_id'])
                self.assertEqual(before['svg'], drawing['svg'])
                row = drawing['projection']['inspection']['occurrences']['decl:'+options['element_id']]
                self.assertEqual(row['native']['is_composite'], options['is_composite'])
                self.assertEqual(row['native']['owner'], self.document.registry[options['owner_id']])
                self.assertIsNone(row['frame_id'])
                self.assertEqual(candidate.linked_records, self.document.linked_records)

    def test_untyped_default_optional_zero_and_maximum_finite_bounds_are_explicit(self):
        for quantity in (None, {'lower':0,'upper':1}, {'lower':0,'upper':0},
                         {'lower':2147483646,'upper':2147483647}):
            with self.subTest(quantity=quantity):
                options = self.options(type_id=None, multiplicity=quantity)
                candidate = self.document.create_usage(**options)
                row = next(r for r in candidate.parsed['parts'] if r['name'] == 'spare')
                self.assertNotIn('type', row); self.assertEqual(row['types'], [])
                self.assertEqual(row['multiplicity'], {'status':'literal', **quantity} if quantity else {'status':'default','lower':1,'upper':1})
                drawing = render(candidate, 'PC_CONTEXT')
                if quantity is not None:
                    text = '['+(str(quantity['lower']) if quantity['lower']==quantity['upper'] else f"{quantity['lower']}..{quantity['upper']}")+']'
                    self.assertIn('>'+text+'<', drawing['svg'])

    def test_quoted_native_segments_cross_file_typing_and_crlf_trivia(self):
        views = '\r\ndoc cseViews /* CSE-VIEWS/1.1\r\n'+json.dumps({'views':[{'id':'PC','kind':'physical_composition','mode':'usages','nodes':[{'id':'Root','element':'Owners::root','parent':None,'level':0,'edge':None}]}]})+'\r\n*/\r\n'
        owner = '// 🛰 exact\r\npackage Owners {\r\n    part root; // exact tail\r\n'+views+'}\r\n'
        types = "// unchanged type file\r\npackage 'P::named' { part def 'part'; }\r\n"
        d = CompositionDocument({'owner.sysml':owner, 'types.sysml':types})
        options = dict(owner_id=self.identity('Owners::root',d), element_id=str(uuid4()), new_name="Sénsor's::spare",
            short_id=None, type_id=self.identity("'P::named'::part",d), is_composite=True, multiplicity={'lower':2,'upper':2},
            view_id='PC', placement=None, expected_source_sha256=d.revision)
        candidate = d.create_usage(**options)
        self.assertEqual(candidate.files['types.sysml'], types)
        self.assertIn("part 'Sénsor\\'s::spare' [2] : 'P::named'::'part';", candidate.files['owner.sysml'])
        self.assertIn('} // exact tail\r\n', candidate.files['owner.sysml'])
        self.assertEqual(candidate.files['owner.sysml'].count('\n'), candidate.files['owner.sysml'].count('\r\n'))
        self.assertEqual(next(r['type'] for r in candidate.parsed['parts'] if r['name']==options['new_name']), "'P::named'::part")

    def test_invalid_identity_typing_bounds_and_source_names_refuse(self):
        cases = [{'owner_id':'missing'}, {'element_id':self.identity('Composition::Sensor')}, {'element_id':'bad'},
            {'new_name':''}, {'new_name':'line\nbreak'}, {'new_name':'🛰 spare'}, {'short_id':''},
            {'owner_id':self.identity('Composition::Base'),'new_name':'sensor'},
            {'owner_id':self.identity('Composition::Base'),'short_id':'SENSOR'},
            {'type_id':'missing'}, {'type_id':self.identity('Composition::current')}, {'is_composite':1},
            {'multiplicity':{'lower':True,'upper':1}}, {'multiplicity':{'lower':2,'upper':1}},
            {'multiplicity':{'lower':0,'upper':2147483648}}, {'multiplicity':{}}, {'expected_source_sha256':'stale'}]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(EditError):
                self.document.create_usage(**self.options(**change))
        self.assertEqual(self.document.files, self.case['models'])

    def test_corrupt_native_anchor_or_type_reference_cannot_change_another_element(self):
        for target, field, value in [('Composition::current','namespace_end_offset',0),
                                     ('Composition::Sensor','qualified_reference','Composition::Assembly')]:
            d = deepcopy(self.document)
            for group in ('parts','part_definitions'):
                for row in d.parsed[group]:
                    if row['qualified_name']==target: row['source_span'][field]=value
            with self.subTest(field=field), self.assertRaises(EditError):
                d.create_usage(**self.options(d))

    def test_declaration_placement_overlap_and_other_view_fail_atomically(self):
        placement = {'box':{'x':56,'y':160,'width':360,'height':90},'points':[[416,205],[56,205]]}
        for changes in ({'placement':placement}, {'is_composite':False,'placement':placement},
                        {'owner_id':self.identity('Composition::Base'),'view_id':'PC_DECLARATION','placement':placement},
                        {'view_id':'missing'}):
            with self.subTest(changes=changes), self.assertRaises(EditError):
                self.document.create_usage(**self.options(**changes))

    def test_creation_does_not_repair_unknown_or_failed_selected_claims(self):
        for name, expected in [('optional','unknown'),('suppressed','fail')]:
            case = next(c for c in self.fixture['cases'] if c['id']==name)
            d = CompositionDocument(case['models'], linked_records={'scope.json':{'kind':'retained_configuration','text':case['retained_scope_text']}})
            candidate = d.create_usage(**self.options(d))
            self.assertEqual(candidate.linked_records['scope.json'], d.linked_records['scope.json'])
            self.assertEqual(candidate.configuration_reviews[0]['report']['status'], expected)

    def test_native_owned_alias_collision_is_preserved_and_refused(self):
        source = self.case['models']['model.sysml'].replace('part current : Assembly;', 'part current : Assembly { alias Taken for Composition::Sensor; }')
        d = CompositionDocument({'model.sysml':source}, linked_records=self.records)
        with self.assertRaises(EditError) as error:
            d.create_usage(**self.options(d,new_name='Taken'))
        self.assertEqual(error.exception.code,'name_collision')

    def test_comment_delimiters_preserve_native_names_in_frames_and_rename_bindings(self):
        options = self.options(new_name='spare*/unit')
        candidate = self.document.create_usage(**options)
        drawing = render(candidate, 'PC_CONTEXT')
        self.assertEqual(next(row['native']['name'] for row in drawing['projection']['nodes'].values()
            if row['element_id']==options['element_id']), 'spare*/unit')
        doc = next(row for row in candidate.parsed['documents'] if row.get('name')=='cseViews')
        self.assertNotIn('*/', doc['body'])
        renamed = candidate.rename(options['element_id'], 'spare/*renamed', expected_source_sha256=candidate.revision)
        self.assertEqual(next(row['native']['name'] for row in render(renamed,'PC_CONTEXT')['projection']['nodes'].values()
            if row['element_id']==options['element_id']), 'spare/*renamed')
        self.assertEqual(renamed.linked_records['scope.json'], self.records['scope.json'])
        definition = self.document.create_definition(self.identity('Composition::Base'),str(uuid4()),
            'module/*nested',None,'PC_DECLARATION',None,expected_source_sha256=self.document.revision)
        self.assertIn('module/*nested', render(definition,'PC_DECLARATION')['svg'])

    def test_native_comment_encoding_does_not_change_standalone_linked_json(self):
        from verifier.composition_records import rebind_document, rebind_json, strict_json
        body = next(row['body'] for row in self.document.parsed['documents'] if row.get('name')=='cseViews')
        payload = body.split('\n',1)[1]
        replacement = "Composition::'current*/unit'"
        mapped = lambda value: replacement if value=='Composition::current' else value
        standalone, standalone_findings = rebind_json(payload,'views',mapped)
        embedded, embedded_findings = rebind_document(body,'cseViews',mapped)
        self.assertEqual(strict_json(standalone),strict_json(embedded.split('\n',1)[1]))
        self.assertEqual(standalone_findings,embedded_findings)
        self.assertIn('*/',standalone)
        self.assertNotIn('*/',embedded)
        self.assertEqual(standalone,payload.replace('Composition::current',replacement))

    def test_cli_candidate_matches_the_shared_operation_without_mutating_input(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        options = self.options(is_composite=False,multiplicity={'lower':0,'upper':2})
        candidate = self.document.create_usage(**options)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as tmp:
            p = Path(tmp)/'bundle.json'; bundle = {'version':'cse-composition-bundle-1','models':self.document.files,'linked_records':self.records}
            raw = json.dumps(bundle);p.write_text(raw)
            result = subprocess.run([sys.executable,'-B',str(ROOT/'scripts/composition_edit.py'),'create-usage','--bundle',str(p),
                '--project-id',self.document.project_id,'--owner-id',options['owner_id'],'--element-id',options['element_id'],
                '--name','spare','--short-id','SPARE','--type-id',options['type_id'],'--usage-kind','reference','--lower','0','--upper','2',
                '--view-id','PC_CONTEXT','--expected-bundle-sha256',self.document.revision],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr);report=json.loads(result.stdout)
            self.assertEqual(report['files'],candidate.files);self.assertEqual(report['registry'],candidate.registry)
            self.assertEqual(p.read_text(),raw)

    def test_session_receipt_retry_reopen_restore_and_concurrent_creation(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as tmp:
            project,_ = CompositionProject.create(Path(tmp)/'project.git',self.document.files,project_id=self.document.project_id,
                request_id=str(uuid4()),linked_records=self.records)
            options = self.options();options.pop('expected_source_sha256')
            request = dict(operation='create_usage',request_id=str(uuid4()),expected_revision=1,**options)
            session = CompositionSession(project,'PC_CONTEXT'); initial = project.snapshot();old_svg=render(initial['document'],'PC_CONTEXT')['svg']
            preview = session.preview(request);self.assertEqual(project.head(),initial['commit'])
            self.assertEqual(preview['created_element']['element_id'],options['element_id'])
            with ThreadPoolExecutor(max_workers=2) as pool:
                receipts=list(pool.map(lambda _:CompositionProject(project.repository).transact(request),range(2)))
            self.assertEqual(receipts[0],receipts[1]);self.assertEqual(session.apply(request)['receipt'],receipts[0])
            self.assertEqual(CompositionProject(project.repository).snapshot()['revision'],2)
            with self.assertRaises(EditError): project.transact({**request,'request_id':str(uuid4()),'element_id':str(uuid4())})
            restored=session.apply({'operation':'restore','request_id':str(uuid4()),'expected_revision':2,'target_revision':1})['receipt']
            self.assertEqual(restored['revision'],3);final=CompositionProject(project.repository).snapshot()
            self.assertEqual((final['document'].files,final['document'].registry,final['document'].linked_records),
                             (initial['document'].files,initial['document'].registry,initial['document'].linked_records))
            self.assertEqual(render(final['document'],'PC_CONTEXT')['svg'],old_svg)
            self.assertEqual(session.apply(request)['receipt'],receipts[0]);self.assertEqual(project.snapshot()['revision'],3)


if __name__ == '__main__':
    unittest.main()
