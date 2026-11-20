import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const output = path.resolve(process.argv[2]);
const { chromium } = createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE || 'playwright');
const cli = (...args) => JSON.parse(execFileSync('python3', args, { cwd: root }));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
fs.mkdirSync(output);
const fixturePath = path.join(output, 'fixture');
const log = fs.openSync(path.join(output, 'fixture.log'), 'wx');
const fixture = spawn('python3', ['-B', 'tests/browser/composition_fixture.py', fixturePath, 'PC_USAGE'],
  { cwd: root, stdio: ['ignore', log, log] });
const done = new Promise(resolve => fixture.once('exit', resolve));
let browser;
try {
  const connection = path.join(fixturePath, 'connection.json');
  for (let attempt = 0; !fs.existsSync(connection); attempt++) {
    assert(fixture.exitCode === null && attempt < 1200, 'Native artwork fixture failed to start');
    await sleep(100);
  }
  const { url, project } = JSON.parse(fs.readFileSync(connection));
  const projectCli = (command, ...flags) => cli('scripts/composition_project.py', command, '--project', project, ...flags);
  const beforeDir = path.join(output, 'before');
  assert.equal(projectCli('render', '--view', 'PC_USAGE', '--output', beforeDir).status, 'pass');
  const layout = fs.readFileSync(path.join(beforeDir, 'layout.json'));
  const source = fs.readFileSync(path.join(beforeDir, 'sources/model.sysml'));
  const scope = fs.readFileSync(path.join(beforeDir, 'companions/left.scope.json'));
  const beforeLayout = JSON.parse(layout);
  const dotted = cli('scripts/icons.py', 'show', 'palette-rectangle-grey-dots');
  const expectedMaster = fs.readFileSync(path.join(root, 'assets/engineering-library', dotted.component.file));
  assert.equal(hash(expectedMaster), dotted.component.sha256);

  browser = await chromium.launch({ executablePath: process.env.CSE_BROWSER_EXECUTABLE,
    args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    globalThis.tools = new Map();
    Object.defineProperty(document, 'modelContext', {
      value: { registerTool(tool) { tools.set(tool.name, tool.execute); } },
    });
  });
  await page.goto(url);
  const ready = revision => page.waitForFunction(value =>
    globalThis.cseWorkbench?.context().ready && cseWorkbench.context().guard.model_revision === value,
  revision, { timeout: 120000 });
  await ready(1);
  const context = () => page.evaluate(() => cseWorkbench.context());
  const tool = (name, args) => page.evaluate(({ name, args }) => tools.get(name)(args), { name, args });
  const atCurrent = (name, args) => page.evaluate(({ name, args }) =>
    tools.get(name)({ ...args, guard: cseWorkbench.context().guard }), { name, args });
  const saved = (node = 'Left') => page.frameLocator('#view').locator('g[data-node-id="' + node + '"]');
  const changed = (node = 'Left') => page.frameLocator('#candidate-diagram').locator('g[data-node-id="' + node + '"]');
  await saved().press('Enter');
  let initial = await context();
  const base = { guard: initial.guard, view_id: 'PC_USAGE', node_id: 'Left', element_id: initial.guard.editing_element_id,
    component_id: dotted.component.id, catalog_sha256: dotted.catalog_sha256, svg_sha256: dotted.component.sha256,
    legend: ['Grey dots identify the authored frame treatment.'] };
  assert.equal((await tool('cse_preview_frame_master', { ...base, node_id: 'Optional' })).error.code, 'target');
  const badMaster = await tool('cse_preview_frame_master', { ...base, component_id: 'mech-pulley' });
  assert.equal(badMaster.error.code, 'artwork_role');
  await page.locator('#discard-draft').click();
  const style = { fill: 'N10', stroke: 'N100', text: 'N100', align: 'left' };
  const malformed = await tool('cse_preview_frame_style', { ...base, guard: (await context()).guard, style: null });
  assert.equal(malformed.error.code, 'input');
  assert.equal((await context()).artwork_placement_draft, null);
  const illegible = await tool('cse_preview_frame_style', { ...base, guard: (await context()).guard,
    style: { ...style, fill: 'N0', text: 'N0' } });
  assert.equal(illegible.error.code, 'presentation_conflict');
  assert.equal((await context()).guard.commit, initial.guard.commit);
  await page.locator('#discard-draft').click();

  if (!(await page.locator('#catalog-panel').evaluate(panel => panel.open)))
    await page.locator('#catalog-panel > summary').press('Enter');
  await page.locator('#catalog-query').fill(dotted.component.id);
  await page.locator('#catalog-query').press('Enter');
  await page.getByRole('button', { name: /Rectangle Dots Grey.*palette-rectangle-grey-dots/ }).press('Enter');
  await page.getByRole('button', { name: 'Use as frame master' }).press('Enter');
  await page.getByLabel('Local key, one line per entry').fill(base.legend[0]);
  await page.getByLabel('Fill swatch', { exact: true }).selectOption(style.fill);
  await page.getByLabel('Text alignment', { exact: true }).selectOption(style.align);
  await page.evaluate(() => {
    const original = loadOriginalDiagramFonts;
    const gate = new Promise(resolve => { globalThis.resumeCandidateFonts = resolve; });
    loadOriginalDiagramFonts = async doc => {
      if (doc.body?.dataset.candidateGeneration) await gate;
      return original(doc);
    };
  });
  await page.getByRole('button', { name: 'Preview frame artwork' }).press('Enter');
  await page.waitForFunction(() => !cseWorkbench.context().busy &&
    cseWorkbench.context().pending_change?.request.operation === 'set_frame_master',
    null, { timeout: 120000 });
  assert(await page.locator('#save').isDisabled());
  const waiting = await context();
  const premature = await tool('cse_save_change', {
    guard: waiting.guard, request_id: waiting.pending_change.request.request_id,
  });
  assert.equal(premature.error.code, 'save_unavailable');
  await page.evaluate(() => resumeCandidateFonts());
  await page.waitForFunction(() => !document.getElementById('candidate-diagram').hidden &&
    document.getElementById('candidate-diagram').style.visibility === 'visible');
  let candidate = await context();
  assert.equal(candidate.guard.model_revision, 1);
  assert.equal(candidate.pending_change.request.component_id, dotted.component.id);
  assert.deepEqual(candidate.pending_change.request.style, style);
  assert.deepEqual(candidate.pending_change.preview.frame_style, style);
  assert.deepEqual(candidate.pending_change.preview.changed_model_files, []);
  assert.equal(await saved().locator('pattern').count(), 0);
  assert.equal(await changed().locator('pattern').count(), 1);
  assert.equal(await changed().locator(':scope > text').first().getAttribute('text-anchor'), 'start');
  assert(await changed().locator('[fill="#E6E6E6"]').count());
  const previewImage = await page.locator('#candidate-diagram').screenshot({ path: path.join(output, 'desktop-candidate.png') });

  const requestFile = path.join(output, 'request.json');
  fs.writeFileSync(requestFile, JSON.stringify(candidate.pending_change.request));
  const cliPreview = projectCli('preview', '--request', requestFile);
  assert.equal(cliPreview.status, 'pass');
  assert.deepEqual(cliPreview.preview.changed_linked_records, candidate.pending_change.preview.changed_linked_records);
  assert.equal(cliPreview.preview.request_sha256, candidate.pending_change.preview.request_sha256);
  const applied = page.waitForResponse(response => new URL(response.url()).pathname === '/api/apply');
  await page.locator('#save').click();
  const savedResponse = await applied;
  assert.equal(savedResponse.status(), 200, await savedResponse.text());
  await ready(2);
  const receipt = projectCli('receipt', '--request', requestFile).receipt;
  assert.equal(receipt.revision, 2);
  assert.equal(projectCli('apply', '--request', requestFile).receipt.commit, receipt.commit);
  const afterDir = path.join(output, 'after');
  assert.equal(projectCli('render', '--view', 'PC_USAGE', '--output', afterDir).status, 'pass');
  assert.equal(projectCli('check-render', '--view', 'PC_USAGE', '--output', afterDir).status, 'pass');
  assert.deepEqual(fs.readFileSync(path.join(afterDir, 'sources/model.sysml')), source);
  assert.deepEqual(fs.readFileSync(path.join(afterDir, 'companions/left.scope.json')), scope);
  assert.deepEqual(fs.readFileSync(path.join(afterDir, 'artwork/' + dotted.component.id + '.svg')), expectedMaster);
  const afterLayout = JSON.parse(fs.readFileSync(path.join(afterDir, 'layout.json')));
  assert.deepEqual(afterLayout.nodes, beforeLayout.nodes);
  assert.deepEqual(afterLayout.edges, beforeLayout.edges);
  assert.equal(afterLayout.width, beforeLayout.width);
  assert(afterLayout.height >= beforeLayout.height);
  const usage = JSON.parse(fs.readFileSync(path.join(afterDir, 'kit-usage.json')));
  assert.equal(usage.adaptations.find(row => row.node === 'Left').template, dotted.component.id);
  assert.equal(usage.components[dotted.component.id], dotted.component.sha256);

  await page.setViewportSize({ width: 390, height: 1000 });
  await page.reload();
  await ready(2);
  assert.equal(await saved().locator('pattern').count(), 1);
  await saved().press('Enter');
  assert.deepEqual((await context()).saved_frame_master,
    { component_id: dotted.component.id, svg_sha256: dotted.component.sha256 });
  assert.deepEqual((await context()).saved_frame_style, { template: dotted.component.id, ...style });
  if (!(await page.locator('#catalog-panel').evaluate(panel => panel.open)))
    await page.locator('#catalog-panel > summary').press('Enter');
  await page.getByRole('button', { name: 'Edit saved frame style' }).press('Enter');
  assert.equal(await page.getByLabel('Fill swatch', { exact: true }).inputValue(), style.fill);
  assert.equal(await page.getByLabel('Text alignment', { exact: true }).inputValue(), style.align);
  await page.locator('#discard-draft').click();
  const savedImage = await page.locator('#view').screenshot({ path: path.join(output, 'phone-saved.png') });
  await saved('Optional').press('Enter');
  const reopened = await context();
  const diagonal = cli('scripts/icons.py', 'show', 'palette-rectangle-grey-diagonal');
  const next = { ...base, guard: reopened.guard, node_id: 'Optional', element_id: reopened.guard.editing_element_id,
    component_id: diagonal.component.id, catalog_sha256: diagonal.catalog_sha256, svg_sha256: diagonal.component.sha256,
    legend: null };
  const stale = await atCurrent('cse_preview_frame_master', { ...next, svg_sha256: '0'.repeat(64) });
  assert.equal(stale.error.code, 'stale_catalog');
  await page.locator('#discard-draft').click();
  const act = await atCurrent('cse_preview_frame_style', { ...next,
    style: { fill: 'N0', stroke: 'N100', text: 'N100', align: 'left' } });
  assert.equal(act.outcome, 'previewed', JSON.stringify(act.error));
  assert.deepEqual(act.preview.changed_linked_records, ['presentation/PC_USAGE.appearance.json']);
  assert.equal((await context()).guard.commit, receipt.commit);
  await page.locator('#discard').click();
  await page.locator('#restore-target').selectOption('1');
  await page.locator('#restore-form button').click();
  await page.locator('#save').click();
  await ready(3);
  assert.equal(await saved().locator('pattern').count(), 0);
  await page.locator('#restore-target').selectOption('2');
  await page.locator('#restore-form button').click();
  await page.locator('#save').click();
  await ready(4);
  assert.equal(await saved().locator('pattern').count(), 1);
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify({
    status: 'pass', persisted_revision: 2, restored_revision: 4, commit: receipt.commit, native_sha256: hash(source),
    scope_sha256: hash(scope), master_sha256: dotted.component.sha256, chromium: browser.version(),
    desktop_candidate_sha256: hash(previewImage), phone_saved_sha256: hash(savedImage),
    frame_style: style,
    scope: 'Native Git and Chromium manual and site-tool appearance editing. Exact CLI preview, contrast refusal, durable retry, source and layout preservation, original artwork, restored swatches and alignment.',
  }, null, 2) + '\n');
  await page.close();
} finally {
  if (browser) await browser.close();
  if (fixture.exitCode === null) fixture.kill('SIGINT');
  await done;
  fs.closeSync(log);
}
