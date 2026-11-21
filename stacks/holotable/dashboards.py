"""Holotable dashboards over the lab warehouse, as plain specs.

Three dashboards that link to each other:

  Lumen Supply: executive overview   are we on track? (strategic)
    click a region  ->  Lumen Supply: region detail, for that region
  Lumen Supply: region detail        why? (analytical)
    click a channel ->  filters this dashboard to that channel
  Lumen Supply: service health       is something wrong now? (operational)
    click a service ->  filters this dashboard to that service

The overview links to the other two by id, so they are created first.
"""

from __future__ import annotations

METRICS = "lab-metrics"
OPS = "lab-ops"

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
CHANNELS = ["web", "mobile", "partner"]
SERVICES = ["web", "checkout", "payments", "search", "inventory"]

# The last full calendar quarter. Holotable forbids now() in SQL, since the
# server owns the time range, so the quarter is found from the newest data.
# The data runs up to today, so this is the last full quarter before today.
_THIS_Q = "(SELECT date_trunc('quarter', max(month)) FROM monthly_kpis)"
LAST_Q = f"month >= {_THIS_Q} - interval '3 months' AND month < {_THIS_Q}"
LAST_Q_DAYS = f"order_date >= {_THIS_Q} - interval '3 months' AND order_date < {_THIS_Q}"
LAST_Q_TS = f"ordered_at >= {_THIS_Q} - interval '3 months' AND ordered_at < {_THIS_Q}"
# Business charts label their x axis as text ("Dec 2025", "2026 Q3"). Dates
# are midnight UTC, which a time axis would show as the evening before in
# the viewer's time zone. Their windows are relative to the newest data.
_NEWEST_DAY = "(SELECT max(order_date) FROM daily_revenue)"


def per(column: str, values: list[str], expr: str) -> str:
    """One output column per value, named after it, for charts that draw one
    series per numeric column. A series' name is then the value itself, so a
    click on it can set a variable."""
    parts = []
    for v in values:
        cond = f"{column} = '{v}'"
        parts.append(f"{expr.format(cond=cond)} AS {v}")
    return ", ".join(parts)


ATTAINMENT_STEPS = [
    {"value": 0, "color": "danger"},
    {"value": 92, "color": "warning"},
    {"value": 98, "color": "success"},
]

TITLES = {
    "overview": "Lumen Supply: executive overview",
    "region": "Lumen Supply: region detail",
    "service": "Lumen Supply: service health",
}


def text(pid: str, content: list[str], layout: dict) -> dict:
    return {
        "id": pid,
        "title": "About this dashboard",
        "viz": "text",
        "options": {"content": "\n".join(content)},
        "layout": layout,
    }


