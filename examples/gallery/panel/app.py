"""Lumen Supply, built with Panel (HoloViz).

Run: panel serve app.py --index app
Every query lives in data.py and reads the `metrics` views.
"""

import data
import holoviews as hv
import pandas as pd
import panel as pn
from bokeh.models import (
    ColumnDataSource,
    FactorRange,
    HoverTool,
    NumberFormatter,
    NumeralTickFormatter,
    Span,
)
from bokeh.plotting import figure

hv.extension("bokeh")
pn.extension("tabulator", sizing_mode="stretch_width")

# --- Theme ---------------------------------------------------------------

LIGHT = {
    "bg": "#f6f7f9",
    "surface": "#ffffff",
    "surface2": "#eef0f4",
    "border": "#dde1e8",
    "text": "#1b1f27",
    "muted": "#5a6170",
    "series": ["#2563eb", "#f08c2e", "#0f9d8a", "#8b5cf6", "#64748b"],
    "success": "#15803d",
    "warning": "#b45309",
    "danger": "#c2410c",
    "success_bg": "#dcfce7",
    "warning_bg": "#fef3c7",
    "danger_bg": "#ffedd5",
}
DARK = {
    "bg": "#0e1116",
    "surface": "#161b22",
    "surface2": "#1f2630",
    "border": "#2b3340",
    "text": "#e6e9ef",
    "muted": "#9aa3b2",
    "series": ["#60a5fa", "#fbae5c", "#34d3b8", "#b197fc", "#94a3b8"],
    "success": "#4ade80",
    "warning": "#fbbf24",
    "danger": "#fb923c",
    "success_bg": "#12301f",
    "warning_bg": "#3a2c0c",
    "danger_bg": "#3b1f0e",
}
theme_arg = pn.state.session_args.get("theme", [b"default"])[0]
IS_DARK = theme_arg == b"dark"
T = DARK if IS_DARK else LIGHT
# The channel colors are fixed by the brief: web, mobile, partner.
CHANNEL_COLORS = {"web": "#2563eb", "mobile": "#f08c2e", "partner": "#0f9d8a"}
CHANNELS = list(CHANNEL_COLORS)


BAND_KEYS = {"Missed": "danger", "Close": "warning", "On track": "success"}


def band(attainment: float) -> tuple[str, str, str]:
    """Label, color, and background for an attainment value."""
    if attainment < 0.92:
        word = "Missed"
    elif attainment < 0.98:
        word = "Close"
    else:
        word = "On track"
    key = BAND_KEYS[word]
    return word, T[key], T[f"{key}_bg"]


def money_short(v: float) -> str:
    if abs(v) >= 1e6:
        return f"${v / 1e6:.2f}M"
    if abs(v) >= 1e3:
        return f"${v / 1e3:.0f}K"
    return f"${v:,.0f}"


def pct(v: float, signed: bool = False) -> str:
    return f"{v * 100:+.1f}%" if signed else f"{v * 100:.1f}%"


CSS = f"""
:root {{ --lumen-text: {T["text"]}; --lumen-muted: {T["muted"]}; }}
.kpi {{ background: {T["surface"]}; border: 1px solid {T["border"]}; border-radius: 10px;
        padding: 12px 16px; font-family: Inter, system-ui, sans-serif; color: {T["text"]}; }}
.kpi .label {{ font-size: 14px; color: {T["muted"]}; }}
.kpi .value {{ font-size: 32px; font-weight: 600; line-height: 1.2; }}
.kpi .delta {{ font-size: 14px; color: {T["muted"]}; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px;
          font-weight: 600; }}
.note {{ color: {T["muted"]}; font-size: 14px; }}
"""


def style(fig, title: str, x_label: str, y_label: str):
    fig.title.text = title
    fig.title.text_font_size = "16px"
    fig.xaxis.axis_label = x_label
    fig.yaxis.axis_label = y_label
    fig.toolbar.logo = None
    fig.outline_line_color = None
    fig.min_border_left = 16
    return fig


def section(*items):
    return pn.Column(
        *items,
        styles={
            "background": T["surface"],
            "border": f"1px solid {T['border']}",
            "border-radius": "10px",
            "padding": "8px 12px",
        },
        margin=(8, 0),
    )


