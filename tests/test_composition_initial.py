"""Independently expected native roots and no-replace first-publication recovery."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import EditError
from verifier.composition_initial import document_for, initialize, prepare, lookup, validate_request, _rename_noreplace
from verifier.composition_project import CompositionProject, request_digest
from verifier.composition_view import render, write_artifacts, check_artifacts


def request(**changes):
    return {'operation':'initialize_physical_project', 'request_id':str(uuid4()),
            'project_id':str(uuid4()), 'expected_revision':0, 'root_element_id':str(uuid4()),
            'root_kind':'definition', 'new_name':'System', 'short_id':None,
            'namespace_name':None, 'view_id':'PC', 'expected_bundle_sha256':None, **changes}


def checked_request(**changes):
    return prepare(request(**changes))[1]


class InitialTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT/'.tmp')
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def test_native_kinds_owners_short_ids_and_quoted_source_are_exact(self):
        for kind, package, name, short, qualified in [
                ('definition',None,'System',None,'System'),
                ('usage',None,'system',None,'system'),
                ('definition','Project','System','SYS','Project::System'),
                ('usage','Project','current','CURRENT','Project::current'),
                ('definition','P::named','part',None,"'P::named'::part"),
                ('usage','P*/named','Root*/part',None,"'P*/named'::'Root*/part'"),
                ('definition','Project','cseViews',None,'Project::cseViews')]:
            with self.subTest(kind=kind,package=package,name=name):
                intent=request(root_kind=kind, namespace_name=package,new_name=name,short_id=short)
                document=document_for(intent)
                self.assertEqual(document.registry,{intent['root_element_id']:qualified})
                row=document.inspect()['elements'][0]
                self.assertEqual((row['name'],row.get('id')),(name,short))
                self.assertEqual(row.get('owner_kind'),'Namespace' if package is None else 'Package')
                self.assertEqual(row.get('owner'),None if package is None else "'P::named'" if package=='P::named' else "'P*/named'" if package=='P*/named' else package)
                self.assertEqual(row['source_location']['file'],'model.sysml')
                self.assertEqual(document.configuration_reviews,[])
                self.assertEqual(document.linked_records,{})
                if kind=='usage':
                    self.assertIs(row['is_composite'],False)
                    self.assertEqual(row['types'],[])
                    self.assertEqual(row['multiplicity'],{'status':'default','lower':1,'upper':1})
                else:
                    self.assertEqual(row['supertypes'],[])
                    self.assertNotIn('multiplicity',row)
                drawing=render(document,'PC')['projection']
                self.assertEqual(len(drawing['nodes']),1)
                self.assertEqual(drawing['edges'],{})

    def test_actual_top_level_metadata_package_collisions_preserve_root(self):
        project=str(uuid4());reserved='CSE_Views_'+project.replace('-','')
        for changes in ({'new_name':reserved},{'namespace_name':reserved},{'short_id':reserved},
                        {'new_name':reserved,'short_id':reserved+'_1'}):
            intent=request(project_id=project,**changes)
            document=document_for(intent)
            suffix='_2' if changes.get('short_id')==reserved+'_1' else '_1'
            self.assertIn('package '+reserved+suffix+' {',document.files['views.sysml'])
            self.assertEqual(document.inspect()['elements'][0]['name'],intent['new_name'])
            self.assertEqual(len(document.registry),1)

    def test_supplied_uuid_does_not_depend_on_root_spelling(self):
        intent=request()
        before=document_for(intent)
        after=document_for({**intent,'new_name':'Renamed','namespace_name':'Project'})
        self.assertEqual(set(before.registry),set(after.registry))
        self.assertEqual(after.registry[intent['root_element_id']],'Project::Renamed')

    def test_invalid_requests_refuse_without_any_storage(self):
        valid=request()
        for change in ({'expected_revision':False},{'expected_revision':1},{'root_kind':'reference'},
                {'new_name':''},{'new_name':'A\nB'},{'new_name':'A'*65},{'short_id':''},
                {'namespace_name':''},{'view_id':'../PC'},{'root_element_id':valid['project_id']},
                {'root_element_id':'BAD'},{'root_kind':[]},{'extra':0}):
            with self.subTest(change=change),self.assertRaises(EditError):
                initialize(self.work/'model.git',{**valid,**change})
        self.assertEqual(list(self.work.iterdir()),[])

    def test_unsupported_glyph_cannot_create_project(self):
        for key in ('new_name','short_id','namespace_name'):
            with self.subTest(key=key),self.assertRaises(EditError) as error:
                prepare(request(**{key:'🚀'}))
            self.assertEqual(error.exception.code,'presentation_conflict')
        self.assertEqual(list(self.work.iterdir()),[])

    def test_first_receipt_real_git_retry_edit_restore_and_export(self):
        for kind in ('definition','usage'):
            intent=checked_request(root_kind=kind,namespace_name='Project',short_id='ROOT')
            candidate=document_for(intent)
            project,receipt=initialize(self.work/(kind+'.git'),intent)
            self.assertEqual((receipt['revision'],receipt['operation']),(1,'initialize_physical_project'))
            self.assertEqual(receipt['request_sha256'],request_digest(intent))
            self.assertEqual(project.snapshot()['document'].registry,candidate.registry)
            self.assertEqual(project.snapshot()['document'].files,candidate.files)
            self.assertEqual(project._git('rev-list','--count','HEAD').stdout.strip(),b'1')
            renamed=project.transact({'operation':'rename','request_id':str(uuid4()),
                'expected_revision':1,'element_id':intent['root_element_id'],'new_name':'Changed'})
            self.assertEqual(renamed['revision'],2)
            with patch('verifier.composition_initial.document_for',side_effect=AssertionError('Retry regenerated sources')):
                self.assertEqual(initialize(project.repository,intent)[1],receipt)
                self.assertEqual(project.lookup_receipt(intent)['receipt'],receipt)
            self.assertEqual(project.head(),renamed['commit'])
            restore=project.transact({'operation':'restore','request_id':str(uuid4()),'expected_revision':2,'target_revision':1})
            self.assertEqual(restore['revision'],3)
            saved=CompositionProject(project.repository).snapshot()
            self.assertEqual(saved['document'].files,candidate.files)
            self.assertEqual(saved['document'].registry,candidate.registry)
            output=self.work/(kind+'-export')
            write_artifacts(saved,'PC',output);check_artifacts(saved,'PC',output)
            self.assertEqual(initialize(project.repository,intent)[1],receipt)
            with self.assertRaises(EditError) as error:
                initialize(project.repository,{**intent,'new_name':'Another'})
            self.assertEqual(error.exception.code,'request_reuse')
            self.assertEqual(project.head(),restore['commit'])

    def test_occupied_regular_empty_directory_and_symlink_are_preserved(self):
        targets=[self.work/'file',self.work/'empty',self.work/'link',self.work/'broken']
        targets[0].write_bytes(b'exact user bytes');targets[1].mkdir()
        targets[2].symlink_to(targets[1],target_is_directory=True)
        targets[3].symlink_to(self.work/'absent')
        intent=checked_request()
        for target in targets:
            with self.subTest(target=target),self.assertRaises(EditError) as error:
                initialize(target,intent)
            self.assertEqual(error.exception.code,'project_exists')
        self.assertEqual(targets[0].read_bytes(),b'exact user bytes')
        self.assertEqual(list(targets[1].iterdir()),[])
        self.assertTrue(targets[2].is_symlink());self.assertTrue(targets[3].is_symlink())

    def test_native_noreplace_cannot_overwrite_existing_empty_directory(self):
        source=self.work/'staging';target=self.work/'target';source.mkdir();target.mkdir()
        (source/'source').write_text('owned attempt')
        with self.assertRaises(FileExistsError):_rename_noreplace(source,target)
        self.assertEqual(list(target.iterdir()),[])
        self.assertEqual((source/'source').read_text(),'owned attempt')
        target.rmdir();_rename_noreplace(source,target)
        self.assertFalse(source.exists());self.assertEqual((target/'source').read_text(),'owned attempt')

    def test_identical_concurrent_initializers_converge_on_one_commit(self):
        intent=checked_request();target=self.work/'model.git';gate=Barrier(2)
        from verifier.composition_initial import _rename_noreplace as original
        def publish(source,destination):gate.wait(timeout=60);return original(source,destination)
        with patch('verifier.composition_initial._rename_noreplace',side_effect=publish):
            with ThreadPoolExecutor(max_workers=2) as pool:
                receipts=list(pool.map(lambda _:initialize(target,intent)[1],range(2)))
        self.assertEqual(receipts[0],receipts[1])
        self.assertEqual(len(CompositionProject(target).history()),1)
        self.assertEqual([p.name for p in self.work.iterdir()],['model.git'])

    def test_different_concurrent_initializers_preserve_the_winner_and_losing_intent(self):
        first=checked_request();second=prepare({**first,'request_id':str(uuid4()),'new_name':'Other','expected_bundle_sha256':None})[1]
        target=self.work/'model.git';gate=Barrier(2)
        from verifier.composition_initial import _rename_noreplace as original
        def publish(source,destination):gate.wait(timeout=60);return original(source,destination)
        def run(intent):
            try:return ('saved',initialize(target,intent)[1])
            except EditError as error:return ('refused',error.code)
        with patch('verifier.composition_initial._rename_noreplace',side_effect=publish):
            with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(run,[first,second]))
        self.assertEqual(sorted(x[0] for x in outcomes),['refused','saved'])
        self.assertIn(('refused','project_exists'),outcomes)
        winner=next(x[1] for x in outcomes if x[0]=='saved')
        self.assertEqual(CompositionProject(target).head(),winner['commit'])
        self.assertEqual(len(CompositionProject(target).history()),1)

    def test_failed_parent_flush_remains_unconfirmed_until_recovery_flush(self):
        from verifier.composition_initial import _fsync_directory as original
        intent=checked_request();target=self.work/'model.git'
        def flush(path):
            if Path(path)==self.work and target.is_dir():raise OSError('injected parent flush failure')
            original(path)
        with patch('verifier.composition_initial._fsync_directory',side_effect=flush):
            with self.assertRaises(OSError):initialize(target,intent)
            self.assertTrue(target.is_dir())
            with self.assertRaises(OSError):initialize(target,intent)
            with self.assertRaises(OSError):CompositionProject(target).lookup_receipt(intent)
        with patch('verifier.composition_initial._fsync_directory',wraps=original) as flushed:
            project,receipt=initialize(target,intent)
            self.assertTrue(all(call.args==(self.work,) for call in flushed.call_args_list))
        self.assertEqual(receipt['revision'],1)
        self.assertEqual(len(project.history()),1)

    def test_refused_publication_has_no_partial_authoritative_directory(self):
        with patch('verifier.composition_initial._rename_noreplace',side_effect=EditError('storage_unsupported','injected')):
            with self.assertRaises(EditError) as error:initialize(self.work/'model.git',checked_request())
        self.assertEqual(error.exception.code,'storage_unsupported')
        self.assertEqual(list(self.work.iterdir()),[])

    def test_legacy_import_digest_and_initial_history_remain_compatible(self):
        identity=str(uuid4());rid=str(uuid4());models={'old.sysml':'package Old { part def Original; }'}
        original={'operation':'import','request_id':rid,'project_id':identity,'models':models,'linked_records':{}}
        project,receipt=CompositionProject.create(self.work/'old.git',models,project_id=identity,request_id=rid)
        self.assertEqual(receipt['request_sha256'],sha256(json.dumps(original,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest())
        self.assertEqual(CompositionProject.create(project.repository,models,project_id=identity,request_id=rid)[1],receipt)
        self.assertEqual(len(project.history()),1)
        with self.assertRaises(EditError):initialize(project.repository,checked_request(project_id=identity))
        self.assertEqual(project.head(),receipt['commit'])

    def test_absent_receipt_is_revision_zero_without_reservation(self):
        intent=checked_request();target=self.work/'model.git'
        observed=CompositionProject(target).lookup_receipt(intent)
        self.assertEqual(observed,{'observed_commit':None,'observed_revision':0,
            'request_sha256':request_digest(intent),'receipt':None})
        self.assertFalse(target.exists())
        project,receipt=initialize(target,intent)
        self.assertEqual(project.lookup_receipt(intent)['receipt'],receipt)

    def test_preview_digest_is_required_and_generator_change_cannot_publish(self):
        draft=request();target=self.work/'model.git'
        for action in (initialize,lookup):
            with self.assertRaises(EditError) as error:action(target,draft)
            self.assertEqual(error.exception.code,'preview_required')
        candidate,intent=prepare(draft)
        with self.assertRaises(EditError) as error:
            initialize(target,{**intent,'new_name':'Changed after preview'})
        self.assertEqual(error.exception.code,'candidate_changed')
        self.assertFalse(target.exists())
        from verifier.composition_initial import embedded_json as original
        with patch('verifier.composition_initial.embedded_json',side_effect=lambda *a,**kw:original(*a,**kw)+'\n'):
            with self.assertRaises(EditError) as error:initialize(target,intent)
        self.assertEqual(error.exception.code,'candidate_changed')
        self.assertEqual(list(self.work.iterdir()),[])

    def test_symlink_parent_refuses_before_publication_or_staging(self):
        actual=self.work/'real';actual.mkdir();alias=self.work/'alias';alias.symlink_to(actual,target_is_directory=True)
        intent=checked_request()
        for action in (initialize,lookup):
            with self.assertRaises(OSError):action(alias/'model.git',intent)
        self.assertEqual(list(actual.iterdir()),[])

    def test_uncertain_history_read_is_not_reclassified_as_occupied(self):
        intent=checked_request();target=self.work/'model.git';initialize(target,intent)
        for code in ('storage','storage_integrity'):
            with patch.object(CompositionProject,'history',side_effect=EditError(code,'injected unreadable history')):
                with self.assertRaises(EditError) as error:initialize(target,intent)
                self.assertEqual(error.exception.code,code)

    def test_successful_publication_never_cleans_a_reused_staging_name(self):
        from verifier.composition_initial import _rename_noreplace as original
        intent=checked_request();replacement=[]
        def publish(source,target):
            original(source,target)
            source.mkdir();(source/'unrelated').write_text('preserve')
            replacement.append(source)
        with patch('verifier.composition_initial._rename_noreplace',side_effect=publish):
            initialize(self.work/'model.git',intent)
        self.assertEqual((replacement[0]/'unrelated').read_text(),'preserve')

    def test_missing_initial_source_blob_cannot_acknowledge_a_recovered_receipt(self):
        intent=checked_request();project,receipt=initialize(self.work/'model.git',intent)
        oid=project._tree(receipt['commit'])['models/model.sysml']
        blob=project.repository/'objects'/oid[:2]/oid[2:];held=self.work/'held-object'
        blob.rename(held)
        try:
            with patch('verifier.composition_initial.document_for',side_effect=AssertionError('Regenerated retry')):
                for action in (initialize,lookup):
                    with self.assertRaises(EditError) as error:action(project.repository,intent)
                    self.assertEqual(error.exception.code,'storage')
        finally:held.rename(blob)
        self.assertEqual(lookup(project.repository,intent)['receipt'],receipt)

    def test_cli_prepares_initializes_recovers_and_continues_the_same_native_project(self):
        target=self.work/'model.git';raw=self.work/'draft.json';checked=self.work/'checked.json'
        intent=request(root_kind='usage',namespace_name='Project');raw.write_text(json.dumps(intent))
        def run(command,request_path=None):
            args=[sys.executable,'-B',str(ROOT/'scripts/composition_project.py'),command,'--project',str(target)]
            if request_path:args+=['--request',str(request_path)]
            result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=60)
            report=json.loads(result.stdout)
            self.assertEqual(result.returncode,0,report)
            return report
        candidate=run('prepare-initial',raw)
        self.assertFalse(target.exists())
        self.assertEqual(candidate['registry'].keys(),{intent['root_element_id']})
        self.assertRegex(candidate['request']['expected_bundle_sha256'],'^[0-9a-f]{64}$')
        checked.write_text(json.dumps(candidate['request']))
        self.assertEqual(run('receipt',checked)['observed_revision'],0)
        receipt=run('initialize',checked)['receipt']
        self.assertEqual(receipt['revision'],1)
        saved=run('inspect')
        self.assertEqual(saved['files'],candidate['files'])
        self.assertEqual(saved['registry'],candidate['registry'])
        self.assertIs(saved['elements'][0]['is_composite'],False)
        edit=self.work/'edit.json';edit.write_text(json.dumps({'operation':'rename','request_id':str(uuid4()),
            'expected_revision':1,'element_id':intent['root_element_id'],'new_name':'updated'}))
        self.assertEqual(run('apply',edit)['receipt']['revision'],2)
        self.assertEqual(run('initialize',checked)['receipt'],receipt)
        self.assertEqual(run('receipt',checked)['observed_revision'],2)

    def test_killed_process_before_and_after_publication_recovers_once(self):
        # These are actual SIGKILL/restart boundaries. They do not simulate
        # physical power loss or certify filesystem/device firmware behavior.
        worker=r'''
import json,os,signal,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from verifier import composition_initial as initial
target=Path(sys.argv[2]);phase=sys.argv[3];intent=json.loads(Path(sys.argv[4]).read_text())
publish=initial._rename_noreplace;flush=initial._fsync_directory
def stop():
    print('ready',flush=True)
    signal.pause()
def rename(source,destination):
    if phase=='before_publish':stop()
    publish(source,destination)
    if phase=='after_publish':stop()
def fsync(path):
    flush(path)
    if phase=='before_ack' and Path(path)==target.parent and target.is_dir():stop()
initial._rename_noreplace=rename;initial._fsync_directory=fsync
initial.initialize(target,intent)
raise AssertionError('Worker passed selected interruption boundary')
'''
        for phase in ('before_publish','after_publish','before_ack'):
            with self.subTest(phase=phase):
                folder=self.work/phase;folder.mkdir();target=folder/'model.git'
                intent=checked_request();intent_path=folder/'request.json';intent_path.write_text(json.dumps(intent))
                process=subprocess.Popen([sys.executable,'-B','-c',worker,str(ROOT),str(target),phase,str(intent_path)],
                    cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                try:
                    readable,_,_=select.select([process.stdout],[],[],60)
                    self.assertTrue(readable,'Worker did not reach interruption point')
                    marker=process.stdout.readline()
                    self.assertEqual(marker,b'ready\n')
                    process.kill();process.wait(timeout=10)
                    self.assertLess(process.returncode,0)
                finally:
                    if process.poll() is None:process.kill();process.wait(timeout=10)
                    process.stdout.close();process.stderr.close()
                abandoned={str(p.relative_to(folder)):sha256(p.read_bytes()).hexdigest()
                    for attempt in folder.glob('.cse-initial-*') for p in attempt.rglob('*') if p.is_file()}
                observation=lookup(target,intent)
                self.assertEqual(observation['observed_revision'],0 if phase=='before_publish' else 1)
                project,receipt=initialize(target,intent)
                self.assertEqual(receipt['revision'],1)
                self.assertEqual(len(project.history()),1)
                self.assertEqual(project.snapshot()['document'].registry.keys(),{intent['root_element_id']})
                self.assertEqual(initialize(target,intent)[1],receipt)
                for name,digest in abandoned.items():self.assertEqual(sha256((folder/name).read_bytes()).hexdigest(),digest)


if __name__=='__main__':unittest.main()
