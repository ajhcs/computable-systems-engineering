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
const view = 'PC_USAGE';
fs.mkdirSync(output);
const directory = path.join(output, 'fixture');
const log = fs.openSync(path.join(output, 'fixture.log'), 'wx');
const fixture = spawn('python3', ['-B', 'tests/browser/composition_fixture.py', directory, view],
  { cwd: root, stdio: ['ignore', log, log] });
const finished = new Promise(resolve => fixture.once('exit', resolve));
let browser;
try {
  const connection = path.join(directory, 'connection.json');
  for (let attempt = 0; !fs.existsSync(connection); attempt++) {
    assert(fixture.exitCode === null && attempt < 1200, 'Display alias fixture failed to start');
    await sleep(100);
  }
  const { url, project } = JSON.parse(fs.readFileSync(connection));
  const cli = (command, ...flags) => JSON.parse(execFileSync('python3',
    ['-B', 'scripts/composition_project.py', command, '--project', project, ...flags], { cwd: root }));
  const git = (revision, file) => execFileSync('git', ['--git-dir', project, 'show', revision+':'+file], { cwd: root });
  const exportView = name => {
    const folder = path.join(output, name);
    assert.equal(cli('render', '--view-id', view, '--output', folder).status, 'pass');
    return folder;
  };
  const baseline = exportView('baseline');
  const node = JSON.parse(fs.readFileSync(path.join(baseline, 'view.json'))).projection.nodes.Left;
  const binding = { view_id: view, node_id: 'Left', element_id: node.element_id };
  const alias = 'A · B & C';
  const requestFile = path.join(output, 'request.json');
  const request = fields => {
    fs.writeFileSync(requestFile, JSON.stringify(fields));
    return requestFile;
  };
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
  const context = () => page.evaluate(() => cseWorkbench.context());
  const ready = revision => page.waitForFunction(value =>
    globalThis.cseWorkbench?.context().ready && cseWorkbench.context().guard.model_revision === value, revision);
  const call = (name, args) => page.evaluate(({ name, args }) =>
    tools.get(name)({ guard: cseWorkbench.context().guard, ...args }), { name, args });
  const select = async () => {
    const selected = await call('cse_select_element', { element_id: node.element_id, occurrence_id: 'Left' });
    assert.equal(selected.outcome, 'selected', JSON.stringify(selected));
  };
  const label = frame => page.frameLocator(frame).locator('g[data-node-id="Left"] text').first();
  await ready(1);
  await select();
  const initial = await context();
  assert.match(initial.selection.display_alias, /<script>/);
  assert.equal(await page.getByLabel('Declared name', { exact: true }).inputValue(), 'left');
  assert.equal((await call('cse_preview_display_alias', { ...binding, node_id: 'Right', alias })).error.code, 'target');
  assert.equal((await call('cse_preview_display_alias', { ...binding, alias: 'This\nis invalid' })).error.code, 'input');
  assert.equal((await call('cse_preview_display_alias', { ...binding, alias: '未' })).error.code, 'linked_records');
  await page.locator('#discard-draft').click();

  const editor = page.getByLabel('Display alias in this view');
  assert.equal(await editor.inputValue(), initial.selection.display_alias);
  await editor.fill(alias);
  await page.getByRole('button', { name: 'Preview display alias' }).press('Enter');
  await page.waitForFunction(() => cseWorkbench.context().pending_change?.request.operation === 'set_display_alias' &&
    document.getElementById('candidate-diagram').style.visibility === 'visible');
  const pending = (await context()).pending_change;
  assert.deepEqual(pending.preview.display_alias, { ...binding, alias });
  assert.deepEqual(pending.preview.changed_model_files, []);
  assert.equal(await label('#candidate-diagram').textContent(), alias);
  const candidate = cli('preview', '--request', request(pending.request)).preview;
  assert.equal(candidate.request_sha256, pending.preview.request_sha256);
  const save = await call('cse_save_change', { request_id: pending.request.request_id });
  assert.equal(save.outcome, 'committed', JSON.stringify(save.error));
  await ready(2);
  const saved = exportView('saved');
  for (const file of ['sources/model.sysml', 'registry.json', 'layout.json', 'kit-usage.json'])
    assert.deepEqual(fs.readFileSync(path.join(saved, file)), fs.readFileSync(path.join(baseline, file)), file);
  assert.deepEqual(git('HEAD', 'linked/left.scope.json'), git('HEAD^', 'linked/left.scope.json'));
  const svg = fs.readFileSync(path.join(saved, 'view.svg'));
  assert.equal(hash(svg), pending.preview.candidate_svg_sha256);
  assert.equal(await label('#view').textContent(), alias);
  await page.setViewportSize({ width: 390, height: 1050 });
  await page.reload();
  await ready(2);
  await select();
  assert.equal((await context()).selection.display_alias, alias);
  assert.equal(await editor.inputValue(), alias);

  const stale = await call('cse_preview_display_alias', { ...binding, guard: initial.guard, alias: null });
  assert.equal(stale.error.code, 'stale_context');
  const clear = await call('cse_preview_display_alias', { ...binding, alias: null });
  assert.equal(clear.outcome, 'previewed', JSON.stringify(clear.error));
  await page.waitForFunction(() => document.getElementById('candidate-diagram').style.visibility === 'visible');
  assert.equal(await label('#candidate-diagram').textContent(), 'left');
  assert.equal((await call('cse_save_change', { request_id: clear.request.request_id })).outcome, 'committed');
  await ready(3);
  assert.equal(await label('#view').textContent(), 'left');
  await select();
  assert.equal((await context()).selection.display_alias, null);
  assert.equal(await editor.inputValue(), '');
  const restore = { operation: 'restore', request_id: randomUUID(), expected_revision: 3, target_revision: 2 };
  assert.equal(cli('apply', '--request', request(restore)).receipt.revision, 4);
  await ready(4);
  assert.deepEqual(fs.readFileSync(path.join(exportView('restored'), 'view.svg')), svg);
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify({
    status: 'pass', chromium: browser.version(), commit: save.receipt.commit, restored_revision: 4,
    svg_sha256: hash(svg), inputs: Object.fromEntries([
      'verifier/composition_view.py', 'verifier/composition_project.py', 'verifier/composition_session.py',
      'web/composition-workbench.html', 'web/composition-workbench.js', 'web/composition-site-tools.js',
      'tests/browser/composition_display_alias.mjs', 'tests/browser/composition_fixture.py',
    ].map(file => [file, hash(fs.readFileSync(path.join(root, file)))])),
    scope: 'Native Git, Chromium and synthetic WebMCP registration. Keyboard preview, CLI equivalence, exact native source, scope, registry, master usage and geometry, phone reopen, alias removal and exact Git restoration.',
  }, null, 2)+'\n');
} finally {
  if (browser) await browser.close();
  if (fixture.exitCode === null) fixture.kill('SIGINT');
  await finished;
  fs.closeSync(log);
}