# --- Header and KPIs -----------------------------------------------------

head = data.header()
k = data.kpis()
PERIOD = head["period"]
as_of = pd.Timestamp(head["as_of"]).tz_convert("UTC").strftime("%b %d, %Y %H:%M UTC")

header = pn.pane.HTML(
    f'<div class="note">Showing <b>{PERIOD}</b>, the last full quarter, against the '
    f"quarter before. Data as of <b>{as_of}</b>.</div>",
    stylesheets=[CSS],
)


def kpi_card(label: str, value: str, delta: str) -> pn.pane.HTML:
    return pn.pane.HTML(
        f'<div class="kpi"><div class="label">{label}</div>'
        f'<div class="value">{value}</div><div class="delta">{delta}</div></div>',
        stylesheets=[CSS],
    )


word, _, bg = band(k["attainment"])
band_color = T[BAND_KEYS[word]]
kpi_row = pn.Row(
    kpi_card("Revenue", money_short(k["revenue"]), f"{pct(k['revenue_change'], True)} vs prior quarter"),
    kpi_card(
        "Target",
        money_short(k["target"]),
        f"Revenue is ${abs(k['gap']):,.0f} {'below' if k['gap'] < 0 else 'above'} target",
    ),
    kpi_card(
        "Attainment",
        f'<span style="color:{band_color}">{pct(k["attainment"])}</span>',
        f'<span class="badge" style="background:{bg};color:{band_color}">{word}</span> of target',
    ),
    kpi_card("Orders", f"{k['orders']:,}", f"{pct(k['orders_change'], True)} vs prior quarter"),
)

# --- Revenue against target by month ------------------------------------

m = data.monthly()
m_src = ColumnDataSource(m.assign(month=pd.to_datetime(m["month"])))
monthly_fig = figure(
    height=300, sizing_mode="stretch_width", x_axis_type="datetime", tools="hover,reset,save"
)
monthly_fig.line("month", "revenue", source=m_src, color=T["series"][0], line_width=3, legend_label="Revenue")
monthly_fig.line(
    "month",
    "target",
    source=m_src,
    color=T["series"][1],
    line_width=2,
    line_dash="dashed",
    legend_label="Target",
)
monthly_fig.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
monthly_fig.legend.location = "bottom_right"
monthly_fig.select_one(HoverTool).tooltips = [
    ("Month", "@month{%b %Y}"),
    ("Revenue", "@revenue{$0,0}"),
    ("Target", "@target{$0,0}"),
]
monthly_fig.select_one(HoverTool).formatters = {"@month": "datetime"}
monthly_fig.select_one(HoverTool).mode = "vline"
style(monthly_fig, "Revenue against target by month, last 12 full months", "Month", "Revenue (USD)")

# --- Attainment by region (click to filter) -----------------------------

att = data.attainment_by_region()
att["color"] = [band(a)[1] for a in att.attainment]
att["label"] = [f"{pct(a)} {band(a)[0]}" for a in att.attainment]
REGIONS = list(att.region)
att_src = ColumnDataSource(att)
att_fig = figure(
    height=260,
    sizing_mode="stretch_width",
    y_range=FactorRange(factors=REGIONS[::-1]),
    x_range=(0.8, 1.12),
    tools="tap,reset",
    toolbar_location=None,
)
att_fig.hbar(
    y="region",
    right="attainment",
    left=0.8,
    height=0.65,
    source=att_src,
    color="color",
    nonselection_fill_alpha=0.3,
    nonselection_line_alpha=0.3,
)
att_fig.text(
    x="attainment",
    y="region",
    text="label",
    source=att_src,
    x_offset=6,
    text_baseline="middle",
    text_font_size="13px",
    text_color=T["text"],
)
att_fig.add_layout(
    Span(location=1.0, dimension="height", line_dash="dashed", line_color=T["muted"], line_width=2)
)
att_fig.xaxis.formatter = NumeralTickFormatter(format="0%")
att_fig.add_tools(
    HoverTool(
        tooltips=[
            ("Region", "@region"),
            ("Revenue", "@revenue{$0,0}"),
            ("Target", "@target{$0,0}"),
            ("Attainment", "@attainment{0.0%}"),
        ]
    )
)
style(att_fig, f"Attainment by region, {PERIOD} (click a bar to filter)", "Attainment (% of target)", "")

