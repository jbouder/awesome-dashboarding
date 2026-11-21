# Lightdash

**Type:** analytical. **License:** MIT.
**URL:** <http://localhost:8080>, sign in as `admin@dashlab.local` /
`dashlab-admin-1`.

```sh
make up lightdash
```

Lightdash publishes an `amd64` image only. On Apple Silicon, Docker runs it
under emulation, so the first start takes a few minutes. It also brings its
own Postgres and MinIO, which it requires for storage.

## What the lab sets up

Lightdash is BI on top of a dbt project: metrics and dimensions are defined in
dbt's YAML, next to the models. The lab's project is in `dbt/`:

- Three models, `daily_revenue`, `monthly_kpis`, and `line_facts`. Each one
  names an existing view in the warehouse's `metrics` schema. Lightdash only
  compiles the project. It never runs dbt, so nothing is written to the
  warehouse.
- `models/schema.yml` defines the metrics: revenue, gross margin, orders,
  units, target, and **revenue attainment**, plus the dimensions to slice by.

`bootstrap.py` creates the admin, the organization, and the **Lumen Supply**
project, then compiles it.

## Tour

1. Press **Run a query**, then pick the **Monthly KPIs** table. Pick **Region**, **Revenue**,
   and **Revenue attainment**. Filter **Month** to the last completed
   quarter. EMEA is at about 90%.
2. Switch to **Daily revenue**, add **Channel**, and filter to EMEA. Group by
   quarter to see the partner channel shrink.
3. Save the chart, and add it to a new dashboard.
4. Open `dbt/models/schema.yml`. Every metric you clicked is defined there,
   in Git. Add one, then press **Refresh dbt** above the table list to
   pick it up.

## Notes

- dbt writes `target/`, `logs/`, and `dbt_packages/` into `dbt/`. Git
  ignores them.
- Usage analytics are turned off.
- Lightdash's AI features need its own model settings. See its docs.
