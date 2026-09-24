# AGENTS.md

Maxim's Workbench is an Obsidian theme featured by floating sidebars and optimized print layout, which helps you to focus on the content.

## Docs

Official theme development guide: https://docs.obsidian.md/themes/app-themes/build-theme

## Codebase conventions

- `src/**` is the source of truth; `theme.css` is generated. Never judge a change without rebuilding and
  diffing the artifact (`tools/css-audit/verify-refactor.js` reports differences as selectors/declarations,
  not text lines).
- `src/main.css` must keep its `/* @settings ... */` header **first**: `postcss-collect-settings.js` hoists
  every later `@settings` comment by appending it to that block, so moving or removing it breaks the Style
  Settings panel. Keep the file's line count stable when possible — the trailing-newline shape of
  `src/main.css` is visible in `theme.css`.
- **Design tokens are overrides only.** `global/design/setting.css` / `color.css` may only define a property
  whose value differs from Obsidian's `app.css` default at the same selector context; `check-tokens.py
  --strict` must stay at 0 mirrors. Deleting a mirror is only safe when the app defines the same value itself.
- **Never classify a selector as dead by reading it.** Obsidian's CodeMirror 6 keeps many CodeMirror 5 class
  names (`.cm-tab`, `.cm-searching`, `.cm-fat-cursor`, `.cm-animate-fat-cursor`, `.cm-negative`,
  `.cm-positive`, `.cm-strikethrough`, `.cm-invalidchar`, `.cm-force-border`, `.cm-tab-wrap-hack`,
  `.HyperMD-*` are all live; verify against the extracted `app.css`). Only `.CodeMirror-*` and `.mod-cm5` are
  provably gone in Obsidian ≥ 1.x. The opposite also holds: a declaration overridden later in the *same*
  block is dead, but the same property in a *different* block is normal cascade.
- Vendored / upstream-copied blocks (callout kanban, stickies, banner switches, shadow presets) keep their
  upstream form; clean only what is provably inert, and never rewrite a value to "fix" a look. Unresolvable
  `var()` hooks (`--stickies-color-1`, `--p-kanban-*`, `--theme-color`, `--cmdr-spacing`) are **intentional
  override points** for snippets/plugins — leave them undefined.
- Keep `*.css.bak*` out of `src/`: the glob skips them, but tooling and agents read them as source.
- `tools/css-audit/` (analyze / dead-declarations / fix-dead-declarations / extract-app-css / check-tokens /
  verify-refactor) is the audit toolset; see README "Auditing the codebase".

## Workflows

### Test

- Create TempVault in the `tests`
- Create symlinks in `tests/VaultTemp/.obsidian/themes/Maxim's Workbench`

```shell
ln -s manifest.json "tests/TempVault/.obsidian/themes/Maxim's Workbench/manifest.json"
ln -s theme.css  "tests/TempVault/.obsidian/themes/Maxim's Workbench/theme.css"
```

### Build

```shell
npm run build     # postcss src/main.css -o theme.css
```

`src/**` is the source of truth; `theme.css` is the single release artifact (generated — never hand-edit it).
`postcss.config.js` chains `postcss-import-ext-glob` → `postcss-import` → `postcss-collect-settings.js`
(which hoists every `/* @settings */` block to the top of `theme.css` for Style Settings).

### Print / PDF

Print output comes from **two different pipelines** — but which one Better Export PDF uses depends on its
`data.json` `version`. Check that first:

| | Native (`Cmd+P`, command `workspace:export-pdf`) | Better Export PDF — `version: "2"` (current) | Better Export PDF — `version: "1"` |
|---|---|---|---|
| Render location | **Same document**: appends `document.body.createDiv("print")`, renders the note into `div.print`, then `detach()`s it after export | **Also the same document**: renders into `document.body`'s `.print` (+ a copy inside the dialog's `.print-preview-item`), then exports through Obsidian's own `ipcRenderer.send('print-to-pdf')` | **Separate document**: `<webview src="app://obsidian.md/help.html" class="print-preview-container">` holding a copy of the app `<head>` plus the `.print` subtree |
| Print CSS | real `@media print` | real `@media print` (same IPC → **page-for-page identical to the native export**) | the plugin replays every app `@media print` rule with the media wrapper stripped, through `insertCSS` (so those rules also apply under screen media) |
| App UI | `body > :not(.print) { display:none !important }` (from app.css) hides everything else | same | irrelevant (clean document) |

