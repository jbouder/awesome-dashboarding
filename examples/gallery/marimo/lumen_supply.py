import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="medium",
    app_title="Lumen Supply · marimo",
    css_file="lumen.css",
)


@app.cell(hide_code=True)
def _():
    # Setup: imports, one query helper, formats, and the lab palette.
    import os
    from datetime import timezone
    from decimal import Decimal

    import altair as alt
    import marimo as mo
    import pandas as pd
    import psycopg

    def query(sql, params=()):
        """Run SQL on the lab warehouse as the read-only role."""
        with psycopg.connect(os.environ["WAREHOUSE_URL"]) as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            df = pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
        # Postgres numeric arrives as Decimal. Charts need floats.
        for col in df.columns:
            if df[col].map(lambda v: isinstance(v, Decimal)).any():
                df[col] = df[col].astype(float)
        return df

    def money(x):
        """$5.64M, $94K: the KPI format."""
        if abs(x) >= 1e6:
            return f"${x / 1e6:,.2f}M"
        return f"${x / 1e3:,.0f}K"

    def band(att):
        """Attainment band: CSS class and the word that goes with it."""
        if att < 0.92:
            return "danger", "Missed"
        if att < 0.98:
            return "warning", "Close"
        return "success", "On track"

    # The last full quarter, as SQL, from context.md.
    Q_START = "date_trunc('quarter', now()) - interval '3 months'"
    Q_END = "date_trunc('quarter', now())"

    CHANNELS = ["web", "mobile", "partner"]
    CHANNEL_COLORS = ["#2563eb", "#f08c2e", "#0f9d8a"]
    BAND_COLORS = {"danger": "#c2410c", "warning": "#b45309", "success": "#15803d"}
    SERVICE_COLORS = ["#2563eb", "#f08c2e", "#0f9d8a", "#8b5cf6", "#64748b"]
    return (
        BAND_COLORS,
        CHANNELS,
        CHANNEL_COLORS,
        Q_END,
        Q_START,
        SERVICE_COLORS,
        alt,
        band,
        mo,
        money,
        pd,
        query,
        timezone,
    )


@app.cell(hide_code=True)
def _(mo, query, timezone):
    # 1. Header: the period shown and how fresh the data is.
    _meta = query(
        "SELECT to_char(date_trunc('quarter', now()) - interval '3 months', '\"Q\"Q YYYY') AS period, "
        "to_char(date_trunc('quarter', now()) - interval '6 months', '\"Q\"Q YYYY') AS prior, "
        "(SELECT max(ordered_at) FROM metrics.order_facts) AS as_of"
    ).iloc[0]
    period, prior = _meta["period"], _meta["prior"]
    _as_of = _meta["as_of"].astimezone(timezone.utc).strftime("%b %-d, %Y, %H:%M UTC")
    mo.Html(
        f"""
        <div class="lm-header">
          <h1>Lumen Supply</h1>
          <div>
            <span class="lm-period">{period}</span>
            <span class="lm-meta">&nbsp;last full quarter · Data as of {_as_of}</span>
          </div>
        </div>
        """
    )
    return period, prior


@app.cell(hide_code=True)
def _(Q_END, band, mo, money, prior, query):
    # 2. KPI row: last full quarter against the quarter before.
    with mo.status.spinner(title="Loading KPIs..."):
        _k = query(
            f"SELECT month >= date_trunc('quarter', now()) - interval '3 months' AS current, "
            "sum(revenue) AS revenue, sum(revenue_target) AS target, sum(orders) AS orders "
            "FROM metrics.monthly_kpis "
            f"WHERE month >= date_trunc('quarter', now()) - interval '6 months' AND month < {Q_END} "
            "GROUP BY 1"
        ).set_index("current")
    _cur, _prev = _k.loc[True], _k.loc[False]
    _att = _cur.revenue / _cur.target
    _band, _word = band(_att)
    _rev_chg = _cur.revenue / _prev.revenue - 1
    _ord_chg = _cur.orders / _prev.orders - 1
    _gap = _cur.revenue - _cur.target

    def _card(label, value, sub, value_class=""):
        return (
            f'<div class="lm-card"><div class="lm-label">{label}</div>'
            f'<div class="lm-value {value_class}">{value}</div><div class="lm-sub">{sub}</div></div>'
        )

    mo.Html(
        '<div class="lm-kpis">'
        + _card("Revenue", money(_cur.revenue), f"{_rev_chg:+.1%} vs. {prior}")
        + _card("Target", money(_cur.target), f"{'-' if _gap < 0 else '+'}{money(abs(_gap))} gap to target")
        + _card(
            "Attainment",
            f"{_att:.1%}",
            f'<span class="lm-badge lm-band-{_band}">{_word}</span>',
            f"lm-band-{_band}",
        )
        + _card("Orders", f"{int(_cur.orders):,}", f"{_ord_chg:+.1%} vs. {prior}")
        + "</div>"
    )
    return


