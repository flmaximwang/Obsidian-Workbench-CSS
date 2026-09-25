'use strict';
/**
 * Print invariants — the rules that were measured, not guessed.
 *
 * Each assertion below encodes a fact that cost a real PDF regression to learn
 * (see AGENTS.md "Bases views shrink the whole page" and
 * tools/print-harness/FINDINGS-base-fit-shrink.md). They are static on purpose:
 * a live PDF export is the strongest check (`npm run test:live`), but it needs a
 * running Obsidian, and these catch the break before anyone exports.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');

const { build, parse, rules, definedCustomProps } = require('./lib/theme');

const declsOf = (rule) => Object.fromEntries(rule.decls.map((d) => [d.prop, d.value]));

test('the Bases fit-shrink fix is present and NOT wrapped in @media print', async () => {
  const { css } = await build();
  const all = rules(parse(css));

  const cases = [
    { selector: '.print .bases-embed, .print .bases-view', required: { 'max-width': 'var(--print-page-width)', overflow: 'hidden' } },
    { selector: '.print .bases-table-container', required: { 'overflow-x': 'hidden' } },
    {
      selector: '.print .bases-td, .print .bases-table-header',
      required: { 'min-width': '0', 'white-space': 'normal', 'overflow-wrap': 'anywhere' },
    },
  ];

  for (const c of cases) {
    const rule = all.filter((r) => r.selector === c.selector);
    assert.equal(rule.length, 1, `expected exactly one \`${c.selector}\` rule in theme.css, found ${rule.length}`);
    assert.deepEqual(
      rule[0].atRules,
      [],
      `\`${c.selector}\` is now inside ${rule[0].atRules.join(' , ')}. The print fit-to-page decision is ` +
        'made in a non-print layout, so a version scoped to @media print measurably does not fix the ' +
        'whole-page shrink — keep these media-less and scoped to `.print`.',
    );
    const decls = declsOf(rule[0]);
    for (const [prop, value] of Object.entries(c.required)) {
      assert.equal(decls[prop], value, `\`${c.selector}\` lost \`${prop}: ${value}\``);
    }
  }
});

test('print geometry tokens are defined and consumed', async () => {
  const { css } = await build();
  const root = parse(css);
  const props = definedCustomProps(root);
  const all = rules(root);

  // 714px is the measured A4 content width at 96dpi with default margins; the
  // 714px ruler band printing as 482pt (scale 0.9) is the known-good geometry.
  assert.equal(props.get('--a4-page-print-width-original'), '714px', 'the A4 content width constant moved');
  assert.equal(
    props.get('--a4-page-print-width-zoomed'),
    'calc(var(--a4-page-print-width-original) / var(--print-zoom) * 100)',
    'the zoom formula changed — re-measure the ruler band before trusting it',
  );
  assert.equal(props.get('--print-page-width'), 'var(--a4-page-print-width-zoomed)');

  const printRule = all.find((r) => r.selector === '.print' && r.atRules.includes('@media print'));
  assert.ok(printRule, '.print has no width rule inside @media print — exported pages lose their page width');
  const d = declsOf(printRule);
  for (const prop of ['width', 'max-width', 'min-width']) {
    assert.equal(d[prop], 'var(--print-page-width)', `.print { ${prop} } no longer comes from --print-page-width`);
  }
});

test('the theme does not set --file-line-width / --document-width', async () => {
  const { css } = await build();
  const root = parse(css);
  const offenders = [];
  root.walkDecls((d) => {
    if (d.prop === '--file-line-width' || d.prop === '--document-width') {
      offenders.push(`${d.prop}: ${d.value} (${d.source.start.line})`);
    }
  });
  assert.deepEqual(
    offenders,
    [],
    'these were dropped because `--words-per-line` is defined nowhere, so the calc() was guaranteed-invalid ' +
      'and silently killed the app\'s own 700px default. Re-adding them needs a live measurement ' +
      '(tools/print-harness/ab-file-line-width.py), not a guess.',
  );
});

test('the print ruler overlays are scoped to @media print', async () => {
  const { css } = await build();
  const all = rules(parse(css));
  for (const cls of ['print-ruler-paper', 'print-ruler-print', 'print-ruler-content']) {
    const matching = all.filter((r) => new RegExp(`\\.${cls}(?![\\w-])`).test(r.selector));
    assert.ok(matching.length, `.${cls} is a Style Settings class-toggle with no rule`);
    for (const r of matching) {
      assert.ok(
        r.atRules.includes('@media print'),
        `.${cls} is applied outside @media print — the rulers are debugging overlays for the export only. ` +
          `Offending rule: \`${r.selector}\` (${r.atRules.join(' , ') || 'no at-rule'})`,
      );
    }
  }
});
