// Physical-composition acceptance checks; requires an explicitly configured browser runtime.
import fs from 'node:fs';import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn,execFileSync} from 'node:child_process';import {createHash} from 'node:crypto';import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE||'playwright');
if(!process.argv[2]||!process.env.TMPDIR)throw new Error('Supply a fresh output directory and explicit writable TMPDIR.');
const root=fileURLToPath(new URL('../../',import.meta.url)),output=path.resolve(process.argv[2]);fs.mkdirSync(output);
const hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');const assert=(c,m)=>{if(!c)throw new Error(m);};const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const sourceNames=['web/composition-reader.html','web/composition-workbench.js','web/composition-workbench.html','web/composition-site-tools.js','verifier/composition_view.py','verifier/composition_inspection.py','verifier/composition_project.py','verifier/composition_session.py'];
const sourcePins=Object.fromEntries(sourceNames.map(p=>[p,hash(path.join(root,p))]));
function readableGeometry(){
 const vp=document.getElementById('diagram-viewport'),a=vp.getBoundingClientRect(),id=cseSelectionContext.selected_occurrence_ids[0],r=[...vp.querySelectorAll('g[data-node-id]')].find(e=>e.dataset.nodeId===id).getBoundingClientRect();
 const left=a.left+vp.clientLeft+12,right=a.left+vp.clientLeft+vp.clientWidth-12,top=a.top+vp.clientTop+12,bottom=a.top+vp.clientTop+vp.clientHeight-12;
 const fitsX=r.width<=right-left+1,fitsY=r.height<=bottom-top+1;
 const inspectableX=r.left-a.left+vp.scrollLeft>=-1&&r.right-a.left+vp.scrollLeft<=vp.scrollWidth+1;
 const inspectableY=r.top-a.top+vp.scrollTop>=-1&&r.bottom-a.top+vp.scrollTop<=vp.scrollHeight+1;
 const xOK=fitsX?r.left>=left-1&&r.right<=right+1:Math.abs((r.left+r.right-left-right)/2)<=1&&inspectableX;
 const yOK=fitsY?r.top>=top-1&&r.bottom<=bottom+1:Math.abs((r.top+r.bottom-top-bottom)/2)<=1&&inspectableY;
 return{id,scale:cseDiagramNavigation.state().scale,fitsX,fitsY,xOK,yOK,focus:document.activeElement.id,width:r.width,height:r.height,viewport_width:right-left,viewport_height:bottom-top};
}
const browser=await chromium.launch({executablePath:process.env.CSE_BROWSER_EXECUTABLE,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});const observations=[];
try{for(const width of [1440,390])for(const view of ['PC_USAGE','PC_DEFINITION']){
 const name=view+'-'+width,folder=path.join(output,name),log=fs.openSync(path.join(output,name+'.log'),'wx');
 const server=spawn('python3',['-B','tests/browser/composition_fixture.py',folder,view],{cwd:root,env:process.env,stdio:['ignore',log,log]});let terminal=false;server.on('exit',()=>terminal=true);
 const page=await browser.newPage({viewport:{width,height:1100}}),errors=[],mutations=[];page.setDefaultTimeout(90000);page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/api/'))mutations.push(r.url().split('/api/')[1]);});
 await page.addInitScript(()=>{globalThis.__tools=new Map();Object.defineProperty(document,'modelContext',{value:{registerTool:async t=>__tools.set(t.name,t)}});});
 try{
  for(let n=0;!fs.existsSync(path.join(folder,'connection.json'));n++){if(terminal||n>900)throw new Error('Fixture startup');await sleep(100);}
  const connection=JSON.parse(fs.readFileSync(path.join(folder,'connection.json')));await page.goto(connection.url);await page.waitForFunction(()=>globalThis.cseSelectionContext?.selected_element_ids?.length===1&&globalThis.cseSiteTools?.status==='registered');
  const inner=()=>page.frame({name:'cse-saved-view'}),navigation=()=>inner().evaluate(()=>cseDiagramNavigation.state());
  const tool=(name,args={})=>page.evaluate(async({name,args})=>await __tools.get(name).execute(args),{name,args});const context=async()=> (await tool('cse_get_context')).context;const state=()=>page.evaluate(async()=> (await(await fetch('/api/state')).json()).state);
  const snapshot=await state(),svgBefore=await page.evaluate(async()=>await(await fetch('/view.svg')).text());const expectedNode=view==='PC_USAGE'?'Left':'Module',identity=snapshot.projection.nodes[expectedNode].element_id;
  assert((await navigation()).scale===1,'Initial reader shrank labels');
  const checkFit=async()=>{
   await inner().waitForFunction(()=>{const n=cseDiagramNavigation.state();return n.mode==='overview'&&Math.abs(n.scale-Math.min(1,(n.viewport_width-24)/n.drawing_width,(n.viewport_height-24)/n.drawing_height))<1e-8;});
   const r=await inner().evaluate(()=>{const v=document.getElementById('diagram-viewport'),a=v.getBoundingClientRect(),b=v.querySelector('svg').getBoundingClientRect();return{state:cseDiagramNavigation.state(),fits:b.left>=a.left&&b.top>=a.top&&b.right<=a.right+1&&b.bottom<=a.bottom+1,nodes:[...v.querySelectorAll('g[data-node-id]')].map(e=>e.dataset.nodeId)};});assert(r.fits&&r.nodes.length===Object.keys(snapshot.projection.nodes).length,'Overview clipped/omitted saved SVG');return r.state;
  };
  await page.frameLocator('#view').locator('#overview').click();const fit=await checkFit();const overviewImage=path.join(output,name+'-overview.png');await page.screenshot({path:overviewImage,fullPage:true});
  await page.setViewportSize({width:width+120,height:1200});await checkFit();await page.setViewportSize({width,height:1100});await checkFit();
  await inner().evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));await sleep(100);
  let c=await context(),r=await tool('cse_select_element',{guard:c.guard,element_id:identity,occurrence_id:expectedNode});assert(r.outcome==='selected'&&r.context.navigation.mode==='readable'&&r.context.navigation.scale===1,'Agent did not reveal readable selection: '+JSON.stringify(r));
  r=await tool('cse_set_view_mode',{guard:r.context.guard,mode:'overview'});assert(r.outcome==='navigated','Own reveal returned unstable navigation guard: '+JSON.stringify(r));await checkFit();
  await page.frameLocator('#view').locator('g[data-node-id="'+expectedNode+'"]').click();assert((await navigation()).mode==='readable'&&(await context()).guard.selected_element_id===identity,'Human overview selection lost native identity');assert(mutations.length===0,'Navigation created engineering request');
  // A manually panned viewport survives unchanged-model refresh, without following the selection.
  await inner().evaluate(()=>{const v=document.getElementById('diagram-viewport');v.scrollLeft=v.scrollWidth;v.scrollTop=v.scrollHeight;});await sleep(50);const panned=await navigation();
  await tool('cse_refresh_project',{guard:(await context()).guard});await page.waitForFunction(()=>!document.getElementById('edits').disabled);await sleep(50);
  const refreshed=await navigation();assert(refreshed.scroll_left===panned.scroll_left&&refreshed.scroll_top===panned.scroll_top,'Refresh overrode manually panned viewport');
  r=await tool('cse_set_view_mode',{guard:(await context()).guard,mode:'readable'});assert(r.outcome==='navigated','Readable reveal failed');
  const beforeDraft=await context();await page.locator('#rename-name').fill('retainedNavigationDraft');await page.frameLocator('#view').locator('#overview').click();c=await context();assert(c.has_form_draft&&c.editing_target.element_id===identity&&c.editing_target.declared_name==='retainedNavigationDraft','Viewport retargeted draft');
  assert((await tool('cse_set_view_mode',{guard:beforeDraft.guard,mode:'readable'})).error.code==='stale_context','Stale viewport/draft guard accepted');
  r=await tool('cse_set_view_mode',{guard:c.guard,mode:'readable'});assert(r.outcome==='navigated'&&r.context.has_form_draft,'Agent discarded draft');
  await page.locator('#preview-rename').click();await page.waitForFunction(()=>!document.getElementById('save').disabled);c=await context();const request=c.pending_change.request;
  r=await tool('cse_set_view_mode',{guard:c.guard,mode:'overview'});assert(r.outcome==='navigated'&&r.context.pending_change.request.request_id===request.request_id,'Navigation replaced checked request');
  await tool('cse_refresh_project',{guard:(await context()).guard});await page.waitForFunction(()=>document.getElementById('view').contentWindow.cseDiagramNavigation?.state().mode==='overview');await checkFit();c=await context();assert(c.has_form_draft&&c.editing_target.declared_name==='retainedNavigationDraft','Overview refresh lost retained values');
  await tool('cse_discard_change',{guard:c.guard});await tool('cse_set_view_mode',{guard:(await context()).guard,mode:'readable'});
  const group=page.frameLocator('#view').locator('g[data-node-id="'+expectedNode+'"]');await group.scrollIntoViewIfNeeded();const box=await group.boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();c=await context();
  assert(c.gesture_active&&(await navigation()).locked,'Gesture did not lock navigation');assert(await page.frameLocator('#view').locator('#overview').isDisabled()&&await page.frameLocator('#view').locator('#next').isDisabled(),'Gesture allowed camera/selection controls');assert((await tool('cse_set_view_mode',{guard:c.guard,mode:'overview'})).error.code==='interaction_busy','Tool changed camera during drag');
  const other=Object.keys(snapshot.projection.nodes).find(id=>id!==expectedNode);await page.frameLocator('#view').locator('g[data-node-id="'+other+'"]').press('Enter');assert((await context()).guard.selected_element_id===identity,'Keyboard selection retargeted active drag');await page.frameLocator('#view').locator('g[data-node-id="'+other+'"]').press('Escape');await page.mouse.up();assert(!(await navigation()).locked,'Cancelled drag left camera locked');
  for(let i=0;i<Object.keys(snapshot.projection.nodes).length;i++){
   await page.frameLocator('#view').locator('#next').click();const visible=await inner().evaluate(readableGeometry);assert(visible.scale===1&&visible.xOK&&visible.yOK&&visible.focus==='next','Keyboard reveal containment/focus failed: '+JSON.stringify(visible));
  }
  const after=await state(),svgAfter=await page.evaluate(async()=>await(await fetch('/view.svg')).text());assert(after.commit===snapshot.commit&&JSON.stringify(after.layout)===JSON.stringify(snapshot.layout)&&svgAfter===svgBefore,'Viewport changed saved source/layout/SVG');assert(mutations.every(p=>p==='preview'),'Viewport sent a save');
  await inner().evaluate(()=>document.fonts.ready);const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');const {root:dom}=await cdp.send('DOM.getDocument',{depth:-1,pierce:true});function findFrame(n){if(n.nodeName==='IFRAME'&&n.attributes?.includes('cse-saved-view')&&n.contentDocument)return n.contentDocument;for(const c of n.children||[]){const f=findFrame(c);if(f)return f;}return null;}
  const {nodeIds}=await cdp.send('DOM.querySelectorAll',{nodeId:findFrame(dom).nodeId,selector:'svg text'}),fonts=[];for(const nodeId of nodeIds){const data=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});fonts.push(...data.fonts.filter(f=>f.glyphCount));}assert(fonts.length&&fonts.every(f=>f.isCustomFont&&f.familyName.startsWith('DejaVu Sans')),'Font substitution');
  const readableImage=path.join(output,name+'-readable.png');await page.screenshot({path:readableImage,fullPage:true});
  const offline=path.join(folder,'offline');execFileSync('python3',['-B','scripts/composition_project.py','render','--project',connection.project,'--view-id',view,'--output',offline],{cwd:root,env:process.env});
  const saved=await browser.newPage({viewport:{width,height:1100}});await saved.goto('file://'+path.join(offline,'index.html'));await saved.locator('#overview').click();assert(await saved.evaluate(()=>cseDiagramNavigation.state().mode)==='overview','Standalone overview absent');await saved.locator('#readable').click();assert(await saved.evaluate(()=>cseDiagramNavigation.state().scale)===1,'Standalone labels shrank');await saved.setViewportSize({width:250,height:250});const oversized=[];
  for(let i=0;i<Object.keys(snapshot.projection.nodes).length;i++){await saved.locator('#next').click();const geometry=await saved.evaluate(readableGeometry);assert(geometry.scale===1&&geometry.xOK&&geometry.yOK,'Oversized frame cannot be centered/inspected: '+JSON.stringify(geometry));oversized.push(geometry);}
  assert(oversized.some(r=>!r.fitsX),'Oversized horizontal test was not exercised');if(view==='PC_USAGE')assert(oversized.some(r=>!r.fitsY),'Oversized vertical test was not exercised');
  await saved.close();assert(!errors.length,'Script errors: '+errors.join(';'));
  observations.push({width,view,fit,revision:after.revision,commit:after.commit,identity,panned,refreshed,oversized,svg_sha256:createHash('sha256').update(svgAfter).digest('hex'),fonts,screenshots:[overviewImage,readableImage].map(p=>({path:p,sha256:hash(p)})),standalone_reader:true,script_errors:errors});console.log(JSON.stringify({case:name,status:'pass'}));
 }catch(e){await page.screenshot({path:path.join(output,name+'-failed.png'),fullPage:true}).catch(()=>{});throw e;}
 finally{await page.close();if(!terminal){server.kill('SIGINT');await new Promise(r=>server.once('exit',r));}fs.closeSync(log);}
}
assert(sourceNames.every(p=>hash(path.join(root,p))===sourcePins[p]),'Source changed during navigation checks');
fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({claim:'Actual local Chromium navigation/gesture/source-preservation checks; synthetic host callbacks only, not actual Codex/ChatGPT or engineering acceptance',browser:browser.version(),source_sha256:sourcePins,driver_sha256:hash(fileURLToPath(import.meta.url)),fixture_sha256:hash(path.join(root,'tests/browser/composition_fixture.py')),observations},null,2)+'\n');
}finally{await browser.close();}
