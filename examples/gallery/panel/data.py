"""Queries for the Lumen Supply dashboard.

Every query reads the `metrics` views, so the numbers match the rest of the
lab. Postgres numeric columns come back as Decimal; `_frame` turns them into
floats before anything is charted.
"""

import os
import time
from decimal import Decimal

import pandas as pd
import psycopg

URL = os.environ.get("WAREHOUSE_URL", "postgresql://lab_ro:lab_ro@localhost:5433/lab")
CACHE_SECONDS = 300

# The last calendar quarter that has ended, and the one before it.
LAST_Q = "date_trunc('quarter', now()) - interval '3 months'"
THIS_Q = "date_trunc('quarter', now())"
PREV_Q = "date_trunc('quarter', now()) - interval '6 months'"

_cache: dict = {}


def _frame(sql: str, params: dict | None = None) -> pd.DataFrame:
    with psycopg.connect(URL) as conn, conn.cursor() as cur:
        cur.execute(sql, params or {})
        cols = [c.name for c in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=cols)
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


def _cached(key, fn):
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
        return hit[1]
    value = fn()
    _cache[key] = (time.monotonic(), value)
    return value


def header() -> dict:
    """The period label and the time of the latest order."""

    def run():
        df = _frame(
            f"""
            select to_char({LAST_Q}, '"Q"Q YYYY') as period,
                   (select max(ordered_at) from metrics.order_facts) as as_of
            """
        )
        return df.iloc[0].to_dict()

    return _cached("header", run)


def kpis() -> dict:
    """Revenue, target, attainment, and orders, last full quarter and the one before."""

    def run():
        df = _frame(
            f"""
            select case when month >= {LAST_Q} then 'last' else 'prev' end as q,
                   sum(revenue) as revenue,
                   sum(revenue_target) as target,
                   sum(orders) as orders
            from metrics.monthly_kpis
            where month >= {PREV_Q} and month < {THIS_Q}
            group by 1
            """
        ).set_index("q")
        last, prev = df.loc["last"], df.loc["prev"]
        return {
            "revenue": last.revenue,
            "revenue_change": last.revenue / prev.revenue - 1,
            "target": last.target,
            "gap": last.revenue - last.target,
            "attainment": last.revenue / last.target,
            "orders": int(last.orders),
            "orders_change": last.orders / prev.orders - 1,
        }

    return _cached("kpis", run)


def monthly() -> pd.DataFrame:
    """Revenue and target by month, the last 12 full months."""
    return _cached(
        "monthly",
        lambda: _frame(
            """
            select month, sum(revenue) as revenue, sum(revenue_target) as target
            from metrics.monthly_kpis
            where month >= date_trunc('month', now()) - interval '12 months'
              and month < date_trunc('month', now())
            group by month order by month
            """
        ),
    )


def attainment_by_region() -> pd.DataFrame:
    """Attainment by region, last full quarter, worst first."""
    return _cached(
        "attainment",
        lambda: _frame(
            f"""
            select region, sum(revenue) as revenue, sum(revenue_target) as target,
                   sum(revenue) / sum(revenue_target) as attainment
            from metrics.monthly_kpis
            where month >= {LAST_Q} and month < {THIS_Q}
            group by region order by attainment
            """
        ),
    )


def channel_by_quarter(region: str | None = None) -> pd.DataFrame:
    """Revenue by channel by quarter, last four full quarters."""
    return _cached(
        ("channel", region),
        lambda: _frame(
            f"""
            select to_char(date_trunc('quarter', order_date), '"Q"Q YYYY') as quarter,
                   date_trunc('quarter', order_date) as quarter_start,
                   channel, sum(revenue) as revenue
            from metrics.daily_revenue
            where order_date >= {THIS_Q} - interval '12 months' and order_date < {THIS_Q}
              and (%(region)s::text is null or region = %(region)s)
            group by 1, 2, 3 order by 2, 3
            """,
            {"region": region},
        ),
    )


def top_products(region: str | None = None, channel: str | None = None) -> pd.DataFrame:
    """Products by revenue, last full quarter, for the selected region and channel."""
    return _cached(
        ("products", region, channel),
        lambda: _frame(
            f"""
            select product, category, sum(units) as units, sum(revenue) as revenue
            from metrics.line_facts
            where order_date >= {LAST_Q} and order_date < {THIS_Q}
              and (%(region)s::text is null or region = %(region)s)
              and (%(channel)s::text is null or channel = %(channel)s)
            group by product, category order by revenue desc
            """,
            {"region": region, "channel": channel},
        ),
    )


def orders_last_quarter() -> pd.DataFrame:
    """One row per completed order in the last full quarter."""
    return _cached(
        "orders",
        lambda: _frame(
            f"""
            select order_id, order_date, region, channel, segment,
                   revenue, gross_margin, units
            from metrics.order_facts
            where order_date >= {LAST_Q} and order_date < {THIS_Q}
            """
        ),
    )


def live_error_rate() -> pd.DataFrame:
    """Error rate by service and minute, last 15 minutes. Never cached."""
    return _frame(
        """
        select minute, service, error_rate
        from metrics.service_health
        where minute >= now() - interval '15 minutes'
        order by minute, service
        """
    )
