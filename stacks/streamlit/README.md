# Streamlit

**Type:** AI-built app. **License:** Apache 2.0.
**URL:** <http://localhost:3003>. No sign-in.

```sh
make up streamlit
```

## What the lab sets up

`app.py` is the kind of app an AI assistant writes from a prompt like "build
me a dashboard for this database": one file, about 150 lines, quick to make,
easy to change. It shows last quarter's KPIs, revenue against target, revenue
by channel, and attainment by region, with a region filter.

## Tour

1. Open the app. The numbers match Superset, Metabase, and Holotable, because
   it reads the `metrics` views.
2. Pick **EMEA** in the sidebar.
3. Switch **Revenue definition** to **Raw tables**. Revenue jumps from $5.64M
   to $6.54M and attainment to 114%. The app now sums every order line,
   including refunded and canceled orders, with no discounts. That is a
   plausible first guess for "revenue", and it is wrong.
4. Read `app.py` and think about owning it: hosting, sign-in, and keeping its
   numbers right are now yours.

## Notes

- Change `app.py` and run `make restart streamlit` to see the change.
