"""Write live service metrics to ops.request_metrics every few seconds.

Rows from an active incident in ops.incidents get more errors or more
latency, so operational dashboards have something to alert on.

Environment:
  WAREHOUSE_URL    Postgres URL of the warehouse (owner role)
  STREAM_INTERVAL  seconds between writes, default 5
  STREAM_RETAIN    hours of metrics to keep, default 24
"""

from __future__ import annotations

import datetime as dt
import math
import os
import random
import time

import psycopg
from seed import SERVICES

INTERVAL = float(os.environ.get("STREAM_INTERVAL", "5"))
RETAIN_HOURS = int(os.environ.get("STREAM_RETAIN", "24"))


def tick(conn: psycopg.Connection, rng: random.Random) -> None:
    now = dt.datetime.now(dt.UTC)
    hour = now.hour + now.minute / 60
    diurnal = 0.65 + 0.35 * math.sin(2 * math.pi * (hour - 8) / 24)
    scale = INTERVAL / 10  # SERVICES rates are per 10 seconds
    with conn.cursor() as cur:
        cur.execute("SELECT service, kind FROM ops.incidents WHERE now() BETWEEN started_at AND ends_at")
        active = {(s, k) for s, k in cur.fetchall()}
        rows = []
        for service, (peak, err, p95) in SERVICES.items():
            req = max(1, int(rng.gauss(peak * diurnal * scale, peak * scale * 0.05)))
            if (service, "errors") in active:
                err = 0.12
            if (service, "latency") in active:
                p95 *= 6
            errors = max(0, round(rng.gauss(req * err, math.sqrt(req * err))))
            rows.append((now, service, req, errors, round(rng.gauss(p95, p95 * 0.08), 1)))
        cur.executemany(
            "INSERT INTO ops.request_metrics (ts, service, requests, errors, p95_latency_ms) VALUES (%s, %s, %s, %s, %s)",
            rows,
        )
    conn.commit()


def main() -> None:
    rng = random.Random()
    url = os.environ["WAREHOUSE_URL"]
    print(f"[stream] writing service metrics every {INTERVAL:g}s")
    last_prune = 0.0
    while True:
        try:
            with psycopg.connect(url) as conn:
                while True:
                    tick(conn, rng)
                    if time.monotonic() - last_prune > 600:
                        with conn.cursor() as cur:
                            cur.execute(
                                "DELETE FROM ops.request_metrics WHERE ts < now() - make_interval(hours => %s)",
                                (RETAIN_HOURS,),
                            )
                        conn.commit()
                        last_prune = time.monotonic()
                    time.sleep(INTERVAL)
        except psycopg.Error as exc:
            # The seed job may be recreating tables. Wait and reconnect.
            print(f"[stream] {type(exc).__name__}, retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
