import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';
import { displayedFonts } from './composition_initial_helpers.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)),out=path.resolve(process.argv[2]);
fs.mkdirSync(out,{mode:0o700});
const data=path.join(out,'data'), log=fs.openSync(path.join(out,'native.log'),'wx');
const child=spawn('python3',['-B',path.join(here,'composition_fixture.py'),data,'CROSS'],{stdio:['ignore',log,log]});
const {chromium}=createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE);
let browser;
const signature=bytes=>createHash('sha256').update(bytes).digest('hex');
try {
  const connection=path.join(data,'connection.json');
  for(let n=0;!fs.existsSync(connection);n++){
    assert(child.exitCode===null&&n<1200,'Native fixture failed to start');
    await sleep(100);
  }
  const {url,origin}=JSON.parse(fs.readFileSync(connection,'utf8'));
  browser=await chromium.launch({executablePath:process.env.CSE_BROWSER_EXECUTABLE,
    headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  const observed=[];
  const inputs=Object.fromEntries(['web/composition-reader.html','web/composition-workbench.html',
    'web/composition-workbench.js','web/composition-site-tools.js','verifier/composition_view.py',
    'tests/browser/composition_initial_helpers.mjs','tests/test_composition_view.py',
    'tests/browser/composition_fixture.py','tests/browser/composition_branches.mjs'
  ].map(file=>[file,signature(fs.readFileSync(path.resolve(here,'../..',file)))]));
  for(const width of [1440,390]){
    const page=await browser.newPage({viewport:{width,height:950}});
    const failures=[];
    page.on('pageerror',error=>failures.push(error.message));
    await page.addInitScript(()=>{
      if(window.top!==window)return;
      globalThis.site={};
      Object.defineProperty(document,'modelContext',{value:{registerTool(tool){site[tool.name]=tool.execute;}}});
    });
    await page.goto(url);
    await page.waitForFunction(()=>globalThis.cseWorkbench?.context().ready,null,{timeout:90000});
    const frame=page.frameLocator('#view');
    const ctx=()=>page.evaluate(()=>cseWorkbench.context());
    const before=await ctx();
    const diagram=await page.locator('#view').boundingBox();
    const controls=await page.locator('#model-controls').boundingBox();
    assert(diagram.y<240);
    if(width===1440)assert(controls.x>=diagram.x+diagram.width&&Math.abs(controls.y-diagram.y)<5);
    else assert(controls.y>=diagram.y+diagram.height);
    const bytes=await (await page.request.get(origin+'/view.svg')).body();
    const group=(id)=>frame.locator('g[data-node-id="'+id+'"]');
    await group('A').press('Enter');
    const selected=await ctx();
    assert.equal(selected.selection.occurrence_id,'A');
    await page.locator('#rename-name').fill('Retained draft');
    const afterForm=await ctx();
    const button=frame.locator('#branch-visibility');
    await button.press('Enter');
    await group('C').waitFor({state:'hidden'});
    assert(await group('D').isVisible());
    assert(await frame.locator('g[data-edge-id="ED"]').isVisible());
    assert(await frame.locator('g[data-edge-id="EC"]').isHidden());
    assert(await frame.locator('#composition-crossing-0-gap').isHidden());
    const foldState=frame.locator('#folded-state');
    await group('D').press('Enter');
    assert.equal(await foldState.textContent(),'1 folded branch');
    await foldState.click();
    assert.equal(await frame.locator('#folded-list li').textContent(),selected.selection.element);
    await foldState.click();
    assert(await button.isHidden());
    const declarationColumn=await frame.locator('.declaration-table th').first().boundingBox();
    assert(declarationColumn.width>=320,'Native declaration column lost its readable width');
    const foldedImage=path.join(out,'folded-'+width+'.png');
    await page.screenshot({path:foldedImage,fullPage:true});
    await group('A').press('Enter');
    const folded=await ctx();
    assert.equal(folded.guard.commit,before.guard.commit);
    assert.equal(folded.editing_target.occurrence_id,'A');
    assert(folded.has_form_draft);
    assert.deepEqual(folded.navigation.collapsed_node_ids,['A']);
    assert.deepEqual(folded.navigation.hidden_node_ids,['C']);
    assert(folded.visible_elements.every(row=>row.occurrence_id!=='C'));
    assert(folded.guard.navigation_revision>afterForm.guard.navigation_revision);
    const stale=await page.evaluate(guard=>site.cse_set_branch_visibility({guard,occurrence_id:'A',expanded:true}),afterForm.guard);
    assert.equal(stale.error.code,'stale_context');
    await frame.locator('#overview').click();
    assert(await group('C').isVisible());
    assert.deepEqual((await ctx()).navigation.hidden_node_ids,[]);
    assert((await ctx()).visible_elements.some(row=>row.occurrence_id==='C'));
    assert(await frame.locator('#composition-crossing-0-gap').isVisible());
    assert(await button.isHidden());
    assert.equal(await foldState.textContent(),'All branches shown · 1 folded branch at readable size');
    const overviewImage=path.join(out,'overview-'+width+'.png');
    await page.screenshot({path:overviewImage,fullPage:true});
    await frame.locator('#readable').click();
    await group('C').waitFor({state:'hidden'});
    await page.locator('#refresh').click();
    await page.waitForFunction(()=>cseWorkbench.context().ready&&!busy);
    await group('C').waitFor({state:'hidden'});
    assert.deepEqual((await ctx()).navigation.collapsed_node_ids,['A']);
    const expanded=await page.evaluate(async ()=>{
      const guard=cseWorkbench.context().guard;
      return site.cse_set_branch_visibility({guard,occurrence_id:'A',expanded:true});
    });
    assert.equal(expanded.outcome,'navigated',JSON.stringify(expanded.error));
    assert(await group('C').isVisible());
    assert(await frame.locator('#composition-crossing-0-gap').isVisible());
    await button.press('Enter');
    const revealed=await page.evaluate(async ()=>{
      let guard=cseWorkbench.context().guard;
      const found=await site.cse_list_inspection_occurrences({guard,origin:'frame',offset:0,limit:10});
      const candidate=found.inspection_page.items.find(row=>row.id==='C');
      return site.cse_select_element({guard,element_id:candidate.element_id,occurrence_id:'C'});
    });
    assert.equal(revealed.outcome,'selected',JSON.stringify(revealed.error));
    assert.equal(revealed.context.editing_target.occurrence_id,'A');
    assert.equal(revealed.context.selection.occurrence_id,'C');
    assert.deepEqual(revealed.context.navigation.hidden_node_ids,[]);
    assert(await group('C').isVisible());
    assert.equal((await page.locator('#rename-name').inputValue()),'Retained draft');
    const after=await (await page.request.get(origin+'/view.svg')).body();
    assert.deepEqual(after,bytes);
    assert.deepEqual(failures,[]);
    observed.push({width,commit:before.guard.commit,svg_sha256:signature(bytes),glyphs:await displayedFonts(page,'view'),
      screenshots:[foldedImage,overviewImage].map(file=>({file,sha256:signature(fs.readFileSync(file))}))});
    await page.close();
  }
  assert(Object.entries(inputs).every(([file,digest])=>signature(fs.readFileSync(path.resolve(here,'../..',file)))===digest),
    'Source changed during the branch checks');
  fs.writeFileSync(path.join(out,'receipt.json'),JSON.stringify({status:'pass',
    scope:'Branch and responsive layout on original physical SVG and native Git in Chromium. Synthetic site callbacks.',
    source_sha256:inputs,observed},null,2)+'\n');
  console.log('PASS branch navigation preserves saved source, drawing and draft');
} finally {
  if(browser)await browser.close();
  if(child.exitCode===null){
    child.kill('SIGINT');
    await new Promise(resolve=>child.once('exit',resolve));
  }
  fs.closeSync(log);
}