# --- Filters --------------------------------------------------------------

region_pick = pn.widgets.Select(name="Region", options=["All regions", *REGIONS], width=200)
channel_pick = pn.widgets.Select(name="Channel", options=["All channels", *CHANNELS], width=200)
clear_btn = pn.widgets.Button(name="Clear filters", button_type="primary", width=140, align="end")
filter_text = pn.pane.HTML(stylesheets=[CSS], align="end")


def current() -> tuple[str | None, str | None]:
    r = region_pick.value if region_pick.value in REGIONS else None
    c = channel_pick.value if channel_pick.value in CHANNELS else None
    return r, c


# --- Revenue by channel by quarter (click to filter) ---------------------

ch_srcs = {c: ColumnDataSource({"quarter": [], "bottom": [], "top": [], "revenue": []}) for c in CHANNELS}
ch_fig = figure(
    height=320, sizing_mode="stretch_width", x_range=FactorRange(), tools="tap,reset", toolbar_location=None
)
for c in CHANNELS:
    ch_fig.vbar(
        x="quarter",
        bottom="bottom",
        top="top",
        width=0.6,
        source=ch_srcs[c],
        color=CHANNEL_COLORS[c],
        legend_label=c,
        nonselection_fill_alpha=0.3,
        nonselection_line_alpha=0.3,
    )
ch_fig.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
ch_fig.legend.orientation = "horizontal"
ch_fig.add_layout(ch_fig.legend[0], "above")
ch_fig.add_tools(HoverTool(tooltips=[("Quarter", "@quarter"), ("Revenue", "@revenue{$0,0}")]))
ch_fig.y_range.start = 0
style(
    ch_fig, "Revenue by channel by quarter (click a channel to filter products)", "Quarter", "Revenue (USD)"
)
ch_empty = pn.pane.HTML(stylesheets=[CSS], visible=False)

# --- Top products ---------------------------------------------------------

search = pn.widgets.TextInput(name="Search products", placeholder="Product or category", width=260)
products = pn.widgets.Tabulator(
    pd.DataFrame(columns=["product", "category", "units", "revenue"]),
    show_index=False,
    disabled=True,
    pagination="local",
    page_size=15,
    layout="fit_columns",
    titles={"product": "Product", "category": "Category", "units": "Units", "revenue": "Revenue"},
    formatters={"units": NumberFormatter(format="0,0"), "revenue": NumberFormatter(format="$0,0")},
    text_align={"units": "right", "revenue": "right"},
    theme="midnight" if IS_DARK else "simple",
)
products_title = pn.pane.Markdown()
products_empty = pn.pane.HTML(stylesheets=[CSS], visible=False)

_syncing = False


def refresh_below(*_):
    """Re-query everything under the attainment chart for the current filters."""
    region, channel = current()
    scope = " · ".join(x for x in (region, channel) if x) or "None"
    filter_text.object = f'<span class="note">Active filters: <b>{scope}</b></span>'
    clear_btn.disabled = region is None and channel is None

    # Channel chart
    ch_fig.title.text = (
        f"Revenue by channel by quarter, {region or 'all regions'} (click a channel to filter products)"
    )
    df = data.channel_by_quarter(region)
    if df.empty:
        ch_empty.object = f'<p class="note">No revenue for {region} in the last four quarters.</p>'
        ch_empty.visible = True
    else:
        ch_empty.visible = False
        wide = df.pivot_table(
            index=["quarter_start", "quarter"], columns="channel", values="revenue", fill_value=0
        )
        wide = wide.reindex(columns=CHANNELS, fill_value=0).reset_index().sort_values("quarter_start")
        ch_fig.x_range.factors = list(wide.quarter)
        bottom = pd.Series(0.0, index=wide.index)
        for c in CHANNELS:
            top = bottom + wide[c]
            ch_srcs[c].data = {
                "quarter": list(wide.quarter),
                "bottom": list(bottom),
                "top": list(top),
                "revenue": list(wide[c]),
            }
            ch_srcs[c].selected.indices = list(range(len(wide))) if c == channel else []
            bottom = top

    # Products
    prod = data.top_products(region, channel)
    term = (search.value_input or "").strip().lower()
    if term:
        prod = prod[
            prod["product"].str.lower().str.contains(term, regex=False)
            | prod["category"].str.lower().str.contains(term, regex=False)
        ]
    who = ", ".join(x for x in (region, channel) if x) or "all regions and channels"
    products_title.object = f"### Top products, {PERIOD}, {who}"
    products.value = prod.reset_index(drop=True)
    products_empty.visible = prod.empty
    products_empty.object = f'<p class="note">No products match {who}{f" and “{term}”" if term else ""}.</p>'


