"""Lumen Supply, built with Plotly Dash.

Run: gunicorn app:server, or python app.py for development.
Every query lives in data.py and reads the `metrics` views.
"""

import data
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, ctx, dash_table, dcc, html, no_update
from dash.dash_table.Format import Format, Group, Scheme, Symbol

# Hex values from examples/_shared/design-tokens.css, for Plotly.
THEMES = {
    "light": {
        "surface": "#ffffff",
        "border": "#dde1e8",
        "text": "#1b1f27",
        "muted": "#5a6170",
        "series": ["#2563eb", "#f08c2e", "#0f9d8a", "#8b5cf6", "#64748b"],
        "danger": "#c2410c",
        "warning": "#b45309",
        "success": "#15803d",
    },
    "dark": {
        "surface": "#161b22",
        "border": "#2b3340",
        "text": "#e6e9ef",
        "muted": "#9aa3b2",
        "series": ["#60a5fa", "#fbae5c", "#34d3b8", "#b197fc", "#94a3b8"],
        "danger": "#fb923c",
        "warning": "#fbbf24",
        "success": "#4ade80",
    },
}
# The channel colors are fixed by the brief: web, mobile, partner.
CHANNEL_COLORS = {"web": "#2563eb", "mobile": "#f08c2e", "partner": "#0f9d8a"}
CHANNELS = list(CHANNEL_COLORS)
SERVICES = ["web", "checkout", "payments", "search", "inventory"]


def band(attainment: float) -> tuple[str, str]:
    """The word and token name for an attainment value."""
    if attainment < 0.92:
        return "Missed", "danger"
    if attainment < 0.98:
        return "Close", "warning"
    return "On track", "success"


def money_short(v: float) -> str:
    if abs(v) >= 1e6:
        return f"${v / 1e6:.2f}M"
    if abs(v) >= 1e3:
        return f"${v / 1e3:.0f}K"
    return f"${v:,.0f}"


def pct(v: float, signed: bool = False) -> str:
    return f"{v * 100:+.1f}%" if signed else f"{v * 100:.1f}%"


def styled(
    fig: go.Figure, theme: str, title: str, x_title: str, y_title: str, height: int = 320
) -> go.Figure:
    t = THEMES[theme]
    fig.update_layout(
        title={"text": title, "font": {"size": 16}},
        height=height,
        margin={"l": 64, "r": 24, "t": 56, "b": 48},
        paper_bgcolor=t["surface"],
        plot_bgcolor=t["surface"],
        font={"family": "Inter, system-ui, sans-serif", "color": t["text"], "size": 13},
        legend={"orientation": "h", "y": -0.22, "x": 0},
        hoverlabel={"font": {"family": "Inter, system-ui, sans-serif"}},
    )
    fig.update_xaxes(title=x_title, gridcolor=t["border"], linecolor=t["border"], zeroline=False)
    fig.update_yaxes(title=y_title, gridcolor=t["border"], linecolor=t["border"], zeroline=False)
    return fig


def empty_fig(theme: str, message: str) -> go.Figure:
    fig = styled(go.Figure(), theme, "", "", "", height=240)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(text=message, showarrow=False, font={"size": 15, "color": THEMES[theme]["muted"]})
    return fig


def loading(child, what: str):
    return dcc.Loading(
        child, custom_spinner=html.Div(f"Loading {what}...", className="muted"), delay_show=150
    )


app = Dash(__name__, title="Lumen Supply")
server = app.server

# --- Layout -----------------------------------------------------------------


def kpi(label: str, value, delta) -> html.Div:
    return html.Div(
        [
            html.Div(label, className="label"),
            html.Div(value, className="value"),
            html.Div(delta, className="delta"),
        ],
        className="kpi",
    )


