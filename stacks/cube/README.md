# Cube

**Type:** semantic layer. **License:** Apache 2.0.
**Playground:** <http://localhost:4000>. **SQL API:** `localhost:15432`, user
`cube`, password `cube`.

```sh
make up cube
```

## What the lab sets up

Cube is not a dashboard. It is the layer under dashboards and agents that
says what a metric means. `model/sales.yml` defines Lumen Supply's metrics on
the raw `shop` tables:

- **revenue**: completed orders only, net of discounts.
- **gross_margin**, **orders**, **units**, and **avg_order_value**.
- The dimensions: region, channel, segment, category, product, and order
  time.
- **targets**: the monthly plan per region.

Any tool can then ask Cube instead of writing its own SQL, over REST,
GraphQL, or a Postgres-compatible SQL API.

## Tour

1. Open the Playground. Pick the measure **Sales Revenue**, the dimension
   **Sales Region**, and the time range **Last quarter**. Press **Run**.
   EMEA is about $1.56M.
2. Open the **Generated SQL** tab. That is the join, the completed-orders
   filter, and the discount math, none of which the person asking had to
   know.
3. Query it like a database:

   ```sh
   psql "postgresql://cube:cube@localhost:15432/cube" -c \
     "SELECT region, MEASURE(revenue) FROM sales GROUP BY 1"
   ```

4. Compare with the warehouse: `make story`. The totals differ by a dollar
   or two. The warehouse views round each order to the cent before summing,
   and Cube sums unrounded lines. Where you round is part of a metric's
   definition, and it is easy to miss.

## Notes

- Dev mode is on, which turns on the Playground. A deployment would turn it
  off and require a signed token on every request.
