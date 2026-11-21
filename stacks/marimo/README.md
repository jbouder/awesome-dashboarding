# marimo

**Type:** AI-built app. **License:** Apache 2.0.
**URL:** <http://localhost:3004>. No sign-in.

```sh
make up marimo
```

## What the lab sets up

`lumen_supply.py` is a reactive notebook, stored as plain Python. Every cell
reruns when a value it uses changes, so it works as an app. The lab serves it
in app view, with the code one click away.

## Tour

1. Open the notebook. Pick a region. The KPIs and the chart update.
2. In the chart, click a channel in the legend or a bar. The **Top products**
   table below narrows to that channel. That is a drill-down with no
   callbacks written: the table's cell reads the chart's selection.
3. Open the code from the menu at the top right.

## Edit it, with AI

Set `MARIMO_MODE=edit` in `.env` and run `make restart marimo`. The notebook
opens in marimo's editor, where **Generate with AI** writes and edits cells.
Point it at a model in the editor's settings. Edits stay in the container. Copy
them out with:

```sh
docker compose cp marimo:/home/lab/notebooks/lumen_supply.py stacks/marimo/
```
