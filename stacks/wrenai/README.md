# WrenAI

**Type:** generative. **License:** Apache 2.0.
**Status:** guide only. The lab does not run WrenAI in a container.

WrenAI is now a CLI and a set of skills for the coding agent you already use,
such as Claude Code, Cursor, or Codex. It gives the agent a governed semantic
layer: metric definitions, joins, and examples kept as YAML and Markdown in a
project folder. So the lab provides the database, and you bring the agent.

## Point it at the lab

1. Start any stack so the warehouse is running, for example `make up grafana`.
2. Follow WrenAI's own
   [quickstart for your agent](https://docs.getwren.ai/oss/get_started/quickstart).
3. When it asks for a database, give it the lab warehouse:

   | Setting | Value |
   | --- | --- |
   | Type | PostgreSQL |
   | Host | `localhost` |
   | Port | `5433` |
   | Database | `lab` |
   | User / password | `lab_ro` / `lab_ro` |
   | Schema | `metrics` (or `shop` to start from raw tables) |

4. Give it the lab's definitions as business context. Point it at
   `semantic/metrics.yml` in this repo.
5. Ask: "Which region missed its revenue target last quarter, and why?"

## Things to compare

- Start one project on `shop` and one on `metrics`. Does the raw-table
  project define revenue the same way the semantic layer does?
- WrenAI can deploy a dashboard to Vercel or Cloudflare Pages. That step needs
  your own account and is not part of the lab.
