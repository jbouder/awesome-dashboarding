# Examples plan

Examples for both talks in the "Dashboarding in the Age of AI" series, and
a gallery of framework examples built to one shared dashboard spec. Every
example comes with the prompts that build it and a short prompt to run live.

Status: built, November 22, 2026. Everything below is in `examples/`. The one open item:
`examples/part-2/ai-answers` needs answers recorded with a model at rehearsal.

## Decisions

| Question | Decision |
| --- | --- |
| Data for the artifact demos | Both: a raw extract, so the assistant defines revenue itself, and a semantic-layer extract for the governed version |
| GitHub Pages | On. A workflow publishes the static examples. The data is synthetic |
| Frameworks | Panel, Plotly Dash, Shiny for Python, marimo, Streamlit, Observable Framework, and Gradio (small, and it says why) |
| Assistants | Reference builds recorded with Claude and Claude Code only. Prompts work elsewhere, unrecorded |

## What every example has

- **Build prompt.** The full prompt that produces the reference build. Long
  and exact, so anyone can reproduce the example.
- **Demo prompt.** The short prompt to type live. It finishes in about a
  minute and comes with the expected result, one or two follow-ups in
  order, what to point out, and the fallback to open if the live run stalls.
- **Reference build.** The result, committed, as the demo fallback. Written
  from the build prompt with Claude. A live run will differ in the details.
- **README.** Which slide it supports, how to run it, what to point out, and
  a screenshot.
- **Smoke check.** `make smoke` checks that it serves and that its numbers
  match the warehouse.

Every prompt uses the lab data, so every answer can be checked against the
same known numbers: last quarter's revenue of $5.64M at 98.6% of target, and
EMEA at 89.6% because its partner revenue fell about two thirds.

## Layout

```text
examples/
  README.md              index of every example
  _shared/
    spec.md              the dashboard every framework builds
    context.md           schema, metric definitions, design rules, to attach to prompts
    design-tokens.css    one palette and type scale, light and dark
  part-1/RUNBOOK.md      run of show: slide, command, prompt, what to point out, fallback
  part-2/RUNBOOK.md
  01-claude-artifact/    prompts, extracts, result.html
  02-static-html/        prompts, index.html, published by the Pages workflow
  03-streamlit/          prompts for Claude Code, app/
  04-chart-libraries/    one page, six libraries, a prompt for each
  05-two-answers/        raw tables against the semantic layer
  gallery/
    panel/ dash/ shiny/ marimo/ streamlit/ observable/ gradio/
  part-2/
    superset/ grafana/ holotable/ ai-answers/ patterns/
```

Runnable examples get `make example <name>`, separate from the platform
stacks' `make up`.

## The shared spec

Every gallery framework builds the same **Lumen Supply dashboard**:

- A KPI row: revenue, target, attainment, and orders for the last full
  quarter, each against the quarter before.
- Revenue against target by month.
- Attainment by region. Clicking a region drills into it.
- Revenue by channel by quarter. Clicking a channel filters the page.
- Top products, with search and sorting.
- A live panel: error rate by service, refreshed every 5 seconds.

The bar for professional: one set of design tokens, consistent number
formats, light and dark themes, loading and empty states, colors that pass
contrast and do not rely on hue alone, and a header that says how fresh the
data is.

## Phases

### 1. Foundation

- `examples/_shared/`: the spec, the context pack, the design tokens.
- `make extract`: writes the raw and semantic-layer CSV extracts.
- `make example <name>` and the example smoke checks.

### 2. Part 1 demos

| Slide | Example | Demo prompt, in short |
| --- | --- | --- |
| Demo 1 · Claude artifact | `01-claude-artifact` | Attach the raw extract and ask which region missed its revenue target last quarter and why, as an interactive dashboard. Follow-ups: drill into EMEA by channel, then publish |
| Demo 2 · Static HTML | `02-static-html` | Turn the Demo 1 dashboard into one self-contained HTML file. Then open it locally and push it to Pages |
| Demo 3 · Streamlit | `03-streamlit` | In Claude Code: a Streamlit app on the warehouse for the same question. Follow-up: add a region filter and a chart |
| Chart libraries | `04-chart-libraries` | The same chart, EMEA revenue by channel by quarter, in Vega-Lite, ECharts, Recharts with shadcn, Plotly, D3, and uPlot (weekly revenue). The page shows each one's code length |
| Tradeoffs, foundations | `05-two-answers` | Ask for last quarter's revenue from the raw tables, then from the semantic layer. $6.54M against $5.64M |

Plus `part-1/RUNBOOK.md`.

### 3. Framework gallery

The shared spec in Panel, Plotly Dash, Shiny for Python, marimo, Streamlit,
Observable Framework, and Gradio. Each has a build prompt for Claude Code, a
demo prompt that adds or changes one section, and a `make example` command.

### 4. Part 2 examples

| Slide | Demo | To add | Where the demo prompt goes |
| --- | --- | --- | --- |
| Demo 1 · Superset | KPIs, drill by region, SQL Lab, row-level security, embedding | Row-level security (a role that sees only EMEA), an embedded-dashboard page, and a checked drill-by step. Built first in this phase | An agent connected to Superset's MCP server |
| Demo 2 · Grafana | Live dashboard, an alert firing, the query behind a panel | A runbook with timings, the ClickHouse version, and Grafana's MCP server ([mcp-grafana](https://github.com/grafana/mcp-grafana)) in the stack | An agent connected to mcp-grafana |
| Demo 3 · Holotable | Ask, assemble, refine, save | Prompts, a reference spec of a good answer, model setup steps | Holotable itself |
| Optional · Claude artifact | A 60-second AI-built report | Reuse Part 1's Demo 1, plus a compare-the-numbers step | Claude |
| Open source coverage | One platform per type | A tour that opens one stack per type | None |
| Patterns | Semantic layers, licensing, open core | The same question through Cube, raw SQL, and the views | Claude Code |

`part-2/ai-answers/` asks every AI feature in the lab the same question, and
records what each answered against the known answer: Holotable, Metabot,
Superset and ClickHouse through MCP, WrenAI, and the AI in Lightdash and Rill
if their free versions have it. Tools whose free version has no AI say so.

Plus `part-2/RUNBOOK.md`, with a pre-talk checklist: `make up superset
grafana holotable`, `make smoke`, and a test call to the model.

## Where each stack's demo prompt goes

| Stack | Where you type it |
| --- | --- |
| Holotable, Metabase, Rill, Lightdash | The tool's own AI, where the free version has one |
| Superset, ClickHouse, Grafana | An agent connected to the tool's MCP server |
| Evidence, Cube, WrenAI, and every gallery framework | Claude Code in the repo, adding or changing one section |
| OpenSearch Dashboards | Its assistant plugin, if it runs without a model service. Otherwise an agent querying OpenSearch |