@app.cell(hide_code=True)
def _(alt, mo, query):
    # 3. Revenue against target by month, last 12 full months.
    _m = query(
        'SELECT month, sum(revenue) AS "Revenue", sum(revenue_target) AS "Target" '
        "FROM metrics.monthly_kpis "
        "WHERE month >= date_trunc('month', now()) - interval '12 months' "
        "AND month < date_trunc('month', now()) GROUP BY month ORDER BY month"
    ).melt("month", var_name="series", value_name="usd")
    _chart = (
        alt.Chart(_m, title="Revenue against target by month, last 12 full months")
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
        .properties(width="container", height=280)
    )
    mo.ui.altair_chart(_chart, chart_selection=False, legend_selection=False)
    return


@app.cell(hide_code=True)
def _(mo):
    # The clear button. Every cell that reads it reruns on a click, which
    # rebuilds the pickers and charts with nothing selected. No callback.
    clear = mo.ui.button(label="Clear filters", kind="neutral")
    return (clear,)


@app.cell(hide_code=True)
def _(CHANNELS, Q_END, Q_START, clear, mo, query):
    # Pickers, rebuilt (and so reset) whenever Clear is clicked.
    clear
    attain_df = query(
        "SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target, "
        "sum(revenue) / sum(revenue_target) AS attainment FROM metrics.monthly_kpis "
        f"WHERE month >= {Q_START} AND month < {Q_END} GROUP BY region ORDER BY attainment"
    )
    region_picker = mo.ui.dropdown(
        options=["All regions", *attain_df["region"].tolist()], value="All regions", label="Region"
    )
    channel_picker = mo.ui.dropdown(
        options=["All channels", *CHANNELS], value="All channels", label="Channel"
    )
    return attain_df, channel_picker, region_picker


