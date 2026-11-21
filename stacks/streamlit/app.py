"""Lumen Supply explorer: an AI-built report, the way an assistant writes one.

This is what "build me a dashboard for this database" tends to produce: one
file, quick to write, easy to change. It reads the semantic layer views in
schema `metrics`, so its numbers match Superset, Metabase, and Holotable.
Switch to "Raw tables" in the sidebar to see what happens when an app
defines revenue on its own.
"""

from __future__ import annotations

import os
from decimal import Decimal

import altair as alt
import pandas as pd
import psycopg
import streamlit as st

st.set_page_config(page_title="Lumen Supply explorer", layout="wide")

URL = os.environ["WAREHOUSE_URL"]
LAST_Q = (
    "month >= date_trunc('quarter', now()) - interval '3 months' AND month < date_trunc('quarter', now())"
)


@st.cache_data(ttl=60)
def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with psycopg.connect(URL) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [c.name for c in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=cols)
    # Postgres numeric arrives as Decimal, which charts do not read as numbers.
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


def money(x: float) -> str:
    return f"${x / 1e6:,.2f}M" if abs(x) >= 1e6 else f"${x / 1e3:,.0f}K"


st.title("Lumen Supply explorer")
st.caption("An AI-built report over the lab warehouse. Revenue is completed orders net of discounts.")

with st.sidebar:
    st.header("Filters")
    regions = query("SELECT DISTINCT region FROM metrics.monthly_kpis ORDER BY 1")["region"].tolist()
    region = st.selectbox("Region", ["All regions", *regions], index=0)
    source = st.radio(
        "Revenue definition",
        ["Semantic layer", "Raw tables"],
        help="Raw tables sums every order line, including refunded and canceled orders, "
        "with no discounts applied. A plausible first guess, and wrong.",
    )

where_region = "" if region == "All regions" else "AND region = %s"
params: tuple = () if region == "All regions" else (region,)

# --- KPIs -----------------------------------------------------------------
kpi = query(
    "SELECT sum(revenue) AS revenue, sum(revenue_target) AS target, sum(orders) AS orders "
    f"FROM metrics.monthly_kpis WHERE {LAST_Q} {where_region}",
    params,
).iloc[0]
if source == "Raw tables":
    raw = query(
        "SELECT sum(i.quantity * i.unit_price) AS revenue, count(DISTINCT o.order_id) AS orders "
        "FROM shop.orders o JOIN shop.order_items i USING (order_id) "
        "WHERE o.ordered_at >= date_trunc('quarter', now()) - interval '3 months' "
        "AND o.ordered_at < date_trunc('quarter', now()) " + where_region.replace("region", "o.region"),
        params,
    ).iloc[0]
    revenue, orders = float(raw["revenue"]), int(raw["orders"])
else:
    revenue, orders = float(kpi["revenue"]), int(kpi["orders"])
target = float(kpi["target"])

st.subheader(f"Last full quarter, {region}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", money(revenue))
c2.metric("Target", money(target))
c3.metric("Attainment", f"{revenue / target:.1%}", delta=f"{revenue / target - 1:+.1%} vs. plan")
c4.metric("Orders", f"{orders:,}")
if source == "Raw tables":
    st.warning(
        f"Raw tables say {money(revenue)}. The semantic layer says {money(float(kpi['revenue']))}. "
        "Same question, two answers. This is why the semantic layer matters."
    )

# --- Charts ---------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.markdown("**Revenue vs. target by month**")
    monthly = query(
        "SELECT month, sum(revenue) AS revenue, sum(revenue_target) AS target FROM metrics.monthly_kpis "
        f"WHERE month < date_trunc('month', now()) {where_region} GROUP BY month ORDER BY month",
        params,
    ).melt("month", var_name="series", value_name="usd")
    st.altair_chart(
        alt.Chart(monthly)
        .mark_line(point=True)
        .encode(
            x=alt.X("month:T", title=None),
            y=alt.Y("usd:Q", title="USD", axis=alt.Axis(format="$~s")),
            color=alt.Color("series:N", title=None),
            tooltip=["month:T", "series:N", alt.Tooltip("usd:Q", format="$,.0f")],
        ),
        width="stretch",
    )

with right:
    st.markdown("**Revenue by channel, by quarter**")
    by_channel = query(
        "SELECT date_trunc('quarter', order_date)::date AS quarter, channel, sum(revenue) AS revenue "
        "FROM metrics.daily_revenue WHERE order_date >= date_trunc('quarter', now()) - interval '12 months' "
        f"AND order_date < date_trunc('quarter', now()) {where_region} GROUP BY 1, 2 ORDER BY 1",
        params,
    )
    st.altair_chart(
        alt.Chart(by_channel)
        .mark_bar()
        .encode(
            x=alt.X("yearquarter(quarter):O", title=None),
            y=alt.Y("revenue:Q", title="USD", axis=alt.Axis(format="$~s")),
            color=alt.Color("channel:N", title="Channel"),
            tooltip=["channel:N", alt.Tooltip("revenue:Q", format="$,.0f")],
        ),
        width="stretch",
    )

st.markdown("**Attainment by region, last full quarter**")
regions_df = query(
    "SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target, "
    f"sum(revenue) / sum(revenue_target) AS attainment FROM metrics.monthly_kpis WHERE {LAST_Q} "
    "GROUP BY region ORDER BY attainment"
)
st.dataframe(
    regions_df,
    hide_index=True,
    width="stretch",
    column_config={
        "region": "Region",
        "revenue": st.column_config.NumberColumn("Revenue", format="dollar"),
        "target": st.column_config.NumberColumn("Target", format="dollar"),
        "attainment": st.column_config.ProgressColumn(
            "Attainment", format="percent", min_value=0.8, max_value=1.1
        ),
    },
)

with st.expander("How this app was built"):
    st.markdown(
        "One Python file, about 150 lines, of the kind an AI assistant writes from a prompt like "
        '"Build a dashboard for the Lumen Supply database." It is fast to make and easy to change. '
        "You also now own an app: hosting, access control, and keeping its numbers correct are on you. "
        "See `stacks/streamlit/app.py`."
    )
