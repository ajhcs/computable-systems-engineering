import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';
const {chromium}=createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE);
const root=fileURLToPath(new URL('../../',import.meta.url));
const output=path.resolve(process.argv[2]);
fs.mkdirSync(output,{mode:0o700});
const log=fs.openSync(path.join(output,'native.log'),'wx',0o600);
const folder=path.join(output,'fixture');
const child=spawn('python3',['-B','tests/browser/composition_fixture.py',folder,'PC_USAGE'],{cwd:root,stdio:['ignore',log,log]});
let browser;
try{
  const descriptor=path.join(folder,'connection.json');
  for(let attempt=0;!fs.existsSync(descriptor);attempt++){
    assert(attempt<850&&child.exitCode===null,'Native fixture unavailable');
    await sleep(100);
  }
  const {url}=JSON.parse(fs.readFileSync(descriptor));
  browser=await chromium.launch({executablePath:process.env.CSE_BROWSER_EXECUTABLE});
  const page=await browser.newPage({viewport:{width:390,height:1000}});
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(url);
  await page.waitForFunction(()=>globalThis.cseWorkbench?.context().ready);
  const selection=page.frameLocator('#view').locator('[data-node-id="Left"]');
  const candidate=()=>page.frameLocator('#candidate-diagram');
  async function preview(){
    await selection.press('Enter');
    await page.getByRole('button',{name:'Remove explicit type 1'}).press('Enter');
    await page.locator('#preview-typing').press('Enter');
    await page.waitForFunction(()=>globalThis.cseWorkbench.context().pending_change?.request.operation==='set_types');
  }
  await preview();
  await page.locator('#candidate-scale').getByText('Readable size · 100%').waitFor();
  assert.equal(await page.locator('#candidate-diagram').evaluate(element=>getComputedStyle(element).visibility),'visible');
  const faces=await candidate().locator('body').evaluate(()=>[...document.fonts].map(face=>[face.family,face.weight,face.status]));
  assert.equal(faces.length,4);
  assert(faces.every(row=>row[2]==='loaded'));
  await page.locator('#candidate-overview').press('Enter');
  await page.locator('#candidate-scale').getByText(/Overview/).waitFor();
  await page.locator('#candidate-diagram').screenshot({path:path.join(output,'qualified-390.png')});
  await page.locator('#discard').press('Enter');
  await page.evaluate(()=>{
    const policy=document.createElement('meta');
    policy.httpEquiv='Content-Security-Policy';
    policy.content="font-src 'none'";
    document.head.append(policy);
  });
  await preview();
  await page.locator('#candidate-scale').getByText(/Unsupported candidate drawing/).waitFor();
  assert.equal(await page.locator('#candidate-diagram').evaluate(element=>getComputedStyle(element).visibility),'hidden');
  assert(await page.locator('#preview').isVisible());
  const checked=await page.evaluate(()=>cseWorkbench.context());
  assert.equal(checked.guard.model_revision,1);
  assert.deepEqual(checked.pending_change.request.type_ids,[]);
  assert(checked.pending_change.preview.candidate_model_sources.length>0);
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({status:'pass',scope:'Isolated local Chromium font-rendering proof.',
    original_faces:faces,blocked_candidate_hidden:true,checked_source_retained:true,revision:1},null,2)+'\n');
}finally{
  if(browser)await browser.close();
  child.kill('SIGINT');
  fs.closeSync(log);
}
