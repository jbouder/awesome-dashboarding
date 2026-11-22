# Part 2 · Same question, every AI

**Supports:** Part 2, "Generative" and "Patterns: the semantic layer
decides accuracy". **Needs:** the stacks you want to compare, and a model.

Ask every AI feature in the lab the same question and check each answer
against the known one.

**The question:** "Which region missed its revenue target last quarter, and
why?"

**The known answer:** EMEA, at about 89.6% of target, about $181K short.
Its partner channel fell from about $297K to about $94K. Web and mobile
grew. Last quarter's total revenue was about $5.64M, at 98.6% of target.

## Where to ask

| Tool | Free version has AI? | Where | Setup |
| --- | --- | --- | --- |
| Holotable | Yes | New dashboard on **Lumen Supply (semantic layer)** | `LLM_*` in `.env`, `make restart holotable` |
| Metabase Metabot | Yes, with your own model | The Metabot chat | `LLM_*` in `.env`, `make restart metabase` |
| Superset | Through its MCP server | An agent | `claude mcp add --transport http superset http://localhost:5008/mcp` |
| Grafana | Through mcp-grafana | An agent. Ask the live-ops version below | `claude mcp add --transport http grafana http://localhost:5010/mcp` |
| ClickHouse | Through its MCP server | An agent | `claude mcp add --transport http clickhouse http://localhost:5009/mcp` |
| WrenAI | Yes, as agent skills | Your agent, after `stacks/wrenai/README.md` | WrenAI's CLI and skills |
| Rill | Yes, in Rill Developer | The **AI** button | Uses your OpenAI connector, or Rill's own hosted model service, which sends your question outside the lab |
| Lightdash | No. Its AI agents are enterprise features | | |
| Claude, no tools | Yes | A chat with `01-claude-artifact/extracts/raw/` attached | None |

For Grafana and the live metrics, ask instead: "Is anything wrong with our
services right now?" after `make incident`. The answer: checkout, error rate
around 10%.

## Results

Fill this in at rehearsal, with the model and date. The lab cannot record
answers by itself: every row needs a model you choose.

| Tool | Model | Date | Region | Attainment | Why | Matches? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Holotable | | | | | | | |
| Metabot | | | | | | | |
| Superset MCP | | | | | | | |
| ClickHouse MCP | | | | | | | |
| WrenAI | | | | | | | |
| Rill AI | | | | | | | |
| Claude, raw extract | | | | | | | |

## What to look for

- **Did it find EMEA?** Every tool on the semantic layer should.
- **Did it find why?** "Partner channel" is the real answer. "EMEA sold
  less" is not an answer.
- **What revenue did it use?** Tools on the `metrics` views or Cube say
  $5.64M for the quarter. Tools that went to `shop` tables may say up to
  $6.54M. See `05-two-answers`.
- **Can you see its work?** SQL, a spec, or a cited dataset. An answer you
  cannot check is a guess.

## Demo prompt

Pick two tools with different grounding, for example Holotable (semantic
layer) and the ClickHouse agent (its `lumen` database has no targets
table), and ask both:

```text
Which region missed its revenue target last quarter, and why?
```

**Expected:** Holotable answers EMEA and points at partner. The ClickHouse
agent either says it has no target data, or invents one. Either way, the
point makes itself.
