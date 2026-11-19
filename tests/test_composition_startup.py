"""Prospective-state authority, exact checked startup and saved-editor handoff."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from threading import Thread
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from verifier.composition_edit import EditError
from verifier.composition_project import CompositionProject
from verifier.composition_startup import InitialCompositionSession, InitialCompositionHTTPServer
from tests.test_composition_initial import request


class StartupTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        self.temporary=tempfile.TemporaryDirectory(dir=ROOT/'.tmp');self.addCleanup(self.temporary.cleanup)
        self.work=Path(self.temporary.name);self.intent=request(root_kind='usage',namespace_name='Project')
        self.project=CompositionProject(self.work/'model.git')
        self.session=InitialCompositionSession(self.project,self.intent['project_id'],self.intent['root_element_id'],'PC')

    def test_no_saved_projection_or_native_candidate_is_fabricated(self):
        state=self.session.state()
        self.assertEqual((state['revision'],state['phase'],state['target_observation']),(0,'initial','absent'))
        self.assertIsNone(state['projection']);self.assertIsNone(state['current_saved'])
        self.assertFalse(self.project.repository.exists())

    def test_native_preview_creation_lost_reply_retry_and_existing_editor_handoff(self):
        preview=self.session.preview(self.intent);checked=preview['request']
        self.assertFalse(self.project.repository.exists())
        self.assertEqual(preview['candidate_bundle_sha256'],checked['expected_bundle_sha256'])
        self.assertEqual(preview['candidate']['elements'][0]['is_composite'],False)
        self.assertEqual(self.session.receipt(checked)['observed_revision'],0)
        result=self.session.apply(checked);receipt=result['receipt']
        self.assertEqual(receipt['revision'],1)
        self.assertEqual(self.session.state()['current_saved']['revision'],1)
        self.assertEqual(self.session.apply(checked)['receipt'],receipt)
        with self.assertRaises(EditError) as error:self.session.preview(checked)
        self.assertEqual(error.exception.code,'already_applied')
        existing=self.session.open_saved(checked)
        self.assertEqual(existing['initial_receipt'],receipt)
        self.assertEqual(existing['state']['projection']['project_id'],self.intent['project_id'])
        self.assertIn(self.intent['root_element_id'],existing['view_html'])
        renamed=self.session.saved.apply({'operation':'rename','request_id':str(uuid4()),'expected_revision':1,
            'element_id':self.intent['root_element_id'],'new_name':'updated'})['receipt']
        self.assertEqual(renamed['revision'],2)
        reopened=InitialCompositionSession(CompositionProject(self.project.repository),self.intent['project_id'],self.intent['root_element_id'],'PC')
        self.assertEqual(reopened.receipt(checked)['receipt'],receipt)
        self.assertEqual(reopened.open_saved(checked)['state']['revision'],2)

    def test_request_cannot_replace_prospective_project_root_or_view(self):
        for field in ('project_id','root_element_id','view_id'):
            changed={**self.intent,field:'OTHER' if field=='view_id' else str(uuid4())}
            with self.subTest(field=field),self.assertRaises(EditError) as error:self.session.preview(changed)
            self.assertEqual(error.exception.code,'authorization')
        self.assertFalse(self.project.repository.exists())

    def test_unavailable_history_is_never_reported_as_absent_or_acknowledged(self):
        checked=self.session.preview(self.intent)['request'];self.session.apply(checked)
        with patch.object(CompositionProject,'history',side_effect=EditError('storage','unreadable')):
            self.assertEqual(self.session.state()['target_observation'],'unavailable')
            with self.assertRaises(EditError) as error:self.session.apply(checked)
            self.assertEqual(error.exception.code,'outcome_unknown')

    def test_post_dispatch_failure_cannot_prove_no_other_identical_attempt_will_commit(self):
        checked=self.session.preview(self.intent)['request']
        with patch('verifier.composition_startup.initialize',side_effect=EditError('candidate_changed','injected')):
            with self.assertRaises(EditError) as error:self.session.apply(checked)
        self.assertEqual(error.exception.code,'outcome_unknown')
        self.assertFalse(getattr(error.exception,'definitive_refusal',False))
        self.assertEqual(self.session.receipt(checked)['observed_revision'],0)
        self.assertEqual(self.session.apply(checked)['receipt']['revision'],1)

    def test_inaccessible_target_is_unavailable_and_symlink_is_not_followed(self):
        with patch.object(self.session,'_target',side_effect=PermissionError('inaccessible')):
            self.assertEqual(self.session.state()['target_observation'],'unavailable')
            with self.assertRaises(PermissionError):self.session.preview(self.intent)
        other=self.work/'other';other.mkdir();self.project.repository.symlink_to(other,target_is_directory=True)
        with patch.object(CompositionProject,'history',side_effect=AssertionError('Followed symlink')):
            self.assertEqual(self.session.state()['target_observation'],'occupied')
            with self.assertRaises(EditError) as error:self.session.preview(self.intent)
            self.assertEqual(error.exception.code,'project_exists')

    def test_plain_occupied_directory_and_partial_git_storage_have_distinct_states(self):
        self.project.repository.mkdir()
        self.assertEqual(self.session.state()['target_observation'],'occupied')
        with self.assertRaises(EditError) as error:self.session.preview(self.intent)
        self.assertEqual(error.exception.code,'project_exists')
        (self.project.repository/'HEAD').write_text('partial metadata')
        self.assertEqual(self.session.state()['target_observation'],'unavailable')
        self.assertEqual((self.project.repository/'HEAD').read_text(),'partial metadata')


class StartupHTTPTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        self.temporary=tempfile.TemporaryDirectory(dir=ROOT/'.tmp');self.addCleanup(self.temporary.cleanup)
        self.work=Path(self.temporary.name);self.intent=request();self.project=CompositionProject(self.work/'model.git')
        self.server=InitialCompositionHTTPServer(self.project,self.intent['project_id'],self.intent['root_element_id'],'PC')
        thread=Thread(target=self.server.serve_forever,daemon=True);thread.start()
        server=self.server
        def stop():server.shutdown();server.server_close();thread.join(5)
        self.addCleanup(stop);self.cookie=''

    def call(self,*args,**kwargs):
        from tests.test_composition_session import SessionTests
        return SessionTests.call(self,*args,**kwargs)

    def connect(self):
        status,body,headers=self.call('POST','/session',{'access':self.server.access})
        self.assertEqual(status,200,body);self.cookie=headers['Set-Cookie'].split(';',1)[0]

    def test_initial_boundary_and_saved_access_require_auth_and_matching_handoff(self):
        self.assertEqual(self.call('GET','/startup/state')[0],403)
        self.connect();self.assertIsNone(self.call('GET','/startup/state')[1]['state']['projection'])
        for route in ('/api/state','/api/head','/view','/view.svg','/view.json'):
            self.assertEqual(self.call('GET',route)[0],403)
        self.assertEqual(self.call('POST','/startup/preview',self.intent,headers={'Origin':'https://other.invalid'})[0],403)
        self.assertEqual(self.call('POST','/startup/preview',self.intent,headers={'X-CSE-CSRF':'wrong'})[0],403)
        status,result,_=self.call('POST','/startup/preview',self.intent);self.assertEqual(status,200,result)
        checked=result['preview']['request'];status,saved,_=self.call('POST','/startup/apply',checked)
        self.assertEqual(status,200,saved)
        self.assertEqual(self.call('GET','/api/state')[0],403)
        self.assertEqual(self.call('POST','/api/apply',{'operation':'restore','request_id':str(uuid4()),'expected_revision':1,'target_revision':1})[0],403)
        status,opened,_=self.call('POST','/startup/open',checked);self.assertEqual(status,200,opened)
        self.assertEqual(self.call('GET','/api/state')[1]['state']['revision'],1)
        self.assertEqual(self.call('GET','/view.svg')[0],200)

    def test_different_winning_root_cannot_open_saved_api_using_the_same_project_id(self):
        from verifier.composition_initial import prepare, initialize
        self.connect();other={**self.intent,'root_element_id':str(uuid4()),'request_id':str(uuid4())}
        _,checked=prepare(other);initialize(self.project.repository,checked)
        self.assertEqual(self.call('GET','/api/state')[0],403)
        self.assertEqual(self.call('POST','/startup/open',checked)[0],403)
        with self.assertRaises(EditError):self.server.initial.authorize_saved()

    def test_opened_saved_grant_detects_a_root_or_view_change(self):
        self.connect();checked=self.server.initial.preview(self.intent)['request'];self.server.initial.apply(checked)
        self.server.initial.open_saved(checked)
        self.assertEqual(self.call('GET','/api/head')[0],200)
        with patch.object(self.server.initial,'root_element_id',str(uuid4())):
            self.assertEqual(self.call('GET','/api/state')[0],403)
        with patch.object(self.server.initial,'view_id','OTHER'):
            self.assertEqual(self.call('GET','/api/head')[0],403)

    def test_same_origin_restart_preserves_single_live_listener(self):
        port=self.server.server_port
        with self.assertRaises(OSError):
            InitialCompositionHTTPServer(self.project,self.intent['project_id'],self.intent['root_element_id'],'PC',port)
        self.connect();self.assertEqual(self.call('GET','/startup/state')[0],200)
        self.server.shutdown();self.server.server_close()
        replacement=InitialCompositionHTTPServer(self.project,self.intent['project_id'],self.intent['root_element_id'],'PC',port)
        thread=Thread(target=replacement.serve_forever,daemon=True);thread.start()
        def stop():replacement.shutdown();replacement.server_close();thread.join(5)
        self.addCleanup(stop);self.server=replacement;self.cookie='';self.connect()
        self.assertEqual(self.call('GET','/startup/state')[0],200)


if __name__=='__main__':unittest.main()
