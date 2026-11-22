# 05 · Two answers for revenue

**Supports:** Part 1, "Fast to build, costly to sprawl" and "AI builds the
dashboard, not the data". Part 2, the semantic-layer pattern. **Needs:** the
lab running (any stack).

One question, "What was revenue last quarter?", asked of the raw tables and
of the semantic layer. Every definition below is one a person or a model
might reasonably pick.

```sh
docker compose exec -T warehouse psql -U lab_ro -d lab < examples/05-two-answers/compare.sql
```

| Definition | Last full quarter |
| --- | --- |
| Every line, list price (a common first guess) | about $6.54M |
| Every line, net of discounts | about $6.10M |
| Completed orders, list price | about $6.05M |
| **Completed orders, net of discounts (the semantic layer)** | **about $5.64M** |

The spread is about 16%. At $6.54M, Lumen Supply beat its target. At
$5.64M, it missed. Same data, opposite stories.

The Streamlit stack shows the same thing live: switch its **Revenue
definition** to **Raw tables**. See `stacks/streamlit/`.

## Files

| File | What it is |
| --- | --- |
| `compare.sql` | The four definitions side by side |
| `prompts.md` | The demo prompt and the build prompt |

## What to point out

- **Nothing is wrong with the code.** Each query is correct for its own
  definition. The problem is that there were four definitions to choose
  from.
- **AI makes this worse by default.** A model asked for revenue picks a
  definition on the spot, and a different model, or the same one tomorrow,
  may pick another.
- **The fix is upstream.** Define revenue once, in a semantic layer: here,
  the `metrics` views, Cube, Lightdash's dbt metrics, or WrenAI's model.
  Point every tool and every prompt at it.
