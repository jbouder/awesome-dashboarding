// Shared by the data loaders: run queries against the warehouse's metrics views.
import pg from "pg";

// Postgres returns numeric and bigint as strings. Every query casts what it
// needs, so the JSON holds plain numbers.
export async function withWarehouse(fn) {
  const url = process.env.WAREHOUSE_URL;
  if (!url) throw new Error("Set WAREHOUSE_URL to the warehouse's Postgres URL.");
  const client = new pg.Client({connectionString: url});
  await client.connect();
  try {
    return await fn((sql) => client.query(sql).then((result) => result.rows));
  } finally {
    await client.end();
  }
}

// The last full quarter: the last calendar quarter that has ended.
export const BOUNDS = `
  bounds AS (
    SELECT (date_trunc('quarter', now()) - interval '3 months')::date AS q_start,
           date_trunc('quarter', now())::date AS q_end
  )`;