def serve_layout():
    head = data.header()
    k = data.kpis()
    regions = list(data.attainment_by_region().region)
    word, token = band(k["attainment"])
    as_of = pd.Timestamp(head["as_of"]).tz_convert("UTC").strftime("%b %d, %Y %H:%M UTC")
    period = head["period"]
    return html.Div(
        className="page",
        children=[
            dcc.Store(id="theme", storage_type="local"),
            dcc.Store(id="drill", data={"region": None, "channel": None}),
            dcc.Interval(id="tick", interval=5000),
            html.Div(
                className="header",
                children=[
                    html.Div(
                        [
                            html.H1("Lumen Supply"),
                            html.Div(
                                [
                                    f"Showing {period}, the last full quarter, against the quarter before. ",
                                    f"Data as of {as_of}.",
                                ],
                                className="muted",
                            ),
                        ]
                    ),
                    html.Button("Toggle light or dark", id="theme-toggle", className="btn ghost"),
                ],
            ),
            html.Div(
                className="kpis",
                children=[
                    kpi(
                        "Revenue",
                        money_short(k["revenue"]),
                        f"{pct(k['revenue_change'], True)} vs prior quarter",
                    ),
                    kpi(
                        "Target",
                        money_short(k["target"]),
                        f"Revenue is ${abs(k['gap']):,.0f} {'below' if k['gap'] < 0 else 'above'} target",
                    ),
                    kpi(
                        "Attainment",
                        html.Span(pct(k["attainment"]), className=f"band-{token}"),
                        [html.Span(word, className=f"badge band-{token}"), " of target"],
                    ),
                    kpi("Orders", f"{k['orders']:,}", f"{pct(k['orders_change'], True)} vs prior quarter"),
                ],
            ),
            html.Div(
                className="card",
                children=loading(dcc.Graph(id="monthly", config={"displaylogo": False}), "monthly revenue"),
            ),
            html.Div(
                className="card",
                children=loading(dcc.Graph(id="attainment", config={"displaylogo": False}), "attainment"),
            ),
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="filters",
                        children=[
                            html.Div(
                                [
                                    html.Label("Region", htmlFor="region"),
                                    dcc.Dropdown(id="region", options=regions, placeholder="All regions"),
                                ],
                                className="field",
                            ),
                            html.Div(
                                [
                                    html.Label("Channel", htmlFor="channel"),
                                    dcc.Dropdown(id="channel", options=CHANNELS, placeholder="All channels"),
                                ],
                                className="field",
                            ),
                            html.Button("Clear filters", id="clear", className="btn"),
                            html.Div(id="active-filters", className="muted"),
                        ],
                    ),
                    loading(dcc.Graph(id="channels", config={"displaylogo": False}), "revenue by channel"),
                ],
            ),
            html.Div(
                className="card",
                children=[
                    html.H2(id="products-title"),
                    dcc.Input(
                        id="search",
                        type="search",
                        placeholder="Search product or category",
                        debounce=0.3,
                        className="search",
                    ),
                    loading(html.Div(id="products"), "products"),
                ],
            ),
            html.Div(
                className="card",
                children=[
                    dcc.Graph(id="live", config={"displaylogo": False}),
                    html.Div(id="live-status", className="muted"),
                ],
            ),
            html.Div(
                className="card signature",
                children=[
                    html.Span("Signature: callback-driven drill-through", className="tag"),
                    html.H2("Where did the miss come from? Click to drill down"),
                    html.P(
                        "Click a region, then a channel. Each click fires a callback that queries one level deeper. "
                        "The last level opens daily revenue and the largest orders in a modal. "
                        "The breadcrumb buttons use a pattern-matching callback to step back.",
                        className="muted",
                    ),
                    html.Div(id="crumbs", className="crumbs"),
                    html.Div(
                        className="grid-2",
                        children=[
                            loading(dcc.Graph(id="drill-region", config={"displaylogo": False}), "regions"),
                            loading(html.Div(id="drill-channel-wrap"), "channels"),
                        ],
                    ),
                    html.Div(id="modal"),
                ],
            ),
        ],
    )


app.layout = serve_layout

# --- Theme ------------------------------------------------------------------

app.clientside_callback(
    """
    function(n, stored) {
        let theme = stored;
        if (!theme) {
            theme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        if (n) { theme = theme === 'dark' ? 'light' : 'dark'; }
        document.documentElement.setAttribute('data-theme', theme);
        return theme;
    }
    """,
    Output("theme", "data"),
    Input("theme-toggle", "n_clicks"),
    State("theme", "data"),
)

# --- Filters ----------------------------------------------------------------


@app.callback(
    Output("region", "value"),
    Output("channel", "value"),
    Input("attainment", "clickData"),
    Input("channels", "clickData"),
    Input("clear", "n_clicks"),
    State("region", "value"),
    State("channel", "value"),
    prevent_initial_call=True,
)
def filter_from_clicks(att_click, ch_click, _clear, region, channel):
    """Chart clicks and the clear button set the two pickers. Clicking the same bar again clears it."""
    if ctx.triggered_id == "clear":
        return None, None
    if ctx.triggered_id == "attainment" and att_click:
        picked = att_click["points"][0]["y"]
        return (None if picked == region else picked), no_update
    if ctx.triggered_id == "channels" and ch_click:
        picked = ch_click["points"][0]["customdata"]
        picked = picked[0] if isinstance(picked, list) else picked
        return no_update, (None if picked == channel else picked)
    return no_update, no_update