Consequences (verified against Obsidian 1.6.7 and plugin 2.0.3):

1. "Print HTML" differs from "app HTML" in **computed style, not markup** — the same `outerHTML` serializes
   byte-identically under screen and print media. Compare `getComputedStyle`, never text diffs.
2. **With no `.print` element present, the exported PDF is entirely blank** (every pixel alpha 0).
3. The native `.print` element is **short-lived** — it is detached right after export, so it can only be
   captured by freezing `detach()` first (`freeze-print.js`).
4. With `version: "2"` the plugin leaves **extra `.print` copies** in the body on every dialog open
   (screen-hidden, harmless) — clear them before inserting test markers, or you will measure nothing.
5. Export geometry cannot be judged from the dialog preview: the preview renders under **screen** media,
   so `@media print` widths don't apply and Chromium's fit-to-page doesn't run there.

#### Bases views shrink the whole page

A note containing `![[x.base]]` exports with **every** element scaled to ~2/3 (A4 page then looks 1.5× wider
than the content); notes without a Base are unaffected. Chromium's print fit-to-page fires on the Base's
viewport-tracking table width. Measured fix (in `src/desktop/note/page/print/main.css`):

```css
.print .bases-embed, .print .bases-view { max-width: var(--print-page-width); overflow: hidden; }
.print .bases-table-container { overflow-x: hidden; }
.print .bases-td, .print .bases-table-header { min-width: 0; white-space: normal; overflow-wrap: anywhere; }
```

**These rules must NOT be wrapped in `@media print`** — the fit decision is made in a non-print layout, and
media-scoped versions measurably failed to fix it (media-less versions worked). Keep them media-less and
scoped to `.print` so the reading view is unaffected. Evidence, variants and numbers:
`tools/print-harness/FINDINGS-base-fit-shrink.md`.

Rule of thumb when a PDF looks wrong: if the ruler you injected shrinks too, it's a **whole-page fit-shrink**
(look for oversized content — typically a Base); if only some elements are off, it's a theme width bug.

Tooling: `tools/print-harness/` — see its `README.md` for the full command reference and measured numbers.

```shell
cd tools/print-harness
./launch-obsidian-debug.sh      # Obsidian must be fully quit first: the debug port only applies at launch
                               # (add --remote-allow-origins=* if websocket-client hits a 403)
python3 cdp.py targets          # app://obsidian.md/index.html is the main window

# Fastest path when a PDF looks wrong (real export + 714px border ruler + pixel bands)
python3 export-probe.py --file Logs/2026/09/07/SEC-001/SEC-001.md --out /tmp/a.pdf
python3 measure-bands.py /tmp/a.pdf --pages 1 --expect "<text that must survive>"

# Open the export dialog (do NOT export): the print document then exists as its own target
python3 cdp.py --target webview dump    --out captures
python3 cdp.py --target webview sheets  --out captures/sheets
python3 cdp.py --target webview fixture --out tests/print-fixture   # pins a note for offline iteration
python3 cdp.py --target webview pdf     --out out.pdf --pagesize A4 --background
python3 cdp.py png out.pdf --dpi 110
```

Iterate on CSS live (`inject` / `setsheet` — no rebuild, no repo edit), read the effect back, and only then
write the change into `src/` and rebuild:

```shell
python3 cdp.py --target webview inject --css-text '@media print { .print { width: 500px !important } }'
python3 cdp.py --target webview styles --media print
python3 cdp.py --target webview setsheet --index 2 --css /tmp/candidate.css
```

Non-negotiable rules before concluding anything about `@media print`:

- Always pass `--media print` to `matched` / `styles` / `dump`. Without it, rules inside `@media print` do not
  match and you will wrongly conclude the selector is dead.
- `Emulation.setEmulatedMedia` is per-session — set media and read in the same connection (the `--media` flags
  already do this).
- Browser-injected stylesheets (`insertCSS` — i.e. Better Export PDF's own CSS) are **not** listed in
  `document.styleSheets`; recover them from `matched … --media print` entries with `origin=injected|user`.
- `printBackground` in `better-export-pdf/data.json` gates callout backgrounds; `scale` changes PDF geometry.
- The offline fixture reproduces the live print document exactly in cascade and layout, and the PDF text layer
  matches; pixels differ ~0.5% from glyph antialiasing only — use a tolerant pixel threshold (or compare a
  content region) for regression checks.
