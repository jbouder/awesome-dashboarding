# Rill

**Types:** analytical, operational. **License:** Apache 2.0.
**URL:** <http://localhost:9009>. No sign-in.

```sh
make up rill
```

## What the lab sets up

Rill builds dashboards from YAML files. The whole project is in `project/`:

- `connectors/warehouse.yaml`: the lab warehouse, as `lab_ro`.
- `models/sales.yaml`: completed order lines from `metrics.line_facts`,
  copied into Rill's own DuckDB.
- `models/service_metrics.yaml`: the live service metrics, refreshed every
  minute.
- `metrics/`: two metrics views, which define the measures (revenue, orders,
  average order value, error rate) and dimensions once.
- `dashboards/`: two explore dashboards, **Lumen Supply sales** and
  **Service health**.

## Tour

1. Open **Lumen Supply sales**. Every measure is compared with the previous
   period out of the box.
2. Set the time range to the last full quarter, compared with the previous
   period.
3. Click **EMEA** in the Region list. Everything filters to EMEA. In the
   Channel list, web and mobile grew and partner fell by about two thirds.
4. Open **Edit** to see the YAML behind the dashboard. Change a measure,
   save, and the dashboard updates. The files are easy for an AI assistant to
   write, too.
5. Open **Service health**, run `make incident`, and wait up to a minute for
   the next refresh.

## Notes

- Rill copies data into its own engine. That is why it is fast, and why the
  service metrics are up to a minute behind.
- Edits made in Rill's editor stay in the container. Change
  `stacks/rill/project/` and run `make restart rill` to keep them.
- Usage analytics are turned off in the lab's image.
