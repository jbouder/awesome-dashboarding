# Lumen Supply: quarterly report

Revenue is completed orders net of discounts, from the warehouse's semantic
layer. This report is two files of Markdown and SQL. An AI assistant can
write one like it, and a reviewer can read the diff.

```sql last_quarter
select
  region,
  sum(revenue) as revenue,
  sum(revenue_target) as target,
  sum(revenue) / sum(revenue_target) as attainment,
  sum(orders) as orders
from metrics.monthly_kpis
where month >= date_trunc('quarter', now()) - interval '3 months'
  and month < date_trunc('quarter', now())
group by region
order by attainment
```

```sql totals
select
  sum(revenue) as revenue,
  sum(revenue_target) as target,
  sum(revenue) / sum(revenue_target) as attainment,
  sum(orders) as orders
from metrics.monthly_kpis
where month >= date_trunc('quarter', now()) - interval '3 months'
  and month < date_trunc('quarter', now())
```

## Last full quarter

{% big_value data="totals" value="max(revenue)" title="Revenue" fmt="usd2m" /%}
{% big_value data="totals" value="max(attainment)" title="Attainment" fmt="pct1" /%}
{% big_value data="totals" value="max(orders)" title="Orders" fmt="num0" /%}

{% table data="last_quarter" title="Attainment by region" /%}

EMEA is furthest below target. The next chart shows why.

```sql by_channel
select
  date_trunc('quarter', order_date)::date as quarter,
  region,
  channel,
  sum(revenue) as revenue
from metrics.daily_revenue
where order_date >= date_trunc('quarter', now()) - interval '12 months'
  and order_date < date_trunc('quarter', now())
group by 1, 2, 3
order by 1
```

## Revenue by channel, last four full quarters

{% dropdown id="region" data="by_channel" value_column="region" title="Region" /%}

{% bar_chart
  data="by_channel"
  x="quarter"
  y="sum(revenue)"
  series="channel"
  filters=["region"]
  fmt="usd1m"
  title="Revenue by channel"
/%}

```sql monthly
select month, sum(revenue) as revenue, sum(revenue_target) as target
from metrics.monthly_kpis
where month < date_trunc('month', now())
group by month
order by month
```

## Revenue vs. target by month

{% line_chart data="monthly" x="month" y=["sum(revenue)", "sum(target)"] fmt="usd1m" /%}
