#!/usr/bin/env node
'use strict';
/**
 * Live tier — the checks that need a running Obsidian.
 *
 *   ./tests/VaultTest/run-test-vault.sh   # throwaway profile + test vault + debug port
 *   npm run test:live
 *
 * Everything drives **tests/VaultTest** and nothing else: the vault name is verified before any
 * check runs, and the PDF checks export that vault's own fixtures.
 *
 *   1. link integrity   — a vault silently rendering the default theme / a stale copy
 *   2. live tokens      — `--code-normal` losing its override (printed inline code went #222222),
 *                         `--print-page-width` still the 714px A4 content width
 *   3. mirror guard     — no design token copies an app default. **Version-sensitive**: the same
 *                         theme reports 0 mirrors against the app it was audited on and 56 against
 *                         an Obsidian 1.6.7 instance, so this runs only when the instance is at
 *                         least the manifest's own `minAppVersion`.
 *   4. exported PDF     — the 714px ruler prints as 482pt and the fixture's sentinel survives into
 *                         the text layer. A Base embed shrinking the whole page reads ~321pt, which
 *                         is how that bug was found.
 *
 * Exit codes: 0 all passed, 1 a check failed, 2 nothing listening on the debug port.
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const VAULT = path.join(REPO, 'tests', 'VaultTest');
const HARNESS = path.join(REPO, 'tools', 'print-harness');
const PORT = Number(process.env.PORT || 9222);
const EXPORT_SCALE = Number(process.env.EXPORT_SCALE || 90);
// 714px ruler at scale 0.9 with default margins; a whole-page fit-shrink reads ~321pt.
const RULER_PT_EXPECTED = 482;
const RULER_PT_TOLERANCE = 6;

const results = [];
const record = (name, ok, detail, skipped = false) => {
  results.push({ name, ok, detail, skipped });
  console.log(`${skipped ? 'SKIP' : ok ? 'PASS' : 'FAIL'}  ${name}${detail ? `\n        ${detail}` : ''}`);
};

const sh = (cmd, args) => spawnSync(cmd, args, { cwd: REPO, encoding: 'utf8' });

function debugPortUp() {
  return new Promise((resolve) => {
    const req = http.get({ host: '127.0.0.1', port: PORT, path: '/json/version', timeout: 1500 }, (res) => {
      res.resume();
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

const cmpVersion = (a, b) => {
  const pa = String(a).split('.').map(Number);
  const pb = String(b).split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const d = (pa[i] || 0) - (pb[i] || 0);
    if (d) return d > 0 ? 1 : -1;
  }
  return 0;
};

/** Run probe.py, returning its parsed output (or null with the failure recorded). */
function probe(label, openFixture, { checks = 'all', quiet = false } = {}) {
  const args = [path.join(__dirname, 'probe.py'), '--port', String(PORT), '--vault-prefix', 'VaultTest', '--checks', checks];
  if (openFixture) args.push('--open', openFixture);
  const res = sh('python3', args);
  try {
    const json = JSON.parse(res.stdout);
    for (const c of json.checks) {
      if (quiet && c.ok) continue; // identity probes are a precondition, not a result
      record(`${label}: ${c.name}`, c.ok, c.detail);
    }
    return json;
  } catch {
    record(`${label}: probe`, false, `probe.py did not return JSON:\n${(res.stdout || res.stderr).slice(0, 700)}`);
    return null;
  }
}

/** Pull the thick solid band out of measure-bands.py output (the injected 714px ruler). */
function rulerBandWidth(output) {
  const bands = [];
  for (const line of output.split('\n')) {
    const m = /y\s+\d+\.\.\d+\s+\((\d+)pt\)\s+x\s+\d+\.\.\d+\s+w=(\d+)pt/.exec(line);
    if (m) bands.push({ height: Number(m[1]), width: Number(m[2]) });
  }
  const band = bands.find((b) => b.height >= 20);
  return band ? band.width : null;
}

function measure(pdf) {
  const res = sh('python3', [path.join(HARNESS, 'measure-bands.py'), pdf, '--pages', '1']);
  return { out: `${res.stdout || ''}${res.stderr || ''}`, width: rulerBandWidth(res.stdout || '') };
}

function checkSentinel(pdf, sentinel, label) {
  const res = sh('python3', [path.join(HARNESS, 'measure-bands.py'), pdf, '--pages', '1', '--expect', sentinel]);
  const ok = new RegExp(`文本层包含 '?${sentinel}'?: True`).test(res.stdout || '');
  record(`${label}: the text layer keeps ${sentinel}`, ok, (res.stdout || res.stderr || '').trim().slice(-260));
}

