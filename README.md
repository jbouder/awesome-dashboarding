# Awesome Open Source Dashboarding

A field guide to open source dashboarding in the age of AI, plus a lab to run
each tool on your own machine.

Building a dashboard used to take weeks. Now it can take a prompt. This repo
sorts the open source landscape into four dashboard types, says what each
tool is best at and what AI can do with it, and (soon) gives you one command
per tool to run it locally against the same seed data. Same data, every tool,
side by side.

> **Status:** the guide is here. The local lab (Dockerfiles, Compose stacks,
> seed data, scripts) is in progress. See [Roadmap](#roadmap).

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
- **Local** says whether this repo runs the tool for you. *Planned* means it
  is on the roadmap. A check means the stack ships today.
- **Commercial equivalents** are listed once per type, so you can map the
  tools you already know.

### Strategic: are we on track?

Strategic dashboards track a handful of KPIs against targets. Evidence stands
out here: reports are Markdown and SQL in Git, which makes them easy for AI to
write and easy to review.

| Tool | License | Best at | AI | Local |
| --- | --- | --- | --- | --- |
| [Evidence](https://github.com/evidence-dev/evidence) | MIT | Polished reports as code, versioned in Git | Plain Markdown and SQL, easy for AI to write | Planned |
| [Apache Superset](https://github.com/apache/superset) | Apache 2.0 | KPI dashboards with row-level security in the free build | MCP server | Planned |
| [Metabase](https://github.com/metabase/metabase) | AGPL-3.0 | Self-service for non-technical users | Metabot natural-language questions | Planned |
| [Observable Framework](https://github.com/observablehq/framework) | ISC | Fast static data apps and reports | Code-first, easy for AI to write | Planned |
| [Quarto](https://github.com/quarto-dev/quarto-cli) | MIT | Reports and dashboards from notebooks | Plain-text documents, easy for AI to write | Planned |

**Commercial equivalents:** Power BI, Tableau, Looker Studio, Domo, SAP
Analytics Cloud, MicroStrategy, IBM Cognos.

### Analytical: why did this happen?

The most crowded type. The deciding factors are the semantic layer, how easy
self-service is for non-technical users, and embedding. Notebooks and data app
frameworks belong here too when the analysis needs code.

| Tool | License | Best at | AI | Local |
| --- | --- | --- | --- | --- |
| [Apache Superset](https://github.com/apache/superset) | Apache 2.0 | Drill-down, SQL Lab, embedding with no license obligations | MCP server | Planned |
| [Metabase](https://github.com/metabase/metabase) | AGPL-3.0 | Point-and-click question builder | Metabot natural-language questions | Planned |
| [Lightdash](https://github.com/lightdash/lightdash) | MIT | BI on top of dbt models | dbt metrics give agents a semantic layer | Planned |
| [Cube](https://github.com/cube-js/cube) | Apache 2.0 | Headless semantic layer with SQL, REST, and GraphQL APIs | Grounds any agent in governed metrics | Planned |
| [Streamlit](https://github.com/streamlit/streamlit) | Apache 2.0 | Python data apps | The most common target for AI-written apps | Planned |
| [Plotly Dash](https://github.com/plotly/dash) | MIT | Python data apps with fine-grained callbacks | Plain Python, easy for AI to write | Planned |
| [marimo](https://github.com/marimo-team/marimo) | Apache 2.0 | Reactive notebooks that deploy as apps | Built-in AI assistant, notebooks are plain Python | Planned |

**Commercial equivalents:** Tableau, Looker, Qlik, Sigma, Omni, Hex,
Databricks AI/BI.

### Operational: is something wrong now?

Operational dashboards are only as good as the engine behind them, so this
type mixes dashboards with time-series and real-time OLAP databases. It is the
strongest open source type. Grafana plus ClickHouse, Druid, or TimescaleDB
covers most needs with no license fee.

| Tool | License | Best at | AI | Local |
| --- | --- | --- | --- | --- |
| [Grafana](https://github.com/grafana/grafana) | AGPL-3.0 | Live panels and alerting | MCP server ([mcp-grafana](https://github.com/grafana/mcp-grafana)) | Planned |
| [OpenSearch Dashboards](https://github.com/opensearch-project/OpenSearch-Dashboards) | Apache 2.0 | Logs and search analytics, the open Kibana fork | Chat assistant plugin ([dashboards-assistant](https://github.com/opensearch-project/dashboards-assistant)) | Planned |
| [Rill](https://github.com/rilldata/rill) | Apache 2.0 | Fast metrics explorer on DuckDB or ClickHouse | Metrics defined as code, easy for AI to write | Planned |
| [ClickHouse](https://github.com/ClickHouse/ClickHouse) | Apache 2.0 | Real-time OLAP engine | MCP server ([mcp-clickhouse](https://github.com/ClickHouse/mcp-clickhouse)) | Planned |
| [Apache Druid](https://github.com/apache/druid) / [Apache Pinot](https://github.com/apache/pinot) | Apache 2.0 | Real-time OLAP at high ingest rates | Engine only | Planned |
| [InfluxDB](https://github.com/influxdata/influxdb) | MIT / Apache 2.0 | Purpose-built time-series database | Engine only | Planned |

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
| [Holotable](https://github.com/jbouder/holotable) | Apache 2.0 | Live natural-language monitoring dashboards | The model writes a validated spec, never the data. SQL is guarded | Planned |
| [WrenAI](https://github.com/Canner/WrenAI) | Apache 2.0 | Governed text-to-SQL and dashboards for your own agents | Semantic layer and context kept as YAML and Markdown in Git | Planned |
| [Metabase Metabot](https://github.com/metabase/metabase) | AGPL-3.0 | AI questions inside an existing BI tool | Answers become saved Metabase questions | Planned |
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
| **Open source examples** | Holotable, WrenAI, Metabase Metabot | AI-written Streamlit, Dash, marimo, or Evidence apps |
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
two different answers.

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

> **Coming soon.** This section describes the target experience. The stacks
> are not in the repo yet.

The goal: one prerequisite (Docker with Compose v2), one command per tool,
every tool loaded with the same seed data.

```sh
git clone https://github.com/jbouder/awesome-dashboarding.git
cd awesome-dashboarding
make list              # every stack, its type, port, and license
make up superset       # start one tool with seed data loaded
make up grafana        # start another alongside it
make down              # stop everything
make reset             # stop everything and delete volumes
```

Each tool lives in its own folder under `stacks/` with a `compose.yaml`, any
Dockerfiles it needs, a seed step, and a short README with the login, the
port, and a guided tour. Stacks share one data service, so you can run two
side by side and compare their answers.

Generative stacks need a model. They take an Anthropic or OpenAI-compatible
API key from `.env`, or run a local model through Ollama with no key.

## Seed data

> **Coming soon.**

Every stack loads the same synthetic dataset, generated from a fixed random
seed so results match from run to run. The plan:

- **Business tables** for strategic and analytical views: customers,
  products, orders, order items, subscriptions, and monthly targets, covering
  about two years.
- **A live event stream** for operational views: request rates, latency, and
  errors written every few seconds, with a script to trigger an incident on
  demand so you can watch an alert fire.
- **A semantic model** that defines core metrics (revenue, active customers,
  churn, error rate) once, so generative tools can be compared grounded and
  ungrounded.

The same question asked of every tool, such as "What drove the drop in
revenue last quarter?", is the fastest way to see how they differ.

## Roadmap

1. **Guide.** This README. Done.
2. **Local lab.** Seed data generator, shared data service, a Compose stack
   and seed step per tool, a `Makefile`, and per-stack READMEs.
3. **Comparison scripts.** One set of questions run against each tool, with
   the answers collected side by side.

## Contributing

Corrections and additions are welcome. Open an issue or a pull request.

- Add only open source tools to the type tables. Commercial tools go in the
  one-line equivalents.
- Fill in every column, including what AI can do with the tool. "None yet" is
  a fine answer.
- List a tool that fits several types under its primary job.
- Link to the project's own repository, not a review or a listicle.
- Keep it neutral. Say what a tool does well and where it falls short.

## License

[Apache 2.0](LICENSE). Tool names and trademarks belong to their owners.
