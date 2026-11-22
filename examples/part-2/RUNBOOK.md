# Part 2 runbook: dashboard platforms in the age of AI

Run of show for "Dashboarding in the Age of AI" (Part 2). Each demo lists
the command, the prompt, what to point out, and the fallback. Full prompts
are in each example's `prompts.md`.

## Before the talk

- [ ] `make up superset grafana holotable` (add `clickhouse cube` for the
      patterns), then `make example superset-embed`.
- [ ] `make smoke`. Every check passes.
- [ ] A model in `.env` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`), then
      `make restart holotable`. Run the Holotable demo prompt once.
- [ ] Optional agent demos: in Claude Code,
      `claude mcp add --transport http superset http://localhost:5008/mcp`
      and `claude mcp add --transport http grafana http://localhost:5010/mcp`.
- [ ] Open tabs: Superset (signed in as `admin`), Grafana, Holotable, the
      partner portal at <http://localhost:3121>.
- [ ] Know the answers: **$5.64M**, **98.6%**, **EMEA 89.6%**, about
      **$181K** short, partner **$297K → $94K**.

## Slides

| Slide | Do | Time |
| --- | --- | --- |
| Why now, four types, the type slides | Talk | 10 min |
| Generated vs. AI-built, tradeoffs | Talk. Point back to Part 1 | 4 min |
| Demos | Three demos below | 15 min |
| Open source coverage | `part-2/patterns`, section 4 | 2 min |
| Patterns | `part-2/patterns`, sections 1 to 3 | 5 min |
| Discussion | | |

## Demo 1 · Superset · `part-2/superset`

1. **Executive KPIs**: $5.64M, 98.6%, EMEA at 89.6%.
2. **Revenue analysis**: EMEA revenue by channel, partner shrinking.
3. **SQL Lab**: the attainment query from the README.
4. Sign out, sign in as `emea` / `emea-viewer-1`: the same dashboard, EMEA
   only.
5. <http://localhost:3121>: pick **EMEA** in the portal's header. Guest
   token, row-level security, no credentials in the browser.

**Optional agent prompt:**

```text
Using the Superset tools, which region missed its revenue target last
quarter, and by how much? Use the Lab warehouse datasets and show me the
SQL you ran.
```

**Fallback:** if embedding fails, step 4 shows the same filtering.

## Demo 2 · Grafana · `part-2/grafana`

1. <http://localhost:3001>: **Service health**, live.
2. `make incident`. Checkout crosses 5% within about 30 seconds.
3. **Alerting → Alert rules → High error rate**: Pending, then Firing.
4. A panel's **Edit**: the SQL behind it.
5. Optional: **Service health (ClickHouse)**, the same panels on ClickHouse.

**Optional agent prompt** (after `make incident`):

```text
Using the Grafana tools: is anything wrong with our services right now?
Check the alert rules and the Service health dashboard, and tell me which
service, since when, and how bad.
```

**Fallback:** run `make incident` five minutes before the demo so the
alert is already firing.

## Demo 3 · Holotable · `part-2/holotable`

1. **Data sources → Lumen Supply (semantic layer) → Test**: read-only.
2. New dashboard on that source:

   ```text
   Which region missed its revenue target last quarter, and why?
   ```

3. "Break EMEA's revenue down by channel for each of the last four
   quarters."
4. Save, reload: no model call.
5. Open **Lumen Supply: executive overview** and compare: EMEA at 89.6%
   in both. Click EMEA to drill in.

**Fallback:** skip to step 5.

## Optional · the same question, every AI · `part-2/ai-answers`

Ask Holotable and the ClickHouse agent the same question. One is grounded in
targets, one is not.

## If something breaks

| Problem | Do this |
| --- | --- |
| Holotable says no model | `.env` has `LLM_*`? Then `make restart holotable` |
| Superset embed is blank | `make restart superset`, then reload the portal |
| The alert never fires | `make incident checkout errors 5`, and wait a minute |
| Anything else | `make status`, then `make smoke` to find it |
