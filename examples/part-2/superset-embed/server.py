"""A customer-facing page that embeds Superset's Executive KPIs dashboard.

The browser never sees Superset credentials. It asks this server for a guest
token; the server signs in to Superset as the admin, makes sure the
dashboard is embeddable, and asks Superset for a short-lived guest token
scoped to that one dashboard. When a region is picked, the token carries a
row-level security clause, so Superset itself filters every chart.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SUPERSET = os.environ.get("SUPERSET_URL", "http://superset:8088")
DASHBOARD = os.environ.get("DASHBOARD_SLUG", "executive-kpis")
REGIONS = {"North America", "EMEA", "APAC", "LATAM"}
PAGE = (Path(__file__).parent / "index.html").read_text()


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    req = urllib.request.Request(SUPERSET + path, method=method, headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data, timeout=30) as res:
        return json.loads(res.read() or b"{}")


def admin_token() -> str:
    return call(
        "POST",
        "/api/v1/security/login",
        {
            "username": os.environ.get("SUPERSET_ADMIN_USERNAME", "admin"),
            "password": os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin"),
            "provider": "db",
            "refresh": False,
        },
    )["access_token"]


def embedded_uuid(token: str) -> str:
    try:
        return call("GET", f"/api/v1/dashboard/{DASHBOARD}/embedded", token=token)["result"]["uuid"]
    except urllib.error.HTTPError as err:
        if err.code != 404:
            raise
    return call("POST", f"/api/v1/dashboard/{DASHBOARD}/embedded", {"allowed_domains": []}, token=token)[
        "result"
    ]["uuid"]


def guest_token(region: str | None) -> dict:
    token = admin_token()
    uuid = embedded_uuid(token)
    rls = [{"clause": f"region = '{region}'"}] if region else []
    guest = call(
        "POST",
        "/api/v1/security/guest_token/",
        {
            "user": {"username": "embed-viewer", "first_name": "Embedded", "last_name": "Viewer"},
            "resources": [{"type": "dashboard", "id": uuid}],
            "rls": rls,
        },
        token=token,
    )["token"]
    return {"token": guest, "uuid": uuid}


class Handler(BaseHTTPRequestHandler):
    def send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        url = urllib.parse.urlparse(self.path)
        if url.path == "/":
            self.send(200, PAGE.encode(), "text/html; charset=utf-8")
        elif url.path == "/guest-token":
            region = urllib.parse.parse_qs(url.query).get("region", [""])[0] or None
            if region and region not in REGIONS:
                self.send(400, b'{"error": "unknown region"}', "application/json")
                return
            try:
                self.send(200, json.dumps(guest_token(region)).encode(), "application/json")
            except (urllib.error.URLError, KeyError) as err:
                self.send(502, json.dumps({"error": f"Superset said no: {err}"}).encode(), "application/json")
        else:
            self.send(404, b"not found", "text/plain")

    def log_message(self, fmt: str, *args) -> None:
        print(f"[superset-embed] {fmt % args}", flush=True)


if __name__ == "__main__":
    print("[superset-embed] serving on :8000", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
