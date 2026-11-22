"""Which region missed its revenue target last quarter, and why?

The Part 1 Demo 3 app: what Claude Code builds from the demo prompt in
prompts.md, after the follow-up that adds the region filter and the channel
chart. It reads the semantic layer, so its numbers match every other tool.
"""

import os
from decimal import Decimal

import altair as alt
import pandas as pd
import psycopg
import streamlit as st

st.set_page_config(page_title="Revenue vs. target", layout="wide")

LAST_Q = (
    "month >= date_trunc('quarter', now()) - interval '3 months' AND month < date_trunc('quarter', now())"
)


@st.cache_data(ttl=300)
def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with psycopg.connect(os.environ["WAREHOUSE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        df = pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


st.title("Which region missed its revenue target last quarter?")

regions = query(
    "SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target, "
    f"sum(revenue) / sum(revenue_target) AS attainment FROM metrics.monthly_kpis WHERE {LAST_Q} "
    "GROUP BY region ORDER BY attainment"
)
worst = regions.iloc[0]
total = regions[["revenue", "target"]].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Revenue, last full quarter", f"${total.revenue / 1e6:,.2f}M")
c2.metric("Attainment", f"{total.revenue / total.target:.1%}")
c3.metric("Furthest below target", worst.region, f"{worst.attainment - 1:+.1%} vs. target")

st.subheader("Attainment by region")
bars = (
    alt.Chart(regions)
    .mark_bar()
    .encode(
        x=alt.X("attainment:Q", title="Revenue ÷ target", axis=alt.Axis(format="%"),
                scale=alt.Scale(domain=[0.8, 1.1], clamp=True)),
        y=alt.Y("region:N", sort="x", title=None, axis=alt.Axis(labelLimit=200)),
        color=alt.condition(alt.datum.attainment < 0.98, alt.value("#c2410c"), alt.value("#2563eb")),
        tooltip=["region", alt.Tooltip("attainment:Q", format=".1%"), alt.Tooltip("revenue:Q", format="$,.0f")],
    )
)
target = alt.Chart(pd.DataFrame({"x": [1.0]})).mark_rule(strokeDash=[4, 4]).encode(x="x:Q")
st.altair_chart((bars + target).properties(height=220), width="stretch")

# Follow-up: a region filter and the channel chart that explains the miss.
region = st.selectbox("Region", regions.region.tolist(), index=0)
channels = query(
    "SELECT to_char(date_trunc('quarter', order_date), 'YYYY \"Q\"Q') AS quarter, channel, sum(revenue) AS revenue "
    "FROM metrics.daily_revenue WHERE region = %s "
    "AND order_date >= date_trunc('quarter', now()) - interval '12 months' "
    "AND order_date < date_trunc('quarter', now()) GROUP BY 1, 2 ORDER BY 1",
    (region,),
)
st.subheader(f"{region} revenue by channel, last four full quarters")
st.altair_chart(
    alt.Chart(channels)
    .mark_bar()
    .encode(
        x=alt.X("quarter:O", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("revenue:Q", title="Revenue (USD)", axis=alt.Axis(format="$~s")),
        color=alt.Color("channel:N", scale=alt.Scale(domain=["web", "mobile", "partner"],
                                                     range=["#2563eb", "#f08c2e", "#0f9d8a"])),
        tooltip=["quarter", "channel", alt.Tooltip("revenue:Q", format="$,.0f")],
    ),
    width="stretch",
)
st.caption("Revenue is completed orders net of discounts, from the warehouse's semantic layer (schema metrics).")
