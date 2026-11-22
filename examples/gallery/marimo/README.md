# marimo · Lumen Supply dashboard

**Builds:** the shared spec in [`_shared/spec.md`](../../_shared/spec.md).
**Types:** analytical, operational. **Needs:** the lab warehouse.
`make example marimo` runs it at <http://localhost:3114>.

A reactive notebook, served as an app. It answers which region missed its
revenue target last quarter, and why. KPIs on top, revenue against target by
month, attainment by region, revenue by channel, top products, and a live
error-rate panel. Every number comes from the `metrics` views.

## Files

| File | What it is |
| --- | --- |
| `lumen_supply.py` | The notebook. 19 cells, about 520 lines of plain Python |
| `lumen.css` | The design tokens for the header and KPI cards, light and dark |
| `requirements.txt` | Pinned marimo, psycopg, pandas, altair, duckdb, and sqlglot |
| `Dockerfile`, `compose.yaml` | How `make example marimo` runs it, in run mode with the code one click away |
| `prompts.md` | The demo prompt and the build prompt |

## Signature section: reactivity without callbacks

At the bottom, under **What marimo does best**:

1. Drag across the daily revenue chart to brush a range of days.
2. The next cell reads the brushed days. A SQL cell (`mo.sql`, run by
   DuckDB over a pandas dataframe) groups them by region and channel.
3. The table updates. No callback was written. Each cell names the values it
   uses, and marimo reruns it when one changes.

The filters above work the same way. Clicking a region bar sets `region`,
and the channel chart and products table rerun because they read it.
**Clear filters** is a button that the pickers and charts read, so a click
rebuilds them empty.

## Run it

```sh
make example marimo
```

Then open <http://localhost:3114>. Open the code from the menu at the top
right. To edit it, run `marimo edit lumen_supply.py` on your machine with
`WAREHOUSE_URL=postgresql://lab_ro:lab_ro@localhost:5433/lab`.

## What to point out

- **No callbacks.** A chart selection is a value. Cells that read it rerun.
  The dependency graph is the app.
- **It diffs cleanly.** The notebook is a `.py` file. Each cell is a
  function, so `git diff` shows a few lines of Python, not notebook JSON.
- **SQL and Python mix.** The SQL cell queries a dataframe from the cell
  above it. No extra service.
- **Notebook to app with no rewrite.** `marimo run` serves the same file.
- **The costs.** Layout is a vertical stack of cells, so fine layout control
  takes HTML and CSS. Clearing a chart selection means rebuilding the chart.
  Each viewer gets their own Python kernel, which costs memory as viewers
  grow. Hosting, sign-in, and upkeep are yours, as with any code you own.

## Fallback

If the live build fails, run `make example marimo` and open
<http://localhost:3114>.
