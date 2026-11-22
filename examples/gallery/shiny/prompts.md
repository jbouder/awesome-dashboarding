# Prompts · Shiny for Python

## Demo prompt

**Where:** Claude Code in this repository, with the lab warehouse and
`make example shiny` running. **Time:** one to two minutes, plus a rebuild.

```text
In examples/gallery/shiny/app/app.py, add a "Gross margin by segment" card
under the products table. Use metrics.daily_revenue, which has order_date,
segment, revenue, and gross_margin. Show margin as a percent of revenue for
the last full quarter, one horizontal bar per segment, and make it follow
the Region filter. Keep the existing chart_html helper and design colors.
```

**Expected:** a new card with three bars (Consumer, SMB, Enterprise). Pick
EMEA and only that card, the channel chart, and the products table redraw.

### Follow-ups

```text
Add a "Minimum margin" slider to the what-if panel. Highlight segments
below it in the margin chart. Make sure the other what-if outputs do not
re-run when it moves.
```

```text
Show p95 latency next to the error rate in the live panel, from
metrics.service_health, still refreshing every 5 seconds.
```

**Point out:** the new output re-runs only when the region or the slider
changes. Shiny worked that out from what the function reads.

**Fallback:** `make example shiny`, then open <http://localhost:3113>.

## Build prompt

**Where:** Claude Code in this repository. This reproduces `app/`.

```text
Build the Lumen Supply dashboard in Shiny for Python, in
examples/gallery/shiny/. Follow examples/_shared/spec.md exactly. Read
examples/_shared/context.md for the data, metric definitions, formats, and
known answers, and examples/_shared/design-tokens.css for colors and type.
Copy the folder pattern of examples/03-streamlit/.

Data: connect with the WAREHOUSE_URL environment variable. Query only the
metrics views. Convert Postgres numeric values to float before charting.

Build:
1. Header "Lumen Supply", the last full quarter (Q3 2026), and "Data as
   of" from the latest order.
2. Four KPI cards: revenue with change, target with the gap, attainment
   colored by band (danger #c2410c below 92%, warning #b45309 below 98%,
   success #15803d otherwise) with a word label, orders with change.
3. Plotly charts rendered as HTML with plotly.js served from the plotly
   package. Revenue against target by month, attainment by region with a
   line at 100%, revenue by channel by quarter (web #2563eb, mobile
   #f08c2e, partner #0f9d8a). A click on a region bar or channel band calls
   Shiny.setInputValue and updates the Region and Channel pickers.
4. Top 15 products for the selected region and channel, with a search box
   and a sortable DataGrid. Show an empty state when nothing matches.
5. A live error-rate-by-service chart from metrics.service_health, last 15
   minutes, refreshed with reactive.invalidate_later(5), with a line at 5%.
6. A visible filter status with a Clear filters button. A dark mode toggle
   (input_dark_mode) that the charts read.
7. Signature section: a what-if card with sliders for target uplift % and
   partner revenue recovered %. Use separate reactive calcs for base
   numbers, new targets, and recovered revenue, so each output depends only
   on what it needs. Show a run counter on each output.

Files: app/app.py, app/requirements.txt (pinned exact versions),
app/Dockerfile (python:3.13-slim, non-root user, PYTHONUNBUFFERED=1, port
8000), compose.yaml with service and profile ex-shiny, image
dashlab-ex-shiny:local, port 127.0.0.1:3113:8000, no depends_on, and a
python urllib healthcheck on port 8000. The page must contain "Lumen
Supply". Check: revenue $5.64M, attainment 98.6%, EMEA lowest at 89.6%,
and with EMEA picked, partner revenue near $94K in the last full quarter.
```
