# Prompts · Panel

## Demo prompt

**Where:** Claude Code in this repository, with `make example panel`
running. **Time:** one to two minutes, plus a rebuild.

```text
In examples/gallery/panel/app.py, add a segment picker (Consumer, SMB,
Enterprise, or all) to the signature section. It should filter the orders
before they go into link_selections, so the three linked plots and the
table only show that segment. metrics.order_facts already has a segment
column, and data.orders_last_quarter() returns it. Keep the existing style.
Then rebuild and restart it with:
make example panel
```

**Expected:** a picker above the linked plots. Pick Enterprise and the
scatter plots thin out to the large orders. Brushing still filters all three
plots and the table.

### Follow-ups

```text
Add a fourth linked plot to the signature section: a histogram of order
revenue. It should take part in the same link_selections.
```

```text
Make the region filter at the top also filter the signature section.
```

**Point out:** the new plot joins the cross-filter with one line. There is
no callback to write. Then compare with the Dash drill-through, where every
interaction is a callback you write.

**Fallback:** `make example panel`, then open <http://localhost:3111>.

## Build prompt

**Where:** Claude Code in this repository. This reproduces the folder.

```text
Build the Lumen Supply dashboard in Panel (HoloViz), in
examples/gallery/panel/. Follow examples/_shared/spec.md closely. Read
examples/_shared/context.md for the data, metric definitions, formats, and
known answers, and examples/_shared/design-tokens.css for colors (the hex
values are at the bottom of the file). Copy the folder pattern from
examples/03-streamlit/.

Data:
- Connect with the WAREHOUSE_URL environment variable.
- Query only the metrics views. Put every query in data.py, cache each for
  five minutes, and convert Postgres numeric (Decimal) to float.
- The live chart reads metrics.service_health and is never cached.

Page (app.py, served with `panel serve app.py --index app`):
- A FastListTemplate titled "Lumen Supply" with the theme toggle. Read
  ?theme=dark from the session args and use the dark tokens when set.
- Header line with the period (Q3 2026) and "Data as of" the latest order.
- Four KPI cards: revenue, target with the gap in dollars, attainment
  colored and labeled by band (below 92% danger #c2410c "Missed", below 98%
  warning #b45309 "Close", else success #15803d "On track"), orders.
- Bokeh figures for revenue against target by month (dashed target),
  attainment by region (horizontal bars, worst first, line at 100%), and
  revenue by channel by quarter (stacked, web #2563eb, mobile #f08c2e,
  partner #0f9d8a). Use one ColumnDataSource per channel so a tap tells you
  the channel.
- Tapping a region bar sets a region Select. Tapping a channel segment sets
  a channel Select. A "Clear filters" button and an "Active filters" line.
  Changing either filter re-queries the channel chart and the products.
- A Tabulator of top products for the last full quarter with a search box,
  15 rows per page, sortable, money as $1,560,053.
- Live error rate by service, last 15 minutes, with a dashed line at 5%,
  updated by pn.state.add_periodic_callback every 5 seconds.
- Loading spinners on the filtered sections, and empty-state text that
  names the filter when there are no rows.
- A section titled "Signature: linked cross-filtering": every order in the
  last full quarter from metrics.order_facts, in three HoloViews plots
  joined by hv.link_selections (order value by day, units against order
  value, histogram of gross margin rate), plus a Tabulator of selected
  revenue by region and channel bound to ls.param.selection_expr.

Packaging:
- requirements.txt pinning exact current versions of panel, bokeh,
  holoviews, pandas, and psycopg[binary].
- Dockerfile on python:3.13-slim, non-root user, PYTHONUNBUFFERED=1,
  running panel serve on port 5006 with --liveness and
  --allow-websocket-origin for localhost:3111 and 127.0.0.1:3111.
- compose.yaml with service ex-panel, profile ex-panel, image
  dashlab-ex-panel:local, port 127.0.0.1:3111:5006, WAREHOUSE_URL
  postgresql://lab_ro:lab_ro@warehouse:5432/lab, no depends_on, and a
  python urllib healthcheck against /liveness.

Check: with no filters, revenue $5.64M, attainment 98.6%, EMEA worst at
89.6%. With EMEA selected, partner revenue in Q3 2026 is about $94K.
```
