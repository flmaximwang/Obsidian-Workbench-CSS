// Remove declarations that can never have any effect in any Obsidian runtime
// (desktop = Electron/Chromium, Android = Chromium WebView, iOS = WebKit):
//
//   1. `-ms-*` and `-moz-*` prefixed properties  — no Obsidian runtime is
//      Trident or Gecko, so these are dead everywhere the theme can load.
//   2. the LOSING half of a duplicate property inside one rule block — CSS keeps
//      the last declaration, so the earlier one is dead.
//
// Only declarations that occupy a whole line are removed, and the edit is done on
// the raw text (never re-stringified), so the diff stays line-precise.
//
//   node tools/css-audit/fix-dead-declarations.js src            # dry run
//   node tools/css-audit/fix-dead-declarations.js src --write    # apply
const fs = require('fs');
const path = require('path');
const postcss = require(path.join(__dirname, '..', '..', 'node_modules', 'postcss'));

const REPO = path.join(__dirname, '..', '..');
const write = process.argv.includes('--write');
const roots = process.argv.slice(2).filter(a => !a.startsWith('--'));
if (!roots.length) roots.push('src');

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.css')) out.push(p);
  }
  return out;
}

let removed = 0, skipped = 0;
for (const dir of roots) {
  for (const file of walk(path.join(REPO, dir))) {
    const rel = path.relative(REPO, file);
    const css = fs.readFileSync(file, 'utf8');
    const lines = css.split('\n');
    const drop = new Set();

    const root = postcss.parse(css, { from: file });
    root.walkRules(rule => {
      if (rule.parent.type === 'atrule' && /keyframes/.test(rule.parent.name)) return;
      const seen = new Map();
      rule.walkDecls(d => {
        // dead prefixed PROPERTY: no Obsidian runtime is Trident/Gecko/Presto.
        // (`-webkit-*` stays: Electron and WebKit both honour it.)
        const deadProp = /^-(ms|moz|o)-/.test(d.prop);
        // dead prefixed VALUE, e.g. `display: -ms-grid` (the standard value is
        // declared alongside it in every case found here).
        const deadVal = /^-(ms|moz|o)-/.test(String(d.value).trim().split(/[\s(]/)[0]);

        let reason = null;
        if (deadProp) reason = 'dead-prefix';
        else if (deadVal) reason = 'dead-value';

        // duplicate property inside one block: CSS keeps the LAST one, so every
        // earlier occurrence is dead. Mark the previous one, keep this one.
        if (!deadProp) {
          const prev = seen.get(d.prop);
          if (prev) mark(prev, 'dup-loser');
          seen.set(d.prop, d);
        }
        if (reason) mark(d, reason);

        function mark(node, why) {
          const ln = node.source.start.line;
          const text = lines[ln - 1];
          // only safe when the declaration owns its line
          if (node.source.start.line !== node.source.end.line || !text.trim().startsWith(node.prop + ':')) {
            console.log(`SKIP (not on its own line)  ${rel}:${ln}  ${node.prop}`);
            skipped++;
            return;
          }
          if (drop.has(ln)) return;
          drop.add(ln);
          console.log(`${why.padEnd(13)} ${rel}:${ln}  ${node.prop}: ${node.value.replace(/\s+/g, ' ').slice(0, 50)}`);
          removed++;
        }
      });
    });

    if (write && drop.size) {
      fs.writeFileSync(file, lines.filter((_, i) => !drop.has(i + 1)).join('\n'));
    }
  }
}
console.log(`\n${write ? 'removed' : 'would remove'}: ${removed}   skipped: ${skipped}`);
