// Synthetic, loopback-only: click the real WorkOS sign-in button and report where the form-submitted navigation ends.
// Chromium maps api.workos.com and the synthetic AuthKit hosts to a local HTTPS mock and trusts only that mock's key.
// Every other hostname fails to resolve and proxies are disabled, so no browser request can reach a real service.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn, spawnSync} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';

assert.ok(Number(process.versions.node.split('.')[0]) >= 22, 'Node 22+ with native WebSocket is required.');
const fixture = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const origin = new URL(fixture.origin);
assert.equal(origin.hostname, '127.0.0.1');
assert.match(fixture.host_rules, /^(MAP [a-z0-9.-]+ 127\.0\.0\.1:\d+, )+MAP \* ~NOTFOUND, EXCLUDE 127\.0\.0\.1$/,
  'Only the mapped hosts may resolve, all to loopback; every other name must fail to resolve.');
const binary = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']
  .map(name => spawnSync('which', [name], {encoding: 'utf8'}).stdout.trim()).find(Boolean);
assert.ok(binary, 'A supported installed Chromium binary is required.');
const profile = fs.mkdtempSync(path.join(path.dirname(process.argv[2]), 'chromium-profile-'));
const browser = spawn(binary, ['--headless=new', '--disable-background-networking', '--disable-sync',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check', '--disable-features=HttpsUpgrades',
  '--no-proxy-server', '--disable-component-update', '--disable-quic',
  `--host-resolver-rules=${fixture.host_rules}`, `--ignore-certificate-errors-spki-list=${fixture.spki}`,
  '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], {stdio: ['ignore', 'ignore', 'pipe']});
let browserLog = '';
browser.stderr.on('data', bytes => { browserLog = (browserLog + bytes).slice(-16000); });
let socket;
try {
  // The port file can exist before its first line is written; wait for a usable port.
  const activePort = path.join(profile, 'DevToolsActivePort');
  const readPort = () => fs.existsSync(activePort) ? Number(fs.readFileSync(activePort, 'utf8').split('\n')[0]) : 0;
  for (let attempt = 0; !(readPort() > 0); attempt++) {
    assert.ok(attempt < 150 && browser.exitCode === null && browser.signalCode === null,
      `Chromium startup failed: ${browserLog}`);
    await delay(100);
  }
  const port = readPort();
  const version = (await (await fetch(`http://127.0.0.1:${port}/json/version`)).json()).Browser;
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {method: 'PUT'})).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, {once: true});
    socket.addEventListener('error', reject, {once: true});
  });
  let sequence = 0;
  const pending = new Map();
  const messages = [];
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
    } else if (message.method === 'Log.entryAdded') {
      messages.push(message.params.entry.text);
    }
  });
  const evaluate = async expression =>
    (await call('Runtime.evaluate', {expression, returnByValue: true})).result.value;
  const location = () => evaluate('location.origin + location.pathname');
  await call('Page.enable');
  await call('Log.enable');
  await call('Runtime.enable');
  await call('Page.navigate', {url: new URL('/accounts/login/', origin).href});
  for (let attempt = 0; ; attempt++) {
    assert.ok(attempt < 100, 'sign-in page did not load');
    if (await evaluate("document.readyState === 'complete' && !!document.querySelector('form.stack-form button')")) break;
    await delay(100);
  }
  await evaluate("document.querySelector('form.stack-form button[type=submit]').click(); true");
  // Wait for the chain to settle: either the page leaves the app or a refusal is logged and the page stays.
  let final;
  for (let attempt = 0; attempt < 50; attempt++) {
    await delay(200);
    try { final = await location(); } catch { continue; }
    if (!final.startsWith(origin.origin) || messages.some(text => /form-action/.test(text))) break;
  }
  await delay(1000);
  final = await location();
  const title = await evaluate('document.title');
  // Report only query-free locations and CSP refusal text with ports and query strings removed.
  const csp_refusals = messages.filter(text => /Content Security Policy/.test(text))
    .map(text => text.replace(/\?[^'"\s]*/g, '?<query>').replace(/127\.0\.0\.1:\d+/g, '127.0.0.1:<port>'));
  console.log(JSON.stringify({browser: version, final, title, csp_refusals}));
  await call('Browser.close').catch(() => {});
} finally {
  socket?.close();
  if (browser.exitCode === null) browser.kill('SIGKILL');
  fs.rmSync(profile, {recursive: true, force: true, maxRetries: 5, retryDelay: 200});
}
