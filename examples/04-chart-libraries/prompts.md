# Prompts · 04 Chart libraries

## Demo prompt

**Where:** Claude, with `../_shared/snapshot.json` attached. **Time:** about
a minute per library. Run it twice live, once for a declarative library and
once for D3, and compare.

```text
Using the "channels" rows in this JSON, draw EMEA revenue by channel (web,
mobile, partner) for each quarter as a stacked bar chart with LIBRARY. One
HTML file, the library from a CDN, money on the axis, and a legend.
```

Replace `LIBRARY` with `Vega-Lite`, then `D3`.

**Expected:** both draw the same bars, with partner shrinking in the last
quarter. The Vega-Lite answer is a short spec. The D3 answer is several
times longer.

### Follow-up

```text
Now make it dark mode, and add a tooltip with the exact dollar amount.
```

**Point out:** the declarative version changes a few settings. The D3
version rewrites colors, axes, and event handlers.

**Fallback:** `index.html` in this folder.

## Per-library prompts

Each is the demo prompt with the library's name and what to ask for. Add
"with the design tokens in design-tokens.css" for the lab's look.

| Library | Ask for |
| --- | --- |
| Vega-Lite | "A Vega-Lite v5 spec rendered with vega-embed. Encode channel as color with a fixed order." |
| Apache ECharts | "An ECharts option with one bar series per channel, stacked, and an axis tooltip." |
| Recharts | "A React component using Recharts' BarChart with stacked Bars, without JSX, loaded from unpkg so it needs no build." |
| Plotly | "Plotly.newPlot with one bar trace per channel and barmode stack." |
| D3 | "D3 v7 with d3.stack, band and linear scales, axes, and a legend." |
| uPlot | "uPlot with weekly revenue from the 'weekly' rows, one line per channel, for EMEA." |

## Build prompt

**Where:** Claude Code in this repository. This reproduces `index.html`.

```text
Write examples/04-chart-libraries/index.html: one page that draws the same
chart in six libraries, so an audience can compare them.

The chart: EMEA revenue by channel (web, mobile, partner) for the last four
full quarters, stacked bars, from the "channels" rows of the snapshot
embedded in a <script id="lumen-snapshot" type="application/json"> block
(the same block make extract fills in the other examples). uPlot draws
weekly EMEA revenue per channel from the "weekly" rows instead.

Libraries, each from a pinned CDN version: Vega-Lite 5 with vega-embed,
Apache ECharts 5.6, Recharts 2 with React 18 UMD and no JSX, Plotly.js 2,
D3 7, and uPlot 1.6.

Each library gets a card with its name, its license, one sentence on why it
works or does not with AI, the chart, and a "Show code" disclosure. Write
each chart as one named function, display that function's source with
Function.prototype.toString so the code shown is the code that ran, and
show its line count in the card and in a summary table at the top.

Use the lab's design tokens (series colors, light and dark themes, a theme
toggle that redraws every chart). Format money in the axis. If a library
throws, show the error in its card instead of breaking the page.
```

**Expected:** six charts that agree, with D3 the longest.
