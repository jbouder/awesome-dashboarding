# The Lumen Supply dashboard: shared spec

Every framework in `examples/gallery/` builds this dashboard, so the gallery
compares like with like. Read `context.md` first for the data and metrics.

## Purpose

Answer one question for a sales leader in under a minute: **which region
missed its revenue target last quarter, and why?** Then let them dig in, and
let operations see whether the store is healthy right now.

## Layout, top to bottom

1. **Header.** Title "Lumen Supply", the period shown ("Q3 2026", the last
   full quarter), and "Data as of" with the time of the latest order.
2. **KPI row**, four cards, last full quarter against the quarter before:
   - Revenue, with the change in percent.
   - Target, with revenue's gap to it in dollars.
   - Attainment, colored by band (below 92% danger, below 98% warning, else
     success) and labeled in words ("Missed", "Close", "On track").
   - Orders, with the change in percent.
3. **Revenue against target by month**, the last 12 full months. A line for
   revenue, a dashed line for target.
4. **Attainment by region**, last full quarter. Horizontal bars, sorted
   worst first, with a reference line at 100%. **Clicking a region filters
   everything below to that region.**
5. **Revenue by channel by quarter**, last four full quarters, stacked bars.
   **Clicking a channel filters the products table to that channel.**
6. **Top products**, last full quarter, for the selected region and channel:
   product, category, units, revenue. Searchable and sortable. 15 rows.
7. **Live: error rate by service**, last 15 minutes, refreshed every 5
   seconds, with a reference line at 5%.

A visible control shows the active filters and clears them.

## Behavior

- Filters: region (from the attainment chart or a picker) and channel (from
  the channel chart or a picker).
- Every query reads the `metrics` views. No metric is defined in the app.
- Money, percent, and count formats follow `context.md`.
- Light and dark themes, from `design-tokens.css`.
- Loading state while queries run. Empty state when a filter has no rows.
- Works at 1280 pixels wide and stays usable at 768.

## Acceptance

With no filters the dashboard shows revenue about $5.64M, attainment 98.6%,
and EMEA as the worst region at 89.6%. With EMEA selected, the channel chart
shows partner revenue falling to about $94K in the last full quarter.