@app.cell(hide_code=True)
def _(
    channel,
    channel_picker,
    channel_source,
    clear,
    mo,
    region,
    region_picker,
    region_source,
):
    # Active filters, with the pickers and the clear button.
    _chips = (
        f'<span class="lm-chip">Region: <b>{region or "all"}</b>{region_source}</span>'
        f'<span class="lm-chip">Channel: <b>{channel or "all"}</b>{channel_source}</span>'
    )
    mo.vstack(
        [
            mo.md("## Dig in"),
            mo.md(
                "Click a region bar or a channel bar to filter what sits below it, or use the pickers. "
                "A click on a chart wins over its picker."
            ),
            mo.hstack(
                [region_picker, channel_picker, mo.Html(f"<div>Active filters: {_chips}</div>"), clear],
                justify="start",
                align="center",
                wrap=True,
                gap=1.5,
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(BAND_COLORS, alt, attain_df, band, clear, mo, pd, period):
    # 4. Attainment by region. Clicking a bar selects that region.
    clear
    _df = attain_df.assign(band=[band(a)[0] for a in attain_df["attainment"]])
    _df["label"] = [f"{a:.1%} · {band(a)[1]}" for a in _df["attainment"]]
    _pick = alt.selection_point(fields=["region"], name="region_click", toggle=False)
    # An explicit order: a field sort is dropped when layers disagree about it.
    _y = alt.Y("region:N", title=None, sort=_df.sort_values("attainment")["region"].tolist())
    _bars = (
        alt.Chart(_df)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X(
                "attainment:Q",
                title="Attainment (revenue ÷ target)",
                axis=alt.Axis(format="%"),
                scale=alt.Scale(domain=[0, 1.15]),
            ),
            y=_y,
            color=alt.Color(
                "band:N",
                scale=alt.Scale(domain=list(BAND_COLORS), range=list(BAND_COLORS.values())),
                legend=None,
            ),
            opacity=alt.condition(_pick, alt.value(1.0), alt.value(0.35)),
            tooltip=[
                alt.Tooltip("region:N", title="Region"),
                alt.Tooltip("attainment:Q", title="Attainment", format=".1%"),
                alt.Tooltip("revenue:Q", title="Revenue", format="$,.0f"),
                alt.Tooltip("target:Q", title="Target", format="$,.0f"),
            ],
        )
        .add_params(_pick)
    )
    _labels = (
        alt.Chart(_df)
        .mark_text(align="left", dx=4)
        .encode(x="attainment:Q", y=_y, text="label:N", color=alt.value("#5a6170"))
    )
    _rule = (
        alt.Chart(pd.DataFrame({"x": [1.0]})).mark_rule(strokeDash=[4, 4], color="#5a6170").encode(x="x:Q")
    )
    attain_chart = mo.ui.altair_chart(
        alt.layer(_bars, _labels, _rule).properties(
            title=f"Attainment by region, {period}. Worst first. Click a bar to filter.",
            width="container",
            height=200,
        )
    )
    attain_chart
    return (attain_chart,)


@app.cell(hide_code=True)
def _(attain_chart, attain_df, region_picker):
    # The region filter: a chart click, else the picker.
    _clicked = attain_chart.apply_selection(attain_df)["region"].tolist()
    if len(_clicked) == 1:
        region, region_source = _clicked[0], " (from chart)"
    elif region_picker.value != "All regions":
        region, region_source = region_picker.value, " (from picker)"
    else:
        region, region_source = None, ""
    return region, region_source


@app.cell(hide_code=True)
def _(CHANNELS, CHANNEL_COLORS, Q_END, alt, clear, mo, query, region):
    # 5. Revenue by channel by quarter, for the selected region.
    clear
    with mo.status.spinner(title="Loading revenue by channel..."):
        channel_df = query(
            "SELECT to_char(date_trunc('quarter', order_date), '\"Q\"Q YYYY') AS quarter, "
            "date_trunc('quarter', order_date)::date AS quarter_start, channel, sum(revenue) AS revenue "
            "FROM metrics.daily_revenue "
            f"WHERE order_date >= {Q_END} - interval '12 months' AND order_date < {Q_END} "
            "AND (%(region)s::text IS NULL OR region = %(region)s) "
            "GROUP BY 1, 2, 3 ORDER BY 2",
            {"region": region},
        )
    # Stack web, mobile, partner from the bottom up.
    channel_df["channel_order"] = channel_df["channel"].map(CHANNELS.index)
    _pick = alt.selection_point(fields=["channel"], name="channel_click", toggle=False)
    channel_chart = mo.ui.altair_chart(
        alt.Chart(
            channel_df,
            title=f"Revenue by channel by quarter, {region or 'all regions'}. Click a bar to filter products.",
        )
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
            order=alt.Order("channel_order:Q"),
            opacity=alt.condition(_pick, alt.value(1.0), alt.value(0.35)),
            tooltip=[
                alt.Tooltip("quarter:N", title="Quarter"),
                alt.Tooltip("channel:N", title="Channel"),
                alt.Tooltip("revenue:Q", title="Revenue", format="$,.0f"),
            ],
        )
        .add_params(_pick)
        .properties(width="container", height=280)
    )
    channel_chart if len(channel_df) else mo.callout(mo.md(f"No channel revenue for {region}."), kind="warn")
    return (channel_chart,)


@app.cell(hide_code=True)
def _(channel_chart, channel_picker):
    # The channel filter: a chart click, else the picker.
    _clicked = channel_chart.value["channel"].unique().tolist() if len(channel_chart.value) else []
    if len(_clicked) == 1:
        channel, channel_source = _clicked[0], " (from chart)"
    elif channel_picker.value != "All channels":
        channel, channel_source = channel_picker.value, " (from picker)"
    else:
        channel, channel_source = None, ""
    return channel, channel_source


@app.cell(hide_code=True)
def _(Q_END, Q_START, channel, mo, period, query, region):
    # 6. Top products for the selected region and channel.
    with mo.status.spinner(title="Loading top products..."):
        _top = query(
            'SELECT product AS "Product", category AS "Category", sum(units) AS "Units", '
            'sum(revenue) AS "Revenue" FROM metrics.line_facts '
            f"WHERE ordered_at >= {Q_START} AND ordered_at < {Q_END} "
            "AND (%(region)s::text IS NULL OR region = %(region)s) "
            "AND (%(channel)s::text IS NULL OR channel = %(channel)s) "
            "GROUP BY 1, 2 ORDER BY 4 DESC",
            {"region": region, "channel": channel},
        )
    _scope = f"{region or 'all regions'}, {channel or 'all channels'}"
    mo.vstack(
        [
            mo.md(f"### Top products, {period}: {_scope}"),
            mo.ui.table(
                _top,
                page_size=15,
                selection=None,
                show_column_summaries=False,
                format_mapping={"Units": "{:,.0f}", "Revenue": "${:,.0f}"},
            )
            if len(_top)
            else mo.callout(mo.md(f"No completed orders for {_scope} in {period}."), kind="warn"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # 7. Live panel. The refresh element ticks every 5 seconds, and the
    # cell below reruns because it reads live_refresh.
    live_refresh = mo.ui.refresh(options=["5s", "10s", "30s"], default_interval="5s", label="Auto refresh")
    mo.hstack(
        [mo.md("## Live: error rate by service, last 15 minutes"), live_refresh],
        justify="space-between",
        align="center",
        wrap=True,
    )
    return (live_refresh,)


@app.cell(hide_code=True)
def _(SERVICE_COLORS, alt, live_refresh, mo, pd, query):
    live_refresh
    _h = query(
        "SELECT minute, service, error_rate, requests FROM metrics.service_health "
        "WHERE minute >= now() - interval '15 minutes' ORDER BY minute"
    )
    if _h.empty:
        _out = mo.callout(
            mo.md("No service metrics in the last 15 minutes. Is the `stream` service running?"), kind="warn"
        )
    else:
        _lines = (
            alt.Chart(_h)
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
        _rule = (
            alt.Chart(pd.DataFrame({"y": [0.05]}))
            .mark_rule(color="#c2410c", strokeDash=[4, 4])
            .encode(y="y:Q")
        )
        _latest = _h[_h["minute"] == _h["minute"].max()]
        _hot = _latest[_latest["error_rate"] > 0.05]["service"].tolist()
        _status = (
            mo.callout(mo.md(f"**Above 5% now:** {', '.join(_hot)}"), kind="danger")
            if _hot
            else mo.md("All services are under the 5% line in the latest minute.")
        )
        _out = mo.vstack([alt.layer(_lines, _rule).properties(width="container", height=260), _status])
    _out
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    <div class="lm-signature">

    ## What marimo does best: reactivity without callbacks

    Drag across the chart to brush a date range. The SQL cell below reads
    the brushed days and reruns on its own. Nothing here registers a
    callback. Each cell names the values it uses, and marimo reruns it
    when one of them changes. The filters above work the same way.

    This whole dashboard is one file, `lumen_supply.py`. Each cell is a
    plain Python function, so a change shows up in `git diff` as a few
    lines of Python, not a blob of notebook JSON.

    </div>
    """)
    return


@app.cell(hide_code=True)
def _(Q_END, alt, mo, pd, query):
    # Daily revenue for the last 12 full months, with a brush on the x axis.
    daily_detail = query(
        "SELECT order_date, region, channel, sum(revenue) AS revenue, sum(orders) AS orders "
        "FROM metrics.daily_revenue "
        f"WHERE order_date >= {Q_END} - interval '12 months' AND order_date < {Q_END} "
        "GROUP BY 1, 2, 3"
    )
    daily_detail["order_date"] = pd.to_datetime(daily_detail["order_date"])
    _daily = daily_detail.groupby("order_date", as_index=False)["revenue"].sum()
    _brush = alt.selection_interval(encodings=["x"], name="days")
    daily_chart = mo.ui.altair_chart(
        alt.Chart(_daily, title="Daily revenue, last four full quarters. Drag to select days.")
        .mark_area(color="#2563eb", opacity=0.7, line={"color": "#2563eb"})
        .encode(
            x=alt.X("order_date:T", title="Day"),
            y=alt.Y("revenue:Q", title="Revenue (USD)", axis=alt.Axis(format="$~s")),
            tooltip=[
                alt.Tooltip("order_date:T", title="Day"),
                alt.Tooltip("revenue:Q", title="Revenue", format="$,.0f"),
            ],
        )
        .add_params(_brush)
        .properties(width="container", height=200)
    )
    daily_chart
    return daily_chart, daily_detail


@app.cell(hide_code=True)
def _(daily_chart, daily_detail):
    # The brushed days, or every day when nothing is brushed.
    _days = daily_chart.value["order_date"] if len(daily_chart.value) else daily_detail["order_date"]
    brushed_days = daily_detail[daily_detail["order_date"].isin(_days)]
    return (brushed_days,)


@app.cell
def _(brushed_days, mo):
    # SQL over a Python dataframe, in a plain Python cell. DuckDB runs it.
    mix = mo.sql(
        """
        SELECT
            region,
            channel,
            sum(revenue) AS revenue,
            sum(orders) AS orders,
            100 * sum(revenue) / sum(sum(revenue)) OVER () AS share
        FROM brushed_days
        GROUP BY region, channel
        ORDER BY revenue DESC
        """,
        output=False,
    )
    return (mix,)


@app.cell(hide_code=True)
def _(brushed_days, mix, mo):
    _lo, _hi = brushed_days["order_date"].min(), brushed_days["order_date"].max()
    mo.vstack(
        [
            mo.md(
                f"**Revenue mix by region and channel**, {_lo:%b %-d, %Y} to {_hi:%b %-d, %Y} "
                f"({brushed_days['order_date'].nunique()} days)"
            ),
            mo.ui.table(
                mix,
                page_size=12,
                selection=None,
                show_column_summaries=False,
                format_mapping={"revenue": "${:,.0f}", "orders": "{:,.0f}", "share": "{:.1f}%"},
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
