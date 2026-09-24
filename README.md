# Maxim's Workbench

An [Obsidian](https://obsidian.md) theme with floating sidebars, callout-driven layouts, print-optimized page sizing, and a comprehensive design-token system.

> **Minimum Obsidian version:** 1.10

## Features

- **Floating sidebars** — Sidebars float above the main content with backdrop blur & shadows instead of resizing the workspace.
- **CSS class-driven page layouts** — Add `a4-page`, `a3-page`, or `wide` to a note's `cssclasses` frontmatter to control page width.
- **Rich callout system** — Callouts double as layout primitives: float (text-wrapping), multi-column grids, cards, timelines, absolute positioning, and blank invisible containers — all driven by callout metadata.
- **Print-ready PDF export** — Custom print zoom, A4/A3 page sizes, and optional ruler overlays for debugging page layouts.
- **Gradient heading underlines** — H1/H2 headings have gradient borders that fade into the background.
- **Style Settings support** — Print zoom and ruler overlays are configurable via Obsidian's [Style Settings](https://github.com/mgmeyers/obsidian-style-settings) plugin.

## Architecture

The theme is built from 62 modular CSS source files organized in a layered architecture, compiled into a single `theme.css` distributable. No file is an empty placeholder: every CSS file under `src/` is either imported by the build or explicitly parked (see the notes in the tree below).

```
src/
├── main.css                        # Entry point — 15 lines: the @settings header + imports
├── global/                         # Layer 1: Design tokens & framework
│   ├── design/
│   │   ├── color.css               # 10 overrides of Obsidian's light/dark palette
│   │   ├── setting.css             # 18 overrides of Obsidian's own custom properties
│   │   └── shadow.css              # Box-shadow presets
│   ├── classes/                    # Reusable UI widgets (menus, suggestions)
│   └── settings_layer.css          # Z-index stacking system
├── desktop/                        # Layer 2: Desktop UI theming
│   ├── app/                        # Application chrome (ribbon, inputs, workspace splits)
│   ├── component/                  # Shared components
│   │   └── callout/                #   One file per callout feature — main.css lists them in
│   │                               #   cascade order: card, timeline, absolute, blank, float,
│   │                               #   multiColumn, other, miscCallouts, kanban, hibox,
│   │                               #   infobox, icon, stickies, noIcon
│   ├── note/                       # Note content (text, media, page layout, print)
│   │   ├── text/                   #   Typography, headings, lists, links, embeds
│   │   │   └── block/table.css     #   PARKED: not imported (see note below)
│   │   ├── media/                  #   Images & video
│   │   ├── page/                   #   Page layout, A4/A3, print
│   │   ├── property.css            #   Frontmatter / YAML properties
│   │   └── title.css               #   Inline title
│   └── plugin/                     # Third-party plugin overrides
└── mobile/                         # Layer 3: reserved — the directory exists locally but holds
                                    #   no CSS and nothing imports it (an @import-glob over an
                                    #   empty directory is a build warning, so re-add the glob
                                    #   when the first mobile stylesheet lands)
```

> **`block/table.css` is parked, not missing.** `block/main.css` comments out its `@import`
> ("暂时删除表格样式以适配表格控件"), so the file ships no rules today. Re-enable the import only
> after re-checking it against the current table widget.

### Build pipeline

```
src/main.css
  → postcss-import-ext-glob   (resolves @import-glob wildcards)
  → postcss-import            (inlines all @import)
  → postcss-collect-settings  (aggregates @settings comments for Style Settings)
  → theme.css                 (single distributable file)
```

## Development

```bash
# Install dependencies
npm install

# Build theme.css
npm run build
```

The built `theme.css` is what Obsidian loads as the theme. Place it in your vault's `.obsidian/themes/` directory (or symlink it for development).

### Project conventions

- Source files live under `src/`, organized by layer: global tokens → desktop UI. There is no mobile layer yet.
- `@import-glob "path/**/*.css"` is used for directories where files are auto-discovered (design tokens, plugins). Explicit `@import` is used for structural entry points — `desktop/component/callout/main.css` lists its feature files in cascade order, so adding a file there means adding it in the right position, not at the end.
- Style rules cover both **source view** (CodeMirror 6 classes like `.cm-s-obsidian`, `.HyperMD-*`) and **reading view** (`.markdown-preview-view`, `.markdown-rendered`) for visual consistency.
- **Design tokens are overrides only.** `global/design/setting.css` and `color.css` may only define a custom property whose value differs from Obsidian's own default in `app.css` at the same selector context; byte-identical copies just freeze an old app version. `python3 tools/css-audit/check-tokens.py --strict` enforces this.
- **No `*.css.bak*` files under `src/`** — the glob would skip them, but they get read as source by tooling and agents. Git history is the backup.
- **Don't declare a selector dead by reading it.** Obsidian's CodeMirror 6 reuses many CodeMirror 5 class names (`.cm-tab`, `.cm-searching`, `.cm-fat-cursor`, `.cm-negative`, `.HyperMD-*` are all live). Only `.CodeMirror-*` and `.mod-cm5` are provably gone — verify any class name against the extracted `app.css` before deleting.

### Obtaining Obsidian's official CSS reference

When developing an Obsidian theme, you need Obsidian's base `app.css` as a reference to understand the default selectors, CSS custom properties, and DOM structure. Here are the ways to get it:

1. **Via Developer Tools** (recommended) — Open Obsidian, press `Cmd+Opt+I` (macOS) or `Ctrl+Shift+I` (Windows/Linux), go to the **Sources** tab, and find `app.css` under `app://obsidian.md/`. You can copy the full content from there.

2. **From the app bundle** — Obsidian packages its CSS inside `obsidian.asar` (not `app.asar`). Extract it with:
   ```bash
   npx @electron/asar extract /Applications/Obsidian.app/Contents/Resources/obsidian.asar /tmp/obsidian-extracted
   find /tmp/obsidian-extracted -name "app.css"
   ```

3. **Official documentation** — Obsidian's [Theme Design](https://docs.obsidian.md/Themes/App+themes/Theme+design) guide and [CSS Variables](https://docs.obsidian.md/Themes/App+themes/CSS+variables) reference list the supported custom properties.

To inspect specific UI elements (menus, modals, suggestions), use DevTools' element inspector to see the live DOM and copy HTML snippets — some of which are stored in `examples/` alongside the CSS.

## Print

- Add `a4-page` to `cssclasses` frontmatter for A4-compatible PDF export (714px content width).
- Add `a3-page` for A3 page sizing (72.8rem content width).
- Add `wide` for full-width notes.
- **Important:** Switch to reading view and scroll through the entire note before printing to ensure all content is rendered.

### Print rulers

Print media CSS includes optional ruler overlays for debugging page layouts:
- **Red** — paper edge
- **Green** — print area
- **Blue** — content area

### Debugging PDF CSS

Use [Better Export PDF](https://github.com/l1xnan/obsidian-better-export-pdf) to inspect and debug the print DOM in real time:

1. Open the Better Export PDF dialog (but **do not export** — just open the preview).
2. Open Obsidian DevTools (`Cmd+Opt+I`).
3. In DevTools, open **Rendering** panel (`Cmd+Shift+P` → type "Rendering" → select "Show Rendering"), then choose **Emulate CSS media type: print**.
4. In the **Elements** panel, find the `.print` element.
5. In the Styles panel, uncheck `display: none` (or toggle it off) to make the print DOM visible for inspection.

This gives you a live `.print` DOM tree to debug against, identical to what the plugin uses for actual PDF export.

## Style Settings

Print zoom level and ruler overlays can be toggled via Obsidian's [Style Settings](https://github.com/mgmeyers/obsidian-style-settings) plugin. Install it to adjust these print options from Obsidian's settings panel without editing CSS.

> **Note:** Only the print settings above are wired to Style Settings. The 28 remaining design tokens (`setting.css` + `color.css`) are plain overrides of Obsidian's defaults — to change colors, fonts or spacing today, override those variables in a custom CSS snippet.

## Auditing the codebase

`tools/css-audit/` holds the tools used to keep the tree honest. They are read-only unless a flag says otherwise:

```bash
# Is any src file re-declaring an Obsidian default? (mirrors must stay at 0)
python3 tools/css-audit/extract-app-css.py        # obsidian.asar -> /tmp/app.css (426 KB)
python3 tools/css-audit/check-tokens.py --strict  # exit 1 if a mirror exists

# Which declarations can never apply? (duplicate-in-block, -ms-/-moz-/-o- prefixes)
node tools/css-audit/dead-declarations.js src
node tools/css-audit/fix-dead-declarations.js src --write   # line-precise removal

# Structure report: rule/declaration counts, duplicate blocks, custom-property usage
node tools/css-audit/analyze.js

# Regression gate for a refactor: compares two BUILT stylesheets and reports
# every selector/declaration difference, so each one needs a reason
git show HEAD:theme.css > /tmp/old.css && npm run build
node tools/css-audit/verify-refactor.js /tmp/old.css theme.css
```

A refactor of this tree is only "done" when `verify-refactor.js` shows **0 added declarations** and every
removed declaration is attributable (mirrored token, dead vendor prefix, declaration overridden later in the
same block, or rule that was removed on purpose).

## Author & Version

See [manifest.json](manifest.json) for authorship and version information.
