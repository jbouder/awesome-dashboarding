# Part 2 · Grafana: watching the present

**Supports:** Part 2, Demo 2. **Type:** operational. **Needs:** `make up
grafana` (<http://localhost:3001>, anyone can view, `admin` / `admin` to
edit). For step 5, `make up clickhouse` too.

Same data as the Superset demo, different question: is something wrong right
now? Then the alert that pages someone when nobody is watching.

## The demo, with timings

| Time | Do | What happens |
| --- | --- | --- |
| 0:00 | Open <http://localhost:3001>. **Service health** is the home dashboard | Live panels, refreshed every 5 seconds |
| 0:30 | In a terminal, run `make incident` | Checkout's error rate starts climbing |
| 0:45 | Watch **Error rate by service** | Checkout crosses the red 5% line within about 30 seconds |
| 1:30 | Open **Alerting → Alert rules → High error rate** | Normal, then Pending, then Firing, labeled `service=checkout` |
| 2:30 | Open the **Error rate by service** panel's menu → **Edit** | The SQL behind it, on `ops.request_metrics` |
| 3:00 | Open **Dashboards → Lab → Service health (ClickHouse)** | The same panels from ClickHouse, which copies the metrics every 10 seconds |
| 3:30 | Contrast with Superset | Superset's charts are daily and monthly. Grafana's are seconds old |

The incident lasts three minutes, then the alert resolves on its own. `make
incident payments latency 5` gives a latency incident instead.

## What to point out

- **Operational means now.** Freshness in seconds, not days.
- **Alerting is the point.** An operational dashboard nobody watches still
  has to page someone.
- **The engine matters.** Postgres is fine at lab scale. ClickHouse is what
  teams switch to when it is not.
- **AGPL-3.0.** Fine to run. Review it before you embed or modify Grafana
  in a product.

## Agent

The grafana stack also runs Grafana's MCP server,
[mcp-grafana](https://github.com/grafana/mcp-grafana), at
<http://localhost:5010/mcp>. It signs in as the Grafana admin. Keep it
local. See `prompts.md`.

## Fallback

If the alert is slow, show **Alerting → Alert rules** with the rule's
history, or run `make incident` before the talk so one is already firing.
