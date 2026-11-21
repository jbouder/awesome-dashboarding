import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Lumen Supply notebook")


@app.cell
def _():
    import os
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
        for col in df.columns:
            if df[col].map(lambda v: isinstance(v, Decimal)).any():
                df[col] = df[col].astype(float)
        return df

    return alt, mo, query


@app.cell
def _(mo):
    mo.md(
        """
        # Lumen Supply, in a notebook

        A reactive notebook: every cell reruns when a value it uses changes.
        Pick a region, then **select a channel in the bar chart** to see that
        channel's top products. The data comes from the semantic layer views in
        schema `metrics`, so the numbers match every other stack in the lab.
        """
    )
    return


@app.cell
def _(mo, query):
    regions = query("SELECT DISTINCT region FROM metrics.monthly_kpis ORDER BY 1")["region"].tolist()
    region = mo.ui.dropdown(options=regions, value="EMEA", label="Region")
    region
    return (region,)


@app.cell
def _(mo, query, region):
    _k = query(
        "SELECT sum(revenue) AS revenue, sum(revenue_target) AS target, sum(orders) AS orders "
        "FROM metrics.monthly_kpis WHERE region = %s AND month >= date_trunc('quarter', now()) - interval '3 months' "
        "AND month < date_trunc('quarter', now())",
        (region.value,),
    ).iloc[0]
    _att = _k["revenue"] / _k["target"]
    mo.hstack(
        [
            mo.stat(f"${_k['revenue'] / 1e6:,.2f}M", label="Revenue, last full quarter"),
            mo.stat(f"${_k['target'] / 1e6:,.2f}M", label="Target"),
            mo.stat(f"{_att:.1%}", label="Attainment", direction="increase" if _att >= 1 else "decrease"),
            mo.stat(f"{int(_k['orders']):,}", label="Orders"),
        ],
        justify="space-between",
    )
    return


@app.cell
def _(alt, mo, query, region):
    _df = query(
        "SELECT to_char(date_trunc('quarter', order_date), 'YYYY \"Q\"Q') AS quarter, channel, "
        "sum(revenue) AS revenue FROM metrics.daily_revenue WHERE region = %s "
        "AND order_date >= date_trunc('quarter', now()) - interval '12 months' "
        "AND order_date < date_trunc('quarter', now()) GROUP BY 1, 2 ORDER BY 1",
        (region.value,),
    )
    channels = mo.ui.altair_chart(
        alt.Chart(_df, title=f"{region.value} revenue by channel, last four full quarters")
        .mark_bar()
        .encode(
            x=alt.X("quarter:O", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("revenue:Q", title="USD", axis=alt.Axis(format="$~s")),
            color=alt.Color("channel:N", title="Channel"),
            tooltip=["quarter:N", "channel:N", alt.Tooltip("revenue:Q", format="$,.0f")],
        )
        .properties(width="container", height=320),
        chart_selection="point",
        legend_selection=True,
    )
    channels
    return (channels,)


@app.cell
def _(channels, mo, query, region):
    _picked = sorted(set(channels.value["channel"])) if len(channels.value) else []
    _where = "AND channel = ANY(%s)" if _picked else ""
    _params = (region.value, _picked) if _picked else (region.value,)
    _top = query(
        "SELECT product, category, sum(units) AS units, round(sum(revenue)) AS revenue FROM metrics.line_facts "
        "WHERE region = %s AND ordered_at >= date_trunc('quarter', now()) - interval '3 months' "
        f"AND ordered_at < date_trunc('quarter', now()) {_where} "
        "GROUP BY product, category ORDER BY revenue DESC LIMIT 10",
        _params,
    )
    mo.vstack(
        [
            mo.md(
                f"### Top products, last full quarter: {region.value}, "
                + (", ".join(_picked) if _picked else "all channels")
                + ("" if _picked else " (select a bar to narrow this)")
            ),
            mo.ui.table(_top, selection=None),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
