# Apache Superset

**Types:** strategic, analytical. **License:** Apache 2.0.
**URL:** <http://localhost:8088>, sign in as `admin` / `admin`.

```sh
make up superset
```

## What the lab sets up

- Superset 6.1, with its metadata in the warehouse's `superset` database.
- A connection named **Lab warehouse**, as the read-only `lab_ro` role.
- Three datasets from the semantic layer: `metrics.monthly_kpis`,
  `metrics.daily_revenue`, and `metrics.line_facts`.
- Two dashboards, built by `bootstrap.py`:
  - **Executive KPIs**: last quarter's revenue, attainment, and orders,
    revenue against target by month, and attainment by region.
  - **Revenue analysis**: revenue by channel over time, EMEA revenue by
    channel per quarter, revenue by category, average order value, and top
    products.
- Superset's MCP server at <http://localhost:5008/mcp>.

## Tour

1. Open **Dashboards → Executive KPIs**. That is the strategic view: are we
   on track? Attainment by region shows EMEA furthest below target.
2. Open **Revenue analysis**. That is the analytical view: why?
   **EMEA revenue by channel, by quarter** shows the partner channel
   shrinking in the last full quarter while web and mobile hold up.
3. Click any chart title to open it in Explore, and change the grouping or
   filters to dig further.
4. Open **SQL → SQL Lab** and query the same views by hand:

   ```sql
   SELECT date_trunc('quarter', order_date) AS quarter, channel, sum(revenue)
   FROM metrics.daily_revenue WHERE region = 'EMEA'
   GROUP BY 1, 2 ORDER BY 1, 2;
   ```

## Try the MCP server

Connect an agent to Superset and let it explore. With Claude Code:

```sh
claude mcp add --transport http superset http://localhost:5008/mcp
```

Then ask: "Using Superset, which region missed its revenue target last
quarter, and why?" The lab's MCP server acts as the Superset admin, so the
agent can also create charts and dashboards. Keep it local.

## Notes

- Superset's own example data is not loaded. Everything you see is lab data.
- The bootstrap only creates what is missing. To rebuild the dashboards,
  delete them in the UI and run `make up superset` again.
