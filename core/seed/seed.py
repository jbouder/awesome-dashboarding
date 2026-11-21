"""Generate the Lumen Supply dataset and load it into the warehouse.

Deterministic: the same SEED and the same day give the same data. Dates are
relative to today, so the data always runs up to the present.

The data has a story to find. In the last full quarter, revenue in EMEA
falls well short of target because orders through the partner channel there
dropped by about two thirds. Ask any tool "What drove the drop in revenue
last quarter?" and see whether it finds that.

Environment:
  WAREHOUSE_URL  Postgres URL of the warehouse (owner role)
  SEED           random seed, default 42
  SEED_FORCE     1 to reseed even if data is already loaded
"""

from __future__ import annotations

import datetime as dt
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import psycopg

HERE = Path(__file__).parent
SEED = int(os.environ.get("SEED", "42"))
DATA_VERSION = 1

SEGMENTS = [("Consumer", 0.70), ("SMB", 0.22), ("Enterprise", 0.08)]
REGIONS = [("North America", 0.45), ("EMEA", 0.30), ("APAC", 0.17), ("LATAM", 0.08)]
ACQUISITION = [("Organic", 0.40), ("Paid search", 0.30), ("Referral", 0.15), ("Partner", 0.15)]

CATEGORIES = {
    "Camping": (
        ["Trail", "Summit", "Ridge", "Basecamp", "Alpine"],
        ["Tent", "Sleeping Bag", "Stove", "Backpack", "Hammock"],
        (40, 420),
    ),
    "Apparel": (
        ["Storm", "Drift", "Canyon", "Polar", "Breeze"],
        ["Jacket", "Fleece", "Rain Shell", "Base Layer", "Hiking Pants"],
        (25, 220),
    ),
    "Lighting": (
        ["Lumen", "Beacon", "Glow", "Halo", "Spark"],
        ["Headlamp", "Lantern", "Flashlight", "String Lights", "Solar Lamp"],
        (15, 140),
    ),
    "Kitchen": (
        ["Hearth", "Copper", "Ember", "Field", "Harvest"],
        ["Cookset", "Kettle", "Cooler", "Water Filter", "French Press"],
        (20, 260),
    ),
    "Fitness": (
        ["Pulse", "Stride", "Core", "Peak", "Tempo"],
        ["Yoga Mat", "Kettlebell", "Trekking Poles", "Resistance Bands", "Foam Roller"],
        (15, 160),
    ),
    "Electronics": (
        ["Signal", "Orbit", "Vector", "Echo", "Nova"],
        ["GPS Watch", "Power Bank", "Radio", "Action Camera", "Speaker"],
        (35, 480),
    ),
}

SERVICES = {
    # name: (requests per 10s at peak, base error rate, base p95 ms)
    "web": (1200, 0.004, 180.0),
    "checkout": (260, 0.006, 320.0),
    "payments": (210, 0.003, 410.0),
    "search": (900, 0.002, 140.0),
    "inventory": (380, 0.005, 220.0),
}


def pick(rng: random.Random, weighted: list[tuple[str, float]]) -> str:
    names, weights = zip(*weighted, strict=True)
    return rng.choices(names, weights=weights)[0]


def month_start(d: dt.date) -> dt.date:
    return d.replace(day=1)


def add_months(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    return dt.date(d.year + y, m + 1, 1)


def last_full_quarter(today: dt.date) -> tuple[dt.date, dt.date]:
    q_start = dt.date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)
    prev_start = add_months(q_start, -3)
    return prev_start, q_start  # [start, end)


