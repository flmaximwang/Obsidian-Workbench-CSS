// Structural analysis of the built theme.css — read-only reporting.
const fs = require('fs');
const path = require('path');
const postcss = require(path.join(__dirname, '..', 'node_modules', 'postcss'));

const repo = path.join(__dirname, '..');
const css = fs.readFileSync(path.join(repo, 'theme.css'), 'utf8');
const root = postcss.parse(css);

let rules = 0, decls = 0, atRules = {};
const sigMap = new Map();      // "selector|decls" -> [line]
const selProps = new Map();    // "media|selector|prop" -> [{value,line}]
const selectorLines = new Map(); // selector -> lines
root.walkRules(rule => {
  if (rule.parent.type === 'atrule' && rule.parent.name === 'keyframes') return;
  rules++;
  const media = [];
  let p = rule.parent;
  while (p && p.type !== 'root') { if (p.type === 'atrule') media.push('@' + p.name + ' ' + p.params); p = p.parent; }
  const mediaKey = media.reverse().join(' && ') || '(none)';
  const sel = rule.selector.replace(/\s+/g, ' ');
  if (!selectorLines.has(sel)) selectorLines.set(sel, []);
  selectorLines.get(sel).push(rule.source.start.line);
  const body = [];
  rule.walkDecls(d => {
    decls++;
    body.push(d.prop + ':' + d.value.replace(/\s+/g, ' '));
    const k = mediaKey + '|' + sel + '|' + d.prop;
    if (!selProps.has(k)) selProps.set(k, []);
    selProps.get(k).push({ value: d.value.replace(/\s+/g, ' '), line: rule.source.start.line, important: d.important });
  });
  const sig = sel + ' {' + body.join(';') + '}';
  if (!sigMap.has(sig)) sigMap.set(sig, []);
  sigMap.get(sig).push(rule.source.start.line);
});

root.walkAtRules(a => { atRules['@' + a.name] = (atRules['@' + a.name] || 0) + 1; });

console.log(`theme.css: ${rules} rules, ${decls} declarations`);
console.log('at-rules:', atRules);

// 1. exact duplicate rule blocks (same selector + same declarations)
const dupBlocks = [...sigMap.entries()].filter(([, l]) => l.length > 1);
console.log(`\n=== exact duplicate rule blocks (same selector+decls): ${dupBlocks.length} ===`);
dupBlocks.slice(0, 25).forEach(([sig, lines]) => console.log(`  lines ${lines.join(',')} :: ${sig.slice(0, 140)}`));

// 2. same selector declared N times (fragmentation) — top offenders
const fragmented = [...selectorLines.entries()].filter(([, l]) => l.length >= 4)
  .sort((a, b) => b[1].length - a[1].length);
console.log(`\n=== selectors declared >=4 times: ${fragmented.length} (top 15) ===`);
fragmented.slice(0, 15).forEach(([s, l]) => console.log(`  x${l.length}  ${s.slice(0, 110)}`));

// 3. same selector+prop declared more than once in the SAME media context (redundant / override in place)
const sameKey = [...selProps.entries()].filter(([, v]) => v.length > 1);
let overwrite = 0, identical = 0;
const identicalList = [], overwriteList = [];
sameKey.forEach(([k, v]) => {
  const vals = new Set(v.map(x => x.value));
  if (vals.size === 1) { identical++; identicalList.push([k, v]); }
  else { overwrite++; overwriteList.push([k, v]); }
});
console.log(`\n=== same selector+prop redeclared in same context: ${sameKey.length} (identical: ${identical}, conflicting: ${overwrite}) ===`);
console.log('--- identical (pure duplication) top 20 ---');
identicalList.slice(0, 20).forEach(([k, v]) => console.log(`  x${v.length}  ${k.split('|').slice(1).join(' | ').slice(0, 120)}`));
console.log('--- conflicting (might be accidental override) top 20 ---');
overwriteList.slice(0, 20).forEach(([k, v]) => console.log(`  ${k.split('|').slice(1).join(' | ').slice(0, 110)} -> ${v.map(x => x.value + '@' + x.line).join(' vs ')}`));

// 4. custom properties: defined vs used (across the built file)
const defined = new Map(), used = new Map();
root.walkDecls(d => {
  if (d.prop.startsWith('--')) {
    if (!defined.has(d.prop)) defined.set(d.prop, []);
    defined.get(d.prop).push(d.source.start.line);
  }
  const m = (d.value + ' ' + (d.prop.startsWith('--') ? '' : '')).match(/var\(\s*(--[\w-]+)/g) || [];
  m.forEach(x => {
    const name = x.replace(/var\(\s*/, '');
    if (!used.has(name)) used.set(name, []);
    used.get(name).push(d.source.start.line);
  });
  if (d.prop.startsWith('--')) {
    const m2 = d.value.match(/var\(\s*(--[\w-]+)/g) || [];
    m2.forEach(x => { const n = x.replace(/var\(\s*/, ''); if (!used.has(n)) used.set(n, []); used.get(n).push(d.source.start.line); });
  }
});
const obsidianOwn = /^--(color-|mono-|background-|text-|interactive-|font-|radius-|input-|shadow-|accent-|highlight-|titlebar-|tab-|divider-|collapse-|checkbox-|ribbon-|nav-|workspace-|modal-|prompt-|menu-|tooltip-|status-|scrollbar-|tag-|embed-|file-|icon-|link-|list-|h[1-6]-|p-|heading-|blockquote-|code-|callout-|table-|graph-|canvas-|is-|editor-|line-|cursor-|layer-|drag-|handle-|clickable-|slider-|toggle-|button-|dropdown-|flair-|zoom-|mobile-|sidebar-|vault-|direction-|caret-|toggle-|pro-)/;
const unused = [...defined.keys()].filter(k => !used.has(k) && !obsidianOwn.test(k));
console.log(`\n=== custom properties: defined ${defined.size}, referenced ${used.size} ===`);
console.log(`--- defined but never referenced (non-app, top 40): ${unused.length} ---`);
unused.slice(0, 40).forEach(k => console.log(`  ${k}  @${defined.get(k).join(',')}`));
const undef = [...used.keys()].filter(k => !defined.has(k) && !obsidianOwn.test(k));
console.log(`--- referenced but never defined anywhere in theme.css (non-app, top 40): ${undef.length} ---`);
undef.slice(0, 40).forEach(k => console.log(`  ${k}  x${used.get(k).length}`));

// 5. !important hotspots
const imp = [];
root.walkDecls(d => { if (d.important) imp.push(`${d.prop}${d.source.start.line}`); });
console.log(`\n=== !important declarations: ${imp.length} ===`);

// 6. specificity sanity: selectors that look malformed (":is(*," bug seen in A4.css)
console.log('\n=== suspicious selectors (:is(*, without nested parens closed / double space) ===');
const susp = [...selectorLines.keys()].filter(s => /:is\([^)]*,/.test(s) || /:is\([^()]*,\s*[\w#.]+\)/.test(s));
[...new Set(susp)].slice(0, 10).forEach(s => console.log('  ' + s.slice(0, 140)));
