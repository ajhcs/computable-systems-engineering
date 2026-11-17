"""Host transport invariants, separate from native and actual-application tests."""
from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
NODE=shutil.which('node')


@unittest.skipUnless(NODE, 'Node is required for the browser adapter unit checks')
class HostTests(unittest.TestCase):
    def run_js(self, code):
        prelude="""
import assert from 'node:assert/strict';
import fs from 'node:fs';
const source=fs.readFileSync(SOURCE_PATH);
const {createMcpCompositionHost,compositionModelContext,publishMcpCompositionContext}=await import('data:text/javascript;base64,'+source.toString('base64'));
const boot={project_id:'36c89b0c-a94b-4f3e-86e0-b2940d040928',view_id:'PC_CONTEXT',app_instance_id:'da4e6a7d-b229-4bd0-9be9-2263998d0f61'};
const values=new Map(),storage={getItem:async key=>values.get(key)??null,setItem:async(key,value)=>{values.set(key,value)},removeItem:async key=>{values.delete(key)}};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
""".replace('SOURCE_PATH',json.dumps(str(ROOT/'web/composition-mcp-host.js')))
        result=subprocess.run([NODE,'--input-type=module','-e',prelude+code],cwd=ROOT,text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_invalid_boot_refuses_before_transport_or_storage(self):
        self.run_js("""
let calls=0;const app={callServerTool:async()=>{calls++}};
assert.throws(()=>createMcpCompositionHost(app,{...boot,project_id:'../../private'},storage));
assert.throws(()=>createMcpCompositionHost(app,{...boot,app_instance_id:null},storage));
assert.throws(()=>createMcpCompositionHost(app,boot,{}));
assert.equal(calls,0);assert.equal(values.size,0);
""")

    def test_instances_isolate_exact_pending_intent(self):
        self.run_js("""
const app={callServerTool:async()=>{throw Error('Unexpected transport')}};
const a=createMcpCompositionHost(app,boot,storage),b=createMcpCompositionHost(app,{...boot,app_instance_id:'7b1688ab-3161-4dcb-826b-af0ebc041415'},storage);
await a.intentStorage.setItem('pending','{"request_id":"same-intent"}');
assert.equal(await b.intentStorage.getItem('pending'),null);
assert.equal(await a.intentStorage.getItem('pending'),'{"request_id":"same-intent"}');
await b.intentStorage.removeItem('pending');assert.equal(values.size,1);
assert.equal(Object.hasOwn(globalThis,'cseCompositionHost'),false);
""")

    def test_granted_project_cannot_be_replaced(self):
        self.run_js("""
const calls=[],app={callServerTool:async args=>{calls.push(args);return{_meta:{cse_native:{http_status:200,body:{revision:4}}}}}};
const host=createMcpCompositionHost(app,boot,storage);
await assert.rejects(host.request({operation:'inspection',payload:{project_id:'other'}}));
await assert.rejects(host.request({operation:'inspection',payload:{view_id:'other'}}));
await assert.rejects(host.request({operation:'constructor'}));
await assert.rejects(host.request({operation:'session',payload:{access:'not-forwarded'}}));
assert.equal(calls.length,0);
await host.request({operation:'inspection',payload:{expected_revision:4,origin:'selected_role',offset:0,limit:25}});
assert.equal(calls[0].arguments.project_id,boot.project_id);assert.equal(calls[0].arguments.view_id,boot.view_id);
assert.equal(calls[0].arguments.expected_revision,4);
""")

    def test_native_refusal_and_exact_request_are_retained(self):
        self.run_js("""
const request={operation:'rename',request_id:'29cb2592-a695-4fdf-9bf2-a4a0cf275d05',expected_revision:1,element_id:'c8269fb5-0a79-49f4-b353-5a3da5e7b811',new_name:'sensorArray'};
const native={http_status:409,body:{error:{code:'stale_revision',detail:'Current revision is 2',definitive_refusal:true}}};
let called;const host=createMcpCompositionHost({callServerTool:async args=>{called=args;return{isError:true,_meta:{cse_native:native}}}},boot,storage);
const result=await host.request({operation:'apply',payload:request});
assert.equal(called.name,'cse_apply_composition_change');assert.deepEqual(called.arguments.request,request);
assert.deepEqual(result,{status:409,body:native.body});assert.equal(result.body.error.definitive_refusal,true);
""")

    def test_missing_native_response_is_unknown_transport(self):
        self.run_js("""
const host=createMcpCompositionHost({callServerTool:async()=>({content:[{type:'text',text:'success'}]})},boot,storage);
await assert.rejects(host.request({operation:'state'}),/native composition response/);
""")

    def test_selected_context_never_becomes_complete_review(self):
        self.run_js("""
const context=compositionModelContext({ready:true,guard:{model_revision:4},selection:{element_id:'native-id',origin:'selected_role',native:{owner:'Base'}},creation_draft:{declared_name:'Human draft'},typing_draft:{rows:[{type_id:'retained-type',native_name:'Removed::Type',available:false}]},usage_creation_draft:{declared_name:'Retained usage',type_id:null,is_composite:false,lower:'0'},restoration_target_revision:2,pending_change:{request:{request_id:'retained',operation:'set_layout',expected_revision:4,layout:{large:'not copied'}}},configuration_reviews:[{file:'scope.json',scope_sha256:'scope-hash',report:{status:'unknown',checked:['A'],findings:[]}}]});
assert.equal(context.scope,'selected_ui_context_never_replaces_complete_retained_review');assert.deepEqual(context.typing_draft,{rows:[{type_id:'retained-type',native_name:'Removed::Type',available:false}]});
assert.equal(context.retained_review_identities[0].status,'unknown');assert.equal(context.pending_request.request_id,'retained');
assert.equal(Object.hasOwn(context.pending_request,'layout'),false);assert.equal(Object.hasOwn(context,'configuration_reviews'),false);
assert.equal(context.selected_occurrence.native.owner,'Base');assert.equal(context.creation_draft.declared_name,'Human draft');assert.equal(context.restoration_target_revision,2);assert.deepEqual(context.usage_creation_draft,{declared_name:'Retained usage',type_id:null,is_composite:false,lower:'0'});
""")

    def test_context_retry_needs_no_new_event(self):
        self.run_js("""
let listener,calls=0;const sent=[];const snapshot={ready:true,guard:{model_revision:1},notice:'Checked candidate',pending_change:{request:{request_id:'original',operation:'rename',expected_revision:1}}};
const workbench={context:()=>structuredClone(snapshot),subscribe:fn=>{listener=fn;fn();return()=>{listener=null}}};
const dispose=publishMcpCompositionContext({updateModelContext:async value=>{calls++;if(calls===1)throw Error('Transient host refusal');sent.push(value)}},workbench);
await sleep(330);assert.equal(calls,2);assert.equal(sent.length,1);assert.ok(sent[0].content[0].text.includes('original'));
dispose();assert.equal(listener,null);
""")

    def test_disposal_stops_retries_after_in_flight_failure(self):
        self.run_js("""
let reject,calls=0,unsubscribed=0;
const workbench={context:()=>({ready:true}),subscribe:fn=>{fn();return()=>{unsubscribed++}}};
const dispose=publishMcpCompositionContext({updateModelContext:()=>{calls++;return new Promise((resolve,fail)=>{reject=fail})}},workbench);
dispose();reject(Error('Closed host'));await sleep(300);
assert.equal(calls,1);assert.equal(unsubscribed,1);
""")


if __name__=='__main__':unittest.main()
