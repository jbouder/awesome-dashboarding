"""Write the example data: CSV extracts and the snapshot the static examples embed.

Runs in the seed image against the warehouse (see `make extract`). Writes:

  examples/01-claude-artifact/extracts/raw/        order lines and targets, raw
  examples/01-claude-artifact/extracts/semantic/   the governed metrics views
  examples/_shared/snapshot.json                   aggregates for static pages

and refreshes the snapshot inside every HTML file under examples/ that has a
<script id="lumen-snapshot" type="application/json"> block.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
from decimal import Decimal
from pathlib import Path

import psycopg

ROOT = Path(os.environ.get("EXAMPLES_DIR", "/examples"))
URL = os.environ["WAREHOUSE_URL"]

LAST_Q = "(date_trunc('quarter', now()) - interval '3 months')"
THIS_Q = "(date_trunc('quarter', now()))"
PREV_Q = "(date_trunc('quarter', now()) - interval '6 months')"


def rows(cur, sql: str) -> list[dict]:
    cur.execute(sql)
    names = [c.name for c in cur.description]
    out = []
    for r in cur.fetchall():
        item = {}
        for k, v in zip(names, r, strict=True):
            if isinstance(v, Decimal):
                v = float(v)
            elif isinstance(v, dt.datetime | dt.date):
                v = v.isoformat()
            item[k] = v
        out.append(item)
    return out


def write_csv(cur, path: Path, sql: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    cur.execute(sql)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([c.name for c in cur.description])
        n = 0
        for r in cur.fetchall():
            w.writerow(["" if v is None else v for v in r])
            n += 1
    return n


def quarter_label(d: dt.date) -> str:
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"


def main() -> None:
    with psycopg.connect(URL) as conn, conn.cursor() as cur:
        since = f"{THIS_Q} - interval '15 months'"
        extracts = ROOT / "01-claude-artifact" / "extracts"
        counts = {
            "raw/lumen_order_lines.csv": write_csv(
                cur,
                extracts / "raw" / "lumen_order_lines.csv",
                f"""
                SELECT o.order_id, o.ordered_at::date AS order_date, o.status, o.channel, o.region,
                       c.segment, p.name AS product, p.category, i.quantity, i.unit_price, i.discount
                FROM shop.orders o
                JOIN shop.order_items i USING (order_id)
                JOIN shop.customers c USING (customer_id)
                JOIN shop.products p USING (product_id)
                WHERE o.ordered_at >= {since}
                ORDER BY o.ordered_at, o.order_id""",
            ),
            "raw/lumen_targets.csv": write_csv(
                cur,
                extracts / "raw" / "lumen_targets.csv",
                f"""
                SELECT month, region, revenue_target FROM shop.targets
                WHERE month >= {since} ORDER BY month, region""",
            ),
            "semantic/monthly_kpis.csv": write_csv(
                cur,
                extracts / "semantic" / "monthly_kpis.csv",
                f"""
                SELECT month, region, revenue, revenue_target, attainment, orders, active_customers,
                       avg_order_value
                FROM metrics.monthly_kpis WHERE month >= {since} ORDER BY month, region""",
            ),
            "semantic/daily_revenue.csv": write_csv(
                cur,
                extracts / "semantic" / "daily_revenue.csv",
                f"""
                SELECT order_date, region, segment, channel, revenue, gross_margin, orders, customers
                FROM metrics.daily_revenue WHERE order_date >= {since}
                ORDER BY order_date, region, segment, channel""",
            ),
        }

        cur.execute(f"SELECT {LAST_Q}::date, {PREV_Q}::date, max(ordered_at) FROM shop.orders")
        last_q, prev_q, as_of = cur.fetchone()

        def kpis(start: str, end: str) -> dict:
            return rows(
                cur,
                f"""
                SELECT sum(revenue) AS revenue, sum(revenue_target) AS target,
                       sum(revenue) / sum(revenue_target) AS attainment, sum(orders) AS orders
                FROM metrics.monthly_kpis WHERE month >= {start} AND month < {end}""",
            )[0]

        snapshot = {
            "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "data_as_of": as_of.isoformat(timespec="minutes"),
            "period": quarter_label(last_q),
            "previous_period": quarter_label(prev_q),
            "kpis": {"current": kpis(LAST_Q, THIS_Q), "previous": kpis(PREV_Q, LAST_Q)},
            "monthly": rows(
                cur,
                f"""
                SELECT to_char(month, 'YYYY-MM') AS month, region, revenue, revenue_target AS target
                FROM metrics.monthly_kpis
                WHERE month >= {THIS_Q} - interval '12 months' AND month < date_trunc('month', now())
                ORDER BY month, region""",
            ),
            "regions": rows(
                cur,
                f"""
                SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target,
                       sum(revenue) / sum(revenue_target) AS attainment, sum(orders) AS orders
                FROM metrics.monthly_kpis WHERE month >= {LAST_Q} AND month < {THIS_Q}
                GROUP BY region ORDER BY attainment""",
            ),
            "channels": rows(
                cur,
                f"""
                SELECT to_char(date_trunc('quarter', order_date), 'YYYY "Q"Q') AS quarter, region, channel,
                       sum(revenue) AS revenue
                FROM metrics.daily_revenue
                WHERE order_date >= {THIS_Q} - interval '12 months' AND order_date < {THIS_Q}
                GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""",
            ),
            "products": rows(
                cur,
                f"""
                SELECT region, channel, product, category, sum(units) AS units, sum(revenue) AS revenue
                FROM metrics.line_facts
                WHERE ordered_at >= {LAST_Q} AND ordered_at < {THIS_Q}
                GROUP BY 1, 2, 3, 4 ORDER BY revenue DESC""",
            ),
            "weekly": rows(
                cur,
                f"""
                SELECT date_trunc('week', order_date)::date AS week, region, channel, sum(revenue) AS revenue
                FROM metrics.daily_revenue
                WHERE order_date >= {THIS_Q} - interval '6 months' AND order_date < date_trunc('week', now())
                GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""",
            ),
            "raw_vs_semantic": rows(
                cur,
                f"""
                SELECT
                  (SELECT sum(i.quantity * i.unit_price) FROM shop.orders o JOIN shop.order_items i USING (order_id)
                   WHERE o.ordered_at >= {LAST_Q} AND o.ordered_at < {THIS_Q}) AS raw_all_lines_no_discount,
                  (SELECT sum(revenue) FROM metrics.monthly_kpis
                   WHERE month >= {LAST_Q} AND month < {THIS_Q}) AS semantic_revenue""",
            )[0],
        }

    (ROOT / "_shared").mkdir(parents=True, exist_ok=True)
    (ROOT / "_shared" / "snapshot.json").write_text(json.dumps(snapshot, indent=1) + "\n")
    print(f"[extract] snapshot for {snapshot['period']}, data as of {snapshot['data_as_of']}")
    for name, n in counts.items():
        print(f"[extract] {name}: {n:,} rows")

    pattern = re.compile(r'(<script id="lumen-snapshot" type="application/json">)(.*?)(</script>)', re.DOTALL)
    compact = json.dumps(snapshot, separators=(",", ":"))
    for page in ROOT.rglob("*.html"):
        text = page.read_text()
        if pattern.search(text):
            page.write_text(pattern.sub(lambda m: m.group(1) + compact + m.group(3), text))
            print(f"[extract] refreshed {page.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
