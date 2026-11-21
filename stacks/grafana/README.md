# Grafana

**Type:** operational. **License:** AGPL-3.0.
**URL:** <http://localhost:3001>. Anyone can view. Sign in as `admin` /
`admin` to edit.

```sh
make up grafana
```

## What the lab sets up

Everything is provisioned from files in this folder, so nothing is built by
hand:

- `provisioning/datasources/`: **Lab warehouse**, a PostgreSQL datasource on
  the warehouse as `lab_ro`, with TimescaleDB on.
- `dashboards/service-health.json`: **Service health**, the home
  dashboard. Requests, error rate, and p95 latency per service, refreshed
  every 5 seconds from `ops.request_metrics`, plus recent incidents.
- `provisioning/alerting/`: **High error rate**, which fires for any service
  whose error rate over the last minute is above 5%.

## Tour

1. Open <http://localhost:3001>. The dashboard is live. The `stream` service
   writes new metrics every 5 seconds.
2. Start an incident:

   ```sh
   make incident                     # 3 minutes of errors on checkout
   make incident payments latency 5  # 5 minutes of slow payments
   ```

3. Watch **Error rate by service** cross the red threshold line.
4. Open **Alerting → Alert rules**. **High error rate** goes from Normal to
   Pending, then to Firing about 30 seconds later, labeled with the service.
5. When the incident ends, the alert resolves on its own.

## Compare

Superset and Metabase answer "are we on track?" from daily and monthly data.
Grafana answers "is something wrong right now?" from data seconds old, and
pages someone when the answer is yes.
