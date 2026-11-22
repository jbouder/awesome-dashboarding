// Data loader: runs at build time and writes channels.json.
// Revenue by quarter, region, and channel for the last four full quarters.
import {BOUNDS, withWarehouse} from "../../lib/warehouse.js";

const rows = await withWarehouse((query) =>
  query(`
    WITH ${BOUNDS}
    SELECT 'Q' || extract(quarter FROM order_date) || ' ' || extract(year FROM order_date) AS quarter,
           to_char(date_trunc('quarter', order_date), 'YYYY-MM-DD') AS quarter_start,
           region,
           channel,
           sum(revenue)::float8 AS revenue
    FROM metrics.daily_revenue, bounds
    WHERE order_date >= q_end - interval '12 months' AND order_date < q_end
    GROUP BY 1, 2, 3, 4
    ORDER BY quarter_start, region, channel`)
);

process.stdout.write(JSON.stringify(rows));
