# Part 2 · Patterns that hold across all four types

**Supports:** Part 2, "Open source covers three types well" and "What holds
across all four types". **Needs:** the warehouse, and `make up cube` for the
semantic-layer demo.

## 1. The semantic layer decides accuracy

```sh
examples/part-2/patterns/semantic-layer.sh
```

Last quarter's revenue by region, three ways:

| Region | Raw tables, list price, every line | Warehouse `metrics` views | Cube |
| --- | --- | --- | --- |
| EMEA | about $1.78M | about $1.56M | about $1.56M |
| North America | about $3.15M | about $2.68M | about $2.68M |
| APAC | about $1.14M | about $974K | about $974K |
| LATAM | about $478K | about $423K | about $423K |

EMEA's target was about $1.74M. **On the raw tables, EMEA beat its target.
On either semantic layer, it missed by about $181K.** The two semantic layers
agree to the dollar; the small difference is where each one rounds.

**Point out:** the definition lives in one place, and every tool and agent
that asks gets the same answer. Without it, the answer depends on who wrote
the query.

### Demo prompt

In Claude Code, with the lab running:

```text
Run examples/part-2/patterns/semantic-layer.sh and explain why the first
table disagrees with the other two. Which one should a dashboard use, and
why?
```

**Expected:** the raw query counts refunded and canceled orders and ignores
discounts; use the semantic layer.

## 2. License matters most when you embed

Every tool in the lab, from `make list`:

| License | Tools | Embed in a product? |
| --- | --- | --- |
| Apache 2.0 | Superset, ClickHouse, OpenSearch Dashboards, Rill, Cube, Holotable, Streamlit, marimo | Yes. Keep the notices |
| MIT | Lightdash (outside its enterprise folder), Evidence | Yes. Keep the notice |
| AGPL-3.0 | Grafana, Metabase | Review first. Modifying it or offering it over a network brings obligations |

**Demo:** `make example superset-embed`. Superset is embedded in a mock
partner portal with no license question to answer.

## 3. Open core is the catch

Some features live in paid editions. In this lab:

- **Row-level security:** free in Superset (see `part-2/superset`). In
  Metabase it is a paid feature.
- **AI agents:** free in Holotable, Metabase (with your own model), and
  Rill Developer. Lightdash's AI agents are enterprise features.
- **Rill's hosted AI:** Rill Developer's AI falls back to Rill's own hosted
  model service unless you configure your own key.

Check which edition you are actually running before you promise a feature.

## 4. Platforms span types

| Type | Start | Then open |
| --- | --- | --- |
| Strategic | `make up superset evidence` | Superset **Executive KPIs**; Evidence's quarterly report |
| Analytical | `make up superset lightdash` | Superset **Revenue analysis**; Lightdash's **Monthly KPIs** |
| Operational | `make up grafana clickhouse opensearch` | Grafana **Service health**; OpenSearch **Lumen Supply service logs** |
| Generative | `make up holotable` | Holotable, with a model |

Superset shows up twice. Use the four types to pick a tool's primary job,
not to rule tools out.

## 5. AI pricing is moving to consumption

A talking point, not a demo: the lab runs on your own model keys, so you see
every token. Commercial tools increasingly bill AI by tokens or credits,
which is harder to forecast than seats.
