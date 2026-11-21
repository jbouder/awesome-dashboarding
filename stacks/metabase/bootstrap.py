"""Set up Metabase: the admin account, the lab warehouse, and a dashboard.

Runs once after Metabase is healthy. A second run signs in and skips what
already exists.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("METABASE_URL", "http://metabase:3000")
EMAIL = os.environ["METABASE_ADMIN_EMAIL"]
PASSWORD = os.environ["METABASE_ADMIN_PASSWORD"]
DB_NAME = "Lab warehouse"
DASHBOARD = "Lumen Supply overview"

WAREHOUSE = {
    "host": "warehouse",
    "port": 5432,
    "dbname": "lab",
    "user": "lab_ro",
    "password": "lab_ro",
    "ssl": False,
    "schema-filters-type": "inclusion",
    "schema-filters-patterns": "metrics,shop,ops",
}

LAST_QUARTER = (
    "month >= date_trunc('quarter', now()) - interval '3 months' AND month < date_trunc('quarter', now())"
)

CARDS = [
    # (name, display, sql, visualization settings, (col, row, width, height))
    (
        "Revenue, last full quarter",
        "scalar",
        f"SELECT sum(revenue) AS revenue FROM metrics.monthly_kpis WHERE {LAST_QUARTER}",
        {
            "column_settings": {
                '["name","revenue"]': {"prefix": "$", "number_style": "decimal", "decimals": 0}
            }
        },
        (0, 0, 8, 4),
    ),
    (
        "Attainment, last full quarter",
        "scalar",
        f"SELECT sum(revenue) / sum(revenue_target) AS attainment FROM metrics.monthly_kpis WHERE {LAST_QUARTER}",
        {"column_settings": {'["name","attainment"]': {"number_style": "percent", "decimals": 1}}},
        (8, 0, 8, 4),
    ),
    (
        "Orders, last full quarter",
        "scalar",
        f"SELECT sum(orders) AS orders FROM metrics.monthly_kpis WHERE {LAST_QUARTER}",
        {},
        (16, 0, 8, 4),
    ),
    (
        "Revenue vs. target by month",
        "line",
        "SELECT month, sum(revenue) AS revenue, sum(revenue_target) AS target FROM metrics.monthly_kpis GROUP BY 1 ORDER BY 1",
        {"graph.dimensions": ["month"], "graph.metrics": ["revenue", "target"]},
        (0, 4, 24, 7),
    ),
    (
        "Attainment by region, last full quarter",
        "table",
        f"SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target, sum(revenue) / sum(revenue_target) AS attainment "
        f"FROM metrics.monthly_kpis WHERE {LAST_QUARTER} GROUP BY 1 ORDER BY 4",
        {"column_settings": {'["name","attainment"]': {"number_style": "percent", "decimals": 1}}},
        (0, 11, 12, 6),
    ),
    (
        "Revenue by channel, last full quarter",
        "bar",
        "SELECT region, channel, sum(revenue) AS revenue FROM metrics.daily_revenue "
        "WHERE order_date >= date_trunc('quarter', now()) - interval '3 months' AND order_date < date_trunc('quarter', now()) "
        "GROUP BY 1, 2 ORDER BY 1, 2",
        {
            "graph.dimensions": ["region", "channel"],
            "graph.metrics": ["revenue"],
            "stackable.stack_type": "stacked",
        },
        (12, 11, 12, 6),
    ),
]

session: str | None = None


def call(method: str, path: str, body: dict | None = None) -> dict | list:
    req = urllib.request.Request(BASE + path, method=method, headers={"Content-Type": "application/json"})
    if session:
        req.add_header("X-Metabase-Session", session)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as res:
            raw = res.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as err:
        sys.exit(f"[metabase-bootstrap] {method} {path} failed: {err.code} {err.read()[:400]!r}")


def configure_metabot() -> None:
    """Point Metabot at the lab's OpenAI-compatible model, when one is set."""
    model = os.environ.get("LLM_MODEL", "")
    key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "")
    if not model or not (key or base_url):
        print(
            "[metabase-bootstrap] no LLM_MODEL with LLM_API_KEY or LLM_BASE_URL in .env, so Metabot stays off"
        )
        return
    settings = {
        "llm-openai-api-key": key or None,
        "llm-openai-api-base-url": base_url or None,
        "llm-metabot-provider": f"openai/{model}",
        "metabot-enabled?": True,
    }
    for name, value in settings.items():
        call("PUT", f"/api/setting/{urllib.request.quote(name)}", {"value": value})
    print(f"[metabase-bootstrap] Metabot uses {model}")


def main() -> None:
    global session
    token = call("GET", "/api/session/properties").get("setup-token")
    if token:
        session = call(
            "POST",
            "/api/setup",
            {
                "token": token,
                "user": {
                    "email": EMAIL,
                    "password": PASSWORD,
                    "first_name": "Lab",
                    "last_name": "Admin",
                    "site_name": "Dashboard lab",
                },
                "prefs": {"site_name": "Dashboard lab", "site_locale": "en", "allow_tracking": False},
            },
        )["id"]
        print("[metabase-bootstrap] created admin account")
    else:
        session = call("POST", "/api/session", {"username": EMAIL, "password": PASSWORD})["id"]

    dbs = call("GET", "/api/database")["data"]
    db = next((d for d in dbs if d["name"] == DB_NAME), None)
    if db is None:
        db = call(
            "POST",
            "/api/database",
            {"engine": "postgres", "name": DB_NAME, "details": WAREHOUSE, "is_full_sync": True},
        )
        print(f"[metabase-bootstrap] connected {DB_NAME}")
    db_id = db["id"]

    configure_metabot()

    if any(d["name"] == DASHBOARD for d in call("GET", "/api/dashboard")):
        print(f"[metabase-bootstrap] dashboard {DASHBOARD!r} exists")
        return

    dash_id = call(
        "POST", "/api/dashboard", {"name": DASHBOARD, "description": "Strategic view of the lab dataset."}
    )["id"]
    dashcards = []
    for i, (name, display, sql, viz, (col, row, w, h)) in enumerate(CARDS):
        card = call(
            "POST",
            "/api/card",
            {
                "name": name,
                "display": display,
                "visualization_settings": viz,
                "dataset_query": {"type": "native", "database": db_id, "native": {"query": sql}},
            },
        )
        dashcards.append(
            {"id": -(i + 1), "card_id": card["id"], "col": col, "row": row, "size_x": w, "size_y": h}
        )
    call("PUT", f"/api/dashboard/{dash_id}", {"dashcards": dashcards})
    print(f"[metabase-bootstrap] created dashboard {DASHBOARD!r} with {len(dashcards)} cards")


if __name__ == "__main__":
    main()
