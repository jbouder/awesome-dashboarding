# 03 · An AI-coded Streamlit app

**Supports:** Part 1, Demo 3. **Types:** analytical, generative. **Needs:**
the lab warehouse and Claude Code. `make example streamlit-demo` runs the
reference build at <http://localhost:3101>.

Ask Claude Code for a Streamlit app on the same data, run it in a few
minutes, add a filter and a chart with a follow-up, then walk through the
Python you now own.

## Files

| File | What it is |
| --- | --- |
| `prompts.md` | The demo prompt, the follow-up, and the build prompt |
| `app/app.py` | The reference build, after the follow-up. About 100 lines |
| `app/Dockerfile`, `compose.yaml` | How `make example streamlit-demo` runs it |

The full Streamlit dashboard, built to the shared spec, is in
`examples/gallery/streamlit/`. This one is deliberately the size a one-minute
prompt produces.

## Run it live

1. `make up grafana` (or any stack) so the warehouse is running.
2. In an empty folder, start Claude Code and paste the demo prompt.
3. Run what it writes: `pip install streamlit psycopg[binary] pandas altair`
   and `streamlit run app.py`.
4. Paste the follow-up. Streamlit reloads on save.

## What to point out

- **Minutes, not days.** A working app from one prompt.
- **It used the semantic layer** because the prompt pointed at it. Its
  numbers match Superset and Holotable.
- **The code is yours.** About 100 lines, readable. That is the upside, full
  control and no license, and the downside: someone has to host it, secure
  it, and keep it correct.
- **marimo is the alternative** for a reactive notebook. See
  `examples/gallery/marimo/`.

## Fallback

`make example streamlit-demo`, then open <http://localhost:3101>.
