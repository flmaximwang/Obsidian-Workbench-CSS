'use strict';
/**
 * The test vault (`tests/VaultTest`) must actually run the theme that is in the repo.
 *
 * This encodes the failure the theme docs keep warning about: a vault whose
 * `appearance.json` names a theme folder that does not exist, or that holds a **copy**
 * of the build instead of a symlink, renders the default theme while looking set up —
 * and every visual observation made against it describes the wrong CSS.
 *
 * Absent wiring is setup, not a regression: the test skips and tells you which script to
 * run. Wiring that exists but points somewhere else is a failure.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const { REPO, VAULT_TEST, THEME_NAME, rel, build } = require('./lib/theme');

const THEME_DIR = path.join(VAULT_TEST, '.obsidian', 'themes', THEME_NAME);
const FIXTURES = {
  'fixtures/print-a4.md': ['FIXTURE-A4-SENTINEL-ON-PAGE-1', 'a4-page'],
  'fixtures/print-base.md': ['FIXTURE-BASE-SENTINEL', '![[print-base.base]]'],
  'fixtures/print-base.base': ['views:'],
};
const wired = fs.existsSync(THEME_DIR);

test('the vault names the theme folder the repo actually installs', () => {
  const appearance = path.join(VAULT_TEST, '.obsidian', 'appearance.json');
  assert.ok(fs.existsSync(appearance), `${rel(appearance)} is missing — commit the vault config, it is the reproducibility`);
  const cfg = JSON.parse(fs.readFileSync(appearance, 'utf8'));
  assert.equal(
    cfg.cssTheme,
    THEME_NAME,
    `cssTheme must equal the linked folder name (${THEME_NAME}); a mismatch renders the default theme silently`,
  );
});

test('the theme install is a symlink to the repo, not a drifting copy', { skip: !wired && `run ./tests/VaultTest/link-theme.sh first` }, () => {
  for (const f of ['theme.css', 'manifest.json']) {
    const p = path.join(THEME_DIR, f);
    const st = fs.lstatSync(p);
    assert.ok(st.isSymbolicLink(), `${rel(p)} is a real file: a copy is a second source of truth — link it to ../../.. instead`);
    assert.equal(
      fs.realpathSync(p),
      path.join(REPO, f),
      `${rel(p)} resolves to ${fs.realpathSync(p)}, not the repo's own ${f}`,
    );
  }
});

test('the linked stylesheet is the build this test run produces', { skip: !wired && `run ./tests/VaultTest/link-theme.sh first` }, async () => {
  const { css } = await build();
  const linked = fs.readFileSync(path.join(THEME_DIR, 'theme.css'), 'utf8');
  assert.equal(linked, css, 'the vault loads a different stylesheet than src/** builds — re-link, then rebuild');
});

test('the print fixtures the live checks export are in place', () => {
  for (const [file, needles] of Object.entries(FIXTURES)) {
    const p = path.join(VAULT_TEST, file);
    assert.ok(fs.existsSync(p), `${rel(p)} is missing — the live print checks export it`);
    const text = fs.readFileSync(p, 'utf8');
    for (const needle of needles) {
      assert.ok(text.includes(needle), `${rel(p)} lost \`${needle}\` — the live check greps the PDF text layer for it`);
    }
  }
});

test('the vault carries no copies, and only the documented export plugin', () => {
  const plugins = JSON.parse(fs.readFileSync(path.join(VAULT_TEST, '.obsidian', 'community-plugins.json'), 'utf8'));
  const allowed = ['better-export-pdf'];
  assert.deepEqual(
    plugins.filter((id) => !allowed.includes(id)),
    [],
    `the test vault must stay plugin-minimal (allowed: ${allowed.join(', ')}). Add an entry to the allowlist in ` +
      'tests/vault.test.js only together with a note in tests/README.md explaining which check needs it.',
  );
  for (const id of plugins) {
    const dir = path.join(VAULT_TEST, '.obsidian', 'plugins', id);
    assert.ok(fs.existsSync(dir), `${id} is enabled but not installed at ${rel(dir)} (a plugin listed but absent is ignored in silence)`);
    for (const f of fs.readdirSync(dir)) {
      assert.ok(
        fs.lstatSync(path.join(dir, f)).isSymbolicLink(),
        `${rel(path.join(dir, f))} is a copy — plugin binaries must be symlinked from an existing vault so they ` +
          'cannot rot, and so nothing large lands in this repo',
      );
    }
  }

  const notes = fs
    .readdirSync(path.join(VAULT_TEST, 'fixtures'))
    .filter((f) => !f.startsWith('.') && !/\.(md|base)$/.test(f));
  assert.deepEqual(notes, [], `unexpected files in tests/VaultTest/fixtures: ${notes.join(', ')} — this vault holds synthetic fixtures only`);
});
