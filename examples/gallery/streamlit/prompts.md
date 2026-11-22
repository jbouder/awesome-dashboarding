# Prompts · Streamlit

## Demo prompt

**Where:** Claude Code in this repository, with `make example streamlit`
running. **Time:** one to two minutes.

```text
In examples/gallery/streamlit/app.py, add a section after the products
table: average order value by segment for the last full quarter, for the
selected region and channel, as horizontal bars. Use metrics.order_facts,
which has segment, region, channel, revenue, and ordered_at. Average order
value is revenue divided by orders. Reuse the existing query() helper and
the region and channel variables.
```

**Expected:** about 20 new lines and a new chart. Rebuild with
`make example streamlit`. Click EMEA, then partner, and the bars change.

### Follow-ups

```text
Put the new chart and the products table side by side in two columns.
```

```text
Add a download button that saves the products table as CSV.
```

**Point out:** each change is a few function calls in one script. No
callbacks, no front end code.

**Fallback:** `make example streamlit`, then open <http://localhost:3115>.

## Build prompt

**Where:** Claude Code in this repository. This reproduces the folder.

```text
Build the Lumen Supply dashboard as a Streamlit app in
examples/gallery/streamlit/. Follow examples/_shared/spec.md exactly. Read
examples/_shared/context.md for the data, metrics, formats, and known
answers, and examples/_shared/design-tokens.css for colors and type. Copy
the folder layout and tone of examples/03-streamlit/.

Data: connect with the WAREHOUSE_URL environment variable. Query only the
metrics views, cache with st.cache_data, and convert Postgres numeric
(Decimal) to float before charting. The page title must include
"Lumen Supply". Use width="stretch", never use_container_width.

Build all seven spec sections in order:
1. Header with "Lumen Supply", the period ("Q3 2026"), and data as of.
2. Four st.metric cards against the prior quarter. Attainment gets a word
   (Missed under 92%, Close under 98%, else On track) as its delta, colored
   red, orange, or green.
3. Revenue and dashed target by month, last 12 full months.
4. Attainment by region, worst first, rule at 100%. A click on a bar sets
   the region filter (st.altair_chart with on_select="rerun").
5. Revenue by channel by quarter, stacked, web #2563eb, mobile #f08c2e,
   partner #0f9d8a. A click sets the channel filter.
6. Top products for the region and channel, with a search box, 15 rows.
7. Live error rate by service, last 15 minutes, in an
   st.fragment(run_every=5), with a rule at 5%.
Add region and channel pickers, badges that show the active filters, and a
Clear filters button. Reset charts by changing their widget keys.

Add a signature section, "What Streamlit does best: speed of building": a
radio button that switches between the semantic layer ($5.64M) and raw
tables (sum(quantity * unit_price) over shop.orders and shop.order_items, no
status filter, about $6.54M), with a warning callout that explains the gap
and an expander with both queries.

Put the tokens in .streamlit/config.toml as [theme.light] and [theme.dark],
mapping red, orange, and green to danger #c2410c, warning #b45309, and
success #15803d. Pin exact versions in requirements.txt (streamlit 1.67.0,
psycopg[binary] 3.3.9, pandas 3.1.1, altair 6.3.0). Write a Dockerfile on
python:3.13-slim with a non-root user, PYTHONUNBUFFERED=1, and
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false. Write compose.yaml with service
and profile ex-streamlit, image dashlab-ex-streamlit:local, port
127.0.0.1:3115:8501, no depends_on, and a healthcheck on /_stcore/health
with python urllib. Then a README.md and this prompts.md.

Check it with streamlit.testing AppTest: no exceptions, $5.64M, 98.6%, EMEA
at 89.6%, and EMEA partner revenue near $94K in the last full quarter.
```
