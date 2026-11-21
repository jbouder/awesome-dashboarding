-- Runs once, on an empty warehouse volume.
-- The warehouse holds the seed data every stack reads, plus metadata
-- databases for the stacks that need Postgres.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Read-only role every dashboard tool connects as.
CREATE ROLE lab_ro LOGIN PASSWORD 'lab_ro';
ALTER ROLE lab_ro SET default_transaction_read_only = on;

CREATE SCHEMA IF NOT EXISTS shop;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS metrics;

GRANT USAGE ON SCHEMA shop, ops, metrics TO lab_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA shop GRANT SELECT ON TABLES TO lab_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA ops GRANT SELECT ON TABLES TO lab_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA metrics GRANT SELECT ON TABLES TO lab_ro;

-- Metadata databases for stacks that keep their own state in Postgres.
CREATE DATABASE superset;
