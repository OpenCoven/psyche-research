// Synthetic screenshot/contrast evidence only. Never pass serving state to this module.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

// WCAG 2.2 relative luminance, including alpha compositing in sRGB space.
export function contrastMath() {
  const color = value => {
    const match = /^rgba?\((.*)\)$/.exec(value);
    if (!match) throw new Error('Unsupported computed color');
    const parts = match[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    if (parts.length === 3) parts.push(1);
    if (parts.length !== 4 || parts.some(x => !Number.isFinite(x)) ||
        parts.slice(0, 3).some(x => x < 0 || x > 255) || parts[3] < 0 || parts[3] > 1) {
      throw new Error('Unsupported computed color');
    }
    return parts;
  };
  const blend = (foreground, background) => foreground.slice(0, 3)
    .map((channel, i) => channel * foreground[3] + background[i] * (1 - foreground[3])).concat(1);
  const luminance = value => value.slice(0, 3).map(channel => {
    const unit = channel / 255;
    return unit <= 0.04045 ? unit / 12.92 : ((unit + 0.055) / 1.055) ** 2.4;
  }).reduce((total, channel, i) => total + channel * [0.2126, 0.7152, 0.0722][i], 0);
  const ratio = (a, b) => {
    const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (values[0] + 0.05) / (values[1] + 0.05);
  };
  return {color, blend, ratio};
}

// Runs inside the actual renderer. Returns selectors/colors only, never text or values.
export function renderedContrast(math) {
  const checks = new Map();
  const unknown = [];
  let skippedHidden = 0;
  let skippedDisabled = 0;
  const selector = element => element.id ? '#' + element.id : element.tagName.toLowerCase() +
    [...element.classList].map(name => '.' + name).join('');
  const visible = element => {
    if (element.closest('[hidden], [aria-hidden="true"]')) return false;
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0 &&
      style.display !== 'none' && style.visibility === 'visible';
  };
  const background = element => {
    const ancestors = [];
    for (let current = element; current; current = current.parentElement) ancestors.unshift(current);
    return ancestors.reduce((result, current) => {
      const style = getComputedStyle(current);
      if (style.backgroundImage !== 'none' || Number(style.opacity) !== 1 ||
          style.filter !== 'none' || style.mixBlendMode !== 'normal') {
        throw new Error('Unmeasured image, opacity, filter or blend background');
      }
      return math.blend(math.color(style.backgroundColor), result);
    }, [255, 255, 255, 1]);
  };
  const add = (element, kind, foreground, backdrop, minimum) => {
    const ink = math.blend(math.color(foreground), backdrop);
    const ratio = math.ratio(ink, backdrop);
    const key = JSON.stringify({kind, foreground: ink, background: backdrop, minimum});
    let check = checks.get(key);
    if (!check) {
      check = {kind, foreground: ink, background: backdrop, minimum, ratio,
        pass: ratio >= minimum, elements: 0, selectors: []};
      checks.set(key, check);
    }
    check.elements++;
    const label = selector(element);
    if (check.selectors.length < 5 && !check.selectors.includes(label)) check.selectors.push(label);
  };
  const inspect = (element, kind, pseudo = null) => {
    if (!visible(element)) { skippedHidden++; return; }
    if (element.closest(':disabled')) { skippedDisabled++; return; }
    try {
      const style = getComputedStyle(element, pseudo);
      if (pseudo && Number(style.opacity) !== 1) throw new Error('Unmeasured pseudo opacity');
      const large = parseFloat(style.fontSize) >= 24 ||
        (parseFloat(style.fontSize) >= 56 / 3 && Number(style.fontWeight) >= 700);
      add(element, kind, style.color, background(element), large ? 3 : 4.5);
    } catch (error) { unknown.push({selector: selector(element), kind, reason: error.message}); }
  };
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node.textContent.trim() && !node.parentElement.closest('script, style, textarea, select')) {
      inspect(node.parentElement, 'text');
    }
  }
  for (const element of document.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]), textarea, select')) {
    inspect(element, 'control-text');
    if (element.getAttribute('placeholder') && !element.value) inspect(element, 'placeholder', '::placeholder');
    if (!visible(element) || element.matches(':disabled')) continue;
    try {
      const style = getComputedStyle(element);
      // Explicit CSS field boundaries, not native checkbox/radio appearance.
      if (parseFloat(style.borderTopWidth) > 0 && style.borderTopStyle !== 'none') {
        add(element, 'field-boundary-outside', style.borderTopColor, background(element.parentElement), 3);
        add(element, 'field-boundary-inside', style.borderTopColor, background(element), 3);
      }
    } catch (error) { unknown.push({selector: selector(element), kind: 'field-boundary', reason: error.message}); }
  }
  const active = document.activeElement;
  if (active !== document.body && visible(active)) {
    try {
      const style = getComputedStyle(active);
      if (style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0) {
        add(active, 'focus-outline', style.outlineColor, background(active.parentElement), 3);
      }
    } catch (error) { unknown.push({selector: selector(active), kind: 'focus-outline', reason: error.message}); }
  }
  return {checks: [...checks.values()], unknown, skippedHidden, skippedDisabled};
}

