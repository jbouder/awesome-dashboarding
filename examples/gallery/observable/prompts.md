# Prompts · Observable Framework

## Demo prompt

**Where:** Claude Code in this repository, with `make example observable`
running. **Time:** about a minute, plus 30 seconds to rebuild.

```text
In examples/gallery/observable/app/src/index.md, add a short section after
the report called "Regions at a glance". Write one sentence per region
saying its attainment last quarter and whether it was on track, close, or
missed, using the existing kpis.regions data and the band() and pct()
helpers. Compute every number inline with ${...}. Do not add a chart.
```

Then rebuild with `make example observable` and reload
<http://localhost:3116>.

**Expected:** a new section of four sentences. EMEA reads 89.6% and
"missed", LATAM 93.3% and "close", APAC and North America "on track". The
diff is a few lines of Markdown.

### Follow-ups

```text
Add a sentence to the report naming the best-selling product last quarter
and its revenue, from products.json.
```

```text
Add a small line chart of EMEA partner revenue by quarter under the "Why"
paragraph, in the partner color #0f9d8a.
```

**Point out:** run `git diff`. The change is Markdown that anyone on the
team can read. The prose and the numbers sit side by side, so a reviewer
can check one against the other.

**Fallback:** `make example observable`, then open <http://localhost:3116>.

## Build prompt

**Where:** Claude Code in this repository. This reproduces `app/`.

```text
Build the Lumen Supply dashboard in Observable Framework, in
examples/gallery/observable/. Follow examples/_shared/spec.md for the
layout, behavior, and acceptance numbers. Read examples/_shared/context.md
for the data, metric definitions, formats, and design rules. Use the palette
in examples/_shared/design-tokens.css (copy it to app/src/tokens.css).

Data:
- Write Node data loaders in app/src/data/ (kpis.json.js, channels.json.js,
  products.json.js) with the pg package. They read WAREHOUSE_URL and query
  only the metrics views. Cast numeric and bigint columns so the JSON holds
  numbers. "Last full quarter" is date_trunc('quarter', now()) minus three
  months, up to date_trunc('quarter', now()).
- kpis.json: the period label ("Q3 2026"), the previous period, data as of
  (the latest ordered_at), last and previous quarter totals, attainment by
  region worst first, and revenue and target for the last 12 full months.
- channels.json: revenue by quarter, region, and channel, last four full
  quarters. products.json: units and revenue by region, channel, category,
  and product, last full quarter.

Page, app/src/index.md:
- Header "Lumen Supply", the period, and "Data as of".
- Signature section: a short written report in Markdown with every number
  inline, like "EMEA reached ${pct(worst.attainment)} of target". Say which
  region missed, by how much, and which of its channels fell the most, from
  what to what.
- KPI row of four cards. Attainment colored by band (below 92% danger
  #c2410c "Missed", below 98% warning #b45309 "Close", else success #15803d
  "On track").
- Observable Plot charts: revenue (solid) against target (dashed) by month;
  attainment by region as horizontal bars with a rule at 100%; revenue by
  channel by quarter as stacked bars (web #2563eb, mobile #f08c2e, partner
  #0f9d8a). Use the token CSS variables so dark mode works.
- Filters: Inputs.select pickers for region and channel are the source of
  truth. Clicking a region bar or a channel segment sets the picker through
  Plot's pointer (figure.value) and an input event. Region filters the
  channel chart and the table. Channel filters the table. Show the active
  filters and a "Clear filters" button.
- Top products: Inputs.search and a sortable Inputs.table, top 15 rows,
  money as $1,560,053. Show an empty state when nothing matches.
- Leave out the live error-rate panel and say why in a note at the bottom.

Site: app/observablehq.config.js with no sidebar and app/src/style.css that
imports observablehq:default.css, theme-air for light, theme-near-midnight
for dark, then tokens.css.

Container: package.json pinning @observablehq/framework and pg to exact
versions, with a lockfile. A node:22 slim Dockerfile running as the node
user, with OBSERVABLE_TELEMETRY_DISABLE=true. At image build, run one build
without the warehouse to fill Framework's npm cache. app/start.sh deletes
the cached loader output, runs observable build, then serves dist/ with a
dependency-free app/serve.js on port 3000.

compose.yaml: service ex-observable, profile ex-observable, image
dashlab-ex-observable:local, build ./app, WAREHOUSE_URL
postgresql://lab_ro:lab_ro@warehouse:5432/lab, port 127.0.0.1:3116:3000, no
depends_on, and a healthcheck that fetches http://localhost:3000/.

Check: the page contains "Lumen Supply", and the served data files show
$5.64M, 98.6%, EMEA at 89.6%, and EMEA partner revenue of about $94K in the
last full quarter. Then write README.md and prompts.md in the style of
examples/03-streamlit/.
```
