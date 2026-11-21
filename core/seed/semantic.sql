-- The semantic layer, as plain views. Each metric is defined once here and
-- described in semantic/metrics.yml. Tools that query these views agree on
-- the numbers. Tools that query shop.* directly may not.

CREATE SCHEMA metrics;
GRANT USAGE ON SCHEMA metrics TO lab_ro;

-- One row per completed order, with its net revenue and margin.
-- Revenue counts completed orders only, net of line discounts.
CREATE VIEW metrics.order_facts AS
SELECT
  o.order_id,
  o.ordered_at,
  date_trunc('day', o.ordered_at)::date AS order_date,
  o.customer_id,
  c.segment,
  o.region,
  o.channel,
  sum(i.quantity * i.unit_price * (1 - i.discount))::numeric(12, 2) AS revenue,
  sum(i.quantity * (i.unit_price * (1 - i.discount) - p.unit_cost))::numeric(12, 2) AS gross_margin,
  sum(i.quantity) AS units
FROM shop.orders o
JOIN shop.customers c USING (customer_id)
JOIN shop.order_items i USING (order_id)
JOIN shop.products p USING (product_id)
WHERE o.status = 'completed'
GROUP BY o.order_id, c.segment;

-- Line-level revenue, for questions about products and categories.
CREATE VIEW metrics.line_facts AS
SELECT
  o.order_id,
  o.ordered_at,
  date_trunc('day', o.ordered_at)::date AS order_date,
  c.segment,
  o.region,
  o.channel,
  p.category,
  p.name AS product,
  i.quantity AS units,
  (i.quantity * i.unit_price * (1 - i.discount))::numeric(12, 2) AS revenue
FROM shop.orders o
JOIN shop.customers c USING (customer_id)
JOIN shop.order_items i USING (order_id)
JOIN shop.products p USING (product_id)
WHERE o.status = 'completed';

-- Daily totals by region, segment and channel.
CREATE VIEW metrics.daily_revenue AS
SELECT
  order_date,
  region,
  segment,
  channel,
  sum(revenue)::numeric(12, 2) AS revenue,
  sum(gross_margin)::numeric(12, 2) AS gross_margin,
  count(*) AS orders,
  count(DISTINCT customer_id) AS customers
FROM metrics.order_facts
GROUP BY 1, 2, 3, 4;

-- Monthly KPIs against target, by region.
CREATE VIEW metrics.monthly_kpis AS
WITH actuals AS (
  SELECT
    date_trunc('month', order_date)::date AS month,
    region,
    sum(revenue) AS revenue,
    count(*) AS orders,
    count(DISTINCT customer_id) AS active_customers
  FROM metrics.order_facts
  GROUP BY 1, 2
)
SELECT
  a.month,
  a.region,
  a.revenue::numeric(12, 2) AS revenue,
  t.revenue_target,
  (a.revenue / nullif(t.revenue_target, 0))::numeric(6, 3) AS attainment,
  a.orders,
  a.active_customers,
  (a.revenue / nullif(a.orders, 0))::numeric(10, 2) AS avg_order_value
FROM actuals a
LEFT JOIN shop.targets t USING (month, region);

-- Service health by minute.
CREATE VIEW metrics.service_health AS
SELECT
  time_bucket('1 minute', ts) AS minute,
  service,
  sum(requests) AS requests,
  sum(errors) AS errors,
  (sum(errors)::double precision / nullif(sum(requests), 0)) AS error_rate,
  max(p95_latency_ms) AS p95_latency_ms
FROM ops.request_metrics
GROUP BY 1, 2;

GRANT SELECT ON ALL TABLES IN SCHEMA metrics TO lab_ro;
