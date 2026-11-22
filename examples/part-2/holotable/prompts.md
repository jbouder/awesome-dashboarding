# Prompts · Part 2 Holotable

## Demo prompt

**Where:** Holotable, a new dashboard on the source **Lumen Supply
(semantic layer)**. **Time:** 30 to 90 seconds, depending on the model.

```text
Which region missed its revenue target last quarter, and why?
```

**Expected:** panels for revenue and attainment, attainment by region with
EMEA lowest at about 89.6%, and something that points at channels.

### Follow-up 1

```text
Break EMEA's revenue down by channel for each of the last four quarters.
```

**Expected:** a stacked bar or line by channel, with partner falling from
about $297K to about $94K in the last full quarter.

### Follow-up 2

```text
Add the top 10 products for EMEA's partner channel last quarter.
```

**Expected:** a table of products and revenue.

**Point out:** each answer is a validated spec, not generated data. Open a
panel's SQL to show it.

**Fallback:** the seeded **Lumen Supply: executive overview**.

### Live dashboards too

On the source **Lumen Supply (live service metrics)**:

```text
Error rate and p95 latency for each service, live.
```

Then run `make incident` and watch checkout climb.

## Build prompt

**Where:** Claude Code in this repository. This reproduces the three seeded
dashboards in `stacks/holotable/dashboards.py`.

```text
Seed Holotable with three linked Lumen Supply dashboards, written as specs
in stacks/holotable/dashboards.py and created through Holotable's API by
stacks/holotable/register.py after it registers the lab sources.

Read Holotable's spec format in its docs (the shared IR, panel options,
drilldown) and these rules: the SQL may not call now(), since the server
owns the time range, so define "last full quarter" from the newest month in
the data; line, area, and bar charts draw one series per numeric column, so
write per-channel and per-service series as one column each, named after
the value; and a link's target is a dashboard id, so create the targets
first.

1. "Lumen Supply: executive overview": last quarter's revenue, attainment,
   orders, and active customers; attainment by region as gauge bars; revenue
   against target by month; a treemap of last quarter's revenue by region and
   channel; a region table; and the store's live error rate. Clicking a
   region anywhere opens the region detail for that region.
2. "Lumen Supply: region detail": region and channel pickers; KPIs;
   revenue against target; revenue by channel for the last four full
   quarters; a sankey from channel to segment to category; a segment donut;
   weekly revenue by channel; and top products. Clicking a channel filters
   the dashboard in place.
3. "Lumen Supply: service health": live every 5 seconds, a status grid of
   error rate per service, error rate, latency, and traffic by service, and
   recent incidents. Clicking a service filters to it.

Existing dashboards are kept unless HOLOTABLE_REBUILD=1.
```
