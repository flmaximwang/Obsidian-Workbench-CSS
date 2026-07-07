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

The theme is built from 59 modular CSS source files (4 are empty placeholders for future use) organized in a layered architecture, compiled into a single `theme.css` distributable.

```
src/
├── main.css                        # Entry point — imports everything
├── global/                         # Layer 1: Design tokens & framework
│   ├── design/
│   │   ├── color.css               # Light/dark color palettes
│   │   ├── setting.css             # 355 CSS custom property defaults
│   │   └── shadow.css              # Box-shadow presets
│   ├── classes/                    # Reusable UI widgets (menus, suggestions)
│   └── settings_layer.css          # Z-index stacking system
├── desktop/                        # Layer 2: Desktop UI theming
│   ├── app/                        # Application chrome (ribbon, inputs, workspace splits)
│   ├── component/                  # Shared components (callouts)
│   ├── note/                       # Note content (text, media, page layout, print)
│   │   ├── text/                   #   Typography, headings, lists, tables, links, embeds
│   │   ├── media/                  #   Images & video
│   │   ├── page/                   #   Page layout, A4/A3, print
│   │   ├── property.css            #   Frontmatter / YAML properties
│   │   └── title.css               #   Inline title
│   └── plugin/                     # Third-party plugin overrides
└── mobile/                         # Layer 3: Mobile-specific overrides (placeholder — empty)
```

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

- Source files live under `src/`, organized by layer: global tokens → desktop UI → mobile overrides (currently a placeholder).
- `@import-glob "path/**/*.css"` is used for directories where files are auto-discovered (design tokens, plugins). Explicit `@import` is used for structural entry points.
- Style rules cover both **source view** (CodeMirror 6 classes like `.cm-s-obsidian`, `.HyperMD-*`) and **reading view** (`.markdown-preview-view`, `.markdown-rendered`) for visual consistency.
- `archives/` contains deprecated CSS that has been refactored into the main tree. `examples/` holds reference files (Obsidian's `app.css`, HTML snippets) used during development.

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

## Style Settings

Print zoom level and ruler overlays can be toggled via Obsidian's [Style Settings](https://github.com/mgmeyers/obsidian-style-settings) plugin. Install it to adjust these print options from Obsidian's settings panel without editing CSS.

> **Note:** The 355 CSS custom properties in `src/global/design/setting.css` are not yet wired to Style Settings. To customize colors, fonts, or spacing today, override those variables in a custom CSS snippet.

## Author & Version

See [manifest.json](manifest.json) for authorship and version information.
