'use strict';
/**
 * The Style Settings contract.
 *
 * `postcss-collect-settings.js` hoists every `/* @settings *\/` block in `src/` to the
 * top of `theme.css`; the plugin then reads that block from the *built* file. Three
 * failure modes are invisible until a user opens the panel:
 *   1. `src/main.css` loses its (empty) `@settings` header → the hoist has nothing to
 *      append later blocks to, so every setting disappears;
 *   2. a setting id is renamed in CSS but not in the block (or vice versa) → a toggle
 *      that does nothing;
 *   3. two blocks declare the same id → the panel shows an entry that overwrites another.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');

const {
  SRC_ENTRY,
  rel,
  build,
  parse,
  readTheme,
  rulesWithClass,
  definedCustomProps,
  leadingSettingsBlock,
  parseSettings,
} = require('./lib/theme');

const SETTINGS_HEADER = '/* @settings\nname: Maxim\'s Workbench\nid: maxims-workbench\nsettings:\n*/';

test('src/main.css keeps its @settings header as the very first thing in the file', () => {
  const text = fs.readFileSync(SRC_ENTRY, 'utf8');
  assert.ok(
    text.replace(/^\uFEFF/, '').startsWith(SETTINGS_HEADER),
    `${rel(SRC_ENTRY)} must start with the exact @settings header — postcss-collect-settings hoists later ` +
      'blocks by appending them to this one, so moving or editing it breaks the whole Style Settings panel.\n' +
      `expected:\n${SETTINGS_HEADER}`,
  );
});

test('theme.css carries exactly one @settings block, at the top of the file', () => {
  const theme = readTheme();
  const block = leadingSettingsBlock(theme);
  assert.ok(block, 'theme.css does not start with a /* @settings block');
  const leftovers = theme.slice(theme.indexOf('*/', theme.indexOf('@settings'))).match(/@settings/g) || [];
  assert.deepEqual(
    leftovers.map((m) => m),
    [],
    'an @settings comment survived in the body of theme.css — the collect-settings plugin removes them all, ' +
      'so a surviving one means the hoist ran twice or a block was written outside the processed files',
  );
});

test('every @settings block in src/ lands in the built one', async () => {
  const { css } = await build();
  const built = parseSettings(leadingSettingsBlock(css));
  assert.equal(built.name, "Maxim's Workbench", 'the panel name comes from src/main.css');
  assert.equal(built.id, 'maxims-workbench');

  const srcIds = [];
  for (const file of [SRC_ENTRY, ...require('./lib/theme').walkCss(require('./lib/theme').SRC_DIR)]) {
    const text = fs.readFileSync(file, 'utf8');
    for (const m of text.matchAll(/\/\*\s*@settings([\s\S]*?)\*\//g)) {
      for (const s of parseSettings('@settings' + m[1]).settings) if (s.id) srcIds.push({ file: rel(file), id: s.id });
    }
  }
  const builtIds = built.settings.map((s) => s.id);
  for (const { file, id } of srcIds) {
    assert.ok(builtIds.includes(id), `setting \`${id}\` from ${file} never reached theme.css`);
  }
  assert.equal(builtIds.length, new Set(builtIds).size, `duplicate setting ids in the built block: ${builtIds}`);
});

test('every class-toggle and slider in the panel is backed by CSS', async () => {
  const { css } = await build();
  const root = parse(css);
  const block = parseSettings(leadingSettingsBlock(css));
  const props = definedCustomProps(root);
  const problems = [];

  for (const s of block.settings) {
    if (!s.id || !s.type) continue;
    if (s.type === 'class-toggle') {
      if (!rulesWithClass(root, s.id).length) {
        problems.push(`class-toggle \`${s.id}\` has no .${s.id} rule in theme.css — the toggle would do nothing`);
      }
    } else if (s.type === 'variable-number' || s.type === 'variable-number-slider') {
      const prop = `--${s.id}`;
      if (!props.has(prop)) problems.push(`slider \`${s.id}\` has no \`${prop}\` definition in theme.css`);
    }
  }
  assert.deepEqual(problems, [], 'a Style Settings entry exists but nothing in the built CSS reacts to it');
});
