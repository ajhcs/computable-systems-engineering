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
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const view = 'PC_USAGE';
const node = 'Left';
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
    assert(fixture.exitCode === null && attempt < 1200, 'Native layout fixture failed to start');
    await sleep(100);
  }
  const { url, project } = JSON.parse(fs.readFileSync(connection));
  const artifact = name => {
    const folder = path.join(output, name);
    const cli = command => JSON.parse(execFileSync('python3', ['-B', 'scripts/composition_project.py',
      command, '--project', project, '--view-id', view, '--output', folder], { cwd: root }));
    assert.equal(cli('render').status, 'pass');
    if (name === 'resized') assert.equal(cli('check-render').status, 'pass');
    return file => fs.readFileSync(path.join(folder, file));
  };
  const baseline = artifact('baseline');
  const initial = JSON.parse(baseline('layout.json'));
  const element = JSON.parse(baseline('view.json')).projection.nodes[node].element_id;
  const original = initial.nodes[node];
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
    const result = await call('cse_select_element', { element_id: element, occurrence_id: node });
    assert.equal(result.outcome, 'selected', JSON.stringify(result));
  };
  const frameGroup = (selector = '#view') => page.frameLocator(selector).locator('g[data-node-id="Left"]');
  const drawingRect = selector => frameGroup(selector).evaluate(group => {
    const outline = group.querySelector('rect');
    return outline && ['x','y','width','height'].map(key => Number(outline.getAttribute(key)));
  });
  const pendingDrawing = async box => {
    await page.waitForFunction(() => cseWorkbench.context().pending_change?.request.operation === 'set_layout' &&
      document.getElementById('candidate-diagram').style.visibility === 'visible');
    const { pending_change } = await context();
    assert.deepEqual(pending_change.preview.candidate_layout.nodes[node], box);
    assert.deepEqual(pending_change.preview.changed_model_files, []);
    const candidate = await drawingRect('#candidate-diagram');
    assert.deepEqual(candidate, [box.x, box.y, box.width, box.height]);
    return pending_change;
  };
  await ready(1);
  await select();
  assert.deepEqual(await drawingRect('#view'), [original.x, original.y, original.width, original.height]);
  await frameGroup().scrollIntoViewIfNeeded();
  const bounds = await frameGroup().boundingBox();
  const x = bounds.x + 30, y = bounds.y + 25;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 20, y + 10, { steps: 4 });
  await page.mouse.up();
  const movedBox = { ...original, x: original.x + 20, y: original.y + 10 };
  const move = await pendingDrawing(movedBox);
  assert.deepEqual(await drawingRect('#view'), [original.x, original.y, original.width, original.height]);
  assert.equal((await call('cse_save_change', { request_id: move.request.request_id })).outcome, 'committed');
  await ready(2);
  const moved = artifact('moved');
  assert.equal(hash(moved('view.svg')), move.preview.candidate_svg_sha256);

  await select();
  const invalid = await call('cse_preview_layout', { element_id: element, box: { ...movedBox, width: 4 } });
  assert.equal(invalid.outcome, 'refused');
  assert.equal((await context()).guard.model_revision, 2);
  await page.locator('#discard-draft').click();
  const resizedBox = { ...movedBox, width: movedBox.width + 48, height: movedBox.height + 12 };
  const resize = await call('cse_preview_layout', { element_id: element, box: resizedBox });
  assert.equal(resize.outcome, 'previewed', JSON.stringify(resize.error));
  await pendingDrawing(resizedBox);
  assert.deepEqual(await drawingRect('#view'), [movedBox.x, movedBox.y, movedBox.width, movedBox.height]);
  await page.getByRole('button', { name: 'Save change', exact: true }).press('Enter');
  await ready(3);
  const saved = artifact('resized');
  const layout = JSON.parse(saved('layout.json'));
  assert.deepEqual(layout, resize.preview.candidate_layout);
  assert.equal(hash(saved('view.svg')), resize.preview.candidate_svg_sha256);
  for (const file of ['sources/model.sysml', 'registry.json'])
    assert.deepEqual(saved(file), baseline(file), file);
  const kitBefore = JSON.parse(baseline('kit-usage.json'));
  const kitAfter = JSON.parse(saved('kit-usage.json'));
  const adaptation = kitBefore.adaptations.find(row => row.node === node);
  assert.deepEqual(adaptation.geometry, original);
  adaptation.geometry = resizedBox;
  assert.deepEqual(kitAfter, kitBefore);
  const scope = ref => execFileSync('git', ['--git-dir', project, 'show', ref+':linked/left.scope.json']);
  assert.deepEqual(scope('HEAD'), scope('HEAD~2'));
  for (const [edge, route] of Object.entries(layout.edges)) {
    if (edge === 'OwnLeft')
      assert.deepEqual(route.points.at(-1), [resizedBox.x, resizedBox.y + resizedBox.height/2]);
    else
      assert.deepEqual(route, initial.edges[edge]);
  }
  await page.reload();
  await ready(3);
  await select();
  assert.deepEqual((await context()).selection.box, resizedBox);
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify({
    status: 'pass', chromium: browser.version(), saved_revision: 3,
    moved_svg_sha256: hash(moved('view.svg')), resized_svg_sha256: hash(saved('view.svg')),
    inputs: Object.fromEntries(['verifier/composition_session.py','verifier/composition_view.py',
      'web/composition-workbench.js','web/composition-site-tools.js','tests/browser/composition_fixture.py',
      'tests/browser/composition_layout_preview.mjs'].map(file => [file, hash(fs.readFileSync(path.join(root,file)))])),
    scope: 'Actual Chromium pointer move and guarded site-tool resize, native Git, exact candidate SVG and independent saved exports, unchanged SysML, registry, scope and original kit. Synthetic site registration.',
  }, null, 2)+'\n');
} finally {
  if (browser) await browser.close();
  if (fixture.exitCode === null) fixture.kill('SIGINT');
  await finished;
  fs.closeSync(log);
}
