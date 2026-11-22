# Prompts · 01 Claude artifact

## Demo prompt

**Where:** a new Claude chat, with `extracts/raw/lumen_order_lines.csv` and
`extracts/raw/lumen_targets.csv` attached. **Time:** about a minute.

```text
These are our order lines for the last 15 months and our monthly revenue
targets by region. Which region missed its revenue target last quarter, and
why? Build me an interactive dashboard that answers it: the headline
numbers, attainment by region, and the chart that explains the miss.
```

**Expected:** a dashboard artifact with revenue, target, and attainment for
the last full quarter, attainment by region with EMEA lowest, and a chart
that shows EMEA's partner channel falling.

### Follow-up 1: drill down

```text
Let me click a region to drill into it. Show that region's revenue by
channel for each of the last four quarters, and its top products.
```

**Expected:** clicking EMEA shows the partner channel dropping from about
$297K to about $94K in the last full quarter.

### Follow-up 2: the definition

```text
How did you define revenue? List the exact rules you used, and add them as
a footnote on the dashboard.
```

**Expected:** a list such as "quantity × unit price × (1 − discount), for
completed orders". **Point out:** whatever it says, Claude chose it. Our
governed definition counts completed orders only, net of discounts:
$5.64M for the quarter. Counting every line with no discount gives $6.54M.

### Follow-up 3: publish

Use the artifact's **Publish** menu, then open the link in a private window
to show it works for anyone with the link.

**Fallback:** `result.html` in this folder.

## Build prompt

**Where:** a new Claude chat, with `extracts/semantic/monthly_kpis.csv`,
`extracts/semantic/daily_revenue.csv`, and `../_shared/context.md`
attached. This reproduces `result.html`.

```text
Build an interactive executive dashboard for Lumen Supply, a retailer, as
a single artifact. Use the attached CSVs, which come from our governed
semantic layer: revenue is already defined in them. Follow the metric
definitions and design rules in context.md.

The dashboard answers one question for a sales leader: which region missed
its revenue target last quarter, and why? "Last quarter" is the last
calendar quarter that has ended.

Layout, top to bottom:
1. Header: "Lumen Supply", the quarter shown (for example "Q3 2026"), and
   when the data was last updated.
2. Four KPI cards for the last full quarter: revenue (with the change
   against the quarter before), target (with the gap to it in dollars),
   attainment (revenue ÷ target, with a badge: below 92% "Missed", below
   98% "Close", otherwise "On track"), and orders (with the change).
3. Revenue against target by month for the last 12 full months: a solid
   line for revenue and a dashed line for target.
4. Attainment by region for the last full quarter, as horizontal bars
   sorted best to worst, with a dashed line at 100%. Color bars by the same
   bands as the badge, and label each bar with its value and its word.
   Clicking a region filters the charts below to that region; clicking it
   again clears the filter.
5. Revenue by channel (web, mobile, partner) for the last four full
   quarters, as stacked bars. Clicking a channel filters the products
   table.
6. Top 15 products for the last full quarter, for the current region and
   channel: product, category, units, revenue. Add a search box and make
   every column sortable.

Show the active filters above the charts with a way to clear each one.
Support light and dark themes with a toggle. Format money as $5.64M in
cards and $1,560,053 in tables. Use Apache ECharts. Make it accessible:
labels on controls, keyboard-sortable table headers, and color never the
only signal.
```

**Expected:** a dashboard like `result.html`: $5.64M revenue, 98.6%
attainment, EMEA at 89.6%.

## In other assistants

The prompts work in ChatGPT, Gemini, and Julius too. Attach the same files.
They were recorded with Claude only.
