# ClickHouse

**Type:** operational (engine). **License:** Apache 2.0.
**SQL console:** <http://localhost:8123/play>, user `lab`, password `lab`.
**MCP server:** <http://localhost:5009/mcp>.

```sh
make up clickhouse            # ClickHouse and its MCP server
make up clickhouse grafana    # plus a Grafana dashboard that reads ClickHouse
```

## What the lab sets up

ClickHouse is the engine behind many operational dashboards, not a dashboard
itself. The lab loads it from the warehouse with **refreshable materialized
views** (`initdb/01-lumen.sql`), so no separate sync service is needed:

- `lumen.request_metrics`: the live service metrics, refreshed every 10
  seconds.
- `lumen.sales`: every completed order line, refreshed every hour.

It also runs ClickHouse's own MCP server, so an agent can explore and query
the data. Its auth is off and it accepts only the host's loopback. Keep it
local.

With the grafana stack running too, Grafana has a **Lab ClickHouse**
datasource and a **Service health (ClickHouse)** dashboard.

## Tour

1. Open <http://localhost:8123/play> and sign in as `lab` / `lab`. Run:

   ```sql
   SELECT region, channel, round(sum(revenue)) AS revenue
   FROM lumen.sales
   WHERE ordered_at >= toStartOfQuarter(now()) - INTERVAL 3 MONTH
     AND ordered_at < toStartOfQuarter(now())
   GROUP BY ALL ORDER BY region, channel
   ```

   EMEA's partner revenue is the outlier.
2. Watch the sync: `SELECT view, status, last_success_time FROM
   system.view_refreshes`.
3. Run `make up grafana` too, and open **Service health (ClickHouse)** in
   Grafana. Run `make incident` and watch checkout's error rate climb, with
   up to 10 seconds of sync delay.
4. Connect an agent:

   ```sh
   claude mcp add --transport http clickhouse http://localhost:5009/mcp
   ```

   Then ask: "Using ClickHouse, which region missed its revenue target last
   quarter?" The `lumen` database has no targets table, so watch whether the
   agent says so or invents one.