@app.callback(
    Output("active-filters", "children"),
    Output("clear", "disabled"),
    Input("region", "value"),
    Input("channel", "value"),
)
def show_filters(region, channel):
    active = [x for x in (region, channel) if x]
    return f"Active filters: {', '.join(active) if active else 'none'}", not active


# --- Charts -----------------------------------------------------------------


@app.callback(Output("monthly", "figure"), Input("theme", "data"))
def monthly_chart(theme):
    theme = theme or "light"
    t = THEMES[theme]
    m = data.monthly()
    fig = go.Figure(
        [
            go.Scatter(
                x=m.month,
                y=m.revenue,
                name="Revenue",
                mode="lines+markers",
                line={"color": t["series"][0], "width": 3},
                hovertemplate="%{x|%b %Y}<br>Revenue $%{y:,.0f}<extra></extra>",
            ),
            go.Scatter(
                x=m.month,
                y=m.target,
                name="Target",
                mode="lines",
                line={"color": t["series"][1], "width": 2, "dash": "dash"},
                hovertemplate="%{x|%b %Y}<br>Target $%{y:,.0f}<extra></extra>",
            ),
        ]
    )
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return styled(
        fig, theme, "Revenue against target by month, last 12 full months", "Month", "Revenue (USD)"
    )


@app.callback(Output("attainment", "figure"), Input("theme", "data"), Input("region", "value"))
def attainment_chart(theme, region):
    theme = theme or "light"
    t = THEMES[theme]
    a = data.attainment_by_region().iloc[::-1]  # Plotly draws the first row at the bottom.
    period = data.header()["period"]
    words = [band(v)[0] for v in a.attainment]
    fig = go.Figure(
        go.Bar(
            x=a.attainment,
            y=a.region,
            orientation="h",
            marker={
                "color": [t[band(v)[1]] for v in a.attainment],
                "opacity": [1 if region in (None, r) else 0.35 for r in a.region],
            },
            text=[f"{pct(v)} {w}" for v, w in zip(a.attainment, words, strict=True)],
            textposition="outside",
            customdata=list(zip(a.revenue, a.target, strict=True)),
            hovertemplate="%{y}<br>Attainment %{x:.1%}<br>Revenue $%{customdata[0]:,.0f}<br>Target $%{customdata[1]:,.0f}<extra></extra>",
        )
    )
    fig.add_vline(
        x=1,
        line_dash="dash",
        line_color=t["muted"],
        line_width=2,
        annotation_text="Target",
        annotation_position="top",
    )
    fig.update_xaxes(range=[0.8, 1.12], tickformat=".0%")
    return styled(
        fig,
        theme,
        f"Attainment by region, {period}. Click a bar to filter below",
        "Attainment (% of target)",
        "",
        280,
    )


@app.callback(
    Output("channels", "figure"), Input("theme", "data"), Input("region", "value"), Input("channel", "value")
)
def channel_chart(theme, region, channel):
    theme = theme or "light"
    df = data.channel_by_quarter(region)
    if df.empty:
        return empty_fig(theme, f"No revenue for {region} in the last four quarters.")
    quarters = list(dict.fromkeys(df.sort_values("quarter_start").quarter))
    fig = go.Figure()
    for c in CHANNELS:
        part = df[df.channel == c].set_index("quarter").reindex(quarters, fill_value=0)
        fig.add_bar(
            x=quarters,
            y=part.revenue,
            name=c,
            marker_color=CHANNEL_COLORS[c],
            marker_opacity=1 if channel in (None, c) else 0.35,
            customdata=[c] * len(quarters),
            hovertemplate=f"{c}<br>%{{x}}<br>$%{{y:,.0f}}<extra></extra>",
        )
    fig.update_layout(barmode="stack")
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    title = f"Revenue by channel by quarter, {region or 'all regions'}. Click a channel to filter products"
    return styled(fig, theme, title, "Quarter", "Revenue (USD)")


