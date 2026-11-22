# Prompts · 02 Static HTML

## Demo prompt

**Where:** the same Claude chat as Demo 1, right after it. **Time:** about a
minute.

```text
Turn this dashboard into one self-contained HTML file I can open from my
laptop or put on GitHub Pages. Embed the data in the file, load the chart
library from a CDN, and keep every interaction. Add a footer that says when
the data was captured.
```

**Expected:** a single `.html` file, a few hundred lines, that looks and
behaves like the artifact. Download it and open it from disk.

### Follow-up: what did we give away?

```text
If I email this file to someone, what can they see? List every field and
how much data is embedded.
```

**Point out:** everything embedded is readable by anyone with the file. The
answer should say so plainly.

**Fallback:** `index.html` in this folder.

## Build prompt

**Where:** Claude, or Claude Code in this repository. Attach or point it at
`../_shared/context.md`, `../_shared/spec.md`, and
`../_shared/snapshot.json`. This reproduces `index.html`.

```text
Write one self-contained HTML file, examples/02-static-html/index.html, that
renders the Lumen Supply dashboard described in examples/_shared/spec.md,
without the live error-rate panel, since a static page cannot refresh.

Data: embed it in a <script id="lumen-snapshot" type="application/json">
block, filled from examples/_shared/snapshot.json, and read everything from
that block. The snapshot has kpis (current and previous quarter), monthly
(revenue and target by month and region), regions (last-quarter
attainment), channels (revenue by quarter, region, and channel), and
products (last-quarter units and revenue by region, channel, and product).
Do not compute revenue from anything else.

Styling: inline the design tokens from examples/_shared/design-tokens.css,
including the dark theme, and add a toggle that switches themes. Load Inter
from Google Fonts and Apache ECharts 5.6.0 from cdnjs. No other
dependencies and no build step.

Behavior: clicking a region bar filters the monthly chart, the channel
chart, and the products table to that region; clicking a channel in the
channel chart filters the products table; show active filters as removable
chips with a "Clear all" button. The products table has a search box and
keyboard-sortable headers. Charts redraw on resize and on theme change.

Show the period and the data's timestamp in the header, and a footer that
says revenue comes from the semantic layer and when the snapshot was taken.
Keep it under 300 lines.
```

**Expected:** a page like `index.html`: $5.64M revenue, 98.6% attainment,
and EMEA at 89.6%, drilling into a shrinking partner channel.
