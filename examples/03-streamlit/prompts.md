# Prompts · 03 Streamlit

## Demo prompt

**Where:** Claude Code, in an empty folder, with the lab warehouse running.
**Time:** two to three minutes, including install.

```text
Build a Streamlit app, app.py, that answers: which region missed its
revenue target last quarter, and why?

Data: Postgres at localhost:5433, database lab, user lab_ro, password
lab_ro. Use the views in schema metrics: metrics.monthly_kpis has month,
region, revenue, and revenue_target. Last quarter means the last calendar
quarter that has ended.

Show last quarter's total revenue and attainment as metrics, name the
region furthest below target, and chart attainment by region with a line
at 100%. Then tell me how to run it.
```

**Expected:** an app showing $5.64M, 98.6%, and EMEA as the miss, about 10%
under target.

### Follow-up

```text
Add a region picker, defaulting to the worst region, and a stacked bar
chart of that region's revenue by channel for the last four full quarters.
Use metrics.daily_revenue, which has order_date, region, channel, and
revenue.
```

**Expected:** with EMEA picked, the partner band shrinks sharply in the last
quarter. That is the "why".

**Point out:** open `app.py` and scroll through it. Every line is yours to
maintain.

**Fallback:** `make example streamlit-demo`.

## Build prompt

**Where:** Claude Code in this repository. This reproduces `app/app.py`.

```text
Write examples/03-streamlit/app/app.py, a Streamlit app that answers which
region missed its revenue target last quarter, and why. Read
examples/_shared/context.md for the data and metric definitions.

Connect with the WAREHOUSE_URL environment variable. Query only the metrics
views, cache queries for five minutes, and convert Postgres numeric columns
to floats before charting.

Show:
1. A title that asks the question.
2. Three metrics: last full quarter's revenue as $5.64M, attainment, and
   the region furthest below target with its gap as the delta (red when
   below target).
3. Attainment by region as horizontal Altair bars on a fixed 80% to 110%
   scale, worst first, orange-red below 98% and blue otherwise, with a
   dashed rule at 100%.
4. A region picker defaulting to the worst region, and that region's
   revenue by channel for the last four full quarters as stacked bars in
   the lab's channel colors (web #2563eb, mobile #f08c2e, partner #0f9d8a).
5. A caption saying revenue comes from the semantic layer.

Keep it under 100 lines. Also write a requirements.txt pinning streamlit,
psycopg[binary], pandas, and altair, and a Dockerfile that runs it on port
8501 as a non-root user.
```
