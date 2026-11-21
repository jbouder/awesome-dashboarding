-- Runs once, on an empty ClickHouse volume.
-- ClickHouse pulls from the lab warehouse on a schedule with refreshable
-- materialized views: live metrics every 10 seconds, sales every hour.
-- Queries then run on ClickHouse's own columnar storage.

CREATE DATABASE IF NOT EXISTS lumen;

CREATE TABLE lumen.request_metrics
(
    ts DateTime64(3, 'UTC'),
    service LowCardinality(String),
    requests UInt32,
    errors UInt32,
    p95_latency_ms Float64
)
ENGINE = MergeTree
ORDER BY (service, ts);

CREATE MATERIALIZED VIEW lumen.request_metrics_sync
REFRESH EVERY 10 SECOND TO lumen.request_metrics
AS SELECT ts, service, requests, errors, p95_latency_ms
FROM postgresql('warehouse:5432', 'lab', 'request_metrics', 'lab_ro', 'lab_ro', 'ops')
WHERE ts > now() - INTERVAL 1 DAY;

CREATE TABLE lumen.sales
(
    order_id UInt32,
    ordered_at DateTime64(3, 'UTC'),
    region LowCardinality(String),
    segment LowCardinality(String),
    channel LowCardinality(String),
    category LowCardinality(String),
    product LowCardinality(String),
    units UInt32,
    revenue Decimal(12, 2)
)
ENGINE = MergeTree
ORDER BY (region, ordered_at);

CREATE MATERIALIZED VIEW lumen.sales_sync
REFRESH EVERY 1 HOUR TO lumen.sales
AS SELECT order_id, ordered_at, region, segment, channel, category, product, units, revenue
FROM postgresql('warehouse:5432', 'lab', 'line_facts', 'lab_ro', 'lab_ro', 'metrics');
