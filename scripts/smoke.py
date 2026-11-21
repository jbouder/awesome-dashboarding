"""Check that the running stacks work and agree on the numbers.

Only stacks that are running are checked. Each check prints PASS, FAIL, or
SKIP. The script exits non-zero if anything fails.

The cross-check: last quarter's revenue from the warehouse, from Superset's
SQL API, and from Metabase's dashboard card must match to the cent.
"""

from __future__ import annotations

import base64
import http.cookiejar
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTS = {
    "superset": os.environ.get("SUPERSET_PORT", "8088"),
    "grafana": os.environ.get("GRAFANA_PORT", "3001"),
    "holotable": os.environ.get("HOLOTABLE_PORT", "3000"),
    "metabase": os.environ.get("METABASE_PORT", "3002"),
}
LAST_QUARTER_REVENUE = (
    "SELECT round(sum(revenue), 2) FROM metrics.monthly_kpis "
    "WHERE month >= date_trunc('quarter', now()) - interval '3 months' "
    "AND month < date_trunc('quarter', now())"
)

failures = 0


def report(status: str, name: str, detail: str = "") -> None:
    global failures
    if status == "FAIL":
        failures += 1
    colors = {"PASS": "32", "FAIL": "31", "SKIP": "33"}
    print(f"  \033[{colors[status]}m{status}\033[0m  {name}" + (f": {detail}" if detail else ""))


