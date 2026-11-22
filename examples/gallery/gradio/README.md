# Gradio · Lumen Supply dashboard

**Types:** analytical, generative. **Needs:** the lab warehouse.
`make example gradio` runs it at <http://localhost:3117>.

The Lumen Supply dashboard from [`_shared/spec.md`](../../_shared/spec.md),
built in Gradio as far as Gradio reasonably goes. KPIs for the last full
quarter, revenue against target by month, attainment by region, revenue by
channel, top products, and a live error-rate panel. Every query reads the
`metrics` views.

Gradio is built for machine learning demos: inputs, a function, outputs. It
can show a dashboard, but it was not designed for one.

## Files

| File | What it is |
| --- | --- |
| `prompts.md` | The demo prompt, follow-ups, and the build prompt |
| `app/app.py` | The app. Queries, Plotly charts, the layout, and events. About 500 lines |
| `app/requirements.txt` | Pinned `gradio`, `psycopg[binary]`, `pandas`, `plotly` |
| `app/Dockerfile`, `compose.yaml` | How `make example gradio` runs it on port 3117 |

## Signature: ask about a region

The dashed panel at the bottom is Gradio's home turf. Pick a region and a
quarter, press **Summarize**, and a plain Python function writes what
changed: revenue against target, the change from the quarter before, the
channel that dropped most, and whether recovering it closes the gap. It
uses templates, not an LLM. Pick EMEA and Q3 2026 and it names the partner
drop from $297K to $94K.

Every event is also an API. `gradio_client` can call `/summarize` with the
same two inputs.

## Where it falls short of the spec

- **Charts are not clickable.** `gr.Plot` has no click event. The Region
  and Channel pickers filter instead, and a click on a row in the
  attainment table sets the region.
- **Charts do not follow dark mode.** The page follows the system theme,
  but the server never learns which one, so chart text uses a mid gray
  that reads on both.
- **Layout is coarse.** Rows and columns only. KPI cards are an HTML block.
- **Every interaction is a round trip** to a Python function, with
  Gradio's progress overlay as the loading state.

## What to point out

- **Fastest path from a function to a UI.** Write a function, name its
  inputs and outputs, and the panel exists.
- **The live panel is a timer.** `gr.Timer(5)` ticks and redraws the
  error-rate chart.
- **A free API.** Each event gets an endpoint, which suits model demos and
  agents more than dashboards.
- **Reach for it** to put a model or a query behind a form. Reach for Dash,
  Shiny, or Panel for a dashboard people return to.

## Fallback

`make example gradio`, then open <http://localhost:3117>.