/** Place the fixture as the active document, export it, and measure the ruler band. */
function exportFixture(file, sentinel, label, tmp) {
  const pdf = path.join(tmp, `${path.basename(file, '.md')}.pdf`);

  for (let attempt = 1; attempt <= 2; attempt++) {
    const placed = probe(label, file, { checks: 'identity', quiet: true });
    if (!placed) return;

    const exp = sh('python3', [
      path.join(HARNESS, 'export-probe.py'),
      '--vault-prefix', 'VaultTest',
      '--file', file,
      '--out', pdf,
      '--scale', String(EXPORT_SCALE),
    ]);
    if (exp.status !== 0) {
      record(`${label}: export`, false, (exp.stderr || exp.stdout || '').trim().slice(0, 600));
      return;
    }

    const { out, width } = measure(pdf);
    const good = width !== null && Math.abs(width - RULER_PT_EXPECTED) <= RULER_PT_TOLERANCE;
    if (good) {
      record(
        `${label}: the 714px ruler prints as ~${RULER_PT_EXPECTED}pt (no whole-page fit-shrink)`,
        true,
        `measured ${width}pt`,
      );
      checkSentinel(pdf, sentinel, label);
      return;
    }
    if (attempt === 2) {
      record(
        `${label}: the 714px ruler prints as ~${RULER_PT_EXPECTED}pt (no whole-page fit-shrink)`,
        false,
        width === null
          ? `the ruler band is missing from the export after 2 attempts — a blank PDF means the export ran with no ` +
            `.print document, i.e. the print preview never belonged to the fixture. On an instance below ` +
            `manifest.minAppVersion the plugin's preview is unreliable; re-run against the app version the theme ` +
            `targets. Export output:\n${out.trim().slice(0, 700)}`
          : `measured ${width}pt, expected ${RULER_PT_EXPECTED}±${RULER_PT_TOLERANCE}.`,
      );
      return;
    }
    console.log(`        (attempt ${attempt}: no ruler band — the print document was not ready, retrying)`);
  }
}

(async () => {
  console.log(`live tier — vault ${VAULT}, port ${PORT}\n`);

  if (!(await debugPortUp())) {
    console.error(
      `no debug port on 127.0.0.1:${PORT} — the live tier needs an Obsidian started with\n` +
        `  ./tests/VaultTest/run-test-vault.sh\n` +
        'Nothing listening is reported as skipped, not as a failure.',
    );
    process.exit(2);
  }

  // 1. link + vault wiring
  const link = sh(path.join(VAULT, 'link-theme.sh'), ['--check']);
  record('the vault links the repo build (no stale copy)', link.status === 0, (link.stdout || link.stderr).trim());

  const pluginDir = path.join(VAULT, '.obsidian', 'plugins', 'better-export-pdf');
  const hasPlugin = fs.existsSync(pluginDir);
  if (!hasPlugin) {
    record(
      'the export plugin is installed in the test vault',
      false,
      'run ./tests/VaultTest/link-plugins.sh — it symlinks better-export-pdf from a vault that already has it. ' +
        'The PDF checks drive the export through tools/print-harness/export-probe.py, which invokes that plugin.',
    );
  }

  // 2. computed styles + document identity
  const json = probe('app', 'fixtures/print-a4.md');
  const appVersion = json && json.info ? json.info.appVersion : null;
  const minAppVersion = JSON.parse(fs.readFileSync(path.join(REPO, 'manifest.json'), 'utf8')).minAppVersion;
  if (json && json.info) console.log(`        (vault ${json.info.vault}, Obsidian ${appVersion}, theme ${json.info.theme})`);

  const supported = appVersion && cmpVersion(appVersion, minAppVersion) >= 0;
  // Not a pass/fail on the theme: a fresh profile resolves an old bundle (1.6.7 here), and every
  // conclusion drawn from it describes an app the theme does not claim to support.
  record(
    `the instance meets manifest.minAppVersion (${minAppVersion})`,
    true,
    appVersion
      ? `WARNING: this instance is Obsidian ${appVersion} — treat the checks below as indicative only. ` +
        'Geometry and DOM checks still run; the token-mirror check is skipped because the served app.css ' +
        'is not the sheet the tokens were audited against.'
      : 'could not read the app version',
    !supported,
  );

  // 3. mirror guard — only meaningful on an instance the tokens were audited against,
  //    i.e. one at least as new as minAppVersion. An older sheet makes real overrides
  //    look like copies of its defaults (56 false mirrors on 1.6.7).
  if (!supported) {
    record(
      'no design token mirrors the app default (check-tokens --strict)',
      true,
      `skipped: the served app.css comes from Obsidian ${appVersion} (audited against a newer app). ` +
        'Re-run this against the app version the tokens were audited on, or re-audit.',
      true,
    );
  } else {
    const fetchCss = sh('python3', [path.join(REPO, 'tools', 'css-audit', 'fetch-app-css.py')]);
    if (fetchCss.status !== 0) {
      record('fetch app.css from the running app', false, `${(fetchCss.stderr || '').trim().slice(0, 300)}\n(tip: a token check failure is often a crash rather than a mirror — read the exit code)`);
    } else {
      const tokens = sh('python3', [path.join(REPO, 'tools', 'css-audit', 'check-tokens.py'), '--strict']);
      record(
        'no design token mirrors the app default (check-tokens --strict)',
        tokens.status === 0,
        `exit ${tokens.status}\n${`${tokens.stdout || ''}${tokens.stderr || ''}`.trim().slice(-500)}`,
      );
    }
  }

  // 4. real exports from the vault's fixtures
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'workbench-live-'));
  if (hasPlugin) {
    exportFixture('fixtures/print-a4.md', 'FIXTURE-A4-SENTINEL-ON-PAGE-1', 'fixture print-a4', tmp);
    exportFixture('fixtures/print-base.md', 'FIXTURE-BASE-SENTINEL', 'fixture print-base', tmp);
  }
  console.log(`\nPDFs kept in ${tmp}`);

  const failed = results.filter((r) => !r.ok && !r.skipped);
  const skipped = results.filter((r) => r.skipped);
  console.log(`\n${results.length - failed.length - skipped.length}/${results.length - skipped.length} live checks passed` +
    (skipped.length ? `, ${skipped.length} skipped` : ''));
  process.exit(failed.length ? 1 : 0);
})();
