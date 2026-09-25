'use strict';
/**
 * The audit toolset as a regression gate.
 *
 * `tools/css-audit/*` reads `src/**` and reports provably-dead declarations and mirrored
 * Obsidian defaults. Two of those findings are known and deliberate (documented in
 * AGENTS.md: the restored CodeMirror-5 block keeps its `-moz-animation` alias, and
 * `.cm-searching` keeps the overridden `#ffa` background). Everything else is new debt.
 *
 * The baseline below is a reviewed allowlist, not a "known failures" dump: it must
 * shrink when the underlying code is cleaned, and the test fails on any addition.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('child_process');
const path = require('path');

const { REPO } = require('./lib/theme');

const BASELINE = [
  // Restored CodeMirror-5 block in page/main.css: the `-moz-*` alias sits next to the
  // live `-webkit-`/unprefixed pair and was kept on purpose (see AGENTS.md).
  {
    kind: 'DEAD-PREFIX',
    file: 'src/desktop/note/page/main.css',
    prop: '-moz-animation',
    value: 'blink 1.06s steps(1) infinite',
    count: 2,
    why: 'CM5 block restored verbatim; -moz- is dead but deleting it is a separate decision',
  },
  // `.cm-searching` in the same block: the earlier `#ffa` is overridden by the theme's own rgba().
  {
    kind: 'DUP-OVERRIDE',
    file: 'src/desktop/note/page/main.css',
    prop: 'background-color',
    dead: '#ffa',
    wins: 'rgba(255, 255, 0, 0.4)',
    count: 1,
    why: 'kept verbatim while restoring the CM5 block; needs a live check before removing',
  },
];

const run = (args) => execFileSync('node', [path.join(REPO, 'tools', 'css-audit', 'dead-declarations.js'), ...args], {
  cwd: REPO,
  encoding: 'utf8',
});

const fingerprint = (f) =>
  [f.kind, f.file, f.prop, f.dead || f.value || f.badVar || '', f.wins || ''].join(' | ');

test('dead-declarations.js reports the reviewed baseline and nothing more', () => {
  const { findings } = JSON.parse(run(['src', '--json']));

  const actual = new Map();
  for (const f of findings) actual.set(fingerprint(f), (actual.get(fingerprint(f)) || 0) + 1);

  const expected = new Map();
  for (const b of BASELINE) expected.set(fingerprint(b), b.count);

  const added = [...actual.keys()].filter((k) => !expected.has(k));
  assert.deepEqual(
    added.map((k) => `${k}  (x${actual.get(k)})`),
    [],
    'new dead declaration(s): a property declared twice in one block, a -ms-/-moz- prefix, or a var() name ' +
      'with operators in it. Fix the source, or add a reviewed entry to BASELINE in tests/audit.test.js.',
  );

  const grown = [...expected.keys()].filter((k) => actual.get(k) > expected.get(k));
  assert.deepEqual(grown.map((k) => `${k}  (${expected.get(k)} -> ${actual.get(k)})`), [], 'baseline finding multiplied');

  // Findings that no longer occur are not a failure — the baseline is just stale.
  const stale = [...expected.keys()].filter((k) => !actual.has(k));
  if (stale.length) {
    test.diagnostic?.(`baseline entries that no longer occur: ${stale.join(' ; ')}`);
  }
});

test('the structural audit tool still runs against the current tree', () => {
  const out = execFileSync('node', [path.join(REPO, 'tools', 'css-audit', 'analyze.js')], { cwd: REPO, encoding: 'utf8' });
  assert.match(out, /theme\.css/, 'analyze.js no longer reports on theme.css — the toolset and the artifact drifted apart');
  const decls = out.match(/,\s*(\d+)\s+declarations/);
  assert.ok(decls && Number(decls[1]) > 1000, `analyze.js reported a suspiciously small declaration count:\n${out.slice(0, 400)}`);
});
