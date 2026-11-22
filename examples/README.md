# Examples

Examples for the two "Dashboarding in the Age of AI" talks, and a gallery of
the same dashboard built in seven frameworks. Every example has the prompts
that build it, a short demo prompt to type live, a reference build to fall
back on, and a README with what to point out.

Start with the shared files:

| File | What it is |
| --- | --- |
| [`_shared/context.md`](_shared/context.md) | The data, the metric definitions, the known answers, and the design rules. Attach it to any prompt |
| [`_shared/spec.md`](_shared/spec.md) | The Lumen Supply dashboard every gallery framework builds |
| [`_shared/design-tokens.css`](_shared/design-tokens.css) | One palette and type scale, light and dark |
| `_shared/snapshot.json` | Aggregates the static examples embed. `make extract` writes it |

## Commands

```sh
make extract              # refresh the CSV extracts and every embedded snapshot
make examples             # every runnable example and its URL
make example static       # serve the static examples at http://localhost:3102
make example dash panel   # start runnable examples
```

## Part 1: ad hoc dashboarding with AI

Run of show: [`part-1/RUNBOOK.md`](part-1/RUNBOOK.md).

| Example | Slide | Run |
| --- | --- | --- |
| [01 · Claude artifact](01-claude-artifact/) | Demo 1 | A Claude chat with the attached extract |
| [02 · Static HTML](02-static-html/) | Demo 2 | `make example static`, or GitHub Pages |
| [03 · Streamlit](03-streamlit/) | Demo 3 | `make example streamlit-demo` |
| [04 · Chart libraries](04-chart-libraries/) | Chart libraries | `make example static`, or GitHub Pages |
| [05 · Two answers](05-two-answers/) | Tradeoffs, foundations | `compare.sql` against the warehouse |

## Gallery: one dashboard, seven frameworks

Each builds [`_shared/spec.md`](_shared/spec.md), plus one signature section
that shows what that framework does best.

| Framework | Run | URL |
| --- | --- | --- |
| [Panel](gallery/panel/) | `make example panel` | <http://localhost:3111> |
| [Plotly Dash](gallery/dash/) | `make example dash` | <http://localhost:3112> |
| [Shiny for Python](gallery/shiny/) | `make example shiny` | <http://localhost:3113> |
| [marimo](gallery/marimo/) | `make example marimo` | <http://localhost:3114> |
| [Streamlit](gallery/streamlit/) | `make example streamlit` | <http://localhost:3115> |
| [Observable Framework](gallery/observable/) | `make example observable` | <http://localhost:3116> |
| [Gradio](gallery/gradio/) | `make example gradio` | <http://localhost:3117> |

## Part 2: dashboard platforms in the age of AI

Run of show: [`part-2/RUNBOOK.md`](part-2/RUNBOOK.md). Examples are in
[`part-2/`](part-2/).
