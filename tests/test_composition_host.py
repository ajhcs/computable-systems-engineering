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
import path from 'node:path';
import {pathToFileURL} from 'node:url';
async function importHost(filename) {
  const source = fs.readFileSync(path.join(WEB_PATH, filename), 'utf8').replace(
    './composition-artifact-bytes.mjs',
    pathToFileURL(path.join(WEB_PATH, 'composition-artifact-bytes.mjs')).href,
  );
  return import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
}
const {createMcpCompositionHost,createMcpInitialCompositionHost,compositionModelContext,publishMcpCompositionContext}=await importHost('composition-mcp-host.js');
const {createWebArtifactTransfer,createWebCompositionHost}=await importHost('composition-web-host.js');
const boot={project_id:'36c89b0c-a94b-4f3e-86e0-b2940d040928',view_id:'PC_CONTEXT',app_instance_id:'da4e6a7d-b229-4bd0-9be9-2263998d0f61'};
const values=new Map(),storage={getItem:async key=>values.get(key)??null,setItem:async(key,value)=>{values.set(key,value)},removeItem:async key=>{values.delete(key)}};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
""".replace('WEB_PATH',json.dumps(str(ROOT/'web')))
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

    def test_both_artifact_transports_keep_the_saved_view_and_bytes_bound(self):
        self.run_js("""
const {createHash}=await import('node:crypto');
const hash=value=>createHash('sha256').update(value).digest('hex');
const text='<svg><text font-family="DejaVu Sans">Original</text></svg>';
const binding={kind:'view.svg',commit:'2'.repeat(40),revision:3,view_id:boot.view_id,
  bundle_sha256:'3'.repeat(64),expected_sha256:hash(text)};
