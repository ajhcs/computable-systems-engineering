import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const output = path.resolve(process.argv[2]);
const { chromium } = createRequire(import.meta.url)(process.env.CSE_BROWSER_MODULE || 'playwright');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
fs.mkdirSync(output);
const fixturePath = path.join(output, 'fixture');
const log = fs.openSync(path.join(output, 'fixture.log'), 'wx');
const fixture = spawn('python3', ['-B', 'tests/browser/composition_fixture.py', fixturePath, 'CROSS'],
  { cwd: root, stdio: ['ignore', log, log] });
const done = new Promise(resolve => fixture.once('exit', resolve));
let browser;
try {
  const connection = path.join(fixturePath, 'connection.json');
  for (let attempt = 0; !fs.existsSync(connection); attempt++) {
    assert(fixture.exitCode === null && attempt < 1200, 'Native local key fixture failed to start');
    await sleep(100);
  }
  const { url, project } = JSON.parse(fs.readFileSync(connection));
  const cli = (command, ...flags) => JSON.parse(execFileSync('python3',
    ['scripts/composition_project.py', command, '--project', project, ...flags], { cwd: root }));
  const beforeDir = path.join(output, 'before');
  assert.equal(cli('render', '--view', 'CROSS', '--output', beforeDir).status, 'pass');
  const files = ['sources/model.sysml', 'registry.json', 'layout.json'];
  const before = new Map(files.map(file => [file, fs.readFileSync(path.join(beforeDir, file))]));
  const view = JSON.parse(fs.readFileSync(path.join(beforeDir, 'view.json')));

  const initialKey = ['Brown marks the authored route treatment.'];
  const nodes = view.projection.nodes;
  const palette = JSON.parse(execFileSync('python3', ['-c',
    'import json; from verifier.composition_view import appearance_palette; print(json.dumps(appearance_palette()))'],
  { cwd: root }));
  const seedPath = path.join(output, 'seed.json');
  fs.writeFileSync(seedPath, JSON.stringify({
    operation: 'set_connector_style', request_id: randomUUID(), expected_revision: 1, view_id: 'CROSS',
    edge_id: 'ED', source_id: nodes.B.element_id, target_id: nodes.D.element_id, swatch: 'C13-L36',
    palette_sha256: palette.swatches_sha256, legend: initialKey,
  }));
  assert.equal(cli('apply', '--request', seedPath).receipt.revision, 2);
  const savedAppearance = () => JSON.parse(execFileSync('git',
    ['--git-dir', project, 'show', 'HEAD:linked/presentation/CROSS.appearance.json'], { cwd: root }));
  const baselineAppearance = savedAppearance();
  const lines = ['Ownership route display.', 'Brown marks the authored route treatment.',
    'A gap marks a crossing.', 'Frames show selected definitions.', 'Read the native declarations for details.'];

  browser = await chromium.launch({ executablePath: process.env.CSE_BROWSER_EXECUTABLE,
    args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  page.setDefaultTimeout(90000);
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
    globalThis.cseWorkbench?.context().ready && cseWorkbench.context().guard.model_revision === value, revision);
  await ready(2);
  const context = () => page.evaluate(() => cseWorkbench.context());
  const call = (name, args) => page.evaluate(({ name, args }) =>
    tools.get(name)({ ...args, guard: cseWorkbench.context().guard }), { name, args });
  const keyText = (frame = '#view') => page.frameLocator(frame).locator('g[data-role="local-key"] > text');
  const initial = await context();
  const expected = { ...initial.view_key, legend: lines };
  const wrong = await call('cse_preview_view_key', { ...expected, master_sha256: '0'.repeat(64) });
  assert.equal(wrong.error.code, 'stale_catalog');
  const invalid = await call('cse_preview_view_key', { ...expected, legend: ['未'] });
  assert.equal(invalid.error.code, 'presentation_conflict');
  await page.locator('#discard-draft').click();
  const tooWide = await call('cse_preview_view_key', { ...expected, legend: ['W'.repeat(120)] });
  assert.equal(tooWide.error.code, 'presentation_conflict');
  assert.match(tooWide.error.detail, /key does not fit/i);
  await page.locator('#discard-draft').click();

  if (!(await page.locator('#view-key-panel').evaluate(panel => panel.open)))
    await page.locator('#view-key-panel > summary').press('Enter');
  await page.getByRole('button', { name: 'Edit local key', exact: true }).press('Enter');
  const textarea = page.getByLabel('Key entries, one per line');
  assert.equal(await textarea.inputValue(), initialKey[0]);
  await textarea.fill(lines.join('\n'));
  await page.getByRole('button', { name: 'Preview local key', exact: true }).press('Enter');
  await page.waitForFunction(() => cseWorkbench.context().pending_change?.request.operation === 'set_view_key' &&
    document.getElementById('candidate-diagram').style.visibility === 'visible' && !cseWorkbench.context().busy);
  const candidate = (await context()).pending_change;
  assert.deepEqual(candidate.preview.view_key, expected);
  assert.deepEqual(candidate.preview.changed_model_files, []);
  assert.deepEqual(await keyText().allTextContents(), ['Local key', ...initialKey]);
  assert.deepEqual(await keyText('#candidate-diagram').allTextContents(), ['Local key', ...lines]);
  const requestFile = path.join(output, 'request.json');
  fs.writeFileSync(requestFile, JSON.stringify(candidate.request));
  assert.equal(cli('preview', '--request', requestFile).preview.request_sha256, candidate.preview.request_sha256);
  const save = await call('cse_save_change', { request_id: candidate.request.request_id });
  assert.equal(save.outcome, 'committed', JSON.stringify(save.error));
  await ready(3);
  const afterDir = path.join(output, 'after');
  assert.equal(cli('render', '--view', 'CROSS', '--output', afterDir).status, 'pass');
  assert.equal(cli('check-render', '--view', 'CROSS', '--output', afterDir).status, 'pass');
  for (const file of ['sources/model.sysml', 'registry.json'])
    assert.deepEqual(fs.readFileSync(path.join(afterDir, file)), before.get(file));
  const baseLayout = JSON.parse(before.get('layout.json'));
  const finalLayout = JSON.parse(fs.readFileSync(path.join(afterDir, 'layout.json')));
  assert.ok(finalLayout.height > baseLayout.height);
  assert.deepEqual({ ...finalLayout, height: baseLayout.height }, baseLayout);
  const legendMaster = 'palette-refined-documents-documents-page1-navigation-legend';
  assert.equal(hash(fs.readFileSync(path.join(afterDir, 'artwork', legendMaster + '.svg'))), expected.master_sha256);
  await page.setViewportSize({ width: 390, height: 1050 });
  await page.reload();
  await ready(3);
  const reopened = await context();
  assert.deepEqual(reopened.view_key, expected);
  assert.deepEqual(savedAppearance(), { ...baselineAppearance, legend: lines });
  assert.deepEqual(reopened.connector_styles, initial.connector_styles);
  await page.frameLocator('#view').getByRole('button', { name: 'Overview', exact: true }).click();
  const screenshot = await page.locator('#view').screenshot({ path: path.join(output, 'phone-key-overview.png') });
  assert.deepEqual(await keyText().allTextContents(), ['Local key', ...lines]);
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify({
    status: 'pass', chromium: browser.version(), commit: save.receipt.commit, master_sha256: expected.master_sha256,
    previous_height: baseLayout.height, saved_height: finalLayout.height, screenshot_sha256: hash(screenshot),
    scope: 'Native Git and Chromium. Exact ruled key and fonts, invalid glyph and width refusals, unchanged native sources, frame and connector styles, and exact footer growth and reopen.',
  },null,2)+'\n');
  await page.close();
} finally {
  if (browser) await browser.close();
  if (fixture.exitCode === null) fixture.kill('SIGINT');
  await done;
  fs.closeSync(log);
}