@app.callback(
    Output("products-title", "children"),
    Output("products", "children"),
    Input("region", "value"),
    Input("channel", "value"),
    Input("search", "value"),
)
def products_table(region, channel, term):
    period = data.header()["period"]
    who = ", ".join(x for x in (region, channel) if x) or "all regions and channels"
    df = data.top_products(region, channel)
    term = (term or "").strip().lower()
    if term:
        df = df[
            df["product"].str.lower().str.contains(term, regex=False)
            | df["category"].str.lower().str.contains(term, regex=False)
        ]
    title = f"Top products, {period}, {who}"
    if df.empty:
        return title, html.Div(
            f"No products match {who}{f' and “{term}”' if term else ''}.", className="empty"
        )
    table = dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[
            {"name": "Product", "id": "product"},
            {"name": "Category", "id": "category"},
            {"name": "Units", "id": "units", "type": "numeric", "format": Format(group=Group.yes)},
            {
                "name": "Revenue",
                "id": "revenue",
                "type": "numeric",
                "format": Format(
                    group=Group.yes, precision=0, scheme=Scheme.fixed, symbol=Symbol.yes, symbol_prefix="$"
                ),
            },
        ],
        sort_action="native",
        page_size=15,
        style_cell={"fontFamily": "Inter, system-ui, sans-serif", "padding": "6px 10px", "textAlign": "left"},
        style_cell_conditional=[{"if": {"column_id": c}, "textAlign": "right"} for c in ("units", "revenue")],
        style_header={"fontWeight": 600},
        style_as_list_view=True,
    )
    return title, table


# --- Live -------------------------------------------------------------------


@app.callback(
    Output("live", "figure"),
    Output("live-status", "children"),
    Input("tick", "n_intervals"),
    Input("theme", "data"),
)
def live_chart(_n, theme):
    theme = theme or "light"
    t = THEMES[theme]
    df = data.live_error_rate()
    title = "Live: error rate by service, last 15 minutes"
    if df.empty:
        return empty_fig(theme, "No requests in the last 15 minutes. Is the stream service running?"), ""
    fig = go.Figure()
    for i, s in enumerate(SERVICES):
        part = df[df.service == s]
        fig.add_scatter(
            x=part.minute,
            y=part.error_rate,
            name=s,
            mode="lines",
            line={"color": t["series"][i], "width": 2},
            hovertemplate=f"{s}<br>%{{x|%H:%M}}<br>%{{y:.1%}}<extra></extra>",
        )
    fig.add_hline(
        y=0.05,
        line_dash="dash",
        line_color=t["danger"],
        line_width=2,
        annotation_text="5% alert threshold",
        annotation_position="top left",
    )
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_layout(uirevision="live")
    latest = df[df.minute == df.minute.max()]
    over = latest[latest.error_rate >= 0.05]
    alert = f"Above 5%: {', '.join(over.service)}." if not over.empty else "All services under 5%."
    stamp = pd.Timestamp.now(tz="UTC").strftime("%H:%M:%S UTC")
    return styled(
        fig, theme, title, "Time (UTC)", "Error rate (%)", 300
    ), f"Refreshes every 5 seconds. Last refresh {stamp}. {alert}"


# --- Signature: drill-through -------------------------------------------------


@app.callback(
    Output("drill", "data"),
    Input("drill-region", "clickData"),
    Input({"type": "drill-channel", "level": ALL}, "clickData"),
    Input({"type": "crumb", "level": ALL}, "n_clicks"),
    Input({"type": "close", "level": ALL}, "n_clicks"),
    State("drill", "data"),
    prevent_initial_call=True,
)
def drill_state(region_click, channel_clicks, crumb_clicks, close_clicks, state):
    """One store holds the drill path. Every chart, crumb, and close button writes to it."""
    trig = ctx.triggered_id
    value = ctx.triggered[0]["value"] if ctx.triggered else None
    if not value:  # A component was just created, not clicked.
        return no_update
    if trig == "drill-region":
        return {"region": value["points"][0]["y"], "channel": None}
    if isinstance(trig, dict) and trig["type"] == "drill-channel":
        return {**state, "channel": value["points"][0]["customdata"]}
    if isinstance(trig, dict) and trig["type"] == "crumb":
        return {"region": state["region"] if trig["level"] >= 1 else None, "channel": None}
    if isinstance(trig, dict) and trig["type"] == "close":
        return {**state, "channel": None}
    return no_update


@app.callback(Output("crumbs", "children"), Input("drill", "data"))
def crumbs(state):
    items = [html.Button("All regions", id={"type": "crumb", "level": 0})]
    if state["region"]:
        items += [
            html.Span("›", className="muted"),
            html.Button(state["region"], id={"type": "crumb", "level": 1}),
        ]
    if state["channel"]:
        items += [html.Span("›", className="muted"), html.Span(state["channel"], className="muted")]
    return items


