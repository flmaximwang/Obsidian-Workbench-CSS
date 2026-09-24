// Report declarations that can never apply, per source file:
//   1. the same property declared twice inside ONE rule block (the first one is dead)
//   2. legacy vendor prefixes that Chromium never supports (`-ms-`, `-moz-` outside @keyframes)
//   3. `var()` references whose name is not a valid custom-property name
// Usage: node tools/css-audit/dead-declarations.js [dir ...]   (default: src)
const fs = require('fs');
const path = require('path');
const postcss = require(path.join(__dirname, '..', '..', 'node_modules', 'postcss'));

const roots = process.argv.slice(2).length ? process.argv.slice(2) : ['src'];
const REPO = path.join(__dirname, '..', '..');

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.css')) out.push(p);
  }
  return out;
}

let dupCount = 0, prefixCount = 0, badVarCount = 0;
for (const dir of roots) {
  for (const file of walk(path.join(REPO, dir))) {
    const rel = path.relative(REPO, file);
    const root = postcss.parse(fs.readFileSync(file, 'utf8'), { from: file });
    root.walkRules(rule => {
      if (rule.parent.type === 'atrule' && /keyframes/.test(rule.parent.name)) return;
      const seen = new Map();
      rule.walkDecls(d => {
        // 1. same prop twice in one block
        if (seen.has(d.prop)) {
          const prev = seen.get(d.prop);
          if (prev.value.replace(/\s+/g, ' ') === d.value.replace(/\s+/g, ' ')) {
            console.log(`DUP-IDENTICAL  ${rel}:${prev.line} & ${d.line}  ${d.prop}`);
          } else {
            console.log(`DUP-OVERRIDE   ${rel}:${prev.line} (dead: ${prev.value.replace(/\s+/g, ' ').slice(0, 45)}) -> ${d.line} (wins: ${d.value.replace(/\s+/g, ' ').slice(0, 45)})  ${d.prop}`);
          }
          dupCount++;
        }
        seen.set(d.prop, { line: d.line, value: d.value });
        // 2. dead prefixes
        if (/^-(ms|moz)-/.test(d.prop)) {
          console.log(`DEAD-PREFIX    ${rel}:${d.line}  ${d.prop}: ${d.value.replace(/\s+/g, ' ').slice(0, 40)}`);
          prefixCount++;
        }
        // 3. invalid var() names (operators or spaces inside the name)
        for (const m of d.value.matchAll(/var\(\s*(--[^,)]*)/g)) {
          if (!/^--[\w-]+$/.test(m[1].trim())) {
            console.log(`BAD-VAR-NAME   ${rel}:${d.line}  var(${m[1].trim()})  in  ${d.prop}`);
            badVarCount++;
          }
        }
      });
    });
  }
}
console.log(`\ntotals: duplicate-in-block=${dupCount} dead-prefix=${prefixCount} invalid-var-name=${badVarCount}`);
