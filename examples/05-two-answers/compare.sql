-- Last full quarter's revenue, four ways. Only the last is the governed
-- definition. Run it with:
--   docker compose exec -T warehouse psql -U lab_ro -d lab < examples/05-two-answers/compare.sql

WITH q AS (
  SELECT date_trunc('quarter', now()) - interval '3 months' AS start_at,
         date_trunc('quarter', now()) AS end_at
),
lines AS (
  SELECT o.status, i.quantity, i.unit_price, i.discount
  FROM shop.orders o
  JOIN shop.order_items i USING (order_id), q
  WHERE o.ordered_at >= q.start_at AND o.ordered_at < q.end_at
)
SELECT definition, to_char(revenue, 'FM$999,999,999') AS revenue
FROM (
  SELECT 1 AS n, 'Every line, list price (a common first guess)' AS definition,
         sum(quantity * unit_price) AS revenue FROM lines
  UNION ALL
  SELECT 2, 'Every line, net of discounts',
         sum(quantity * unit_price * (1 - discount)) FROM lines
  UNION ALL
  SELECT 3, 'Completed orders, list price',
         sum(quantity * unit_price) FILTER (WHERE status = 'completed') FROM lines
  UNION ALL
  SELECT 4, 'Completed orders, net of discounts (the semantic layer)',
         sum(revenue) FROM metrics.monthly_kpis, q
         WHERE month >= q.start_at AND month < q.end_at
) t
ORDER BY n;