@app.callback(Output("drill-region", "figure"), Input("theme", "data"), Input("drill", "data"))
def drill_regions(theme, state):
    theme = theme or "light"
    t = THEMES[theme]
    a = data.attainment_by_region().sort_values("revenue")
    gap = a.revenue - a.target
    fig = go.Figure(
        go.Bar(
            x=gap,
            y=a.region,
            orientation="h",
            marker={
                "color": [t[band(v)[1]] for v in a.attainment],
                "opacity": [1 if state["region"] in (None, r) else 0.35 for r in a.region],
            },
            text=[f"{'+' if g >= 0 else '-'}${abs(g) / 1e3:,.0f}K" for g in gap],
            textposition="auto",
            hovertemplate="%{y}<br>Gap to target $%{x:,.0f}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_color=t["muted"], line_width=1)
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    return styled(
        fig,
        theme,
        "1. Revenue gap to target by region. Click a region",
        "Revenue minus target (USD)",
        "",
        300,
    )


@app.callback(Output("drill-channel-wrap", "children"), Input("theme", "data"), Input("drill", "data"))
def drill_channels(theme, state):
    theme = theme or "light"
    t = THEMES[theme]
    region = state["region"]
    if not region:
        return html.Div("Pick a region on the left to see its channels.", className="empty")
    df = data.region_channel_quarters(region)
    head = data.header()["period"]
    fig = go.Figure(
        [
            go.Bar(
                x=df.channel,
                y=df.prev_q,
                name="Quarter before",
                marker_color=t["series"][4],
                customdata=df.channel,
                hovertemplate="%{x}<br>Quarter before $%{y:,.0f}<extra></extra>",
            ),
            go.Bar(
                x=df.channel,
                y=df.last_q,
                name=head,
                marker_color=[CHANNEL_COLORS[c] for c in df.channel],
                customdata=df.channel,
                hovertemplate=f"%{{x}}<br>{head} $%{{y:,.0f}}<extra></extra>",
            ),
        ]
    )
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    styled(
        fig,
        theme,
        f"2. {region} revenue by channel, quarter over quarter. Click a channel",
        "Channel",
        "Revenue (USD)",
        300,
    )
    return dcc.Graph(id={"type": "drill-channel", "level": 2}, figure=fig, config={"displaylogo": False})


@app.callback(Output("modal", "children"), Input("theme", "data"), Input("drill", "data"))
def drill_modal(theme, state):
    theme = theme or "light"
    t = THEMES[theme]
    region, channel = state["region"], state["channel"]
    if not (region and channel):
        return None
    daily = data.drill_daily(region, channel)
    orders = data.drill_orders(region, channel)
    period = data.header()["period"]
    weekly = (
        daily.assign(order_date=pd.to_datetime(daily.order_date))
        .resample("W", on="order_date")
        .sum()
        .reset_index()
    )
    fig = go.Figure(
        go.Bar(
            x=weekly.order_date,
            y=weekly.revenue,
            marker_color=CHANNEL_COLORS[channel],
            hovertemplate="Week of %{x|%b %d}<br>$%{y:,.0f}<extra></extra>",
        )
    )
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    styled(
        fig,
        theme,
        f"Weekly revenue, {region} {channel}, last two full quarters",
        "Week",
        "Revenue (USD)",
        280,
    )
    fig.update_layout(paper_bgcolor=t["surface"], showlegend=False)
    orders = orders.assign(ordered_at=pd.to_datetime(orders.ordered_at).dt.strftime("%b %d, %Y %H:%M"))
    table = dash_table.DataTable(
        data=orders.to_dict("records"),
        columns=[
            {"name": "Order", "id": "order_id"},
            {"name": "Ordered at (UTC)", "id": "ordered_at"},
            {"name": "Segment", "id": "segment"},
            {"name": "Units", "id": "units", "type": "numeric", "format": Format(group=Group.yes)},
            {
                "name": "Revenue",
                "id": "revenue",
                "type": "numeric",
                "format": Format(
                    group=Group.yes, precision=0, scheme=Scheme.fixed, symbol=Symbol.yes, symbol_prefix="$"
                ),
            },
        ],
        sort_action="native",
        page_size=10,
        style_as_list_view=True,
        style_cell={"fontFamily": "Inter, system-ui, sans-serif", "padding": "6px 10px", "textAlign": "left"},
        style_header={"fontWeight": 600},
    )
    total = daily.revenue.sum()
    return html.Div(
        className="modal-backdrop",
        children=html.Div(
            className="modal",
            role="dialog",
            **{"aria-modal": "true", "aria-label": f"{region} {channel} detail"},
            children=[
                html.Div(
                    className="modal-head",
                    children=[
                        html.H2(f"3. {region} · {channel}"),
                        html.Button("Close", id={"type": "close", "level": 3}, className="btn"),
                    ],
                ),
                html.P(
                    f"${total:,.0f} over the last two full quarters. Largest orders in {period} below.",
                    className="muted",
                ),
                dcc.Graph(figure=fig, config={"displaylogo": False}),
                html.H2("Largest orders"),
                table,
            ],
        ),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
