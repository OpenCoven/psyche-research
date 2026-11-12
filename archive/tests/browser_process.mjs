// A parent exit alone is insufficient: descendants may still own inherited output handles.
export async function waitForBrowserExit(browser, timeoutMs = 5000) {
  const closed = () => (browser.exitCode !== null || browser.signalCode !== null)
    && browser.stdio.every(stream => stream === null || stream.closed);
  const wait = () => new Promise(resolve => {
    if (closed()) return resolve(true);
    const onClose = () => { clearTimeout(timer); resolve(true); };
    const timer = setTimeout(() => {
      browser.removeListener('close', onClose);
      resolve(closed());
    }, timeoutMs);
    browser.once('close', onClose);
  });
  if (await wait()) return;
  browser.kill('SIGKILL');
  if (!await wait()) throw new Error('Owned Chromium did not close; profile cleanup refused.');
}