def region_spec(overview_id: str | None = None) -> dict:
    """Why did a region land where it did? Filter by region and channel."""
    back = [{"title": "Back to the executive overview", "dashboard": overview_id}] if overview_id else []
    by = "region = :region AND channel = ANY(:channel)"
    return {
        "title": TITLES["region"],
        "timeRange": {"from": "now-365d", "to": "now"},
        "refreshIntervalMs": 60000,
        "variables": [
            {"name": "region", "label": "Region", "type": "enum", "values": REGIONS, "default": "EMEA"},
            {
                "name": "channel",
                "label": "Channel",
                "type": "enum",
                "values": CHANNELS,
                "multi": True,
                "default": CHANNELS,
            },
        ],
        "panels": [
            text(
                "about",
                [
                    "## One region up close",
                    "",
                    "Pick a **region** above, or arrive here by clicking one on the executive overview. "
                    "Revenue is completed orders net of discounts, in USD. "
                    "**Click a channel** in the channel chart or the flow to show only that channel; "
                    "put it back with the Channel picker.",
                ],
                {"x": 0, "y": 0, "w": 12, "h": 2},
            ),
            {
                "id": "attainment",
                "title": "Attainment, last full quarter",
                "viz": "stat",
                "description": "For the whole region, whatever the channel picker says: targets are set per region.",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT 100.0 * sum(revenue) / sum(revenue_target) AS attainment "
                    f"FROM monthly_kpis WHERE region = :region AND {LAST_Q}",
                },
                "format": "percent",
                "options": {"decimals": 1, "thresholds": ATTAINMENT_STEPS},
                "layout": {"x": 0, "y": 2, "w": 3, "h": 3},
            },
            {
                "id": "revenue",
                "title": "Revenue, last full quarter (USD)",
                "viz": "stat",
                "query": {
                    "sourceId": METRICS,
                    "sql": f"SELECT sum(revenue) AS revenue FROM daily_revenue WHERE {by} AND {LAST_Q_DAYS}",
                },
                "format": "number",
                "options": {"compact": True, "decimals": 2},
                "layout": {"x": 3, "y": 2, "w": 3, "h": 3},
            },
            {
                "id": "orders",
                "title": "Orders, last full quarter",
                "viz": "stat",
                "query": {
                    "sourceId": METRICS,
                    "sql": f"SELECT sum(orders) AS orders FROM daily_revenue WHERE {by} AND {LAST_Q_DAYS}",
                },
                "format": "number",
                "options": {"compact": True},
                "layout": {"x": 6, "y": 2, "w": 3, "h": 3},
            },
            {
                "id": "aov",
                "title": "Average order value (USD)",
                "viz": "stat",
                "query": {
                    "sourceId": METRICS,
                    "timeField": "week",
                    "sql": "SELECT date_trunc('week', order_date) AS week, sum(revenue) / sum(orders) AS aov "
                    f"FROM daily_revenue WHERE {by} GROUP BY week ORDER BY week",
                },
                "format": "number",
                "options": {"decimals": 0, "sparkline": True},
                "layout": {"x": 9, "y": 2, "w": 3, "h": 3},
            },
            {
                "id": "vs-target",
                "title": "Revenue vs. target, last 12 months (USD)",
                "viz": "line",
                "description": "All channels, since the target is set for the whole region.",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT to_char(month, 'Mon YYYY') AS month_label, revenue, revenue_target AS target "
                    "FROM monthly_kpis WHERE region = :region AND month > "
                    f"{_THIS_Q} - interval '12 months' AND month < (SELECT max(month) FROM monthly_kpis) ORDER BY month",
                },
                "format": "number",
                "options": {"compact": True, "legend": "top"},
                "layout": {"x": 0, "y": 5, "w": 6, "h": 4},
            },
            {
                "id": "by-channel",
                "title": "Revenue by channel, last four full quarters (USD)",
                "viz": "bar",
                "description": "Click a channel's bar to show only that channel.",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT to_char(date_trunc('quarter', order_date), 'YYYY \"Q\"Q') AS quarter, "
                    + per("channel", CHANNELS, "sum(revenue) FILTER (WHERE {cond})")
                    + f" FROM daily_revenue WHERE {by} AND order_date >= {_THIS_Q} - interval '12 months' "
                    "AND order_date < " + _THIS_Q + " GROUP BY 1 ORDER BY 1",
                },
                "format": "number",
                "options": {"compact": True, "stacked": True, "legend": "top"},
                "links": [{"title": "Show only this channel", "set": {"channel": {"series": True}}}],
                "layout": {"x": 6, "y": 5, "w": 6, "h": 4},
            },
            {
                "id": "flow",
                "title": "Where last quarter's revenue came from",
                "description": "Channel to customer segment to product category, each band as wide as its "
                "revenue. Click a channel to show only it.",
                "viz": "sankey",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT channel, segment, category, sum(revenue) AS revenue FROM line_facts "
                    f"WHERE region = :region AND channel = ANY(:channel) AND {LAST_Q_TS} GROUP BY channel, segment, category",
                },
                "format": "number",
                "options": {"path": ["channel", "segment", "category"], "value": "revenue", "compact": True},
                "links": [{"title": "Show only this channel", "set": {"channel": {"column": "channel"}}}],
                "layout": {"x": 0, "y": 9, "w": 7, "h": 5},
            },
            {
                "id": "segments",
                "title": "Revenue by segment, last full quarter",
                "viz": "donut",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT segment, sum(revenue) AS revenue FROM daily_revenue "
                    f"WHERE {by} AND {LAST_Q_DAYS} GROUP BY segment ORDER BY revenue DESC",
                },
                "format": "number",
                "options": {"legend": "bottom", "compact": True},
                "layout": {"x": 7, "y": 9, "w": 5, "h": 5},
            },
            {
                "id": "weekly",
                "title": "Weekly revenue by channel, last 26 weeks (USD)",
                "viz": "area",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT to_char(date_trunc('week', order_date), 'Mon DD') AS week, "
                    + per("channel", CHANNELS, "sum(revenue) FILTER (WHERE {cond})")
                    + f" FROM daily_revenue WHERE {by} AND order_date > {_NEWEST_DAY} - 182 "
                    "GROUP BY date_trunc('week', order_date) ORDER BY date_trunc('week', order_date)",
                },
                "format": "number",
                "options": {"compact": True, "stacked": True, "legend": "top"},
                "links": [{"title": "Show only this channel", "set": {"channel": {"series": True}}}],
                "layout": {"x": 0, "y": 14, "w": 7, "h": 4},
            },
            {
                "id": "top-products",
                "title": "Top products, last full quarter",
                "viz": "table",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT product, category, sum(units) AS units, sum(revenue) AS revenue FROM line_facts "
                    f"WHERE region = :region AND channel = ANY(:channel) AND {LAST_Q_TS} GROUP BY product, category ORDER BY revenue DESC",
                },
                "options": {
                    "limit": 15,
                    "columns": [
                        {"name": "product", "label": "Product"},
                        {"name": "category", "label": "Category"},
                        {"name": "units", "label": "Units", "align": "right", "compact": True},
                        {"name": "revenue", "label": "Revenue (USD)", "align": "right", "decimals": 0},
                    ],
                },
                **({"links": back} if back else {}),
                "layout": {"x": 7, "y": 14, "w": 5, "h": 4},
            },
        ],
    }


