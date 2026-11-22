# 01 · Claude artifact from a data extract

**Supports:** Part 1, Demo 1, "Building one from scratch". **Type:**
generative. **Needs:** Claude in a browser. No lab required.

Give Claude a data extract and one business question. In about a minute it
returns an interactive dashboard. Refine it in conversation, then publish it
as a shareable page.

## Files

| File | What it is |
| --- | --- |
| `prompts.md` | The demo prompt and follow-ups, and the full build prompt |
| `extracts/raw/` | Order lines and targets, straight from the raw tables. No revenue column: Claude has to define it |
| `extracts/semantic/` | The governed views, `monthly_kpis.csv` and `daily_revenue.csv`. Revenue is already defined |
| `result.html` | The reference result, for when a live run stalls. Same file as `02-static-html/index.html` |

`make extract` refreshes the extracts and the reference result from the
warehouse. Dates are relative to today, so refresh before a talk.

## Run it

1. Open Claude and start a new chat.
2. Attach `extracts/raw/lumen_order_lines.csv` and
   `extracts/raw/lumen_targets.csv`.
3. Paste the demo prompt from `prompts.md`. Then the follow-ups, in order.
4. Publish the artifact from its menu and copy the link.

## What to point out

- **Speed.** From a CSV to a working dashboard in about a minute.
- **The question gets answered.** EMEA missed its target last quarter,
  because its partner channel collapsed.
- **Claude defined revenue on its own.** The second follow-up asks how. If
  it counted refunded and canceled orders, or skipped discounts, its
  revenue is near $6.54M, not $5.64M. That sets up the tradeoffs slide.
- **The governed version.** Run the build prompt with the semantic extracts
  and the numbers match every platform in the lab.

## Fallback

Open `result.html`, or the published copy on GitHub Pages (see the
repository README). It is the dashboard the build prompt asks for.
