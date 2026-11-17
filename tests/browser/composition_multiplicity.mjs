// Real native/Git-backed browser editing; host registration is a test double.
import fs from 'node:fs';import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn,execFileSync} from 'node:child_process';import {createHash,randomUUID} from 'node:crypto';import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE||'playwright');
if(!process.argv[2]||!process.env.TMPDIR)throw Error('Supply a fresh output directory and explicit TMPDIR.');
const root=fileURLToPath(new URL('../../',import.meta.url)),output=path.resolve(process.argv[2]);fs.mkdirSync(output);
const hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex'),assert=(c,m)=>{if(!c)throw Error(m);},sleep=ms=>new Promise(r=>setTimeout(r,ms));
const sourceNames=['tools/sysml/SysmlBridge.java','verifier/composition_edit.py','verifier/composition_project.py','verifier/composition_session.py','verifier/composition_view.py','verifier/composition_inspection.py','web/composition-reader.html','web/composition-workbench.html','web/composition-workbench.js','web/composition-site-tools.js'];
const sourcePins=Object.fromEntries(sourceNames.map(name=>[name,hash(path.join(root,name))]));
const browser=await chromium.launch({executablePath:process.env.CSE_BROWSER_EXECUTABLE,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
const observations=[];
try{for(const width of [1440,390])for(const view of ['PC_USAGE','PC_DEFINITION']){
 const name=view+'-'+width,folder=path.join(output,name),log=fs.openSync(path.join(output,name+'.log'),'wx');
 let server=spawn('python3',['-B','tests/browser/composition_fixture.py',folder,view],{cwd:root,env:process.env,stdio:['ignore',log,log]});
 let terminal=false;server.on('exit',()=>terminal=true);
 const page=await browser.newPage({viewport:{width,height:1100}}),errors=[];page.setDefaultTimeout(90000);page.on('pageerror',e=>errors.push(String(e)));
 await page.addInitScript(()=>{globalThis.__tools=new Map();Object.defineProperty(document,'modelContext',{value:{registerTool:async t=>__tools.set(t.name,t)}});});
 try{
  for(let n=0;!fs.existsSync(path.join(folder,'connection.json'));n++){if(terminal||n>900)throw Error('Fixture startup');await sleep(100);}
  let connection=JSON.parse(fs.readFileSync(path.join(folder,'connection.json')));
  const projectPath=connection.project;
  const ready=()=>page.waitForFunction(()=>typeof frameReady!=='undefined'&&frameReady&&!busy&&globalThis.cseSelectionContext?.selected_element_ids?.length===1&&globalThis.cseSiteTools?.registered.length===15);
  await page.goto(connection.url);await ready();
  const tool=(name,args={})=>page.evaluate(async({name,args})=>await __tools.get(name).execute(args),{name,args});
  const context=async()=> (await tool('cse_get_context')).context;
  const state=()=>page.evaluate(async()=> (await(await fetch('/api/state')).json()).state);
  const select=async occurrence=>{const c=await context(),id=(await state()).projection.nodes[occurrence].element_id;const r=await tool('cse_select_element',{guard:c.guard,element_id:id,occurrence_id:occurrence});assert(r.outcome==='selected','Select failed');return r.context;};
  const save=async()=>{const c=await context(),r=await tool('cse_save_change',{guard:c.guard,request_id:c.pending_change.request.request_id});assert(r.outcome==='committed','Save did not acknowledge: '+JSON.stringify(r));await ready();return r;};
  const screenshots=[],screenshot=async label=>{const p=path.join(output,name+'-'+label+'.png');await page.screenshot({path:p,fullPage:true});screenshots.push({path:p,sha256:hash(p)});};
  const first=await state(),svgFirst=await page.evaluate(async()=>await(await fetch('/view.svg')).text());
  if(view==='PC_DEFINITION'){
   const c=await select('Module');
   assert(await page.locator('#multiplicity-lower').isDisabled()&&await page.locator('#multiplicity-upper').isDisabled(),'Definition acquired editable bounds');
   assert(c.editing_target.multiplicity.lower===''&&c.editing_target.multiplicity.upper==='','Definition acquired fake default bounds');
   const r=await tool('cse_preview_multiplicity',{guard:c.guard,element_id:c.guard.selected_element_id,lower:1,upper:2});
   assert(r.outcome==='refused'&&r.error.code==='element_kind'&&!r.context.has_form_draft,'Definition tool changed a draft');
   assert((await state()).commit===first.commit,'Definition changed the model');await screenshot('disabled');
   assert(!errors.length,'Browser script errors');observations.push({width,view,status:'pass',unchanged_commit:first.commit,screenshots,errors});
   continue;
  }
  let c=await select('Left');const identity=c.guard.selected_element_id,scope=first.configuration_reviews[0].scope_sha256;
  assert(c.editing_target.multiplicity.lower==='2'&&c.editing_target.multiplicity.upper==='2','Saved native bounds not loaded');
  await page.locator('#multiplicity-lower').fill('0');await page.locator('#multiplicity-upper').fill('1');
  await select('Optional');c=await context();assert(c.editing_target.element_id===identity&&c.editing_target.multiplicity.lower==='0'&&c.has_form_draft,'Inspection retargeted bound draft');
  let r=await tool('cse_preview_current_edit',{guard:c.guard,kind:'multiplicity'});
  assert(r.outcome==='previewed'&&r.request.element_id===identity&&r.preview.configuration_reviews[0].report.status==='unknown','Human draft preview lost its target/findings');
  assert((await state()).commit===first.commit,'Preview published source');await screenshot('optional-preview');
  await save();let current=await state();assert(current.revision===2&&current.configuration_reviews[0].report.status==='unknown'&&current.configuration_reviews[0].scope_sha256===scope,'Optional source/scope mismatch');
  c=await select('Left');r=await tool('cse_preview_multiplicity',{guard:c.guard,element_id:identity,lower:0,upper:0});
  assert(r.outcome==='previewed'&&r.preview.configuration_reviews[0].report.status==='fail','Suppressed candidate did not fail selected presence');
  const lostRequest=r.request;
  await page.route('**/api/apply',async route=>{await route.fetch();await route.abort('failed');},{times:1});
  c=await context();r=await tool('cse_save_change',{guard:c.guard,request_id:lostRequest.request_id});
  assert(r.outcome==='unconfirmed'&&r.context.unconfirmed_save,'Lost acknowledgement discarded retry intent');
  await page.reload();await ready();c=await context();assert(c.unconfirmed_save&&c.pending_change.request.request_id===lostRequest.request_id&&c.pending_change.request.lower===0&&c.pending_change.request.upper===0&&c.editing_target.multiplicity.lower==='0'&&c.editing_target.multiplicity.upper==='0'&&c.editing_target.base_revision===lostRequest.expected_revision,'Reload changed exact multiplicity request or visible retained values');await screenshot('lost-response');
  r=await tool('cse_lookup_receipt',{request:lostRequest});assert(r.outcome==='committed'&&r.receipt.revision===3,'Typed receipt lookup lost saved bounds');
  await save();assert((await state()).revision===3,'Retry duplicated suppressed change');
  c=await select('Left');await page.locator('#multiplicity-lower').fill('1');await page.locator('#multiplicity-upper').fill('3');
  const external={operation:'set_multiplicity',request_id:randomUUID(),expected_revision:3,element_id:identity,lower:1,upper:4},requestPath=path.join(folder,'external-request.json');fs.writeFileSync(requestPath,JSON.stringify(external));
  execFileSync('python3',['-B','scripts/composition_project.py','apply','--project',projectPath,'--request',requestPath],{cwd:root,env:process.env});
  c=await context();r=await tool('cse_preview_current_edit',{guard:c.guard,kind:'multiplicity'});assert(r.outcome==='refused'&&r.error.code==='stale_revision','Stale native bounds overwrote another writer');
  await tool('cse_refresh_project',{guard:(await context()).guard});await ready();c=await context();assert(c.editing_target.element_id===identity&&c.editing_target.multiplicity.upper==='3','Conflict refresh changed target/values');
  r=await tool('cse_preview_current_edit',{guard:c.guard,kind:'multiplicity'});assert(r.outcome==='previewed'&&r.request.expected_revision===4,'Fresh multiplicity preview refused');await save();
  current=await state();assert(current.revision===5&&current.configuration_reviews[0].report.status==='pass'&&current.configuration_reviews[0].scope_sha256===scope,'Positive bounds did not reconcile unchanged scope');
  c=await select('Unbounded');assert(c.editing_target.multiplicity.lower===''&&c.editing_target.multiplicity.upper==='','Unsupported bound invented numeric defaults');
  r=await tool('cse_preview_multiplicity',{guard:c.guard,element_id:c.guard.selected_element_id,lower:1,upper:3});assert(r.outcome==='previewed','Finite replacement of unbounded source refused');await save();
  c=await select('Left');r=await tool('cse_preview_multiplicity',{guard:c.guard,element_id:identity,lower:2147483646,upper:2147483647});assert(r.outcome==='previewed','Native maximum range refused');await save();await select('Left');
  current=await state();assert(current.revision===7&&current.projection.nodes.Left.native.source_multiplicity==='[2147483646..2147483647]','Maximum source bounds truncated');
  const group=page.frameLocator('#view').locator('g[data-node-id="Left"]');await group.scrollIntoViewIfNeeded();
  const fit=await group.evaluate(group=>{const box=group.getBoundingClientRect(),texts=[...group.querySelectorAll(':scope > text')];return{lines:texts.map(t=>t.textContent),fits:texts.every(t=>{const r=t.getBoundingClientRect();return r.left>=box.left&&r.right<=box.right&&r.top>=box.top&&r.bottom<=box.bottom;})};});
  assert(fit.fits&&fit.lines.includes('[2147483646..2147483647]'),'Maximum range clipped or fragmented in original SVG');
  const inner=page.frame({name:'cse-saved-view'});await inner.evaluate(()=>document.fonts.ready);
  const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');
  const {root:dom}=await cdp.send('DOM.getDocument',{depth:-1,pierce:true});
  function frameDocument(n){if(n.nodeName==='IFRAME'&&n.attributes?.includes('cse-saved-view')&&n.contentDocument)return n.contentDocument;for(const c of n.children||[]){const found=frameDocument(c);if(found)return found;}return null;}
  const {nodeIds}=await cdp.send('DOM.querySelectorAll',{nodeId:frameDocument(dom).nodeId,selector:'g[data-node-id="Left"] > text'}),fonts=[];
  for(const nodeId of nodeIds){const data=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});fonts.push(...data.fonts.filter(f=>f.glyphCount));}
  assert(fonts.length&&fonts.every(f=>f.isCustomFont&&f.familyName.startsWith('DejaVu Sans')),'Maximum-bound glyph font substitution');await screenshot('maximum');
  c=await context();r=await tool('cse_preview_restore',{guard:c.guard,target_revision:1});assert(r.outcome==='previewed','Original source restoration preview refused');await save();
  current=await state();assert(current.revision===8&&current.projection.nodes.Left.native.source_multiplicity==='[2]'&&current.configuration_reviews[0].scope_sha256===scope,'Restoration changed source identity/scope');
  server.kill('SIGINT');await new Promise(resolve=>server.once('exit',resolve));terminal=false;const nextConnection=path.join(folder,'reopen-connection.json');
  server=spawn('python3',['-B','scripts/composition_workbench.py','--project',projectPath,'--view-id',view,'--connection-file',nextConnection],{cwd:root,env:process.env,stdio:['ignore',log,log]});server.on('exit',()=>terminal=true);
  for(let n=0;!fs.existsSync(nextConnection);n++){if(terminal||n>900)throw Error('Fresh process startup');await sleep(100);}
  connection=JSON.parse(fs.readFileSync(nextConnection));await page.goto(connection.url);await ready();c=await select('Left');
  const reopened=await state(),svgReopened=await page.evaluate(async()=>await(await fetch('/view.svg')).text());
  assert(reopened.revision===8&&c.guard.selected_element_id===identity&&svgReopened===svgFirst&&reopened.configuration_reviews[0].report.status==='pass','Fresh process changed restored model/SVG');await screenshot('reopened');
  const offline=path.join(folder,'offline');execFileSync('python3',['-B','scripts/composition_project.py','render','--project',projectPath,'--view-id',view,'--output',offline],{cwd:root,env:process.env});
  execFileSync('python3',['-B','scripts/composition_project.py','check-render','--project',projectPath,'--view-id',view,'--output',offline],{cwd:root,env:process.env});
  assert(fs.readFileSync(path.join(offline,'view.svg'),'utf8')===svgFirst,'Export diverged from saved SVG');assert(!errors.length,'Browser script errors');
  observations.push({width,view,status:'pass',final_revision:reopened.revision,commit:reopened.commit,identity,retained_scope_sha256:scope,maximum_fit:fit,fonts,lost_request_id:lostRequest.request_id,screenshots,errors});
  console.log(JSON.stringify({case:name,status:'pass'}));
 }catch(error){await page.screenshot({path:path.join(output,name+'-failed.png'),fullPage:true}).catch(()=>{});throw error;}
 finally{await page.close();if(!terminal){server.kill('SIGINT');await new Promise(resolve=>server.once('exit',resolve));}fs.closeSync(log);}
}
assert(sourceNames.every(name=>hash(path.join(root,name))===sourcePins[name]),'Source changed during browser checks');
fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({claim:'Actual local Chromium/native/Git property edit/recovery/export checks; synthetic site callbacks only, not actual Codex/ChatGPT acceptance',browser:browser.version(),inputs:sourcePins,driver_sha256:hash(fileURLToPath(import.meta.url)),fixture_sha256:hash(path.join(root,'tests/browser/composition_fixture.py')),observations},null,2)+'\n');
}finally{await browser.close();}