def service_spec() -> dict:
    """Is something wrong right now? Live, from ops.request_metrics."""
    per_min = (
        "SELECT time_bucket('1 minute', ts) AS minute, service, {select} FROM request_metrics "
        "WHERE service = ANY(:service) GROUP BY minute, service ORDER BY minute"
    )

    def wide(expr: str) -> str:
        return (
            "SELECT time_bucket('1 minute', ts) AS minute, "
            + per("service", SERVICES, expr)
            + " FROM request_metrics WHERE service = ANY(:service) GROUP BY minute ORDER BY minute"
        )

    error_pct = "100.0 * sum(errors) FILTER (WHERE {cond}) / nullif(sum(requests) FILTER (WHERE {cond}), 0)"
    pick = [{"title": "Show only this service", "set": {"service": {"series": True}}}]
    return {
        "title": TITLES["service"],
        "timeRange": {"from": "now-1h", "to": "now"},
        "refreshIntervalMs": 5000,
        "variables": [
            {
                "name": "service",
                "label": "Service",
                "type": "enum",
                "values": SERVICES,
                "multi": True,
                "default": SERVICES,
            },
        ],
        "panels": [
            text(
                "about",
                [
                    "## Lumen Supply service health",
                    "",
                    "Live request metrics for the five services behind the store, refreshed every 5 seconds. "
                    "Run `make incident` in the lab to break one, and watch it turn red here and in Grafana. "
                    "**Click a service** in any chart to show only it.",
                ],
                {"x": 0, "y": 0, "w": 12, "h": 2},
            ),
            {
                "id": "now",
                "title": "Error rate now, by service",
                "viz": "status-grid",
                "description": "Each service's error rate over the last minute.",
                "query": {
                    "sourceId": OPS,
                    "timeField": "minute",
                    "sql": per_min.format(
                        select="100.0 * sum(errors) / nullif(sum(requests), 0) AS error_pct"
                    ),
                },
                "format": "percent",
                "options": {
                    "decimals": 2,
                    "thresholds": [
                        {"value": 0, "color": "success"},
                        {"value": 2, "color": "warning"},
                        {"value": 5, "color": "danger"},
                    ],
                },
                "links": [{"title": "Show only this service", "set": {"service": {"column": "service"}}}],
                "layout": {"x": 0, "y": 2, "w": 12, "h": 2},
            },
            {
                "id": "errors",
                "title": "Error rate by service",
                "viz": "line",
                "query": {"sourceId": OPS, "timeField": "minute", "sql": wide(error_pct)},
                "format": "percent",
                "description": "Above 5% for a minute is an incident. Grafana's alert uses the same line.",
                "options": {"decimals": 1, "legend": "top"},
                "links": pick,
                "layout": {"x": 0, "y": 4, "w": 6, "h": 4},
            },
            {
                "id": "latency",
                "title": "p95 latency by service",
                "viz": "line",
                "query": {
                    "sourceId": OPS,
                    "timeField": "minute",
                    "sql": wide("max(p95_latency_ms) FILTER (WHERE {cond})"),
                },
                "format": "ms",
                "options": {"decimals": 0, "legend": "top"},
                "links": pick,
                "layout": {"x": 6, "y": 4, "w": 6, "h": 4},
            },
            {
                "id": "traffic",
                "title": "Requests per minute",
                "viz": "area",
                "query": {
                    "sourceId": OPS,
                    "timeField": "minute",
                    "sql": wide("sum(requests) FILTER (WHERE {cond})"),
                },
                "format": "number",
                "options": {"compact": True, "stacked": True, "legend": "top"},
                "links": pick,
                "layout": {"x": 0, "y": 8, "w": 7, "h": 4},
            },
            {
                "id": "incidents",
                "title": "Recent incidents",
                "viz": "table",
                "query": {
                    "sourceId": OPS,
                    "sql": "SELECT service, kind, started_at, ends_at FROM incidents ORDER BY started_at DESC",
                },
                "options": {
                    "limit": 20,
                    "columns": [
                        {"name": "service", "label": "Service"},
                        {"name": "kind", "label": "Kind"},
                        {"name": "started_at", "label": "Started"},
                        {"name": "ends_at", "label": "Ends"},
                    ],
                },
                "layout": {"x": 7, "y": 8, "w": 5, "h": 4},
            },
        ],
    }


