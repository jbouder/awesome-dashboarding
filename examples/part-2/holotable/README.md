# Part 2 · Holotable: asking for a dashboard

**Supports:** Part 2, Demo 3. **Type:** generative. **Needs:** `make up
holotable` (<http://localhost:3000>, no sign-in) and a model.

Ask a business question in plain language, watch the dashboard assemble from
governed data, refine it with a follow-up, then save it or throw it away.

## Set up the model

Generation needs a model. Holotable takes any OpenAI-compatible endpoint.

```sh
make env                      # creates .env from .env.example
# edit .env: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
make restart holotable
```

For Anthropic, `LLM_BASE_URL=https://api.anthropic.com/v1/` and a Claude
model ID. For a local Ollama, `LLM_BASE_URL=http://host.docker.internal:11434/v1`
and no key. Check it before the talk: run the demo prompt once.

## The demo

1. Open **Data sources**. Point at **Lumen Supply (semantic layer)**: the
   views in schema `metrics`, each with a description the model reads.
   Press **Test** to show it is read-only.
2. Start a new dashboard on that source and type the demo prompt from
   `prompts.md`.
3. Watch it assemble. Then the follow-ups.
4. Save it. Reload the page: it loads without calling the model again.
5. Open **Lumen Supply: executive overview**, the dashboard the lab seeds.
   It is the reference answer. Compare the numbers: EMEA at 89.6% in both.

## Files

| File | What it is |
| --- | --- |
| `prompts.md` | The demo prompt, follow-ups, and the build prompt for the seeded dashboards |
| `reference-spec.json` | The spec of the seeded executive overview: what a good answer to the demo prompt looks like. Drill links are removed, since they name dashboard ids from one install |

The three seeded dashboards come from `stacks/holotable/dashboards.py`. See
`stacks/holotable/README.md` for their drill-down.

## What to point out

- **Generated at runtime, on governed data.** The model never sees a row.
  It writes a spec; Holotable checks the SQL, runs it, and streams results.
- **Saved means saved.** Refreshes run the SQL again, not the model. No
  token cost to view a dashboard.
- **Same answer as everyone else.** Because the source is the semantic
  layer, the numbers match Superset, Metabase, and Part 1.
- **The open source gap.** This is the type with no complete, governed,
  permissively licensed platform. Holotable is our exploration of it.

## Fallback

If the model is slow or down, open the seeded **Lumen Supply: executive
overview** and walk through its drill-down instead.
