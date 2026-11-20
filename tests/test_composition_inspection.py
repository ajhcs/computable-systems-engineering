"""Native role/context/identity and saved-project inspection acceptance controls."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verifier.composition_edit import CompositionDocument,EditError
from verifier.composition_project import CompositionProject
from verifier.composition_view import project,render,write_artifacts,check_artifacts
from verifier.composition_inspection import page

FIXTURES=json.loads((ROOT/'tests/fixtures/composition-role-inspection.json').read_text())


def document(case,records=None):
    return CompositionDocument(case['models'],project_id=FIXTURES['project_id'],linked_records=records or
        {'scope.json':{'kind':'retained_configuration','text':case['retained_scope_text']}})


def scoped_rows(inspection,kind='selected_role'):
    return [r for r in inspection['occurrences'].values() if r['origin']==kind]


class InspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={c['id']:c for c in FIXTURES['cases']}
        cls.docs={key:document(case) for key,case in cls.cases.items()}

    def test_expected_scope_results_and_native_owners_are_retained(self):
        for key,doc in self.docs.items():
            with self.subTest(case=key):
                inspection=project(doc,'PC_CONTEXT')['inspection'];scope=inspection['scopes'][0];want=self.cases[key]['expected']
                self.assertEqual(scope['report']['status'],want['status'])
                self.assertEqual(set(scope['report']['checked']),set(want['checked']))
                self.assertEqual(scope['report'],doc.configuration_reviews[0]['report'])
                for role in scoped_rows(inspection):
                    self.assertEqual(role['role']['checked'],role['role']['id'] in want['checked'])
                    self.assertEqual(role['role']['selected_parent']['native_name'],'Composition::current')
                    if role['native']:
                        self.assertEqual(role['native']['owner'],'Composition::current' if key=='explicit_override' else 'Composition::Base')
                    if role['role']['checked']:
                        self.assertEqual(role['role']['membership'],'usage_owned' if key=='explicit_override' else 'inherited')
                    else:self.assertIsNone(role['role']['membership'])
        control=FIXTURES['ownership_negative_control']
        with self.assertRaisesRegex(ValueError,'native declaring owner'):
            project(CompositionDocument(control['models']),control['view_id'])

    def test_occurrences_share_native_identity_without_becoming_ownership_children(self):
        doc=self.docs['inherited'];projection=project(doc,'PC_CONTEXT');inspection=projection['inspection']
        role=scoped_rows(inspection)[0];decl=inspection['occurrences']['decl:'+role['element_id']]
        self.assertNotEqual(role['id'],decl['id'])
        self.assertEqual(role['element_id'],decl['element_id'])
        self.assertEqual(decl['native']['owner_kind'],'PartDefinition')
        self.assertEqual(decl['native']['source_multiplicity'],'[2]')
        self.assertEqual(set(projection['nodes']),{'Current'})
        self.assertEqual(projection['edges'],{})
        self.assertEqual(inspection['counts']['declarations'],len(doc.registry))
        self.assertEqual(set(inspection['declarations']),{'decl:'+k for k in doc.registry})
        self.assertEqual(inspection['occurrences']['Current']['origin'],'frame')
        self.assertEqual(inspection['occurrences']['Current']['frame_id'],'Current')
        self.assertEqual({k:inspection['occurrences']['Current'][k] for k in projection['nodes']['Current']},
                         projection['nodes']['Current'])
        self.assertIsNone(decl['frame_id'])
        original=doc.inspect();decl['native']['name']='tampered';inspection['scopes'][0]['report']['status']='pass-by-client'
        self.assertEqual(doc.inspect(),original)

    def test_missing_binding_mixed_results_and_external_reference_stay_distinct(self):
        missing=scoped_rows(project(self.docs['missing'],'PC_CONTEXT')['inspection'])[0]
        self.assertIsNone(missing['element_id']);self.assertIsNone(missing['native']);self.assertIsNone(missing['kind'])
        self.assertEqual(missing['element'],'Composition::Base::absent')
        self.assertEqual(missing['role']['findings'][0]['rule'],'native_identity')
        mixed=project(self.docs['mixed'],'PC_CONTEXT')['inspection'];rows={r['role']['id']:r for r in scoped_rows(mixed)}
        self.assertTrue(rows['Spare']['role']['checked']);self.assertFalse(rows['Sensor']['role']['checked'])
        self.assertEqual(mixed['scopes'][0]['report']['status'],'unknown')
        external=scoped_rows(project(self.docs['external'],'PC_CONTEXT')['inspection'],'external_role')[0]
        self.assertIsNone(external['role']['selected_parent']);self.assertEqual(external['native']['owner_kind'],'Package')
        self.assertFalse(external['native']['is_composite']);self.assertEqual(external['native']['owner'],'Composition')

    def test_quoted_names_and_multiple_scope_files_bind_exactly(self):
        case=deepcopy(self.cases['inherited']);case['models']['model.sysml']=case['models']['model.sysml'].replace('sensor [2]',"'sensor::channel' [2]")
        scope=json.loads(case['retained_scope_text']);scope['selected_roles']['Sensor']['native_name']="Composition::Base::'sensor::channel'"
        text=json.dumps(scope,indent=2)+'\n'
        records={name:{'kind':'retained_configuration','text':text} for name in ('scope-a.json','scope-b.json')}
        doc=document(case,records);inspection=project(doc,'PC_CONTEXT')['inspection'];roles=scoped_rows(inspection)
        self.assertEqual(len(roles),2);self.assertNotEqual(roles[0]['id'],roles[1]['id'])
        self.assertEqual(roles[0]['element_id'],roles[1]['element_id'])
        self.assertEqual(roles[0]['native']['name'],'sensor::channel')
        self.assertEqual(roles[0]['native']['owner'],'Composition::Base')
        self.assertEqual({r['role']['file'] for r in roles},set(records))
        self.assertTrue(all(r['role']['checked'] for r in roles))
        self.assertEqual({k:v['text'] for k,v in doc.linked_records.items()},{k:v['text'] for k,v in records.items()})

    def test_pages_cover_large_declaration_sets_and_refuse_stale_or_invalid_reads(self):
        case=deepcopy(self.cases['inherited']);case['models']['model.sysml']=case['models']['model.sysml'].replace('part def Base {','part def Base {\n'+''.join(f'part extra{i} : Sensor;\n' for i in range(115)))
        doc=document(case);inspection=project(doc,'PC_CONTEXT')['inspection'];offset=0;ids=[]
        while offset is not None:
            p=page(inspection,origin='declaration',offset=offset,limit=25,expected_bundle_sha256=doc.revision)
            ids += [r['id'] for r in p['items']];offset=p['next_offset']
        self.assertGreater(len(ids),100);self.assertEqual(ids,inspection['declarations']);self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(inspection['scopes'][0]['report']['status'],'pass')
        for kwargs in ({'expected_bundle_sha256':'stale'},{'offset':True},{'limit':101},{'origin':'invented'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):page(inspection,**kwargs)
        self.assertEqual(page(inspection,offset=10000)['items'],[])

    def custom_inspection(self, declarations, roles):
        case=deepcopy(self.cases['inherited'])
        source=case['models']['model.sysml'];views=source[source.index('    doc cseViews'):]
        case['models']['model.sysml']='// Synthetic inspection control.\npackage Composition {\n'+declarations+'\n'+views
        scope=json.loads(case['retained_scope_text']);scope['selected_roles']=roles
        case['retained_scope_text']=json.dumps(scope,indent=2)+'\n'
        return project(document(case),'PC_CONTEXT')['inspection']

    def test_nested_type_and_usage_owned_members_keep_selected_parent_separate(self):
        source='''part def Sensor; part def Replacement :> Sensor;
part def Module { part sensor : Sensor; }
part def Base { part module : Module; }
part def Assembly :> Base; part current : Assembly;'''
        roles={'Module':{'parent':'$root','native_name':'Composition::Base::module','type':'Composition::Module'},
               'Sensor':{'parent':'Module','native_name':'Composition::Module::sensor','type':'Composition::Sensor'}}
        inspection=self.custom_inspection(source,roles);rows={r['role']['id']:r for r in scoped_rows(inspection)}
        self.assertEqual(inspection['scopes'][0]['report']['status'],'pass')
        self.assertEqual(rows['Module']['role']['membership'],'inherited')
        self.assertEqual(rows['Sensor']['role']['membership'],'type_owned')
        self.assertEqual(rows['Sensor']['native']['owner'],'Composition::Module')
        self.assertEqual(rows['Sensor']['role']['selected_parent']['native_name'],'Composition::Base::module')
        overridden=source.replace('part module : Module;',
            'part module : Module { part sensor : Replacement [1] redefines Module::sensor; }')
        historical=self.custom_inspection(overridden,roles)
        self.assertEqual(historical['scopes'][0]['report']['status'],'fail')
        sensor=next(r for r in scoped_rows(historical) if r['role']['id']=='Sensor')
        self.assertIsNone(sensor['role']['membership'])
        self.assertEqual([(f['status'],f['rule']) for f in sensor['role']['findings']],[('fail','role_redefined')])
        roles['Sensor'].update(native_name='Composition::Base::module::sensor',type='Composition::Replacement')
        selected=self.custom_inspection(overridden,roles)
        self.assertEqual(selected['scopes'][0]['report']['status'],'pass')
        sensor=next(r for r in scoped_rows(selected) if r['role']['id']=='Sensor')
        self.assertEqual(sensor['role']['membership'],'usage_owned')
        self.assertEqual(sensor['native']['owner'],sensor['role']['selected_parent']['native_name'])
        self.assertEqual(sensor['native']['redefines'],['Composition::Module::sensor'])

    def test_unsupported_parent_specialization_and_variation_do_not_get_membership(self):
        source='''part def Sensor; part def Replacement :> Sensor;
part def Module { part sensor : Sensor; }
part def Base { part module : Module { part sensor : Replacement [1] redefines Module::sensor; } }
part def Assembly :> Base { part module : Module [1] redefines Base::module; }
part current : Assembly;'''
        roles={'Module':{'parent':'$root','native_name':'Composition::Assembly::module','type':'Composition::Module'},
               'Sensor':{'parent':'Module','native_name':'Composition::Module::sensor','type':'Composition::Sensor'}}
        inspection=self.custom_inspection(source,roles);sensor=next(r for r in scoped_rows(inspection) if r['role']['id']=='Sensor')
        self.assertEqual(inspection['scopes'][0]['report']['status'],'unsupported')
        self.assertEqual([(f['status'],f['rule']) for f in sensor['role']['findings']],[('unsupported','parent_context')])
        self.assertFalse(sensor['role']['checked']);self.assertIsNone(sensor['role']['membership'])
        variant='''part def Sensor; variation part def Base { variant part sensor : Sensor; }
part def Assembly :> Base; part current : Assembly;'''
        inspection=self.custom_inspection(variant,{'Sensor':{'parent':'$root','native_name':'Composition::Base::sensor','type':'Composition::Sensor'}})
        self.assertEqual(inspection['scopes'][0]['report']['status'],'unsupported')
        row=scoped_rows(inspection)[0]
        self.assertTrue(row['native']['is_variant']);self.assertFalse(row['role']['checked'])
        self.assertIsNone(row['role']['membership'])

    def test_saved_role_edit_export_restore_and_retry_keep_scope_and_identity(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as folder:
            folder=Path(folder);case=self.cases['inherited'];records={'scope.json':{'kind':'retained_configuration','text':case['retained_scope_text']}}
            p,_=CompositionProject.create(folder/'project.git',case['models'],linked_records=records,project_id=FIXTURES['project_id'],request_id=str(uuid4()))
            first=p.snapshot();initial=project(first['document'],'PC_CONTEXT')['inspection'];role=scoped_rows(initial)[0];svg=render(first['document'],'PC_CONTEXT')['svg']
            write_artifacts(first,'PC_CONTEXT',folder/'export')
            request={'operation':'set_multiplicity','request_id':str(uuid4()),'expected_revision':1,'element_id':role['element_id'],'lower':0,'upper':1}
            saved=p.transact(request);again=p.transact(request);self.assertEqual(saved,again)
            snapshot=CompositionProject(p.repository).snapshot();now=project(snapshot['document'],'PC_CONTEXT')['inspection'];updated=scoped_rows(now)[0]
            self.assertEqual(updated['id'],role['id']);self.assertEqual(updated['element_id'],role['element_id'])
            self.assertEqual(updated['native']['source_multiplicity'],'[0..1]');self.assertFalse(updated['role']['checked'])
            self.assertEqual(snapshot['document'].linked_records,records);self.assertEqual(now['scopes'][0]['report']['status'],'unknown')
            self.assertEqual(render(snapshot['document'],'PC_CONTEXT')['svg'],svg)
            with self.assertRaises(ValueError):check_artifacts(snapshot,'PC_CONTEXT',folder/'export')
            p.transact({'operation':'restore','request_id':str(uuid4()),'expected_revision':2,'target_revision':1})
            restored=p.snapshot();self.assertEqual(restored['revision'],3)
            self.assertEqual(project(restored['document'],'PC_CONTEXT')['inspection'],initial)
            self.assertEqual(p.transact(request),saved);self.assertEqual(p.snapshot()['revision'],3)

    def test_shared_rename_retains_failed_scope_instead_of_rebinding_selection(self):
        doc=self.docs['inherited'];role=scoped_rows(project(doc,'PC_CONTEXT')['inspection'])[0]
        updated=doc.rename(role['element_id'],'sensorArray',expected_source_sha256=doc.revision)
        inspection=project(updated,'PC_CONTEXT')['inspection'];after=scoped_rows(inspection)[0]
        self.assertEqual(after['id'],role['id']);self.assertIsNone(after['element_id'])
        self.assertEqual(inspection['scopes'][0]['report']['status'],'fail')
        self.assertEqual(updated.registry[role['element_id']],'Composition::Base::sensorArray')
        self.assertEqual(inspection['occurrences']['decl:'+role['element_id']]['native']['name'],'sensorArray')
        self.assertEqual(updated.linked_records['scope.json'],doc.linked_records['scope.json'])

    def test_cli_inspection_page_uses_current_snapshot_and_rejects_old_revision(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as folder:
            case=self.cases['inherited'];records={'scope.json':{'kind':'retained_configuration','text':case['retained_scope_text']}}
            p,_=CompositionProject.create(Path(folder)/'project.git',case['models'],linked_records=records,project_id=FIXTURES['project_id'],request_id=str(uuid4()))
            cmd=[sys.executable,'-B',str(ROOT/'scripts/composition_project.py'),'inspect-view','--project',str(p.repository),'--view-id','PC_CONTEXT','--origin','selected_role','--limit','1']
            run=subprocess.run(cmd,capture_output=True,text=True,check=True);report=json.loads(run.stdout)
            self.assertEqual(report['revision'],1);self.assertEqual(report['inspection_page']['items'][0]['native']['owner'],'Composition::Base')
            role=report['inspection_page']['items'][0];p.transact({'operation':'set_multiplicity','request_id':str(uuid4()),'expected_revision':1,'element_id':role['element_id'],'lower':1,'upper':2})
            stale=subprocess.run(cmd+['--expected-revision','1'],capture_output=True,text=True)
            self.assertEqual(stale.returncode,1);self.assertEqual(json.loads(stale.stdout)['error']['code'],'stale_revision')


if __name__=='__main__':unittest.main()