def overview_spec(region_id: str, service_id: str) -> dict:
    """Are we on track? Every region leads to its detail."""
    to_region = [
        {
            "title": "Open region detail",
            "dashboard": region_id,
            "carry": {"timeRange": False},
            "set": {"region": {"column": "region"}},
        }
    ]
    return {
        "title": TITLES["overview"],
        "timeRange": {"from": "now-730d", "to": "now"},
        "refreshIntervalMs": 60000,
        "panels": [
            text(
                "about",
                [
                    "## Are we on track?",
                    "",
                    "Lumen Supply's revenue against plan. Revenue is completed orders net of discounts, in USD. "
                    "**Click a region** in the attainment bars, the map of revenue, or the table to open its "
                    "detail. The question to answer: which region missed its target last quarter, and why?",
                ],
                {"x": 0, "y": 0, "w": 12, "h": 2},
            ),
            {
                "id": "revenue",
                "title": "Revenue, last full quarter (USD)",
                "viz": "stat",
                "query": {
                    "sourceId": METRICS,
                    "sql": f"SELECT sum(revenue) AS revenue FROM monthly_kpis WHERE {LAST_Q}",
                },
                "format": "number",
                "options": {"compact": True, "decimals": 2},
                "layout": {"x": 0, "y": 2, "w": 3, "h": 3},
            },
            {
                "id": "attainment",
                "title": "Attainment, last full quarter",
                "viz": "stat",
                "query": {
                    "sourceId": METRICS,
                    "sql": f"SELECT 100.0 * sum(revenue) / sum(revenue_target) AS attainment FROM monthly_kpis WHERE {LAST_Q}",
                },
                "format": "percent",
                "options": {"decimals": 1, "thresholds": ATTAINMENT_STEPS},
                "layout": {"x": 3, "y": 2, "w": 3, "h": 3},
            },
            {
                "id": "orders",
                "title": "Orders, last full quarter",
                "viz": "stat",
                "query": {
                    "sourceId": METRICS,
                    "sql": f"SELECT sum(orders) AS orders FROM monthly_kpis WHERE {LAST_Q}",
                },
                "format": "number",
                "options": {"compact": True},
                "layout": {"x": 6, "y": 2, "w": 3, "h": 3},
            },
            {
                "id": "customers",
                "title": "Active customers by month",
                "viz": "stat",
                "query": {
                    "sourceId": METRICS,
                    "timeField": "month",
                    "sql": "SELECT month, sum(active_customers) AS customers FROM monthly_kpis "
                    "GROUP BY month ORDER BY month",
                },
                "format": "number",
                "options": {"compact": True, "sparkline": True},
                "layout": {"x": 9, "y": 2, "w": 3, "h": 3},
            },
            {
                "id": "by-region",
                "title": "Attainment by region, last full quarter",
                "description": "Click a region to open its detail.",
                "viz": "gauge",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT region, 100.0 * sum(revenue) / sum(revenue_target) AS attainment "
                    f"FROM monthly_kpis WHERE {LAST_Q} GROUP BY region ORDER BY attainment",
                },
                "format": "percent",
                "options": {
                    "variant": "bar",
                    "min": 80,
                    "max": 110,
                    "decimals": 1,
                    "thresholds": ATTAINMENT_STEPS,
                },
                "links": to_region,
                "layout": {"x": 0, "y": 5, "w": 5, "h": 4},
            },
            {
                "id": "vs-target",
                "title": "Revenue vs. target by month (USD)",
                "viz": "line",
                "description": "Full months only. The current month is left out until it ends.",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT to_char(month, 'Mon YYYY') AS month, sum(revenue) AS revenue, "
                    "sum(revenue_target) AS target FROM monthly_kpis "
                    "WHERE month < (SELECT max(month) FROM monthly_kpis) GROUP BY monthly_kpis.month "
                    "ORDER BY monthly_kpis.month",
                },
                "format": "number",
                "options": {"compact": True, "legend": "top"},
                "layout": {"x": 5, "y": 5, "w": 7, "h": 4},
            },
            {
                "id": "mix",
                "title": "Last quarter's revenue by region and channel",
                "description": "Each region's share, split by channel. Click a region to open its detail.",
                "viz": "treemap",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT region, channel, sum(revenue) AS revenue FROM daily_revenue "
                    f"WHERE {LAST_Q_DAYS} GROUP BY region, channel",
                },
                "format": "number",
                "options": {"path": ["region", "channel"], "value": "revenue", "compact": True},
                "links": to_region,
                "layout": {"x": 0, "y": 9, "w": 6, "h": 5},
            },
            {
                "id": "regions",
                "title": "Regions, last full quarter",
                "viz": "table",
                "description": "Each row links to the region's detail.",
                "query": {
                    "sourceId": METRICS,
                    "sql": "SELECT region, sum(revenue) AS revenue, sum(revenue_target) AS target, "
                    "100.0 * sum(revenue) / sum(revenue_target) AS attainment, sum(orders) AS orders "
                    f"FROM monthly_kpis WHERE {LAST_Q} GROUP BY region ORDER BY attainment",
                },
                "options": {
                    "columns": [
                        {"name": "region", "label": "Region"},
                        {
                            "name": "revenue",
                            "label": "Revenue (USD)",
                            "align": "right",
                            "compact": True,
                            "decimals": 2,
                        },
                        {
                            "name": "target",
                            "label": "Target (USD)",
                            "align": "right",
                            "compact": True,
                            "decimals": 2,
                        },
                        {
                            "name": "attainment",
                            "label": "Attainment",
                            "format": "percent",
                            "decimals": 1,
                            "align": "right",
                        },
                        {"name": "orders", "label": "Orders", "align": "right", "compact": True},
                    ]
                },
                "links": to_region,
                "layout": {"x": 6, "y": 9, "w": 6, "h": 3},
            },
            {
                "id": "ops",
                "title": "Store error rate, last hour",
                "viz": "line",
                "description": "From the live service metrics. Open the service health dashboard from this panel's menu.",
                "query": {
                    "sourceId": OPS,
                    "timeField": "minute",
                    "sql": "SELECT time_bucket('1 minute', ts) AS minute, "
                    "100.0 * sum(errors) / nullif(sum(requests), 0) AS error_pct "
                    "FROM request_metrics GROUP BY minute ORDER BY minute",
                },
                "timeRange": {"from": "now-1h", "to": "now"},
                "format": "percent",
                "options": {"decimals": 1, "legend": "none"},
                "links": [
                    {"title": "Open service health", "dashboard": service_id, "carry": {"timeRange": False}}
                ],
                "layout": {"x": 6, "y": 12, "w": 6, "h": 2},
            },
        ],
    }