const calls=[], downloads=[], webDownloads=[];
let altered=false, forgedDigest=false;
function file() {
  const bytes=altered?text.replace('DejaVu Sans','serif'):text;
  return {
    project_id:boot.project_id, view_id:binding.view_id, kind:binding.kind, commit:binding.commit,
    revision:binding.revision, bundle_sha256:binding.bundle_sha256, media_type:'image/svg+xml',
    text:bytes, bytes:Buffer.byteLength(bytes), sha256:forgedDigest?binding.expected_sha256:hash(bytes),
  };
}
const app={
  getHostCapabilities:()=>({downloadFile:{}}),
  downloadFile:async payload=>{downloads.push(payload);return{isError:false};},
  callServerTool:async payload=>{
    calls.push(payload);
    return {_meta:{cse_native:{http_status:200,body:file()}}};
  },
};
assert.equal(createMcpCompositionHost(app,boot,storage).openArtifact,null);
const host=createMcpCompositionHost(app,{...boot,allow_artifact_download:true},storage);
await assert.rejects(host.openArtifact({...binding,view_id:'AnotherView'}),/exact saved physical view/);
assert.equal(calls.length,0);
await host.openArtifact(binding);
assert.deepEqual(calls,[{
  name:'cse_export_composition_artifact',arguments:{project_id:boot.project_id,...binding},
}]);
assert.equal(downloads[0].contents[0].resource.text,text);
const web=createWebArtifactTransfer(boot,async()=>'synthetic-token',file=>webDownloads.push(file));
let fetches=0;
globalThis.fetch=async(url,options)=>{
  fetches++;
  assert.equal(url,'/api/composition/'+boot.project_id);
  assert.equal(options.headers.Authorization,'Bearer synthetic-token');
  const {view_id,...payload}=binding;
  assert.deepEqual(JSON.parse(options.body),{operation:'artifact',view_id,payload});
  return Response.json(file());
};
await assert.rejects(web({...binding,view_id:'AnotherView'}),/exact saved physical view/);
assert.equal(fetches,0);
assert.deepEqual(await web(binding),{isError:false});
assert.deepEqual(webDownloads,[{name:'CSE-PC_CONTEXT-r3.svg',mediaType:'image/svg+xml',text}]);
altered=true;
await assert.rejects(host.openArtifact(binding),/does not match the selected saved revision/);
await assert.rejects(web(binding),/does not match the selected saved revision/);
forgedDigest=true;
await assert.rejects(host.openArtifact(binding),/bytes failed verification/);
await assert.rejects(web(binding),/bytes failed verification/);
assert.equal(downloads.length,1);
assert.equal(webDownloads.length,1);
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

    def test_ownership_reads_keep_granted_view_distinct_from_affected_view(self):
        self.run_js("""
const calls=[],app={callServerTool:async args=>{calls.push(args);return{_meta:{cse_native:{http_status:200,body:{revision:4}}}}}};
const host=createMcpCompositionHost(app,boot,storage);
const payload={element_id:'captured',expected_revision:4,expected_bundle_sha256:'source',offset:0,limit:25,view_id:'PC_DETAIL_LEFT'};
await host.request({operation:'ownership_context',payload});
assert.equal(calls[0].name,'cse_read_composition_ownership_context');
assert.equal(calls[0].arguments.project_id,boot.project_id);
assert.equal(calls[0].arguments.view_id,boot.view_id);
assert.equal(calls[0].arguments.affected_view_id,'PC_DETAIL_LEFT');
assert.equal(calls[0].arguments.element_id,'captured');
await assert.rejects(host.request({operation:'ownership_context',payload:{...payload,project_id:'other'}}));
assert.equal(calls.length,1);
const request={operation:'reparent',request_id:'same',checked_bundle_sha256:'checked'};
await host.request({operation:'preview_view',payload:{request,view_id:'PC_DETAIL_LEFT'}});
assert.equal(calls[1].name,'cse_read_composition_candidate_view');
assert.equal(calls[1].arguments.view_id,boot.view_id);
assert.equal(calls[1].arguments.affected_view_id,'PC_DETAIL_LEFT');
assert.deepEqual(calls[1].arguments.request,request);
await assert.rejects(host.request({operation:'preview_view',payload:{request,view_id:'PC_DETAIL_LEFT',project_id:'other'}}));
assert.equal(calls.length,2);
""")

    def test_retained_review_reads_are_bound_to_the_project_without_a_view(self):
        self.run_js("""
const payload={revision:4,bundle_sha256:'1'.repeat(64),file:'saved.scope.json',scope_sha256:'2'.repeat(64),offset:1,limit:25};
const calls=[],body={project_id:boot.project_id,...payload,findings:[],next_offset:null};
const app={callServerTool:async args=>{calls.push(args);return{_meta:{cse_native:{http_status:200,body}}}}};
const mcp=createMcpCompositionHost(app,{...boot,allow_project_views:true},storage);
const command={operation:'model_review',viewId:'PC_OTHER',payload};
assert.deepEqual(await mcp.request(command),{status:200,body});
assert.deepEqual(calls,[{name:'cse_read_retained_composition_review',arguments:{project_id:boot.project_id,...payload}}]);
await assert.rejects(mcp.request({...command,payload:{...payload,project_id:'other'}}));
await assert.rejects(mcp.request({...command,payload:{...payload,view_id:'other'}}));
assert.equal(calls.length,1);
globalThis.fetch=async(url,options)=>{
  assert.equal(url,'/api/composition/'+boot.project_id);
  assert.deepEqual(JSON.parse(options.body),{operation:'model_review',view_id:null,payload});
  return {status:200,json:async()=>body};
};
const web=createWebCompositionHost({...boot,allow_project_views:true},async()=>'signed.token',storage);
assert.deepEqual(await web.request(command),{status:200,body});
""")

    def test_source_chunks_cannot_replace_granted_project_or_view(self):
        self.run_js("""
const calls=[],app={callServerTool:async args=>{calls.push(args);return{_meta:{cse_native:{http_status:200,body:{text:'exact',offset:0}}}}}};
const host=createMcpCompositionHost(app,boot,storage);
const payload={expected_revision:4,expected_bundle_sha256:'snapshot',request:null,file:'model.sysml',offset:0,limit:25};
const result=await host.request({operation:'source',payload});
assert.equal(calls[0].name,'cse_read_composition_source');
assert.equal(calls[0].arguments.project_id,boot.project_id);assert.equal(calls[0].arguments.view_id,boot.view_id);
assert.equal(calls[0].arguments.file,'model.sysml');assert.equal(calls[0].arguments.request,null);
assert.equal(result.body.text,'exact');
await assert.rejects(host.request({operation:'source',payload:{...payload,project_id:'other'}}));
await assert.rejects(host.request({operation:'source',payload:{...payload,view_id:'other'}}));
assert.equal(calls.length,1);
""")

    def test_removal_uses_same_project_grant_and_keeps_exact_closed_view_receipt(self):
        self.run_js("""
const calls=[],receipt={revision:5,request_id:'exact-removal'};
const result={receipt,state:null,view_closed:{view_id:'PC_CONTEXT',available_views:['PC_SECOND'],revision:5}};
const app={callServerTool:async args=>{calls.push(args);return{_meta:{cse_native:{http_status:200,body:result}}}}};
const fixed=createMcpCompositionHost(app,boot,storage);
boot.allow_project_views=true;
await assert.rejects(fixed.request({operation:'state',viewId:'PC_SECOND'}),/View selection/);
const flexible=createMcpCompositionHost(app,boot,storage);
const target={expected_revision:4,expected_bundle_sha256:'saved',view_id:'PC_SECOND',node_id:'Root'};
await flexible.request({operation:'removal_context',payload:target,viewId:'PC_SECOND'});
assert.equal(calls[0].name,'cse_read_composition_removal_context');
assert.deepEqual(calls[0].arguments,{project_id:boot.project_id,view_id:'PC_SECOND',request:target});
await assert.rejects(flexible.request({operation:'removal_context',payload:{...target,project_id:'elsewhere'}}));
const request={operation:'remove_occurrence',request_id:receipt.request_id,checked_bundle_sha256:'checked'};
assert.deepEqual((await flexible.request({operation:'apply',payload:request})).body,result);
assert.deepEqual(calls[1].arguments.request,request);
const context=compositionModelContext({pending_change:{request},available_views:['PC_SECOND'],view_available:false});
assert.equal(context.pending_request.checked_bundle_sha256,'checked');
assert.deepEqual(context.available_views,['PC_SECOND']);
assert.equal(context.view_available,false);
""")

    def test_missing_native_response_is_unknown_transport(self):
        self.run_js("""
const host=createMcpCompositionHost({callServerTool:async()=>({content:[{type:'text',text:'success'}]})},boot,storage);
await assert.rejects(host.request({operation:'state'}),/native composition response/);
""")

    def test_initial_grant_and_async_intent_are_isolated_from_saved_controller(self):
        self.run_js("""
const initialBoot={...boot,root_element_id:'438daf62-7334-43e2-a401-5def698d62b8'};
let calls=0,opened=0;const app={callServerTool:async()=>{calls++;throw Error('Unexpected transport')}};
assert.throws(()=>createMcpInitialCompositionHost(app,boot,storage,()=>{}));
assert.throws(()=>createMcpInitialCompositionHost(app,{...initialBoot,root_element_id:'../../other'},storage,()=>{}));
assert.throws(()=>createMcpInitialCompositionHost(app,initialBoot,storage,null));
const initial=createMcpInitialCompositionHost(app,initialBoot,storage,()=>{opened++});
const saved=createMcpCompositionHost(app,boot,storage);
await initial.intentStorage.setItem('pending','exact-initial');
assert.equal(await initial.intentStorage.getItem('pending'),'exact-initial');
assert.equal(await saved.intentStorage.getItem('pending'),null);
assert.deepEqual(initial.grant,{project_id:boot.project_id,view_id:boot.view_id,root_element_id:initialBoot.root_element_id});
await assert.rejects(initial.request({operation:'session',payload:{access:'not-forwarded'}}));
await assert.rejects(initial.request({operation:'constructor'}));
await assert.rejects(initial.request({operation:'initial_state',payload:{}}));
for(const field of ['project_id','root_element_id','view_id'])await assert.rejects(initial.request({operation:'initial_preview',payload:{project_id:boot.project_id,root_element_id:initialBoot.root_element_id,view_id:boot.view_id,[field]:'other'}}));
assert.equal(calls,0);assert.equal(opened,0);
""")

    def test_initial_native_protocol_keeps_revision_zero_and_exact_checked_request(self):
        self.run_js("""
const root='438daf62-7334-43e2-a401-5def698d62b8',calls=[];
const native={http_status:503,body:{error:{code:'outcome_unknown',detail:'Retain exact initial request',definitive_refusal:false}}};
const host=createMcpInitialCompositionHost({callServerTool:async args=>{calls.push(args);return{isError:true,_meta:{cse_native:native}}}},{...boot,root_element_id:root},storage,()=>{});
const request={operation:'initialize_physical_project',project_id:boot.project_id,root_element_id:root,view_id:boot.view_id,request_id:'29cb2592-a695-4fdf-9bf2-a4a0cf275d05',expected_revision:0,root_kind:'usage',new_name:'current',short_id:null,namespace_name:null,expected_bundle_sha256:'a'.repeat(64)};
const response=await host.request({operation:'initial_apply',payload:request});
assert.equal(calls[0].name,'cse_initialize_composition_project');assert.equal(calls[0].arguments.root_element_id,root);assert.deepEqual(calls[0].arguments.request,request);
assert.deepEqual(response,{status:503,body:native.body});
const context=compositionModelContext({ready:true,phase:'initial',guard:{model_revision:0},initial_state:{projection:null,revision:0},raw_draft:{new_name:'Retained root'},candidate_ready:true,pending_change:{request}});
assert.equal(context.phase,'initial');assert.equal(context.initial_state.projection,null);assert.equal(context.pending_request.expected_revision,0);assert.equal(context.pending_request.expected_bundle_sha256,request.expected_bundle_sha256);assert.equal(context.scope,'selected_ui_context_never_replaces_complete_retained_review');assert.equal(context.retained_review_identities.length,0);
""")

    def test_selected_context_never_becomes_complete_review(self):
        self.run_js("""
const navigation={project_id:boot.project_id,view_id:boot.view_id,revision:3,mode:'readable',
  collapsed_node_ids:['Parent'],collapsed_bindings:{Parent:'parent-uuid'},hidden_node_ids:['Child']};
const context=compositionModelContext({ready:true,guard:{model_revision:4},selection:{element_id:'native-id',origin:'selected_role',native:{owner:'Base'}},creation_draft:{declared_name:'Human draft'},typing_draft:{rows:[{type_id:'retained-type',native_name:'Removed::Type',available:false}]},usage_creation_draft:{declared_name:'Retained usage',type_id:null,is_composite:false,lower:'0'},restoration_target_revision:2,pending_change:{request:{request_id:'retained',operation:'set_layout',expected_revision:4,layout:{large:'not copied'}}},configuration_reviews:[{file:'scope.json',scope_sha256:'scope-hash',report:{status:'unknown',checked:['A'],findings:[]}}]});
assert.equal(context.navigation,null);
assert.deepEqual(compositionModelContext({navigation}).navigation,navigation);
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
