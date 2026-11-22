// Data loader: runs at build time and writes products.json.
// Units and revenue by product, region, and channel for the last full quarter.
import {BOUNDS, withWarehouse} from "../../lib/warehouse.js";

const rows = await withWarehouse((query) =>
  query(`
    WITH ${BOUNDS}
    SELECT region, channel, category, product,
           sum(units)::int AS units,
           sum(revenue)::float8 AS revenue
    FROM metrics.line_facts, bounds
    WHERE order_date >= q_start AND order_date < q_end
    GROUP BY 1, 2, 3, 4
    ORDER BY revenue DESC`)
);

process.stdout.write(JSON.stringify(rows));
