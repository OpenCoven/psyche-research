import assert from 'node:assert/strict';
import test from 'node:test';
import {contrastMath} from './browser_review.mjs';

const math = contrastMath();
const white = [255, 255, 255, 1];
const black = [0, 0, 0, 1];

test('WCAG reference ratios and the 4.5 threshold are not rounded into a pass', () => {
  assert.equal(math.ratio(black, white), 21);
  assert.equal(math.ratio(white, white), 1);
  assert.ok(math.ratio([119, 119, 119, 1], white) < 4.5);
  assert.ok(math.ratio([118, 118, 118, 1], white) > 4.5);
});

test('transparent surfaces and foregrounds preserve the underlying sRGB color', () => {
  assert.deepEqual(math.blend(math.color('rgba(0, 0, 0, 0)'), white), white);
  assert.deepEqual(math.blend(math.color('rgba(0, 0, 0, 0.5)'), white), [127.5, 127.5, 127.5, 1]);
  assert.deepEqual(math.blend(math.color('rgb(255, 255, 255)'), black), white);
});

test('unsupported and invalid computed colors cannot silently become measurements', () => {
  for (const value of ['transparent', 'color(display-p3 1 0 0)', 'rgb(NaN, 0, 0)', 'rgba(0, 0, 0, 2)', 'rgb(256, 0, 0)']) {
    assert.throws(() => math.color(value), /Unsupported computed color/);
  }
});
