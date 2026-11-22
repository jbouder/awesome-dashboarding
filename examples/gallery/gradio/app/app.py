"""Lumen Supply dashboard in Gradio.

Builds examples/_shared/spec.md on the metrics views as far as Gradio allows,
plus an "ask" panel: pick a region and quarter, get a plain-English summary.
"""

import os
from decimal import Decimal

import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import psycopg

URL = os.environ.get("WAREHOUSE_URL", "postgresql://lab_ro:lab_ro@localhost:5433/lab")

# Design tokens (examples/_shared/design-tokens.css), as hex for Plotly.
# Gradio does not tell the server which theme the browser uses, so chart
# text uses a mid gray that reads on light and dark backgrounds.
TEXT = "#7b8494"
GRID = "rgba(128,128,128,0.25)"
REVENUE, TARGET = "#2563eb", "#f08c2e"
CHANNEL_COLORS = {"web": "#2563eb", "mobile": "#f08c2e", "partner": "#0f9d8a"}
SERVICE_COLORS = ["#2563eb", "#f08c2e", "#0f9d8a", "#8b5cf6", "#64748b"]
BANDS = {"danger": "#c2410c", "warning": "#b45309", "success": "#15803d"}

LAST_Q = "date_trunc('quarter', now()) - interval '3 months'"
THIS_Q = "date_trunc('quarter', now())"
ALL = "All"


