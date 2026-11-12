// Real Chromium, synthetic fixture only. Production ships no browser-side JavaScript.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn, spawnSync} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {waitForBrowserExit} from '../../archive/tests/browser_process.mjs';

const fixture = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const origin = new URL(fixture.origin);
assert.equal(origin.hostname, '127.0.0.1');
assert.ok(['flow', 'paused'].includes(fixture.phase));
const binary = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']
  .map(name => spawnSync('which', [name], {encoding: 'utf8'}).stdout.trim()).find(Boolean);
assert.ok(binary, 'An installed supported Chromium binary is required.');
const profile = fs.mkdtempSync(path.join(path.dirname(process.argv[2]), 'chromium-profile-'));
const browser = spawn(binary, ['--headless=new', '--disable-background-networking', '--disable-sync',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check', '--disable-component-update',
  '--no-proxy-server', '--disable-quic', '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',
  '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], {stdio: ['ignore', 'ignore', 'pipe']});
let socket;
let browserLog = '';
browser.stderr.on('data', bytes => { browserLog = (browserLog + bytes).slice(-8000); });
try {
  const activePort = path.join(profile, 'DevToolsActivePort');
  const readPort = () => fs.existsSync(activePort) ? Number(fs.readFileSync(activePort, 'utf8').split('\n')[0]) : 0;
  for (let attempt = 0; !readPort(); attempt++) {
    assert.ok(attempt < 100 && browser.exitCode === null && browser.signalCode === null, `Chromium startup failed: ${browserLog}`);
    await delay(100);
  }
  const debugPort = readPort();
  const version = (await (await fetch(`http://127.0.0.1:${debugPort}/json/version`)).json()).Browser;
  const target = await (await fetch(`http://127.0.0.1:${debugPort}/json/new?about:blank`, {method: 'PUT'})).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.addEventListener('open', resolve, {once: true}); socket.addEventListener('error', reject, {once: true}); });
  let sequence = 0;
  const pending = new Map();
  const external = [];
  const statuses = [];
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 15000);
    pending.set(id, {resolve, reject, timer}); socket.send(JSON.stringify({id, method, params}));
  });
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const request = pending.get(message.id); if (!request) return;
      pending.delete(message.id); clearTimeout(request.timer);
      if (message.error) request.reject(new Error(JSON.stringify(message.error))); else request.resolve(message.result);
    } else if (message.method === 'Network.requestWillBeSent') {
      const url = message.params.request.url;
      if (/^https?:/.test(url) && new URL(url).origin !== origin.origin) external.push(new URL(url).origin);
    } else if (message.method === 'Network.responseReceived' && message.params.type === 'Document') {
      statuses.push(message.params.response.status);
    }
  });
  const evaluate = async expression => {
    const result = await call('Runtime.evaluate', {expression, returnByValue: true, userGesture: true});
    assert.ok(!result.exceptionDetails, JSON.stringify(result.exceptionDetails)); return result.result.value;
  };
  const until = async (expression, label) => {
    for (let attempt = 0; attempt < 100; attempt++) {
      try { if (await evaluate(expression)) return; } catch { /* navigation can replace the execution context */ }
      await delay(100);
    }
    assert.fail(label);
  };
  let navigation = 0;
  const navigate = async (pathname = '/') => {
    const url = new URL(pathname, origin);
    url.searchParams.set('browser_probe', String(++navigation));
    await call('Page.navigate', {url: url.href});
    await until(`document.readyState === 'complete' && location.href === ${JSON.stringify(url.href)}`, 'Page did not load.');
  };
  const screenshot = async name => {
    const capture = await call('Page.captureScreenshot', {format: 'png'});
    fs.writeFileSync(path.join(fixture.review_directory, name + '.png'), Buffer.from(capture.data, 'base64'));
  };
  const key = async (key, code, virtual, text) => {
    await call('Input.dispatchKeyEvent', {type: 'keyDown', key, code, windowsVirtualKeyCode: virtual, ...(text ? {text} : {})});
    await call('Input.dispatchKeyEvent', {type: 'keyUp', key, code, windowsVirtualKeyCode: virtual});
  };
  const tab = () => key('Tab', 'Tab', 9);
  const enter = () => key('Enter', 'Enter', 13, '\r');
  const fill = async (email, name = 'Synthetic browser fixture') => {
    await evaluate(`document.getElementById('id_email').value=${JSON.stringify(email)}; document.getElementById('id_name').value=${JSON.stringify(name)}; document.getElementById('id_interest').value='reader'; document.getElementById('id_consent').checked=true; true`);
  };
  await call('Page.enable'); await call('Runtime.enable'); await call('Network.enable'); await call('Page.bringToFront');
  const layout = [];
  if (fixture.phase === 'flow') {
    for (const width of [1440, 390, 320]) {
      await call('Emulation.setDeviceMetricsOverride', {width, height: 900, deviceScaleFactor: 1, mobile: width < 500});
      await navigate();
      const measurement = await evaluate(`({width:innerWidth, scroll:document.documentElement.scrollWidth, controls:[...document.querySelectorAll('header, input:not([type=hidden]),select,button')].map(e=>({tag:e.tagName,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right}))})`);
      assert.equal(measurement.width, width);
      assert.ok(measurement.scroll <= width + 1, `Horizontal page overflow at ${width}: ${measurement.scroll}`);
      assert.ok(measurement.controls.every(e => e.left >= -1 && e.right <= width + 1), `Control overflow at ${width}`);
      layout.push(measurement);
      await screenshot(`home-${width}`);
      await evaluate("document.querySelector('.form-card').scrollIntoView(); true");
      await screenshot(`form-${width}`);
    }
    await navigate();
    await tab();
    assert.equal(await evaluate('document.activeElement.className'), 'skip');
    await enter();
    assert.equal(await evaluate('document.activeElement.id'), 'main');
    await evaluate("document.querySelector('button[type=submit]').click(); true");
    assert.equal(await evaluate('document.activeElement.id'), 'id_email');
    assert.equal(await evaluate('document.activeElement.validity.valueMissing'), true);
    // Exercise native keyboard input, select, checkbox, privacy link and submit traversal.
    await call('Input.insertText', {text: 'browser-check@example.invalid'});
    await tab(); await key('ArrowDown', 'ArrowDown', 40);
    await tab(); await call('Input.insertText', {text: 'Synthetic browser fixture'});
    await tab(); assert.equal(await evaluate('document.activeElement.id'), 'id_consent');
    await key(' ', 'Space', 32, ' '); await tab(); await tab();
    assert.equal(await evaluate('document.activeElement.tagName'), 'BUTTON');
    await enter();
    await until("location.pathname==='/confirmation/' && document.readyState==='complete'", 'Keyboard registration did not confirm.');
    const confirmation = await evaluate('document.body.innerText');
    assert.ok(!confirmation.includes('browser-check@example.invalid'));
    await screenshot('confirmation');
    await navigate(); await fill('BROWSER-CHECK@example.invalid', 'Must not overwrite');
    await evaluate("document.querySelector('button[type=submit]').click(); true");
    await until("location.pathname==='/confirmation/' && document.readyState==='complete'", 'Duplicate did not confirm.');
    assert.equal(await evaluate('document.body.innerText'), confirmation);
    await navigate(); await fill('error-check@example.invalid');
    await evaluate("const choice=new Option('Synthetic invalid','private-input@example.invalid'); const select=document.getElementById('id_interest'); select.add(choice); select.value=choice.value; document.querySelector('form').submit(); true");
    await until("document.readyState==='complete' && !!document.getElementById('errors')", 'Server validation summary missing.');
    assert.equal(await evaluate('document.activeElement.id'), 'errors');
    assert.equal(await evaluate("document.getElementById('id_email').value"), '');
    assert.ok(!await evaluate("document.body.innerText.includes('private-input@example.invalid') || document.body.innerText.includes('error-check@example.invalid')"));
    assert.ok(statuses.includes(400));
    await screenshot('validation-error');
  } else {
    await call('Emulation.setDeviceMetricsOverride', {width: 390, height: 900, deviceScaleFactor: 1, mobile: true});
    await navigate(); await fill('paused-check@example.invalid');
    await evaluate("document.querySelector('button[type=submit]').click(); true");
    await until("document.readyState==='complete' && document.body.innerText.includes('Registration is temporarily unavailable.')", 'Pause message missing.');
    assert.equal(await evaluate("document.getElementById('id_email').value"), '');
    assert.ok(statuses.includes(503));
    await screenshot('paused');
  }
  assert.deepEqual(external, [], 'No fixture browser request may leave loopback.');
  console.log(JSON.stringify({ok: true, browser: version, phase: fixture.phase, layout, document_statuses: statuses, external_requests: 0}));
  await call('Browser.close').catch(() => {});
} finally {
  socket?.close();
  await waitForBrowserExit(browser);
}
