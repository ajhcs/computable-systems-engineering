// Native diagram/source removal, exact Git recovery and original-kit drawings.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { setTimeout as sleep } from 'node:timers/promises';

const { chromium } = createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE);
const root = fileURLToPath(new URL('../../', import.meta.url));
const output = path.resolve(process.argv[2]);
fs.mkdirSync(output, {mode: 0o700});
const browser = await chromium.launch({executablePath: process.env.CSE_BROWSER_EXECUTABLE});
const observations = [];
const hash = value => createHash('sha256').update(value).digest('hex');
const viewEffects = views => views.map(({view_id, action, node_ids, edge_ids}) => ({view_id, action, node_ids, edge_ids}));

try {
  for (const width of [1440, 390]) {
    const folder = path.join(output, String(width));
    const log = fs.openSync(path.join(output, width+'.log'), 'wx', 0o600);
    const service = spawn('python3', ['-B', 'tests/browser/composition_fixture.py', folder, 'PC_USAGE'], {
      cwd: root, stdio: ['ignore', log, log],
    });
    const page = await browser.newPage({viewport: {width, height: 1000}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    try {
      const connection = path.join(folder, 'connection.json');
      for (let attempt = 0; !fs.existsSync(connection); attempt++) {
        assert(service.exitCode === null && attempt < 900, 'Native fixture failed to start');
        await sleep(100);
      }
      const address = JSON.parse(fs.readFileSync(connection));
      await page.addInitScript(() => {
        globalThis.testSiteTools = {};
        Object.defineProperty(document, 'modelContext', {value: {
          registerTool(tool) { globalThis.testSiteTools[tool.name] = tool.execute; },
        }});
      });
      await page.goto(address.url);
      const context = () => page.evaluate(() => cseWorkbench.context());
      const getState = async view => (await (await page.request.get(address.origin+'/api/state', {
        headers: view ? {'X-CSE-View': view} : {},
      })).json()).state;
      async function ready(revision, view) {
        await page.waitForFunction(({revision, view}) => {
          const context = cseWorkbench.context();
          return context.ready && context.guard.model_revision === revision && context.guard.view_id === view;
        }, {revision, view}, {timeout: 60000});
      }
      async function call(name, fields) {
        const guard = (await context()).guard;
        const result = await page.evaluate(async ({name, fields, guard}) => {
          return await testSiteTools[name]({guard, ...fields});
        }, {name, fields, guard});
        return result;
      }
      const svg = async view => (await page.request.get(address.origin+'/view.svg?view='+view)).text();
      const currentFrame = page.frameLocator('#view');
      const select = node => currentFrame.locator('[data-node-id="'+node+'"]').press('Enter');
      const waitChecked = () => page.waitForFunction(() => Boolean(cseWorkbench.context().pending_change?.request.checked_bundle_sha256),
        null, {timeout:60000});
      const openRemoval = () => page.locator('#removal-details > summary').click();
      const confirm = () => page.locator('#ownership-candidate-ack').check();
      const expectedCandidate = (state, id) => state.pending_change.preview.affected_views[id].candidate_svg_sha256;

      await ready(1,'PC_USAGE');
      const first = await getState();
      const original = await svg('PC_USAGE');
      const definition = await svg('PC_DEFINITION');
      assert.equal(first.configuration_reviews[0].report.status, 'pass');
      await select('Left');
      await openRemoval();
      await page.locator('#remove-diagram').press('Enter');
      await page.locator('[data-removal-view="PC_USAGE"]').check({timeout: 15000});
      await page.route('**/api/preview', async route => {
        const response = await route.fetch();
        const body = await response.json();
        assert.equal(response.status(),200);
        body.preview.candidate_svg = original;
        await route.fulfill({response,json:body});
      }, {times:1});
      await page.locator('#preview-removal').press('Enter');
      await page.locator('#notice').getByText(/drawing does not match the checked candidate/).waitFor();
      assert.equal((await context()).pending_change,null);
      assert.equal((await getState()).revision,1);
      for(const negative of [
        {pattern:/affected view does not match/, change(preview) {
          preview.candidate_svg=null;
          preview.candidate_svg_sha256=null;
          preview.affected_views.PC_USAGE.candidate_svg_sha256=null;
        }},
        {pattern:/affected view does not match/, change(preview) {
          preview.affected_views.PC_USAGE.view_effect.edge_ids=[];
        }},
        {pattern:/removal summary does not match/, change(preview) {
          preview.removal.views[0].node_ids=['Optional'];
        }},
      ]){
        await page.route('**/api/preview',async route=>{
          const response=await route.fetch();
          assert.equal(response.status(),200);
          const body=await response.json();
          negative.change(body.preview);
          await route.fulfill({response,json:body});
        },{times:1});
        // Wait for this request rather than retaining the previous refusal.
        const response = page.waitForResponse('**/api/preview');
        await page.locator('#preview-removal').press('Enter');
        await response;
        await page.locator('#notice').getByText(negative.pattern).waitFor();
        assert.equal((await context()).pending_change,null);
        assert.equal((await getState()).revision,1);
      }
      await page.locator('#preview-removal').press('Enter');
      await waitChecked();
      const diagram = await context();
      assert.equal(diagram.pending_change.request.node_id,'Left');
      assert.equal(diagram.pending_change.request.operation,'remove_occurrence');
      assert.equal(diagram.pending_change.preview.configuration_reviews[0].scope_sha256,first.configuration_reviews[0].scope_sha256);
      assert(await page.locator('#save').isDisabled());
      await page.locator('#ownership-show-candidate').click();
      await page.locator('#ownership-candidate-status').getByText(/checked unsaved bundle/).waitFor();
      const candidate = await page.locator('#candidate-diagram').getAttribute('srcdoc');
      assert(candidate.includes('DejaVu Sans Mono') && !candidate.includes('data-node-id="Left"'));
      await page.route('**/api/preview-view',async route=>{
        const response=await route.fetch();
        assert.equal(response.status(),200);
        const body=await response.json();
        body.closed=true;
        body.candidate_svg=null;
        await route.fulfill({response,json:body});
      },{times:1});
      await page.locator('#ownership-show-candidate').click();
      await page.locator('#ownership-candidate-status').getByText(/requires a drawing for this view/).waitFor();
      assert(await page.locator('#candidate-diagram').isHidden());
      await page.locator('#ownership-show-candidate').click();
      await page.locator('#ownership-candidate-status').getByText(/checked unsaved bundle/).waitFor();
      await confirm();
      await page.route('**/api/apply',async route=>{
        const response=await route.fetch();
        const body=await response.json();
        assert.equal(response.status(),200);
        body.receipt.bundle_sha256='0'.repeat(64);
        await route.fulfill({response,json:body});
      },{times:1});
      await page.locator('#save').press('Enter');
      await page.waitForFunction(()=>cseWorkbench.context().unconfirmed_save);
      const malformedReceipt=await context();
      assert.equal(malformedReceipt.last_acknowledged_receipt,null);
      assert.equal(malformedReceipt.pending_change.request.request_id,diagram.pending_change.request.request_id);
      await page.locator('#save').press('Enter');
      await ready(2,'PC_USAGE');
      const diagramSvg = await svg('PC_USAGE');
      assert.equal(hash(diagramSvg),expectedCandidate(diagram,'PC_USAGE'));
      assert.equal(await svg('PC_DEFINITION'),definition);
      const saved = await getState();
      assert.equal(saved.configuration_reviews[0].report.status,'pass');

      const row = Object.values(saved.projection.inspection.occurrences).find(entry=>entry.origin==='declaration'&&entry.element.endsWith('::left'));
      await currentFrame.locator('[data-inspection-id="'+row.id+'"]').press('Enter');
      const impact = await call('cse_read_removal_impact',{scope:'model'});
      assert.equal(impact.outcome,'observed',JSON.stringify(impact.error));
      assert.equal(impact.element_id,row.element_id);
      assert.deepEqual(impact.views,[]);
      const deletion = await call('cse_preview_native_deletion',{element_id:row.element_id,reference_effects:[],view_effects:[]});
      assert.equal(deletion.outcome,'previewed',JSON.stringify(deletion.error));
      const beforeNativeSave = await context();
      assert.equal(beforeNativeSave.pending_change.preview.configuration_reviews[0].report.status,'fail');
      assert.equal(beforeNativeSave.pending_change.preview.configuration_reviews[0].scope_sha256,first.configuration_reviews[0].scope_sha256);
      assert((await page.locator('#summary').textContent()).includes('native_identity'));
      const nativeRequest = beforeNativeSave.pending_change.request;
      const reviewed = await call('cse_acknowledge_removal_candidate',{request_id:nativeRequest.request_id,
        checked_bundle_sha256:nativeRequest.checked_bundle_sha256});
      assert.equal(reviewed.outcome,'reviewed',JSON.stringify(reviewed.error));
      const nativeSave = await call('cse_save_change',{request_id:nativeRequest.request_id});
      assert.equal(nativeSave.outcome,'committed');
      await ready(3,'PC_USAGE');
      assert.equal(await svg('PC_USAGE'),diagramSvg);
      assert.equal((await getState()).configuration_reviews[0].report.status,'fail');

      await select('Root');
      const closure = await call('cse_read_removal_impact',{scope:'diagram'});
      const beforeClose = await svg('PC_USAGE');
      await page.route('**/api/preview',async route=>{
        const response=await route.fetch();
        assert.equal(response.status(),200);
        const body=await response.json();
        const preview=body.preview;
        preview.affected_views.PC_USAGE.view_effect.action='remove_occurrences';
        preview.affected_views.PC_USAGE.candidate_svg_sha256=hash(beforeClose);
        preview.candidate_svg=beforeClose;
        preview.candidate_svg_sha256=hash(beforeClose);
        preview.current_view_closed=false;
        await route.fulfill({response,json:body});
      },{times:1});
      const malformedClosure=await call('cse_preview_diagram_removal',{element_id:closure.element_id,node_id:'Root',
        view_effects:viewEffects(closure.views)});
      assert.equal(malformedClosure.outcome,'refused');
      assert.match(malformedClosure.error.detail,/affected view does not match/);
      assert.equal((await context()).pending_change,null);
      assert.equal((await getState()).revision,3);
      const discard=await call('cse_discard_change',{});
      assert.equal(discard.outcome,'discarded');
      const closing = await call('cse_preview_diagram_removal',{element_id:closure.element_id,node_id:'Root',
        view_effects:viewEffects(closure.views)});
      assert.equal(closing.outcome,'previewed',JSON.stringify(closing.error));
      await page.locator('#ownership-show-candidate').click();
      await page.locator('#ownership-candidate-status').getByText(/closes in this exact candidate/).waitFor();
      await confirm();
      let dropped = false;
      await page.route('**/api/apply', async route => {
        const response = await route.fetch();
        assert.equal(response.status(),200);
        dropped = true;
        await route.abort('failed');
      }, {times:1});
      await page.locator('#save').press('Enter');
      await page.waitForFunction(() => cseWorkbench.context().unconfirmed_save);
      assert(dropped);
      await page.reload();
      await page.waitForFunction(() => {
        const context = cseWorkbench.context();
        return context.view_available===false && context.unconfirmed_save && context.guard.model_revision===4;
      },null,{timeout:60000});
      const retry = await context();
      assert.equal(retry.pending_change.request.request_id,closing.request.request_id);
      await page.locator('#save').press('Enter');
      await page.waitForFunction(() => cseWorkbench.context().last_acknowledged_receipt?.revision===4);
      await page.locator('#saved-view-picker').selectOption('PC_DEFINITION');
      await page.locator('#open-saved-view').press('Enter');
      await ready(4,'PC_DEFINITION');
      assert.equal(await svg('PC_DEFINITION'),definition);
      await select('Catalog');
      const lastImpact = await call('cse_read_removal_impact',{scope:'diagram'});
      const last = await call('cse_preview_diagram_removal',{element_id:lastImpact.element_id,node_id:'Catalog',
        view_effects:viewEffects(lastImpact.views)});
      assert.equal(last.outcome,'previewed',JSON.stringify(last.error));
      await confirm();
      await page.locator('#save').press('Enter');
      await page.waitForFunction(() => {
        const context = cseWorkbench.context();
        return context.view_available===false && !context.available_views.length && context.guard.model_revision===5;
      },null,{timeout:60000});
      await page.locator('#closed-retained-reviews > summary').click();
      assert((await page.locator('#closed-retained-findings').textContent()).includes('native_identity'));
      await page.locator('#source-panel > summary').click();
      await page.locator('#source-read').press('Enter');
      await page.locator('#source-text').waitFor();
      assert((await page.locator('#source-text').textContent()).includes('part def Catalog'));
      const restoration = await call('cse_preview_restore',{target_revision:1});
      assert.equal(restoration.outcome,'previewed',JSON.stringify(restoration.error));
      await page.locator('#save').press('Enter');
      await ready(6,'PC_DEFINITION');
      assert.equal(await svg('PC_USAGE'),original);
      assert.equal(await svg('PC_DEFINITION'),definition);
      assert.equal((await getState()).configuration_reviews[0].scope_sha256,first.configuration_reviews[0].scope_sha256);
      assert.deepEqual(errors,[]);
      const fontFamilies = await page.frame({name:'cse-saved-view'}).evaluate(()=>[...document.fonts].map(face=>face.family+':'+face.weight).sort());
      assert.equal(fontFamilies.length,4);
      await page.frame({name:'cse-saved-view'}).evaluate(()=>cseDiagramNavigation.mode('overview'));
      await page.locator('#view').screenshot({path:path.join(folder,'restored.png')});
      observations.push({width, original_sha256:hash(original), candidate_sha256:hash(diagramSvg), restored_revision:6,
        exact_retry_revision:4,provider_effect_controls:5,fontFamilies,observed_views:['PC_USAGE','PC_DEFINITION']});
      console.log('PASS removal and restoration at '+width+' px');
    } finally {
      await page.close();
      service.kill('SIGINT');
      fs.closeSync(log);
    }
  }
} finally {
  await browser.close();
}
fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({status:'pass',scope:'Local Chromium with test site-tool registration and native Git.',observations},null,2)+'\n');
