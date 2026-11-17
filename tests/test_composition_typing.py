"""Exact native typing deltas, source trivia and durable project controls."""
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
from verifier.composition_view import render, write_artifacts, check_artifacts


class TypingTests(unittest.TestCase):
    prefix = 'package P { part def Device; part def Other; '

    @classmethod
    def setUpClass(cls):
        fixture = json.loads((ROOT/'tests/fixtures/composition-role-inspection.json').read_text())
        cls.project_id = fixture['project_id']
        case = fixture['cases'][0]
        cls.models = {name:text.replace('part def Sensor;', 'part def Sensor;\n    part def Other;')
                      for name, text in case['models'].items()}
        cls.records = {'scope.json':{'kind':'retained_configuration', 'text':case['retained_scope_text']}}
        cls.document = CompositionDocument(cls.models, project_id=cls.project_id, linked_records=cls.records)

    def identity(self, document, name):
        return next(k for k, v in document.registry.items() if v == name)

    def change(self, document, target, names):
        result = document.set_types(self.identity(document, target),
            [self.identity(document, name) for name in names], expected_source_sha256=document.revision)
        expected = fingerprint(document.parsed)
        for row in expected['parts']:
            if row['qualified_name'] == target:
                row['types'] = names
                if len(names) == 1:
                    row['type'] = names[0]
                else:
                    row.pop('type', None)
        self.assertEqual(fingerprint(result.parsed), expected)
        self.assertEqual(result.registry, document.registry)
        self.assertEqual(result.linked_records, document.linked_records)
        return result

    def test_add_retarget_remove_and_multiple_types_keep_other_native_facts(self):
        for declaration, names in [
                ('part role [2];', ['P::Device', 'P::Other']),
                ('part role : Device [2];', ['P::Other']),
                ('part role [2] : Device;', []),
                ('ref part role [0..2] : Device, Other;', ['P::Other']),
                ('part role : Device : Other;', ['P::Other', 'P::Device']),
                ('part role defined by Device;', []),
                ('part role : Device, Other;', [])]:
            with self.subTest(declaration=declaration, types=names):
                document = CompositionDocument(self.prefix+declaration+' }')
                self.change(document, 'P::role', names)

    def test_hidden_notes_unicode_crlf_and_untouched_file_bytes(self):
        source = "// 🛰 exact\r\npackage P {\r\n part 'rôle' [2] defined // delimiter note\r\n by // type note\r\n Types::Device; // tail\r\n}\r\n"
        types = "// exact types\r\npackage Types { part def Device; part def Other; }\r\n"
        document = CompositionDocument({'owner.sysml':source, 'types.sysml':types})
        result = self.change(document, "P::'rôle'", ['Types::Other'])
        self.assertEqual(result.files['types.sysml'], types)
        self.assertEqual(result.files['owner.sysml'], source.replace('Types::Device', 'Types::Other'))
        removed = self.change(document, "P::'rôle'", [])
        self.assertEqual(removed.files['owner.sysml'], source.replace('defined', '').replace('by //', ' //').replace('Types::Device', ''))

    def test_native_quoted_keyword_segments_and_comment_marker_names(self):
        source = "package 'P::named' { part def 'part'; part def 'Other*/type'; part role : 'part'; }"
        document = CompositionDocument(source)
        result = self.change(document, "'P::named'::role", ["'P::named'::'Other*/type'"])
        self.assertIn(": 'P::named'::'Other*/type'", result.source)
        document = CompositionDocument("package 'part' { part def 'state'; part def Other; part role : Other; }")
        self.assertIn(": 'part'::'state'", self.change(document, 'part::role', ['part::state']).source)

    def test_interleaved_redefinition_and_nested_declarations_are_preserved(self):
        source = 'package P { part def Device; part def Other :> Device; part def Base {part original : Device;} part def Derived :> Base {part role : Device redefines Base::original : Other {part nested : Device;}} }'
        document = CompositionDocument(source)
        result = self.change(document, 'P::Derived::role', ['P::Other'])
        self.assertIn('redefines Base::original', result.source)
        self.assertIn('{part nested : Device;}', result.source)

    def test_retained_configuration_reports_failure_without_scope_or_geometry_changes(self):
        document = self.document
        result = self.change(document, 'Composition::Base::sensor', ['Composition::Other'])
        self.assertEqual(document.configuration_reviews[0]['report']['status'], 'pass')
        self.assertEqual(result.configuration_reviews[0]['report']['status'], 'fail')
        self.assertEqual(result.configuration_reviews[0]['report']['findings'], [{'id':'Sensor',
            'rule':'selected_type', 'status':'fail', 'detail':'Selected role has a different or ambiguous direct type'}])
        for view in ('PC_CONTEXT', 'PC_DECLARATION'):
            self.assertEqual(render(result, view)['svg'], render(document, view)['svg'])
            self.assertEqual(render(result, view)['layout'], render(document, view)['layout'])

    def test_invalid_input_stale_kind_and_duplicate_choices_refuse(self):
        document = self.document
        target = self.identity(document, 'Composition::Base::sensor')
        type_id = self.identity(document, 'Composition::Sensor')
        for element_id, choices, digest in [(target, None, document.revision), (target, {}, document.revision),
                (target, [True], document.revision), (target, [type_id, type_id], document.revision),
                (target, ['missing'], document.revision), (target, [target], document.revision),
                ('missing', [], document.revision), (type_id, [], document.revision), (target, [], 'stale')]:
            with self.subTest(choices=choices), self.assertRaises(EditError):
                document.set_types(element_id, choices, expected_source_sha256=digest)
        self.assertEqual(document.files, self.models)

    def test_native_anchor_corruption_cannot_remove_other_tokens_or_relink_a_type(self):
        for field, value in [('status', 'unsupported'), ('target', 'Composition::Other'),
                ('prefix_tokens', [{'encoding':'utf16', 'offset':0, 'length':2, 'text':'//'}])]:
            document = deepcopy(self.document)
            row = next(r for r in document.parsed['parts'] if r['name']=='sensor')
            row['source_span']['typing_sources'][0][field] = value
            with self.subTest(field=field), self.assertRaises(EditError):
                self.change(document, 'Composition::Base::sensor', ['Composition::Other'])
        document = deepcopy(self.document)
        next(r for r in document.parsed['part_definitions'] if r['name']=='Other')['source_span']['qualified_reference']='Composition::Sensor'
        with self.assertRaises(EditError):
            self.change(document, 'Composition::Base::sensor', ['Composition::Other'])

    def test_identical_list_preserves_original_typing_spelling_exactly(self):
        document = CompositionDocument(self.prefix+'part role defined by Device : Other; }')
        self.assertIs(self.change(document, 'P::role', ['P::Device', 'P::Other']), document)

    def test_invalid_shapes_types_and_stale_inputs_refuse_without_source_changes(self):
        document=self.document;target=self.identity(document,'Composition::Base::sensor')
        definition=self.identity(document,'Composition::Sensor');usage=self.identity(document,'Composition::current')
        for choices in (None, {}, 'one', [True], [definition,definition], ['missing'], [usage], [definition]*129):
            with self.subTest(choices=choices), self.assertRaises(EditError):
                document.set_types(target,choices,expected_source_sha256=document.revision)
        for element,revision in [('missing',document.revision),(definition,document.revision),(target,'stale')]:
            with self.subTest(element=element,revision=revision), self.assertRaises(EditError):
                document.set_types(element,[],expected_source_sha256=revision)
        self.assertEqual(document.files,self.models)

    def test_missing_or_corrupt_native_typing_boundaries_cannot_edit_another_source_token(self):
        for mutation in ('status','delimiter','token','inventory'):
            document=deepcopy(self.document)
            row=next(r for r in document.parsed['parts']if r['qualified_name']=='Composition::Base::sensor')
            anchor=row['source_span']['typing_sources'][0]
            if mutation=='status':anchor['status']='unsupported'
            elif mutation=='delimiter':anchor['prefix_tokens'][0]['text']=','
            elif mutation=='token':anchor['reference_tokens'][0]['offset']=0
            else:row['source_span']['typing_sources']=[]
            with self.subTest(mutation=mutation), self.assertRaises(EditError):
                self.change(document,'Composition::Base::sensor',['Composition::Other'])

    def test_unnamed_redefinition_keeps_its_identity_when_explicit_typing_is_added(self):
        source='package P {part def Device;part def Other :> Device;part def Base {part role : Device;}part def Derived :> Base {part :>> Base::role;}}'
        document=CompositionDocument(source)
        result=self.change(document,'P::Derived::role',['P::Other'])
        self.assertIn(':>> Base::role',result.source)

    def test_source_cli_matches_native_operation_and_preserves_input(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        document = self.document
        target = self.identity(document, 'Composition::Base::sensor')
        choices = [self.identity(document, 'Composition::Other')]
        expected = self.change(document, 'Composition::Base::sensor', ['Composition::Other'])
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as folder:
            path=Path(folder)/'bundle.json'
            raw=json.dumps({'version':'cse-composition-bundle-1','models':document.files,'linked_records':document.linked_records})
            path.write_text(raw)
            run=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/composition_edit.py'),'set-types','--bundle',str(path),
                '--project-id',document.project_id,'--element-id',target,'--type-ids',json.dumps(choices),
                '--expected-bundle-sha256',document.revision],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertEqual(json.loads(run.stdout)['files'],expected.files)
            self.assertEqual(path.read_text(),raw)

    def test_preview_concurrent_retry_native_export_and_monotonic_restore(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as folder:
            project,_=CompositionProject.create(Path(folder)/'project.git',self.models,project_id=self.project_id,
                request_id=str(uuid4()),linked_records=self.records)
            initial=project.snapshot();document=initial['document'];session=CompositionSession(project,'PC_CONTEXT')
            request={'operation':'set_types','request_id':str(uuid4()),'expected_revision':1,
                'element_id':self.identity(document,'Composition::Base::sensor'),
                'type_ids':[self.identity(document,'Composition::Other')]}
            preview=session.preview(request)
            self.assertEqual(project.head(),initial['commit'])
            self.assertEqual(preview['edited_element']['native']['types'],['Composition::Other'])
            self.assertEqual(preview['candidate_svg'],render(document,'PC_CONTEXT')['svg'])
            with ThreadPoolExecutor(max_workers=2) as pool:
                receipts=list(pool.map(lambda _:CompositionProject(project.repository).transact(request),range(2)))
            self.assertEqual(receipts[0],receipts[1])
            self.assertEqual(CompositionSession(CompositionProject(project.repository),'PC_CONTEXT').apply(request)['receipt'],receipts[0])
            with self.assertRaises(EditError):
                project.transact({**request,'request_id':str(uuid4())})
            saved=project.snapshot();write_artifacts(saved,'PC_CONTEXT',Path(folder)/'export')
            check_artifacts(saved,'PC_CONTEXT',Path(folder)/'export')
            self.assertEqual(saved['revision'],2)
            restored=session.apply({'operation':'restore','request_id':str(uuid4()),'expected_revision':2,'target_revision':1})
            self.assertEqual(restored['receipt']['revision'],3)
            final=CompositionProject(project.repository).snapshot()
            self.assertEqual((final['document'].files,final['document'].registry,final['document'].linked_records),
                (document.files,document.registry,document.linked_records))
            self.assertEqual(session.apply(request)['receipt'],receipts[0])
            self.assertEqual(project.snapshot()['revision'],3)


if __name__ == '__main__':
    unittest.main()