def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run one query against the metrics views. Numeric columns come back as floats."""
    with psycopg.connect(URL) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [c.name for c in cur.description]
        rows = [[float(v) if isinstance(v, Decimal) else v for v in r] for r in cur.fetchall()]
    return pd.DataFrame(rows, columns=cols)


def money(v: float) -> str:
    if abs(v) >= 1e6:
        return f"${v / 1e6:.2f}M"
    if abs(v) >= 1e3:
        return f"${v / 1e3:.0f}K"
    return f"${v:,.0f}"


def change(new: float, old: float) -> str:
    if not old:
        return "no prior quarter"
    d = (new - old) / old * 100
    return f"{'▲' if d >= 0 else '▼'} {abs(d):.1f}% vs prior quarter"


def band(att: float) -> tuple[str, str]:
    if att < 0.92:
        return "danger", "Missed"
    if att < 0.98:
        return "warning", "Close"
    return "success", "On track"


def qlabel(ts) -> str:
    ts = pd.Timestamp(ts)
    return f"Q{ts.quarter} {ts.year}"


def style(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=13, color=TEXT),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=1.12, x=0),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def empty_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=15, color=TEXT))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style(fig, 200)


def where(region: str, channel: str | None = None) -> tuple[str, tuple]:
    clauses, params = [], []
    if region and region != ALL:
        clauses.append("AND region = %s")
        params.append(region)
    if channel and channel != ALL:
        clauses.append("AND channel = %s")
        params.append(channel)
    return " ".join(clauses), tuple(params)


# --- Spec sections -----------------------------------------------------------


def header_html() -> str:
    k = kpi_frame()
    as_of = query("SELECT max(ordered_at) AS t FROM metrics.order_facts")["t"].iloc[0]
    q = qlabel(k["quarter"].iloc[-1]) if len(k) else "no data"
    when = pd.Timestamp(as_of).strftime("%b %d, %Y %H:%M UTC") if as_of is not None else "unknown"
    return (
        '<div class="lab-header"><h1>Lumen Supply</h1>'
        f'<div class="lab-muted"><strong>{q}</strong> · last full quarter · Data as of {when}</div></div>'
    )


def kpi_frame() -> pd.DataFrame:
    return query(f"""
        SELECT date_trunc('quarter', month) AS quarter, sum(revenue) AS revenue,
               sum(revenue_target) AS target, sum(orders) AS orders
        FROM metrics.monthly_kpis
        WHERE month >= {LAST_Q} - interval '3 months' AND month < {THIS_Q}
        GROUP BY 1 ORDER BY 1""")


def kpis_html() -> str:
    k = kpi_frame()
    if len(k) < 2:
        return '<div class="empty">No orders in the last two full quarters.</div>'
    prev, cur = k.iloc[-2], k.iloc[-1]
    att = cur.revenue / cur.target
    key, word = band(att)
    gap = cur.revenue - cur.target
    cards = [
        ("Revenue", money(cur.revenue), change(cur.revenue, prev.revenue), ""),
        ("Target", money(cur.target), f"Revenue is {money(abs(gap))} {'over' if gap >= 0 else 'under'}", ""),
        (
            "Attainment",
            f"{att * 100:.1f}%",
            f'<span class="pill" style="background:{BANDS[key]}">{word}</span> of target',
            f"color:{BANDS[key]}",
        ),
        ("Orders", f"{int(cur.orders):,}", change(cur.orders, prev.orders), ""),
    ]
    body = "".join(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="{css}">{value}</div><div class="kpi-sub">{sub}</div></div>'
        for label, value, sub, css in cards
    )
    return f'<div class="kpi-row">{body}</div>'


def monthly_fig() -> go.Figure:
    d = query("""
        SELECT month, sum(revenue) AS revenue, sum(revenue_target) AS target
        FROM metrics.monthly_kpis
        WHERE month >= date_trunc('month', now()) - interval '12 months'
          AND month < date_trunc('month', now())
        GROUP BY 1 ORDER BY 1""")
    if d.empty:
        return empty_fig("No monthly data yet.")
    fig = go.Figure()
    fig.add_scatter(
        x=d.month, y=d.revenue, name="Revenue", mode="lines+markers", line=dict(color=REVENUE, width=3)
    )
    fig.add_scatter(
        x=d.month, y=d.target, name="Target", mode="lines", line=dict(color=TARGET, width=2, dash="dash")
    )
    fig.update_yaxes(title="Revenue (USD)", tickprefix="$", tickformat=".2s")
    fig.update_xaxes(title="Month", tickformat="%b %Y")
    fig.update_traces(hovertemplate="%{x|%b %Y}: $%{y:,.0f}<extra>%{fullData.name}</extra>")
    return style(fig)


def region_frame() -> pd.DataFrame:
    return query(f"""
        SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target,
               sum(revenue) / sum(revenue_target) AS attainment
        FROM metrics.monthly_kpis
        WHERE month >= {LAST_Q} AND month < {THIS_Q}
        GROUP BY 1 ORDER BY attainment""")


def region_fig(selected: str) -> go.Figure:
    d = region_frame()
    if d.empty:
        return empty_fig("No regional data for the last full quarter.")
    d = d.sort_values("attainment", ascending=False)  # Plotly draws bottom up, so worst lands on top.
    fig = go.Figure(
        go.Bar(
            x=d.attainment * 100,
            y=d.region,
            orientation="h",
            marker=dict(
                color=[BANDS[band(a)[0]] for a in d.attainment],
                opacity=[1 if selected in (ALL, None, r) else 0.35 for r in d.region],
            ),
            text=[f"{a * 100:.1f}% · {band(a)[1]}" for a in d.attainment],
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(color="#ffffff"),
            hovertemplate="%{y}: %{x:.1f}% of target<extra></extra>",
        )
    )
    fig.add_vline(x=100, line=dict(color=TEXT, dash="dash", width=1.5))
    fig.update_xaxes(title="Attainment (% of target)", range=[80, 110], ticksuffix="%")
    return style(fig, 280)


def region_table() -> pd.DataFrame:
    d = region_frame()
    return pd.DataFrame(
        {
            "Region": d.region,
            "Attainment": [f"{a * 100:.1f}%" for a in d.attainment],
            "Status": [band(a)[1] for a in d.attainment],
        }
    )


def channel_fig(region: str, channel: str) -> go.Figure:
    clause, params = where(region)
    d = query(
        f"""
        SELECT date_trunc('quarter', order_date) AS quarter, channel, sum(revenue) AS revenue
        FROM metrics.daily_revenue
        WHERE order_date >= {THIS_Q} - interval '12 months' AND order_date < {THIS_Q} {clause}
        GROUP BY 1, 2 ORDER BY 1, 2""",
        params,
    )
    if d.empty:
        return empty_fig("No channel revenue for this region.")
    d["label"] = d.quarter.map(qlabel)
    fig = go.Figure()
    for ch, color in CHANNEL_COLORS.items():
        s = d[d.channel == ch]
        fig.add_bar(
            x=s.label,
            y=s.revenue,
            name=ch,
            marker=dict(color=color, opacity=1 if channel in (ALL, None, ch) else 0.35),
            hovertemplate=f"{ch}, %{{x}}: $%{{y:,.0f}}<extra></extra>",
        )
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title="Revenue (USD)", tickprefix="$", tickformat=".2s")
    fig.update_xaxes(title="Quarter")
    return style(fig)


def products(region: str, channel: str):
    clause, params = where(region, channel)
    d = query(
        f"""
        SELECT product AS "Product", category AS "Category", sum(units) AS "Units",
               sum(revenue) AS "Revenue"
        FROM metrics.line_facts
        WHERE order_date >= {LAST_Q} AND order_date < {THIS_Q} {clause}
        GROUP BY 1, 2 ORDER BY 4 DESC LIMIT 15""",
        params,
    )
    note = "" if len(d) else "**No products match these filters.** Clear a filter to see rows."
    d["Units"] = d["Units"].astype(int)
    return d.style.format({"Units": "{:,}", "Revenue": "${:,.0f}"}), note


def status(region: str, channel: str) -> str:
    active = []
    if region != ALL:
        active.append(f"Region: **{region}**")
    if channel != ALL:
        active.append(f"Channel: **{channel}**")
    return "Filtered by " + ", ".join(active) if active else "No filters. Showing all regions and channels."


def live_fig() -> go.Figure:
    d = query("""
        SELECT minute, service, error_rate
        FROM metrics.service_health
        WHERE minute >= now() - interval '15 minutes'
        ORDER BY minute, service""")
    if d.empty:
        return empty_fig("No requests in the last 15 minutes. Is the stream service running?")
    fig = go.Figure()
    for i, (svc, s) in enumerate(d.groupby("service")):
        fig.add_scatter(
            x=s.minute,
            y=s.error_rate * 100,
            name=svc,
            mode="lines",
            line=dict(color=SERVICE_COLORS[i % 5], width=2),
            hovertemplate=f"{svc} %{{x|%H:%M}}: %{{y:.2f}}%<extra></extra>",
        )
    fig.add_hline(y=5, line=dict(color=BANDS["danger"], dash="dash", width=1.5), annotation_text="5% alert")
    fig.update_yaxes(
        title="Error rate (%)", range=[0, max(6.0, float(d.error_rate.max() * 100) * 1.1)], ticksuffix="%"
    )
    fig.update_xaxes(title="Time (UTC)", tickformat="%H:%M")
    return style(fig, 280)


# --- Signature: the ask panel --------------------------------------------------


def quarter_choices() -> list[str]:
    d = query(f"""
        SELECT DISTINCT date_trunc('quarter', month) AS q FROM metrics.monthly_kpis
        WHERE month >= {THIS_Q} - interval '12 months' AND month < {THIS_Q} ORDER BY 1 DESC""")
    return [qlabel(q) for q in d.q]


def summarize(region: str, quarter: str) -> str:
    """Turn the numbers for one region and quarter into a short plain-English summary."""
    if not quarter:
        return "Pick a quarter."
    qn, year = int(quarter[1]), int(quarter.split()[1])
    start = pd.Timestamp(year=year, month=3 * qn - 2, day=1)
    prev = start - pd.DateOffset(months=3)
    end = start + pd.DateOffset(months=3)
    clause, params = where(region)
    scope = "All regions" if region == ALL else region
    k = query(
        f"""
        SELECT month >= %s AS current, sum(revenue) AS revenue, sum(revenue_target) AS target,
               sum(orders) AS orders
        FROM metrics.monthly_kpis
        WHERE month >= %s AND month < %s {clause}
        GROUP BY 1""",
        (start, prev, end, *params),
    ).set_index("current")
    if True not in k.index:
        return f"No data for {scope} in {quarter}."
    cur = k.loc[True]
    att = cur.revenue / cur.target
    key, word = band(att)
    lines = [
        f"### {scope} in {quarter}",
        f"Revenue was **{money(cur.revenue)}**, **{att * 100:.1f}%** of its {money(cur.target)} target. "
        f"Status: **{word}**.",
    ]
    if False in k.index:
        p = k.loc[False]
        lines.append(
            f"That is {change(cur.revenue, p.revenue).replace('vs prior quarter', 'from the quarter before')}, "
            f"on {int(cur.orders):,} orders ({change(cur.orders, p.orders).split(' vs')[0]})."
        )
    ch = query(
        f"""
        SELECT channel,
               sum(revenue) FILTER (WHERE order_date >= %s) AS now,
               sum(revenue) FILTER (WHERE order_date < %s) AS before
        FROM metrics.daily_revenue
        WHERE order_date >= %s AND order_date < %s {clause}
        GROUP BY 1""",
        (start, start, prev, end, *params),
    ).fillna(0.0)
    if not ch.empty:
        ch["delta"] = ch.now - ch.before
        worst, best = ch.loc[ch.delta.idxmin()], ch.loc[ch.delta.idxmax()]
        if worst.delta < 0:
            lines.append(
                f"The biggest drop was the **{worst.channel}** channel, down {money(-worst.delta)} "
                f"({money(worst.before)} to {money(worst.now)})."
            )
        if best.delta > 0:
            lines.append(f"The biggest gain was **{best.channel}**, up {money(best.delta)}.")
    if key != "success" and not ch.empty and worst.delta < 0:
        gap = cur.target - cur.revenue
        if gap > 0 and -worst.delta >= gap:
            lines.append(
                f"Recovering the {worst.channel} drop alone would close the {money(gap)} gap to target."
            )
        elif gap > 0:
            share = -worst.delta / gap * 100
            lines.append(
                f"Recovering the {worst.channel} drop alone would close about {share:.0f}% of the gap to target."
            )
    return "\n\n".join(lines)


# --- Layout ----------------------------------------------------------------------

CSS = """
:root { --lab-muted:#5a6170; --lab-border:#dde1e8; --lab-surface:#ffffff; }
.dark { --lab-muted:#9aa3b2; --lab-border:#2b3340; --lab-surface:#161b22; }
.gradio-container { font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif !important; }
.lab-header { display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:12px; }
.lab-header h1 { font-size:28px; font-weight:700; margin:0; }
.lab-muted { color: var(--lab-muted); font-size:14px; }
.kpi-row { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap:16px; }
.kpi { border:1px solid var(--lab-border); border-radius:10px; padding:16px; background: var(--lab-surface); }
.kpi-label { font-size:14px; color: var(--lab-muted); }
.kpi-value { font-size:32px; font-weight:700; line-height:1.2; }
.kpi-sub { font-size:14px; color: var(--lab-muted); }
.pill { display:inline-block; padding:2px 10px; border-radius:999px; font-size:13px; font-weight:600; color:#fff; }
.empty { padding:24px; text-align:center; color: var(--lab-muted); }
.signature { border:2px dashed #2563eb !important; border-radius:10px; }
"""

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
    radius_size=gr.themes.sizes.radius_md,
)

with gr.Blocks(title="Lumen Supply · Gradio", analytics_enabled=False) as demo:
    header = gr.HTML(
        '<div class="lab-header"><h1>Lumen Supply</h1><div class="lab-muted">Loading…</div></div>'
    )
    kpis = gr.HTML('<div class="empty">Loading the last full quarter…</div>')

    gr.Markdown(
        "### Revenue against target by month\nLast 12 full months, all regions. Dashed line is target."
    )
    monthly = gr.Plot(show_label=False)

    with gr.Row(equal_height=True):
        region = gr.Dropdown([ALL], value=ALL, label="Region", scale=1)
        channel = gr.Dropdown([ALL, "web", "mobile", "partner"], value=ALL, label="Channel", scale=1)
        with gr.Column(scale=2):
            filters = gr.Markdown("No filters. Showing all regions and channels.")
            clear = gr.Button("Clear filters", size="sm", variant="secondary")

    with gr.Row():
        with gr.Column():
            gr.Markdown(
                "### Attainment by region, last full quarter\n"
                "Revenue as a percent of target, worst first. Click a row in the table to filter."
            )
            regions = gr.Plot(show_label=False)
            region_rows = gr.Dataframe(interactive=False, show_label=False, max_height=200)
        with gr.Column():
            gr.Markdown(
                "### Revenue by channel by quarter\n"
                "Last four full quarters. Use the Channel picker to filter the products table."
            )
            channels = gr.Plot(show_label=False)

    gr.Markdown("### Top products, last full quarter\nTop 15 by revenue for the selected region and channel.")
    product_note = gr.Markdown()
    product_table = gr.Dataframe(interactive=False, show_label=False, show_search="search", max_height=560)

    gr.Markdown(
        "### Live: error rate by service\nLast 15 minutes, refreshed every 5 seconds. Dashed line is 5%."
    )
    live = gr.Plot(show_label=False)
    timer = gr.Timer(5)

    with gr.Group(elem_classes="signature"):
        gr.Markdown(
            "### Signature: ask about a region\n"
            "Gradio's model is inputs, a function, outputs. Pick a region and a quarter, "
            "press Summarize, and a plain Python function writes what changed. No LLM."
        )
        with gr.Row():
            ask_region = gr.Dropdown([ALL, "EMEA"], value="EMEA", label="Region")
            ask_quarter = gr.Dropdown([], label="Quarter")
        ask = gr.Button("Summarize", variant="primary")
        answer = gr.Markdown("Pick a region and quarter, then press Summarize.")

    gr.Markdown(
        '<div class="lab-muted">Every number comes from the metrics views in the lab warehouse.</div>'
    )

    # --- Events -------------------------------------------------------------------

    def load():
        names = region_frame()["region"].tolist()
        quarters = quarter_choices()
        prods, note = products(ALL, ALL)
        return (
            header_html(),
            kpis_html(),
            monthly_fig(),
            gr.Dropdown(choices=[ALL, *names], value=ALL),
            region_fig(ALL),
            region_table(),
            channel_fig(ALL, ALL),
            prods,
            note,
            live_fig(),
            gr.Dropdown(choices=[ALL, *names], value="EMEA"),
            gr.Dropdown(choices=quarters, value=quarters[0] if quarters else None),
        )

    demo.load(
        load,
        outputs=[
            header,
            kpis,
            monthly,
            region,
            regions,
            region_rows,
            channels,
            product_table,
            product_note,
            live,
            ask_region,
            ask_quarter,
        ],
    )

    def on_region(r, c):
        prods, note = products(r, c)
        return region_fig(r), channel_fig(r, c), prods, note, status(r, c)

    def on_channel(r, c):
        prods, note = products(r, c)
        return channel_fig(r, c), prods, note, status(r, c)

    region.change(on_region, [region, channel], [regions, channels, product_table, product_note, filters])
    channel.change(on_channel, [region, channel], [channels, product_table, product_note, filters])
    clear.click(lambda: (ALL, ALL), outputs=[region, channel])

    def pick_region(evt: gr.SelectData):
        return evt.row_value[0]

    region_rows.select(pick_region, outputs=region)
    timer.tick(live_fig, outputs=live, show_progress="hidden")
    ask.click(summarize, [ask_region, ask_quarter], answer)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=THEME,
        css=CSS,
        footer_links=["gradio"],
    )
