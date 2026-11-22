# Prompts · Part 2 Superset

## Demo prompt

**Where:** Claude Code with Superset's MCP server connected:

```sh
claude mcp add --transport http superset http://localhost:5008/mcp
```

**Time:** about a minute.

```text
Using the Superset tools, which region missed its revenue target last
quarter, and by how much? Use the Lab warehouse datasets and show me the
SQL you ran.
```

**Expected:** EMEA, at about 89.6% of target, about $181K short. The agent
lists datasets, reads `monthly_kpis`, and runs a query.

### Follow-up

```text
Make a chart in Superset of EMEA revenue by channel for the last four
quarters, and give me a link to it.
```

**Expected:** a new chart and an Explore link. The lab's MCP server acts as
the admin, so the agent can create charts. Delete it after the demo.

**Point out:** the agent works through governed datasets, not raw tables,
and anything it makes is a normal Superset object people can review.

**Fallback:** show the existing **EMEA revenue by channel, by quarter**
chart in **Revenue analysis**.

## Build prompts

These reproduce what the lab adds to Superset for this demo. Run them in
Claude Code in this repository.

### Row-level security

```text
Add stacks/superset/security.py, run as a one-shot service after
superset-bootstrap, that uses Superset's app context to create:
1. A "Lab viewer" role with Gamma's permissions plus datasource_access on
   every dataset in schema metrics and database_access on their database.
2. An "EMEA only" row-level security rule with clause region = 'EMEA' on
   those datasets, tied to an "EMEA only" role.
3. A user emea with password emea-viewer-1 and both roles.
Make it safe to run again. Add the service to stacks/superset/compose.yaml
and to the superset jobs in scripts/lab.sh.
```

### Embedding

```text
Turn on Superset embedding for the lab: in stacks/superset/superset_config.py
set the EMBEDDED_SUPERSET feature flag, GUEST_ROLE_NAME = "Lab viewer", a
guest-token secret, and turn off Talisman and HTTP_HEADERS so a page on
another localhost port can frame Superset (local only).

Then write examples/part-2/superset-embed/: a stdlib Python server on port
8000 and an index.html. The server signs in to Superset as the admin,
creates or reuses the embedded config for the executive-kpis dashboard,
and returns a guest token for one dashboard, with an rls clause
region = '<region>' when a region is given. index.html is a mock partner
portal with a region picker that embeds the dashboard with
@superset-ui/embedded-sdk 0.4.0 from unpkg. Add a Dockerfile, and a
compose.yaml with service ex-superset-embed, profile ex-superset-embed, on
127.0.0.1:3121.
```
