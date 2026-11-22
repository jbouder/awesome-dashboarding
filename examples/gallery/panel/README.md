# Panel · Lumen Supply dashboard

**Types:** analytical, operational. **Needs:** the lab warehouse.
`make example panel` runs it at <http://localhost:3111>.

The shared Lumen Supply dashboard (`examples/_shared/spec.md`) built with
[Panel](https://panel.holoviz.org) from HoloViz. It answers which region
missed its target last quarter, and why: KPIs for Q3 2026, revenue against
target by month, attainment by region, revenue by channel, top products, and
a live error-rate chart. Click EMEA, and the channel chart shows partner
revenue falling to about $94K.

## Files

| File | What it is |
| --- | --- |
| `app.py` | The dashboard: Bokeh figures in a `FastListTemplate`, plus the HoloViews signature section |
| `data.py` | Every query. Reads only the `metrics` views and turns Decimals into floats |
| `requirements.txt` | Pinned `panel`, `bokeh`, `holoviews`, `pandas`, `psycopg` |
| `Dockerfile`, `compose.yaml` | How `make example panel` runs it on port 3111 |
| `prompts.md` | The demo prompt, its follow-ups, and the build prompt |

## Signature: linked cross-filtering

The last section loads every Q3 2026 order (about 7,800) into three
HoloViews plots joined by `hv.link_selections`: order value by day, units
against order value, and a histogram of gross margin rate. Drag a box in any
plot and the other two dim everything outside the selection. A Panel table
under the plots is bound to the same selection with `pn.bind`, so it shows
the selected revenue by region and channel. All of that is about 40 lines.

Try it: box-select the large orders in "Units against order value", then
look at how much of the selection is EMEA partner revenue.

## What to point out

- **Linked brushing for free.** `link_selections` is the thing Panel and
  HoloViews do that the other Python frameworks do not. You get
  crossfilter-style brushing across plots without writing the callbacks.
- **Python objects, live in the browser.** Each chart is a Bokeh figure
  with a `ColumnDataSource`. A click in the browser sets
  `source.selected.indices` in Python, and a Python change pushes new data to
  the browser over a websocket. The filter wiring is plain `on_change` and
  `param.watch`.
- **Real server state.** Each viewer gets a session. The live chart is a
  `pn.state.add_periodic_callback` that updates the data source every five
  seconds without redrawing the page.
- **The cost is the stack.** Panel, Param, Bokeh, and HoloViews each have
  their own API, and you use all four here. Small things take digging, such
  as stacked bars that report which segment was clicked, or the loading
  spinner, which has to sit on a column and not on a Bokeh pane.
- **Theming is coarse.** The template's theme toggle reloads the page with
  `?theme=dark`. The app reads that and picks the dark tokens. There is no
  live switch.
- **Websockets matter for hosting.** Every session holds a server
  connection, so it needs sticky sessions behind a load balancer, and
  `--allow-websocket-origin` must list the host people use.

## Fallback

`make example panel`, then open <http://localhost:3111>. Add `?theme=dark`
for the dark theme.
