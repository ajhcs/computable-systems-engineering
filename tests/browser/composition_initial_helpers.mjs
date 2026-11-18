import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawn,execFileSync} from 'node:child_process';import {createHash} from 'node:crypto';
export const root=fileURLToPath(new URL('../../',import.meta.url));
export const hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
export const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
export const assert=(value,message)=>{if(!value)throw Error(message)};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
export const sourceNames=['tools/sysml/SysmlBridge.java','verifier/composition_edit.py','verifier/composition_initial.py','verifier/composition_startup.py','verifier/composition_records.py','verifier/composition_project.py','verifier/composition_session.py','verifier/composition_view.py','verifier/composition_inspection.py','verifier/composition_fonts.py','verifier/kit_fonts.py','verifier/kit_templates.py','web/composition-initial.html','web/composition-initial.js','web/composition-reader.html','web/composition-workbench.html','web/composition-workbench.js','web/composition-site-tools.js','web/composition-mcp-host.js','tests/browser/composition_initial_fixture.py','tests/browser/composition_initial_helpers.mjs'];
export const pins=extra=>Object.fromEntries([...sourceNames,...extra].map(name=>[name,hash(path.join(root,name))]));
export function unchanged(inputs){for(const[name,sha]of Object.entries(inputs))assert(hash(path.join(root,name))===sha,'Source changed during browser run: '+name)}
export async function fixture(output,name,{port=0,connection='connection.json',reuse=false}={}){
 const folder=path.join(output,name),logPath=path.join(output,name+'-'+connection+'.log'),log=fs.openSync(logPath,'wx',0o600);
 if(!reuse)assert(!fs.existsSync(folder),'Fixture target already exists');
 let ended=false,closed=false;const process=spawn('python3',['-B','tests/browser/composition_initial_fixture.py',folder,'--port',String(port),'--connection',connection],{cwd:root,env:globalThis.process.env,stdio:['ignore',log,log]});process.on('exit',()=>ended=true);
 async function stop(){
  if(closed)return;closed=true;
  try{if(!ended){let timer;const done=new Promise(r=>process.once('exit',r));process.kill('SIGINT');try{await Promise.race([done,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Owned fixture stop timed out')),10000)})])}finally{clearTimeout(timer)}}}
  finally{fs.closeSync(log)}
 }
 try{
  for(let i=0;!fs.existsSync(path.join(folder,connection));i++){if(ended||i>900)throw Error('Initial fixture startup failed; inspect '+logPath);await sleep(100)}
  const data=JSON.parse(fs.readFileSync(path.join(folder,connection)));return{...data,connectionFile:path.join(folder,connection),stop};
 }catch(error){await stop();throw error}

}
export async function toolRegistration(page){await page.addInitScript(()=>{globalThis.__tools=new Map();Object.defineProperty(document,'modelContext',{value:{registerTool:async tool=>__tools.set(tool.name,tool),unregisterTool:async name=>__tools.delete(name)}})})}
export const context=page=>page.evaluate(()=>cseInitialWorkbench.context());
export const tool=(page,name,args={})=>page.evaluate(async({name,args})=>__tools.get(name).execute(args),{name,args});
export const initialReady=page=>page.waitForFunction(()=>globalThis.cseInitialWorkbench?.context().ready&&cseInitialSiteTools.registered.length===7);
export const candidateReady=page=>page.waitForFunction(()=>cseInitialWorkbench.context().ready&&cseInitialWorkbench.context().candidate_ready);
export async function shot(page,output,name,images){const file=path.join(output,name+'.png');assert(!fs.existsSync(file),'Screenshot filename reused');await page.screenshot({path:file,fullPage:true});images.push({path:file,sha256:hash(file)})}
export function verifyShots(images){assert(new Set(images.map(i=>i.path)).size===images.length,'Duplicate screenshot paths');for(const image of images)assert(hash(image.path)===image.sha256,'Screenshot overwritten')}
export function snapshot(project){return JSON.parse(execFileSync('python3',['-B','-c',"import json,sys;from verifier.composition_project import CompositionProject;p=CompositionProject(sys.argv[1]);s=p.snapshot();print(json.dumps({'revision':s['revision'],'commit':s['commit'],'registry':s['document'].registry,'files':s['document'].files,'inspection':s['document'].inspect(),'history':p.history()}))",project],{cwd:root,env:process.env,encoding:'utf8'}))}
export async function displayedFonts(page,id='initial-diagram'){
 const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');const tree=(await cdp.send('DOM.getDocument',{depth:-1,pierce:true})).root;let target;
 function find(node){const a=node.attributes||[];if(node.nodeName==='IFRAME'&&a.some((v,i)=>i%2===0&&v==='id'&&a[i+1]===id))target=node.contentDocument;for(const child of [...node.children||[],...(node.contentDocument?[node.contentDocument]:[])])find(child)}find(tree);assert(target,'Exact displayed SVG frame not found');
 const nodes=[];function walk(node){if(node.nodeName==='text')nodes.push(node.nodeId);for(const child of node.children||[])walk(child)}walk(target);assert(nodes.length>=2,'Missing exact root/heading text');const observations=[];
 for(const nodeId of nodes){const used=(await cdp.send('CSS.getPlatformFontsForNode',{nodeId})).fonts.filter(f=>f.glyphCount>0);assert(used.length,'Displayed text has no measured glyph supplier');observations.push({nodeId,fonts:used})}
 await cdp.detach();assert(observations.every(o=>o.fonts.every(f=>f.isCustomFont&&f.familyName.startsWith('DejaVu'))),'Displayed SVG uses fallback glyphs');return{frame_id:id,text_nodes:nodes.length,observations};
}
