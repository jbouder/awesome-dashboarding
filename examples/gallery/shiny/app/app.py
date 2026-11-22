"""Lumen Supply dashboard in Shiny for Python.

Builds examples/_shared/spec.md on the metrics views, plus a what-if panel
that shows Shiny's fine-grained reactivity.
"""

import json
import os
from decimal import Decimal
from pathlib import Path

import pandas as pd
import plotly
import plotly.graph_objects as go
import psycopg
from shiny import App, reactive, render, ui

URL = os.environ.get("WAREHOUSE_URL", "postgresql://lab_ro:lab_ro@localhost:5433/lab")

# Design tokens (examples/_shared/design-tokens.css), as hex for Plotly.
LIGHT = {"text": "#1b1f27", "muted": "#5a6170", "grid": "#dde1e8", "s1": "#2563eb", "s2": "#f08c2e"}
DARK = {"text": "#e6e9ef", "muted": "#9aa3b2", "grid": "#2b3340", "s1": "#60a5fa", "s2": "#fbae5c"}
CHANNEL_COLORS = {"web": "#2563eb", "mobile": "#f08c2e", "partner": "#0f9d8a"}
SERVICE_COLORS = ["#2563eb", "#f08c2e", "#0f9d8a", "#8b5cf6", "#64748b"]
BANDS = {"danger": "#c2410c", "warning": "#b45309", "success": "#15803d"}

LAST_Q = "date_trunc('quarter', now()) - interval '3 months'"
THIS_Q = "date_trunc('quarter', now())"


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


def pct_change(new: float, old: float) -> str:
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


def quarter_label(ts) -> str:
    ts = pd.Timestamp(ts)
    return f"Q{ts.quarter} {ts.year}"


def chart_html(fig: go.Figure, div_id: str, dark: bool, click_input: str | None = None, key: str = "y"):
    """Render a Plotly figure as HTML. A click sends the clicked label to a Shiny input."""
    t = DARK if dark else LIGHT
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=13, color=t["text"]),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.08, x=0),
        hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(gridcolor=t["grid"], zerolinecolor=t["grid"], title_font_color=t["muted"])
    fig.update_yaxes(gridcolor=t["grid"], zerolinecolor=t["grid"], title_font_color=t["muted"])
    post = None
    if click_input:
        post = (
            "var gd = document.getElementById('{plot_id}');"
            "gd.on('plotly_click', function (e) {"
            f"  var p = e.points[0]; var v = '{key}' === 'name' ? p.data.name : p.{key};"
            f"  Shiny.setInputValue({json.dumps(click_input)}, v, {{priority: 'event'}});"
            "});"
        )
    html = fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=div_id,
        post_script=post,
        config={"displayModeBar": False, "responsive": True},
        default_height="320px",
    )
    return ui.HTML(html)


# --- Queries that do not depend on filters -----------------------------------


def load_kpis() -> pd.DataFrame:
    return query(f"""
        SELECT date_trunc('quarter', month) AS quarter, sum(revenue) AS revenue,
               sum(revenue_target) AS target, sum(orders) AS orders
        FROM metrics.monthly_kpis
        WHERE month >= {LAST_Q} - interval '3 months' AND month < {THIS_Q}
        GROUP BY 1 ORDER BY 1""")


def load_monthly() -> pd.DataFrame:
    return query("""
        SELECT month, sum(revenue) AS revenue, sum(revenue_target) AS target
        FROM metrics.monthly_kpis
        WHERE month >= date_trunc('month', now()) - interval '12 months'
          AND month < date_trunc('month', now())
        GROUP BY 1 ORDER BY 1""")


def load_regions() -> pd.DataFrame:
    return query(f"""
        SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target,
               sum(revenue) / sum(revenue_target) AS attainment
        FROM metrics.monthly_kpis
        WHERE month >= {LAST_Q} AND month < {THIS_Q}
        GROUP BY 1 ORDER BY attainment""")


def load_partner() -> pd.DataFrame:
    """Partner revenue per region, last full quarter and the one before."""
    return query(f"""
        SELECT region,
               sum(revenue) FILTER (WHERE order_date >= {LAST_Q}) AS partner_now,
               sum(revenue) FILTER (WHERE order_date < {LAST_Q}) AS partner_before
        FROM metrics.daily_revenue
        WHERE channel = 'partner'
          AND order_date >= {LAST_Q} - interval '3 months' AND order_date < {THIS_Q}
        GROUP BY 1""")


