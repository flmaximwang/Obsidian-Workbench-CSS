# tests — the regression suite

Two tiers. The **offline tier is the default** and needs nothing running; the **live tier**
drives a real Obsidian and is where PDF/print regressions are caught.

```shell
npm test                                    # offline tier — no Obsidian, ~2 s
./tests/VaultTest/link-theme.sh             # one-time: link the repo into the test vault
./tests/VaultTest/run-test-vault.sh         # throwaway Obsidian profile + debug port (does not touch your vaults)
npm run test:live                           # live tier — needs that debug-port instance
```

`run-test-vault.sh` opens a **separate profile** (`--user-data-dir=/tmp/obs-workbench-test`): the
single-instance lock is per profile, so a running Obsidian window, its vault list and its tabs are
untouched. Kill it with `pkill -f "user-data-dir=/tmp/obs-workbench-test"`.

## The test vault

`tests/VaultTest/` is the only vault any check may touch — real vaults are never used. Its config
JSONs are committed (that is its reproducibility); the theme install and plugin binaries are
symlinks and gitignored:

| Path | What |
|---|---|
| `.obsidian/appearance.json` | `cssTheme: Workbench` — must equal the linked folder name, or the app silently renders the default theme |
| `.obsidian/themes/Workbench/{theme.css,manifest.json}` | symlinks to the repo root, created by `link-theme.sh` |
| `.obsidian/plugins/better-export-pdf/` | symlink to an existing install, created by `link-plugins.sh`; binaries only, **no `data.json`** (otherwise the test vault would write into the source vault's plugin settings) |
| `fixtures/print-a4.md` | A4 page, inline code, callout, table, two sentinels — the geometry + text-layer fixture |
| `fixtures/print-base.md` + `.base` | the note that reproduces the whole-page fit-shrink (a Base embed) |
| `fixtures/` content | synthetic placeholder only, never real notes |

## Offline tier (`npm test`) — what each file guards

| File | Guards | Why it exists |
|---|---|---|
| `build.test.js` | `theme.css` is byte-identical to a fresh build of `src/**`; the build is warning-free; the built file starts with the hoisted `@settings` block | a hand-edited artifact, or an `src/` edit committed without a rebuild, renders stale CSS with no signal; a warning means a placeholder or glob went stale |
| `structure.test.js` | every `src/**/*.css` is reachable from `src/main.css` or explicitly parked; parked files stay un-imported; no `*.css.bak*` / empty files; no rule block emitted twice | an unimported stylesheet is a silent no-op; a double import only bloats the artifact |
| `settings.test.js` | the `@settings` header stays first in `src/main.css`; exactly one collected block; every `class-toggle` has a matching `.class` rule and every slider a `--var` definition | the whole Style Settings panel hangs off the hoist, and a renamed id is a toggle that does nothing |
| `print.test.js` | the Bases fit-shrink rules exist **outside** `@media print`; `--print-page-width` / 714px geometry; no `--file-line-width`; rulers stay print-scoped | each of these cost a real PDF regression (see `tools/print-harness/FINDINGS-base-fit-shrink.md`) |
| `audit.test.js` | `dead-declarations.js` reports the reviewed baseline and nothing new; `analyze.js` still runs | the toolset is now part of the test contract, and new dead declarations are debt |
| `release.test.js` | manifest fields + semver; README ↔ manifest `minAppVersion`; README's file count/tree still match `src/`; LICENSE; 512×288 `screenshot.png` | the store reads the README and the manifest at the default branch — drift is a broken listing |
| `vault.test.js` | the test vault names the linked folder, the install is a **symlink** (never a copy), the linked stylesheet equals the current build, fixtures present | "I already symlinked it" being false is the classic false-positive setup: you then observe the default theme and believe it |

## Live tier (`npm run test:live`)

| Step | Check |
|---|---|
| 1 | `link-theme.sh --check` — no stale copy in the vault |
| 2 | `tests/live/probe.py` — in the running app: the theme is `Workbench`; inline code has a **different** computed colour than body text (`--code-normal` losing its override dropped printed inline code from `#5a5a5a` to `#222222`); `--print-page-width` still resolves to the 714px A4 content width |
| 3 | `fetch-app-css.py` + `check-tokens.py --strict` — no design token mirrors an app default |
| 4 | `export-probe.py` + `measure-bands.py` on `fixtures/print-a4.md` — the injected 714px ruler prints as **482pt** (±6) and the page-1 sentinel survives into the text layer |
| 5 | same export on `fixtures/print-base.md` — the Base fixture must **not** shrink the page (a fit-shrink reads ~321pt) and must not clip the Base's columns |

Exit codes: `0` all passed, `1` a check failed, `2` nothing listening on the debug port (skipped, not
failed — the message says which script to run).

Notes that save time:

- The ruler is a **border** because `printBackground: false` means CSS backgrounds do not print.
- `measure-bands.py` output is parsed for the band whose height ≥ 20pt: that is the ruler, and its
  `w=NNNpt` is the scale witness. Anything else on the page is text.
- The PDF is kept next to `os.tmpdir()` and its path is printed, so a failure can be looked at.
- With no `.print` element in the DOM the export is blank; both scripts go through
  `export-probe.py`, which builds the print document first and then exports over Obsidian's own
  `print-to-pdf` IPC.
- **A measurement is only trustworthy after the document identity is proven.** `getLeaf(false).openFile()`
  can land on a leaf that never renders the file, and the export then prints a *different* note (or
  nothing) while still producing a PDF. Hence: `probe.py --open <fixture>` (new tab, poll
  `app.workspace.getActiveFile().path`, force reading mode, read `<code>` from **that leaf's own
  container** — several tabs hold a `.markdown-reading-view` and `document.querySelector` picks the
  first), a retry when the ruler band is missing, and a text-layer sentinel check per fixture.

### Measured on the throwaway profile (Obsidian 1.6.7, 2026-09-24)

Run end to end, so these numbers are observations rather than expectations:

| Check | Result |
|---|---|
| link integrity, theme identity, reading view | pass |
| inline code colour | `rgb(90, 90, 90)` vs body `rgb(34, 34, 34)` — the `--code-normal` override is live |
| A4 constant / `--print-page-width` | `714px`, `calc(714px / 100 * 100)` |
| `fixtures/print-base.md` export | ruler **482pt**, `FIXTURE-BASE-SENTINEL` in the text layer |
| `fixtures/print-a4.md` export | **blank PDF both attempts**, no `.print` document to measure |
| `check-tokens.py --strict` | **skipped** — see below |

Two findings worth knowing before trusting a green run:

1. **`check-tokens.py --strict` is app-version dependent.** The same theme reports 0 mirrors against
   the app it was audited on and **56 mirrors** against Obsidian 1.6.7's served `app.css`: tokens the
   theme deliberately pins look like copies of an older app's defaults. The live tier therefore runs
   that check only when the instance is at least `manifest.minAppVersion`, and prints the version of
   every run. A fresh throwaway profile resolves an **old** bundle (1.6.7 here) — below this theme's
   own minimum — so the token check is skipped and the other results are labelled *indicative only*.
   Run the live tier against the instance the theme targets for a verdict on the token guard.
2. **The blank `print-a4` export is an environment quirk of that old bundle, not (so far) the theme:**
   the same code path exported `print-base.md` twice at exactly 482pt. The check is written to refuse
   the measurement rather than report it — a blank PDF means the print preview never belonged to the
   fixture, so any number derived from it would be fiction.
