'use strict';
/**
 * Release surface — the files the community directory and Obsidian's theme picker read.
 *
 * The store reads `manifest.json` at the HEAD of the default branch and installs the
 * release whose tag equals `manifest.version`, so a stale field or a wrong claim in the
 * README is a broken install for every user, not a cosmetic issue.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const { REPO, walkCss, readManifest } = require('./lib/theme');

const readme = () => fs.readFileSync(path.join(REPO, 'README.md'), 'utf8');

test('manifest.json carries what the directory requires', () => {
  const m = readManifest();
  for (const key of ['name', 'version', 'minAppVersion', 'author']) {
    assert.ok(typeof m[key] === 'string' && m[key].length, `manifest.json is missing \`${key}\``);
  }
  assert.match(m.version, /^\d+\.\d+\.\d+$/, 'manifest.version must be a bare semver — the release tag has to equal it');
  assert.match(m.minAppVersion, /^\d+\.\d+(\.\d+)?$/, 'manifest.minAppVersion must be a version number');
  if (m.authorUrl) assert.match(m.authorUrl, /^https:\/\//, 'authorUrl is rendered as a link in the listing');
});

test('README and manifest agree on the minimum Obsidian version', () => {
  const m = readManifest();
  const claimed = readme().match(/Minimum Obsidian version:\*{0,2}\s*v?([\d.]+)/i);
  assert.ok(claimed, "README no longer states a minimum Obsidian version — the store listing renders the README");
  assert.equal(claimed[1], m.minAppVersion, 'README and manifest.json disagree about minAppVersion');
});

test('the README\'s architecture claims still match the tree', () => {
  const text = readme();
  const files = walkCss(path.join(REPO, 'src')).map((f) => path.relative(REPO, f).split(path.sep).join('/'));

  const claimed = text.match(/built from (\d+) modular CSS source files/);
  assert.ok(claimed, 'README no longer states how many CSS source files the theme is built from');
  assert.equal(
    Number(claimed[1]),
    files.length,
    `README claims ${claimed[1]} CSS source files, src/** holds ${files.length} — update the architecture section`,
  );

  const tree = text.match(/```\nsrc\/\n([\s\S]*?)```/);
  assert.ok(tree, 'README lost the `src/` tree block');
  const mentioned = [
    ...new Set([...tree[1].matchAll(/([\w-]+\.css)/g)].map((m) => m[1])),
  ];
  const present = new Set(files.map((f) => path.basename(f)));
  const gone = mentioned.filter((f) => !present.has(f));
  assert.deepEqual(gone, [], 'the README tree names stylesheets that no longer exist under src/');
});

test('the release assets exist and are the right shape', () => {
  const license = path.join(REPO, 'LICENSE');
  assert.ok(fs.existsSync(license), 'a license file is required before the theme can be listed');

  const shot = path.join(REPO, 'screenshot.png');
  assert.ok(fs.existsSync(shot), 'the listing needs a 512x288 screenshot (capture it from VaultExample/)');
  const head = fs.readFileSync(shot).subarray(0, 33);
  assert.equal(head.subarray(1, 4).toString('ascii'), 'PNG', 'screenshot.png is not a PNG');
  const width = head.readUInt32BE(16);
  const height = head.readUInt32BE(20);
  assert.deepEqual([width, height], [512, 288], `the screenshot must be exactly 512x288, got ${width}x${height}`);
});
