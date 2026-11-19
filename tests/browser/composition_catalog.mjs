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
const cli = (...args) => JSON.parse(execFileSync('python3', ['scripts/icons.py', ...args], { cwd: root }));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
fs.mkdirSync(output);
const fixtureRoot = path.join(output, 'fixture');
const log = fs.openSync(path.join(output, 'fixture.log'), 'wx');
const fixture = spawn('python3', ['-B', 'tests/browser/composition_fixture.py', fixtureRoot, 'PC_USAGE'],
  { cwd: root, stdio: ['ignore', log, log] });
const done = new Promise(resolve => fixture.on('exit', resolve));
let browser;
try {
  const before = cli('list', '--query', 'pulley', '--limit', '1');
  assert.equal(before.items[0].id, 'mech-pulley');
  assert.equal(before.total, 5);
  const detail = cli('show', 'mech-pulley');
  const sourceBytes = fs.readFileSync(path.join(root, 'assets/engineering-library', detail.component.file));
  assert.equal(hash(sourceBytes), detail.component.sha256);
  const connection = path.join(fixtureRoot, 'connection.json');
  for (let attempt = 0; !fs.existsSync(connection); attempt++) {
    assert(fixture.exitCode === null && attempt < 1200, 'Native catalog fixture failed to start');
    await sleep(100);
  }
  const { url } = JSON.parse(fs.readFileSync(connection));
  browser = await chromium.launch({ executablePath: process.env.CSE_BROWSER_EXECUTABLE,
    args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const observations = [];
  for (const width of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 1050 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      globalThis.tools = new Map();
      Object.defineProperty(document, 'modelContext', {
        value: { registerTool(tool) { tools.set(tool.name, tool.execute); } },
      });
    });
    await page.goto(url);
    await page.waitForFunction(() => globalThis.cseWorkbench?.context().ready &&
      tools.has('cse_inspect_component_catalog'), null, { timeout: 120000 });
    const tool = (name, args) => page.evaluate(({ name, args }) => tools.get(name)(args), { name, args });
    const context = () => page.evaluate(() => cseWorkbench.context());
    const selected = page.frameLocator('#view').locator('g[data-node-id="Left"]');
    await selected.press('Enter');
    await page.locator('#rename-name').fill('Retained catalog test draft');
    const withDraft = await context();
    assert.equal(withDraft.editing_target.declared_name, 'Retained catalog test draft');

    const inputs = { query: 'pulley', family: null, sysml: null, cursor: null, limit: 1 };
    const unwrap = ({ action, outcome, context, ...body }) => {
      assert.equal(outcome, 'observed', JSON.stringify(body));
      return body;
    };
    assert.deepEqual(unwrap(await tool('cse_search_component_catalog', inputs)), before);
    const second = { ...inputs, cursor: before.next_cursor };
    const pageTwo = unwrap(await tool('cse_search_component_catalog', second));
    assert.deepEqual(pageTwo, cli('list', '--query', 'pulley', '--limit', '1', '--cursor', before.next_cursor));
    const mismatch = await tool('cse_search_component_catalog', { ...second, query: 'port' });
    assert.equal(mismatch.error.code, 'cursor_scope_mismatch');
    const exact = { component_id: 'mech-pulley', catalog_sha256: before.catalog_sha256 };
    assert.deepEqual(unwrap(await tool('cse_inspect_component_catalog', exact)), detail);
    const stale = await tool('cse_inspect_component_catalog', { ...exact, catalog_sha256: '0'.repeat(64) });
    assert.equal(stale.error.code, 'stale_catalog');
    const unknown = await tool('cse_inspect_component_catalog', { ...exact, component_id: 'missing-pulley' });
    assert.equal(unknown.error.code, 'unknown_component_id');

    await page.locator('#catalog-panel > summary').press('Enter');
    await page.locator('#catalog-query').fill('rectangle');
    await page.locator('#catalog-query').press('Enter');
    const more = page.getByRole('button', { name: 'More components' });
    await more.waitFor();
    await more.press('Enter');
    await page.waitForFunction(() => document.getElementById('catalog-results').children.length === 9);
    assert(!(await more.isVisible()));
    await page.locator('#catalog-query').fill('pulley');
    await page.locator('#catalog-query').press('Enter');
    await page.getByRole('button', { name: 'Pulley · mech-pulley', exact: true }).press('Enter');
    const artwork = page.getByRole('img', { name: 'Pulley', exact: true });
    await artwork.waitFor();
    assert.deepEqual(Buffer.from((await artwork.getAttribute('src')).split(',')[1], 'base64'), sourceBytes);
    await page.waitForFunction(() => document.getElementById('catalog-artwork').naturalWidth > 0);
    assert.match(await page.locator('#catalog-metadata').innerText(), /proposed/);
    await page.getByRole('button', { name: 'Add to artwork selection', exact: true }).press('Enter');
    await page.locator('#catalog-selection-panel > summary').press('Enter');
    const selectedIds = ['mech-pulley', 'mech-pulley-variant-a'];
    await page.getByRole('button', { name: /Pulley A.*mech-pulley-variant-a/ }).press('Enter');
    await page.waitForFunction(() => document.getElementById('catalog-title').textContent.includes('Pulley A') &&
      !document.getElementById('catalog-inspection').hidden);
    await page.getByRole('button', { name: 'Add to artwork selection', exact: true }).press('Enter');
    const record = cli('selection', '--ids', ...selectedIds);
    const observed = await tool('cse_get_component_selection', {});
    assert.deepEqual(observed.selection, record);
    const proposal = { catalog_sha256: record.catalog_sha256, component_ids: selectedIds };
    assert.deepEqual((await tool('cse_validate_component_selection', proposal)).selection, record);
    const guard = (await context()).guard;
    const agentSelection = await tool('cse_set_component_selection', {
      guard, selection_revision: observed.selection_revision, selection: proposal,
    });
    assert.equal(agentSelection.outcome, 'selected', JSON.stringify(agentSelection.error));
    assert.deepEqual(agentSelection.selection, record);
    const staleSelection = await tool('cse_set_component_selection', {
      guard, selection_revision: observed.selection_revision, selection: null,
    });
    assert.equal(staleSelection.error.code, 'stale_selection');
    assert.equal((await tool('cse_validate_component_selection', {
      ...proposal, component_ids: ['mech-pulley', 'mech-pulley'],
    })).error.code, 'duplicate_id');
    const pendingDownload = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download selection', exact: true }).press('Enter');
    const download = await pendingDownload;
    assert.equal(download.suggestedFilename(), 'cse-component-selection.json');
    const savedRecord = path.join(output, width + '-selection.json');
    await download.saveAs(savedRecord);
    assert.deepEqual(JSON.parse(fs.readFileSync(savedRecord)), record);
    if (width === 1440) {
      const exportParent = fs.mkdtempSync(path.join(process.env.TMPDIR, 'cse-artwork-export-'));
      const result = cli('export', '--format', 'svg', '--selection', savedRecord, '--out', path.join(exportParent, 'svg'));
      assert.deepEqual(result.component_ids, selectedIds);
      assert.deepEqual(fs.readFileSync(path.join(exportParent, 'svg/components/mech-pulley.svg')), sourceBytes);
    }
    const after = await context();
    for (const key of ['project_id', 'commit', 'bundle_sha256', 'model_revision', 'editing_element_id', 'editing_occurrence_id'])
      assert.equal(after.guard[key], withDraft.guard[key], key);
    assert.equal(after.editing_target.declared_name, withDraft.editing_target.declared_name);
    assert.equal(after.has_form_draft, true);
    assert.deepEqual(errors, []);
    const panel = page.locator('#catalog-panel');
    assert(await panel.evaluate(element => element.scrollWidth <= element.clientWidth + 1));
    const screenshot = await panel.screenshot({ path: path.join(output, width + '-catalog.png') });
    await page.reload();
    await page.waitForFunction(() => globalThis.cseWorkbench?.context().ready);
    await page.locator('#catalog-panel > summary').press('Enter');
    await page.locator('#catalog-selection-panel > summary').press('Enter');
    const selectionFile = page.getByLabel('Open saved selection');
    await selectionFile.setInputFiles({ name: 'stale.json', mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify({ ...record, catalog_sha256: '0'.repeat(64) })) });
    await page.getByText(/library changed/i).waitFor();
    assert.equal((await context()).catalog_selection, null);
    await selectionFile.setInputFiles(savedRecord);
    await page.getByText('Opened 2 selected artwork IDs').waitFor();
    assert.deepEqual((await context()).catalog_selection, record);
    assert.equal((await context()).guard.commit, withDraft.guard.commit);
    await page.getByRole('button', { name: 'Remove mech-pulley-variant-a', exact: true }).press('Enter');
    assert.deepEqual((await context()).catalog_selection.component_ids, ['mech-pulley']);
    assert.deepEqual(errors, []);
    observations.push({ width, opened_exact_id: exact.component_id, svg_sha256: hash(sourceBytes),
      screenshot_sha256: hash(screenshot), retained_commit: after.guard.commit, selected_ids: selectedIds,
      selection_sha256: hash(fs.readFileSync(savedRecord)) });
    await page.close();
  }
  fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify({
    status: 'pass', catalog_sha256: before.catalog_sha256, chromium: browser.version(), observations,
    scope: 'Native Git project and real Chromium, synthetic site registration. Exact CLI equality, original SVG bytes, draft preservation, selection download and reload, stale and duplicate refusals, and CLI export from the downloaded record.',
  }, null, 2) + '\n');
} finally {
  if (browser) await browser.close();
  if (fixture.exitCode === null) fixture.kill('SIGINT');
  await done;
  fs.closeSync(log);
}