# --- UI ----------------------------------------------------------------------

CSS = """
:root { --lab-bg:#f6f7f9; --lab-surface:#ffffff; --lab-border:#dde1e8; --lab-text:#1b1f27;
        --lab-muted:#5a6170; --lab-accent:#2563eb; }
[data-bs-theme="dark"] { --lab-bg:#0e1116; --lab-surface:#161b22; --lab-border:#2b3340;
        --lab-text:#e6e9ef; --lab-muted:#9aa3b2; --lab-accent:#60a5fa; }
body { background: var(--lab-bg); color: var(--lab-text);
       font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }
.card { background: var(--lab-surface); border-color: var(--lab-border); border-radius: 10px; }
.lab-header { display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap;
              gap:12px; margin: 8px 0 16px; }
.lab-header h1 { font-size: 28px; font-weight: 700; margin: 0; }
.lab-muted { color: var(--lab-muted); font-size: 14px; }
.kpi-label { font-size: 14px; color: var(--lab-muted); }
.kpi-value { font-size: 32px; font-weight: 700; line-height: 1.2; }
.kpi-sub { font-size: 14px; color: var(--lab-muted); }
.pill { display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: 13px;
        font-weight: 600; color: #fff; }
.filters { display:flex; gap:8px; align-items:center; flex-wrap:wrap; font-size:14px; }
.chip { background: var(--lab-surface); border:1px solid var(--lab-border); border-radius: 999px;
        padding: 2px 10px; }
.empty { padding: 24px; text-align:center; color: var(--lab-muted); }
.whatif-count { font-size: 12px; color: var(--lab-muted); }
.signature { border: 2px dashed var(--lab-accent); }
"""


def card(title: str, *body, subtitle: str | None = None):
    head = [ui.tags.strong(title)]
    if subtitle:
        head.append(ui.div(subtitle, class_="lab-muted"))
    return ui.card(ui.card_header(*head), *body)


app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.title("Lumen Supply · Shiny"),
        ui.tags.script(src="vendor/plotly.min.js"),
        ui.tags.style(CSS),
    ),
    ui.busy_indicators.use(),
    ui.div(
        ui.div(
            ui.h1("Lumen Supply"),
            ui.output_ui("period"),
        ),
        ui.div(ui.input_dark_mode(id="mode"), class_="d-flex align-items-center gap-2"),
        class_="lab-header",
    ),
    ui.output_ui("kpis"),
    card(
        "Revenue against target by month",
        ui.output_ui("monthly_chart"),
        subtitle="Last 12 full months, all regions. Dashed line is target.",
    ),
    ui.card(
        ui.div(
            ui.div(
                ui.input_select("region", "Region", choices={"": "All regions"}, width="200px"),
                class_="me-2",
            ),
            ui.input_select(
                "channel",
                "Channel",
                choices={"": "All channels", "web": "web", "mobile": "mobile", "partner": "partner"},
                width="200px",
            ),
            ui.output_ui("filter_status", class_="ms-3"),
            class_="d-flex flex-wrap align-items-end gap-2",
        ),
    ),
    ui.layout_columns(
        card(
            "Attainment by region, last full quarter",
            ui.output_ui("region_chart"),
            subtitle="Revenue as a percent of target, worst first. Click a bar to filter.",
        ),
        card(
            "Revenue by channel by quarter",
            ui.output_ui("channel_chart"),
            subtitle="Last four full quarters. Click a channel to filter the products table.",
        ),
        col_widths={"sm": 12, "lg": (6, 6)},
    ),
    card(
        "Top products, last full quarter",
        ui.input_text("search", None, placeholder="Search product or category", width="320px"),
        ui.output_ui("products_note"),
        ui.output_data_frame("products"),
        subtitle="Top 15 by revenue for the selected region and channel. Click a header to sort.",
    ),
    card(
        "Live: error rate by service",
        ui.output_ui("live_chart"),
        subtitle="Last 15 minutes, refreshed every 5 seconds. Dashed line is the 5% alert level.",
    ),
    ui.card(
        ui.card_header(
            ui.tags.strong("Signature: what-if, with fine-grained reactivity"),
            ui.div(
                "Each output re-runs only when an input it depends on changes. "
                "The run counters show it: move one slider and watch which counters move.",
                class_="lab-muted",
            ),
        ),
        ui.layout_columns(
            ui.div(
                ui.input_slider("uplift", "Target uplift", min=-10, max=10, value=0, step=1, post="%"),
                ui.output_ui("whatif_target"),
            ),
            ui.div(
                ui.input_slider(
                    "recovery", "Partner revenue recovered", min=0, max=100, value=0, step=5, post="%"
                ),
                ui.output_ui("whatif_recovery"),
            ),
            col_widths={"sm": 12, "md": (6, 6)},
        ),
        ui.output_ui("whatif_table"),
        class_="signature",
    ),
    ui.div(
        "Every number comes from the metrics views in the lab warehouse.",
        class_="lab-muted my-3",
    ),
    title="Lumen Supply",
)


