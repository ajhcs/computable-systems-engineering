import fs from 'node:fs';import path from 'node:path';import{fileURLToPath}from'node:url';
import{spawn}from'node:child_process';import{createHash}from'node:crypto';import{createRequire}from'node:module';
const{chromium}=createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE||'playwright');
const root=fileURLToPath(new URL('../../',import.meta.url)),output=path.resolve(process.argv[2]);fs.mkdirSync(output);
const hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex'),assert=(ok,message)=>{if(!ok)throw Error(message)},sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const sources=['web/composition-workbench.js','web/composition-workbench.html','web/composition-site-tools.js','web/composition-mcp-host.js','web/composition-reader.html','verifier/composition_session.py','verifier/composition_project.py','verifier/composition_view.py','tests/browser/composition_roles_fixture.py'];
const inputs=Object.fromEntries(sources.map(name=>[name,hash(path.join(root,name))])),driverHash=hash(fileURLToPath(import.meta.url)),observations=[];
const browser=await chromium.launch({executablePath:process.env.CSE_BROWSER_EXECUTABLE,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
async function fixture(name,work){
 const folder=path.join(output,name);const log=fs.openSync(path.join(output,name+'.log'),'wx');
 const child=spawn('python3',['-B','tests/browser/composition_roles_fixture.py',folder,'inherited'],{cwd:root,env:process.env,stdio:['ignore',log,log]});let ended=false;child.on('exit',()=>ended=true);
 try{for(let n=0;!fs.existsSync(path.join(folder,'connection.json'));n++){if(ended||n>900)throw Error('Fixture failed');await sleep(100)}const connection=JSON.parse(fs.readFileSync(path.join(folder,'connection.json')));const result=await work(connection);observations.push({case:name,status:'pass',...result});console.log(JSON.stringify({case:name,status:'pass'}));}
 finally{if(!ended){const stopped=new Promise(resolve=>child.once('exit',resolve));child.kill('SIGINT');await stopped}fs.closeSync(log)}
}
async function pageFor(connection,options={}){
 const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[],requests=[];page.setDefaultTimeout(90000);page.on('pageerror',error=>errors.push(String(error)));page.on('request',request=>{const name=new URL(request.url()).pathname;if(name.startsWith('/api/')||name==='/session')requests.push(name);});
 await page.addInitScript(options=>{
  if(window!==window.top)return;
  globalThis.__tools=new Map();Object.defineProperty(document,'modelContext',{value:{registerTool:async tool=>__tools.set(tool.name,tool)}});
  if(options.invalid){Object.defineProperty(globalThis,'cseCompositionHost',{value:options.invalid==='undefined'?undefined:options.invalid==='null'?null:{version:'wrong'}});return;}
  if(!options.proxy)return;
  let csrf,firstState,releaseRead,releaseWrite;
  const readGate=new Promise(resolve=>releaseRead=resolve),writeGate=new Promise(resolve=>releaseWrite=resolve),originalFetch=globalThis.fetch;
  const test={requests:[],artifacts:[],readStarted:false,writeStarted:false,failWrite:false,failCleanup:false,
   releaseRead:()=>releaseRead(),releaseWrite:()=>releaseWrite(),originalFetch};globalThis.providerTest=test;
  globalThis.cseCompositionHost={version:'cse-composition-host-1',kind:'test_proxy',
   openArtifact:options.artifact?async artifact=>{test.artifacts.push(artifact);return{isError:false};}:null,
   async request({operation,payload}){
    test.requests.push(operation);const routes={session:'/session',state:'/api/state',head:'/api/head',inspection:'/api/inspection',preview:'/api/preview',apply:'/api/apply',receipt:'/api/receipt'};
    const init={credentials:'same-origin',cache:'no-store'};
    if(payload!==undefined)Object.assign(init,{method:'POST',headers:{'Content-Type':'application/json','X-CSE-CSRF':csrf||''},body:JSON.stringify(payload)});
    const response=await originalFetch(routes[operation],init),body=await response.json();if(body.csrf)csrf=body.csrf;if(operation==='state'&&!firstState)firstState=body.state;
    if(operation==='state'&&options.artifact&&!test.omitArtifactHash){
     const bytes=await (await originalFetch('/view.svg')).arrayBuffer();
     const digest=await crypto.subtle.digest('SHA-256',bytes);
     test.artifactHash=[...new Uint8Array(digest)].map(byte=>byte.toString(16).padStart(2,'0')).join('');
     body.state.artifact_hashes={'view.svg':test.artifactHash};
    }
    if(operation==='state'&&test.omitArtifactHash)delete body.state.artifact_hashes;
    if(operation==='apply'&&body.receipt){if(test.corruptProject)body.receipt.project_id='00000000-0000-0000-0000-000000000000';if(test.corruptDigest)body.receipt.request_sha256='0'.repeat(64);}
    return{status:response.status,body};
   },intentStorage:{
    async getItem(key){
     test.readStarted=true;await readGate;const old=sessionStorage.getItem(key);if(old!==null)return old;
     if(options.artifact)return null;
     const row=Object.values(firstState.projection.inspection.occurrences).find(row=>row.origin==='selected_role');
     const request={operation:'rename',request_id:crypto.randomUUID(),expected_revision:1,element_id:row.element_id,new_name:'sensorArray'};
     return JSON.stringify({request,selectedId:row.element_id,selectedOccurrenceId:row.id,editTargetId:row.element_id,editTargetOccurrenceId:row.id,editTargetName:row.element,draftKind:'rename',baseCommit:firstState.commit,description:'Retained exact intent',fields:{'rename-name':'sensorArray'}});
    },
    async setItem(key,value){test.writeStarted=true;if(test.failWrite)throw Error('Synthetic storage refusal');await writeGate;sessionStorage.setItem(key,value);test.stored=value;},
    async removeItem(key){if(test.failCleanup)throw Error('Synthetic cleanup refusal');sessionStorage.removeItem(key);},
   }};
 },options);
 await page.goto(connection.url);return{page,errors,requests};
}
const context=page=>page.evaluate(()=>cseWorkbench.context()),ready=page=>page.waitForFunction(()=>globalThis.cseWorkbench?.context().ready&&!busy);
try{
 await fixture('invalid-provider',async connection=>{
  const variants=[];
  for(const invalid of['undefined','null','partial']){const{page,errors,requests}=await pageFor(connection,{invalid});
   await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('incomplete physical-composition host'));await sleep(1700);
   assert(!(await context(page)).ready&&!requests.length,'Incomplete provider fell back to local transport');assert(!errors.length,'Invalid provider threw a page error');variants.push(invalid);await page.close();}
  return{variants,transport_side_effects:0};
 });
 await fixture('async-intent-and-subscribers',async connection=>{
  const{page,errors}=await pageFor(connection,{proxy:true});
  await page.waitForFunction(()=>providerTest.readStarted);const loading=await page.evaluate(()=>({ready:cseWorkbench.context().ready,fieldset:document.getElementById('edits').disabled,input:document.getElementById('rename-name').matches(':disabled'),busy}));
  assert(!loading.ready&&loading.fieldset&&loading.input&&loading.busy,'Async intent read exposed an editable view: '+JSON.stringify(loading));
  assert(await page.locator('#view').evaluate(e=>getComputedStyle(e).visibility==='hidden'),'Recovery displayed a premature selection');
  await page.evaluate(()=>providerTest.releaseRead());await ready(page);let c=await context(page);const request=c.pending_change.request;
  assert(c.unconfirmed_save&&c.editing_target.declared_name==='sensorArray'&&c.editing_target.occurrence_id===c.selection.occurrence_id,'Async recovery lost exact fields/occurrence');
  assert(await page.evaluate(()=>globalThis.fetch===providerTest.originalFetch),'Provider replaced global fetch');
  await page.evaluate(()=>{
   cseWorkbench.subscribe(snapshot=>{if(snapshot.configuration_reviews)snapshot.configuration_reviews[0].report.status='forged';});
   cseWorkbench.subscribe(()=>{throw Error('Synchronous subscriber failure')});
   cseWorkbench.subscribe(async()=>{throw Error('Asynchronous subscriber failure')});
   providerTest.failWrite=true;
  });
  await page.locator('#save').click();await page.waitForFunction(()=>!busy&&document.getElementById('notice').textContent.includes('Save was not sent'));
  assert(!(await page.evaluate(()=>providerTest.requests.includes('apply'))),'Failed storage dispatched an apply');
  c=await context(page);assert(c.unconfirmed_save&&c.pending_change.request.request_id===request.request_id&&c.configuration_reviews[0].report.status==='pass','Subscriber/storage failure changed original intent or native findings');
  await page.evaluate(()=>{providerTest.failWrite=false;providerTest.failCleanup=true});await page.locator('#save').click();await page.waitForFunction(()=>providerTest.writeStarted&&busy);
  assert(!(await page.evaluate(()=>providerTest.requests.includes('apply'))),'Apply started before async intent persistence');
  await page.evaluate(()=>providerTest.releaseWrite());await page.waitForFunction(()=>cseWorkbench.context().guard.model_revision===2&&cseWorkbench.context().ready&&!busy);
  c=await context(page);assert(c.last_acknowledged_receipt.revision===2&&!c.pending_change&&!c.unconfirmed_save,'Cleanup failure revoked a known durable acknowledgement');
  assert(c.configuration_reviews[0].report.status==='fail'&&!JSON.stringify(c).includes('csrf'),'Native scope or credential boundary changed');
  assert((await page.locator('#notice').textContent()).includes('cleanup failed'),'Acknowledged cleanup failure was hidden');
  await page.reload();await page.waitForFunction(()=>providerTest.readStarted);assert(!(await context(page)).ready,'Reload bypassed async recovery');await page.evaluate(()=>providerTest.releaseRead());await ready(page);
  c=await context(page);assert(c.unconfirmed_save&&c.pending_change.request.request_id===request.request_id&&c.editing_target.declared_name==='sensorArray','Reload replaced acknowledged stale intent');
  await page.evaluate(()=>providerTest.releaseWrite());await page.locator('#save').click();await page.waitForFunction(()=>cseWorkbench.context().ready&&!busy&&!cseWorkbench.context().pending_change);
  c=await context(page);assert(c.guard.model_revision===2&&c.last_acknowledged_receipt.request_id===request.request_id,'Exact retry duplicated publication');assert(!errors.length,'Subscriber fault escaped into page errors: '+errors.join(';'));
  const screenshot=path.join(output,'async-intent-final.png');await page.screenshot({path:screenshot,fullPage:true});await page.close();return{request,final_revision:2,screenshot:{path:screenshot,sha256:hash(screenshot)},errors};
 });
 await fixture('superseded-font-completion',async connection=>{
  const{page,errors}=await pageFor(connection);await ready(page);const first=await context(page);
  await page.evaluate(()=>{globalThis.__fontGates=[];globalThis.__holdFonts=true;});
  await page.addInitScript(()=>{if(window===window.top)return;const load=FontFace.prototype.load;FontFace.prototype.load=function(...args){const result=load.apply(this,args);if(!parent.__holdFonts)return result;return result.then(face=>new Promise((resolve,reject)=>parent.__fontGates.push({resolve:()=>resolve(face),reject})));};});
  await page.locator('#refresh').click();await page.waitForFunction(()=>__fontGates.length===4&&cseWorkbench.context().view_status==='checking_fonts');
  assert(!(await context(page)).ready&&await page.locator('#view').evaluate(e=>getComputedStyle(e).visibility==='hidden'),'Pending fonts displayed a qualified drawing');
  await page.evaluate(()=>__holdFonts=false);await page.locator('#refresh').click();await ready(page);
  await page.evaluate(()=>{for(const gate of __fontGates)gate.reject(Error('Superseded font refusal'));});await sleep(150);
  const after=await context(page);assert(after.ready&&after.view_status==='ready'&&after.guard.commit===first.guard.commit,'Stale font failure hid/replaced the newer saved view');
  assert(await page.locator('#view').evaluate(e=>getComputedStyle(e).visibility==='visible'),'New drawing hidden by stale font failure');assert(!errors.length,'Font race escaped page errors');await page.close();return{revision:after.guard.model_revision,superseded_font_loads:4,errors};
 });
 await fixture('exact-saved-artifact-binding',async connection=>{
  const {page,errors}=await pageFor(connection,{proxy:true,artifact:true});
  await page.waitForFunction(()=>providerTest.readStarted);
  await page.evaluate(()=>providerTest.releaseRead());
  await ready(page);
  const saved=(await context(page)).guard;
  const view=page.frameLocator('#view');
  await view.getByRole('link',{name:'SVG',exact:true}).click();
  await page.waitForFunction(()=>providerTest.artifacts.length===1);
  const {artifacts:[artifact],artifactHash}=await page.evaluate(()=>providerTest);
  assert(artifact.kind==='view.svg'&&artifact.commit===saved.commit&&artifact.revision===saved.model_revision,
    'Artifact lost its saved revision identity');
  assert(artifact.view_id===saved.view_id&&artifact.bundle_sha256===saved.bundle_sha256&&artifact.expected_sha256===artifactHash,
    'Artifact lost its exact view, bundle or byte digest');
  const exportView=args=>page.evaluate(args=>__tools.get('cse_export_saved_view').execute(args),args);
  await page.locator('#rename-name').fill('Retained export draft');
  const draft=await context(page);
  assert(draft.has_form_draft,'Expected a pending form draft');
  const old=await exportView({guard:{...draft.guard,commit:'0'.repeat(40)},kind:'view.svg'});
  assert(old.outcome==='refused'&&old.error.code==='stale_context','Stale tool context allowed export');
  const exported=await exportView({guard:draft.guard,kind:'view.svg'});
  assert(exported.outcome==='transfer_requested','Agent export was refused');
  const transfers=await page.evaluate(()=>providerTest.artifacts);
  assert(transfers.length===2&&JSON.stringify(transfers[0])===JSON.stringify(transfers[1]),
    'Diagram and site tool requested different saved artifacts');
  assert(exported.context.has_form_draft&&await page.locator('#rename-name').inputValue()==='Retained export draft',
    'Export changed the pending draft');
  const missing=await exportView({guard:exported.context.guard,kind:'view.json'});
  assert(missing.outcome==='refused'&&missing.error.code==='artifact_unavailable',
    'Site tool transferred an artifact without a saved digest');
  await page.evaluate(()=>providerTest.omitArtifactHash=true);
  await page.locator('#refresh').click();
  await page.waitForFunction(()=>!busy&&frameReady);
  assert(await view.getByRole('link',{name:'SVG',exact:true}).count()===0
    &&await view.locator('a[aria-disabled=true]').filter({hasText:/^SVG$/}).count()===1,
    'An artifact without a saved digest stayed actionable');
  assert(!errors.length,errors.join('; '));
  await page.close();
  return{artifact,missing_digest_refused:true,site_guard_refused:true,site_and_link_same_artifact:true};
 });
 await fixture('receipt-project-and-payload-binding',async connection=>{
  const{page,errors}=await pageFor(connection,{proxy:true});await page.waitForFunction(()=>providerTest.readStarted);await page.evaluate(()=>{providerTest.releaseRead();providerTest.releaseWrite()});await ready(page);
  const request=(await context(page)).pending_change.request;
  for(const fault of['corruptProject','corruptDigest']){
   await page.evaluate(fault=>{providerTest.corruptProject=false;providerTest.corruptDigest=false;providerTest[fault]=true},fault);
   await page.locator('#save').click();await page.waitForFunction(()=>!busy&&cseWorkbench.context().unconfirmed_save);
   const c=await context(page);assert(c.guard.model_revision===1&&!c.last_acknowledged_receipt&&c.pending_change.request.request_id===request.request_id,'Mismatched receipt was acknowledged or changed intent: '+fault);
   assert(JSON.stringify(c.pending_change.request)===JSON.stringify(request),'Mismatched receipt replaced exact payload');
  }
  await page.evaluate(()=>{providerTest.corruptProject=false;providerTest.corruptDigest=false});await page.locator('#save').click();await page.waitForFunction(()=>cseWorkbench.context().ready&&!busy&&!cseWorkbench.context().pending_change);
  const c=await context(page);assert(c.guard.model_revision===2&&c.last_acknowledged_receipt.request_id===request.request_id,'Valid recovery duplicated publication');assert(!errors.length,'Receipt failure escaped page errors');await page.close();return{request,rejected_receipt_fields:['project_id','request_sha256'],final_revision:2,errors};
 });
 assert(hash(fileURLToPath(import.meta.url))===driverHash,'Driver changed');for(const[name,pin]of Object.entries(inputs))assert(hash(path.join(root,name))===pin,'Source changed '+name);
 fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({claim:'Real local native/Git browser checks with explicit test provider; no actual Codex/ChatGPT or hosted durability qualification',browser:browser.version(),driver_sha256:driverHash,inputs,observations},null,2)+'\n');
}finally{await browser.close()}