def compose(*args: str) -> str:
    out = subprocess.run(["docker", "compose", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return out.stdout.strip()


def running(service: str) -> bool:
    return bool(compose("--profile", "*", "ps", "--status", "running", "-q", service))


def sql(query: str) -> str:
    return compose("exec", "-T", "warehouse", "psql", "-U", "lab_ro", "-d", "lab", "-At", "-c", query)


class Client:
    def __init__(self, base: str) -> None:
        self.base = base
        self.headers: dict[str, str] = {"Content-Type": "application/json"}
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def call(self, method: str, path: str, body: dict | None = None, raw: bool = False):
        req = urllib.request.Request(self.base + path, method=method, headers=self.headers)
        data = json.dumps(body).encode() if body is not None else None
        with self.opener.open(req, data, timeout=30) as res:
            payload = res.read()
            return payload if raw else json.loads(payload or b"{}")


def check(name: str):
    """Run a check function, turning any exception into a FAIL."""

    def wrap(fn):
        try:
            fn()
        except (urllib.error.URLError, KeyError, IndexError, ValueError, TypeError) as exc:
            report("FAIL", name, f"{type(exc).__name__}: {exc}"[:200])
        return fn

    return wrap


def main() -> int:
    print("Warehouse")
    if not running("warehouse"):
        report("FAIL", "warehouse", "not running. Start a stack with: make up <stack>")
        return 1
    expected = sql(LAST_QUARTER_REVENUE)
    orders = int(sql("SELECT count(*) FROM shop.orders") or 0)
    report("PASS" if orders > 0 else "FAIL", "seed data loaded", f"{orders:,} orders")
    lag = sql("SELECT coalesce(extract(epoch FROM now() - max(ts))::int, -1) FROM ops.request_metrics")
    fresh = lag.lstrip("-").isdigit() and 0 <= int(lag) <= 30
    report("PASS" if fresh else "FAIL", "live metrics streaming", f"newest row {lag}s old")
    report("PASS", "last quarter's revenue", f"${float(expected):,.2f}")

    print("Superset")
    if not running("superset"):
        report("SKIP", "superset", "not running")
    else:

        @check("superset")
        def _superset() -> None:
            c = Client(f"http://localhost:{PORTS['superset']}")
            token = c.call(
                "POST",
                "/api/v1/security/login",
                {
                    "username": "admin",
                    "password": os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin"),
                    "provider": "db",
                    "refresh": False,
                },
            )["access_token"]
            c.headers["Authorization"] = f"Bearer {token}"
            for slug in ("executive-kpis", "revenue-analysis"):
                charts = c.call("GET", f"/api/v1/dashboard/{slug}/charts")["result"]
                report("PASS" if len(charts) == 5 else "FAIL", f"dashboard {slug}", f"{len(charts)} charts")
            q = json.dumps({"filters": [{"col": "database_name", "opr": "eq", "value": "Lab warehouse"}]})
            db_id = c.call("GET", f"/api/v1/database/?q={urllib.request.quote(q)}")["result"][0]["id"]
            res = c.call(
                "POST",
                "/api/v1/sqllab/execute/",
                {"database_id": db_id, "sql": LAST_QUARTER_REVENUE, "runAsync": False, "schema": "metrics"},
            )
            got = f"{float(next(iter(res['data'][0].values()))):.2f}"
            report(
                "PASS" if got == expected else "FAIL", "revenue matches the warehouse", f"${float(got):,.2f}"
            )

    print("Metabase")
    if not running("metabase"):
        report("SKIP", "metabase", "not running")
    else:

        @check("metabase")
        def _metabase() -> None:
            c = Client(f"http://localhost:{PORTS['metabase']}")
            session = c.call(
                "POST",
                "/api/session",
                {
                    "username": "admin@dashlab.local",
                    "password": os.environ.get("METABASE_ADMIN_PASSWORD", "dashlab-admin-1"),
                },
            )["id"]
            c.headers["X-Metabase-Session"] = session
            dash = next(d for d in c.call("GET", "/api/dashboard") if d["name"] == "Lumen Supply overview")
            cards = c.call("GET", f"/api/dashboard/{dash['id']}")["dashcards"]
            report(
                "PASS" if len(cards) == 6 else "FAIL",
                "dashboard Lumen Supply overview",
                f"{len(cards)} cards",
            )
            card = next(d["card"] for d in cards if d["card"]["name"] == "Revenue, last full quarter")
            rows = c.call("POST", f"/api/card/{card['id']}/query")["data"]["rows"]
            got = f"{float(rows[0][0]):.2f}"
            report(
                "PASS" if got == expected else "FAIL", "revenue matches the warehouse", f"${float(got):,.2f}"
            )

    print("Grafana")
    if not running("grafana"):
        report("SKIP", "grafana", "not running")
    else:

        @check("grafana")
        def _grafana() -> None:
            c = Client(f"http://localhost:{PORTS['grafana']}")
            password = os.environ.get("GRAFANA_ADMIN_PASSWORD", "admin")
            c.headers["Authorization"] = "Basic " + base64.b64encode(f"admin:{password}".encode()).decode()
            health = c.call("GET", "/api/datasources/uid/lab-warehouse/health")
            report(
                "PASS" if health.get("status") == "OK" else "FAIL",
                "datasource Lab warehouse",
                health.get("message", ""),
            )
            dash = c.call("GET", "/api/dashboards/uid/lab-service-health")["dashboard"]
            report("PASS", "dashboard Service health", f"{len(dash['panels'])} panels")
            rule = c.call("GET", "/api/v1/provisioning/alert-rules/lab-high-error-rate")
            report("PASS" if rule.get("title") == "High error rate" else "FAIL", "alert rule High error rate")

    print("Holotable")
    if not running("holotable"):
        report("SKIP", "holotable", "not running")
    else:

        @check("holotable")
        def _holotable() -> None:
            c = Client(f"http://localhost:{PORTS['holotable']}")
            c.call("GET", "/api/auth/login", raw=True)
            for source in ("lab-metrics", "lab-ops"):
                res = c.call("POST", f"/api/sources/{source}/test")
                read_only = res.get("readOnly", {}).get("verdict") == "refused"
                report(
                    "PASS" if res.get("ok") and read_only else "FAIL",
                    f"source {source}",
                    "connects, read-only" if read_only else res.get("message", ""),
                )

    print()
    if failures:
        print(f"{failures} check(s) failed.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
