// Regression gate for a "provably neutral" CSS refactor.
//
// Compares two built stylesheets and reports every difference in terms of
// selectors and declarations (not text lines) so each change can be attributed
// to a reason:
//
//   A  removed selector            — must be a selector that can never match
//   B  removed declaration         — must be dead (overridden / prefixed / invalid)
//   C  added selector/declaration  — suspicious: a refactor must not add rules
//
// Usage:
//   node tools/css-audit/verify-refactor.js <old.css> <new.css> [--allow <regex>]
// `--allow <regex>` whitelists a removed declaration (repeatable), e.g. the
// 434 mirrored custom properties: --allow '^--'.
const fs = require('fs');
const path = require('path');
const postcss = require(path.join(__dirname, '..', '..', 'node_modules', 'postcss'));

const argv = process.argv.slice(2);
const allow = [];
for (let i = 0; i < argv.length; i++) if (argv[i] === '--allow') allow.push(new RegExp(argv[++i]));
const [oldFile, newFile] = argv.filter(a => !a.startsWith('--') && !allow.some(r => r.source.includes(a)));
if (!oldFile || !newFile) { console.error('usage: verify-refactor.js <old.css> <new.css> [--allow <regex>]...'); process.exit(2); }

function index(file) {
  const root = postcss.parse(fs.readFileSync(file, 'utf8'), { from: file });
  const out = new Map(); // "media|selector" -> [declaration strings]
  root.walkRules(rule => {
    if (rule.parent.type === 'atrule' && /keyframes/.test(rule.parent.name)) return;
    const media = [];
    let p = rule.parent;
    while (p && p.type !== 'root') { if (p.type === 'atrule') media.push('@' + p.name + ' ' + p.params.trim()); p = p.parent; }
    const key = (media.reverse().join(' && ') || '-') + '|' + rule.selector.replace(/\s+/g, ' ').trim();
    const decls = [];
    rule.walkDecls(d => decls.push(d.prop + ': ' + d.value.replace(/\s+/g, ' ').trim() + (d.important ? ' !important' : '')));
    if (!out.has(key)) out.set(key, []);
    out.get(key).push(...decls);
  });
  return out;
}

const A = index(oldFile), B = index(newFile);
const counts = { removedSelector: 0, removedDecl: 0, addedSelector: 0, addedDecl: 0, allowed: 0 };

for (const [key, decls] of A) {
  if (!B.has(key)) { console.log(`A REMOVED-SELECTOR  ${decls.length} decl(s)  ${key.slice(0, 150)}`); counts.removedSelector++; continue; }
  const nb = B.get(key);
  const nbc = new Map();
  nb.forEach(d => nbc.set(d, (nbc.get(d) || 0) + 1));
  const ac = new Map();
  decls.forEach(d => ac.set(d, (ac.get(d) || 0) + 1));
  for (const [d, n] of ac) {
    const have = nbc.get(d) || 0;
    if (have < n) {
      const lost = n - have;
      const ok = allow.some(r => r.test(d));
      for (let i = 0; i < lost; i++) {
        if (ok) { counts.allowed++; continue; }
        console.log(`B REMOVED-DECL      ${key.slice(0, 110)}  ||  ${d.slice(0, 80)}`);
        counts.removedDecl++;
      }
    }
  }
}
for (const [key, decls] of B) {
  if (!A.has(key)) { console.log(`C ADDED-SELECTOR    ${decls.length} decl(s)  ${key.slice(0, 150)}`); counts.addedSelector++; continue; }
  const na = A.get(key);
  const nac = new Map();
  na.forEach(d => nac.set(d, (nac.get(d) || 0) + 1));
  const bc = new Map();
  decls.forEach(d => bc.set(d, (bc.get(d) || 0) + 1));
  for (const [d, n] of bc) {
    const have = nac.get(d) || 0;
    for (let i = 0; i < n - have; i++) {
      if (i + have >= n) break;
      if (allow.some(r => r.test(d))) { counts.allowed++; continue; }
      console.log(`C ADDED-DECL        ${key.slice(0, 110)}  ||  ${d.slice(0, 80)}`);
      counts.addedDecl++;
    }
  }
}

console.log(`\nremoved selectors=${counts.removedSelector}  removed decls=${counts.removedDecl}  ` +
            `added selectors=${counts.addedSelector}  added decls=${counts.addedDecl}  whitelisted=${counts.allowed}`);
process.exit(counts.addedSelector || counts.addedDecl ? 1 : 0);
