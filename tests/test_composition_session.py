"""Real loopback requests against native parsing, Git CAS and saved kit views."""
from copy import deepcopy
from http.client import HTTPConnection, RemoteDisconnected
import json
from pathlib import Path
import sys
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import EditError
from verifier.composition_project import CompositionProject
from verifier.composition_session import CompositionHTTPServer, CompositionHandler

SOURCE = (ROOT/'examples/workbench/composition/diagram-model.sysml').read_text()
SCOPE = {'version':'configuration-1.0',
         'root':{'native_name':'DiagramComposition::current','type':'DiagramComposition::Assembly'},
         'selected_roles':{'Left':{'parent':'$root','native_name':'DiagramComposition::current::left','type':'DiagramComposition::Device'}},
         'open_alternatives':[], 'connections':[]}


class SessionTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'.tmp')
        self.addCleanup(self.temp.cleanup)
        self.project, _ = CompositionProject.create(Path(self.temp.name)/'project.git', {'model.sysml':SOURCE},
            project_id=str(uuid4()), request_id=str(uuid4()),
            linked_records={'left.scope.json':{'kind':'retained_configuration','text':json.dumps(SCOPE)}})
        self.server = CompositionHTTPServer(self.project, 'PC_USAGE')
        thread = Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        def stop():
            self.server.shutdown(); self.server.server_close(); thread.join(5)
        self.addCleanup(stop)
        self.cookie = ''
        status, body, headers = self.call('POST','/session',{'access':self.server.access})
        self.assertEqual(status,200,body)
        self.cookie = headers['Set-Cookie'].split(';',1)[0]
        self.cookie_header = headers['Set-Cookie']
        self.identity = next(k for k,v in self.project.snapshot()['document'].registry.items() if v=='DiagramComposition::current::left')

    def call(self, method, path, body=None, *, headers=None, raw=None):
        connection = HTTPConnection('127.0.0.1',self.server.server_port,timeout=90)
        supplied = {'Origin':self.server.origin,'Cookie':self.cookie,'X-CSE-CSRF':self.server.csrf}
        if body is not None or raw is not None:
            supplied['Content-Type']='application/json'
        supplied.update(headers or {})
        payload = raw if raw is not None else json.dumps(body).encode() if body is not None else None
        try:
            connection.request(method,path,payload,supplied)
            response=connection.getresponse()
            content=response.read()
            kind=response.getheader('Content-Type','')
            result=json.loads(content) if kind.startswith('application/json') else content
            return response.status,result,dict(response.getheaders())
        finally:
            connection.close()

    def rename(self, name='detector', revision=1):
        return {'operation':'rename','request_id':str(uuid4()),'expected_revision':revision,
                'element_id':self.identity,'new_name':name}

    def test_preview_is_unsaved_and_apply_uses_the_identical_candidate(self):
        request=self.rename()
        head=self.project.head()
        objects=self.project._git('count-objects','-v').stdout
        candidate=self.project.preview(request)
        self.assertEqual(candidate['changed_model_files'],['model.sysml'])
        self.assertEqual(candidate['changed_linked_records'],[])
        self.assertEqual(candidate['document'].registry[self.identity],'DiagramComposition::current::detector')
        self.assertEqual(candidate['document'].linked_records['left.scope.json']['text'],json.dumps(SCOPE))
        self.assertEqual(candidate['document'].configuration_reviews[0]['report']['status'],'fail')
        self.assertEqual(self.project.head(),head)
        self.assertEqual(self.project._git('count-objects','-v').stdout,objects)
        receipt=self.project.transact(request)
        self.assertEqual(self.project.snapshot()['document'].files,candidate['document'].files)
        self.assertEqual(receipt['request_sha256'],candidate['request_sha256'])
        with self.assertRaises(EditError) as error:self.project.preview(request)
        self.assertEqual(error.exception.code,'already_applied')

    def test_multiplicity_preview_commit_retry_refusal_and_restore_share_the_native_model(self):
        original=self.project.snapshot()
        request={'operation':'set_multiplicity','request_id':str(uuid4()),'expected_revision':1,
                 'element_id':self.identity,'lower':0,'upper':1}
        status,result,_=self.call('POST','/api/preview',request)
        self.assertEqual(status,200,result)
        self.assertEqual(result['preview']['configuration_reviews'][0]['report']['status'],'unknown')
        self.assertEqual(self.project.head(),original['commit'])
        status,result,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,200,result)
        receipt=result['receipt'];self.assertEqual(receipt['operation'],'set_multiplicity')
        self.assertEqual(receipt['revision'],2)
        self.assertEqual(self.call('POST','/api/apply',request)[1]['receipt'],receipt)
        self.assertEqual(self.call('POST','/api/receipt',request)[1]['receipt'],receipt)
        reopened=CompositionProject(self.project.repository).snapshot()
        self.assertEqual(reopened['document'].registry,original['document'].registry)
        self.assertEqual(reopened['document'].linked_records,original['document'].linked_records)
        self.assertEqual(reopened['document'].configuration_reviews[0]['report']['status'],'unknown')
        status,svg,_=self.call('GET','/view.svg')
        self.assertEqual(status,200);self.assertIn(b'[0..1]',svg)
        definition=next(k for k,v in reopened['document'].registry.items() if v=='DiagramComposition::Device')
        for fields in ({'lower':True},{'lower':1.0},{'upper':2147483648},{'lower':2,'upper':1},{'element_id':definition}):
            invalid={**request,'request_id':str(uuid4()),'expected_revision':2,**fields}
            status,result,_=self.call('POST','/api/apply',invalid)
            self.assertEqual(status,400,result);self.assertTrue(result['error']['definitive_refusal'])
            self.assertEqual(self.project.head(),receipt['commit'])
        status,result,_=self.call('POST','/api/apply',{**request,'request_id':str(uuid4())})
        self.assertEqual(status,409,result);self.assertEqual(result['error']['code'],'stale_revision')
        restore={'operation':'restore','request_id':str(uuid4()),'expected_revision':2,'target_revision':1}
        self.assertEqual(self.call('POST','/api/apply',restore)[0],200)
        restored=self.project.snapshot()
        self.assertEqual(restored['revision'],3)
        self.assertEqual(restored['document'].files,original['document'].files)
        self.assertEqual(restored['document'].configuration_reviews[0]['report']['status'],'pass')

    def test_loopback_origin_session_csrf_and_json_boundaries_do_not_publish(self):
        head=self.project.head()
        self.assertIn('HttpOnly',self.cookie_header)
        self.assertIn('SameSite=Strict',self.cookie_header)
        cases=[('GET','/api/state',None,{'Cookie':''},403),
               ('GET','/api/state',None,{'Origin':'https://other.invalid'},403),
               ('GET','/api/state',None,{'Host':'other.invalid'},403),
               ('POST','/api/apply',self.rename(),{'X-CSE-CSRF':''},403),
               ('POST','/api/apply',self.rename(),{'Origin':''},403),
               ('GET','/../../verifier/composition_project.py',None,{},404)]
        for method,path,body,headers,expected in cases:
            with self.subTest(path=path,headers=headers):self.assertEqual(self.call(method,path,body,headers=headers)[0],expected)
        for raw in (b'{"operation":"rename","operation":"restore"}',b'{"value":NaN}'):
            self.assertEqual(self.call('POST','/api/apply',raw=raw)[0],400)
        self.assertEqual(self.call('POST','/api/apply',raw=b'{}',headers={'Content-Length':'1000001'})[0],400)
        status,html,headers=self.call('GET','/')
        self.assertEqual(status,200)
        self.assertNotIn(str(self.project.repository).encode(),html)
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertEqual(self.project.head(),head)

    def test_http_preview_save_and_revision_bound_source_views(self):
        request=self.rename()
        before=self.project.snapshot()
        status,result,_=self.call('POST','/api/preview',request)
        self.assertEqual(status,200,result)
        self.assertEqual(result['preview']['base_revision'],1)
        self.assertEqual(result['preview']['configuration_reviews'][0]['report']['status'],'fail')
        self.assertEqual(self.project.head(),before['commit'])
        status,result,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,200,result)
        self.assertEqual(result['receipt']['revision'],2)
        self.assertEqual(result['state']['projection']['nodes']['Left']['element_id'],self.identity)
        self.assertEqual(result['state']['projection']['nodes']['Left']['native']['name'],'detector')
        status,_,_=self.call('GET','/view.json?commit='+before['commit'])
        self.assertEqual(status,409)
        status,data,_=self.call('GET','/view.json?commit='+result['receipt']['commit'])
        self.assertEqual(status,200)
        self.assertEqual(data['commit'],result['receipt']['commit'])
        status,page,_=self.call('GET','/api/state')
        self.assertEqual(status,200)
        self.assertIn('data-native-name="DiagramComposition::current::detector"',page['view_html'])
        self.assertIn('left.scope.json',page['view_html'])
        status,reused,_=self.call('POST','/api/apply',{**request,'new_name':'differentPayload'})
        self.assertEqual(status,409,reused)
        self.assertEqual(reused['error']['code'],'request_reuse')
        self.assertTrue(reused['error']['definitive_refusal'])
        self.assertEqual(self.project.snapshot()['revision'],2)

    def test_an_external_edit_invalidates_preview_without_rebasing(self):
        pending=self.rename('pending')
        saved=self.project.transact(self.rename('intervening'))
        status,result,_=self.call('POST','/api/preview',pending)
        self.assertEqual(status,409,result)
        self.assertEqual(result['error']['code'],'stale_revision')
        self.assertEqual(self.project.head(),saved['commit'])
        status,current,_=self.call('GET','/api/state')
        self.assertEqual(status,200)
        self.assertEqual(current['state']['projection']['nodes']['Left']['native']['name'],'intervening')

    def test_receipt_lookup_is_read_only_bound_to_observed_head_and_exact_payload(self):
        request=self.rename()
        head=self.project.head()
        objects=self.project._git('count-objects','-v').stdout
        status,absent,_=self.call('POST','/api/receipt',request)
        self.assertEqual(status,200,absent)
        self.assertIsNone(absent['receipt'])
        self.assertEqual(absent['observed_commit'],head)
        self.assertEqual(absent['observed_revision'],1)
        self.assertEqual(self.project._git('count-objects','-v').stdout,objects)
        self.assertEqual(self.call('POST','/api/receipt',request,headers={'X-CSE-CSRF':''})[0],403)
        status,saved,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,200,saved)
        later=self.project.transact({'operation':'restore','request_id':str(uuid4()),
                                     'expected_revision':2,'target_revision':1})
        objects=self.project._git('count-objects','-v').stdout
        status,found,_=self.call('POST','/api/receipt',request)
        self.assertEqual(status,200,found)
        self.assertEqual(found['receipt'],saved['receipt'])
        self.assertEqual(found['request_sha256'],saved['receipt']['request_sha256'])
        self.assertEqual(found['observed_revision'],3)
        self.assertEqual(found['observed_commit'],later['commit'])
        self.assertEqual(self.project.head(),later['commit'])
        self.assertEqual(self.project._git('count-objects','-v').stdout,objects)
        status,reused,_=self.call('POST','/api/receipt',{**request,'new_name':'changedPayload'})
        self.assertEqual(status,409,reused)
        self.assertEqual(reused['error']['code'],'request_reuse')
        for invalid in ({}, {**request,'unknown':True}):
            self.assertEqual(self.call('POST','/api/receipt',invalid)[0],400)
        status,script,_=self.call('GET','/site-tools.js')
        self.assertEqual(status,200)
        self.assertIn(b'document.modelContext',script)
        self.assertNotIn(str(self.project.repository).encode(),script)
        status,page,_=self.call('GET','/api/state')
        self.assertEqual(status,200)
        self.assertEqual(page['state']['configuration_reviews'][0]['report']['status'],'pass')

    def test_layout_retries_restoration_and_reopen_preserve_sources_and_identity(self):
        original=self.project.snapshot()
        layout=deepcopy(self.server.session.state()['layout'])
        layout['nodes']['Left']['x']+=20
        layout['nodes']['Left']['height']+=40
        route=layout['edges']['OwnLeft']['points']
        route[-1][0]+=20;route[-1][1]+=20;route[-2][1]+=20
        request={'operation':'set_layout','request_id':str(uuid4()),'expected_revision':1,'layout':layout}
        self.assertEqual(self.call('POST','/api/preview',request)[0],200)
        self.assertEqual(self.project.snapshot()['revision'],1)
        first=self.call('POST','/api/apply',request)
        second=self.call('POST','/api/apply',request)
        self.assertEqual(first[0],200,first)
        self.assertEqual(first[1]['receipt'],second[1]['receipt'])
        reopened=CompositionProject(self.project.repository).snapshot()
        self.assertEqual(reopened['document'].files,original['document'].files)
        self.assertEqual(reopened['document'].registry,original['document'].registry)
        self.assertEqual(self.server.session.state()['layout'],layout)
        for expected,target in [(2,1),(3,2)]:
            restore={'operation':'restore','request_id':str(uuid4()),'expected_revision':expected,'target_revision':target}
            self.assertEqual(self.call('POST','/api/preview',restore)[0],200)
            self.assertEqual(self.project.snapshot()['revision'],expected)
            self.assertEqual(self.call('POST','/api/apply',restore)[0],200)
        self.assertEqual(self.project.snapshot()['revision'],4)
        self.assertEqual(self.server.session.state()['layout'],layout)
        self.assertEqual(self.call('POST','/api/apply',{**request,'request_id':str(uuid4())})[0],409)

    def test_lost_http_response_recovers_one_durable_receipt(self):
        request=self.rename()
        send=CompositionHandler._send
        lost=False
        def lose(handler,status,body,*args,**kwargs):
            nonlocal lost
            if handler.path=='/api/apply' and status==200 and not lost:
                lost=True
                handler.close_connection=True
                return
            return send(handler,status,body,*args,**kwargs)
        with patch.object(CompositionHandler,'_send',lose):
            with self.assertRaises(RemoteDisconnected):self.call('POST','/api/apply',request)
        status,result,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,200,result)
        self.assertEqual(result['receipt']['revision'],2)
        self.assertEqual(self.project.snapshot()['revision'],2)
        self.assertEqual(len(self.project.history()),2)

    def test_post_publication_refresh_failure_keeps_the_durable_acknowledgement(self):
        request=self.rename()
        with patch.object(self.server.session,'state',side_effect=EditError('presentation_conflict','injected refresh failure')):
            status,result,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,200,result)
        self.assertEqual(result['receipt']['revision'],2)
        self.assertIsNone(result['state'])
        self.assertEqual(result['refresh_error']['code'],'presentation_conflict')
        self.assertEqual(self.project.snapshot()['revision'],2)
        status,recovered,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,200,recovered)
        self.assertEqual(recovered['receipt'],result['receipt'])
        self.assertEqual(recovered['state']['revision'],2)

    def test_storage_error_after_publication_recovers_the_matching_receipt(self):
        request=self.rename()
        publish=self.project._publish
        def fail_after(commit,previous):
            publish(commit,previous)
            raise OSError('injected storage exception after publication')
        with patch.object(self.project,'_publish',fail_after):
            status,result,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,200,result)
        self.assertEqual(result['receipt']['revision'],2)
        self.assertEqual(self.project.snapshot()['revision'],2)
        self.assertEqual(self.call('POST','/api/apply',request)[1]['receipt'],result['receipt'])

    def test_unconfirmed_storage_outcome_requires_the_same_request_retry(self):
        request=self.rename()
        with patch.object(self.project,'_publish',side_effect=OSError('injected storage exception before publication')):
            status,result,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,503,result)
        self.assertEqual(result['error']['code'],'outcome_unknown')
        self.assertEqual(self.project.snapshot()['revision'],1)
        status,result,_=self.call('POST','/api/apply',request)
        self.assertEqual(status,200,result)
        self.assertEqual(result['receipt']['revision'],2)
        self.assertEqual(len(self.project.history()),2)


    def test_retry_read_failures_do_not_revoke_an_existing_publication(self):
        request=self.rename()
        original=self.call('POST','/api/apply',request)[1]['receipt']
        with patch.object(self.server.session,'preview',side_effect=EditError('storage','injected preliminary read failure')):
            status,recovered,_=self.call('POST','/api/apply',request)
            self.assertEqual(status,200,recovered)
            self.assertEqual(recovered['receipt'],original)
            with patch.object(self.project,'history',side_effect=EditError('storage','injected receipt lookup failure')):
                status,unknown,_=self.call('POST','/api/apply',request)
                self.assertEqual(status,503,unknown)
                self.assertEqual(unknown['error']['code'],'outcome_unknown')
                self.assertFalse(unknown['error']['definitive_refusal'])
        with patch.object(self.server.session,'preview',side_effect=EditError('stale_revision','injected apparent refusal')):
            with patch.object(self.project,'_retry',side_effect=EditError('storage_integrity','injected ambiguous receipt resolution')):
                status,unknown,_=self.call('POST','/api/apply',request)
                self.assertEqual(status,503,unknown)
                self.assertEqual(unknown['error']['code'],'outcome_unknown')
                self.assertFalse(unknown['error']['definitive_refusal'])
        self.assertEqual(self.call('POST','/api/apply',request)[1]['receipt'],original)
        self.assertEqual(self.project.snapshot()['revision'],2)


if __name__=='__main__':unittest.main()
