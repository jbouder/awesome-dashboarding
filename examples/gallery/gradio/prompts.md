# Prompts · Gradio

## Demo prompt

**Where:** Claude Code in this repository, with the lab warehouse and
`make example gradio` running. **Time:** one to two minutes, plus a rebuild.

```text
In examples/gallery/gradio/app/app.py, extend the "ask about a region"
panel. Add a "Compare with" dropdown of regions. When it is set, the
summary adds one paragraph comparing the two regions' attainment and
partner revenue for the chosen quarter. Keep it template-based, no LLM.
```

**Expected:** a third input in the panel. EMEA against North America in
Q3 2026 says EMEA reached 89.6% and North America 104.9%, and that EMEA's
partner revenue fell while North America's held.

### Follow-ups

```text
Wrap the summarize function in a gr.Interface tab with three examples
(EMEA Q3 2026, LATAM Q3 2026, All Q2 2026) so people can click one.
```

```text
Show me how to call /summarize from Python with gradio_client.
```

**Point out:** the new feature is one function and one more input. The UI
and the API endpoint came with it.

**Fallback:** `make example gradio`, then open <http://localhost:3117>.

## Build prompt

**Where:** Claude Code in this repository. This reproduces `app/`.

```text
Build the Lumen Supply dashboard in Gradio, in examples/gallery/gradio/.
Follow examples/_shared/spec.md as far as Gradio reasonably allows. Read
examples/_shared/context.md for the data, metric definitions, formats, and
known answers, and examples/_shared/design-tokens.css for colors and type.
Copy the folder pattern of examples/03-streamlit/.

Data: connect with the WAREHOUSE_URL environment variable. Query only the
metrics views. Convert Postgres numeric values to float before charting.

Build with gr.Blocks(title="Lumen Supply · Gradio"):
1. A header with "Lumen Supply", the last full quarter, and "Data as of"
   from the latest order. Four KPI cards as HTML: revenue with change,
   target with the gap, attainment colored by band (danger #c2410c below
   92%, warning #b45309 below 98%, success #15803d otherwise) with a word
   label, orders with change.
2. Plotly charts in gr.Plot with transparent backgrounds: revenue against
   target by month, attainment by region with a line at 100%, revenue by
   channel by quarter (web #2563eb, mobile #f08c2e, partner #0f9d8a).
3. Region and Channel dropdowns, a filter status line, and a Clear filters
   button. gr.Plot has no click event, so also let a row click in an
   attainment table set the region.
4. Top 15 products as a gr.Dataframe with search, formatted with a pandas
   Styler. Show a note when nothing matches.
5. A live error-rate-by-service chart from metrics.service_health, last 15
   minutes, redrawn by gr.Timer(5), with a line at 5%.
6. Signature section: an "ask" panel. Region and quarter dropdowns and a
   Summarize button call a function that writes a plain-English summary of
   what changed, from templates, no LLM.

Files: app/app.py, app/requirements.txt (pinned exact versions),
app/Dockerfile (python:3.13-slim, non-root user, PYTHONUNBUFFERED=1,
GRADIO_ANALYTICS_ENABLED=False, port 7860), compose.yaml with service and
profile ex-gradio, image dashlab-ex-gradio:local, port
127.0.0.1:3117:7860, no depends_on, and a python urllib healthcheck on port
7860. Pass theme and css to launch(), as Gradio 6 expects. Check: revenue
$5.64M, attainment 98.6%, EMEA lowest at 89.6%, and with EMEA picked,
partner revenue near $94K in the last full quarter. Then write a README
that says plainly where Gradio falls short of the spec.
```
