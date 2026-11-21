#!/usr/bin/env bash
# One-shot Superset setup. Every step is safe to run again.
set -euo pipefail

echo "[superset-init] migrating metadata"
superset db upgrade

echo "[superset-init] creating admin user (skipped if present)"
superset fab create-admin \
  --username "$SUPERSET_ADMIN_USERNAME" \
  --firstname Lab --lastname Admin \
  --email admin@dashlab.local \
  --password "$SUPERSET_ADMIN_PASSWORD" || true

echo "[superset-init] syncing roles and permissions"
superset init

echo "[superset-init] done"
