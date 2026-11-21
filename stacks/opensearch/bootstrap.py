"""Import the lab's index pattern, visualizations, and dashboard into
OpenSearch Dashboards. Runs once after Dashboards is up. Importing again
overwrites the lab's own objects and nothing else.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = os.environ.get("DASHBOARDS_URL", "http://opensearch-dashboards:5601")
PATTERN_ID = "lumen-logs"


def call(method: str, path: str, body: bytes | None = None, ctype: str = "application/json") -> dict:
    req = urllib.request.Request(
        BASE + path, data=body, method=method, headers={"osd-xsrf": "true", "Content-Type": ctype}
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read() or b"{}")


def vis(vid: str, title: str, vis_state: dict, query: str = "") -> dict:
    return {
        "id": vid,
        "type": "visualization",
        "attributes": {
            "title": title,
            "visState": json.dumps({"title": title, **vis_state}),
            "uiStateJSON": "{}",
            "description": "",
            "version": 1,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps(
                    {
                        "query": {"query": query, "language": "kuery"},
                        "filter": [],
                        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
                    }
                )
            },
        },
        "references": [
            {
                "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                "type": "index-pattern",
                "id": PATTERN_ID,
            }
        ],
    }


def date_histogram(aid: str, schema: str = "segment") -> dict:
    return {
        "id": aid,
        "enabled": True,
        "type": "date_histogram",
        "schema": schema,
        "params": {"field": "@timestamp", "interval": "auto", "min_doc_count": 1, "extended_bounds": {}},
    }


def terms(aid: str, field: str, schema: str, size: int = 10, order_by: str = "1") -> dict:
    return {
        "id": aid,
        "enabled": True,
        "type": "terms",
        "schema": schema,
        "params": {"field": field, "size": size, "order": "desc", "orderBy": order_by},
    }


def xy(kind: str, aggs: list[dict], stacked: bool = True) -> dict:
    mode = "stacked" if stacked else "normal"
    return {
        "type": kind,
        "aggs": aggs,
        "params": {
            "type": kind,
            "grid": {"categoryLines": False},
            "categoryAxes": [
                {
                    "id": "CategoryAxis-1",
                    "type": "category",
                    "position": "bottom",
                    "show": True,
                    "scale": {"type": "linear"},
                    "labels": {"show": True, "truncate": 100},
                    "title": {},
                }
            ],
            "valueAxes": [
                {
                    "id": "ValueAxis-1",
                    "name": "LeftAxis-1",
                    "type": "value",
                    "position": "left",
                    "show": True,
                    "scale": {"type": "linear", "mode": "normal"},
                    "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                    "title": {"text": ""},
                }
            ],
            "seriesParams": [
                {
                    "show": True,
                    "type": "histogram" if kind == "histogram" else "line",
                    "mode": mode,
                    "data": {"label": "Count", "id": "1"},
                    "valueAxis": "ValueAxis-1",
                    "drawLinesBetweenPoints": True,
                    "lineWidth": 2,
                    "showCircles": False,
                }
            ],
            "addTooltip": True,
            "addLegend": True,
            "legendPosition": "right",
            "times": [],
            "addTimeMarker": False,
        },
    }


COUNT = {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}}

OBJECTS = [
    {
        "id": PATTERN_ID,
        "type": "index-pattern",
        "attributes": {"title": "lumen-logs-*", "timeFieldName": "@timestamp"},
        "references": [],
    },
    vis(
        "lumen-requests-by-status",
        "Requests by status class",
        xy("histogram", [COUNT, date_histogram("2"), terms("3", "status_class", "group", 5)]),
    ),
    vis(
        "lumen-errors-by-service",
        "5xx errors by service",
        xy("line", [COUNT, date_histogram("2"), terms("3", "service", "group", 5)], stacked=False),
        query="status >= 500",
    ),
    vis(
        "lumen-error-count",
        "5xx errors",
        {
            "type": "metric",
            "aggs": [COUNT],
            "params": {
                "addTooltip": True,
                "addLegend": False,
                "type": "metric",
                "metric": {
                    "percentageMode": False,
                    "useRanges": False,
                    "colorSchema": "Green to Red",
                    "metricColorMode": "None",
                    "colorsRange": [{"from": 0, "to": 10000}],
                    "labels": {"show": True},
                    "invertColors": False,
                    "style": {
                        "bgFill": "#000",
                        "bgColor": False,
                        "labelColor": False,
                        "subText": "",
                        "fontSize": 48,
                    },
                },
            },
        },
        query="status >= 500",
    ),
    vis(
        "lumen-errors-share",
        "Where the errors are",
        {
            "type": "pie",
            "aggs": [COUNT, terms("2", "service", "segment", 5)],
            "params": {
                "type": "pie",
                "addTooltip": True,
                "addLegend": True,
                "legendPosition": "right",
                "isDonut": True,
                "labels": {"show": True, "values": True, "last_level": True, "truncate": 100},
            },
        },
        query="status >= 500",
    ),
    vis(
        "lumen-slow-routes",
        "Slowest routes",
        {
            "type": "table",
            "aggs": [
                {
                    "id": "1",
                    "enabled": True,
                    "type": "avg",
                    "schema": "metric",
                    "params": {"field": "latency_ms", "customLabel": "Avg latency (ms)"},
                },
                {"id": "3", "enabled": True, "type": "count", "schema": "metric", "params": {}},
                terms("2", "route", "bucket", 10),
            ],
            "params": {
                "perPage": 10,
                "showPartialRows": False,
                "showMetricsAtAllLevels": False,
                "sort": {"columnIndex": None, "direction": None},
                "showTotal": False,
                "totalFunc": "sum",
                "percentageCol": "",
            },
        },
    ),
]

LAYOUT = [  # (visualization id, x, y, w, h) on a 48-column grid
    ("lumen-error-count", 0, 0, 12, 12),
    ("lumen-requests-by-status", 12, 0, 36, 12),
    ("lumen-errors-by-service", 0, 12, 30, 15),
    ("lumen-errors-share", 30, 12, 18, 15),
    ("lumen-slow-routes", 0, 27, 48, 15),
]


def dashboard() -> dict:
    panels, refs = [], []
    for i, (vid, x, y, w, h) in enumerate(LAYOUT):
        pid = str(uuid.uuid5(uuid.NAMESPACE_URL, vid))
        panels.append(
            {
                "panelIndex": pid,
                "gridData": {"x": x, "y": y, "w": w, "h": h, "i": pid},
                "embeddableConfig": {},
                "version": "3.10.0",
                "panelRefName": f"panel_{i}",
            }
        )
        refs.append({"name": f"panel_{i}", "type": "visualization", "id": vid})
    return {
        "id": "lumen-service-logs",
        "type": "dashboard",
        "attributes": {
            "title": "Lumen Supply service logs",
            "description": "Access logs from the lab's five services. Run make incident to see an error burst.",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"hidePanelTitles": False, "useMargins": True}),
            "timeRestore": True,
            "timeFrom": "now-1h",
            "timeTo": "now",
            "refreshInterval": {"pause": False, "value": 10000},
            "version": 1,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})
            },
        },
        "references": refs,
    }


def main() -> None:
    for _ in range(60):
        try:
            status = call("GET", "/api/status")
            if status.get("status", {}).get("overall", {}).get("state") == "green":
                break
        except (urllib.error.URLError, ConnectionError, json.JSONDecodeError):
            pass
        time.sleep(3)
    else:
        sys.exit("[opensearch-bootstrap] OpenSearch Dashboards did not become ready")

    ndjson = "\n".join(json.dumps(o) for o in [*OBJECTS, dashboard()]) + "\n"
    boundary = "dashlab" + uuid.uuid4().hex
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="lab.ndjson"\r\n'
        f"Content-Type: application/ndjson\r\n\r\n{ndjson}\r\n--{boundary}--\r\n"
    ).encode()
    try:
        res = call(
            "POST",
            "/api/saved_objects/_import?overwrite=true",
            body,
            f"multipart/form-data; boundary={boundary}",
        )
    except urllib.error.HTTPError as err:
        sys.exit(f"[opensearch-bootstrap] import failed: {err.code} {err.read()[:400]!r}")
    if not res.get("success"):
        sys.exit(f"[opensearch-bootstrap] import had errors: {json.dumps(res.get('errors'))[:600]}")
    call(
        "POST",
        "/api/opensearch-dashboards/settings",
        json.dumps({"changes": {"defaultIndex": PATTERN_ID}}).encode(),
    )
    print(f"[opensearch-bootstrap] imported {res.get('successCount')} objects")


if __name__ == "__main__":
    main()