# --- Server ------------------------------------------------------------------


def server(input, output, session):
    runs = {"target": 0, "recovery": 0, "table": 0}

    @reactive.calc
    def dark() -> bool:
        return input.mode() == "dark"

    @reactive.calc
    def kpis_data():
        return load_kpis()

    @reactive.calc
    def regions():
        return load_regions()

    @reactive.effect
    def _fill_regions():
        names = regions()["region"].tolist()
        ui.update_select("region", choices={"": "All regions", **{n: n for n in names}})

    @reactive.effect
    @reactive.event(input.region_click)
    def _region_from_chart():
        ui.update_select("region", selected=input.region_click())

    @reactive.effect
    @reactive.event(input.channel_click)
    def _channel_from_chart():
        ui.update_select("channel", selected=input.channel_click())

    @reactive.effect
    @reactive.event(input.clear)
    def _clear():
        ui.update_select("region", selected="")
        ui.update_select("channel", selected="")
        ui.update_text("search", value="")

    @render.ui
    def period():
        k = kpis_data()
        as_of = query("SELECT max(ordered_at) AS t FROM metrics.order_facts")["t"].iloc[0]
        q = quarter_label(k["quarter"].iloc[-1]) if len(k) else "no data"
        return ui.div(
            ui.tags.strong(q),
            " · last full quarter · Data as of ",
            pd.Timestamp(as_of).strftime("%b %d, %Y %H:%M UTC") if as_of else "unknown",
            class_="lab-muted",
        )

    @render.ui
    def kpis():
        k = kpis_data()
        if len(k) < 2:
            return ui.div("No orders in the last two full quarters.", class_="empty")
        prev, cur = k.iloc[-2], k.iloc[-1]
        att = cur.revenue / cur.target
        key, word = band(att)
        gap = cur.revenue - cur.target

        def box(label, value, sub, extra=None):
            return ui.card(
                ui.div(label, class_="kpi-label"),
                ui.div(value, class_="kpi-value", style=f"color:{BANDS[key]}" if extra else None),
                ui.div(extra, sub) if extra else ui.div(sub, class_="kpi-sub"),
            )

        return ui.layout_columns(
            box("Revenue", money(cur.revenue), pct_change(cur.revenue, prev.revenue)),
            box(
                "Target", money(cur.target), f"Revenue is {money(abs(gap))} {'over' if gap >= 0 else 'under'}"
            ),
            box(
                "Attainment",
                f"{att * 100:.1f}%",
                ui.span(" of target", class_="kpi-sub"),
                extra=ui.span(word, class_="pill", style=f"background:{BANDS[key]}"),
            ),
            box("Orders", f"{int(cur.orders):,}", pct_change(cur.orders, prev.orders)),
            col_widths={"sm": 6, "lg": 3},
        )

    @render.ui
    def monthly_chart():
        d = load_monthly()
        if d.empty:
            return ui.div("No monthly data yet.", class_="empty")
        t = DARK if dark() else LIGHT
        fig = go.Figure()
        fig.add_scatter(
            x=d.month, y=d.revenue, name="Revenue", mode="lines+markers", line=dict(color=t["s1"], width=3)
        )
        fig.add_scatter(
            x=d.month, y=d.target, name="Target", mode="lines", line=dict(color=t["s2"], width=2, dash="dash")
        )
        fig.update_yaxes(title="Revenue (USD)", tickprefix="$", tickformat=".2s")
        fig.update_xaxes(title="Month", tickformat="%b %Y")
        fig.update_traces(hovertemplate="%{x|%b %Y}: $%{y:,.0f}<extra>%{fullData.name}</extra>")
        return chart_html(fig, "monthly", dark())

    @render.ui
    def region_chart():
        d = regions()
        if d.empty:
            return ui.div("No regional data for the last full quarter.", class_="empty")
        d = d.sort_values("attainment", ascending=False)  # Plotly draws bottom up, so worst lands on top.
        colors = [BANDS[band(a)[0]] for a in d.attainment]
        sel = input.region()
        fig = go.Figure(
            go.Bar(
                x=d.attainment * 100,
                y=d.region,
                orientation="h",
                marker=dict(color=colors, opacity=[1 if not sel or r == sel else 0.35 for r in d.region]),
                text=[f"{a * 100:.1f}% · {band(a)[1]}" for a in d.attainment],
                textposition="inside",
                insidetextanchor="end",
                hovertemplate="%{y}: %{x:.1f}% of target<extra></extra>",
            )
        )
        fig.add_vline(x=100, line=dict(color=(DARK if dark() else LIGHT)["text"], dash="dash", width=1.5))
        fig.update_xaxes(title="Attainment (% of target)", range=[80, 110], ticksuffix="%")
        fig.update_yaxes(title=None)
        return chart_html(fig, "regions", dark(), click_input="region_click", key="y")

    @reactive.calc
    def channel_data():
        params: tuple = ()
        where = ""
        if input.region():
            where, params = "AND region = %s", (input.region(),)
        return query(
            f"""
            SELECT date_trunc('quarter', order_date) AS quarter, channel, sum(revenue) AS revenue
            FROM metrics.daily_revenue
            WHERE order_date >= {THIS_Q} - interval '12 months' AND order_date < {THIS_Q} {where}
            GROUP BY 1, 2 ORDER BY 1, 2""",
            params,
        )

    @render.ui
    def channel_chart():
        d = channel_data()
        if d.empty:
            return ui.div("No channel revenue for this region.", class_="empty")
        d["label"] = d.quarter.map(quarter_label)
        sel = input.channel()
        fig = go.Figure()
        for ch, color in CHANNEL_COLORS.items():
            s = d[d.channel == ch]
            fig.add_bar(
                x=s.label,
                y=s.revenue,
                name=ch,
                marker=dict(color=color, opacity=1 if not sel or sel == ch else 0.35),
                hovertemplate=f"{ch}, %{{x}}: $%{{y:,.0f}}<extra></extra>",
            )
        fig.update_layout(barmode="stack")
        fig.update_yaxes(title="Revenue (USD)", tickprefix="$", tickformat=".2s")
        fig.update_xaxes(title="Quarter")
        return chart_html(fig, "channels", dark(), click_input="channel_click", key="name")

    @render.ui
    def filter_status():
        active = [("Region", input.region()), ("Channel", input.channel())]
        chips = [ui.span(f"{k}: {v}", class_="chip") for k, v in active if v]
        if not chips:
            return ui.div(
                ui.span("No filters. Showing all regions and channels.", class_="lab-muted"), class_="filters"
            )
        return ui.div(
            ui.span("Filtered by", class_="lab-muted"),
            *chips,
            ui.input_action_button("clear", "Clear filters", class_="btn-sm btn-outline-secondary"),
            class_="filters",
        )

    @reactive.calc
    def products_data():
        clauses, params = [], []
        if input.region():
            clauses.append("AND region = %s")
            params.append(input.region())
        if input.channel():
            clauses.append("AND channel = %s")
            params.append(input.channel())
        d = query(
            f"""
            SELECT product, category, sum(units) AS units, sum(revenue) AS revenue
            FROM metrics.line_facts
            WHERE order_date >= {LAST_Q} AND order_date < {THIS_Q} {" ".join(clauses)}
            GROUP BY 1, 2 ORDER BY revenue DESC""",
            tuple(params),
        )
        term = input.search().strip().lower()
        if term:
            d = d[
                d["product"].str.lower().str.contains(term, regex=False)
                | d["category"].str.lower().str.contains(term, regex=False)
            ]
        return d.head(15)

    @render.ui
    def products_note():
        if products_data().empty:
            return ui.div("No products match these filters. Clear a filter or the search.", class_="empty")
        return None

    @render.data_frame
    def products():
        d = products_data().copy()
        d["units"] = d["units"].map(lambda v: f"{int(v):,}")
        d["revenue"] = d["revenue"].map(lambda v: f"${v:,.0f}")
        d.columns = ["Product", "Category", "Units", "Revenue"]
        return render.DataGrid(d, width="100%", summary=False)

    @render.ui
    def live_chart():
        reactive.invalidate_later(5)
        d = query("""
            SELECT minute, service, error_rate
            FROM metrics.service_health
            WHERE minute >= now() - interval '15 minutes'
            ORDER BY minute, service""")
        if d.empty:
            return ui.div(
                "No requests in the last 15 minutes. Is the stream service running?", class_="empty"
            )
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
        fig.add_hline(
            y=5, line=dict(color=BANDS["danger"], dash="dash", width=1.5), annotation_text="5% alert"
        )
        top = max(6.0, float(d.error_rate.max() * 100) * 1.1)
        fig.update_yaxes(title="Error rate (%)", range=[0, top], ticksuffix="%")
        fig.update_xaxes(title="Time (UTC)", tickformat="%H:%M")
        return chart_html(fig, "live", dark())

    # --- Signature: what-if ------------------------------------------------
    # Three reactive calcs. Each output reads only the calcs it needs, so
    # moving "uplift" never re-runs the recovery output, and the reverse.

    @reactive.calc
    def base():
        r = regions().set_index("region")
        p = load_partner().set_index("region")
        return r.join(p).fillna(0.0)

    @reactive.calc
    def new_targets():
        return base()["target"] * (1 + input.uplift() / 100)

    @reactive.calc
    def recovered():
        b = base()
        lost = (b["partner_before"] - b["partner_now"]).clip(lower=0)
        return lost * input.recovery() / 100

    @render.ui
    def whatif_target():
        runs["target"] += 1
        t = new_targets().sum()
        return ui.div(
            ui.div(f"Quarter target becomes {money(t)}", class_="kpi-sub"),
            ui.div(f"This output has run {runs['target']} times", class_="whatif-count"),
        )

    @render.ui
    def whatif_recovery():
        runs["recovery"] += 1
        r = recovered()
        top = r.idxmax() if r.max() > 0 else None
        line = f"Adds {money(r.sum())} of revenue" + (f", most of it in {top}" if top else "")
        return ui.div(
            ui.div(line, class_="kpi-sub"),
            ui.div(f"This output has run {runs['recovery']} times", class_="whatif-count"),
        )

    @render.ui
    def whatif_table():
        runs["table"] += 1
        b = base()
        rev = b["revenue"] + recovered()
        att = rev / new_targets()
        rows = []
        for region in att.sort_values().index:
            a = att[region]
            key, word = band(a)
            rows.append(
                ui.tags.tr(
                    ui.tags.td(region),
                    ui.tags.td(f"{b.loc[region, 'attainment'] * 100:.1f}%"),
                    ui.tags.td(ui.tags.strong(f"{a * 100:.1f}%")),
                    ui.tags.td(ui.span(word, class_="pill", style=f"background:{BANDS[key]}")),
                )
            )
        total = rev.sum() / new_targets().sum()
        return ui.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(*[ui.tags.th(h) for h in ["Region", "Actual", "What-if", "Status"]])
                ),
                ui.tags.tbody(*rows),
                class_="table table-sm mt-3",
            ),
            ui.div(
                f"Company attainment under this scenario: {total * 100:.1f}%. "
                f"This table depends on both sliders and has run {runs['table']} times.",
                class_="whatif-count",
            ),
        )


app = App(
    app_ui,
    server,
    static_assets={"/vendor": Path(plotly.__file__).parent / "package_data"},
)
