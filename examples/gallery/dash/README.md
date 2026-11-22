# Dash · Lumen Supply dashboard

**Types:** analytical, operational. **Needs:** the lab warehouse.
`make example dash` runs it at <http://localhost:3112>.

The shared Lumen Supply dashboard (`examples/_shared/spec.md`) built with
[Plotly Dash](https://dash.plotly.com). It answers which region missed its
target last quarter, and why: KPIs for Q3 2026, revenue against target by
month, attainment by region, revenue by channel, top products, and a live
error-rate chart. Click EMEA, and the channel chart shows partner revenue
falling to about $94K.

## Files

| File | What it is |
| --- | --- |
| `app.py` | The layout and every callback, including the drill-through |
| `data.py` | Every query. Reads only the `metrics` views and turns Decimals into floats |
| `assets/style.css` | The lab design tokens plus layout. Dash loads `assets/` on its own |
| `requirements.txt` | Pinned `dash`, `plotly`, `pandas`, `psycopg`, `gunicorn` |
| `Dockerfile`, `compose.yaml` | How `make example dash` runs it on port 3112, under gunicorn |
| `prompts.md` | The demo prompt, its follow-ups, and the build prompt |

## Signature: callback-driven drill-through

The last section walks from the miss to the orders behind it, one callback
per level:

1. **Region.** Revenue gap to target by region. Click EMEA.
2. **Channel.** EMEA revenue by channel, this quarter against the one
   before. Partner drops from about $297K to about $94K. Click partner.
3. **Detail.** A modal with weekly revenue for EMEA partner over two
   quarters and the 25 largest orders.

One `dcc.Store` holds the drill path. The level-2 chart, the breadcrumb
buttons, and the modal's close button are created by callbacks, so they use
pattern-matching IDs (`{"type": "crumb", "level": ALL}`) to send clicks back
to that store. Every other part of the section re-renders from the store.

## What to point out

- **Every interaction is explicit.** A callback names its inputs and
  outputs. You can read `app.py` and see exactly what a click changes. That
  is why Dash is common for apps that grow past a few charts.
- **Pattern-matching callbacks** handle components that do not exist until
  a callback creates them, such as the drill-down chart and the breadcrumbs.
- **Stateless server.** Callbacks are plain HTTP requests, and state lives
  in the browser (`dcc.Store`). It runs under gunicorn with several workers
  and needs no sticky sessions.
- **Theme switches live.** A clientside callback sets `data-theme` on the
  page, and the chart callbacks redraw with the dark tokens. Dash 4
  components read CSS variables, which `assets/style.css` maps to the tokens.
- **The cost is wiring.** Cross-filtering takes callbacks you write by
  hand: a click handler, a toggle for clicking the same bar twice, a guard
  for components that just mounted. Panel's `link_selections` does that in
  one line.
- **Polling, not push.** The live chart is a `dcc.Interval` that asks the
  server every five seconds. That is fine here, but every open tab makes
  that request.

## Fallback

`make example dash`, then open <http://localhost:3112>.
