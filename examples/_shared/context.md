# Lumen Supply: context for prompts

Attach or paste this file into any prompt that builds a dashboard on the lab
data. It tells the assistant what the data is, what the metrics mean, and
how the result should look. Every build prompt in `examples/` assumes it.

## The business

Lumen Supply is a made-up online retailer of outdoor and home gear. It sells
in four regions (North America, EMEA, APAC, LATAM) through three channels
(web, mobile, partner) to three customer segments (Consumer, SMB,
Enterprise). It has a monthly revenue target per region. Its storefront runs
on five services (web, checkout, payments, search, inventory).

## Connecting

Postgres (TimescaleDB), read-only:

| Setting | From your machine | From a container in the lab |
| --- | --- | --- |
| Host | `localhost` | `warehouse` |
| Port | `5433` | `5432` |
| Database | `lab` | `lab` |
| User / password | `lab_ro` / `lab_ro` | `lab_ro` / `lab_ro` |

URL from a lab container: `postgresql://lab_ro:lab_ro@warehouse:5432/lab`.

## Use the semantic layer

Query the views in schema `metrics`. Each metric is defined once there, so
every tool in the lab gets the same numbers. Do not define revenue yourself
from the `shop` tables unless the prompt asks you to.

| View | One row per | Columns |
| --- | --- | --- |
| `metrics.monthly_kpis` | month and region | `month` date, `region`, `revenue`, `revenue_target`, `attainment`, `orders`, `active_customers`, `avg_order_value` |
| `metrics.daily_revenue` | day, region, segment, channel | `order_date` date, `region`, `segment`, `channel`, `revenue`, `gross_margin`, `orders`, `customers` |
| `metrics.line_facts` | completed order line | `order_id`, `ordered_at` timestamptz, `order_date`, `segment`, `region`, `channel`, `category`, `product`, `units`, `revenue` |
| `metrics.order_facts` | completed order | `order_id`, `ordered_at`, `order_date`, `customer_id`, `segment`, `region`, `channel`, `revenue`, `gross_margin`, `units` |
| `metrics.service_health` | minute and service | `minute` timestamptz, `service`, `requests`, `errors`, `error_rate` (0 to 1), `p95_latency_ms` |

Raw tables, for when a prompt asks for them: `shop.orders` (`status` is
`completed`, `refunded`, or `canceled`), `shop.order_items` (`quantity`,
`unit_price`, `discount` from 0 to 1), `shop.products`, `shop.customers`,
`shop.targets`, and the live `ops.request_metrics` (one row per service
every 5 seconds) and `ops.incidents`.

## Metric definitions

- **Revenue:** `sum(quantity * unit_price * (1 - discount))` over lines of
  **completed** orders only. Refunded and canceled orders do not count.
- **Target:** the monthly plan per region. **Attainment** is revenue divided
  by target.
- **Orders:** count of completed orders. **Average order value** is revenue
  divided by orders.
- **Error rate:** errors divided by requests.
- **Last full quarter:** the last calendar quarter that has ended. In SQL,
  `date_trunc('quarter', now()) - interval '3 months'` up to, not including,
  `date_trunc('quarter', now())`.

## Known answers

Use these to check any result. They hold while the seed is 42; `make story`
prints the current values.

- Last full quarter: revenue about **$5.64M**, **98.6%** of target, about
  **7,800** orders.
- Attainment by region: **EMEA 89.6%** (the miss), LATAM 93.3%, APAC 100.8%,
  North America 104.9%.
- Why: EMEA's **partner** channel fell from about $297K to about $94K
  quarter over quarter. Web and mobile grew.
- Summing every order line in the raw tables, with no status filter and no
  discount, gives about **$6.54M**. That is the wrong answer, and a common
  one.

## Design rules

- Use the palette and type scale in `design-tokens.css`. Support light and
  dark.
- Money: `$5.64M` in KPIs, `$1,560,053` in tables. Percentages to one
  decimal. Counts with thousands separators.
- Color: blue for the main series, orange for comparison or target. Never
  red and green alone to mean good and bad; pair color with a label or icon.
- Put the answer first: KPIs on top, then the chart that explains them, then
  detail.
- Show how fresh the data is in the header.
- Every chart has a title that says what it shows, and axis labels with
  units.
- Loading and empty states say what is happening, not just spin.
