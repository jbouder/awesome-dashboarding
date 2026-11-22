# Observable Framework · Lumen Supply dashboard

**Framework:** [Observable Framework](https://github.com/observablehq/framework)
1.13.4, ISC license. **Needs:** the lab warehouse. `make example observable`
runs it at <http://localhost:3116>.

The Lumen Supply dashboard from [`../../_shared/spec.md`](../../_shared/spec.md),
built as a static site. The page opens with a short written report whose
numbers come from the data, then the KPI row, revenue against target by
month, attainment by region, revenue by channel, and the top products table.
Click a region bar to filter the channel chart and the table. Click a channel
segment to filter the table. The pickers and the "Clear filters" button do
the same.

## Files

| File | What it is |
| --- | --- |
| `prompts.md` | The demo prompt and the build prompt |
| `app/src/index.md` | The whole dashboard: Markdown prose, JavaScript cells, Plot charts, and Inputs |
| `app/src/data/*.json.js` | Data loaders. Each runs one or more queries on the `metrics` views at build time and prints JSON |
| `app/lib/warehouse.js` | The loaders' shared Postgres connection and the "last full quarter" bounds |
| `app/src/style.css`, `app/src/tokens.css` | Framework's air and near-midnight themes, with the lab's design tokens on top |
| `app/observablehq.config.js` | Site settings: title, no sidebar, the custom stylesheet |
| `app/start.sh`, `app/serve.js` | Build the site with fresh data, then serve `dist/` with a tiny Node server |
| `app/Dockerfile`, `compose.yaml` | How `make example observable` runs it |

## Signature section: the written report

The top of the page is prose, not a chart. Sentences like "EMEA reached
89.6% of target" are Markdown with inline expressions, `${pct(worst.attainment)}`,
so the words update with the data. The "why" sentence finds the channel that
fell the most in the worst region and quotes its before and after revenue.

Two things follow from that. The whole dashboard is one Markdown file, so a
change is a readable diff in Git and a reviewer can follow it. And Markdown
with a little JavaScript is a format AI writes well, so a prompt like "add a
paragraph on APAC" lands in a minute.

## What to point out

- **Static output.** `observable build` writes plain HTML, JavaScript, and
  JSON to `dist/`. Any static host can serve it: GitHub Pages, S3, a CDN.
  No app server, no database connection from the browser.
- **Build-time data.** Data loaders run SQL when the site builds and save
  the results as files. Here that happens at container start, so restart
  the container to refresh. The browser never sees a credential.
- **The data is a snapshot.** That is the cost. The spec's live error-rate
  panel, refreshed every five seconds, does not fit a static site, so it is
  left out. Grafana does that job in the lab.
- **Interactivity is client-side.** Filters run in the browser on the
  loaded JSON, so they are instant. The tradeoff is that every row the page
  might need ships to the browser. Here that is 123 kB.
- **Plot and Inputs come with Framework.** No chart library to choose or
  install. Click-to-filter is a few lines: a Plot pointer sets a picker's
  value and fires an input event.
- **The numbers match the other tools** because the loaders read the
  `metrics` views: $5.64M, 98.6%, EMEA at 89.6%, EMEA partner at $94K.

## Fallback

`make example observable`, then open <http://localhost:3116>. If the
warehouse is down, the container exits at build time. Run `make up grafana`
(or any stack) so the warehouse is up, then run it again.
