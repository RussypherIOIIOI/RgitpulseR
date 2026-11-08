# TMC design system

GitPulse uses the official brand system of **The Meredith Collective** (TMC). Tokens, fonts, marks, icons and patterns come from the TMC Design System (`tokens.json` v1, 2026-11-01) and its asset library. The site applies them; it does not define new brand values. IncidentLens uses the same system, so the portfolio reads as one family.

Source: [globals.css](../app/globals.css) (tokens and components), [brand.tsx](../app/_components/brand.tsx) (icons and marks), [site.tsx](../app/_components/site.tsx) (header, method band, footer), [page.tsx](../app/page.tsx) (hero and dashboard).

## Brand rules applied

- Flat color only: no gradients, glows or drop shadows. Layers separate with 1px `line` rules and `surface-raised`. The browser test fails if a chart, panel or primary action gains a gradient.
- Every border is 1px. Structural borders use `line`; state chips, the mode chip, the open maintainer control and data marks (the merge bar's Circuit cap, the dashed partial-week bar and the pulse's partial-week ring) draw their 1px border in their semantic color, so state reads without relying on fill alone.
- Dark (Void) is the default theme. The Method band switches to the Ivory canvas with `data-theme="light"`; the page opens on dark.
- Uppercase appears only in label, button and signal styles. Headings and body text use sentence case.
- Matrix Sans is reserved for readouts: metrics, ledger figures, timestamps, record numbers and the repository name in the hero. It is never used for paragraphs.
- Copy that describes the data follows the deployment: the method band's limits change with demo or live mode and with whether manual refresh is enabled, so a live or maintainer-enabled deployment never calls itself synthetic or read-only.
- Icons come only from the TMC outline set (24px grid, 1.5px stroke, `currentColor`). Each sits beside a text label and is hidden from assistive technology.
- The compact mark is used under 48px (header, favicon, Apple touch icon); the horizontal lockup appears in the footer. Marks are the canonical Design System files, never recolored, and carry ™, not ®.
- Patterns (orbits, dot matrix) appear only behind areas without text, at 100% scale and with no added color.

## Tokens

| Semantic token     | Dark value          | Light value          | Role                                   |
| ------------------ | ------------------- | -------------------- | -------------------------------------- |
| `surface`          | Void `#08070D`      | Ivory `#FAF9F5`      | Page and band ground, chart plot areas |
| `surface-raised`   | Void 2 `#13111C`    | Ivory 2 `#F1EEE5`    | Panels, KPIs, the hero pulse           |
| `surface-selected` | Void 3 `#221F2E`    | `#E6E2D7`            | Table row hover                        |
| `line`             | Rule dark `#2E2A3D` | Rule light `#D9D5C8` | Every border and rule                  |
| `ink`              | Ivory               | Slate `#141413`      | Primary text                           |
| `ink-muted`        | Mist `#B9B4C7`      | Stone `#5C5A55`      | Secondary text and labels              |
| `brand`            | Iris `#7F00FF`      | Iris                 | Merge bars, marks, partial-week ring   |
| `brand-text`       | `#C9A6FF`           | Iris                 | Links, emphasis, merged state          |
| `signal`           | Circuit `#76B900`   | Circuit              | Status dots, age bars, lit LED dots    |
| `signal-text`      | Circuit             | Olive `#5F6B32`      | Open state, status text                |
| `cta`              | Iris                | Slate                | Primary button fill                    |
| `focus`            | Circuit             | Iris                 | 2px keyboard focus outline             |

Two site-level choices sit on top of the brand tokens. `control-line` (= `ink-muted`) draws input and select boundaries, because `line` is under 3:1 against raised surfaces. `caution` (Manila `#E8DDBF`) marks failure and staleness notices; the printed title always carries the meaning.

## Typography

| Role    | Family            | Use                                                   |
| ------- | ----------------- | ----------------------------------------------------- |
| Display | Poppins 600       | Hero line, section, panel and card headings           |
| Body    | Lora 400/600      | Lead text, descriptions, table titles, notes          |
| Label   | Space Grotesk 400/500 | Eyebrows, chips, buttons, navigation, table headers |
| Signal  | Matrix Sans 400   | Metrics, ledger figures, timestamps, record numbers   |

All fonts are self-hosted WOFF2 files in [app/fonts](../app/fonts) loaded with `next/font/local`, with their SIL Open Font License texts copied into the container image. No font CDN is used.

## Layout

Header → hero (headline, actions, a ledger of snapshot figures, and the LED pulse) → dot-matrix strip → dashboard (repository strip, freshness, three KPIs, two charts, activity table) → Ivory method band → footer. The hero pulse draws one column per UTC week; lit dots scale to the busiest week, and the current partial week is ringed in Iris. Below 980px the hero stacks, below 900px the charts stack, below 760px the KPIs stack and the maintainer form opens rightward, and below 720px the header navigation hides (its links remain in the footer). Recovery states (no dataset, database unavailable, invalid filters) hide the in-page navigation because those anchors are not rendered.

## Motion

- The hero copy settles upward into place; the pulse lights its dots column by column and sweeps a 1px line across once.
- KPIs, panels and method cards lift into place as they scroll into view where `animation-timeline: view()` is supported. Elsewhere they render static.
- Data marks (merge bars, age bars) never animate, so a screenshot, print or slow frame never shows a wrong value.
- Animations change only `transform` and decorative fills. Text is never clipped, faded or recolored, so it paints immediately for readers, crawlers and screenshots. None loops except the loading indicator.
- `prefers-reduced-motion: reduce` disables every animation, transition and smooth scroll; the browser test checks this.

## Preserved contracts

Test IDs (`merge-median`, `open-count`, `activity-row`, `last-success`), the `Repository overview` heading, `Synthetic demo` mode label, filter labels, `Apply filters` / `Clear filters`, pagination text and the maintainer controls keep their names, so the existing browser flows still apply.

## Contrast

Calculated flat-color pairs (2026-11-07): Mist on Void 9.95:1 and on Void 2 9.26:1, `brand-text` on Void 2 9.23:1, Circuit on Void 2 7.74:1, Manila on Void 2 13.8:1, Ivory on Iris 5.96:1, Stone on Ivory 6.54:1 and on Ivory 2 5.94:1, Iris on Ivory 2 5.41:1, and Iris bars on Void 3.20:1 (non-text). The browser test recomputes rendered pairs: secondary text on the dark ground at 7:1, controls and the Ivory band at 4.5:1. Forced-colors mode redraws data marks in system colors. These checks do not establish full accessibility compliance; a screen-reader pass has not been run.
