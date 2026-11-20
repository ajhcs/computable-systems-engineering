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
const loseReply = process.argv[3] === 'lost-reply';
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
    assert(fixture.exitCode === null && attempt < 1200, 'Native connector fixture failed to start');
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
  const legend = ['Brown marks the authored route treatment.'];
  const swatch = 'C13-L36', color = '#493C00', gap = '.crossing-line';

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
  await ready(1);
  const context = () => page.evaluate(() => cseWorkbench.context());
  const call = (name, args) => page.evaluate(({ name, args }) =>
    tools.get(name)({ ...args, guard: cseWorkbench.context().guard }), { name, args });
  const fillFor = (id, frame = '#view') => page.frameLocator(frame).locator('g[data-edge-id="' + id + '"] > path');
  const gapFor = (frame = '#view') => page.frameLocator(frame).locator(gap);
  const catalog = (await context()).appearance_palette;
  assert.equal(catalog.swatches[swatch], color);
  const request = { view_id: 'CROSS', edge_id: 'ED', source_id: view.projection.nodes.B.element_id,
    target_id: view.projection.nodes.D.element_id, swatch, palette_sha256: catalog.swatches_sha256, legend };
  const wrong = await call('cse_preview_connector_style', { ...request, target_id: request.source_id });
  assert.equal(wrong.error.code, 'target');
  const stale = await call('cse_preview_connector_style', { ...request, palette_sha256: '0'.repeat(64) });
  assert.equal(stale.error.code, 'stale_palette');
  const faint = await call('cse_preview_connector_style', { ...request, swatch: 'N0' });
  assert.equal(faint.error.code, 'presentation_conflict');
  assert.match(faint.error.detail, /low-contrast/);
  await page.locator('#discard-draft').click();

  if (!(await page.locator('#connector-style-panel').evaluate(panel => panel.open)))
    await page.locator('#connector-style-panel > summary').press('Enter');
  await page.getByLabel('Saved connector', { exact: true }).selectOption('ED');
  assert.equal((await context()).selected_connector.swatch, 'N100');
  await page.getByRole('button', { name: 'Edit connector style' }).press('Enter');
  await page.getByLabel('Connector swatch', { exact: true }).selectOption(swatch);
  await page.locator('#connector-style-legend').fill(legend[0]);
  await page.getByRole('button', { name: 'Preview connector style', exact: true }).press('Enter');
  await page.waitForFunction(() => !cseWorkbench.context().busy && cseWorkbench.context().pending_change &&
    document.getElementById('candidate-diagram').style.visibility === 'visible');
  const candidate = (await context()).pending_change;
  assert.deepEqual(candidate.preview.changed_model_files, []);
  assert.equal(await fillFor('ED').getAttribute('stroke'), '#000000');
  assert.equal(await fillFor('ED', '#candidate-diagram').getAttribute('stroke'), color);
  assert.equal(await fillFor('EC', '#candidate-diagram').getAttribute('stroke'), '#000000');
  assert.equal(await gapFor('#candidate-diagram').getAttribute('stroke'), color);
  assert.equal(await fillFor('ED', '#candidate-diagram').getAttribute('marker-end'), null);
  const desktop = await page.locator('#candidate-diagram').screenshot({ path: path.join(output, 'desktop-candidate.png') });

  const requestFile = path.join(output, 'request.json');
  fs.writeFileSync(requestFile, JSON.stringify(candidate.request));
  assert.equal(cli('preview', '--request', requestFile).preview.request_sha256, candidate.preview.request_sha256);
  if (loseReply) {
    const endpoint = '**/api/apply';
    let published;
    const dropReply = async route => {
      const response = await route.fetch();
      assert.equal(response.status(), 200, await response.text());
      published = (await response.json()).receipt;
      await route.abort();
    };
    await page.route(endpoint, dropReply);
    await page.locator('#save').click();
    await page.waitForFunction(() => cseWorkbench.context().unconfirmed_save && !cseWorkbench.context().busy);
    assert.equal(published.request_id, candidate.request.request_id);
    await page.unroute(endpoint, dropReply);
    await page.reload();
    await ready(2);
    const reopened = await context();
    assert.equal(reopened.unconfirmed_save, true);
    assert.deepEqual(reopened.pending_change.request, candidate.request);
    assert.equal(reopened.connector_style_draft.edge_id, 'ED');
    const retry = await call('cse_save_change', { request_id: published.request_id });
    assert.equal(retry.outcome, 'committed', JSON.stringify(retry.error));
    assert.equal(retry.receipt.commit, published.commit);
  } else {
    const response = page.waitForResponse(reply => new URL(reply.url()).pathname === '/api/apply');
    await page.locator('#save').click();
    const applied = await response;
    assert.equal(applied.status(), 200, await applied.text());
  }
  await ready(2);
  const receipt = cli('receipt', '--request', requestFile).receipt;
  assert.equal(receipt.revision, 2);
  assert.equal(cli('apply', '--request', requestFile).receipt.commit, receipt.commit);
  const afterDir = path.join(output, 'after');
  assert.equal(cli('render', '--view', 'CROSS', '--output', afterDir).status, 'pass');
  assert.equal(cli('check-render', '--view', 'CROSS', '--output', afterDir).status, 'pass');
  for (const [file, bytes] of before) assert.deepEqual(fs.readFileSync(path.join(afterDir, file)), bytes, file);

  await page.setViewportSize({ width: 390, height: 1050 });
  await page.reload();
  await ready(2);
  assert.equal((await context()).connector_styles.ED, swatch);
  assert.equal(await fillFor('ED').getAttribute('stroke'), color);
  assert.equal(await gapFor().getAttribute('stroke'), color);
  const phone = await page.locator('#view').screenshot({ path: path.join(output, 'phone-saved.png') });
  const under = await call('cse_preview_connector_style', { ...request, edge_id: 'EC',
    source_id: view.projection.nodes.A.element_id, target_id: view.projection.nodes.C.element_id, swatch: 'N50', legend: null });
  assert.equal(under.outcome, 'previewed', JSON.stringify(under.error));
  assert.equal(await gapFor('#candidate-diagram').getAttribute('stroke'), color);
  await page.locator('#discard').click();
  for (const [source, revision, expected] of [[1, 3, '#000000'], [2, 4, color]]) {
    const restore = await call('cse_preview_restore', { target_revision: source });
    assert.equal(restore.outcome, 'previewed', JSON.stringify(restore.error));
    const publish = await call('cse_save_change', { request_id: (await context()).pending_change.request.request_id });
    assert.equal(publish.outcome, 'committed', JSON.stringify(publish.error));
    await ready(revision);
    assert.equal(await gapFor().getAttribute('stroke'), expected);
  }
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify({
    status: 'pass', chromium: browser.version(), swatch, color, saved_commit: receipt.commit, restored_revision: 4,
    lost_reply_recovered: loseReply,
    desktop_candidate_sha256: hash(desktop), phone_saved_sha256: hash(phone),
    scope: 'Native Git, Chromium keyboard and site-tool connector style, contrast and identity refusals, exact CLI preview, save/retry/reopen/restore, bytes of source/registry/layout preserved, and original crossing-gap over-route rendering.',
  }, null, 2) + '\n');
  await page.close();
} finally {
  if (browser) await browser.close();
  if (fixture.exitCode === null) fixture.kill('SIGINT');
  await done;
  fs.closeSync(log);
}
