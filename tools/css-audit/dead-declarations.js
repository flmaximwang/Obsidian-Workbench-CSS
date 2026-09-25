// Report declarations that can never apply, per source file:
//   1. the same property declared twice inside ONE rule block (the earlier one is dead)
//   2. legacy vendor prefixes that no Obsidian runtime supports (`-ms-`, `-moz-`)
//   3. `var()` references whose name is not a valid custom-property name
//
// Usage:
//   node tools/css-audit/dead-declarations.js [dir ...]        (default: src)
//   node tools/css-audit/dead-declarations.js src --json        (for tooling / the test suite)
//
// Exit code is always 0: this is a report, not a gate. `tests/audit.test.js` holds the
// reviewed baseline of findings that are deliberate (documented in AGENTS.md) and fails
// when a NEW one appears.
const fs = require('fs');
const path = require('path');
const postcss = require(path.join(__dirname, '..', '..', 'node_modules', 'postcss'));

const argv = process.argv.slice(2);
const asJson = argv.includes('--json');
const roots = argv.filter((a) => !a.startsWith('--'));
if (!roots.length) roots.push('src');

const REPO = path.join(__dirname, '..', '..');
const findings = [];

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.css')) out.push(p);
  }
  return out;
}

const clean = (s) => String(s).replace(/\s+/g, ' ').trim();

for (const dir of roots) {
  for (const file of walk(path.join(REPO, dir))) {
    const rel = path.relative(REPO, file).split(path.sep).join('/');
    const root = postcss.parse(fs.readFileSync(file, 'utf8'), { from: file });
    root.walkRules((rule) => {
      if (rule.parent.type === 'atrule' && /keyframes/.test(rule.parent.name)) return;
      const seen = new Map();
      rule.walkDecls((d) => {
        const line = d.source && d.source.start ? d.source.start.line : null;

        // 1. same property twice inside one block
        if (seen.has(d.prop)) {
          const prev = seen.get(d.prop);
          const identical = clean(prev.value) === clean(d.value);
          findings.push({
            kind: identical ? 'DUP-IDENTICAL' : 'DUP-OVERRIDE',
            file: rel,
            line,
            prevLine: prev.line,
            prop: d.prop,
            dead: clean(prev.value),
            wins: clean(d.value),
            selector: clean(rule.selector),
            text: identical
              ? `DUP-IDENTICAL  ${rel}:${prev.line} & ${line}  ${d.prop}`
              : `DUP-OVERRIDE   ${rel}:${prev.line} (dead: ${clean(prev.value).slice(0, 45)}) -> ${line} (wins: ${clean(d.value).slice(0, 45)})  ${d.prop}`,
          });
        }
        seen.set(d.prop, { line, value: d.value });

        // 2. dead vendor prefixes
        if (/^-(ms|moz)-/.test(d.prop)) {
          findings.push({
            kind: 'DEAD-PREFIX',
            file: rel,
            line,
            prop: d.prop,
            value: clean(d.value),
            selector: clean(rule.selector),
            text: `DEAD-PREFIX    ${rel}:${line}  ${d.prop}: ${clean(d.value).slice(0, 40)}`,
          });
        }

        // 3. invalid var() names (operators or spaces inside the name)
        for (const m of d.value.matchAll(/var\(\s*(--[^,)]*)/g)) {
          if (!/^--[\w-]+$/.test(m[1].trim())) {
            findings.push({
              kind: 'BAD-VAR-NAME',
              file: rel,
              line,
              prop: d.prop,
              badVar: m[1].trim(),
              selector: clean(rule.selector),
              text: `BAD-VAR-NAME   ${rel}:${line}  var(${m[1].trim()})  in  ${d.prop}`,
            });
          }
        }
      });
    });
  }
}

const count = (kind) => findings.filter((f) => f.kind.startsWith(kind)).length;

if (asJson) {
  console.log(JSON.stringify({ roots, findings }, null, 2));
} else {
  for (const f of findings) console.log(f.text);
  console.log(
    `\ntotals: duplicate-in-block=${count('DUP')} dead-prefix=${count('DEAD-PREFIX')} invalid-var-name=${count('BAD-VAR-NAME')}`,
  );
}
