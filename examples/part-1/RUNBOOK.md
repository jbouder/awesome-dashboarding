# Part 1 runbook: ad hoc dashboarding with AI

Run of show for "Dashboarding in the Age of AI: Part 1". Each demo lists the
command, the prompt to type, what to point out, and the fallback if a live
run stalls. Every prompt is in full in its example's `prompts.md`.

## Before the talk

- [ ] `make up grafana` (any stack starts the warehouse), then `make
      extract` so the extracts and snapshots are from today.
- [ ] `make example static streamlit-demo`, then `make smoke`.
- [ ] Open these tabs: Claude (new chat), Claude Code in an empty folder,
      <http://localhost:3102/02-static-html/>,
      <http://localhost:3102/04-chart-libraries/>, <http://localhost:3101>.
- [ ] Have `examples/01-claude-artifact/extracts/raw/` open in Finder for
      dragging into Claude.
- [ ] Know the answers: **$5.64M** revenue, **98.6%** of target, **EMEA
      89.6%**, partner channel **$297K → $94K**. Raw tables: **$6.54M**.

## Slides

| Slide | Do | Time |
| --- | --- | --- |
| Why now | Talk | 2 min |
| Four types | Talk. Ad hoc dashboards land in analytical and generative work | 2 min |
| Toolkit | Talk | 2 min |
| Chart libraries | Show `04-chart-libraries` (below) | 3 min |
| Demo 1 · Claude artifact | `01-claude-artifact` (below) | 6 min |
| Demo 2 · Static HTML | `02-static-html` (below) | 4 min |
| Demo 3 · Streamlit | `03-streamlit` (below) | 6 min |
| Tradeoffs | `05-two-answers` (below) | 3 min |
| Foundations, Graduate | Talk. Point at Part 2 | 3 min |

## Chart libraries · `04-chart-libraries`

Open <http://localhost:3102/04-chart-libraries/>. Show the line-count table,
then open **Show code** on Vega-Lite and on D3.

**Optional live prompt** (Claude, attach `_shared/snapshot.json`):

```text
Using the "channels" rows in this JSON, draw EMEA revenue by channel (web,
mobile, partner) for each quarter as a stacked bar chart with Vega-Lite.
One HTML file, the library from a CDN, money on the axis, and a legend.
```

**Point out:** declarative specs are short and hard to break; D3 is long.

## Demo 1 · `01-claude-artifact`

1. New Claude chat. Attach `lumen_order_lines.csv` and `lumen_targets.csv`
   from `extracts/raw/`.
2. Type:

   ```text
   These are our order lines for the last 15 months and our monthly revenue
   targets by region. Which region missed its revenue target last quarter, and
   why? Build me an interactive dashboard that answers it: the headline
   numbers, attainment by region, and the chart that explains the miss.
   ```

3. Follow-up: "Let me click a region to drill into it. Show that region's
   revenue by channel for each of the last four quarters, and its top
   products."
4. Follow-up: "How did you define revenue? List the exact rules you used,
   and add them as a footnote on the dashboard."
5. Publish, and open the link in a private window.

**Point out:** a minute from CSV to dashboard. EMEA misses because partner
collapsed. Claude chose its own revenue definition; note it for later.

**Fallback:** `examples/01-claude-artifact/result.html`.

## Demo 2 · `02-static-html`

1. In the same chat, type:

   ```text
   Turn this dashboard into one self-contained HTML file I can open from my
   laptop or put on GitHub Pages. Embed the data in the file, load the chart
   library from a CDN, and keep every interaction. Add a footer that says when
   the data was captured.
   ```

2. Download it and open it from disk.
3. Show the published copy on GitHub Pages.

**Point out:** you own it, hosting is free, the data is a snapshot, and
anyone with the file sees all of it.

**Fallback:** <http://localhost:3102/02-static-html/>.

## Demo 3 · `03-streamlit`

1. In Claude Code, in an empty folder, paste the demo prompt from
   `examples/03-streamlit/prompts.md`.
2. Run it with `streamlit run app.py`.
3. Paste the follow-up: a region picker and EMEA's channel chart.
4. Scroll through `app.py`.

**Point out:** minutes to an app; it used the semantic layer because the
prompt said to; every line is now yours to maintain.

**Fallback:** <http://localhost:3101> (`make example streamlit-demo`).

## Tradeoffs · `05-two-answers`

Run:

```sh
docker compose exec -T warehouse psql -U lab_ro -d lab < examples/05-two-answers/compare.sql
```

Four reasonable definitions, $5.64M to $6.54M. At $6.54M Lumen Supply beat
its target; at $5.64M it missed. Tie it back to the definition Claude picked
in Demo 1.

**Optional live prompt:** the two Claude Code prompts in
`examples/05-two-answers/prompts.md`, raw tables first.

## If something breaks

| Problem | Do this |
| --- | --- |
| Claude is slow or errors | Open the fallback for that demo and keep talking |
| A port is busy | `make doctor` names the process |
| Numbers look different from the slides | `make extract`, then reload. Dates are relative to today |
| The warehouse is down | `make up grafana`, about 30 seconds |
