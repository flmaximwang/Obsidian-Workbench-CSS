'use strict';
/**
 * Shared helpers for the regression suite.
 *
 * Run:  npm test        (== node --test tests/*.test.js)
 *
 * Everything here is deliberately offline and side-effect free: the build runs in
 * memory through the repo's own postcss config, so a test can never overwrite the
 * release artifact `theme.css`.
 */
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const postcss = require(path.join(REPO, 'node_modules', 'postcss'));
const fg = require(path.join(REPO, 'node_modules', 'fast-glob'));

const SRC_ENTRY = path.join(REPO, 'src', 'main.css');
const SRC_DIR = path.join(REPO, 'src');
const THEME = path.join(REPO, 'theme.css');
const VAULT_TEST = path.join(REPO, 'tests', 'VaultTest');
const THEME_NAME = 'Workbench';

const rel = (p) => path.relative(REPO, p).split(path.sep).join('/');

let _build = null;

/** Build `src/main.css` with the repo's real postcss pipeline, in memory. */
function build() {
  if (!_build) {
    _build = (async () => {
      const config = require(path.join(REPO, 'postcss.config.js'));
      const res = await postcss(config.plugins).process(fs.readFileSync(SRC_ENTRY, 'utf8'), {
        from: SRC_ENTRY,
      });
      return {
        css: res.css,
        warnings: res.warnings().map((w) => ({ plugin: w.plugin, text: w.text })),
        root: res.root,
      };
    })();
  }
  return _build;
}

function parse(css, from = THEME) {
  return postcss.parse(css, { from });
}

function readTheme() {
  return fs.readFileSync(THEME, 'utf8');
}

function readManifest() {
  return JSON.parse(fs.readFileSync(path.join(REPO, 'manifest.json'), 'utf8'));
}

/** Every `*.css` under a directory, sorted, as absolute paths. */
function walkCss(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walkCss(p, out);
    else if (e.name.endsWith('.css')) out.push(p);
  }
  return out;
}

/** All rules in a tree, with the at-rules wrapping them. */
function rules(root) {
  const out = [];
  root.walkRules((rule) => {
    if (rule.parent.type === 'atrule' && /keyframes/.test(rule.parent.name)) return;
    const atRules = [];
    for (let p = rule.parent; p && p.type !== 'root'; p = p.parent) {
      if (p.type === 'atrule') atRules.unshift(`@${p.name} ${p.params}`.trim());
    }
    out.push({
      selector: rule.selector.replace(/\s+/g, ' ').trim(),
      atRules,
      line: rule.source && rule.source.start ? rule.source.start.line : null,
      decls: rule.nodes
        .filter((n) => n.type === 'decl')
        .map((d) => ({ prop: d.prop, value: d.value.replace(/\s+/g, ' ').trim(), important: !!d.important })),
    });
  });
  return out;
}

/** Rules whose selector mentions a class name, at any nesting level. */
function rulesWithClass(root, className) {
  const needle = new RegExp(`\\.${className.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\w-])`);
  return rules(root).filter((r) => needle.test(r.selector));
}

/** Custom properties defined anywhere in a tree. */
function definedCustomProps(root) {
  const out = new Map();
  root.walkDecls((d) => {
    if (d.prop.startsWith('--')) out.set(d.prop, d.value.replace(/\s+/g, ' ').trim());
  });
  return out;
}

/**
 * The leading `/* @settings ... *\/` comment of a built stylesheet, or null.
 * Style Settings reads the built file, so this block must be first.
 */
function leadingSettingsBlock(css) {
  const trimmed = css.replace(/^\uFEFF/, '');
  if (!/^\s*\/\*\s*@settings/.test(trimmed)) return null;
  const end = trimmed.indexOf('*/');
  if (end === -1) return null;
  return trimmed.slice(trimmed.indexOf('/*') + 2, end);
}

/** Parse a collected `@settings` comment body into { name, id, settings: [...] }. */
function parseSettings(blockText) {
  const out = { name: null, id: null, settings: [] };
  let cur = null;
  const push = () => {
    if (cur && Object.keys(cur).length) out.settings.push(cur);
    cur = null;
  };
  for (const raw of blockText.replace(/^\s*@settings\s*/, '').split('\n')) {
    if (/^\s*-\s*$/.test(raw)) {
      push();
      cur = {};
      continue;
    }
    const m = /^(\s*)([A-Za-z][\w.-]*):\s*(.*?)\s*$/.exec(raw);
    if (!m) continue;
    const [, indent, key, val] = m;
    if (indent.length === 0) {
      push();
      if (key !== 'settings') out[key] = val; // `settings:` is the list opener, not a value
      continue;
    }
    if (cur) cur[key] = val;
  }
  push();
  return out;
}

/** The `@import` / `@import-glob` statements of one file, in order. */
function listImports(file) {
  const root = parse(fs.readFileSync(file, 'utf8'), file);
  const out = [];
  root.walkAtRules((a) => {
    if (a.name !== 'import' && a.name !== 'import-glob') return;
    const m = /^\s*(?:"([^"]+)"|'([^']+)'|([^\s'"]+))/.exec(a.params);
    if (!m) return;
    out.push({
      importer: rel(file),
      kind: a.name,
      spec: m[1] || m[2] || m[3],
      line: a.source && a.source.start ? a.source.start.line : null,
    });
  });
  return out;
}

function resolveImport(spec, fromFile) {
  const dir = path.dirname(fromFile);
  if (spec.includes('*')) {
    return fg.sync(spec, { cwd: dir, absolute: true, onlyFiles: true }).sort();
  }
  const p = path.resolve(dir, spec);
  return fs.existsSync(p) ? [p] : [];
}

/**
 * Transitive import graph of the entry stylesheet.
 * `seen` counts how many times each file is pulled in, `missing` holds
 * statements that resolve to nothing (the build warns about these).
 */
function importGraph(entry = SRC_ENTRY) {
  const seen = new Map();
  const edges = [];
  const missing = [];
  const walk = (file, depth) => {
    if (depth > 16) throw new Error(`import cycle or runaway depth at ${rel(file)}`);
    seen.set(file, (seen.get(file) || 0) + 1);
    for (const imp of listImports(file)) {
      const targets = resolveImport(imp.spec, file).filter((t) => t.endsWith('.css'));
      if (!targets.length) missing.push(imp);
      edges.push({ ...imp, targets: targets.map(rel) });
      targets.forEach((t) => walk(t, depth + 1));
    }
  };
  walk(entry, 0);
  return { seen, edges, missing };
}

/**
 * Source files that are intentionally NOT part of the build.
 * Adding an entry here is a deliberate act: the test below fails when a parked
 * file becomes reachable, so the README/AGENTS description has to be updated too.
 */
const PARKED_FILES = {
  'src/desktop/note/text/block/table.css': {
    reason: 'import commented out in block/main.css ("暂时删除表格样式以适配表格控件")',
    guaranteedBy: 'src/desktop/note/text/block/main.css',
  },
};

module.exports = {
  REPO,
  SRC_ENTRY,
  SRC_DIR,
  THEME,
  VAULT_TEST,
  THEME_NAME,
  PARKED_FILES,
  rel,
  build,
  parse,
  readTheme,
  readManifest,
  walkCss,
  rules,
  rulesWithClass,
  definedCustomProps,
  leadingSettingsBlock,
  parseSettings,
  listImports,
  resolveImport,
  importGraph,
};
