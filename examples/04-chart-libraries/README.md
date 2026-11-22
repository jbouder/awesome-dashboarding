# 04 · One chart, six libraries

**Supports:** Part 1, "Pick libraries models can write reliably". **Needs:**
a browser. `make example static` serves it at
<http://localhost:3102/04-chart-libraries/>, and GitHub Pages publishes it:
<https://jbouder.github.io/dashboarding-lab/04-chart-libraries/>.

The same chart, EMEA revenue by channel for the last four full quarters, in
each library on the slide: Vega-Lite, Apache ECharts, Recharts (what shadcn
charts wrap), Plotly, D3, and uPlot. uPlot draws weekly revenue instead,
since it is built for time series. Each panel has **Show code**, which shows
the exact function that drew it, and its line count.

## Files

| File | What it is |
| --- | --- |
| `prompts.md` | A demo prompt per library, and the build prompt for the page |
| `index.html` | The comparison page. Data embedded, refreshed by `make extract` |

## What to point out

- **Declarative wins for AI.** Vega-Lite and ECharts are a spec: short,
  checkable, hard to break. A model gets them right on the first try.
- **D3 is the longest,** and every axis, legend, and tooltip is hand-built.
  Generated D3 grows quickly and breaks in subtle ways.
- **Recharts fits a design system.** It is React components, so it inherits
  your theme. That matters when a dashboard should look like your product.
- **Plotly is one call,** in Python or JavaScript, at the cost of a large
  bundle.
- **uPlot is for speed,** not variety. Use it for long time series.
- **Same data, six looks.** The numbers agree. The defaults do not.

Line counts are for the code as written here. Formatting changes them, so
compare the shape, not the exact number.
