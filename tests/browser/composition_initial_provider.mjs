// Adversarial supplied-host controls over a real native initial Git backend.
// Transport/font/storage faults are explicit test injections, not model verdicts.
import fs from 'node:fs';import path from 'node:path';import {createRequire} from 'node:module';import {fileURLToPath} from 'node:url';
import {assert,hash,digest,pins,unchanged,fixture,toolRegistration,context,tool,initialReady,candidateReady,shot,verifyShots,snapshot,displayedFonts,root} from './composition_initial_helpers.mjs';
const {chromium}=createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE),out=path.resolve(process.argv[2]);fs.mkdirSync(out,{mode:0o700});
const inputs=pins(['tests/browser/composition_initial_provider.mjs']),browser=await chromium.launch({executablePath:process.env.CSE_BROWSER_EXECUTABLE,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']}),results=[],images=[],deliveries=[];
async function provided(page,connection,initialFault=null){
 await page.context().request.post(connection.origin+'/session',{headers:{Origin:connection.origin},data:{access:new URLSearchParams(new URL(connection.url).hash.slice(1)).get('access')}});
 await toolRegistration(page);
 await page.addInitScript(({grant,initialFault})=>{
  const storage=globalThis.sessionStorage;let csrf;
  globalThis.__asyncStorage=initialFault==='async_storage';globalThis.__fault=__asyncStorage?null:initialFault;globalThis.__failWrites=false;globalThis.__fontFault=null;globalThis.__dropApply=null;globalThis.__calls=[];globalThis.__opened=[];
  globalThis.__pauseNextWrite=false;globalThis.__registrationStarts=[];
  if(initialFault==='delayed_registration'){const register=document.modelContext.registerTool;document.modelContext.registerTool=async tool=>{__registrationStarts.push(tool.name);globalThis.__closedTool=tool;await new Promise(resolve=>globalThis.__releaseRegistration=resolve);return register(tool)}}
  globalThis.cseInitialHost={version:'cse-initial-host-1',kind:'loopback',grant,
   intentStorage:{getItem:key=>__asyncStorage?new Promise(resolve=>setTimeout(()=>resolve(storage.getItem(key)),20)):storage.getItem(key),setItem:(key,value)=>{const write=()=>{if(__failWrites)throw Error('Injected intent storage failure');storage.setItem(key,value)};if(__pauseNextWrite){__pauseNextWrite=false;return new Promise(resolve=>globalThis.__releaseWrite=resolve).then(write)}return __asyncStorage?new Promise((resolve,reject)=>setTimeout(()=>{try{write();resolve()}catch(error){reject(error)}},20)):write()},removeItem:key=>storage.removeItem(key)},
   request:async({operation,payload})=>{
    __calls.push(operation);if(operation==='session')throw Error('Supplied provider must not receive access fragment');
    const paths={initial_state:'/startup/state',initial_preview:'/startup/preview',initial_apply:'/startup/apply',initial_receipt:'/startup/receipt',initial_open:'/startup/open'};
    if(operation==='initial_apply'&&__dropApply==='before')throw Error('Injected lost dispatch');
    const options={credentials:'same-origin'};if(payload!==undefined)Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-CSE-CSRF':csrf},body:JSON.stringify(payload)});
    const response=await fetch(paths[operation],options),body=await response.json();if(body.csrf)csrf=body.csrf;
    if(operation==='initial_apply'&&__dropApply==='after')throw Error('Injected committed reply loss');
    if(operation==='initial_apply'&&globalThis.__pauseApplyReply){__pauseApplyReply=false;await new Promise(resolve=>globalThis.__releaseApplyReply=resolve)}
    if(response.ok&&operation==='initial_apply'){if(__fault==='contradictory_apply_head')body.startup_state.current_saved.commit='f'.repeat(40);if(__fault==='unavailable_apply_head'){body.startup_state.current_saved=null;body.startup_state.target_observation='unavailable'}}
    if(response.ok&&operation==='initial_state'&&__fault==='wrong_state')body.state.root_element_id='11111111-1111-4111-8111-111111111111';
    if(response.ok&&operation==='initial_preview'){
     if(__fault==='stale_request')body.preview.request.new_name='Another root';
     if(__fault==='wrong_source')body.preview.files['model.sysml']+='\n';
     if(__fault==='empty_svg')body.preview.candidate_svg='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="410"/>';
     if(__fault==='wrong_root')body.preview.candidate.elements[0].element_id='11111111-1111-4111-8111-111111111111';
     if(['wrong_owner','wrong_owner_reference'].includes(__fault)){const row=body.preview.candidate.elements[0],owner=row.owner,name=row.qualified_name;row.owner='Other';body.preview.candidate_svg=body.preview.candidate_svg.replace('data-native-owner="'+owner+'"','data-native-owner="Other"');if(__fault==='wrong_owner_reference'){row.qualified_name='Other::System';body.preview.registry[row.element_id]=row.qualified_name;body.preview.candidate_svg=body.preview.candidate_svg.replace('data-native-name="'+name+'"','data-native-name="'+row.qualified_name+'"')}}
    }
    if(response.ok&&operation==='initial_receipt'){if(__fault==='receipt_zero_head'){body.observed_revision=0;body.observed_commit=null}if(__fault==='receipt_wrong_head')body.observed_commit='f'.repeat(40);if(__fault==='older_observation'){body.observed_revision=1;body.observed_commit=body.receipt.commit}}
    if(response.ok&&operation==='initial_open'){
     if(body.state.revision===1&&!globalThis.__firstOpen)globalThis.__firstOpen=JSON.parse(JSON.stringify(body));
     if(__fault==='wrong_open_receipt')body.initial_receipt.commit='0'.repeat(40);
     if(__fault==='wrong_open_project')body.state.projection.project_id='11111111-1111-4111-8111-111111111111';
     if(__fault==='wrong_open_view')body.state.projection.id='Another';
     if(__fault==='stale_open_view')body.state.revision++;
     if(['coherent_first_commit','coherent_first_bundle'].includes(__fault)){const doc=new DOMParser().parseFromString(body.view_html,'text/html'),tag=doc.getElementById('cse-data'),data=JSON.parse(tag.textContent);if(__fault==='coherent_first_commit')body.state.commit=data.commit='f'.repeat(40);else body.state.projection.bundle_sha256=data.projection.bundle_sha256='f'.repeat(64);body.view_html=body.view_html.replace(tag.textContent,JSON.stringify(data).replace(/</g,'\\u003c'))}
     if(__fault==='stale_observed_head')return{status:response.status,body:JSON.parse(JSON.stringify(__firstOpen))};
    }
    return{status:response.status,body};
   },openSaved:async result=>{__opened.push(result.initial_receipt)},
  };
  document.addEventListener('DOMContentLoaded',()=>{
   const frame=document.getElementById('initial-diagram');if(!frame)return;
   frame.addEventListener('load',()=>{if(!__fontFault)return;const doc=frame.contentDocument;if(__fontFault==='empty_frame')doc.querySelector('svg')?.remove();if(__fontFault==='zero_faces')doc.fonts.load=async()=>[];if(__fontFault==='hanging_faces')doc.fonts.load=()=>new Promise(()=>{})},true);
  });
 },{grant:{project_id:connection.project_id,root_element_id:connection.root_element_id,view_id:connection.view_id},initialFault});
 page.on('response',response=>{if(new URL(response.url()).pathname==='/initial.js')deliveries.push(response.body().then(bytes=>{const actual=hashBytes(bytes);assert(actual===inputs['web/composition-initial.js'],'Served startup JS differs');return{url:response.url(),sha256:actual}}))});
 await page.goto(connection.origin+'/start#access=DO_NOT_FORWARD');
}
const hashBytes=digest;
async function fill(page){await page.locator('#root-kind').selectOption('definition');await page.locator('#root-name').fill('System');await page.locator('#root-short').fill('SYS');await page.locator('#namespace-mode').selectOption('global')}
const invoke=(page,method)=>page.evaluate(async method=>{try{return{ok:true,result:await cseInitialWorkbench[method]()}}catch(error){return{ok:false,code:error.code||'error',message:error.message}}},method);
async function runCase(name,fn,{fault=null}={}){
 const native=await fixture(out,name),page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];page.setDefaultTimeout(90000);page.on('pageerror',error=>errors.push(String(error)));
 try{await provided(page,native,fault);if(fault==='wrong_state')await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Initial session unavailable'));else if(fault==='delayed_registration')await page.waitForFunction(()=>globalThis.cseInitialWorkbench?.context().ready&&typeof __releaseRegistration==='function');else await initialReady(page);const detail=await fn(page,native);assert(!errors.length,errors.join(';'));await shot(page,out,name,images);results.push({id:name,status:'pass',...detail,errors});console.log('PASS '+name)}
 catch(error){await shot(page,out,name+'-failed',images).catch(()=>{});throw error}
 finally{await page.close();await native.stop()}
}
try{
 await runCase('namespace-and-response-binding',async(page,native)=>{
  await fill(page);await page.locator('#namespace-mode').selectOption('package');await page.locator('#package-name').fill('HiddenPackage');await page.locator('#namespace-mode').selectOption('');
  const count=await page.evaluate(()=>__calls.filter(n=>n==='initial_preview').length),invalid=await invoke(page,'preview');
  assert(!invalid.ok&&invalid.code==='input','Blank namespace silently selected the hidden package');assert(await page.evaluate(()=>__calls.filter(n=>n==='initial_preview').length)===count,'Invalid namespace dispatched preview');
  await page.locator('#namespace-mode').selectOption('global');const raw=JSON.stringify((await context(page)).raw_draft),refusals=[];
  for(const fault of['stale_request','wrong_source','empty_svg','wrong_root']){
   await page.evaluate(value=>__fault=value,fault);const result=await invoke(page,'preview'),after=await context(page);
   assert(!result.ok&&['response_binding','presentation'].includes(result.code),'Malformed preview accepted: '+fault);assert(!after.pending_change&&!after.candidate_ready&&JSON.stringify(after.raw_draft)===raw,'Malformed response changed the retained draft');assert(!fs.existsSync(native.project),'Malformed preview published');refusals.push({fault,code:result.code});
  }
  await page.locator('#namespace-mode').selectOption('package');await page.locator('#package-name').fill('P::named');for(const fault of ['wrong_owner','wrong_owner_reference']){await page.evaluate(value=>__fault=value,fault);const result=await invoke(page,'preview');assert(!result.ok&&result.code==='response_binding','Inconsistent named owner accepted');refusals.push({fault,code:result.code})}await page.evaluate(()=>__fault=null);assert((await invoke(page,'preview')).ok,'Valid native preview refused');await candidateReady(page);
  assert(await page.evaluate(()=>!__calls.includes('session')),'Supplied loopback label received an access credential');
  return{refusals,fonts:await displayedFonts(page),claim:'Native response/byte/identity binding and explicit namespace choice'};
 });
 await runCase('font-load-failures',async(page,native)=>{
  await fill(page);const observations=[];
  for(const fault of['empty_frame','zero_faces','hanging_faces']){
   await page.evaluate(value=>__fontFault=value,fault);const result=await invoke(page,'preview');assert(result.ok,'Native preview failed before font fault');
   await page.waitForFunction(()=>document.getElementById('notice').textContent.startsWith('Unsupported view:'),null,{timeout:25000});const c=await context(page);assert(!c.candidate_ready&&await page.locator('#create-initial').isDisabled(),'Unusable frame enabled creation');
   const refused=await invoke(page,'save');assert(!refused.ok&&refused.code==='candidate_not_ready','Save bypassed original-font gate');assert(!fs.existsSync(native.project),'Font failure published');observations.push({fault,notice:c.notice});
   const edited=await tool(page,'cse_edit_initial_draft',{guard:c.guard});assert(edited.outcome==='draft_retained','Font failure trapped draft');
  }
  await page.evaluate(()=>__fontFault=null);await invoke(page,'preview');await candidateReady(page);return{observations,fonts:await displayedFonts(page)};
 });
 await runCase('first-dispatch-storage-failure',async(page,native)=>{
  await fill(page);await invoke(page,'preview');await candidateReady(page);const before=await context(page);await page.evaluate(()=>__failWrites=true);const result=await invoke(page,'save'),after=await context(page);
  assert(result.ok&&result.result.outcome==='not_sent'&&!after.unconfirmed_save&&!after.pending_change.dispatched,'First pre-send storage failure became dispatched');assert(await page.locator('#edit-draft').isEnabled(),'Never-dispatched draft locked');assert(!fs.existsSync(native.project)&&await page.evaluate(()=>!__calls.includes('initial_apply')),'Storage failure dispatched native save');
  await page.reload();await initialReady(page);await candidateReady(page);assert(JSON.stringify((await context(page)).pending_change.request)===JSON.stringify(before.pending_change.request),'Reload changed checked first request');return{request:before.pending_change.request,outcome:'not_dispatched'};
 });
 await runCase('unconfirmed-retry-storage-and-handoff',async(page,native)=>{
  await fill(page);await invoke(page,'preview');await candidateReady(page);const before=await context(page),request=before.pending_change.request;
  await page.evaluate(()=>__dropApply='after');const lost=await invoke(page,'save');assert(lost.ok&&lost.result.outcome==='unconfirmed','Lost committed reply became refusal');assert(snapshot(native.project).revision===1,'Lost reply fixture did not commit');
  await page.evaluate(()=>__failWrites=true);const calls=await page.evaluate(()=>__calls.filter(n=>n==='initial_apply').length),retry=await invoke(page,'save'),after=await context(page);
  assert(retry.ok&&retry.result.outcome==='not_sent'&&after.unconfirmed_save&&after.pending_change.dispatched,'Failed retry persistence erased earlier dispatch');assert(await page.locator('#edit-draft').isDisabled(),'Unresolved original request unlocked editing');assert(await page.evaluate(()=>__calls.filter(n=>n==='initial_apply').length)===calls,'Failed retry persistence dispatched again');
  await page.reload();await initialReady(page);let c=await context(page);assert(c.unconfirmed_save&&JSON.stringify(c.pending_change.request)===JSON.stringify(request),'Reload lost dispatched request');for(const fault of ['receipt_zero_head','receipt_wrong_head']){await page.evaluate(value=>__fault=value,fault);const result=await invoke(page,'recover');assert(result.ok&&result.result.outcome==='unconfirmed'&&!(await context(page)).last_acknowledged_receipt,'Inconsistent first receipt observation acknowledged')}await page.evaluate(()=>__fault=null);c=await context(page);const recovered=await tool(page,'cse_recover_initial_creation',{guard:c.guard,request});assert(recovered.outcome==='committed'&&recovered.receipt.revision===1,'Exact first recovery failed');assert(snapshot(native.project).history.length===1,'Recovery duplicated first commit');
  const refusals=[];for(const fault of['wrong_open_receipt','wrong_open_project','wrong_open_view','stale_open_view','coherent_first_commit','coherent_first_bundle']){
   await page.evaluate(value=>__fault=value,fault);const result=await invoke(page,'openSaved');assert(!result.ok&&['response_binding','receipt'].includes(result.code),'Malformed handoff accepted: '+fault);assert(await page.evaluate(()=>__opened.length)===0,'Malformed response reached supplied saved-controller callback');refusals.push({fault,code:result.code});
  }
  await page.evaluate(()=>__fault=null);const stateReply=await page.context().request.get(native.origin+'/startup/state'),csrf=(await stateReply.json()).csrf;const edit=await page.context().request.post(native.origin+'/api/apply',{headers:{Origin:native.origin,'X-CSE-CSRF':csrf},data:{operation:'rename',request_id:crypto.randomUUID(),expected_revision:1,element_id:native.root_element_id,new_name:'Later'}});assert(edit.ok(),'Later native edit failed');assert((await invoke(page,'recover')).result.outcome==='committed'&&(await context(page)).initial_state.current_saved.revision===2,'Newer head not retained');await page.evaluate(()=>__fault='older_observation');assert((await invoke(page,'recover')).result.outcome==='receipt_unavailable'&&!(await context(page)).unconfirmed_save,'Older observation erased acknowledgement');await page.evaluate(()=>__fault='stale_observed_head');const stale=await invoke(page,'openSaved');assert(!stale.ok&&stale.code==='response_binding'&&await page.evaluate(()=>__opened.length)===0,'Older self-consistent saved view opened');await page.evaluate(()=>__fault=null);assert((await invoke(page,'openSaved')).ok&&await page.evaluate(()=>__opened.length)===1,'Valid saved handoff refused');
  await page.evaluate(async()=>{await cseInitialWorkbench.dispose();document.body.innerHTML='<p>Supplied saved-controller shell</p>';dispatchEvent(new Event('resize'))});assert((await context(page)).phase==='closed','Initial controller did not dispose');
  return{request,receipt:recovered.receipt,refusals,outcome:'recovered_once'};
 });
 for(const missing of [false,true])await runCase(missing?'unavailable-save-head':'contradictory-save-head',async(page,native)=>{
  await fill(page);await invoke(page,'preview');await candidateReady(page);const before=await context(page),request=before.pending_change.request;await page.evaluate(fault=>__fault=fault,missing?'unavailable_apply_head':'contradictory_apply_head');const result=await invoke(page,'save'),after=await context(page);
  assert(result.ok&&snapshot(native.project).revision===1,'Native acknowledgement fixture failed');
  if(missing){assert(result.result.outcome==='committed'&&after.last_acknowledged_receipt&&after.initial_state.target_observation==='unavailable','Unavailable current read erased a valid first receipt')}
  else{assert(result.result.outcome==='unconfirmed'&&after.unconfirmed_save&&!after.last_acknowledged_receipt&&!after.initial_state.current_saved,'Contradictory first head was acknowledged');await page.evaluate(()=>__fault=null);const recovered=await invoke(page,'recover');assert(recovered.result.outcome==='committed'&&!((await context(page)).unconfirmed_save),'Valid receipt could not repair contradictory response')}
  return{request,outcome:missing?'acknowledged_head_unavailable':'unconfirmed_then_recovered'};
 });
 await runCase('malformed-retained-acknowledgement',async(page,native)=>{
  await fill(page);await invoke(page,'preview');await candidateReady(page);
  const saved=await page.evaluate(()=>{const key=Object.keys(sessionStorage).find(key=>key.startsWith('cse-initial:'));return{key,value:sessionStorage.getItem(key)}});
  await page.evaluate(({key,value})=>{const state=JSON.parse(value);state.acknowledged={revision:1};sessionStorage.setItem(key,JSON.stringify(state))},saved);await page.reload();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Initial session unavailable'));assert(!(await context(page)).ready,'Malformed acknowledgement became ready');for(const id of['create-initial','recover-initial','open-saved'])assert(await page.locator('#'+id).isDisabled(),'Malformed retained state enabled '+id);assert(!fs.existsSync(native.project),'Malformed cache created a model');
  await page.evaluate(({key,value})=>sessionStorage.setItem(key,value),saved);await page.reload();await initialReady(page);await candidateReady(page);return{outcome:'blocked_without_discarding_original_intent'};
 });
 await runCase('async-intent-storage',async(page,native)=>{
  await fill(page);await page.locator('#root-name').fill('First draft');await page.locator('#root-name').fill('System');await invoke(page,'preview');await candidateReady(page);const c=await context(page),request=c.pending_change.request;
  const cached=await page.evaluate(()=>JSON.parse(sessionStorage.getItem(Object.keys(sessionStorage).find(key=>key.startsWith('cse-initial:')))));assert(cached.pending.request.new_name==='System'&&cached.pending.request.request_id===request.request_id,'Async earlier write replaced current checked intent');
  await page.evaluate(()=>__dropApply='before');const lost=await invoke(page,'save');assert(lost.result.outcome==='unconfirmed'&&!fs.existsSync(native.project),'Async lost dispatch not retained');await page.reload();await initialReady(page);assert((await context(page)).unconfirmed_save,'Async intent read did not precede ready');await page.evaluate(()=>__dropApply=null);const saved=await invoke(page,'save');assert(saved.result.outcome==='committed'&&snapshot(native.project).history.length===1,'Async exact save/recovery duplicated initial revision');return{request,receipt:saved.result.receipt,outcome:'async_ordered_exact_intent'};
 },{fault:'async_storage'});
 await runCase('disposal-before-dispatch',async(page,native)=>{
  await fill(page);await invoke(page,'preview');await candidateReady(page);const observations=[];
  for(const retry of [false,true]){
   if(retry){await page.reload();await initialReady(page);await candidateReady(page);await page.evaluate(()=>__dropApply='before');assert((await invoke(page,'save')).result.outcome==='unconfirmed','Retry fixture did not retain a prior unresolved dispatch');await page.evaluate(()=>__dropApply=null)}
   const before=await context(page),calls=await page.evaluate(()=>__calls.filter(n=>n==='initial_apply').length);
   await page.evaluate(()=>{__pauseNextWrite=true;globalThis.__saveAcrossDispose=cseInitialWorkbench.save()});await page.waitForFunction(()=>typeof __releaseWrite==='function');await page.evaluate(async()=>{await cseInitialWorkbench.dispose();document.body.innerHTML='<p>Supplied saved-controller shell</p>'});
   assert((await context(page)).phase==='closed','Controller remained open during paused storage');
   const result=await page.evaluate(async()=>{__releaseWrite();return __saveAcrossDispose});
   assert(result.outcome==='not_sent'&&result.error.code==='closed'&&result.unconfirmed_save===retry,'Disposal changed earlier dispatch certainty');assert(await page.evaluate(()=>__calls.filter(n=>n==='initial_apply').length)===calls,'Closed controller dispatched after storage resumed');
   const cached=await page.evaluate(()=>JSON.parse(sessionStorage.getItem(Object.keys(sessionStorage).find(key=>key.startsWith('cse-initial:')))));assert(cached.pending.dispatched===retry&&cached.unknown===retry&&cached.pending.request.request_id===before.pending_change.request.request_id,'Disposal lost the exact original recovery record');assert(!fs.existsSync(native.project),'Closed controller created a native project');observations.push({retry,outcome:result.outcome,retained_unconfirmed:cached.unknown,apply_calls:calls});
  }
  return{observations};
 });
 await runCase('disposal-with-dispatched-acknowledgement',async(page,native)=>{
  await fill(page);await invoke(page,'preview');await candidateReady(page);const before=await context(page);
  await page.evaluate(()=>{globalThis.__pauseApplyReply=true;globalThis.__saveAcrossDispose=cseInitialWorkbench.save()});await page.waitForFunction(()=>typeof __releaseApplyReply==='function');assert(snapshot(native.project).revision===1,'Paused acknowledgement did not commit native source');
  await page.evaluate(async()=>{await cseInitialWorkbench.dispose();document.body.innerHTML='<p>Supplied saved-controller shell</p>'});const result=await page.evaluate(async()=>{__releaseApplyReply();return __saveAcrossDispose});
  const closed=await context(page),cached=await page.evaluate(()=>JSON.parse(sessionStorage.getItem(Object.keys(sessionStorage).find(key=>key.startsWith('cse-initial:')))));assert(result.outcome==='committed'&&closed.phase==='closed'&&closed.last_acknowledged_receipt?.revision===1,'Unmount discarded an already-dispatched durable acknowledgement');assert(cached.unknown===false&&cached.acknowledged.commit===result.receipt.commit&&JSON.stringify(cached.raw)===JSON.stringify(before.raw_draft),'Unmount changed the durable acknowledgement or retained form');assert(await page.evaluate(()=>__calls.filter(n=>n==='initial_apply').length)===1&&snapshot(native.project).history.length===1,'Closed acknowledgement duplicated native dispatch');
  await page.reload();await initialReady(page);assert((await context(page)).last_acknowledged_receipt?.commit===result.receipt.commit,'Reload lost receipt retained after unmount');return{receipt:result.receipt,outcome:'closed_acknowledged_and_reopened'};
 });
 await runCase('disposal-during-registration',async(page,native)=>{
  await page.evaluate(()=>cseInitialWorkbench.dispose());assert((await context(page)).phase==='closed','Delayed registration disposal failed');
  await page.evaluate(()=>__releaseRegistration());await page.waitForFunction(()=>cseInitialSiteTools.registered.length===0&&__tools.size===0&&cseInitialSiteTools.status==='disposed');
  const result=await page.evaluate(()=>__closedTool.execute({}));assert(result.outcome==='refused'&&result.error.code==='closed','Retired callback remained usable');assert(await page.evaluate(()=>__registrationStarts.length)===1,'Registration continued after disposal');await page.evaluate(()=>cseInitialWorkbench.dispose());assert(!fs.existsSync(native.project),'Registration teardown created a project');return{outcome:'pending_registration_retired',started:await page.evaluate(()=>__registrationStarts),closed_callback:result};
 },{fault:'delayed_registration'});
 await runCase('wrong-initial-grant',async(page,native)=>{assert(!(await context(page)).ready,'Supplied response replaced the grant');for(const id of['create-initial','recover-initial','open-saved'])assert(await page.locator('#'+id).isDisabled(),'Wrong grant enabled '+id);assert(!fs.existsSync(native.project),'Wrong grant created model');return{outcome:'refused'}},{fault:'wrong_state'});
 const served=await Promise.all(deliveries);verifyShots(images);unchanged(inputs);
 fs.writeFileSync(path.join(out,'receipt.json'),JSON.stringify({status:'pass',claim:'Adversarial supplied browser transport/storage/font controls over real native/Git loopback; injected faults are not engineering verdicts or actual MCP/product-host qualification',inputs,driver_sha256:hash(fileURLToPath(import.meta.url)),browser_version:browser.version(),results,served_startup_scripts:served,images},null,2)+'\n');
}finally{await browser.close()}
