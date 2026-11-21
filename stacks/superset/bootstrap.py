"""Connect Superset to the lab warehouse and build two dashboards.

Runs once after Superset is healthy. Everything is looked up by name first,
so running it again changes nothing.

  Executive KPIs    the strategic view: revenue against target
  Revenue analysis  the analytical view: where revenue comes from
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("SUPERSET_URL", "http://superset:8088")
DB_NAME = "Lab warehouse"
DB_URI = os.environ["LAB_RO_URL"]


class Api:
    def __init__(self) -> None:
        token = self.call(
            "POST",
            "/api/v1/security/login",
            {
                "username": os.environ["SUPERSET_ADMIN_USERNAME"],
                "password": os.environ["SUPERSET_ADMIN_PASSWORD"],
                "provider": "db",
                "refresh": False,
            },
            auth=False,
        )["access_token"]
        self.token = token

    def call(self, method: str, path: str, body: dict | None = None, auth: bool = True) -> dict:
        req = urllib.request.Request(BASE + path, method=method)
        req.add_header("Content-Type", "application/json")
        if auth:
            req.add_header("Authorization", f"Bearer {self.token}")
        data = json.dumps(body).encode() if body is not None else None
        try:
            with urllib.request.urlopen(req, data) as res:
                return json.loads(res.read() or b"{}")
        except urllib.error.HTTPError as err:
            sys.exit(f"[superset-bootstrap] {method} {path} failed: {err.code} {err.read()[:400]!r}")

    def find(self, resource: str, column: str, value: str) -> int | None:
        q = json.dumps({"filters": [{"col": column, "opr": "eq", "value": value}]})
        res = self.call("GET", f"/api/v1/{resource}/?q={urllib.request.quote(q)}")
        return res["result"][0]["id"] if res.get("count") else None


def metric(sql: str, label: str) -> dict:
    return {"expressionType": "SQL", "sqlExpression": sql, "label": label}


REVENUE = metric("SUM(revenue)", "Revenue")
TARGET = metric("SUM(revenue_target)", "Target")
ATTAINMENT = metric("SUM(revenue) / NULLIF(SUM(revenue_target), 0)", "Attainment")
ORDERS = metric("SUM(orders)", "Orders")
AOV = metric("SUM(revenue) / NULLIF(SUM(orders), 0)", "Avg order value")


def chart(name: str, viz: str, dataset: str, params: dict) -> dict:
    return {"name": name, "viz": viz, "dataset": dataset, "params": params}


EXECUTIVE = [
    chart(
        "Revenue, last full quarter",
        "big_number_total",
        "monthly_kpis",
        {
            "metric": REVENUE,
            "time_range": "previous calendar quarter",
            "y_axis_format": "$,.3s",
            "subheader": "Completed orders, net of discounts",
        },
    ),
    chart(
        "Attainment, last full quarter",
        "big_number_total",
        "monthly_kpis",
        {
            "metric": ATTAINMENT,
            "time_range": "previous calendar quarter",
            "y_axis_format": ".1%",
            "subheader": "Revenue / target",
        },
    ),
    chart(
        "Orders, last full quarter",
        "big_number_total",
        "monthly_kpis",
        {
            "metric": ORDERS,
            "time_range": "previous calendar quarter",
            "y_axis_format": ",d",
        },
    ),
    chart(
        "Revenue vs. target by month",
        "echarts_timeseries_line",
        "monthly_kpis",
        {
            "x_axis": "month",
            "time_grain_sqla": "P1M",
            "metrics": [REVENUE, TARGET],
            "time_range": "No filter",
            "y_axis_format": "$,.2s",
            "rich_tooltip": True,
        },
    ),
    chart(
        "Attainment by region, last full quarter",
        "table",
        "monthly_kpis",
        {
            "query_mode": "aggregate",
            "groupby": ["region"],
            "metrics": [REVENUE, TARGET, ATTAINMENT],
            "time_range": "previous calendar quarter",
            "order_desc": True,
            "column_config": {
                "Attainment": {"d3NumberFormat": ".1%"},
                "Revenue": {"d3NumberFormat": "$,.0f"},
                "Target": {"d3NumberFormat": "$,.0f"},
            },
        },
    ),
]

ANALYSIS = [
    chart(
        "Weekly revenue by channel",
        "echarts_area",
        "daily_revenue",
        {
            "x_axis": "order_date",
            "time_grain_sqla": "P1W",
            "metrics": [REVENUE],
            "groupby": ["channel"],
            "time_range": "Last year",
            "stack": "Stack",
            "y_axis_format": "$,.2s",
            "rich_tooltip": True,
        },
    ),
    chart(
        "EMEA revenue by channel, by quarter",
        "echarts_timeseries_bar",
        "daily_revenue",
        {
            "x_axis": "order_date",
            "time_grain_sqla": "P3M",
            "metrics": [REVENUE],
            "groupby": ["channel"],
            "time_range": "Last year",
            "stack": "Stack",
            "y_axis_format": "$,.2s",
            "rich_tooltip": True,
            "adhoc_filters": [
                {
                    "clause": "WHERE",
                    "expressionType": "SIMPLE",
                    "subject": "region",
                    "operator": "==",
                    "comparator": "EMEA",
                }
            ],
        },
    ),
    chart(
        "Revenue by category",
        "pie",
        "line_facts",
        {
            "metric": REVENUE,
            "groupby": ["category"],
            "time_range": "previous calendar quarter",
            "number_format": "$,.2s",
            "show_labels": True,
            "label_type": "key_percent",
        },
    ),
    chart(
        "Average order value by segment",
        "echarts_timeseries_line",
        "daily_revenue",
        {
            "x_axis": "order_date",
            "time_grain_sqla": "P1M",
            "metrics": [AOV],
            "groupby": ["segment"],
            "time_range": "No filter",
            "y_axis_format": "$,.0f",
        },
    ),
    chart(
        "Top products, last full quarter",
        "table",
        "line_facts",
        {
            "query_mode": "aggregate",
            "groupby": ["product", "category"],
            "metrics": [REVENUE],
            "time_range": "previous calendar quarter",
            "row_limit": 15,
            "order_desc": True,
            "timeseries_limit_metric": REVENUE,
        },
    ),
]

DASHBOARDS = [
    ("Executive KPIs", "executive-kpis", EXECUTIVE, [[0, 1, 2], [3], [4]]),
    ("Revenue analysis", "revenue-analysis", ANALYSIS, [[0], [1, 2], [3, 4]]),
]

DATASETS = {
    "monthly_kpis": "month",
    "daily_revenue": "order_date",
    "line_facts": "order_date",
}


def layout(title: str, chart_ids: list[int], names: list[str], rows: list[list[int]]) -> dict:
    pos: dict = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": title}},
    }
    for r, row in enumerate(rows):
        row_id = f"ROW-{r}"
        pos["GRID_ID"]["children"].append(row_id)
        pos[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        width = 12 // len(row)
        for i in row:
            cid = f"CHART-{chart_ids[i]}"
            pos[row_id]["children"].append(cid)
            pos[cid] = {
                "type": "CHART",
                "id": cid,
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {
                    "chartId": chart_ids[i],
                    "width": width,
                    "height": 30 if len(row) == 3 else 60,
                    "sliceName": names[i],
                },
            }
    return pos


def main() -> None:
    api = Api()

    db_id = api.find("database", "database_name", DB_NAME)
    if db_id is None:
        db_id = api.call(
            "POST",
            "/api/v1/database/",
            {
                "database_name": DB_NAME,
                "sqlalchemy_uri": DB_URI,
                "expose_in_sqllab": True,
                "allow_run_async": False,
            },
        )["id"]
        print(f"[superset-bootstrap] created database {DB_NAME}")

    dataset_ids = {}
    for table, time_col in DATASETS.items():
        ds_id = api.find("dataset", "table_name", table)
        if ds_id is None:
            ds_id = api.call(
                "POST", "/api/v1/dataset/", {"database": db_id, "schema": "metrics", "table_name": table}
            )["id"]
            api.call("PUT", f"/api/v1/dataset/{ds_id}", {"main_dttm_col": time_col})
            print(f"[superset-bootstrap] created dataset metrics.{table}")
        dataset_ids[table] = ds_id

    for title, slug, charts, rows in DASHBOARDS:
        if api.find("dashboard", "dashboard_title", title) is not None:
            print(f"[superset-bootstrap] dashboard {title!r} exists")
            continue
        dash_id = api.call(
            "POST", "/api/v1/dashboard/", {"dashboard_title": title, "slug": slug, "published": True}
        )["id"]
        chart_ids = []
        for c in charts:
            ds = dataset_ids[c["dataset"]]
            params = {"viz_type": c["viz"], "datasource": f"{ds}__table", **c["params"]}
            time_range = params.pop("time_range", "No filter")
            params["adhoc_filters"] = params.get("adhoc_filters", []) + [
                {
                    "clause": "WHERE",
                    "expressionType": "SIMPLE",
                    "operator": "TEMPORAL_RANGE",
                    "subject": DATASETS[c["dataset"]],
                    "comparator": time_range,
                }
            ]
            chart_ids.append(
                api.call(
                    "POST",
                    "/api/v1/chart/",
                    {
                        "slice_name": c["name"],
                        "viz_type": c["viz"],
                        "datasource_id": ds,
                        "datasource_type": "table",
                        "params": json.dumps(params),
                        "dashboards": [dash_id],
                    },
                )["id"]
            )
        api.call(
            "PUT",
            f"/api/v1/dashboard/{dash_id}",
            {
                "position_json": json.dumps(layout(title, chart_ids, [c["name"] for c in charts], rows)),
                "json_metadata": json.dumps({"refresh_frequency": 0, "color_scheme": "supersetColors"}),
            },
        )
        print(f"[superset-bootstrap] created dashboard {title!r} with {len(chart_ids)} charts")

    print("[superset-bootstrap] done")


if __name__ == "__main__":
    main()