def with_loading(fn):
    def run(*events):
        global _syncing
        if _syncing:
            return
        _syncing = True
        try:
            for part in (ch_section, products_section):
                part.loading = True
            fn(*events)
        finally:
            for part in (ch_section, products_section):
                part.loading = False
            _syncing = False

    return run


def on_region_tap(attr, old, new):
    if _syncing:
        return
    region_pick.value = REGIONS[new[0]] if new else "All regions"


def on_channel_tap(channel):
    def cb(attr, old, new):
        if _syncing:
            return
        if new:
            channel_pick.value = channel
        elif channel_pick.value == channel and not any(s.selected.indices for s in ch_srcs.values()):
            channel_pick.value = "All channels"

    return cb


def on_pick(*_):
    region, _channel = current()
    att_src.selected.indices = [REGIONS.index(region)] if region else []
    refresh_below()


att_src.selected.on_change("indices", on_region_tap)
for c in CHANNELS:
    ch_srcs[c].selected.on_change("indices", on_channel_tap(c))
region_pick.param.watch(with_loading(on_pick), "value")
channel_pick.param.watch(with_loading(on_pick), "value")
search.param.watch(with_loading(refresh_below), "value_input")
clear_btn.on_click(
    lambda _: (setattr(region_pick, "value", "All regions"), setattr(channel_pick, "value", "All channels"))
)

ch_pane = pn.pane.Bokeh(ch_fig, sizing_mode="stretch_width")
ch_section = section(pn.Row(region_pick, channel_pick, clear_btn, filter_text), ch_pane, ch_empty)
products_section = section(products_title, search, products, products_empty)
refresh_below()

# --- Live error rate -------------------------------------------------------

SERVICES = ["web", "checkout", "payments", "search", "inventory"]
live_srcs = {s: ColumnDataSource({"minute": [], "error_rate": []}) for s in SERVICES}
live_fig = figure(
    height=280,
    sizing_mode="stretch_width",
    x_axis_type="datetime",
    tools="hover,reset",
    toolbar_location=None,
)
for i, s in enumerate(SERVICES):
    live_fig.line(
        "minute", "error_rate", source=live_srcs[s], color=T["series"][i], line_width=2, legend_label=s
    )
live_fig.add_layout(
    Span(location=0.05, dimension="width", line_dash="dashed", line_color=T["danger"], line_width=2)
)
live_fig.yaxis.formatter = NumeralTickFormatter(format="0.0%")
live_fig.y_range.start = 0
live_fig.legend.orientation = "horizontal"
live_fig.legend.location = "top_left"
live_fig.select_one(HoverTool).tooltips = [("Minute", "@minute{%H:%M}"), ("Error rate", "@error_rate{0.0%}")]
live_fig.select_one(HoverTool).formatters = {"@minute": "datetime"}
style(
    live_fig,
    "Live: error rate by service, last 15 minutes (5% line is the alert threshold)",
    "Time (UTC)",
    "Error rate (%)",
)
live_status = pn.pane.HTML(stylesheets=[CSS])


def refresh_live():
    df = data.live_error_rate()
    if df.empty:
        live_status.object = (
            '<span class="note">No requests in the last 15 minutes. Is the stream service running?</span>'
        )
        return
    for s in SERVICES:
        part = df[df.service == s]
        live_srcs[s].data = {"minute": list(pd.to_datetime(part.minute)), "error_rate": list(part.error_rate)}
    latest = df[df.minute == df.minute.max()]
    over = latest[latest.error_rate >= 0.05]
    alert = (
        f'<b style="color:{T["danger"]}">Above 5%: {", ".join(over.service)}</b>'
        if not over.empty
        else "All services under 5%."
    )
    stamp = pd.Timestamp.now(tz="UTC").strftime("%H:%M:%S UTC")
    live_status.object = f'<span class="note">Refreshes every 5 seconds. Last refresh {stamp}. {alert}</span>'


