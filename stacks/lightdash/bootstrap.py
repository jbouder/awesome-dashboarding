"""Set up Lightdash: the admin, the organization, and the Lumen Supply project.

The project reads the dbt project mounted at /usr/app/dbt and queries the
warehouse as the read-only role. A second run signs in and changes nothing.
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("LIGHTDASH_URL", "http://lightdash:8080")
EMAIL = os.environ["LIGHTDASH_ADMIN_EMAIL"]
PASSWORD = os.environ["LIGHTDASH_ADMIN_PASSWORD"]
PROJECT = "Lumen Supply"

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def call(method: str, path: str, body: dict | None = None, ok_errors: tuple[int, ...] = ()) -> dict:
    req = urllib.request.Request(BASE + path, method=method, headers={"Content-Type": "application/json"})
    data = json.dumps(body).encode() if body is not None else None
    try:
        with opener.open(req, data, timeout=120) as res:
            return json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as err:
        if err.code in ok_errors:
            return {"status": "error", "code": err.code}
        sys.exit(f"[lightdash-bootstrap] {method} {path} failed: {err.code} {err.read()[:500]!r}")


def main() -> None:
    signed_in = call(
        "POST", "/api/v1/login", {"email": EMAIL, "password": PASSWORD}, ok_errors=(401, 403, 404)
    )
    if signed_in.get("status") != "ok":
        call(
            "POST",
            "/api/v1/user",
            {"firstName": "Lab", "lastName": "Admin", "email": EMAIL, "password": PASSWORD},
        )
        print("[lightdash-bootstrap] created admin account")

    user = call("GET", "/api/v1/user")["results"]
    if not user.get("organizationUuid"):
        call("PUT", "/api/v1/org", {"name": "Dashboard lab"})
        print("[lightdash-bootstrap] created organization")

    projects = call("GET", "/api/v1/org/projects")["results"]
    project = next((p for p in projects if p["name"] == PROJECT), None)
    if project:
        uuid = project["projectUuid"]
        print(f"[lightdash-bootstrap] project {PROJECT!r} exists")
    else:
        created = call(
            "POST",
            "/api/v1/org/projects",
            {
                "name": PROJECT,
                "type": "DEFAULT",
                "dbtVersion": "v1.9",
                "dbtConnection": {"type": "dbt", "project_dir": "/usr/app/dbt"},
                "warehouseConnection": {
                    "type": "postgres",
                    "host": "warehouse",
                    "port": 5432,
                    "user": "lab_ro",
                    "password": "lab_ro",
                    "dbname": "lab",
                    "schema": "metrics",
                    "sslmode": "disable",
                },
            },
        )["results"]
        uuid = created["project"]["projectUuid"] if "project" in created else created["projectUuid"]
        print(f"[lightdash-bootstrap] created project {PROJECT!r}")

    if len(compiled(uuid)) >= 3:
        print("[lightdash-bootstrap] project already compiled")
        return
    call("POST", f"/api/v1/projects/{uuid}/refresh")
    for _ in range(120):
        names = compiled(uuid)
        if len(names) >= 3:
            print(f"[lightdash-bootstrap] compiled: {', '.join(sorted(names))}")
            return
        time.sleep(5)
    sys.exit("[lightdash-bootstrap] the dbt project did not compile in time. See: make logs lightdash")


def compiled(uuid: str) -> list[str]:
    """Names of the project's explores that compiled without errors."""
    explores = call("GET", f"/api/v1/projects/{uuid}/explores", ok_errors=(400, 404, 500))
    return [e.get("name") for e in explores.get("results", []) if not e.get("errors")]


if __name__ == "__main__":
    main()
