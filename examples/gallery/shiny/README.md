# Shiny for Python · Lumen Supply dashboard

**Types:** analytical, operational. **Needs:** the lab warehouse.
`make example shiny` runs it at <http://localhost:3113>.

The Lumen Supply dashboard from [`_shared/spec.md`](../../_shared/spec.md),
built in Shiny for Python. KPIs for the last full quarter, revenue against
target by month, attainment by region, revenue by channel, top products,
and a live error-rate panel. Click a region bar or a channel band to filter
what is below it. Every query reads the `metrics` views.

## Files

| File | What it is |
| --- | --- |
| `prompts.md` | The demo prompt, follow-ups, and the build prompt |
| `app/app.py` | The app. Queries, Plotly charts, and the reactive graph. About 590 lines |
| `app/requirements.txt` | Pinned `shiny`, `psycopg[binary]`, `pandas`, `plotly` |
| `app/Dockerfile`, `compose.yaml` | How `make example shiny` runs it on port 3113 |

## Signature: what-if with fine-grained reactivity

The last card has two sliders: **target uplift** and **partner revenue
recovered**. Three reactive calcs sit behind them. One holds the quarter's
base numbers. One applies the uplift to the targets. One works out how much
lost partner revenue comes back.

Each output reads only the calcs it needs. Move the uplift slider and the
"quarter target" line and the scenario table re-run. The "adds revenue"
line does not. Each output prints how many times it has run, so the room
can see it. No callbacks are wired by hand. Shiny tracks the dependencies.

## What to point out

- **Reactivity you do not wire.** Outputs re-run when what they read
  changes, and only then. Compare that with Streamlit, which re-runs the
  whole script on every click.
- **The live panel is one line.** `reactive.invalidate_later(5)` refreshes
  the error-rate chart every 5 seconds and touches nothing else.
- **Light and dark come from Bootstrap.** `input_dark_mode()` flips the
  page, and the charts read it as an input and redraw in the dark palette.
- **The cost is plumbing.** Clickable Plotly charts need a few lines of
  JavaScript that call `Shiny.setInputValue`. `shinywidgets` is the
  packaged route, at the price of another dependency.
- **The image compiles libsass** on Linux arm64, where no wheel exists. The
  first build takes a few minutes.
- **R heritage.** Shiny has a long track record in R. The Python port is
  younger, with a smaller set of components.

## Fallback

`make example shiny`, then open <http://localhost:3113>.
