# Prompts · 05 Two answers

## Demo prompt

**Where:** Claude Code in this repository, with the lab running. Ask twice,
in two fresh sessions. **Time:** about a minute each.

First, raw tables only:

```text
Connect to the Postgres database at localhost:5433, database lab, user
lab_ro, password lab_ro. Using only the tables in schema shop, what was our
revenue last quarter? Show the SQL you ran.
```

Then the semantic layer:

```text
Connect to the Postgres database at localhost:5433, database lab, user
lab_ro, password lab_ro. Read examples/_shared/context.md first and use the
metrics views it describes. What was our revenue last quarter? Show the SQL
you ran.
```

**Expected:** the first answer is one of the raw definitions in
`compare.sql`, often $6.54M or $6.10M, depending on whether the model
thought of status and discounts. The second is $5.64M, every time.

### Follow-up

```text
Did we hit our target last quarter?
```

**Point out:** with the raw answer, the model may say yes. With the
semantic layer, it says no: 98.6%, with EMEA at 89.6%.

**Fallback:** run `compare.sql` and show the table.

## Build prompt

**Where:** Claude Code in this repository. This reproduces `compare.sql`.

```text
Write examples/05-two-answers/compare.sql: one Postgres query that shows
last full quarter's revenue four ways, as rows of (definition, revenue):

1. Every order line at list price: sum(quantity * unit_price).
2. Every order line net of discounts.
3. Completed orders only, at list price.
4. Completed orders only, net of discounts, read from
   metrics.monthly_kpis, which is the governed definition.

Use shop.orders and shop.order_items for the first three. Define the
quarter once in a CTE as the last calendar quarter that has ended. Format
revenue as whole dollars, label each definition in plain words, and add a
comment with the command that runs it through the lab's warehouse.
```
