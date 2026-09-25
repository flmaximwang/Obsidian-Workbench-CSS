---
cssclasses:
  - a4-page
tags:
  - workbench-fixture
---

# Print fixture — A4 page

Synthetic placeholder only: this note exists so `npm run test:live` can export a PDF from
`tests/VaultTest` without touching a real vault.

FIXTURE-A4-SENTINEL-ON-PAGE-1

Inline code such as `--print-page-width` resolves through `--code-normal`; if that token stops
resolving, the printed colour of inline code silently falls back to the body text colour. The live
probe compares the two computed colours.

> [!note] Callout on page 1
> Callout backgrounds only print when the export enables background graphics
> (`printBackground` in the plugin's `data.json`).

| item | expectation |
|:-----|:------------|
| page width | 714px content area at print zoom 100 |
| ruler band | a 714px border renders as 482pt at scale 0.9 |
| text layer | both sentinels survive into the PDF |

A paragraph of filler so the page break is not ambiguous. Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Vivamus lacinia odio vitae vestibulum vestibulum. Cras venenatis euismod malesuada.
Suspendisse potenti. Phasellus volutpat neque in augue ullamcorper, eget tristique velit aliquam.

Maecenas sed diam eget risus varius blandit sit amet non magna. Donec ullamcorper nulla non metus
auctor fringilla. Nullam quis risus eget urna mollis ornare vel eu leo. Cum sociis natoque penatibus
et magnis dis parturient montes, nascetur ridiculus mus.

## Second block

FIXTURE-A4-SENTINEL-ON-PAGE-2

More filler to guarantee a second page: Cras mattis consectetur purus sit amet fermentum. Donec id
elit non mi porta gravida at eget metus. Nullam id dolor id nibh ultricies vehicula ut id elit.
Aenean lacinia bibendum nulla sed consectetur. Donec sed odio dui. Vivamus sagittis lacus vel augue
laoreet rutrum faucibus dolor auctor.
