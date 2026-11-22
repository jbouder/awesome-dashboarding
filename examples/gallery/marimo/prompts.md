# Prompts · marimo

## Demo prompt

**Where:** Claude Code in this repository, with `make example marimo`
running. **Time:** one to two minutes.

```text
In examples/gallery/marimo/lumen_supply.py, add a cell after the attainment
chart that shows the selected region's revenue against target by month for
the last 12 full months, from metrics.monthly_kpis. Use a blue line for
revenue (#2563eb) and a dashed orange line for target (#f08c2e). When no
region is selected, show all regions. Read the existing `region` variable.
Do not add a callback.
```

**Expected:** a new cell that reads `region`. Rebuild with
`make example marimo`. Click EMEA in the attainment chart and the new chart
redraws for EMEA, with revenue under target in every month of Q3.

### Follow-ups

```text
Add a dropdown to the new cell that switches the measure between revenue,
orders, and average order value.
```

```text
Show me the git diff for lumen_supply.py.
```

**Point out:** the new cell names `region`, and that is the whole wiring.
The diff is plain Python, a few lines long.

**Fallback:** `make example marimo`, then open <http://localhost:3114>.

## Build prompt

**Where:** Claude Code in this repository. This reproduces the folder.

```text
Build the Lumen Supply dashboard as a marimo notebook in
examples/gallery/marimo/. Follow examples/_shared/spec.md exactly. Read
examples/_shared/context.md for the data, metrics, formats, and known
answers, and examples/_shared/design-tokens.css for colors and type. Copy
the folder layout and tone of examples/03-streamlit/.

Data: connect with the WAREHOUSE_URL environment variable. Query only the
metrics views. Convert Postgres numeric (Decimal) to float before charting.

Build all seven spec sections in order:
1. Header with "Lumen Supply", the period ("Q3 2026"), and data as of.
2. Four KPI cards against the prior quarter. Color attainment by band
   (danger #c2410c under 92%, warning #b45309 under 98%, else success
   #15803d) and label it Missed, Close, or On track.
3. Revenue and dashed target by month, last 12 full months.
4. Attainment by region, worst first, rule at 100%. A click on a bar sets
   the region filter (mo.ui.altair_chart with a selection_point on region).
5. Revenue by channel by quarter, stacked, web #2563eb, mobile #f08c2e,
   partner #0f9d8a. A click sets the channel filter.
6. Top products for the region and channel, mo.ui.table, 15 rows a page.
7. Live error rate by service, last 15 minutes, with mo.ui.refresh every
   5 seconds and a rule at 5%.
Add region and channel pickers, a line that shows the active filters, and
a Clear filters button that the pickers and charts read, so a click rebuilds
them. No callbacks.

Add a signature section, "What marimo does best: reactivity without
callbacks": a daily revenue chart with an x-axis brush, a cell that reads
the brushed days, and a mo.sql cell that groups them by region and channel.
Say that the notebook is a .py file that diffs cleanly in Git.

Put token colors for light and dark in lumen.css (marimo marks dark mode
with .dark). Pin exact versions in requirements.txt (marimo 0.25.2,
psycopg[binary] 3.3.9, pandas 3.1.1, altair 6.3.0, duckdb, sqlglot). Write a
Dockerfile on python:3.13-slim with a non-root user and PYTHONUNBUFFERED=1
that runs `marimo run lumen_supply.py --include-code` on port 2718. Write
compose.yaml with service and profile ex-marimo, image
dashlab-ex-marimo:local, port 127.0.0.1:3114:2718, no depends_on, and a
healthcheck on /health with python urllib. Then a README.md and this
prompts.md.

Check it: run `marimo check` and `marimo export html` in the container, and
confirm $5.64M, 98.6%, EMEA at 89.6%, and EMEA partner revenue near $94K in
the last full quarter.
```
