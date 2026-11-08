// Native browser workflow on disposable synthetic data. No npm dependencies.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn, spawnSync} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {BrowserReview} from './browser_review.mjs';

assert.ok(Number(process.versions.node.split('.')[0]) >= 22);
const fixture = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const origin = new URL(fixture.origin);
assert.equal(origin.hostname, '127.0.0.1');
assert.equal(origin.protocol, 'http:');
const binary = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']
  .map(name => spawnSync('which', [name], {encoding: 'utf8'}).stdout.trim()).find(Boolean);
assert.ok(binary, 'A supported installed Chromium binary is required');
const profile = fs.mkdtempSync(path.join(path.dirname(process.argv[2]), 'chromium-profile-'));
const browser = spawn(binary, ['--headless=new', '--disable-background-networking', '--disable-sync',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check',
  '--remote-debugging-pipe', `--user-data-dir=${profile}`],
  {stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe']});
let log = '';
browser.stderr.on('data', data => { log = (log + data).slice(-16000); });
let terminal = false;
let sequence = 0;
let buffer = '';
const pending = new Map();
const pages = new Map();
const failures = [];
const call = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
  if (terminal) return reject(new Error('Browser is terminal'));
  const id = ++sequence;
  const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP timeout: ' + method)); }, 15000);
  pending.set(id, {resolve, reject, timer});
  browser.stdio[3].write(JSON.stringify({id, method, params, ...(sessionId ? {sessionId} : {})}) + '\0');
});
const rejectPending = error => {
  for (const request of pending.values()) { clearTimeout(request.timer); request.reject(error); }
  pending.clear();
};
browser.on('error', error => { terminal = true; rejectPending(error); });
browser.on('exit', (code, signal) => {
  terminal = true;
  rejectPending(new Error(`Chromium exited ${code}/${signal}: ${log}`));
});
browser.stdio[4].setEncoding('utf8');
browser.stdio[4].on('data', chunk => {
  buffer += chunk;
  let end;
  while ((end = buffer.indexOf('\0')) >= 0) {
    const line = buffer.slice(0, end); buffer = buffer.slice(end + 1);
    if (!line) continue;
    const event = JSON.parse(line);
    if (event.id) {
      const request = pending.get(event.id);
      if (!request) continue;
      pending.delete(event.id); clearTimeout(request.timer);
      event.error ? request.reject(new Error(JSON.stringify(event.error))) : request.resolve(event.result);
    } else if (event.method === 'Fetch.requestPaused') {
      const local = new URL(event.params.request.url).origin === origin.origin;
      void call(local ? 'Fetch.continueRequest' : 'Fetch.failRequest',
        {requestId: event.params.requestId, ...(!local ? {errorReason: 'BlockedByClient'} : {})}, event.sessionId)
        .catch(error => failures.push(error.message));
    } else if (event.method === 'Network.responseReceived' && event.params.type === 'Document') {
      const page = pages.get(event.sessionId);
      if (page) page.status = event.params.response.status;
    } else if (event.method === 'Page.lifecycleEvent' && event.params.name === 'load') {
      const page = pages.get(event.sessionId);
      if (page && event.params.frameId === page.mainFrameId) page.loadedLoaders.add(event.params.loaderId);
    }
  }
});
const contexts = [];
const checks = [];
let review;
let active;
try {
  const version = await call('Browser.getVersion');
  const createPage = async identity => {
    const {browserContextId} = await call('Target.createBrowserContext');
    contexts.push(browserContextId);
    const {targetId} = await call('Target.createTarget', {url: 'about:blank', browserContextId});
    const {sessionId} = await call('Target.attachToTarget', {targetId, flatten: true});
    const page = {identity, sessionId, status: null, loadedLoaders: new Set()};
    pages.set(sessionId, page);
    page.call = (method, params) => call(method, params, sessionId);
    page.eval = async expression => {
      const result = await page.call('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
      assert.ok(!result.exceptionDetails, 'Renderer expression failed');
      return result.result.value;
    };
    await page.call('Page.enable');
    page.mainFrameId = (await page.call('Page.getFrameTree')).frameTree.frame.id;
    await page.call('Page.setLifecycleEventsEnabled', {enabled: true});
    await page.call('Network.enable');
    await page.call('Fetch.enable', {patterns: [{urlPattern: 'http://*'}, {urlPattern: 'https://*'}]});
    if (identity !== 'anonymous') {
      const result = await page.call('Network.setCookie', {name: 'sessionid', value: fixture.cookies[identity],
        url: origin.origin, httpOnly: true, sameSite: 'Lax'});
      assert.equal(result.success, true);
    }
    page.wait = async (test, message) => {
      for (let n = 0; !(await (typeof test === 'function' ? test() : page.eval(test))); n++) {
        assert.ok(n < 100, message); await delay(100);
      }
    };
    page.navigate = async pathname => {
      active = page;
      await page.call('Page.bringToFront');
      const old = (await page.call('Page.getFrameTree')).frameTree.frame.loaderId;
      await page.call('Page.navigate', {url: origin.origin + pathname});
      await page.wait(async () => {
        const frame = (await page.call('Page.getFrameTree')).frameTree.frame;
        return frame.loaderId !== old && page.loadedLoaders.has(frame.loaderId);
      }, 'Expected the new document to complete its load lifecycle');
    };
    page.text = () => page.eval('document.body.innerText');
    page.key = async (key, modifiers = 0) => {
      const codes = {Tab: 9, Enter: 13, a: 65};
      for (const type of ['keyDown', 'keyUp']) await page.call('Input.dispatchKeyEvent',
        {type, key, code: key === 'a' ? 'KeyA' : key, windowsVirtualKeyCode: codes[key], modifiers,
          ...(type === 'keyDown' && key === 'Enter' ? {text: '\r', unmodifiedText: '\r'} : {})});
    };
    page.tabTo = async selector => {
      assert.equal(await page.eval('document.querySelectorAll(' + JSON.stringify(selector) + ').length'),
        1, 'Keyboard target must identify exactly one control: ' + selector);
      for (let n = 0; !(await page.eval('document.activeElement.matches(' + JSON.stringify(selector) + ')')); n++) {
        assert.ok(n < 100, 'Keyboard cannot reach ' + selector); await page.key('Tab');
      }
    };
    page.fill = fields => page.eval(`(() => { for (const [id, value] of Object.entries(${JSON.stringify(fields)})) {
      const field = document.getElementById(id); if (!field) throw new Error('Missing fixed fixture field');
      if (field.type === 'checkbox') field.checked = value; else field.value = value;
    } })()`);
    page.type = async (selector, text) => {
      await page.call('Page.bringToFront');
      await page.tabTo(selector);
      await page.key('a', process.platform === 'darwin' ? 4 : 2);
      await page.call('Input.insertText', {text});
    };
    page.submit = async selector => {
      active = page;
      await page.call('Page.bringToFront');
      await page.tabTo(selector);
      const old = (await page.call('Page.getFrameTree')).frameTree.frame.loaderId;
      await page.key('Enter');
      await page.wait(async () => {
        const frame = (await page.call('Page.getFrameTree')).frameTree.frame;
        return frame.loaderId !== old && page.loadedLoaders.has(frame.loaderId);
      }, 'Keyboard submission must load a new document');
    };
    page.post = (pathname, data) => page.eval(`(async () => {
      const body = new URLSearchParams(${JSON.stringify(data)});
      body.set('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
      const response = await fetch(${JSON.stringify(pathname)}, {method: 'POST', body});
      return response.status;
    })()`);
    return page;
  };
  const anon = await createPage('anonymous');
  const author = await createPage('author');
  const other = await createPage('other');
  const self = await createPage('self');
  const moderator = await createPage('moderator');
  review = new BrowserReview(fixture.review_directory, fixture.source,
    (method, params) => active.call(method, params), expression => active.eval(expression));
  const submitted = fixture.submissions.author;
  const moderate = '/moderation/' + submitted + '/';
  const editor = '/workspace/' + submitted + '/';
  const reason = action => 'SYNTHETIC PRIVATE ' + action;
  const decision = async action => {
    await moderator.navigate(moderate);
    assert.ok((await moderator.text()).includes('must not be described as scientific peer review'));
    await moderator.fill({id_conflicts: 'None; SYNTHETIC fixture', id_reason: reason(action), id_action: action});
    await moderator.submit('form.stack-form:not([action]) button[type=submit]');
    assert.equal(moderator.status, 200);
    assert.ok((await moderator.text()).includes(reason(action)));
  };
  const operate = async (open, limit) => {
    await moderator.navigate('/operations/');
    await moderator.fill({id_intake_open: open, id_queue_limit: limit,
      id_reason: 'SYNTHETIC browser capacity change'});
    await moderator.submit('form.stack-form:not([action]) button[type=submit]');
    assert.equal(moderator.status, 200);
    assert.equal(await moderator.eval('document.getElementById("id_intake_open").checked'), open);
  };
  const audit = async (page, name, width, phase = 'page') => {
    active = page;
    await page.call('Emulation.setDeviceMetricsOverride', {width, height: 900, deviceScaleFactor: 1, mobile: false});
    const geometry = await page.eval(`({width: innerWidth, client: document.documentElement.clientWidth,
      scroll: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
      main: document.querySelectorAll('main#main').length, h1: document.querySelectorAll('h1').length})`);
    assert.equal(geometry.width, width); assert.ok(geometry.scroll <= geometry.client, 'Horizontal overflow: ' + name);
    assert.equal(geometry.main, 1); assert.equal(geometry.h1, 1);
    await review.audit(name, width, phase, true);
  };
  await anon.navigate(moderate);
  assert.ok((await anon.eval('location.pathname')).startsWith('/accounts/login/'));
  assert.ok(!(await anon.text()).includes('SYNTHETIC moderation workflow fixture'));
  await other.navigate('/moderation/'); assert.equal(other.status, 403);
  await other.navigate(editor); assert.equal(other.status, 404);
  await other.navigate(editor + 'export/'); assert.equal(other.status, 404);
  await other.navigate('/workspace/');
  assert.equal(await other.post(moderate, {action: 'publish', reason: 'SYNTHETIC forbidden',
    conflicts: 'None; SYNTHETIC fixture', revision: '1'}), 403);
  checks.push('anonymous and unrelated superuser private/decision boundaries');
  await self.navigate('/moderation/' + fixture.submissions.self + '/');
  await self.fill({id_conflicts: 'None; SYNTHETIC fixture', id_reason: 'SYNTHETIC forbidden self', id_action: 'publish'});
  await self.submit('form.stack-form:not([action]) button[type=submit]');
  assert.equal(self.status, 403); assert.ok((await self.text()).includes('own submission'));
  checks.push('explicit moderator/superuser self-decision refusal');
  for (const width of [1440, 390, 320]) {
    for (const [pathname, label] of [['/moderation/', 'moderation-queue'], [moderate, 'decision'], ['/operations/', 'operations']]) {
      await moderator.navigate(pathname);
      await audit(moderator, label, width);
      if (pathname === '/moderation/') assert.ok((await moderator.text()).includes('not scientific validation or independent peer review'));
    }
  }
  await moderator.call('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'reduce'}]});
  assert.equal(await moderator.eval(`matchMedia('(prefers-reduced-motion: reduce)').matches &&
    getComputedStyle(document.documentElement).scrollBehavior === 'auto' &&
    [...document.querySelectorAll('.button')].every(button =>
      getComputedStyle(button).transitionDuration.split(',').every(value => parseFloat(value) === 0))`), true);
  checks.push('reduced-motion styles in the actual renderer');
  await moderator.navigate(moderate);
  // Skip only the browser's required-field gate to exercise server validation.
  // The native POST and every server permission/CSRF rule remain in force.
  await moderator.eval('document.querySelector("form.stack-form:not([action])").noValidate = true');
  await moderator.submit('form.stack-form:not([action]) button[type=submit]');
  assert.equal(moderator.status, 400);
  await moderator.tabTo('.form-errors a[href="#id_reason"]');
  await moderator.key('Enter');
  await moderator.wait('document.activeElement.id === "id_reason"', 'Error summary must focus its field');
  assert.equal(await moderator.eval(`(() => {
    const field = document.activeElement, style = getComputedStyle(field), rect = field.getBoundingClientRect();
    const described = (field.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean);
    return field.getAttribute('aria-invalid') === 'true' && field.labels.length === 1 &&
      described.includes('id_reason_error') && described.every(id => document.getElementById(id)) &&
      style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) >= 2 &&
      rect.top >= 0 && rect.top < innerHeight;
  })()`), true, 'Invalid moderation field must have visible focus and linked descriptions');
  await audit(moderator, 'decision-error', 320, 'error');
  checks.push('moderation linked validation errors and native keyboard focus');
  await decision('changes');
  await author.navigate(editor); assert.ok((await author.text()).includes(reason('changes')));
  assert.ok(await author.eval('!!document.getElementById("id_claims")'));
  await author.type('#id_claims', 'SYNTHETIC revised claims before appeal.');
  await author.submit('button[value=save]'); assert.equal(author.status, 200);
  assert.equal(await author.eval('document.querySelector("[name=revision]").value'), '3');
  await author.submit('button[value=submit]'); assert.equal(author.status, 409);
  assert.ok((await author.text()).includes('Intake is paused'));
  await operate(true, 2);
  await author.navigate(editor); await author.submit('button[value=submit]'); assert.equal(author.status, 429);
  assert.ok((await author.text()).includes('Moderation capacity is full'));
  await operate(true, 3);
  await author.navigate(editor); await author.submit('button[value=submit]'); assert.equal(author.status, 200);
  assert.ok((await author.text()).includes('This version is frozen'));
  checks.push('changes/save while paused, paused refusal, finite queue refusal, resubmit');
  await operate(false, 3);
  await decision('decline');
  assert.equal(await moderator.post(moderate, {action: 'publish', reason: 'SYNTHETIC stale',
    conflicts: 'None; SYNTHETIC fixture', revision: '4'}), 409);
  await author.navigate(editor); assert.ok((await author.text()).includes(reason('decline')));
  await audit(author, 'author-declined', 320);
  await author.fill({id_reason: reason('appeal')});
  await author.submit('form[action$="/appeal/"] button'); assert.equal(author.status, 200);
  assert.ok((await author.text()).includes('Open appeal'));
  await moderator.navigate('/operations/'); assert.ok((await moderator.text()).includes(reason('appeal')));
  await moderator.navigate(moderate);
  const responseId = await moderator.eval('document.querySelector("textarea[id^=appeal-response-]").id');
  const reopenId = responseId.replace('response', 'reopen');
  await moderator.fill({[responseId]: reason('response'), [reopenId]: true});
  await moderator.submit('form[action^="/moderation/appeals/"] button'); assert.equal(moderator.status, 200);
  await audit(moderator, 'appeal-resolved', 320);
  await author.navigate(editor); assert.ok((await author.text()).includes(reason('response')));
  await author.type('#id_claims', 'SYNTHETIC final frozen claims after appeal.');
  await operate(true, 3);
  await author.submit('button[value=submit]'); assert.equal(author.status, 200);
  await operate(false, 3);
  await decision('publish');
  // Lost-response retry must not create another publication or decision.
  assert.equal(await moderator.post(moderate, {action: 'publish', reason: reason('publish'),
    conflicts: 'None; SYNTHETIC fixture', revision: '7'}), 200);
  checks.push('decline/stale refusal/private appeal and response/reopen/exact publish/idempotent retry');
  await author.navigate('/workspace/' + fixture.draft + '/');
  await author.fill({id_title: 'SYNTHETIC saved while paused'});
  await author.submit('button[value=save]'); assert.equal(author.status, 200);
  await audit(author, 'paused-draft', 320);
  await anon.navigate('/archive/');
  const versionPath = await anon.eval('document.querySelector(".research-card h2 a").getAttribute("href")');
  assert.match(versionPath, /^\/research\/[0-9a-f-]+\/v1\/$/);
  await anon.navigate(versionPath);
  const text = await anon.text();
  assert.ok(text.includes('SYNTHETIC final frozen claims after appeal.'));
  assert.ok(!text.includes('SYNTHETIC PRIVATE'));
  assert.ok(!text.includes('SYNTHETIC revised claims before appeal.'));
  await audit(anon, 'published-version', 320);
  const exported = await anon.eval(`fetch(${JSON.stringify(versionPath + 'export/')}).then(r => r.json())`);
  assert.equal(exported.research.claims, 'SYNTHETIC final frozen claims after appeal.');
  assert.ok(!JSON.stringify(exported).includes('SYNTHETIC PRIVATE'));
  checks.push('public exact snapshot and no private decision/appeal content');
  assert.deepEqual(failures, []);
  const result = review.finish(true, version.product);
  result.workflow_checks = checks;
  result.isolated_browser_contexts = contexts.length;
  result.non_loopback_fetches_blocked = true;
  result.sandbox_disable_flag = false;
  review.save();
  console.log(JSON.stringify({browser: version.product, workflow_checks: checks,
    isolated_browser_contexts: contexts.length, screenshot_states: result.states.length,
    contrast_failures: result.failures.length, contrast_unmeasured: result.unknown.length,
    human_accessibility: 'unrun', actual_browser_zoom: 'unrun'}));
  assert.equal(result.unknown.length, 0, 'Unmeasured moderation contrast requires review');
  assert.equal(result.failures.length, 0, 'Moderation contrast failure');
} finally {
  if (review && !review.finished) review.finish(false);
  for (const browserContextId of contexts) {
    if (!terminal) try { await call('Target.disposeBrowserContext', {browserContextId}); } catch {}
  }
  if (!terminal) try { await call('Browser.close'); } catch {}
  for (const signal of ['SIGTERM', 'SIGKILL']) {
    if (!terminal) await Promise.race([new Promise(resolve => browser.once('exit', resolve)), delay(2000)]);
    if (!terminal) browser.kill(signal);
  }
  rejectPending(new Error('Probe closed'));
}
