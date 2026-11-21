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

The model sees table and column names and descriptions, never rows. It
writes a dashboard spec. Holotable checks the SQL, runs it, and streams the
results. Refreshing a panel runs the SQL again. It does not call the model
again.

## Tour

1. Open **Data sources**. Both lab sources are listed. Press **Test** on one
   to see the read-only check pass.
2. Create a dashboard on **Lumen Supply (semantic layer)** and ask:
   "Which region missed its revenue target last quarter, and why?"
3. Refine it: "Break EMEA down by channel."
4. Create one on **Lumen Supply (live service metrics)** and ask: "Error rate
   and p95 latency per service, live." Then run `make incident` and watch it.
5. Save a dashboard, reload it, and note that it loads without the model.

## Compare

Ask the same question in Metabase's Metabot, through Superset's MCP server,
and with WrenAI. Check each answer against the Executive KPIs dashboard in
Superset. The tools that use the `metrics` views should agree.
