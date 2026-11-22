"""Lumen Supply dashboard, built with Streamlit.

The gallery's Streamlit build of examples/_shared/spec.md. One script, run top
to bottom on every interaction. Every number comes from the semantic layer
views in schema `metrics`, except the raw-tables comparison at the end, which
exists to show why that matters.
"""

from __future__ import annotations

import os
from datetime import UTC
from decimal import Decimal

import altair as alt
import pandas as pd
import psycopg
import streamlit as st

st.set_page_config(page_title="Lumen Supply · Streamlit", layout="wide")

# The last full quarter, as SQL, from context.md.
Q_START = "date_trunc('quarter', now()) - interval '3 months'"
Q_END = "date_trunc('quarter', now())"

CHANNELS = ["web", "mobile", "partner"]
CHANNEL_COLORS = ["#2563eb", "#f08c2e", "#0f9d8a"]
BANDS = {"danger": "#c2410c", "warning": "#b45309", "success": "#15803d"}
SERVICE_COLORS = ["#2563eb", "#f08c2e", "#0f9d8a", "#8b5cf6", "#64748b"]
MUTED = "#64748b"


def run_sql(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run SQL on the lab warehouse as the read-only role."""
    with psycopg.connect(os.environ["WAREHOUSE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        df = pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
    # Postgres numeric arrives as Decimal. Charts need floats.
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


@st.cache_data(ttl=300, show_spinner="Querying the warehouse...")
def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    return run_sql(sql, params)


def money(x: float) -> str:
    """$5.64M, $94K: the KPI format."""
    return f"${x / 1e6:,.2f}M" if abs(x) >= 1e6 else f"${x / 1e3:,.0f}K"


def band(att: float) -> tuple[str, str, str]:
    """Attainment band, its word, and the matching Streamlit color name."""
    if att < 0.92:
        return "danger", "Missed", "red"
    if att < 0.98:
        return "warning", "Close", "orange"
    return "success", "On track", "green"


# Filters live in session state. Clear bumps a counter that is part of every
# filter widget's key, so each one comes back new and empty.
st.session_state.setdefault("gen", 0)


def clear_filters() -> None:
    st.session_state.gen += 1


gen = st.session_state.gen

# --- 1. Header ---------------------------------------------------------------
meta = query(
    f"SELECT to_char({Q_START}, '\"Q\"Q YYYY') AS period, "
    f"to_char({Q_START} - interval '3 months', '\"Q\"Q YYYY') AS prior, "
    "(SELECT max(ordered_at) FROM metrics.order_facts) AS as_of"
).iloc[0]
period, prior = meta["period"], meta["prior"]
as_of = meta["as_of"].astimezone(UTC).strftime("%b %-d, %Y, %H:%M UTC")

st.title("Lumen Supply")
st.markdown(f"**{period}**, the last full quarter. Data as of {as_of}.")

# --- 2. KPI row --------------------------------------------------------------
k = query(
    f"SELECT month >= {Q_START} AS current, sum(revenue) AS revenue, "
    "sum(revenue_target) AS target, sum(orders) AS orders FROM metrics.monthly_kpis "
    f"WHERE month >= {Q_START} - interval '3 months' AND month < {Q_END} GROUP BY 1"
).set_index("current")
cur, prev = k.loc[True], k.loc[False]
att = cur.revenue / cur.target
_, word, color = band(att)
gap = cur.revenue - cur.target

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", money(cur.revenue), f"{cur.revenue / prev.revenue - 1:+.1%} vs. {prior}", border=True)
c2.metric(
    "Target",
    money(cur.target),
    f"{'-' if gap < 0 else '+'}{money(abs(gap))} gap to target",
    delta_color="normal",
    border=True,
)
c3.metric("Attainment", f"{att:.1%}", word, delta_color=color, delta_arrow="off", border=True)
c4.metric("Orders", f"{int(cur.orders):,}", f"{cur.orders / prev.orders - 1:+.1%} vs. {prior}", border=True)

# --- 3. Revenue against target by month ---------------------------------------
monthly = query(
    'SELECT month, sum(revenue) AS "Revenue", sum(revenue_target) AS "Target" FROM metrics.monthly_kpis '
    "WHERE month >= date_trunc('month', now()) - interval '12 months' AND month < date_trunc('month', now()) "
    "GROUP BY month ORDER BY month"
).melt("month", var_name="series", value_name="usd")
st.subheader("Revenue against target by month, last 12 full months")
st.altair_chart(
    alt.Chart(monthly)
    .mark_line(point=True, strokeWidth=2)
    .encode(
        x=alt.X("month:T", title="Month", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("usd:Q", title="Revenue (USD)", axis=alt.Axis(format="$~s")),
        color=alt.Color(
            "series:N",
            title=None,
            scale=alt.Scale(domain=["Revenue", "Target"], range=["#2563eb", "#f08c2e"]),
            legend=alt.Legend(orient="top"),
        ),
        strokeDash=alt.StrokeDash(
            "series:N", scale=alt.Scale(domain=["Revenue", "Target"], range=[[1, 0], [6, 4]]), legend=None
        ),
        tooltip=[
            alt.Tooltip("month:T", title="Month", format="%B %Y"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("usd:Q", title="USD", format="$,.0f"),
        ],
    )
    .properties(height=280),
    width="stretch",
)

# --- Filter bar ----------------------------------------------------------------
# Drawn here, filled in as the charts below report their selections.
st.subheader("Dig in")
st.caption(
    "Click a region bar or a channel bar to filter what sits below it, or use the pickers. "
    "A click on a chart wins over its picker."
)
bar = st.container(border=True)
pick_region_col, pick_channel_col, chips_col, clear_col = bar.columns(
    [2, 2, 4, 1.4], vertical_alignment="bottom"
)
clear_col.button("Clear filters", on_click=clear_filters, width="stretch")
chips = chips_col.empty()

# --- 4. Attainment by region ------------------------------------------------------
regions = query(
    "SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target, "
    "sum(revenue) / sum(revenue_target) AS attainment FROM metrics.monthly_kpis "
    f"WHERE month >= {Q_START} AND month < {Q_END} GROUP BY region ORDER BY attainment"
)
regions["band"] = [band(a)[0] for a in regions["attainment"]]
regions["label"] = [f"{a:.1%} · {band(a)[1]}" for a in regions["attainment"]]

region_pick = pick_region_col.selectbox(
    "Region", ["All regions", *regions["region"]], key=f"region_pick_{gen}"
)

st.subheader(f"Attainment by region, {period}")
click_region = alt.selection_point(fields=["region"], name="region_click", toggle=False)
# An explicit order: a field sort is dropped when layers disagree about it.
worst_first = regions.sort_values("attainment")["region"].tolist()
y_region = alt.Y("region:N", title=None, sort=worst_first)
attain_bars = (
    alt.Chart(regions)
    .mark_bar(cornerRadiusEnd=3)
    .encode(
        x=alt.X(
            "attainment:Q",
            title="Attainment (revenue ÷ target)",
            axis=alt.Axis(format="%"),
            scale=alt.Scale(domain=[0, 1.15]),
        ),
        y=y_region,
        color=alt.Color(
            "band:N", scale=alt.Scale(domain=list(BANDS), range=list(BANDS.values())), legend=None
        ),
        opacity=alt.condition(click_region, alt.value(1.0), alt.value(0.35)),
        tooltip=[
            alt.Tooltip("region:N", title="Region"),
            alt.Tooltip("attainment:Q", title="Attainment", format=".1%"),
            alt.Tooltip("revenue:Q", title="Revenue", format="$,.0f"),
            alt.Tooltip("target:Q", title="Target", format="$,.0f"),
        ],
    )
    .add_params(click_region)
)
attain_labels = (
    alt.Chart(regions).mark_text(align="left", dx=4).encode(x="attainment:Q", y=y_region, text="label:N")
)
target_rule = alt.Chart(pd.DataFrame({"x": [1.0]})).mark_rule(strokeDash=[4, 4], color=MUTED).encode(x="x:Q")
attain_event = st.altair_chart(
    alt.layer(attain_bars, attain_labels, target_rule).properties(height=200),
    width="stretch",
    on_select="rerun",
    selection_mode="region_click",
    key=f"attain_{gen}",
)
st.caption("Worst first. The dashed line is 100% of target. Click a bar to filter everything below.")

clicked = [p["region"] for p in attain_event.selection.get("region_click", [])]
if clicked:
    region, region_source = clicked[0], "chart"
elif region_pick != "All regions":
    region, region_source = region_pick, "picker"
else:
    region, region_source = None, ""

# --- 5. Revenue by channel by quarter -----------------------------------------------
channel_pick = pick_channel_col.selectbox("Channel", ["All channels", *CHANNELS], key=f"channel_pick_{gen}")

by_channel = query(
    "SELECT to_char(date_trunc('quarter', order_date), '\"Q\"Q YYYY') AS quarter, "
    "date_trunc('quarter', order_date)::date AS quarter_start, channel, sum(revenue) AS revenue "
    f"FROM metrics.daily_revenue WHERE order_date >= {Q_END} - interval '12 months' AND order_date < {Q_END} "
    "AND (%(region)s::text IS NULL OR region = %(region)s) GROUP BY 1, 2, 3 ORDER BY 2",
    {"region": region},
)
by_channel["stack"] = by_channel["channel"].map(CHANNELS.index)

st.subheader(f"Revenue by channel by quarter, {region or 'all regions'}")
channel_event = None
if by_channel.empty:
    st.info(f"No channel revenue for {region} in the last four full quarters.")
else:
    click_channel = alt.selection_point(fields=["channel"], name="channel_click", toggle=False)
    channel_event = st.altair_chart(
        alt.Chart(by_channel)
        .mark_bar()
        .encode(
            x=alt.X(
                "quarter:O", title="Quarter", sort=alt.SortField("quarter_start"), axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y("revenue:Q", title="Revenue (USD)", axis=alt.Axis(format="$~s")),
            color=alt.Color(
                "channel:N",
                title="Channel",
                scale=alt.Scale(domain=CHANNELS, range=CHANNEL_COLORS),
                legend=alt.Legend(orient="top"),
            ),
            order=alt.Order("stack:Q"),
            opacity=alt.condition(click_channel, alt.value(1.0), alt.value(0.35)),
            tooltip=[
                alt.Tooltip("quarter:N", title="Quarter"),
                alt.Tooltip("channel:N", title="Channel"),
                alt.Tooltip("revenue:Q", title="Revenue", format="$,.0f"),
            ],
        )
        .add_params(click_channel)
        .properties(height=280),
        width="stretch",
        on_select="rerun",
        selection_mode="channel_click",
        # A new region gives a new chart, with no channel selected.
        key=f"channel_{gen}_{region}",
    )
    st.caption("Click a bar to filter the products table to that channel.")

clicked = [p["channel"] for p in channel_event.selection.get("channel_click", [])] if channel_event else []
if clicked:
    channel, channel_source = clicked[0], "chart"
elif channel_pick != "All channels":
    channel, channel_source = channel_pick, "picker"
else:
    channel, channel_source = None, ""

with chips.container():
    st.markdown("**Active filters**")
    st.badge(
        f"Region: {region or 'all'}" + (f" (from {region_source})" if region_source else ""),
        color="blue" if region else "gray",
    )
    st.badge(
        f"Channel: {channel or 'all'}" + (f" (from {channel_source})" if channel_source else ""),
        color="blue" if channel else "gray",
    )

# --- 6. Top products ---------------------------------------------------------------
scope = f"{region or 'all regions'}, {channel or 'all channels'}"
st.subheader(f"Top products, {period}: {scope}")
products = query(
    "SELECT product, category, sum(units) AS units, sum(revenue) AS revenue FROM metrics.line_facts "
    f"WHERE ordered_at >= {Q_START} AND ordered_at < {Q_END} "
    "AND (%(region)s::text IS NULL OR region = %(region)s) "
    "AND (%(channel)s::text IS NULL OR channel = %(channel)s) "
    "GROUP BY 1, 2 ORDER BY revenue DESC",
    {"region": region, "channel": channel},
)
search = st.text_input("Search products or categories", placeholder="Type to filter, for example: tent")
if search:
    hit = products["product"].str.contains(search, case=False) | products["category"].str.contains(
        search, case=False
    )
    products = products[hit]
if products.empty:
    st.info(f"No products match for {scope}" + (f' and "{search}"' if search else "") + ".")
else:
    st.dataframe(
        products.head(15),
        hide_index=True,
        width="stretch",
        column_config={
            "product": "Product",
            "category": "Category",
            "units": st.column_config.NumberColumn("Units", format="localized"),
            "revenue": st.column_config.NumberColumn("Revenue", format="dollar", step=1),
        },
    )
    st.caption(f"Top 15 of {len(products):,} products by revenue. Click a column header to sort.")


# --- 7. Live: error rate by service ---------------------------------------------------
# A fragment reruns on its own timer, without rerunning the rest of the page.
@st.fragment(run_every=5)
def live_panel() -> None:
    st.subheader("Live: error rate by service, last 15 minutes")
    health = run_sql(
        "SELECT minute, service, error_rate, requests FROM metrics.service_health "
        "WHERE minute >= now() - interval '15 minutes' ORDER BY minute"
    )
    if health.empty:
        st.info("No service metrics in the last 15 minutes. Is the stream service running?")
        return
    lines = (
        alt.Chart(health)
        .mark_line(point=True)
        .encode(
            x=alt.X("minute:T", title="Time", axis=alt.Axis(format="%H:%M")),
            y=alt.Y("error_rate:Q", title="Error rate (errors ÷ requests)", axis=alt.Axis(format="%")),
            color=alt.Color(
                "service:N",
                title="Service",
                scale=alt.Scale(range=SERVICE_COLORS),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("minute:T", title="Minute", format="%H:%M"),
                alt.Tooltip("service:N", title="Service"),
                alt.Tooltip("error_rate:Q", title="Error rate", format=".1%"),
                alt.Tooltip("requests:Q", title="Requests", format=","),
            ],
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"y": [0.05]}))
        .mark_rule(color=BANDS["danger"], strokeDash=[4, 4])
        .encode(y="y:Q")
    )
    st.altair_chart(alt.layer(lines, rule).properties(height=260), width="stretch")
    latest = health[health["minute"] == health["minute"].max()]
    hot = latest[latest["error_rate"] > 0.05]["service"].tolist()
    if hot:
        st.error(f"Above 5% in the latest minute: {', '.join(hot)}.", icon=":material/warning:")
    else:
        st.caption(
            "Every service is under the 5% line (dashed) in the latest minute. Refreshes every 5 seconds."
        )


live_panel()

# --- Signature: what Streamlit does best ----------------------------------------------
st.divider()
st.header("What Streamlit does best: speed of building")
st.markdown(
    "This section is about 30 lines of Python: a radio button, two queries, three metrics, and a "
    "callout. Streamlit reruns the script on every click, so there is no state to wire up. Flip the "
    "switch to see what happens when an app defines revenue on its own instead of using the semantic layer."
)

source = st.radio("Revenue definition", ["Semantic layer", "Raw tables"], horizontal=True)
SEMANTIC_SQL = (
    "SELECT sum(revenue) AS revenue, sum(orders) AS orders\n"
    "FROM metrics.monthly_kpis\n"
    f"WHERE month >= {Q_START}\n  AND month < {Q_END}"
)
RAW_SQL = (
    "SELECT sum(i.quantity * i.unit_price) AS revenue,\n"
    "       count(DISTINCT o.order_id) AS orders\n"
    "FROM shop.orders o JOIN shop.order_items i USING (order_id)\n"
    f"WHERE o.ordered_at >= {Q_START}\n  AND o.ordered_at < {Q_END}"
)
semantic = query(SEMANTIC_SQL).iloc[0]
picked = query(RAW_SQL).iloc[0] if source == "Raw tables" else semantic

s1, s2, s3 = st.columns(3)
s1.metric(f"Revenue, {period}", money(picked.revenue), border=True)
s2.metric("Attainment", f"{picked.revenue / cur.target:.1%}", border=True)
s3.metric("Orders", f"{int(picked.orders):,}", border=True)

if source == "Raw tables":
    st.warning(
        f"Raw tables say **{money(picked.revenue)}**. The semantic layer says **{money(semantic.revenue)}**. "
        f"The raw sum is {money(picked.revenue - semantic.revenue)} too high because it counts refunded and "
        "canceled orders and ignores discounts. Same question, two answers. Define each metric once, in the "
        "warehouse, and every app gets the right one.",
        icon=":material/warning:",
    )
else:
    st.success(
        "Completed orders only, net of discounts. The same number every tool in the lab shows.",
        icon=":material/check_circle:",
    )

with st.expander("The SQL behind each answer"):
    left, right = st.columns(2)
    left.markdown("**Semantic layer**")
    left.code(SEMANTIC_SQL, language="sql")
    right.markdown("**Raw tables**")
    right.code(RAW_SQL, language="sql")
