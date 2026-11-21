"""Register the lab warehouse in Holotable and build its dashboards.

  lab-metrics  the semantic views in schema metrics (business and service health)
  lab-ops      the raw live metrics in schema ops

Then three linked dashboards from dashboards.py. Holotable runs in local
mode, so signing in is one request. Sources and dashboards that already
exist, by id or title, are left alone.
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import dashboards

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

    build_dashboards()
    print("[holotable-register] done")


def find_dashboard(title: str) -> str | None:
    q = urllib.parse.urlencode({"workspaceId": WORKSPACE, "search": title})
    for d in call("GET", f"/api/dashboards?{q}").get("dashboards", []):
        if d.get("title") == title:
            return d["id"]
    return None


REBUILD = os.environ.get("HOLOTABLE_REBUILD") == "1"


def save(spec: dict) -> str:
    existing = find_dashboard(spec["title"])
    if existing and REBUILD:
        call("PUT", f"/api/dashboards/{existing}", {"spec": {"specVersion": 1, **spec}})
        print(f"[holotable-register] rebuilt dashboard {spec['title']!r}")
        return existing
    if existing:
        print(f"[holotable-register] dashboard {spec['title']!r} exists")
        return existing
    created = call("POST", "/api/dashboards", {"spec": {"specVersion": 1, **spec}})["dashboard"]
    print(f"[holotable-register] created dashboard {spec['title']!r} with {len(spec['panels'])} panels")
    return created["id"]


def build_dashboards() -> None:
    region_title = dashboards.TITLES["region"]
    region_existed = find_dashboard(region_title) is not None
    region_id = save(dashboards.region_spec())
    service_id = save(dashboards.service_spec())
    overview_id = save(dashboards.overview_spec(region_id, service_id))
    if not region_existed or REBUILD:
        # The region detail links back to the overview, which did not exist yet.
        call(
            "PUT",
            f"/api/dashboards/{region_id}",
            {"spec": {"specVersion": 1, **dashboards.region_spec(overview_id)}},
        )


if __name__ == "__main__":
    main()
