"""Turn the lab's live service metrics into access logs in OpenSearch.

Every few seconds this reads the newest row per service from
ops.request_metrics, and writes a sample of log lines that match it: the
same mix of errors, the same latency. An incident in the warehouse (`make
incident`) shows up here as a burst of 5xx lines. On start it backfills the
last hour.

Environment:
  WAREHOUSE_URL   Postgres URL of the warehouse (read-only role is enough)
  OPENSEARCH_URL  default http://opensearch:9200
  LOG_INTERVAL    seconds between writes, default 5
"""

from __future__ import annotations

import datetime as dt
import json
import os
import random
import time
import urllib.error
import urllib.request
import uuid

import psycopg

OPENSEARCH = os.environ.get("OPENSEARCH_URL", "http://opensearch:9200")
INTERVAL = float(os.environ.get("LOG_INTERVAL", "5"))
LINES_PER_SERVICE = 40  # a sample of each interval's requests, not all of them

ROUTES = {
    "web": ["GET /", "GET /products", "GET /products/:id", "GET /cart"],
    "checkout": ["POST /checkout", "GET /checkout/:id", "POST /checkout/:id/confirm"],
    "payments": ["POST /payments", "POST /payments/:id/capture", "POST /refunds"],
    "search": ["GET /search", "GET /search/suggest"],
    "inventory": ["GET /inventory/:sku", "POST /inventory/reserve", "POST /inventory/release"],
}
REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
ERRORS = {
    500: "upstream error: payment gateway timed out",
    502: "bad gateway from inventory service",
    503: "service unavailable: connection pool exhausted",
}

TEMPLATE = {
    "index_patterns": ["lumen-logs-*"],
    "template": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "service": {"type": "keyword"},
                "route": {"type": "keyword"},
                "method": {"type": "keyword"},
                "status": {"type": "integer"},
                "status_class": {"type": "keyword"},
                "latency_ms": {"type": "float"},
                "region": {"type": "keyword"},
                "level": {"type": "keyword"},
                "request_id": {"type": "keyword"},
                "message": {"type": "text"},
            }
        },
    },
}


def request(method: str, path: str, body: bytes | None = None, ctype: str = "application/json") -> dict:
    req = urllib.request.Request(OPENSEARCH + path, data=body, method=method, headers={"Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read() or b"{}")


def lines(ts: dt.datetime, service: str, error_rate: float, p95: float, rng: random.Random) -> list[dict]:
    out = []
    for _ in range(LINES_PER_SERVICE):
        route = rng.choice(ROUTES[service])
        method, path = route.split(" ", 1)
        if rng.random() < error_rate:
            status = rng.choice(list(ERRORS))
            level, message = "error", ERRORS[status]
        else:
            status = rng.choices([200, 201, 204, 304, 404], weights=[70, 10, 5, 10, 5])[0]
            level, message = ("warn", "not found") if status == 404 else ("info", "ok")
        latency = max(1.0, rng.lognormvariate(0, 0.5) * p95 / 2.2)
        stamp = ts - dt.timedelta(milliseconds=rng.randrange(int(INTERVAL * 1000)))
        out.append(
            {
                "@timestamp": stamp.isoformat(),
                "service": service,
                "route": path,
                "method": method,
                "status": status,
                "status_class": f"{status // 100}xx",
                "latency_ms": round(latency, 1),
                "region": rng.choice(REGIONS),
                "level": level,
                "request_id": uuid.UUID(int=rng.getrandbits(128)).hex[:16],
                "message": f"{method} {path} {status} {latency:.0f}ms: {message}",
            }
        )
    return out


def bulk(docs: list[dict]) -> None:
    if not docs:
        return
    body = []
    for d in docs:
        index = "lumen-logs-" + d["@timestamp"][:10].replace("-", ".")
        body.append(json.dumps({"index": {"_index": index}}))
        body.append(json.dumps(d))
    res = request("POST", "/_bulk", ("\n".join(body) + "\n").encode(), "application/x-ndjson")
    if res.get("errors"):
        print("[opensearch-logs] some documents failed to index")


def metrics_since(conn: psycopg.Connection, since: dt.datetime) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ts, service, errors::float / nullif(requests, 0), p95_latency_ms "
            "FROM ops.request_metrics WHERE ts > %s ORDER BY ts",
            (since,),
        )
        return cur.fetchall()


def main() -> None:
    rng = random.Random()
    while True:
        try:
            request("GET", "/_cluster/health?wait_for_status=yellow&timeout=30s")
            break
        except (urllib.error.URLError, ConnectionError):
            print("[opensearch-logs] waiting for OpenSearch")
            time.sleep(3)
    request("PUT", "/_index_template/lumen-logs", json.dumps(TEMPLATE).encode())

    with psycopg.connect(os.environ["WAREHOUSE_URL"], autocommit=True) as conn:
        # Backfill: one batch per minute of the last hour, unless already there.
        try:
            count = request("GET", "/lumen-logs-*/_count").get("count", 0)
        except urllib.error.HTTPError:
            count = 0
        last = dt.datetime.now(dt.UTC) - dt.timedelta(hours=1)
        if count == 0:
            rows = metrics_since(conn, last)
            docs, seen_minute = [], set()
            for ts, service, err, p95 in rows:
                key = (ts.replace(second=0, microsecond=0), service)
                if key in seen_minute:
                    continue
                seen_minute.add(key)
                docs.extend(lines(ts, service, err or 0.0, p95, rng)[:10])
            bulk(docs)
            print(f"[opensearch-logs] backfilled {len(docs):,} lines")
        last = dt.datetime.now(dt.UTC) - dt.timedelta(seconds=INTERVAL * 2)

        print(f"[opensearch-logs] writing logs every {INTERVAL:g}s")
        while True:
            rows = metrics_since(conn, last)
            docs = []
            for ts, service, err, p95 in rows:
                docs.extend(lines(ts, service, err or 0.0, p95, rng))
                last = max(last, ts)
            bulk(docs)
            time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
