'use strict';
/**
 * Build integrity — the artifact must be exactly what `src/**` builds, and the
 * build must stay clean.
 *
 * Why this is a regression test and not a habit: `theme.css` is the single file
 * Obsidian loads, while `src/**` is the source of truth. Nothing in the repo
 * detects the two drifting apart (hand-edit to the artifact, or an `src/` edit
 * committed without a rebuild) — the app just silently renders the old build.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const crypto = require('crypto');

const { THEME, build, leadingSettingsBlock } = require('./lib/theme');

const md5 = (s) => crypto.createHash('md5').update(s).digest('hex');
const lines = (s) => s.split('\n').length;

test('theme.css is byte-identical to a fresh build of src/**', async () => {
  const { css } = await build();
  const committed = fs.readFileSync(THEME, 'utf8');
  assert.equal(
    md5(css),
    md5(committed),
    `theme.css is out of sync with src/** (built ${lines(css)} lines / ${Buffer.byteLength(css)} B, ` +
      `committed ${lines(committed)} lines / ${Buffer.byteLength(committed)} B). ` +
      'Run `npm run build` and commit the rebuilt artifact — never hand-edit theme.css.',
  );
});

test('the build emits no warnings', async () => {
  const { warnings } = await build();
  assert.deepEqual(
    warnings.map((w) => `${w.plugin || '?'}: ${w.text}`),
    [],
    'postcss warned during the build — a placeholder file went stale, an @import-glob matches no ' +
      'directory, or an @import points at a missing file. A warning-free build is the baseline.',
  );
});

test('the built stylesheet is parseable and carries the settings block first', async () => {
  const { css } = await build();
  const block = leadingSettingsBlock(css);
  assert.ok(block, 'theme.css must start with the hoisted /* @settings block — Style Settings reads it from there');
  assert.ok(/^\s*@settings/.test(block), `unexpected settings block shape: ${JSON.stringify(block.slice(0, 60))}`);
  assert.ok(
    /name:/.test(block) && /id:/.test(block),
    'the leading @settings block lost its `name:`/`id:` header (it comes from src/main.css)',
  );
});