refresh_live()
pn.state.add_periodic_callback(refresh_live, period=5000)

# --- Signature: linked cross-filtering with HoloViews ---------------------

orders = data.orders_last_quarter()
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["margin_rate"] = orders["gross_margin"] / orders["revenue"]
ds = hv.Dataset(orders, kdims=[], vdims=list(orders.columns))
ls = hv.link_selections.instance(unselected_alpha=0.15, selected_color=T["series"][0])
opts = {
    "height": 280,
    "responsive": True,
    "tools": ["box_select", "lasso_select", "hover"],
    "active_tools": ["box_select"],
}
by_day = hv.Scatter(ds, "order_date", ["revenue"]).opts(
    title="Order value by day (drag to select dates)",
    xlabel="Order date",
    ylabel="Order revenue (USD)",
    size=3,
    **opts,
)
size_vs_value = hv.Scatter(ds, "units", ["revenue"]).opts(
    title="Units against order value",
    xlabel="Units per order",
    ylabel="Order revenue (USD)",
    size=4,
    jitter=0.4,
    **opts,
)
margin_hist = hv.operation.histogram(ds, dimension="margin_rate", num_bins=30).opts(
    title="Gross margin rate",
    xlabel="Gross margin (% of revenue)",
    ylabel="Orders",
    xformatter=NumeralTickFormatter(format="0%"),
    **opts,
)
linked = ls(by_day + size_vs_value + margin_hist).cols(3)


def selection_summary(selection_expr):
    sel = ls.filter(orders, selection_expr) if selection_expr is not None else orders
    if sel.empty:
        return pn.pane.HTML(
            '<p class="note">No orders in this selection. Drag a smaller box or reset.</p>', stylesheets=[CSS]
        )
    share = sel.revenue.sum() / orders.revenue.sum()
    lead = pn.pane.HTML(
        f'<p class="note">Selected <b>{len(sel):,}</b> of {len(orders):,} orders, '
        f"<b>${sel.revenue.sum():,.0f}</b> ({pct(share)} of {PERIOD} revenue). "
        "The table below follows the selection.</p>",
        stylesheets=[CSS],
    )
    table = sel.pivot_table(index="region", columns="channel", values="revenue", aggfunc="sum", fill_value=0)
    table = table.reindex(columns=CHANNELS, fill_value=0)
    table["total"] = table.sum(axis=1)
    table = table.sort_values("total", ascending=False).reset_index()
    table.columns.name = None
    return pn.Column(
        lead,
        pn.widgets.Tabulator(
            table,
            show_index=False,
            disabled=True,
            layout="fit_columns",
            theme="midnight" if IS_DARK else "simple",
            titles={
                "region": "Region",
                "web": "Web",
                "mobile": "Mobile",
                "partner": "Partner",
                "total": "Total",
            },
            formatters={c: NumberFormatter(format="$0,0") for c in [*CHANNELS, "total"]},
            text_align={c: "right" for c in [*CHANNELS, "total"]},
        ),
    )


signature = pn.Column(
    pn.pane.Markdown(
        f"## Signature: linked cross-filtering\n"
        f"Every {PERIOD} order, in three HoloViews plots joined by `link_selections`. "
        "Drag a box in any plot and the other two, plus the table, filter to the same orders. "
        "Double-click a plot to clear."
    ),
    linked,
    pn.bind(selection_summary, ls.param.selection_expr),
)

# --- Page -----------------------------------------------------------------


template = pn.template.FastListTemplate(
    title="Lumen Supply",
    site="Panel",
    accent=T["series"][0],
    header_background=T["series"][0] if not IS_DARK else T["surface"],
    theme_toggle=True,
    main_max_width="1400px",
)
template.main.extend(
    [
        header,
        kpi_row,
        section(pn.pane.Bokeh(monthly_fig, sizing_mode="stretch_width")),
        section(pn.pane.Bokeh(att_fig, sizing_mode="stretch_width")),
        ch_section,
        products_section,
        section(pn.pane.Bokeh(live_fig, sizing_mode="stretch_width"), live_status),
        section(signature),
    ]
)
template.servable()
