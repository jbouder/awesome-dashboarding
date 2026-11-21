# Evidence

**Type:** strategic. **License:** MIT.
**URL:** <http://localhost:3005>, user `lab`, password `lab`.

```sh
make up evidence
```

## What the lab sets up

Evidence builds reports from Markdown and SQL. The whole project is in
`project/`:

- `connection.yaml`: a direct connection to the warehouse as `lab_ro`.
  Queries run live against Postgres. No Evidence Studio account is needed.
- `pages/index.md`: **Lumen Supply: quarterly report**. Last quarter's
  revenue, attainment, and orders, attainment by region, revenue by channel
  with a region picker, and revenue against target by month.

The image is built from Evidence's own self-host Dockerfile and runs
`evidence serve`, the production server. Evidence requires a password when
it listens beyond the container, so the lab sets `lab` / `lab`.

## Tour

1. Open the report and sign in. Read it top to bottom: it is a report, not a
   dashboard, and it reads like one.
2. Pick **EMEA** in the Region menu above the channel chart, and compare the
   partner bars across quarters.
3. Open `project/pages/index.md`. The whole report is under 100 lines. Change
   a query or a chart, then run `make restart evidence`.
4. Ask an AI assistant to add a section, for example "a table of the top 10
   products last quarter". Evidence's syntax is plain text, so the change is
   a diff you can review.

## Check it from the command line

```sh
docker compose exec evidence evidence validate
docker compose exec evidence evidence query "SELECT count(*) FROM metrics.daily_revenue"
```
