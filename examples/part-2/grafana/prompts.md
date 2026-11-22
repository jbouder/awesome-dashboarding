# Prompts · Part 2 Grafana

## Demo prompt

**Where:** Claude Code with Grafana's MCP server connected:

```sh
claude mcp add --transport http grafana http://localhost:5010/mcp
```

Run `make incident` first. **Time:** about a minute.

```text
Using the Grafana tools: is anything wrong with our services right now?
Check the alert rules and the Service health dashboard, and tell me which
service, since when, and how bad.
```

**Expected:** checkout, with a firing **High error rate** alert and an error
rate around 10%, starting when you ran `make incident`.

### Follow-up

```text
Add a panel to the Service health dashboard that shows checkout's error
rate alone, with a red line at 5%.
```

**Expected:** a new panel on the dashboard. The dashboard is provisioned
from a file, so restarting Grafana may put it back the way the file has it.

**Point out:** the agent reads alerts and dashboards through the same API
people use, and what it changes is visible to everyone.

**Fallback:** open **Alerting → Alert rules** and show the firing rule.

## Build prompts

These reproduce the Grafana stack. Run them in Claude Code in this
repository.

### The dashboard and the alert

```text
Provision Grafana for the lab in stacks/grafana/: a PostgreSQL datasource
"Lab warehouse" (uid lab-warehouse) on the warehouse as lab_ro; a "Service
health" dashboard, refreshed every 5 seconds over the last hour, with stat
panels for requests per second, error rate, worst p95 latency, and active
incidents, time series of requests, error rate (threshold at 5%), and p95
latency by service from ops.request_metrics, and a table of recent
incidents; and an alert rule "High error rate" that fires when any
service's error rate over the last minute is above 5% for 20 seconds,
labeled by service. Make the dashboard the home dashboard and allow
anonymous viewers.
```

### Grafana's MCP server

```text
Add Grafana's MCP server to stacks/grafana/compose.yaml: image
grafana/mcp-grafana pinned to a release, streamable-http on 0.0.0.0:8000,
published on 127.0.0.1:5010, signed in as the Grafana admin, with an
allowed-hosts list for the host port and a healthcheck on /healthz.
```
