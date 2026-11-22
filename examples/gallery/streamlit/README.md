# Streamlit · Lumen Supply dashboard

**Builds:** the shared spec in [`_shared/spec.md`](../../_shared/spec.md).
**Types:** analytical, operational. **Needs:** the lab warehouse.
`make example streamlit` runs it at <http://localhost:3115>.

One Python script that answers which region missed its revenue target last
quarter, and why. KPIs on top, revenue against target by month, attainment
by region, revenue by channel, top products, and a live error-rate panel.
Every number comes from the `metrics` views, except the raw-tables
comparison at the end, which is there to show why that matters.

## Files

| File | What it is |
| --- | --- |
| `app.py` | The app. About 390 lines, top to bottom in spec order |
| `.streamlit/config.toml` | The design tokens as a Streamlit theme, light and dark |
| `requirements.txt` | Pinned streamlit, psycopg, pandas, and altair |
| `Dockerfile`, `compose.yaml` | How `make example streamlit` runs it |
| `prompts.md` | The demo prompt and the build prompt |

The small Part 1 demo app is in `examples/03-streamlit/`. This one is the
full spec.

## Signature section: speed of building

At the bottom, under **What Streamlit does best**, a radio button switches
the revenue definition:

- **Semantic layer:** $5.64M for the last full quarter, 98.6% of target.
- **Raw tables:** `sum(quantity * unit_price)` over `shop.orders` and
  `shop.order_items` with no status filter. It says $6.54M and 114.4%. A
  warning explains the $903K gap: refunded and canceled orders, and no
  discounts.

The section is about 30 lines: a radio button, two queries, three metrics,
and a callout. The SQL for both answers sits in an expander.

## Run it

```sh
make example streamlit
```

Then open <http://localhost:3115>. Change `app.py` and rebuild with the same
command.

## What to point out

- **Fast to build.** Widgets are function calls. The script reruns on every
  click, so there is no state to wire up.
- **Charts are inputs.** `st.altair_chart(on_select="rerun")` returns the
  clicked region or channel, and the script uses it like any variable.
- **Live without a full rerun.** The error-rate panel is an
  `st.fragment(run_every=5)`. Only that function reruns.
- **Theme in one file.** The tokens live in `.streamlit/config.toml`, and
  viewers pick light or dark in Settings.
- **The costs.** Every click reruns the whole script, so slow queries need
  `st.cache_data`. Resetting a chart selection means a new widget key.
  Layout is rows and columns, with little fine control. Hosting, sign-in,
  and keeping the numbers right are yours.

## Fallback

If the live build fails, run `make example streamlit` and open
<http://localhost:3115>.
