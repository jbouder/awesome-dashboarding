# Holotable

**Type:** generative. **License:** Apache 2.0.
**URL:** <http://localhost:3000>. No sign-in: in local mode you are the
owner.

```sh
make up holotable
```

Generating dashboards needs a model. Set `LLM_BASE_URL`, `LLM_API_KEY`, and
`LLM_MODEL` in `.env` (see `.env.example`), then run `make up holotable`
again. Without a model, saved dashboards, the live viewer, and the SQL editor
still work.

## What the lab sets up

- Holotable's quickstart image, with its own TimescaleDB and demo dashboards.
- Two sources on the lab warehouse, registered by `register.py` as the
  read-only `lab_ro` role:
  - **Lumen Supply (semantic layer)**: the views in schema `metrics`, each
    with a description the model reads.
  - **Lumen Supply (live service metrics)**: `ops.request_metrics` and
    `ops.incidents`.
- Three linked dashboards, defined in `dashboards.py`:
  - **Lumen Supply: executive overview**: last quarter's revenue,
    attainment, and orders, attainment by region as bars, revenue against
    target, a treemap of revenue by region and channel, and a region table.
    **Click a region** in the bars, the treemap, or the table to drill into
    its detail. A panel menu link opens service health.
  - **Lumen Supply: region detail**: region and channel pickers, KPIs,
    revenue against target, revenue by channel per quarter, a flow from
    channel to segment to category, a segment donut, weekly revenue, and top
    products. **Click a channel** in a chart or the flow to filter the whole
    dashboard to it.
  - **Lumen Supply: service health**: live, every 5 seconds. A tile per
    service, error rate, latency, and traffic by service, and recent
    incidents. **Click a service** to show only it.

The model sees table and column names and descriptions, never rows. It
writes a dashboard spec. Holotable checks the SQL, runs it, and streams the
results. Refreshing a panel runs the SQL again. It does not call the model
again. The seeded dashboards need no model at all.

## Tour

1. Open **Dashboards → Lumen Supply: executive overview**. EMEA is the red
   bar.
2. Click EMEA. The region detail opens filtered to EMEA.
3. In **Revenue by channel, last four full quarters**, click the thin partner
   slice of the last bar. Every panel narrows to the partner channel. Put it
   back with the Channel picker.
4. Open **Lumen Supply: service health** and run `make incident`. The
   checkout tile turns red within a minute.
5. With a model set, ask for a new dashboard on **Lumen Supply (semantic
   layer)**: "Which region missed its revenue target last quarter, and why?"
   Compare what it builds with the seeded dashboards.

## Change the seeded dashboards

Edit them in Holotable and your edits are kept. To reset them to the specs in
`dashboards.py`, run:

```sh
HOLOTABLE_REBUILD=1 make restart holotable
```

## Compare

Ask the same question in Metabase's Metabot, through Superset's MCP server,
and with WrenAI. Check each answer against the Executive KPIs dashboard in
Superset. The tools that use the `metrics` views should agree.
