import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import test from 'node:test';

import {waitForBrowserExit} from './browser_process.mjs';

test('profile cleanup can start only after the browser has exited', async () => {
  const child = spawn(process.execPath, ['-e', "console.log('ready'); setTimeout(() => process.exit(0), 100)"],
    {stdio: ['ignore', 'pipe', 'pipe']});
  try {
    await once(child.stdout, 'data');
    await waitForBrowserExit(child, 1000);
    assert.equal(child.exitCode, 0, 'Graceful browser exit must be observed before profile deletion');
    assert.equal(child.signalCode, null);
  } finally {
    if (child.exitCode === null && child.signalCode === null) child.kill('SIGKILL');
  }
});

test('an unresponsive browser is killed and reaped before profile cleanup', async () => {
  const child = spawn(process.execPath, ['-e', "console.log('ready'); setInterval(() => {}, 1000)"],
    {stdio: ['ignore', 'pipe', 'pipe']});
  try {
    await once(child.stdout, 'data');
    await waitForBrowserExit(child, 30);
    assert.equal(child.signalCode, 'SIGKILL', 'Sending a signal alone is insufficient; observe process exit');
  } finally {
    if (child.exitCode === null && child.signalCode === null) child.kill('SIGKILL');
  }
});

test('an already exited browser does not leave cleanup waiting for an old event', async () => {
  const child = spawn(process.execPath, ['-e', 'process.exit(0)']);
  await once(child, 'close');
  await waitForBrowserExit(child, 30);
  assert.equal(child.exitCode, 0);
});

test('parent exit does not permit cleanup while a descendant still holds browser stderr', async () => {
  const child = spawn(process.execPath, ['-e', `
    require('node:child_process').spawn(process.execPath,
      ['-e', 'setTimeout(() => process.exit(0), 200)'], {stdio: ['ignore', 'ignore', 2]});
    console.log('ready');
    setTimeout(() => process.exit(0), 20);
  `], {stdio: ['ignore', 'pipe', 'pipe']});
  await once(child.stdout, 'data');
  await once(child, 'exit');
  assert.equal(child.stderr.closed, false, 'The descendant must still own the inherited pipe');
  await waitForBrowserExit(child, 1000);
  assert.equal(child.stderr.closed, true, 'Wait for browser close, including inherited output handles');
});
