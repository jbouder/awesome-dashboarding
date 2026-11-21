# Awesome Open Source Dashboarding

A field guide to open source dashboarding in the age of AI, plus a lab to run
each tool on your own machine.

Building a dashboard used to take weeks. Now it can take a prompt. This repo
sorts the open source landscape into four dashboard types, says what each
tool is best at and what AI can do with it, and gives you one command per
tool to run it locally against the same seed data. Same data, every tool,
side by side.

> **Try it:** `make up all`, then open the URLs it prints. You need Docker
> with Compose. See [Run them locally](#run-them-locally).

## Contents

- [Why now](#why-now)
- [The four dashboard types](#the-four-dashboard-types)
- [How to read the tables](#how-to-read-the-tables)
- [Strategic](#strategic-are-we-on-track)
- [Analytical](#analytical-why-did-this-happen)
- [Operational](#operational-is-something-wrong-now)
- [Generative](#generative-what-answers-my-question)
- [Generated at runtime vs. AI-built](#generated-at-runtime-vs-ai-built)
- [Coverage by type](#coverage-by-type)
- [Patterns that hold across all four types](#patterns-that-hold-across-all-four-types)
- [Run them locally](#run-them-locally)
- [Seed data](#seed-data)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

## Why now

Three shifts frame everything else in this guide.

- **Chat is the interface.** Conversational analytics went from novelty to
  table stakes. Most tools are assisted or conversational. Few are truly
  agentic yet.
- **Semantic layers decide accuracy.** AI answers are only as trustworthy as
  the metric definitions underneath them.
- **Open source caught up.** Metabase ships AI questions in its free edition.
  Superset, Grafana, and ClickHouse have MCP servers. WrenAI went Apache 2.0.
  Many AI and governance features still sit in paid editions, though.

## The four dashboard types

The classic framing is strategic, analytical, and operational. AI adds a
fourth: generative dashboards, assembled per question by an agent and often
thrown away after.

| Type | Question it answers | Freshness | Interaction | Audience | What matters |
| --- | --- | --- | --- | --- | --- |
| **Strategic** | Are we on track? | Daily to monthly | Glance and review | Executives, leadership | Polish, governance, scheduled delivery |
| **Analytical** | Why did this happen? | Hourly to daily | Explore, drill, slice | Analysts, managers, business users | Semantic layer, self-service, embedding |
| **Operational** | Is something wrong now? | Seconds to minutes | Watch, get alerted, act | Operators, SREs, support | Streaming, alerting, render speed |
| **Generative** | What answers my question? | Whatever the source has | Ask, refine, save or discard | Anyone who can ask | Semantic grounding, auditability |

Audience (internal or customer-facing) and output format (dashboard, report,
data app) cut across all four. Treat them as separate dimensions, not types.
Most tools also span several types. A tool is listed under its primary job.

## How to read the tables

- **License** is the license of the open source edition. AGPL and open-core
  editions need review before you embed or modify them in a product.
- **AI** says what AI can do with the tool today: a built-in assistant, an
  MCP server an agent can call, a semantic layer that grounds answers, or a
  plain-text format that AI writes well.
- **Local** says whether this repo runs the tool for you. A stack name links
  to its tour. *Guide* means a written setup against the lab's data, with no
  container. *TBD* means not yet.
- **Commercial equivalents** are listed once per type, so you can map the
  tools you already know.

### Strategic: are we on track?

Strategic dashboards track a handful of KPIs against targets. Evidence stands
out here: reports are Markdown and SQL in Git, which makes them easy for AI to
write and easy to review.

| Tool | License | Best at | AI | Local |
| --- | --- | --- | --- | --- |
| [Evidence](https://github.com/evidence-dev/evidence) | MIT | Polished reports as code, versioned in Git | Plain Markdown and SQL, easy for AI to write | [`evidence`](stacks/evidence/) |
| [Apache Superset](https://github.com/apache/superset) | Apache 2.0 | KPI dashboards with row-level security in the free build | MCP server | [`superset`](stacks/superset/) |
| [Metabase](https://github.com/metabase/metabase) | AGPL-3.0 | Self-service for non-technical users | Metabot natural-language questions | [`metabase`](stacks/metabase/) |
| [Observable Framework](https://github.com/observablehq/framework) | ISC | Fast static data apps and reports | Code-first, easy for AI to write | TBD |
| [Quarto](https://github.com/quarto-dev/quarto-cli) | MIT | Reports and dashboards from notebooks | Plain-text documents, easy for AI to write | TBD |

**Commercial equivalents:** Power BI, Tableau, Looker Studio, Domo, SAP
Analytics Cloud, MicroStrategy, IBM Cognos.

### Analytical: why did this happen?

The most crowded type. The deciding factors are the semantic layer, how easy
self-service is for non-technical users, and embedding. Notebooks and data app
frameworks belong here too when the analysis needs code.

| Tool | License | Best at | AI | Local |
| --- | --- | --- | --- | --- |
| [Apache Superset](https://github.com/apache/superset) | Apache 2.0 | Drill-down, SQL Lab, embedding with no license obligations | MCP server | [`superset`](stacks/superset/) |
| [Metabase](https://github.com/metabase/metabase) | AGPL-3.0 | Point-and-click question builder | Metabot natural-language questions | [`metabase`](stacks/metabase/) |
| [Lightdash](https://github.com/lightdash/lightdash) | MIT | BI on top of dbt models | dbt metrics give agents a semantic layer | [`lightdash`](stacks/lightdash/) |
| [Cube](https://github.com/cube-js/cube) | Apache 2.0 | Headless semantic layer with SQL, REST, and GraphQL APIs | Grounds any agent in governed metrics | [`cube`](stacks/cube/) |
| [Streamlit](https://github.com/streamlit/streamlit) | Apache 2.0 | Python data apps | The most common target for AI-written apps | [`streamlit`](stacks/streamlit/) |
| [Plotly Dash](https://github.com/plotly/dash) | MIT | Python data apps with fine-grained callbacks | Plain Python, easy for AI to write | TBD |
| [marimo](https://github.com/marimo-team/marimo) | Apache 2.0 | Reactive notebooks that deploy as apps | Built-in AI assistant, notebooks are plain Python | [`marimo`](stacks/marimo/) |

**Commercial equivalents:** Tableau, Looker, Qlik, Sigma, Omni, Hex,
Databricks AI/BI.

### Operational: is something wrong now?

Operational dashboards are only as good as the engine behind them, so this
type mixes dashboards with time-series and real-time OLAP databases. It is the
strongest open source type. Grafana plus ClickHouse, Druid, or TimescaleDB
covers most needs with no license fee.

| Tool | License | Best at | AI | Local |
| --- | --- | --- | --- | --- |
| [Grafana](https://github.com/grafana/grafana) | AGPL-3.0 | Live panels and alerting | MCP server ([mcp-grafana](https://github.com/grafana/mcp-grafana)) | [`grafana`](stacks/grafana/) |
| [OpenSearch Dashboards](https://github.com/opensearch-project/OpenSearch-Dashboards) | Apache 2.0 | Logs and search analytics, the open Kibana fork | Chat assistant plugin ([dashboards-assistant](https://github.com/opensearch-project/dashboards-assistant)) | [`opensearch`](stacks/opensearch/) |
| [Rill](https://github.com/rilldata/rill) | Apache 2.0 | Fast metrics explorer on DuckDB or ClickHouse | Metrics defined as code, easy for AI to write | [`rill`](stacks/rill/) |
| [ClickHouse](https://github.com/ClickHouse/ClickHouse) | Apache 2.0 | Real-time OLAP engine | MCP server ([mcp-clickhouse](https://github.com/ClickHouse/mcp-clickhouse)) | [`clickhouse`](stacks/clickhouse/) |
| [Apache Druid](https://github.com/apache/druid) / [Apache Pinot](https://github.com/apache/pinot) | Apache 2.0 | Real-time OLAP at high ingest rates | Engine only | TBD |
| [InfluxDB](https://github.com/influxdata/influxdb) | MIT / Apache 2.0 | Purpose-built time-series database | Engine only | TBD |

**Commercial equivalents:** Datadog, New Relic, Dynatrace, Grafana Cloud,
Microsoft Fabric Real-Time Intelligence, Tinybird.

### Generative: what answers my question?

Generative dashboards are assembled on demand by an agent. Accuracy depends
more on semantic grounding than on the model. Many open source options here
are libraries and specs you put together yourself. WrenAI is the closest to a
complete platform: Apache 2.0, with a governed semantic layer your agents
use. It is young and changing fast.

| Tool | License | Best at | AI | Local |
| --- | --- | --- | --- | --- |
| [Holotable](https://github.com/jbouder/holotable) | Apache 2.0 | Live natural-language monitoring dashboards | The model writes a validated spec, never the data. SQL is guarded | [`holotable`](stacks/holotable/) |
| [WrenAI](https://github.com/Canner/WrenAI) | Apache 2.0 | Governed text-to-SQL and dashboards for your own agents | Semantic layer and context kept as YAML and Markdown in Git | [Guide](stacks/wrenai/) |
| [Metabase Metabot](https://github.com/metabase/metabase) | AGPL-3.0 | AI questions inside an existing BI tool | Answers become saved Metabase questions | [`metabase`](stacks/metabase/) |
| [Vercel AI SDK](https://github.com/vercel/ai) | Apache 2.0 | Generative UI building blocks | A library, not a platform | Library |
| [A2UI](https://github.com/a2ui-project/a2ui) | Apache 2.0 | Agents stream layout, apps render native components | A framework, not a platform | Library |

**Commercial equivalents:** ThoughtSpot Spotter, Power BI Copilot, Looker
with Gemini, Databricks Genie, Snowflake Intelligence, and general assistants
such as Claude and ChatGPT.

## Generated at runtime vs. AI-built

Ad hoc and custom reporting is one of the biggest shifts AI has caused. A
custom dashboard used to cost days of engineering. Now it takes minutes. It
comes in two flavors with very different costs.

| | Generated at runtime | AI-built |
| --- | --- | --- |
| **What happens** | The tool assembles a dashboard per question, on governed data | AI writes the dashboard as code, once. You own it from there |
| **Open source examples** | Holotable, WrenAI, Metabase Metabot | AI-written Streamlit, Dash, marimo, or Evidence apps. The lab's [Streamlit](stacks/streamlit/) and [marimo](stacks/marimo/) stacks are two |
| **You maintain** | Nothing new | A new app to host, secure, and keep correct |

AI-built reports are fast to build and costly to sprawl.

| Dimension | Strength | Risk |
| --- | --- | --- |
| Speed | Minutes from question to dashboard | Shipped before the numbers are checked |
| Flexibility | Any layout, fits your design system | No consistency across reports |
| Ownership | Code you control, no license | Maintenance lands on the builder |
| Governance | Can sit on a semantic layer | Often raw data, ad hoc metrics |
| Scale | Great for one-offs and prototypes | Sprawl of near-duplicate dashboards |

Governance is the big one. An AI-built dashboard usually queries raw tables
with metrics defined on the spot, so two people asking for revenue can get
two different answers. The lab's Streamlit app shows it: switch it to raw
tables and last quarter's revenue goes from $5.64M to $6.54M.

**Rule of thumb:** use AI-built reports to explore and prototype. Graduate
the good ones into a governed tool.

## Coverage by type

Open source covers three types well. Generative is the youngest.

| Type | Mature tools | Gap |
| --- | --- | --- |
| Strategic | Evidence, Superset, Metabase | Pixel-perfect output is mostly in legacy commercial tools |
| Analytical | Superset, Metabase, Lightdash, Cube | Governance is often in paid editions |
| Operational | Grafana, OpenSearch, Rill, ClickHouse | Few gaps. Strongest type |
| **Generative** | Holotable, WrenAI, Metabase Metabot | **Few complete platforms. Most options are libraries you assemble** |

## Patterns that hold across all four types

- **The semantic layer decides accuracy.** Grounded in governed metrics, AI
  answers hold up. Over raw tables, they drift. Cube, Lightdash on dbt, and
  WrenAI's model all ground an agent before it writes SQL.
- **License matters most when you embed.** Apache 2.0, MIT, and ISC embed
  freely. AGPL needs review. Superset, Cube, Rill, and ECharts are
  permissive. Metabase and Grafana are AGPL. Licenses change, so check the
  repository before you commit.
- **Open core is the catch.** Row-level security, SSO, and AI features often
  live in paid editions. Check which edition you are actually running.
- **Bring your own model.** Open source AI features mostly take an API key or
  a local model. Your data, your model choice, and your token bill.
- **Tools span types.** Superset does strategic and analytical. Grafana does
  operational. Holotable does generative. Pick by primary job, not to rule
  tools out.

## Run them locally

You need Docker with Compose v2 and `make`. Running every stack at once takes
about 8 GB of memory for Docker. A few at a time need much less. The first
start downloads every image, about 40 GB on disk, which takes a while.
`make up superset` downloads only what Superset needs. After that,
`make up all` is ready in about two and a half minutes, most of it Lightdash.

```sh
git clone https://github.com/jbouder/awesome-dashboarding.git
cd awesome-dashboarding
make doctor                # check Docker, memory, ports, and tools
make up all                # start every stack, seed data loaded
make smoke                 # check every stack works and agrees on the numbers
make open all              # open them in the browser
```

Run `make help` for every command. The ones you will use most:

| Command | What it does |
| --- | --- |
| `make up superset grafana` | Start some stacks. Stacks already running keep running |
| `make stop metabase` | Stop one stack and keep its data |
| `make status` | Each stack's state, and whether its URL responds |
| `make story` | The questions to ask every tool, and the warehouse's answer |
| `make incident` | Three minutes of errors on checkout. Watch Grafana's alert fire |
| `make psql` | A read-only SQL shell on the warehouse |
| `make sql Q="SELECT ..."` | Run one query on the warehouse |
| `make env` | Create `.env` from `.env.example`, to add a model |
| `make down` | Stop everything and keep the data |
| `make reset` | Stop everything and delete all data |

| Stack | Type | URL | Sign-in | Tour |
| --- | --- | --- | --- | --- |
| Superset | Strategic, analytical | <http://localhost:8088> | `admin` / `admin` | [stacks/superset](stacks/superset/) |
| Metabase | Strategic, analytical | <http://localhost:3002> | `admin@dashlab.local` / `dashlab-admin-1` | [stacks/metabase](stacks/metabase/) |
| Lightdash | Analytical | <http://localhost:8080> | `admin@dashlab.local` / `dashlab-admin-1` | [stacks/lightdash](stacks/lightdash/) |
| Evidence | Strategic | <http://localhost:3005> | `lab` / `lab` | [stacks/evidence](stacks/evidence/) |
| Grafana | Operational | <http://localhost:3001> | None to view, `admin` / `admin` to edit | [stacks/grafana](stacks/grafana/) |
| ClickHouse | Operational engine | <http://localhost:8123/play> | `lab` / `lab` | [stacks/clickhouse](stacks/clickhouse/) |
| OpenSearch Dashboards | Operational, logs | <http://localhost:5601> | None | [stacks/opensearch](stacks/opensearch/) |
| Rill | Analytical, operational | <http://localhost:9009> | None | [stacks/rill](stacks/rill/) |
| Holotable | Generative | <http://localhost:3000> | None | [stacks/holotable](stacks/holotable/) |
| Cube | Semantic layer | <http://localhost:4000> | None | [stacks/cube](stacks/cube/) |
| Streamlit | AI-built app | <http://localhost:3003> | None | [stacks/streamlit](stacks/streamlit/) |
| marimo | AI-built app | <http://localhost:3004> | None | [stacks/marimo](stacks/marimo/) |
| WrenAI | Generative | Your own agent | | [stacks/wrenai](stacks/wrenai/) |

These are local test passwords. Every port is bound to `127.0.0.1`, so
nothing is reachable from your network. Do not reuse them elsewhere.

### How it fits together

```text
              ┌───────────────────────── warehouse (TimescaleDB) ─────────────────────────┐
  seed ─────▶ │ shop.*     raw tables: customers, products, orders, order_items, targets │
  (one-shot)  │ metrics.*  semantic layer: one view per metric definition               │
  stream ───▶ │ ops.*      live service metrics every 5 s, and incidents                │
              └──────────────────────────────────▲───────────────────────────────────┘
                                                 │                        all read-only
      Superset, Metabase, Lightdash, Evidence, Grafana, ClickHouse,   as lab_ro
      OpenSearch (logs), Rill, Holotable, Cube, Streamlit, marimo
```

- `core/` is the shared data layer. It always starts.
- `stacks/<name>/` holds one tool: its `compose.yaml`, any config, a setup
  script that connects it to the warehouse and builds starter dashboards, and
  a README with the tour.
- `scripts/lab.sh` is what `make` runs. Each stack is a Compose profile, so
  stacks start and stop independently on one shared network.

### Generative stacks need a model

Copy `.env.example` to `.env` and set `LLM_BASE_URL`, `LLM_API_KEY`, and
`LLM_MODEL`. Any OpenAI-compatible endpoint works, including Anthropic's and
a local Ollama with no key. Holotable and Metabase's Metabot use it. marimo's
editor and Rill have their own AI settings. Without
a model, every stack still starts and every saved dashboard still loads.

## Seed data

Every stack reads the same synthetic dataset from one warehouse. It is
generated from a fixed random seed, so the same seed on the same day gives
the same numbers. Dates run up to today.

- **Lumen Supply**, a made-up online retailer of outdoor and home gear: about
  57,000 orders over two years, 6,000 customers, 60 products in 6 categories,
  4 regions, 3 channels, and a monthly revenue target per region.
- **A semantic layer** in schema `metrics`: revenue, margin, orders, active
  customers, average order value, attainment, error rate, and latency, each
  defined once as a view. [`semantic/metrics.yml`](semantic/metrics.yml)
  documents every definition.
- **Live service metrics** in schema `ops`: requests, errors, and p95
  latency for five services, written every 5 seconds. `make incident` makes
  one service fail so you can watch an alert fire.

The data has a story to find. Ask every tool **"Which region missed its
revenue target last quarter, and why?"** EMEA came in about 10% under target,
because orders through its partner channel fell by about two thirds. A tool
that finds the partner channel has done real analysis. Then ask the same
question against the raw `shop` tables and see whether the answers still
agree.

`make reseed` regenerates the data, for example after changing `SEED` in
`.env`.

## Roadmap

1. **Guide.** This README. Done.
2. **Local lab.** Shared warehouse, seed data, live metrics, and stacks for
   Superset, Metabase, Grafana, Rill, Holotable, Cube, Streamlit, and marimo,
   plus a WrenAI guide. Done.
3. **High-profile stacks.** Lightdash, Evidence, ClickHouse, and OpenSearch
   Dashboards. Done. Everything still marked *TBD* waits on demand.
4. **Comparison scripts.** One set of questions run against each tool, with
   the answers collected side by side.

## Contributing

Corrections and additions are welcome. Open an issue or a pull request.

- Add only open source tools to the type tables. Commercial tools go in the
  one-line equivalents.
- Fill in every column, including what AI can do with the tool. "None yet" is
  a fine answer.
- A new stack goes in `stacks/<name>/` with a `compose.yaml` behind a profile
  of the same name, a setup script that connects it to the warehouse as
  `lab_ro`, and a README with a tour. Register it in `scripts/lab.sh` and
  `compose.yaml`, and add its checks to `scripts/smoke.py`. Before opening a
  pull request, run `make lint`, then `make reset && make up <name> && make
  smoke`.
- List a tool that fits several types under its primary job.
- Link to the project's own repository, not a review or a listicle.
- Keep it neutral. Say what a tool does well and where it falls short.

## License

[Apache 2.0](LICENSE). Tool names and trademarks belong to their owners.
