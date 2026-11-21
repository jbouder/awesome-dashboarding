"""Superset config for the lab. Shared by the web app, the MCP server, and init."""

import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

# Superset's own metadata lives in the warehouse, in its own database.
SQLALCHEMY_DATABASE_URI = os.environ["SUPERSET_METADATA_URL"]

# No Redis in the lab. Simple in-process caches are fine for one user.
CACHE_CONFIG = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}
DATA_CACHE_CONFIG = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 60}
RATELIMIT_STORAGE_URI = "memory://"

FEATURE_FLAGS = {
    "DRILL_TO_DETAIL": True,
    "DRILL_BY": True,
    "DASHBOARD_RBAC": False,
}

# Local lab only: no CSRF on the REST API so the bootstrap script stays short.
WTF_CSRF_ENABLED = False

# --- MCP server ------------------------------------------------------------
# Every MCP tool runs as this user. The lab uses the admin so an agent can
# build charts and dashboards. Do not copy this to a shared deployment.
MCP_DEV_USERNAME = os.environ.get("SUPERSET_ADMIN_USERNAME", "admin")
MCP_AUTH_ENABLED = False
MCP_TOOL_SEARCH_CONFIG = {"enabled": False}
SUPERSET_WEBSERVER_ADDRESS = "http://superset:8088"
WEBDRIVER_BASEURL = "http://superset:8088/"
WEBDRIVER_BASEURL_USER_FRIENDLY = "http://localhost:8088/"
MCP_SERVICE_URL = "http://superset-mcp:5008"
