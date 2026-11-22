# Prompts · Dash

## Demo prompt

**Where:** Claude Code in this repository, with `make example dash`
running. **Time:** one to two minutes, plus a rebuild.

```text
In examples/gallery/dash/app.py, add a segment level to the drill-through
signature section. After a channel is clicked, and before the modal opens,
show revenue by segment (Consumer, SMB, Enterprise) for that region and
channel, last full quarter against the quarter before. Clicking a segment
opens the modal, filtered to that segment. Use metrics.daily_revenue, which
has a segment column, and add the query to data.py. Keep the drill store
and the pattern-matching breadcrumbs working. Then rebuild and restart it with:
make example dash
```

**Expected:** EMEA, then partner, then a segment chart. The breadcrumbs
gain a third step, and the modal title names the segment.

### Follow-ups

```text
Add a "Download CSV" button to the modal that downloads the largest
orders table, using dcc.Download.
```

```text
Make the region and channel filters part of the URL, so a filtered view
can be shared as a link.
```

**Point out:** each new level is one more callback with named inputs and
outputs. Then compare with Panel's linked selections, where the cross-filter
is one line but the flow is less explicit.

**Fallback:** `make example dash`, then open <http://localhost:3112>.

## Build prompt

**Where:** Claude Code in this repository. This reproduces the folder.

```text
Build the Lumen Supply dashboard in Plotly Dash, in examples/gallery/dash/.
Follow examples/_shared/spec.md closely. Read examples/_shared/context.md
for the data, metric definitions, formats, and known answers, and
examples/_shared/design-tokens.css for colors. Copy the folder pattern from
examples/03-streamlit/.

Data:
- Connect with the WAREHOUSE_URL environment variable.
- Query only the metrics views. Put every query in data.py, cache each for
  five minutes, and convert Postgres numeric (Decimal) to float.
- The live chart reads metrics.service_health and is never cached.

Page (app.py, Dash title "Lumen Supply", served by gunicorn app:server):
- Copy the design tokens into assets/style.css, with light and dark sets
  keyed on data-theme. Map the Dash 4 component variables (--Dash-Text-Strong
  and friends) to the tokens. A theme button runs a clientside callback that
  sets data-theme and stores the choice; chart callbacks take the theme as
  an input and use the matching hex values.
- Header with "Lumen Supply", the period (Q3 2026), and "Data as of" the
  latest order.
- Four KPI cards: revenue, target with the gap in dollars, attainment
  colored and labeled by band (below 92% danger #c2410c "Missed", below 98%
  warning #b45309 "Close", else success #15803d "On track"), orders.
- Plotly charts for revenue against target by month (dashed target),
  attainment by region (horizontal bars, worst first, line at 100%), and
  revenue by channel by quarter (stacked, web #2563eb, mobile #f08c2e,
  partner #0f9d8a, channel in customdata).
- Region and channel dropdowns. One callback sets both from the attainment
  clickData, the channel clickData, and a "Clear filters" button. Clicking
  the same bar again clears it. Show the active filters.
- A DataTable of top products for the last full quarter with a search
  input, native sorting, 15 rows per page, money as $1,560,053.
- Live error rate by service, last 15 minutes, with a dashed line at 5%,
  driven by dcc.Interval every 5 seconds.
- dcc.Loading with text that says what is loading, and empty states that
  name the filter.
- A section labeled "Signature: callback-driven drill-through": revenue gap
  by region, click a region to see its channels this quarter against last,
  click a channel to open a modal with weekly revenue and the 25 largest
  orders. Keep the path in one dcc.Store. Use pattern-matching IDs for the
  level-2 chart, breadcrumb buttons, and the close button.

Packaging:
- requirements.txt pinning exact current versions of dash, plotly, pandas,
  psycopg[binary], and gunicorn.
- Dockerfile on python:3.13-slim, non-root user, PYTHONUNBUFFERED=1,
  gunicorn on port 8050 with two workers.
- compose.yaml with service ex-dash, profile ex-dash, image
  dashlab-ex-dash:local, port 127.0.0.1:3112:8050, WAREHOUSE_URL
  postgresql://lab_ro:lab_ro@warehouse:5432/lab, no depends_on, and a
  python urllib healthcheck against /_dash-layout.

Check: with no filters, revenue $5.64M, attainment 98.6%, EMEA worst at
89.6%. With EMEA selected, partner revenue in Q3 2026 is about $94K.
```
