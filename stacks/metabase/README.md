# Metabase

**Types:** strategic, analytical. **License:** AGPL-3.0.
**URL:** <http://localhost:3002>, sign in as `admin@dashlab.local` /
`dashlab-admin-1`.

```sh
make up metabase
```

## What the lab sets up

`bootstrap.py` does the setup steps for you:

- The admin account.
- A connection named **Lab warehouse**, as `lab_ro`, limited to the
  `metrics`, `shop`, and `ops` schemas.
- A dashboard, **Lumen Supply overview**, with the same KPIs as Superset's
  Executive KPIs, written as SQL questions.
- Metabot, when `.env` sets `LLM_MODEL` and either `LLM_API_KEY` or
  `LLM_BASE_URL`. It uses the OpenAI-compatible connection. Change it in
  **Admin → AI**.

Metabase's own sample database is also there. Ignore it, or remove it in
**Admin → Databases**.

## Tour

1. Open **Lumen Supply overview**. The numbers match Superset's Executive KPIs
   exactly, because both read the same views.
2. Press **New → Question**, pick **Lab warehouse → Metrics → Daily Revenue**,
   and build "Revenue by channel, filtered to EMEA, by quarter" without SQL.
   This is where Metabase is strongest.
3. Build the same question on **Shop → Orders** instead. With no semantic
   layer you have to join order items and decide what counts as revenue.
4. If Metabot is on, ask it: "Which region missed its revenue target last
   quarter, and why?"
