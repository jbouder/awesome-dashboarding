# OpenSearch Dashboards

**Type:** operational (logs). **License:** Apache 2.0.
**URL:** <http://localhost:5601>. No sign-in. OpenSearch's API is at
<http://localhost:9200>.

```sh
make up opensearch
```

The security plugin is off so the lab needs no certificates or passwords.
Never run OpenSearch that way anywhere else.

## What the lab sets up

- OpenSearch, single node, with half a gigabyte of heap.
- **Access logs** from the five Lumen Supply services, written by `logs.py`.
  It reads the live service metrics and writes log lines that match them:
  the same mix of errors, the same latency. It backfills the last hour on
  first start.
- OpenSearch Dashboards with an index pattern, `lumen-logs-*`, and a
  dashboard, **Lumen Supply service logs**, imported by `bootstrap.py`:
  5xx errors, requests by status class, errors by service over time, where
  the errors are, and the slowest routes.

## Tour

1. Open **Dashboards → Lumen Supply service logs**. It refreshes every 10
   seconds.
2. Run `make incident`. Within a minute, 5xx errors climb, and checkout takes
   over the **Where the errors are** donut.
3. Click checkout in the donut. The whole dashboard filters to checkout.
4. Open **Discover** and search `service:checkout and status >= 500`.
   Expand a line to see its request id and message. This is the "why" behind
   a red tile in Grafana.

## Compare

Grafana and Rill show metrics: how many and how fast. OpenSearch shows the
events behind them. Operational teams usually need both.