def generate(today: dt.date):
    rng = random.Random(SEED)
    start = add_months(month_start(today), -24)
    story_start, story_end = last_full_quarter(today)
    days = (today - start).days + 1

    # Products
    products = []
    pid = 1
    for category, (adjectives, nouns, (lo, hi)) in CATEGORIES.items():
        for noun in nouns:
            for adjective in rng.sample(adjectives, 2):
                price = round(rng.uniform(lo, hi), 2)
                cost = round(price * rng.uniform(0.38, 0.62), 2)
                products.append((pid, f"{adjective} {noun}", category, price, cost))
                pid += 1

    # Customers, with more sign-ups as the business grows
    customers = []
    for cid in range(1, 6001):
        offset = int(days * math.sqrt(rng.random()))
        signed_up = start + dt.timedelta(days=min(offset, days - 1))
        if cid <= 400:  # an existing base on day one
            signed_up = start
        customers.append((cid, pick(rng, SEGMENTS), pick(rng, REGIONS), pick(rng, ACQUISITION), signed_up))
    customers.sort(key=lambda c: c[4])
    signup_days = [(c[4] - start).days for c in customers]

    # Orders and items
    orders, items = [], []
    oid = 1
    for day in range(days):
        date = start + dt.timedelta(days=day)
        growth = 1.0 + 0.32 * day / 365
        season = 1.0 + 0.18 * math.sin(2 * math.pi * (date.timetuple().tm_yday - 100) / 365)
        if date.month in (11, 12):
            season += 0.35
        weekday = 1.12 if date.weekday() < 5 else 0.82
        expected = 52 * growth * season * weekday
        n = max(0, int(rng.gauss(expected, math.sqrt(expected))))

        # customers who have signed up by this day
        hi = 0
        while hi < len(customers) and signup_days[hi] <= day:
            hi += 1
        hi = max(hi, 1)

        in_story = story_start <= date < story_end
        for _ in range(n):
            cust = customers[rng.randrange(hi)]
            cid, segment, region = cust[0], cust[1], cust[2]
            if segment == "Enterprise":
                channel = pick(rng, [("web", 0.25), ("mobile", 0.05), ("partner", 0.70)])
            else:
                channel = pick(rng, [("web", 0.58), ("mobile", 0.32), ("partner", 0.10)])
            if in_story and region == "EMEA" and channel == "partner" and rng.random() < 0.8:
                continue  # an EMEA partner contract ended: the story
            hour = min(23, max(0, int(rng.gauss(14, 4))))
            ordered_at = dt.datetime.combine(
                date, dt.time(hour, rng.randrange(60), rng.randrange(60)), tzinfo=dt.UTC
            )
            if ordered_at > dt.datetime.now(dt.UTC):
                continue
            status = pick(rng, [("completed", 0.93), ("refunded", 0.04), ("canceled", 0.03)])
            orders.append((oid, cid, ordered_at, status, channel, region))

            for product in rng.sample(products, rng.choice([1, 1, 1, 2, 2, 3, 4])):
                if segment == "Enterprise":
                    qty = rng.randint(3, 14)
                    discount = rng.choice([0.10, 0.15, 0.15, 0.20])
                elif segment == "SMB":
                    qty = rng.randint(1, 8)
                    discount = rng.choice([0, 0, 0.05, 0.10])
                else:
                    qty = rng.choice([1, 1, 1, 2, 2, 3])
                    discount = rng.choice([0, 0, 0, 0, 0.10, 0.20])
                items.append((oid, product[0], qty, product[3], discount))
            oid += 1

    # Targets: last year's month plus 18%, or a plan near actuals in year one
    order_meta = {o[0]: (o[2].date().replace(day=1), o[5], o[3]) for o in orders}
    actual = defaultdict(float)
    for order_id, _product_id, qty, price, discount in items:
        month, region, status = order_meta[order_id]
        if status == "completed":
            actual[(month, region)] += qty * float(price) * (1 - discount)
    targets = []
    trng = random.Random(SEED + 1)
    month = start
    while month <= month_start(today):
        for region, _ in REGIONS:
            prior = actual.get((add_months(month, -12), region))
            if prior:
                target = prior * 1.18
            else:
                base = actual.get((month, region), 0.0)
                if story_start <= month < story_end and region == "EMEA":
                    base *= 1.6  # the plan did not know about the partner loss
                target = base * trng.uniform(0.97, 1.06)
            targets.append((month, region, round(target, 2)))
        month = add_months(month, 1)

    return customers, products, orders, items, targets, (story_start, story_end)


def backfill_ops(conn: psycopg.Connection, hours: int = 6) -> int:
    """Write the last few hours of service metrics so charts are not empty."""
    now = dt.datetime.now(dt.UTC).replace(microsecond=0)
    start = now - dt.timedelta(hours=hours)
    rng = random.Random(SEED + 2)
    rows = []
    t = start
    while t <= now:
        hour = t.hour + t.minute / 60
        diurnal = 0.65 + 0.35 * math.sin(2 * math.pi * (hour - 8) / 24)
        for service, (peak, err, p95) in SERVICES.items():
            req = max(1, int(rng.gauss(peak * diurnal, peak * 0.05)))
            errors = max(0, round(rng.gauss(req * err, math.sqrt(req * err))))
            rows.append((t, service, req, errors, round(rng.gauss(p95, p95 * 0.08), 1)))
        t += dt.timedelta(seconds=10)
    with conn.cursor() as cur:
        cur.execute("TRUNCATE ops.request_metrics")
        with cur.copy(
            "COPY ops.request_metrics (ts, service, requests, errors, p95_latency_ms) FROM STDIN"
        ) as copy:
            for row in rows:
                copy.write_row(row)
    return len(rows)


def main() -> int:
    url = os.environ["WAREHOUSE_URL"]
    force = os.environ.get("SEED_FORCE") == "1"
    with psycopg.connect(url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS public.lab_seed (version int, seed int, seeded_on date, seeded_at timestamptz DEFAULT now())"
            )
            cur.execute(
                "SELECT version, seed, seeded_on FROM public.lab_seed ORDER BY seeded_at DESC LIMIT 1"
            )
            row = cur.fetchone()
        conn.commit()
        if row and row[0] == DATA_VERSION and row[1] == SEED and not force:
            print(
                f"[seed] data already loaded (seed {SEED}, generated {row[2]}). Run `make reseed` to regenerate."
            )
            return 0

        today = dt.datetime.now(dt.UTC).date()
        print(f"[seed] generating with seed {SEED} for {today}")
        customers, products, orders, items, targets, story = generate(today)

        with conn.cursor() as cur:
            cur.execute((HERE / "schema.sql").read_text())
            for table, cols, rows in [
                ("shop.customers", "customer_id, segment, region, channel, signed_up_at", customers),
                ("shop.products", "product_id, name, category, unit_price, unit_cost", products),
                ("shop.orders", "order_id, customer_id, ordered_at, status, channel, region", orders),
                ("shop.order_items", "order_id, product_id, quantity, unit_price, discount", items),
                ("shop.targets", "month, region, revenue_target", targets),
            ]:
                with cur.copy(f"COPY {table} ({cols}) FROM STDIN") as copy:
                    for r in rows:
                        copy.write_row(r)
                print(f"[seed] {table}: {len(rows):,} rows")
            cur.execute((HERE / "semantic.sql").read_text())
        n = backfill_ops(conn)
        print(f"[seed] ops.request_metrics: {n:,} rows of history")
        with conn.cursor() as cur:
            cur.execute("ANALYZE")
            cur.execute(
                "INSERT INTO public.lab_seed (version, seed, seeded_on) VALUES (%s, %s, %s)",
                (DATA_VERSION, SEED, today),
            )
        conn.commit()
    print(f"[seed] done. The story quarter is {story[0]} to {story[1]}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
