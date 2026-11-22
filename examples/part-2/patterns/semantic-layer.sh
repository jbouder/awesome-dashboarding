#!/usr/bin/env bash
# Last quarter's revenue by region, three ways:
#   1. raw SQL on the shop tables, with a plausible but wrong definition
#   2. the warehouse's semantic layer, the metrics views
#   3. Cube's semantic layer, through its Postgres-compatible SQL API
# Needs the warehouse running, and `make up cube` for the third.
set -euo pipefail
cd "$(dirname "$0")/../../.."

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
sql() { docker compose exec -T warehouse psql -U lab_ro -d lab -P pager=off "$@"; }

say "1. Raw tables: every order line at list price"
sql -c "SELECT o.region, to_char(sum(i.quantity * i.unit_price), 'FM\$999,999,999') AS revenue
  FROM shop.orders o JOIN shop.order_items i USING (order_id)
  WHERE o.ordered_at >= date_trunc('quarter', now()) - interval '3 months'
    AND o.ordered_at < date_trunc('quarter', now())
  GROUP BY 1 ORDER BY 1"

say "2. The semantic layer in the warehouse (metrics views)"
sql -c "SELECT region, to_char(sum(revenue), 'FM\$999,999,999') AS revenue
  FROM metrics.monthly_kpis
  WHERE month >= date_trunc('quarter', now()) - interval '3 months'
    AND month < date_trunc('quarter', now())
  GROUP BY 1 ORDER BY 1"

say "3. Cube's semantic layer, through its SQL API (MEASURE(revenue) is defined in stacks/cube/model)"
if [ -n "$(docker compose ps --status running -q cube 2>/dev/null)" ]; then
  docker compose exec -T warehouse psql "postgresql://cube:${CUBE_SQL_PASSWORD:-cube}@cube:15432/cube" -P pager=off -c \
    "SELECT region, to_char(MEASURE(revenue), 'FM\$999,999,999') AS revenue FROM sales
     WHERE ordered_at >= date_trunc('quarter', now()) - interval '3 months'
       AND ordered_at < date_trunc('quarter', now())
     GROUP BY 1 ORDER BY 1"
else
  echo "Cube is not running. Start it with: make up cube"
fi
