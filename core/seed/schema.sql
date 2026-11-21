-- The lab dataset. Recreated from scratch on every seed.
-- Lumen Supply is a made-up online retailer of outdoor and home gear.

DROP SCHEMA IF EXISTS metrics CASCADE;
DROP TABLE IF EXISTS shop.order_items, shop.orders, shop.targets,
  shop.products, shop.customers CASCADE;

CREATE TABLE shop.customers (
  customer_id   integer PRIMARY KEY,
  segment       text NOT NULL,          -- Consumer, SMB, Enterprise
  region        text NOT NULL,          -- North America, EMEA, APAC, LATAM
  channel       text NOT NULL,          -- how they were acquired
  signed_up_at  date NOT NULL
);

CREATE TABLE shop.products (
  product_id  integer PRIMARY KEY,
  name        text NOT NULL,
  category    text NOT NULL,
  unit_price  numeric(10, 2) NOT NULL,
  unit_cost   numeric(10, 2) NOT NULL
);

CREATE TABLE shop.orders (
  order_id     integer PRIMARY KEY,
  customer_id  integer NOT NULL REFERENCES shop.customers,
  ordered_at   timestamptz NOT NULL,
  status       text NOT NULL,           -- completed, refunded, canceled
  channel      text NOT NULL,           -- web, mobile, partner
  region       text NOT NULL
);
CREATE INDEX ON shop.orders (ordered_at);

CREATE TABLE shop.order_items (
  order_id    integer NOT NULL REFERENCES shop.orders,
  product_id  integer NOT NULL REFERENCES shop.products,
  quantity    integer NOT NULL,
  unit_price  numeric(10, 2) NOT NULL,
  discount    numeric(4, 3) NOT NULL DEFAULT 0
);
CREATE INDEX ON shop.order_items (order_id);

CREATE TABLE shop.targets (
  month           date NOT NULL,
  region          text NOT NULL,
  revenue_target  numeric(12, 2) NOT NULL,
  PRIMARY KEY (month, region)
);

-- Live operational metrics, one row per service every few seconds.
CREATE TABLE IF NOT EXISTS ops.request_metrics (
  ts              timestamptz NOT NULL,
  service         text NOT NULL,
  requests        integer NOT NULL,
  errors          integer NOT NULL,
  p95_latency_ms  double precision NOT NULL
);
SELECT create_hypertable('ops.request_metrics', 'ts', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS request_metrics_service_ts ON ops.request_metrics (service, ts DESC);

-- Incidents the streamer plays back. scripts/incident.sh adds one.
CREATE TABLE IF NOT EXISTS ops.incidents (
  id          serial PRIMARY KEY,
  service     text NOT NULL,
  kind        text NOT NULL,            -- errors, latency
  started_at  timestamptz NOT NULL DEFAULT now(),
  ends_at     timestamptz NOT NULL
);

GRANT SELECT ON ALL TABLES IN SCHEMA shop, ops TO lab_ro;
