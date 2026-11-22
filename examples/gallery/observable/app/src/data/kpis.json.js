// Data loader: runs at build time and writes kpis.json.
// Quarter totals, attainment by region, and revenue against target by month.
import {BOUNDS, withWarehouse} from "../../lib/warehouse.js";

const data = await withWarehouse(async (query) => {
  const [meta] = await query(`
    WITH ${BOUNDS}
    SELECT 'Q' || extract(quarter FROM q_start) || ' ' || extract(year FROM q_start) AS period,
           'Q' || extract(quarter FROM q_start - interval '3 months') || ' '
             || extract(year FROM q_start - interval '3 months') AS previous_period,
           (SELECT max(ordered_at) FROM metrics.order_facts) AS as_of
    FROM bounds`);

  const quarters = await query(`
    WITH ${BOUNDS}
    SELECT CASE WHEN month >= q_start THEN 'current' ELSE 'previous' END AS period,
           sum(revenue)::float8 AS revenue,
           sum(revenue_target)::float8 AS target,
           (sum(revenue) / sum(revenue_target))::float8 AS attainment,
           sum(orders)::int AS orders
    FROM metrics.monthly_kpis, bounds
    WHERE month >= q_start - interval '3 months' AND month < q_end
    GROUP BY 1`);

  const regions = await query(`
    WITH ${BOUNDS}
    SELECT region,
           sum(revenue)::float8 AS revenue,
           sum(revenue_target)::float8 AS target,
           (sum(revenue) / sum(revenue_target))::float8 AS attainment,
           sum(orders)::int AS orders
    FROM metrics.monthly_kpis, bounds
    WHERE month >= q_start AND month < q_end
    GROUP BY region
    ORDER BY attainment`);

  const monthly = await query(`
    WITH ${BOUNDS}
    SELECT to_char(month, 'YYYY-MM-DD') AS month,
           sum(revenue)::float8 AS revenue,
           sum(revenue_target)::float8 AS target
    FROM metrics.monthly_kpis, bounds
    WHERE month >= q_end - interval '12 months' AND month < q_end
    GROUP BY month
    ORDER BY month`);

  return {
    period: meta.period,
    previousPeriod: meta.previous_period,
    asOf: meta.as_of,
    current: quarters.find((q) => q.period === "current"),
    previous: quarters.find((q) => q.period === "previous"),
    regions,
    monthly
  };
});

process.stdout.write(JSON.stringify(data));
