// Native reference-name edits through real local controls/Git. Site host is a test double.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {spawn,execFileSync} from 'node:child_process';import {createHash} from 'node:crypto';import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE||'playwright');
if(!process.argv[2]||!process.env.TMPDIR)throw Error('Supply a fresh output directory and explicit TMPDIR.');
const root=fileURLToPath(new URL('../../',import.meta.url)),output=path.resolve(process.argv[2]);fs.mkdirSync(output,{mode:0o700});
const replacementNames=process.argv.includes('--replacement-names');
const hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex'),assert=(ok,m)=>{if(!ok)throw Error(m)},sleep=ms=>new Promise(r=>setTimeout(r,ms));
const sourceNames=['tools/sysml/SysmlBridge.java','verifier/sysml.py','verifier/composition_edit.py','verifier/composition_project.py','verifier/composition_session.py','verifier/composition_view.py','verifier/composition_inspection.py','verifier/kit_fonts.py','verifier/kit_templates.py','verifier/composition_fonts.py','assets/workbench/composition-font-metrics.json','web/composition-reader.html','web/composition-workbench.html','web/composition-workbench.js','web/composition-site-tools.js','examples/workbench/composition/reference-names.sysml','tests/test_composition_edit.py','tests/browser/composition_reference_fixture.py'];
const inputs=Object.fromEntries(sourceNames.map(p=>[p,hash(path.join(root,p))])),observations=[];
const original=fs.readFileSync(path.join(root,'examples/workbench/composition/reference-names.sysml'),'utf8');
function expectedSource(view){
 if(replacementNames){
  if(view==='PC_SENSOR'){
   const token="'Δetector\\'s unit'",old="ReferenceComposition::'Sénsor::unit'",changed="ReferenceComposition::'Δetector\\'s unit'";
   return original.replace("part def <S> 'Sénsor::unit';",'part def <S> '+token+';').replaceAll("for 'Sénsor::unit';",'for '+token+';').replace("part direct : 'Sénsor::unit';",'part direct : '+token+';').replaceAll(old+';',changed+';').replace(JSON.stringify(old),JSON.stringify(changed).replace('Δ','\\u0394'));
  }
  return original.replace('part def <O> Outer {',"part def <O> 'Assembly::frame' {").replace('alias OuterAlias for Outer;',"alias OuterAlias for 'Assembly::frame';").replace('part remote : Outer::Remote;',"part remote : 'Assembly::frame'::Remote;").replaceAll('ReferenceComposition::Outer',"ReferenceComposition::'Assembly::frame'").replace("part def <I> 'Inner::device';","part def <I> 'part';").replace("OuterAlias::'Inner::device';","OuterAlias::'part';").replaceAll("ReferenceComposition::'Assembly::frame'::'Inner::device'","ReferenceComposition::'Assembly::frame'::part");
 }
 if(view==='PC_SENSOR')return original.replace("part def <S> 'Sénsor::unit';",'part def <S> SensingUnit;').replaceAll("for 'Sénsor::unit';",'for SensingUnit;').replace("part direct : 'Sénsor::unit';",'part direct : SensingUnit;').replaceAll("ReferenceComposition::'Sénsor::unit'",'ReferenceComposition::SensingUnit');
 return original.replace('part def <O> Outer {','part def <O> Platform {').replace('alias OuterAlias for Outer;','alias OuterAlias for Platform;').replace('part remote : Outer::Remote;','part remote : Platform::Remote;').replaceAll('ReferenceComposition::Outer','ReferenceComposition::Platform').replace("part def <I> 'Inner::device';",'part def <I> Module;').replace("OuterAlias::'Inner::device';",'OuterAlias::Module;').replaceAll("ReferenceComposition::Platform::'Inner::device'",'ReferenceComposition::Platform::Module');
}
const snapshotCode="import json,sys;from verifier.composition_project import CompositionProject;s=CompositionProject(sys.argv[1]).snapshot();print(json.dumps({'revision':s['revision'],'commit':s['commit'],'files':s['document'].files,'registry':s['document'].registry,'records':s['document'].linked_records}))";
const readProject=project=>JSON.parse(execFileSync('python3',['-B','-c',snapshotCode,project],{cwd:root,env:process.env,encoding:'utf8'}));
const browser=await chromium.launch({executablePath:process.env.CSE_BROWSER_EXECUTABLE,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
try{for(const width of [1440,390])for(const view of ['PC_REFERENCE','PC_SENSOR']){
 const name=view+'-'+width,folder=path.join(output,name),log=fs.openSync(path.join(output,name+'.log'),'wx',0o600);
 let server=spawn('python3',['-B','tests/browser/composition_reference_fixture.py',folder,view],{cwd:root,env:process.env,stdio:['ignore',log,log]}),terminal=false;server.on('exit',()=>terminal=true);
 const page=await browser.newPage({viewport:{width,height:1100}}),errors=[],screenshots=[];page.setDefaultTimeout(90000);page.on('pageerror',e=>errors.push(String(e)));
 await page.addInitScript(()=>{globalThis.__tools=new Map();Object.defineProperty(document,'modelContext',{value:{registerTool:async t=>__tools.set(t.name,t)}})});
 try{
  for(let n=0;!fs.existsSync(path.join(folder,'connection.json'));n++){if(terminal||n>900)throw Error('Fixture startup');await sleep(100)}
  let connection=JSON.parse(fs.readFileSync(path.join(folder,'connection.json')));const project=connection.project;
  const ready=()=>page.waitForFunction(()=>typeof frameReady!=='undefined'&&frameReady&&!busy&&globalThis.cseSelectionContext?.selected_element_ids?.length===1&&globalThis.cseSiteTools?.registered.length===15);
  const tool=(name,args={})=>page.evaluate(async({name,args})=>await __tools.get(name).execute(args),{name,args});
  const context=async()=>(await tool('cse_get_context')).context,state=()=>page.evaluate(async()=>(await(await fetch('/api/state')).json()).state);
  const select=async occurrence=>{const c=await context(),id=(await state()).projection.nodes[occurrence].element_id,r=await tool('cse_select_element',{guard:c.guard,element_id:id,occurrence_id:occurrence});assert(r.outcome==='selected','Native selection refused');return r.context};
  const save=async()=>{const c=await context(),r=await tool('cse_save_change',{guard:c.guard,request_id:c.pending_change.request.request_id});assert(r.outcome==='committed','Exact native save unacknowledged');await ready();return r};
  const screenshot=async label=>{const p=path.join(output,name+'-'+label+'.png');await page.screenshot({path:p,fullPage:true});screenshots.push({path:p,sha256:hash(p)})};
  await page.goto(connection.url);await ready();const first=await state(),initial=readProject(project),svgFirst=await page.evaluate(async()=>await(await fetch('/view.svg')).text());
  const firstNode=view==='PC_SENSOR'?'Sensor':'Outer',secondNode=view==='PC_SENSOR'?'Sensor':'Inner',firstName=replacementNames?(view==='PC_SENSOR'?'Sénsor::array':'Assembly::frame'):(view==='PC_SENSOR'?'Detector':'Platform'),secondName=replacementNames?(view==='PC_SENSOR'?"Δetector's unit":'part'):(view==='PC_SENSOR'?'SensingUnit':'Module');
  const initialContext=await select(firstNode);const firstId=initialContext.guard.selected_element_id,secondId=first.projection.nodes[secondNode].element_id,scope=first.configuration_reviews[0].scope_sha256;
  assert(first.configuration_reviews[0].report.status==='pass','Initial retained scope did not reconcile');
  const inner=()=>page.frame({name:'cse-saved-view'});
  const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');
  function frameDocument(n){if(n.nodeName==='IFRAME'&&n.attributes?.includes('cse-saved-view')&&n.contentDocument)return n.contentDocument;for(const c of n.children||[]){const found=frameDocument(c);if(found)return found}return null}
  const inspectFonts=async()=>{
  await inner().evaluate(()=>document.fonts.ready);const {root:dom}=await cdp.send('DOM.getDocument',{depth:-1,pierce:true});
  const {nodeIds}=await cdp.send('DOM.querySelectorAll',{nodeId:frameDocument(dom).nodeId,selector:'g[data-node-id] > text'}),fonts=[];
  for(const nodeId of nodeIds){const r=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});fonts.push(...r.fonts.filter(f=>f.glyphCount))}
  assert(fonts.length&&fonts.every(f=>f.isCustomFont&&f.familyName.startsWith('DejaVu Sans')),'Original glyph supplier substituted');
  const measured=await inner().evaluate(()=>[...document.querySelectorAll('g[data-node-id] > text')].map(t=>({text:t.textContent,size:Number(t.getAttribute('font-size')),family:t.getAttribute('font-family'),weight:Number(t.getAttribute('font-weight')),actual:t.getComputedTextLength()})));
  const advanceCode="import json,sys;from verifier.composition_fonts import text_width;print(json.dumps([text_width(t['text'],t['size'],t['family'],t['weight']) for t in json.loads(sys.argv[1])]))";
  const advances=JSON.parse(execFileSync('python3',['-B','-c',advanceCode,JSON.stringify(measured)],{cwd:root,env:process.env,encoding:'utf8'}));
  measured.forEach((t,i)=>assert(Math.abs(t.actual-advances[i])<0.15,'Browser/source advance mismatch: '+JSON.stringify({...t,expected:advances[i]})));
  return{fonts,measured,advances};};
  const {fonts,measured,advances}=await inspectFonts();
  const refusedNames=[];
  if(replacementNames)for(const new_name of ['bad\nname','bad\rname','bad\r\nname']){
   const before=await context(),r=await tool('cse_preview_rename',{guard:before.guard,element_id:firstId,new_name}),after=await context();
   assert(r.outcome==='refused'&&r.error.code==='name','Site silently normalized a non-single-line name');
   assert(JSON.stringify(after.editing_target)===JSON.stringify(before.editing_target)&&!after.has_form_draft&&!after.pending_change&&(await state()).commit===first.commit,'Refused site name changed draft or project');
   refusedNames.push({requested:new_name,outcome:r.outcome,code:r.error.code});
  }
  await screenshot('initial');
  // Human declared-name form and save invoke the same native transaction.
  await page.locator('#rename-name').fill(firstName);await page.locator('#preview-rename').click();await page.waitForFunction(()=>pending&&!busy);
  assert((await state()).commit===first.commit,'Human preview published source');await page.locator('#save').click();await page.waitForFunction(()=>state.revision===2&&frameReady&&!busy);
  let current=await state();assert(current.projection.nodes[firstNode].element_id===firstId&&current.projection.nodes[firstNode].native.name===firstName,'Human rename lost name/UUID');
  let c=await select(secondNode),r=await tool('cse_preview_rename',{guard:c.guard,element_id:secondId,new_name:secondName});assert(r.outcome==='previewed','Native site rename refused: '+JSON.stringify(r.error));const request=r.request;
  assert((await state()).revision===2,'Site preview published source');await screenshot('preview');
  await page.route('**/api/apply',async route=>{await route.fetch();await route.abort('failed')},{times:1});c=await context();r=await tool('cse_save_change',{guard:c.guard,request_id:request.request_id});assert(r.outcome==='unconfirmed'&&r.context.unconfirmed_save,'Lost save discarded request');
  await page.reload();await ready();c=await context();assert(c.unconfirmed_save&&JSON.stringify(c.pending_change.request)===JSON.stringify(request)&&c.editing_target.declared_name===secondName&&c.editing_target.base_revision===2,'Reload changed exact rename/base/form');await screenshot('lost-response');
  r=await tool('cse_lookup_receipt',{request});assert(r.outcome==='committed'&&r.receipt.revision===3,'Durable rename receipt unavailable');await save();
  current=await state();const saved=readProject(project);assert(current.revision===3&&current.projection.nodes[secondNode].element_id===secondId&&current.projection.nodes[secondNode].native.name===secondName,'Saved native rename/UUID diverged');
  assert(saved.files['reference.sysml']===expectedSource(view),'Exact native reference spellings diverged');assert(JSON.stringify(Object.keys(saved.registry).sort())===JSON.stringify(Object.keys(initial.registry).sort()),'Engineering UUID inventory changed');
  assert(saved.records['scope.json'].text===initial.records['scope.json'].text&&current.configuration_reviews[0].scope_sha256===scope,'Retained configuration bytes changed');
  assert(current.configuration_reviews[0].report.status===(view==='PC_SENSOR'?'fail':'pass'),'Stale retained type binding kept an earlier finding');
  assert((await tool('cse_preview_rename',{guard:initialContext.guard,element_id:firstId,new_name:'Stale'})).error.code==='stale_context','Stale site context accepted');
  const group=page.frameLocator('#view').locator('g[data-node-id="'+secondNode+'"]');await group.scrollIntoViewIfNeeded();const renamedFontEvidence=await inspectFonts();await screenshot('saved');
  const renamedSvg=await page.evaluate(async()=>await(await fetch('/view.svg')).text()),renamedExport=path.join(folder,'renamed-offline');
  execFileSync('python3',['-B','scripts/composition_project.py','render','--project',project,'--view-id',view,'--output',renamedExport],{cwd:root,env:process.env});
  execFileSync('python3',['-B','scripts/composition_project.py','check-render','--project',project,'--view-id',view,'--output',renamedExport],{cwd:root,env:process.env});
  const renamedManifest=JSON.parse(fs.readFileSync(path.join(renamedExport,'manifest.json')));
  assert(renamedManifest.revision===3&&renamedManifest.commit===saved.commit&&fs.readFileSync(path.join(renamedExport,'view.svg'),'utf8')===renamedSvg,'Changed-state CLI export differs from visible native rename');
  assert(hash(path.join(renamedExport,'fonts/composition-font-metrics.json'))===inputs['assets/workbench/composition-font-metrics.json'],'Export omitted/changed qualified font profile');
  // Restore is monotonic; then restart compute and independently rebuild export.
  c=await context();r=await tool('cse_preview_restore',{guard:c.guard,target_revision:1});assert(r.outcome==='previewed','Native restoration refused');await save();assert((await state()).revision===4,'Restore did not create a new revision');
  server.kill('SIGINT');await new Promise(resolve=>server.once('exit',resolve));terminal=false;const next=path.join(folder,'reopen-connection.json');
  server=spawn('python3',['-B','scripts/composition_workbench.py','--project',project,'--view-id',view,'--connection-file',next],{cwd:root,env:process.env,stdio:['ignore',log,log]});server.on('exit',()=>terminal=true);
  for(let n=0;!fs.existsSync(next);n++){if(terminal||n>900)throw Error('Reopen startup');await sleep(100)}
  connection=JSON.parse(fs.readFileSync(next));await page.goto(connection.url);await ready();await select(secondNode);const reopened=await state(),restored=readProject(project),svg=await page.evaluate(async()=>await(await fetch('/view.svg')).text());
  assert(reopened.revision===4&&svg===svgFirst&&JSON.stringify(restored.registry)===JSON.stringify(initial.registry)&&JSON.stringify(restored.files)===JSON.stringify(initial.files),'Restart/restore changed source, native identities or original SVG');await screenshot('reopened');
  const offline=path.join(folder,'offline');execFileSync('python3',['-B','scripts/composition_project.py','render','--project',project,'--view-id',view,'--output',offline],{cwd:root,env:process.env});execFileSync('python3',['-B','scripts/composition_project.py','check-render','--project',project,'--view-id',view,'--output',offline],{cwd:root,env:process.env});
  assert(fs.readFileSync(path.join(offline,'view.svg'),'utf8')===svgFirst,'CLI export differs from saved original SVG');const kit=JSON.parse(fs.readFileSync(path.join(offline,'kit-usage.json')));for(const [id,digest]of Object.entries(kit.components))assert(hash(path.join(root,'assets/engineering-library/components',id+'.svg'))===digest,'Kit master provenance changed');
  assert(errors.length===0,'Browser script errors');observations.push({width,view,status:'pass',initial_commit:first.commit,renamed_commit:saved.commit,restored_commit:reopened.commit,renamed_export_manifest_sha256:hash(path.join(renamedExport,'manifest.json')),final_revision:reopened.revision,first_id:firstId,second_id:secondId,scope_sha256:scope,fonts,measured,advances,renamed_font_evidence:renamedFontEvidence,refused_names:refusedNames,request_id:request.request_id,screenshots,errors});console.log(JSON.stringify({case:name,status:'pass'}));
 }catch(error){await page.screenshot({path:path.join(output,name+'-failed.png'),fullPage:true}).catch(()=>{});throw error}
 finally{await page.close();if(!terminal){server.kill('SIGINT');await new Promise(resolve=>server.once('exit',resolve))}fs.closeSync(log)}
}
assert(sourceNames.every(p=>hash(path.join(root,p))===inputs[p]),'Source changed during browser checks');fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({claim:'Actual local Chromium/native/Git rename/source/font/recovery checks; synthetic site callbacks, not actual Codex/ChatGPT acceptance',replacement_names:replacementNames,browser:browser.version(),inputs,driver_sha256:hash(fileURLToPath(import.meta.url)),fixture_sha256:hash(path.join(root,'tests/browser/composition_reference_fixture.py')),observations},null,2)+'\n');
}finally{await browser.close()}
