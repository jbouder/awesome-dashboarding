"""Register the lab warehouse as two Holotable sources.

  lab-metrics  the semantic views in schema metrics (business and service health)
  lab-ops      the raw live metrics in schema ops

Holotable runs in local mode, so signing in is one request. Sources that
already exist are left alone.
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("HOLOTABLE_URL", "http://holotable:3000")
WORKSPACE = "local"
SECRET_REF = "LAB_WAREHOUSE"

SOURCES = [
    {
        "id": "lab-metrics",
        "name": "Lumen Supply (semantic layer)",
        "schema": "metrics",
        "tables": {
            "monthly_kpis": (
                "month",
                "Monthly revenue, target, attainment, orders, active customers and average order value by region. Revenue is completed orders net of discounts.",
            ),
            "daily_revenue": (
                "order_date",
                "Daily revenue, gross margin, orders and customers by region, customer segment and sales channel.",
            ),
            "order_facts": ("ordered_at", "One row per completed order with its revenue, margin and units."),
            "line_facts": ("ordered_at", "One row per order line with product, category and revenue."),
            "service_health": (
                "minute",
                "Requests, errors, error rate and p95 latency per service per minute.",
            ),
        },
    },
    {
        "id": "lab-ops",
        "name": "Lumen Supply (live service metrics)",
        "schema": "ops",
        "tables": {
            "request_metrics": (
                "ts",
                "Live request counts, errors and p95 latency per service, written every few seconds.",
            ),
            "incidents": (
                "started_at",
                "Incidents: which service, errors or latency, and when it started and ends.",
            ),
        },
    },
]

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(BASE + path, method=method, headers={"Content-Type": "application/json"})
    data = json.dumps(body).encode() if body is not None else None
    try:
        with opener.open(req, data) as res:
            return json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as err:
        sys.exit(f"[holotable-register] {method} {path} failed: {err.code} {err.read()[:400]!r}")


def main() -> None:
    opener.open(BASE + "/api/auth/login")  # local mode: mints the owner's session
    existing = {s["id"] for s in call("GET", f"/api/sources?workspaceId={WORKSPACE}").get("sources", [])}

    for src in SOURCES:
        if src["id"] in existing:
            print(f"[holotable-register] source {src['id']} exists")
            continue
        connection = {
            "host": "warehouse",
            "port": 5432,
            "database": "lab",
            "schema": src["schema"],
            "ssl": False,
        }
        found = call(
            "POST",
            "/api/sources/discover",
            {
                "kind": "timescaledb",
                "workspaceId": WORKSPACE,
                "secretRef": SECRET_REF,
                "connection": connection,
            },
        )
        columns = {t["name"]: t["columns"] for t in found["tables"]}
        tables = []
        for name, (time_field, description) in src["tables"].items():
            tables.append(
                {"name": name, "description": description, "timeField": time_field, "columns": columns[name]}
            )
        call(
            "POST",
            "/api/sources",
            {
                "id": src["id"],
                "name": src["name"],
                "workspaceId": WORKSPACE,
                "secretRef": SECRET_REF,
                "config": {"kind": "timescaledb", **connection, "tables": tables},
            },
        )
        print(f"[holotable-register] created source {src['id']} with {len(tables)} tables")

    print("[holotable-register] done")


if __name__ == "__main__":
    main()
