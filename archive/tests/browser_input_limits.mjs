// Synthetic, loopback-only native input/encoding verification. No npm dependencies.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn, spawnSync} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {BrowserReview} from './browser_review.mjs';

assert.ok(Number(process.versions.node.split('.')[0]) >= 22, 'Node 22+ with native WebSocket is required.');
const fixture = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const origin = new URL(fixture.origin);
assert.equal(origin.hostname, '127.0.0.1');
const binary = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']
  .map(name => spawnSync('which', [name], {encoding: 'utf8'}).stdout.trim()).find(Boolean);
assert.ok(binary, 'A supported installed Chromium binary is required.');
const profile = fs.mkdtempSync(path.join(path.dirname(process.argv[2]), 'chromium-profile-'));
const browser = spawn(binary, ['--headless=new', '--disable-background-networking', '--disable-sync',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check',
  '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], {stdio: ['ignore', 'ignore', 'pipe']});
let browserLog = '';
browser.stderr.on('data', bytes => { browserLog = (browserLog + bytes).slice(-16000); });
let socket;
let closeBrowser;
let probeFailed = false;
let review;
let failureContext;
try {
  const activePort = path.join(profile, 'DevToolsActivePort');
  for (let attempt = 0; !fs.existsSync(activePort); attempt++) {
    assert.ok(attempt < 150 && browser.exitCode === null && browser.signalCode === null,
      `Chromium startup failed: ${browserLog}`);
    await delay(100);
  }
  const port = Number(fs.readFileSync(activePort, 'utf8').split('\n')[0]);
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {method: 'PUT'})).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, {once: true});
    socket.addEventListener('error', reject, {once: true});
  });
  let sequence = 0;
  const pending = new Map();
  const posts = [];
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 15000);
    pending.set(id, {resolve, reject, timer});
    socket.send(JSON.stringify({id, method, params}));
  });
  closeBrowser = () => call('Browser.close');
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const request = pending.get(message.id);
      if (!request) return;
      pending.delete(message.id); clearTimeout(request.timer);
      if (message.error) request.reject(new Error(JSON.stringify(message.error)));
      else request.resolve(message.result);
    } else if (message.method === 'Fetch.requestPaused') {
      const url = new URL(message.params.request.url);
      const method = url.origin === origin.origin ? 'Fetch.continueRequest' : 'Fetch.failRequest';
      void call(method, {requestId: message.params.requestId,
        ...(method === 'Fetch.failRequest' ? {errorReason: 'BlockedByClient'} : {})}).catch(() => {});
    } else if (message.method === 'Network.requestWillBeSent' && message.params.request.method === 'POST') {
      const request = message.params.request;
      assert.equal(new URL(request.url).origin, origin.origin);
      if (request.postData) posts.push({bytes: Buffer.byteLength(request.postData),
        crlf: request.postData.includes('%0D%0A')});
    }
  });
  const evaluate = async expression => {
    const response = await call('Runtime.evaluate', {expression, returnByValue: true});
    assert.ok(!response.exceptionDetails, JSON.stringify(response.exceptionDetails));
    return response.result.value;
  };
  // Synthetic control metadata only: never log values, cookies, text or URLs.
  failureContext = () => evaluate('(' + function () {
    const active = document.activeElement;
    return {ready: document.readyState, pageFocused: document.hasFocus(),
      activeId: active?.id, activeTag: active?.tagName,
      activeErrorLink: !!active?.matches('.form-errors a[href="#id_artifacts"]'),
      fragment: ['#main', '#id_artifacts', ''].includes(location.hash) ? location.hash : 'other',
      artifactPresent: !!document.getElementById('id_artifacts'),
      errorLinkPresent: !!document.querySelector('.form-errors a[href="#id_artifacts"]'),
      events: window.__syntheticFocusEvents || []};
  }.toString() + ')()');
  review = new BrowserReview(fixture.review_directory, fixture.source, call, evaluate);
  await call('Page.enable');
  await call('Page.addScriptToEvaluateOnNewDocument', {source: '(' + function () {
    const events = window.__syntheticFocusEvents = [];
    const record = event => {
      if (event.type.startsWith('key') && !['Tab', 'Enter'].includes(event.key)) return;
      const target = event.target;
      const active = document.activeElement;
      events.push({type: event.type, key: event.key, ready: document.readyState,
        activeId: active?.id, activeTag: active?.tagName, targetId: target?.id,
        errorLink: !!target?.matches?.('.form-errors a[href="#id_artifacts"]'),
        fragment: ['#main', '#id_artifacts', ''].includes(location.hash) ? location.hash : 'other'});
      if (events.length > 40) events.shift();
    };
    for (const type of ['DOMContentLoaded', 'load', 'hashchange', 'focusin', 'keydown', 'keyup']) {
      window.addEventListener(type, record, true);
    }
  }.toString() + ')()'});
  await call('Page.bringToFront');
  await call('Network.enable', {maxPostDataSize: 1024 * 1024});
  await call('Fetch.enable', {patterns: [{urlPattern: 'http://*'}, {urlPattern: 'https://*'}]});
  const key = async (name, modifiers = 0) => {
    const codes = {Tab: 9, Enter: 13, a: 65};
    for (const type of ['keyDown', 'keyUp']) {
      await call('Input.dispatchKeyEvent', {type, key: name,
        code: name === 'a' ? 'KeyA' : name, windowsVirtualKeyCode: codes[name], modifiers,
        ...(type === 'keyDown' && name === 'Enter' ? {text: '\r', unmodifiedText: '\r'} : {})});
    }
  };
  const waitFor = async (expression, message) => {
    for (let attempt = 0; !(await (typeof expression === 'function' ? expression() : evaluate(expression))); attempt++) {
      assert.ok(attempt < 100, message);
      await delay(100);
    }
  };
  const navigate = async pathname => {
    await call('Page.navigate', {url: origin.origin + pathname});
    await waitFor('location.pathname === ' + JSON.stringify(pathname) +
      ' && document.readyState === "complete"', 'Expected page did not finish rendering');
  };
  const focusVisible = async () => evaluate('(' + function () {
    const element = document.activeElement;
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.top < innerHeight &&
      rect.left >= 0 && rect.right <= innerWidth && style.outlineStyle !== 'none' &&
      parseFloat(style.outlineWidth) >= 2 && style.outlineColor !== 'rgba(0, 0, 0, 0)';
  }.toString() + ')()');
  const tabTo = async (selector, modifiers = 0) => {
    for (let attempt = 0; ; attempt++) {
      if (await evaluate('document.activeElement.matches(' + JSON.stringify(selector) + ')')) return;
      assert.ok(attempt < 80, 'Keyboard could not reach ' + selector);
      await key('Tab', modifiers);
    }
  };
  const reflow = [];
  const auditPages = async paths => {
    for (const width of [1440, 390, 320]) {
      await call('Emulation.setDeviceMetricsOverride',
        {width, height: 900, deviceScaleFactor: 1, mobile: false});
      for (const pathname of paths) {
        await navigate(pathname);
        const name = pathname === fixture.editor ? 'editor' :
          ({'/': 'home', '/archive/': 'archive', '/policies/': 'policies',
            '/accounts/login/': 'login', '/workspace/': 'workspace'})[pathname];
        assert.ok(name, 'Review pages must have an explicit synthetic label');
        const geometry = await evaluate('(' + function () {
          return {viewport: innerWidth, client: document.documentElement.clientWidth,
            scroll: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
            main: document.querySelectorAll('main#main').length,
            headings: document.querySelectorAll('h1').length};
        }.toString() + ')()');
        assert.equal(geometry.viewport, width);
        assert.ok(geometry.scroll <= geometry.client, 'Horizontal page overflow: ' + JSON.stringify({path: pathname, width, ...geometry}));
        assert.equal(geometry.main, 1, 'One main landmark is required');
        assert.equal(geometry.headings, 1, 'One page heading is required');
        await review.audit(name, width, 'page', true);
        // Django's local login intentionally autofocuses username. Reach the first
        // link by native reverse Tab there; other pages must start with the skip link.
        if (await evaluate('document.activeElement.matches("[autofocus]")')) {
          await tabTo('.skip-link', 8);
        } else {
          await key('Tab');
        }
        const focused = await evaluate('({skip: document.activeElement.classList.contains("skip-link"), id: document.activeElement.id, tag: document.activeElement.tagName, pageFocused: document.hasFocus()})');
        assert.equal(focused.skip, true, 'Keyboard must reach the skip link: ' +
          JSON.stringify({path: pathname, width, ...focused}));
        await waitFor(focusVisible, 'Skip-link focus must be visible in the viewport');
        await review.audit(name, width, 'skip');
        await key('Enter');
        await waitFor('document.activeElement.id === "main"', 'Skip link must focus main');
        reflow.push({path: pathname, ...geometry, keyboard_skip_link: true});
      }
    }
  };
  await auditPages(['/', '/archive/', '/policies/', '/accounts/login/']);
  await call('Network.setCookie', {name: fixture.cookie.name, value: fixture.cookie.value, url: origin.origin,
    httpOnly: true, sameSite: 'Lax'});
  await call('Page.navigate', {url: origin.origin + fixture.editor});
  for (let attempt = 0; !(await evaluate('!!document.getElementById("id_methods")')); attempt++) {
    assert.ok(attempt < 100, 'Authenticated editor did not render'); await delay(100);
  }
  await evaluate('document.getElementById("id_methods").focus()');
  await call('Input.insertText', {text: '界'.repeat(9998) + '\nX'});
  const newlineCount = await evaluate('document.getElementById("id_methods").value.length');
  assert.equal(newlineCount, 10000);
  await call('Input.insertText', {text: 'X'});
  assert.equal(await evaluate('document.getElementById("id_methods").value.length'), 10000);
  await evaluate('document.getElementById("id_limitations").focus()');
  await call('Input.insertText', {text: '😀'.repeat(2501)});
  const emojiCount = await evaluate('document.getElementById("id_limitations").value.length');
  assert.equal(emojiCount, 5000);
  const limits = await evaluate(`(() => {
    const form = document.querySelector('form.stack-form');
    const limits = {};
    for (const element of form.querySelectorAll('input[maxlength], textarea[maxlength]')) {
      limits[element.name] = element.maxLength;
      element.value = '界'.repeat(element.maxLength);
    }
    const prefix = 'https://example.org/synthetic/';
    form.elements.artifacts.value = Array.from({length: 8}, (_, index) =>
      prefix + '界'.repeat((index === 7 ? 993 : 1000) - prefix.length)).join('\\n');
    form.elements.methods.value = '界'.repeat(9998) + '\\nX';
    form.elements.rights_confirmed.checked = true;
    form.elements.privacy_confirmed.checked = true;
    form.requestSubmit(form.querySelector('button[value="save"]'));
    return limits;
  })()`);
  for (let attempt = 0; ; attempt++) {
    const revision = await evaluate('document.querySelector("input[name=revision]")?.value');
    if (revision === '1') break;
    assert.ok(attempt < 150, 'Native multilingual form did not save'); await delay(100);
  }
  assert.equal(await evaluate('document.getElementById("id_methods").value'), '界'.repeat(9998) + '\nX');
  assert.equal(await evaluate('document.getElementById("id_artifacts").value.length'), 8000);
  assert.equal(Object.keys(limits).length, 10);
  assert.equal(posts.length, 1);
  assert.ok(posts[0].bytes > 96 * 1024 && posts[0].bytes < 512 * 1024);
  assert.equal(posts[0].crlf, true);
  // A valid unbroken maximum-length title must also reflow in the workspace.
  await tabTo('#id_title');
  await key('a', process.platform === 'darwin' ? 4 : 2);
  await call('Input.insertText', {text: 'SYNTHETIC-' + 'x'.repeat(190)});
  await tabTo('button[value="save"]');
  await key('Enter');
  await waitFor('document.querySelector("input[name=revision]")?.value === "2"',
    'Native keyboard title save did not commit');
  await auditPages(['/workspace/', fixture.editor]);
  await tabTo('#id_artifacts');
  await key('a', process.platform === 'darwin' ? 4 : 2);
  await call('Input.insertText', {text: 'http://127.0.0.1/SYNTHETIC-inert-reference'});
  await tabTo('button[value="save"]');
  await key('Enter');
  const errorLink = '.form-errors a[href="#id_artifacts"]';
  const focusErrorSummary = async () => {
    await waitFor('!!document.querySelector(' + JSON.stringify(errorLink) + ')',
      'Linked artifact error did not render');
    assert.equal(await evaluate('document.querySelector("input[name=revision]").value'), '2',
      'Rejected form input must preserve the accepted draft revision');
    assert.equal(await evaluate('document.getElementById("id_artifacts").getAttribute("aria-invalid")'), 'true');
    assert.equal(await evaluate('document.getElementById("id_artifacts").labels.length'), 1);
    assert.equal(await evaluate('(' + function () {
      const described = document.getElementById('id_artifacts').getAttribute('aria-describedby') || '';
      const ids = described.split(/\s+/).filter(Boolean);
      return ids.includes('id_artifacts_error') && ids.includes('id_artifacts_helptext') &&
        ids.every(id => document.getElementById(id));
    }.toString() + ')()'), true, 'Error/help descriptions must refer to existing elements');
    await tabTo(errorLink);
    await key('Enter');
    await waitFor('document.activeElement.id === "id_artifacts"',
      'Error-summary activation must focus the invalid field');
    await waitFor(focusVisible, 'Error-summary activation must visibly focus the invalid field');
  };
  await focusErrorSummary();
  await review.audit('editor', 320, 'error');
  assert.equal(posts.length, 3, 'Two accepted saves and one rejected validation request are expected');
  // A bounded reproduction, stopping on the first failure. Every iteration is a
  // new rejected document, not a retry of a failed assertion or an accepted save.
  const extraRejectedDocuments = 20;
  for (let round = 0; round < extraRejectedDocuments; round++) {
    const previousLoader = (await call('Page.getFrameTree')).frameTree.frame.loaderId;
    await tabTo('button[value="save"]');
    await key('Enter');
    await waitFor(async () => (await call('Page.getFrameTree')).frameTree.frame.loaderId !== previousLoader,
      'Expected a new validation-error document');
    await focusErrorSummary();
    assert.equal(posts.length, 4 + round, 'Each focus reproduction must issue exactly one rejected POST');
  }
  const version = await call('Browser.getVersion');
  const visual = review.finish(true, version.product);
  console.log(JSON.stringify({browser: version.product, node: process.version, sandbox_disable_flag: false,
    native_methods_units: newlineCount, native_emoji_units: emojiCount,
    extra_input_refused: true, field_limits: limits, multilingual_saved_revision: 1, saved_revision: 2,
    request_bytes: posts[0].bytes, browser_serialized_crlf: true, non_loopback_fetches_blocked: true,
    rendered_reflow: reflow, error_summary_keyboard_focus: true,
    error_summary_activations: 1 + extraRejectedDocuments,
    screen_reader_human_acceptance: 'unrun', actual_browser_zoom: 'unrun',
    screenshot_states: visual.states.length, contrast_failures: visual.failures.length,
    contrast_unmeasured: visual.unknown.length}));
  assert.equal(visual.unknown.length, 0, 'Unmeasured contrast requires review: ' + JSON.stringify(visual.unknown.slice(0, 10)));
  assert.equal(visual.failures.length, 0, 'Rendered contrast failures: ' + JSON.stringify(visual.failures.slice(0, 10)));
} catch (error) {
  probeFailed = true;
  console.error('[browser-contract] primary failure:', error);
  if (failureContext) {
    try { console.error('[browser-contract] synthetic focus context:', JSON.stringify(await failureContext())); }
    catch (contextError) { console.error('[browser-contract] context unavailable:', contextError.message); }
  }
  throw error;
} finally {
  if (review && !review.finished) review.finish(false);
  // Let Chrome close its child processes before removing the temporary profile.
  if (closeBrowser && browser.exitCode === null && browser.signalCode === null) {
    try { await closeBrowser(); } catch (error) {
      console.error('[browser-contract] graceful shutdown failed:', error.message);
    }
  }
  if (socket) socket.close();
  const waitForExit = async () => {
    if (browser.exitCode === null && browser.signalCode === null) {
      await Promise.race([new Promise(resolve => browser.once('exit', resolve)), delay(3000)]);
    }
  };
  await waitForExit();
  if (browser.exitCode === null && browser.signalCode === null) {
    browser.kill('SIGTERM');
    await waitForExit();
  }
  if (browser.exitCode === null && browser.signalCode === null) {
    browser.kill('SIGKILL');
    await waitForExit();
  }
  if (browser.exitCode !== null || browser.signalCode !== null) {
    try {
      fs.rmSync(profile, {recursive: true, force: true, maxRetries: 10, retryDelay: 100});
    } catch (error) {
      // Preserve the original assertion if a Chromium child is still releasing its profile.
      // The Python owner also kills the isolated process group before scratch cleanup.
      if (!probeFailed) throw error;
      console.error('[browser-contract] secondary profile cleanup failure:', error.code);
    }
  }
}