export class BrowserReview {
  constructor(directory, source, call, evaluate) {
    this.directory = directory;
    this.call = call;
    this.evaluate = evaluate;
    this.report = {synthetic_only: true, source, states: [], complete: false,
      browser_zoom: 'unrun', screen_reader_human_acceptance: 'unrun',
      native_checkbox_radio_and_all_other_ui_contrast: 'manual review required'};
    fs.mkdirSync(directory, {recursive: true, mode: 0o700});
    this.save();
  }
  save() {
    fs.writeFileSync(path.join(this.directory, 'report.json'), JSON.stringify(this.report, null, 2) + '\n');
  }
  async capture(name, width, phase, full) {
    assert.match(name, /^[a-z-]+$/);
    assert.ok([1440, 390, 320].includes(width));
    assert.ok(['page', 'skip', 'error'].includes(phase));
    const filename = `${name}-${width}-${phase}.png`;
    const parameters = {format: 'png', captureBeyondViewport: full};
    if (full) {
      const {cssContentSize: size} = await this.call('Page.getLayoutMetrics');
      assert.ok(size.height > 0 && size.height <= 20000, 'Screenshot height exceeds review bound');
      parameters.clip = {x: 0, y: 0, width, height: Math.ceil(size.height), scale: 1};
    }
    const screenshot = await this.call('Page.captureScreenshot', parameters);
    fs.writeFileSync(path.join(this.directory, filename), Buffer.from(screenshot.data, 'base64'));
    return filename;
  }
  async audit(name, width, phase, full = false) {
    const measurement = await this.evaluate(`(${renderedContrast.toString()})((${contrastMath.toString()})())`);
    const screenshot = await this.capture(name, width, phase, full);
    this.report.states.push({name, width, phase, screenshot, ...measurement});
    this.save();
  }
  finish(complete, browser = null) {
    this.report.complete = complete;
    this.report.browser = browser;
    this.report.failures = this.report.states.flatMap(state => state.checks.filter(check => !check.pass)
      .map(check => ({name: state.name, width: state.width, phase: state.phase, ...check})));
    this.report.unknown = this.report.states.flatMap(state => state.unknown
      .map(item => ({name: state.name, width: state.width, phase: state.phase, ...item})));
    this.save();
    const cards = this.report.states.map(state => `<article><h2>${state.name} · ${state.width}px · ${state.phase}</h2><a href="${state.screenshot}"><img src="${state.screenshot}" alt="Synthetic ${state.name} at ${state.width} pixels, ${state.phase} state"></a><p>Open the full image to inspect it.</p></article>`).join('\n');
    fs.writeFileSync(path.join(this.directory, 'index.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic browser review</title><style>body{font:16px/1.5 system-ui;margin:2rem;background:#f7f5ef;color:#262328}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}article{min-width:0;border:1px solid #665f6b;padding:1rem}h2{font-size:1rem}img{width:100%;max-height:600px;object-fit:contain;object-position:top;background:white}a{color:#59426f}</style><h1>SYNTHETIC browser review</h1><p>Test evidence only. These isolated fixtures are not published research or participant records. Source: ${this.report.source.sha}. Complete: ${complete}.</p><p>Human visual, screen-reader, browser zoom, device and operating acceptance remain unrun. Computed color checks have the bounded scope and limitations in report.json. No credentials, sessions or database are included.</p><section>${cards}</section></html>`);
    fs.writeFileSync(path.join(this.directory, 'README.md'), '# SYNTHETIC browser review\n\nOpen index.html locally to inspect the images, and report.json for source fingerprints and measured color pairs. Only synthetic loopback screenshots and non-secret measurement/source metadata are included. No fixture configuration, session cookie, database, raw server log or provider credential is exported.\n\nThis bundle is engineering evidence, not human accessibility acceptance or WCAG conformance. Native checkbox/radio appearance, other UI states, browser zoom, cross-browser/device behavior and assistive technology need separate review.\n');
    this.finished = true;
    return this.report;
  }
}
