# Part 2 · Superset: from KPIs to drill-down

**Supports:** Part 2, Demo 1. **Types:** strategic, analytical. **Needs:**
`make up superset` (<http://localhost:8088>, `admin` / `admin`), and for the
embedding step `make example superset-embed` (<http://localhost:3121>).

The same platform answers "are we on track?" and "why?", then shows two
things the free build includes: row-level security and embedding.

## The demo

1. **Strategic.** Open **Dashboards → Executive KPIs**. $5.64M, 98.6% of
   target, EMEA furthest below at 89.6%.
2. **Analytical.** Open **Revenue analysis**. **EMEA revenue by channel, by
   quarter** shows partner shrinking. Click a chart title to open it in
   Explore and change the grouping.
3. **SQL Lab.** Open **SQL → SQL Lab** and show the query behind the
   numbers:

   ```sql
   SELECT region, sum(revenue) / sum(revenue_target) AS attainment
   FROM metrics.monthly_kpis
   WHERE month >= date_trunc('quarter', now()) - interval '3 months'
     AND month < date_trunc('quarter', now())
   GROUP BY region ORDER BY attainment;
   ```

4. **Row-level security.** Sign out, then sign in as `emea` /
   `emea-viewer-1`. The same Executive KPIs dashboard now shows $1.56M and
   one region. The rule is **Settings → Row Level Security → EMEA only**,
   `region = 'EMEA'` on all three datasets.
5. **Embedding.** Open <http://localhost:3121>, a mock partner portal that
   embeds the dashboard. Pick **EMEA** in the header: the server asks
   Superset for a guest token that carries the same kind of rule, and every
   chart filters. The browser never holds Superset credentials.
6. **Agent (optional).** Connect an agent to Superset's MCP server and run
   the demo prompt in `prompts.md`.

## What the lab sets up for this

| Piece | Where |
| --- | --- |
| Dashboards and datasets | `stacks/superset/bootstrap.py` |
| The `Lab viewer` role, the `EMEA only` rule, and the `emea` user | `stacks/superset/security.py` |
| Embedding turned on, guest role, guest-token secret | `stacks/superset/superset_config.py` |
| The partner portal | `examples/part-2/superset-embed/` (`server.py` gets the guest token, `index.html` embeds with `@superset-ui/embedded-sdk`) |

The lab turns off Superset's frame and content-security protections so a
page on another localhost port can embed it. Do not do that in a
deployment; set allowed domains and Talisman's settings instead.

## What to point out

- **One platform, two types.** KPIs and drill-down without switching
  tools.
- **Apache 2.0.** Embedding carries no license obligations.
- **Row-level security is free.** In Metabase it is a paid feature.
- **The semantic layer shows.** Every chart reads the `metrics` views, so
  its numbers match Part 1's examples.

## Fallback

If live embedding fails, sign in as `emea` instead: it shows the same
filtering in Superset's own UI.
