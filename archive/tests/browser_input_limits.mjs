// Synthetic, loopback-only native input/encoding verification. No npm dependencies.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn, spawnSync} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';

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
  await call('Page.enable');
  await call('Network.enable', {maxPostDataSize: 1024 * 1024});
  await call('Fetch.enable', {patterns: [{urlPattern: 'http://*'}, {urlPattern: 'https://*'}]});
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
  const version = await call('Browser.getVersion');
  console.log(JSON.stringify({browser: version.product, node: process.version, sandbox_disable_flag: false,
    native_methods_units: newlineCount, native_emoji_units: emojiCount,
    extra_input_refused: true, field_limits: limits, saved_revision: 1,
    request_bytes: posts[0].bytes, browser_serialized_crlf: true, non_loopback_fetches_blocked: true}));
} finally {
  if (socket) socket.close();
  browser.kill('SIGTERM');
  await Promise.race([new Promise(resolve => browser.once('exit', resolve)), delay(3000)]);
  if (browser.exitCode === null && browser.signalCode === null) {
    browser.kill('SIGKILL');
    await Promise.race([new Promise(resolve => browser.once('exit', resolve)), delay(3000)]);
  }
  if (browser.exitCode !== null || browser.signalCode !== null) fs.rmSync(profile, {recursive: true, force: true});
}
