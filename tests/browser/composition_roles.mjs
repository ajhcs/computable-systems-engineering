// Native/Git-backed inspection and recovery; document.modelContext is a test double.
import fs from'node:fs';import path from'node:path';import{fileURLToPath}from'node:url';
import{createRequire}from'node:module';import{spawn,execFileSync}from'node:child_process';import{createHash,randomUUID}from'node:crypto';
const{chromium}=createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE);
if(!process.argv[2]||!process.env.TMPDIR)throw Error('Supply a fresh output directory and workspace TMPDIR.');
const root=fileURLToPath(new URL('../../',import.meta.url)),output=path.resolve(process.argv[2]);fs.mkdirSync(output,{mode:0o700});
const hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex'),digest=s=>createHash('sha256').update(s).digest('hex'),assert=(v,m)=>{if(!v)throw Error(m)},sleep=ms=>new Promise(r=>setTimeout(r,ms));
const sources=['tools/sysml/SysmlBridge.java','verifier/sysml.py','verifier/configuration.py','verifier/composition_edit.py','verifier/composition_inspection.py','verifier/composition_project.py','verifier/composition_session.py','verifier/composition_view.py','verifier/composition_fonts.py','verifier/kit_fonts.py','verifier/kit_templates.py','web/composition-reader.html','web/composition-workbench.html','web/composition-workbench.js','web/composition-site-tools.js','tests/browser/composition_roles_fixture.py','tests/fixtures/composition-role-inspection.json'];
const inputs=Object.fromEntries(sources.map(p=>[p,hash(path.join(root,p))])),fixtures=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/composition-role-inspection.json'))),observations=[];
const browser=await chromium.launch({executablePath:process.env.CSE_BROWSER_EXECUTABLE,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
async function fixture(name,caseId,work){
 const folder=path.join(output,name),log=fs.openSync(path.join(output,name+'.log'),'wx',0o600),images=[],errors=[];
 let server,terminal;const start=args=>{terminal=false;server=spawn('python3',['-B',...args],{cwd:root,env:process.env,stdio:['ignore',log,log]});server.on('exit',()=>terminal=true)};
 const stop=async()=>{if(!terminal){server.kill('SIGINT');await new Promise(r=>server.once('exit',r))}};
 start(['tests/browser/composition_roles_fixture.py',folder,caseId]);
 const page=await browser.newPage({viewport:{width:1440,height:1100}});page.setDefaultTimeout(90000);page.on('pageerror',e=>errors.push(String(e)));
 await page.addInitScript(()=>{globalThis.__tools=new Map();Object.defineProperty(document,'modelContext',{value:{registerTool:async t=>__tools.set(t.name,t)}})});
 const waitConnection=async file=>{for(let i=0;!fs.existsSync(file);i++){if(terminal||i>900)throw Error('Fixture startup');await sleep(100)}return JSON.parse(fs.readFileSync(file))};
 const ready=()=>page.waitForFunction(()=>typeof frameReady!=='undefined'&&frameReady&&!busy&&cseSiteTools.registered.length===16);
 const tool=(name,args={})=>page.evaluate(async({name,args})=>__tools.get(name).execute(args),{name,args}),context=async()=>(await tool('cse_get_context')).context;
 const state=()=>page.evaluate(async()=>(await(await fetch('/api/state')).json()).state),svg=()=>page.evaluate(async()=>await(await fetch('/view.svg')).text());
 const select=async row=>{const r=await tool('cse_select_element',{guard:(await context()).guard,element_id:row.element_id,occurrence_id:row.id});assert(r.outcome==='selected','Selection refused: '+JSON.stringify(r.error));return r.context};
 const save=async()=>{const c=await context(),r=await tool('cse_save_change',{guard:c.guard,request_id:c.pending_change.request.request_id});assert(r.outcome==='committed','Save refused: '+JSON.stringify(r.error));await ready();return r};
 const shot=async tag=>{const file=path.join(output,name+'-'+tag+'.png');await page.screenshot({path:file,fullPage:true});images.push({path:file,sha256:hash(file)})};
 let connection;
 try{
  connection=await waitConnection(path.join(folder,'connection.json'));await page.goto(connection.url);await ready();
  const restart=async()=>{await stop();const file=path.join(folder,'reopened.json');start(['scripts/composition_workbench.py','--project',connection.project,'--view-id','PC_CONTEXT','--connection-file',file]);connection=await waitConnection(file);await page.goto(connection.url);await ready()};
  const result=await work({page,folder,project:connection.project,ready,tool,context,state,svg,select,save,shot,restart});
  assert(!errors.length,'Browser errors: '+errors.join(';'));observations.push({case:name,status:'pass',...result,screenshots:images,errors});console.log(JSON.stringify({case:name,status:'pass'}));
 }catch(error){await page.screenshot({path:path.join(output,name+'-failed.png'),fullPage:true}).catch(()=>{});const diagnostic=await page.evaluate(()=>({revision:typeof state==='undefined'?null:state.revision,busy,dirty,draftKind,unknown,frameReady,selectedId,selectedOccurrenceId,editTargetId,editTargetOccurrenceId,pending:pending?.request,notice:document.getElementById('notice').textContent})).catch(()=>({unavailable:true}));fs.writeFileSync(path.join(output,name+'-failure.json'),JSON.stringify(diagnostic,null,2)+'\n');throw error}
 finally{await page.close();await stop();fs.closeSync(log)}
}
async function glyphs(page){
 await page.frame({name:'cse-saved-view'}).evaluate(()=>document.fonts.ready);
 const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');
 const{root:dom}=await cdp.send('DOM.getDocument',{depth:-1,pierce:true});
 function frameDoc(n){if(n.nodeName==='IFRAME'&&n.attributes?.includes('cse-saved-view')&&n.contentDocument)return n.contentDocument;for(const child of n.children||[]){const found=frameDoc(child);if(found)return found}return null}
 const{nodeIds}=await cdp.send('DOM.querySelectorAll',{nodeId:frameDoc(dom).nodeId,selector:'g[data-node-id] > text'}),fonts=[];
 for(const nodeId of nodeIds)fonts.push(...(await cdp.send('CSS.getPlatformFontsForNode',{nodeId})).fonts.filter(f=>f.glyphCount));
 assert(fonts.length&&fonts.every(f=>f.isCustomFont&&f.familyName.startsWith('DejaVu Sans')),'Original diagram glyph supplier substituted');await cdp.detach();return fonts;
}
try{
 for(const test of fixtures.cases)await fixture('inspect-'+test.id,test.id,async({page,tool,context,state,svg,select,shot})=>{
  const first=await state(),inspection=first.projection.inspection,original=await svg(),scope=inspection.scopes[0],checks=[];
  assert(scope.report.status===test.expected.status,'Wrong overall scope status');assert(JSON.stringify([...scope.report.checked].sort())===JSON.stringify([...test.expected.checked].sort()),'Changed checked coverage');
  assert(Object.keys(first.projection.nodes).length===1&&Object.keys(first.projection.edges).length===0,'Inspection invented ownership edges');
  for(const width of[1440,390]){
   await page.setViewportSize({width,height:1100});await page.frame({name:'cse-saved-view'}).evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));await sleep(100);const c=await context(),listed=await tool('cse_list_inspection_occurrences',{guard:c.guard,origin:null,offset:0,limit:100});
   assert(listed.outcome==='observed'&&listed.inspection_page.total===Object.keys(inspection.occurrences).length,'Inspection page omitted rows: '+JSON.stringify({outcome:listed.outcome,error:listed.error,total:listed.inspection_page?.total,expected:Object.keys(inspection.occurrences).length}));
   for(const role of Object.values(inspection.occurrences).filter(row=>row.role)){
    // Real keyboard activation of each retained context/role row.
    await page.frameLocator('#view').locator('[data-inspection-id="'+role.id+'"]').press('Enter');const selected=await context();
    assert(selected.selection.occurrence_id===role.id&&selected.selection.element_id===role.element_id,'Row selection changed native/logical identity');
    assert(JSON.stringify(selected.selection.role)===JSON.stringify(role.role),'Selection narrowed or rewrote role findings');
    assert(selected.configuration_reviews[0].report.status===test.expected.status,'Selected row masked full review');
    assert(await page.locator('#preview-layout').isDisabled(),'Unframed row enabled geometry');
    if(!role.element_id){assert(await page.locator('#preview-rename').isDisabled()&&await page.locator('#preview-multiplicity').isDisabled(),'Missing binding invented an edit target');assert(await page.locator('#restore-form button').isEnabled(),'Missing binding blocked project restoration')}
    if(role.origin==='external_role')assert(!selected.selection.role.selected_parent&&!selected.selection.native.is_composite,'External reference became an owned selected child');
    const before=selected.editing_target,refused=await tool('cse_preview_layout',{guard:selected.guard,element_id:role.element_id||'missing',box:{x:1,y:2,width:3,height:4}});
    assert(refused.outcome==='refused'&&!refused.context.has_form_draft&&JSON.stringify(refused.context.editing_target)===JSON.stringify(before),'Refused row geometry changed form values');
   }
   const bad=await tool('cse_select_element',{guard:(await context()).guard,element_id:null,occurrence_id:'toString'});assert(bad.outcome==='refused'&&bad.error.code==='target','Inherited JS property accepted as occurrence');
   const row=Object.values(inspection.occurrences).find(row=>row.origin==='selected_role');await select(row);await shot(String(width));
   // Returning from the tables must reveal the frame in the reader document,
   // as well as inside its independently scrollable SVG viewport.
   await select(inspection.occurrences.Current);
   const reveal=await page.frame({name:'cse-saved-view'}).evaluate(()=>{const r=document.querySelector('g[data-node-id="Current"]').getBoundingClientRect();return{top:r.top,bottom:r.bottom,document_height:innerHeight,scale:cseDiagramNavigation.state().scale}});
   assert(reveal.top>=11&&reveal.bottom<=reveal.document_height-11&&reveal.scale===1,'Frame ink lacks its document reveal inset: '+JSON.stringify(reveal));await shot(width+'-diagram');
   checks.push({width,selected:row.id,reveal,fonts:await glyphs(page)});
  }
  assert(await svg()===original&&(await state()).commit===first.commit,'Read-only inspection changed SVG or project');
  return{revision:first.revision,bundle_sha256:inspection.bundle_sha256,svg_sha256:digest(original),expected:test.expected,checks};
 });
 for(const width of[1440,390])await fixture('editing-'+width,'inherited',async({page,folder,project,ready,tool,context,state,svg,select,save,shot,restart})=>{
  await page.setViewportSize({width,height:1100});await page.frame({name:'cse-saved-view'}).evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));await sleep(100);const first=await state(),original=await svg(),role=Object.values(first.projection.inspection.occurrences).find(row=>row.origin==='selected_role'),decl=first.projection.inspection.occurrences['decl:'+role.element_id];
  let c=await select(decl);const staleGuard=c.guard;await page.locator('#rename-name').fill('sensorArray');
  for(const kind of['multiplicity','layout','restore','create_definition']){c=await context();const r=await tool('cse_preview_current_edit',{guard:c.guard,kind});assert(r.outcome==='refused'&&r.error.code==='retained_edit'&&r.context.editing_target.declared_name==='sensorArray','Another form consumed a rename draft')}
  c=await select(role);assert(c.editing_target.occurrence_id===decl.id&&c.selection.occurrence_id===role.id,'Same UUID retargeted draft occurrence');
  let r=await tool('cse_preview_current_edit',{guard:staleGuard,kind:'rename'});assert(r.error.code==='stale_context','Old interaction guard accepted');
  await page.locator('#return-target').press('Enter');assert(await page.locator('#rename-name').evaluate(e=>document.activeElement===e),'Return did not focus retained draft');
  assert((await context()).selection.occurrence_id===decl.id,'Return selected wrong occurrence');await page.locator('#discard-draft').click();
  // Semantic property edits on a role use its native declaration, without frame geometry.
  c=await select(role);r=await tool('cse_preview_multiplicity',{guard:c.guard,element_id:role.element_id,lower:0,upper:1});assert(r.outcome==='previewed'&&r.preview.configuration_reviews[0].report.status==='unknown','Role multiplicity preview incorrect');await save();
  assert((await state()).revision===2&&await svg()===original,'Role property edit changed ownership drawing');
  // A lost rename acknowledgement leaves this logical role unresolved, while retaining exact intent.
  c=await context();assert(c.selection.occurrence_id===role.id,'Save lost role occurrence');await page.locator('#rename-name').fill('sensorArray');await page.locator('#preview-rename').click();await page.waitForFunction(()=>pending&&!busy);
  c=await context();const request=c.pending_change.request;
  await page.route('**/api/apply',async route=>{await route.fetch();await route.abort('failed')},{times:1});r=await tool('cse_save_change',{guard:c.guard,request_id:request.request_id});assert(r.outcome==='unconfirmed','Lost response did not retain retry');await page.reload();await ready();c=await context();
  assert(c.unconfirmed_save&&JSON.stringify(c.pending_change.request)===JSON.stringify(request)&&c.editing_target.element_id===role.element_id&&c.editing_target.occurrence_id===role.id&&!c.editing_target.present&&c.editing_target.declared_name==='sensorArray'&&c.editing_target.base_revision===2,'Recovery changed missing-role target or raw draft');
  assert(c.selection.occurrence_id===role.id&&c.selection.element_id===null&&c.configuration_reviews[0].report.status==='fail','Reload silently rebound stale logical role');await shot('unacknowledged');
  r=await tool('cse_lookup_receipt',{request});assert(r.outcome==='committed'&&r.receipt.revision===3,'Missing-role receipt unavailable');await save();assert((await state()).revision===3,'Exact retry duplicated rename');c=await context();assert(c.selection.element_id===null,'Acknowledgement retargeted unresolved role');
  // Clean-start restoration refusal must leave a visible, discardable draft.
  await page.route('**/api/preview',route=>route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({error:{code:'stale_revision',detail:'Synthetic concurrent revision refusal'}})}),{times:1});
  r=await tool('cse_preview_restore',{guard:c.guard,target_revision:1});assert(r.outcome==='refused'&&r.error.code==='stale_revision'&&r.context.has_form_draft&&r.context.draft_kind==='restore','Failed clean restoration left an undiscardable lock');
  assert(await page.locator('#discard-draft').isVisible(),'Failed restoration has no visible discard');await page.locator('#discard-draft').press('Enter');c=await context();assert(!c.has_form_draft&&!c.draft_kind&&await page.locator('#restore-form button').isEnabled(),'Discard did not release restoration lock');
  r=await tool('cse_preview_restore',{guard:c.guard,target_revision:1});assert(r.outcome==='previewed','Unresolved selection blocked global restoration');await save();const restored=await state();assert(restored.revision===4&&restored.configuration_reviews[0].report.status==='pass','Restore was not monotonic or lost scope');
  assert(restored.projection.inspection.occurrences[role.id].element_id===role.element_id,'Restore lost original native UUID');
  await restart();assert((await state()).revision===4&&await svg()===original,'Fresh process changed restored drawing');
  const exported=path.join(folder,'exported');for(const command of['render','check-render'])execFileSync('python3',['-B','scripts/composition_project.py',command,'--project',project,'--view-id','PC_CONTEXT','--output',exported],{cwd:root,env:process.env,stdio:'pipe'});
  assert(fs.readFileSync(path.join(exported,'view.svg'),'utf8')===original,'Export diverged from original SVG');const kit=JSON.parse(fs.readFileSync(path.join(exported,'kit-usage.json')));for(const[id,pin]of Object.entries(kit.components))assert(hash(path.join(root,'assets/engineering-library/components',id+'.svg'))===pin,'Original master source changed');
  await shot('restored');return{width,original_uuid:role.element_id,role_occurrence:role.id,request,final_revision:4,restored_commit:restored.commit,svg_sha256:digest(original),fonts:await glyphs(page),export_manifest_sha256:hash(path.join(exported,'manifest.json'))};
 });
 await fixture('paging','large',async({page,tool,context,state,select,shot})=>{
  const first=await state(),inspection=first.projection.inspection,checks=[];
  for(const width of[1440,390]){
   await page.setViewportSize({width,height:1100});await page.frame({name:'cse-saved-view'}).evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));await sleep(100);
   // Reset each list through the same reveal path before keyboard paging.
   await select(inspection.occurrences[inspection.declarations[0]]);
   for(const region of['#declaration-rows','#role-rows']){
    if(region==='#role-rows')await select(inspection.occurrences[inspection.scopes[0].occurrences[0]]);
    const next=page.frameLocator('#view').locator(region+' [data-inspection-page="Next page"]');await next.press('Enter');
    let focus=await next.evaluate(e=>document.activeElement===e);assert(focus,'Paging lost focus in '+region);
    await next.press('Enter');focus=await next.evaluate(e=>document.activeElement===e);assert(focus,'Repeated paging lost focus in '+region);
    await page.frameLocator('#view').locator(region+' [data-inspection-page="Previous page"]').press('Enter');
    assert(await page.frameLocator('#view').locator(region+' [data-inspection-page="Previous page"]').evaluate(e=>document.activeElement===e),'Previous page lost focus');
    while(await next.isEnabled())await next.press('Enter');
    assert(await page.frameLocator('#view').locator(region+' [data-inspection-id]').first().evaluate(e=>document.activeElement===e),'Last page did not focus its returned row');
   }
   await shot(String(width));checks.push({width,keyboard_paging:'pass'});
  }
  for(const origin of['declaration','selected_role']){let offset=0,ids=[];do{const r=await tool('cse_list_inspection_occurrences',{guard:(await context()).guard,origin,offset,limit:100});assert(r.outcome==='observed','Large inspection page refused');ids.push(...r.inspection_page.items.map(row=>row.id));offset=r.inspection_page.next_offset}while(offset!==null);const expected=Object.values(inspection.occurrences).filter(row=>row.origin===origin);assert(ids.length===expected.length&&ids.length===new Set(ids).size&&ids.length>100,'Large page coverage truncated')}
  assert((await state()).commit===first.commit,'Paging changed saved model');return{counts:inspection.counts,checks};
 });
 assert(sources.every(p=>hash(path.join(root,p))===inputs[p]),'Source changed during browser qualification');
 fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({claim:'Local Chromium/native/Git inspection, editing, recovery and export; synthetic site host only, no actual Codex/ChatGPT acceptance',browser:browser.version(),inputs,driver_sha256:hash(fileURLToPath(import.meta.url)),observations},null,2)+'\n');
}finally{await browser.close()}
