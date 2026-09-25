'use strict';
/**
 * Structural invariants of the source tree.
 *
 * The theme is assembled by `@import` / `@import-glob`; a stylesheet that nothing
 * imports is a silent no-op, and a file imported twice duplicates its rules in the
 * artifact. Neither shows up in a visual check.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const { REPO, SRC_DIR, SRC_ENTRY, PARKED_FILES, rel, build, walkCss, importGraph, parse } = require('./lib/theme');

test('every stylesheet under src/ is reachable from src/main.css, or explicitly parked', async () => {
  const { seen, missing } = importGraph(SRC_ENTRY);
  assert.deepEqual(
    missing.map((m) => `${m.importer}:${m.line} @import${m.kind === 'import-glob' ? '-glob' : ''} "${m.spec}"`),
    [],
    'these import statements resolve to nothing (the build warns about them too)',
  );

  const all = walkCss(SRC_DIR).map(rel);
  const reachable = new Set([...seen.keys()].map(rel));
  const parked = Object.keys(PARKED_FILES);

  const orphans = all.filter((f) => !reachable.has(f) && !parked.includes(f));
  assert.deepEqual(
    orphans,
    [],
    'these files are never imported — they ship no rules at all. Wire them into the build, or add ' +
      'them to PARKED_FILES in tests/lib/theme.js with the reason they stay out.',
  );

  const parkedButLive = parked.filter((f) => reachable.has(f));
  assert.deepEqual(
    parkedButLive,
    [],
    'a parked file is now reachable: remove it from PARKED_FILES and update the README/AGENTS note.',
  );

  const inSrc = all.filter((f) => !path.isAbsolute(f));
  assert.equal(
    new Set(inSrc.filter((f) => !parked.includes(f))).size,
    reachable.size,
    'the reachable set does not line up with the files on disk',
  );
});

test('a parked stylesheet keeps its import commented out', async () => {
  for (const [file, meta] of Object.entries(PARKED_FILES)) {
    const importer = path.join(REPO, meta.guaranteedBy);
    const text = fs.readFileSync(importer, 'utf8');
    const base = path.basename(file);
    assert.ok(
      new RegExp(String.raw`/\*\s*@import\s+"${base.replace('.', '\\.')}"\s*;?\s*\*/`).test(text),
      `${file} is listed as parked (${meta.reason}), but ${meta.guaranteedBy} no longer shows the ` +
        `commented-out import — either the file is live again (update PARKED_FILES + docs) or the ` +
        'note about why it is out was deleted.',
    );
  }
});

test('no backup or empty stylesheets under src/', async () => {
  const all = walkCss(SRC_DIR);
  const backups = all.filter((f) => /\.bak/.test(path.basename(f)));
  assert.deepEqual(backups.map(rel), [], 'git history is the backup — *.css.bak* under src/ gets read as source by tooling');

  const empty = all.filter((f) => fs.readFileSync(f, 'utf8').trim() === '');
  assert.deepEqual(empty.map(rel), [], 'empty stylesheets are build noise: -ext-glob warns once per file it matches');
});

test('no rule block is emitted twice into theme.css', async () => {
  const { css } = await build();
  const root = parse(css);
  const seen = new Map();
  const dups = [];
  root.walkRules((rule) => {
    if (rule.parent.type === 'atrule' && /keyframes/.test(rule.parent.name)) return;
    const atRules = [];
    for (let p = rule.parent; p && p.type !== 'root'; p = p.parent) {
      if (p.type === 'atrule') atRules.unshift(`@${p.name} ${p.params}`.trim());
    }
    const decls = [];
    rule.walkDecls((d) => decls.push(`${d.prop}:${d.value.replace(/\s+/g, ' ')}${d.important ? ' !important' : ''}`));
    const key = `${atRules.join(' && ')} || ${rule.selector.replace(/\s+/g, ' ')} || ${decls.join(';')}`;
    if (seen.has(key)) dups.push(`${rule.selector.replace(/\s+/g, ' ')} (lines ${seen.get(key)} and ${rule.source.start.line})`);
    else seen.set(key, rule.source.start.line);
  });
  assert.deepEqual(dups, [], 'a duplicated block means one stylesheet is imported twice — the extra copy only bloats theme.css');
});
