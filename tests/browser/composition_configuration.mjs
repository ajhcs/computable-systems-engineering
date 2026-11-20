// Check saved and candidate reports against a real native Git project.
import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';

const { chromium } = createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE || 'playwright');
if (!process.argv[2] || !process.env.TMPDIR) throw Error('Supply a fresh output directory and explicit TMPDIR.');
const root = fileURLToPath(new URL('../../', import.meta.url));
const output = path.resolve(process.argv[2]);
fs.mkdirSync(output);
const hash = file => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const sourceFiles = [
  'tools/sysml/SysmlBridge.java', 'verifier/configuration.py', 'verifier/composition_edit.py',
  'verifier/composition_data_tools.py', 'verifier/composition_project.py', 'verifier/composition_session.py', 'verifier/composition_view.py',
  'verifier/composition_inspection.py', 'web/composition-reader.html', 'web/composition-workbench.html',
  'web/composition-workbench.js', 'web/composition-site-tools.js', 'web/composition-artifact-bytes.mjs',
  'tests/browser/composition_fixture.py',
  'tests/browser/composition_configuration.mjs',
];
const pins = Object.fromEntries(sourceFiles.map(file => [file, hash(path.join(root, file))]));
const browser = await chromium.launch({
  executablePath: process.env.CSE_BROWSER_EXECUTABLE,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const observations = [];

try {
  for (const width of [1440, 390]) {
    const folder = path.join(output, String(width));
    const log = fs.openSync(folder + '.log', 'wx');
    const fixture = spawn('python3', ['-B', 'tests/browser/composition_fixture.py', folder, 'PC_USAGE', '--retained-findings'],
      { cwd: root, stdio: ['ignore', log, log] });
    const page = await browser.newPage({ viewport: { width, height: 1100 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    try {
      const connection = path.join(folder, 'connection.json');
      for (let attempt = 0; !fs.existsSync(connection); attempt++) {
        assert(fixture.exitCode === null && attempt < 900, 'Native fixture failed to start');
        await sleep(100);
      }
      const { url, origin, project } = JSON.parse(fs.readFileSync(connection));
      await page.addInitScript(() => {
        globalThis.tools = new Map();
        Object.defineProperty(document, 'modelContext', {
          value: { registerTool(tool) { tools.set(tool.name, tool.execute); } },
        });
      });
      await page.goto(url);
      const ready = revision => page.waitForFunction(expected => {
        const context = globalThis.cseWorkbench?.context();
        return context?.ready && context.guard.model_revision === expected && tools.has('cse_get_context');
      }, revision, { timeout: 90000 });
      const tool = (name, args = {}) => page.evaluate(({ name, args }) => tools.get(name)(args), { name, args });
      const context = async () => (await tool('cse_get_context')).context;
      const select = id => page.frameLocator('#view').locator('g[data-node-id="' + id + '"]').press('Enter');

      await ready(1);
      const before = await context();
      const originalScopeBytes = new Map(before.configuration_reviews.map(review =>
        [review.file, execFileSync('git', ['--git-dir', project, 'show', before.guard.commit+':linked/'+review.file])]));
      const checkExport = async current => {
        const { commit, model_revision, bundle_sha256 } = current.guard;
        const response = await page.request.get(origin+'/view.json?commit='+commit);
        assert.equal(response.status(), 200);
        const exported = await response.json();
        assert.equal(exported.commit, commit);
        assert.equal(exported.revision, model_revision);
        assert.equal(exported.projection.bundle_sha256, bundle_sha256);
        assert.deepEqual(exported.projection.configuration_reviews.map(({retained_scope,...item}) => item),
          current.configuration_reviews);
        assert.equal(exported.retained_scope_sources.length, originalScopeBytes.size);
        for(const entry of exported.retained_scope_sources){
          const bytes = Buffer.from(entry.text, 'utf8');
          assert.deepEqual(bytes, originalScopeBytes.get(entry.file));
          assert.equal(createHash('sha256').update(bytes).digest('hex'), entry.scope_sha256);
        }
        return response.body();
      };
      const baselineArtifact = await checkExport(before);
      const svg = async commit => (await page.request.get(origin+'/view.svg?commit='+commit)).body();
      const baselineSvg = await svg(before.guard.commit);
      async function captureDownload(action, name) {
        const started = page.waitForEvent('download', {timeout:20000});
        const result = await action();
        const download = await started;
        assert.equal(download.suggestedFilename(), 'CSE-PC_USAGE-r1.json');
        const target = path.join(folder, name);
        await download.saveAs(target);
        assert.deepEqual(fs.readFileSync(target), baselineArtifact);
        return result;
      }
      await captureDownload(() => page.frameLocator('#view').getByRole('link', {name:'source bindings'}).press('Enter'),
        'manual-r1.json');
      const { file, scope_sha256: scope } = before.configuration_reviews[0];
      const failing = before.configuration_reviews.find(review => review.file === 'missing.scope.json');
      const read = (guard, offset = 0, extra = {}) => tool('cse_read_retained_review', {
        guard, file, scope_sha256: scope, offset, limit: 1, ...extra,
      });
      const findings = [];
      let offset = 0;
      do {
        const result = await read(before.guard, offset, { file: failing.file, scope_sha256: failing.scope_sha256 });
        assert.equal(result.outcome, 'observed', JSON.stringify(result.error));
        assert.equal(result.commit, before.guard.commit);
        assert.equal(result.status, 'fail');
        assert.equal(result.total_findings, 2);
        assert.deepEqual(result.context, { guard: before.guard });
        findings.push(...result.findings);
        assert(result.next_offset === null || result.next_offset === offset + 1);
        offset = result.next_offset;
      } while (offset !== null);
      assert.deepEqual(findings.map(finding => finding.id), ['missingOne', 'missingTwo']);
      assert.deepEqual(findings, failing.report.findings);
      assert.equal((await read(before.guard)).total_findings, 0);
      assert.equal((await read(before.guard, 0, { scope_sha256: '0'.repeat(64) })).error.code, 'scope_unavailable');
      assert.equal((await read(before.guard, 0, { limit: 101 })).error.code, 'input');
      assert.equal((await read(before.guard, findings.length + 1)).error.code, 'input');
      const savedSummary = page.locator('#closed-retained-reviews > summary');
      const saved = page.locator('#closed-retained-findings');
      const candidate = page.locator('#candidate-retained-findings');
      await savedSummary.click();
      assert.match(await saved.innerText(), /left\.scope\.json · pass/);

      await select('Left');
      const { element_id } = (await context()).editing_target;
      await page.locator('#multiplicity-lower').fill('0');
      await page.locator('#multiplicity-upper').fill('1');
      await select('Optional');
      const draft = await context();
      assert.equal(draft.editing_target.element_id, element_id);
      const preview = await tool('cse_preview_current_edit', { guard: draft.guard, kind: 'multiplicity' });
      assert.equal(preview.outcome, 'previewed', JSON.stringify(preview.error));
      assert.equal(preview.preview.configuration_reviews[0].report.status, 'unknown');
      const checked = await context();
      await checkExport(checked);
      const download = () => tool('cse_export_saved_view',{guard:checked.guard,kind:'view.json'});
      const transferred = await captureDownload(download, 'site-r1.json');
      assert.equal(transferred.outcome,'transfer_requested',JSON.stringify(transferred.error));
      assert.equal(transferred.context.pending_change.request.request_id,checked.pending_change.request.request_id);
      if(width===1440){
        await page.route('**/api/artifact', async route => {
          const response = await route.fetch();
          const body = await response.json();
          body.text += '\n';
          await route.fulfill({response,json:body});
        }, {times:1});
        const rejected = await download();
        assert.equal(rejected.outcome,'refused');
        assert.match(rejected.error.detail,/bytes failed verification/);
      }
      assert.equal(checked.guard.commit, before.guard.commit);
      assert.equal((await read(before.guard)).error.code, 'stale_context');
      const savedWhileChecked = await read(checked.guard);
      assert.equal(savedWhileChecked.status, 'pass');
      assert.deepEqual((await context()).pending_change.request, checked.pending_change.request);
      await page.locator('#candidate-retained-reviews > summary').click();
      const candidateReport = await candidate.innerText();
      assert(candidateReport.includes(scope));
      assert.match(candidateReport, /selected_multiplicity · unknown/);
      assert.match(await saved.innerText(), /left\.scope\.json · pass/);
      const screenshot = path.join(output, width + '-candidate.png');
      await page.screenshot({ path: screenshot, fullPage: true });

      await page.locator('#save').click();
      await ready(2);
      assert.match(await saved.innerText(), /left\.scope\.json · unknown/);
      await page.reload();
      await ready(2);
      await savedSummary.click();
      assert((await saved.innerText()).includes(scope));
      const reopened = await context();
      await checkExport(reopened);
      const editedSvg = await svg(reopened.guard.commit);
      assert.equal(reopened.configuration_reviews[0].report.status, 'unknown');
      assert.equal((await read(reopened.guard)).status, 'unknown');

      if(width===1440){
        await page.route('**/api/preview', async route => {
          const response = await route.fetch();
          const body = await response.json();
          body.preview.restored_from_revision = 2;
          await route.fulfill({response,json:body});
        }, {times:1});
        const refused = await tool('cse_preview_restore', {guard:reopened.guard,target_revision:1});
        assert.equal(refused.outcome,'refused');
        assert.match(refused.error.detail,/requested saved revision/);
        await tool('cse_discard_change',{guard:(await context()).guard});
      }
      const restored = await tool('cse_preview_restore', { guard: (await context()).guard, target_revision: 1 });
      assert.equal(restored.outcome, 'previewed', JSON.stringify(restored.error));
      assert.equal(restored.preview.candidate_svg_sha256,createHash('sha256').update(baselineSvg).digest('hex'));
      assert.equal(restored.preview.restored_from_revision,1);
      const candidateSvg = page.frameLocator('#candidate-diagram').locator('[data-node-id="Left"]');
      await candidateSvg.waitFor({state:'visible'});
      assert.match(await candidateSvg.textContent(),/\[2\]/);
      assert.deepEqual(await svg(reopened.guard.commit),editedSvg);
      await page.locator('#save').click();
      await ready(3);
      const after = await context();
      await checkExport(after);
      assert.equal(after.configuration_reviews[0].scope_sha256, scope);
      assert.equal(after.configuration_reviews[0].report.status, 'pass');
      assert.equal((await read(after.guard)).status, 'pass');
      assert.match(await saved.innerText(), /left\.scope\.json · pass/);
      assert.deepEqual(await svg(after.guard.commit),baselineSvg);
      await page.locator('#restore-target').selectOption('2');
      await page.locator('#restore-form button').press('Enter');
      await candidateSvg.waitFor({state:'visible'});
      const redo = await context();
      assert.equal(redo.pending_change.preview.restored_from_revision,2);
      assert.equal(redo.pending_change.preview.candidate_svg_sha256,createHash('sha256').update(editedSvg).digest('hex'));
      assert.match(await candidateSvg.textContent(),/\[0\.\.1\]/);
      await page.locator('#save').press('Enter');
      await ready(4);
      const redone = await context();
      assert.deepEqual(await svg(redone.guard.commit),editedSvg);
      assert.equal(redone.last_acknowledged_receipt.restored_from_revision,2);
      assert.equal((await read(redone.guard)).status,'unknown');
      await checkExport(redone);
      assert.deepEqual(errors, []);
      observations.push({ width, commit: redone.guard.commit, scope, findings_paged: findings.length, statuses: ['pass', 'unknown', 'pass', 'unknown'],
        screenshot: { path: screenshot, sha256: hash(screenshot) } });
      console.log(JSON.stringify({ width, status: 'pass' }));
    } finally {
      await page.close();
      if (fixture.exitCode === null) {
        fixture.kill('SIGINT');
        await new Promise(resolve => fixture.once('exit', resolve));
      }
      fs.closeSync(log);
    }
  }
  assert(sourceFiles.every(file => hash(path.join(root, file)) === pins[file]), 'Source changed during browser checks');
  fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify({
    status: 'pass', browser: browser.version(), inputs: pins, observations,
    scope: 'Actual desktop and narrow Chromium with native Git and synthetic site registration. Keyboard and site-tool downloads match the captured saved JSON during preview. Returned-byte tampering refuses. Exact retained findings, scope, save, reload and restore.',
  }, null, 2) + '\n');
} finally {
  await browser.close();
}
