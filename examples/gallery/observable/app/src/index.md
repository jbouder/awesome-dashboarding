---
title: Lumen Supply
---

```js
// Data. The loaders in data/ query the warehouse's metrics views at build time.
const kpis = FileAttachment("data/kpis.json").json();
const channels = FileAttachment("data/channels.json").json();
const products = FileAttachment("data/products.json").json();
```

```js
// Formats and colors, from context.md and the design tokens.
const money = (v) =>
  Math.abs(v) >= 1e6 ? `$${(v / 1e6).toFixed(2)}M` : Math.abs(v) >= 1e3 ? `$${Math.round(v / 1e3)}K` : `$${Math.round(v)}`;
const moneyFull = d3.format("$,.0f");
const pct = d3.format(".1%");
const count = d3.format(",");
const change = (now, before) => d3.format("+.1%")(now / before - 1);
const band = (a) =>
  a < 0.92 ? {key: "danger", label: "Missed"} : a < 0.98 ? {key: "warning", label: "Close"} : {key: "success", label: "On track"};
const channelOrder = ["web", "mobile", "partner"];
const channelColors = ["var(--series-1)", "var(--series-2)", "var(--series-3)"];
const asOf = new Date(kpis.asOf).toLocaleString("en-US", {
  month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC", timeZoneName: "short"
});
```

<div class="header">
  <h1>Lumen Supply</h1>
  <div class="muted">${kpis.period}, the last full quarter · Data as of ${asOf}</div>
</div>

```js
// The numbers the report below quotes. Each one comes from the data, so the
// prose changes when the data does.
const cur = kpis.current;
const prev = kpis.previous;
const worst = kpis.regions[0];
const best = kpis.regions.at(-1);
const worstByChannel = d3.rollup(
  channels.filter((d) => d.region === worst.region),
  (v) => d3.sum(v, (d) => d.revenue),
  (d) => d.channel,
  (d) => d.quarter
);
const drops = channelOrder
  .map((c) => ({
    channel: c,
    before: worstByChannel.get(c)?.get(kpis.previousPeriod) ?? 0,
    after: worstByChannel.get(c)?.get(kpis.period) ?? 0
  }))
  .sort((a, b) => (a.after - a.before) - (b.after - b.before));
const why = drops[0];
const grew = drops.filter((d) => d.after > d.before).map((d) => d.channel);
```

<div class="report">

**${kpis.period} in one paragraph.** Lumen Supply booked ${money(cur.revenue)} against a target of ${money(cur.target)}, or ${pct(cur.attainment)} attainment. Revenue moved ${change(cur.revenue, prev.revenue)} from ${kpis.previousPeriod} on ${count(cur.orders)} orders. **${worst.region} missed**: it reached ${pct(worst.attainment)} of target, ${money(worst.target - worst.revenue)} short. ${best.region} led at ${pct(best.attainment)}.

**Why ${worst.region} missed.** Its ${why.channel} channel fell from ${money(why.before)} to ${money(why.after)} quarter over quarter. ${grew.length ? `The ${grew.join(" and ")} channels grew.` : ""} Click ${worst.region} in the attainment chart to see it.

</div>

```js
// KPI row: last full quarter against the quarter before.
const b = band(cur.attainment);
display(html`<div class="grid grid-cols-4">
  <div class="card">
    <div class="kpi-label">Revenue</div>
    <div class="kpi-value">${money(cur.revenue)}</div>
    <div class="kpi-note muted">${change(cur.revenue, prev.revenue)} vs ${kpis.previousPeriod}</div>
  </div>
  <div class="card">
    <div class="kpi-label">Target</div>
    <div class="kpi-value">${money(cur.target)}</div>
    <div class="kpi-note muted">${cur.revenue >= cur.target ? `${money(cur.revenue - cur.target)} above` : `${money(cur.target - cur.revenue)} below`}</div>
  </div>
  <div class="card">
    <div class="kpi-label">Attainment</div>
    <div class="kpi-value band-${b.key}">${pct(cur.attainment)}</div>
    <div class="kpi-note"><span class="badge band-${b.key}">${b.label}</span></div>
  </div>
  <div class="card">
    <div class="kpi-label">Orders</div>
    <div class="kpi-value">${count(cur.orders)}</div>
    <div class="kpi-note muted">${change(cur.orders, prev.orders)} vs ${kpis.previousPeriod}</div>
  </div>
</div>`);
```

<div class="card">
  <h2>Revenue against target by month</h2>
  <h3>All regions, last 12 full months. Solid is revenue, dashed is target</h3>
  ${resize((width) => monthlyChart(width))}
</div>

```js
function monthlyChart(width) {
  const rows = kpis.monthly.flatMap((d) => [
    {month: new Date(d.month), series: "Revenue", value: d.revenue},
    {month: new Date(d.month), series: "Target", value: d.target}
  ]);
  return Plot.plot({
    width,
    height: 280,
    marginLeft: 56,
    x: {type: "utc", label: "Month", tickFormat: "%b %Y"},
    y: {label: "Revenue (USD)", grid: true, tickFormat: money, zero: true},
    color: {domain: ["Revenue", "Target"], range: ["var(--series-1)", "var(--series-2)"], legend: true},
    marks: [
      Plot.lineY(rows.filter((d) => d.series === "Revenue"), {x: "month", y: "value", stroke: "series", strokeWidth: 2.5}),
      Plot.lineY(rows.filter((d) => d.series === "Target"), {x: "month", y: "value", stroke: "series", strokeWidth: 2, strokeDasharray: "6,4"}),
      Plot.dot(rows, {x: "month", y: "value", fill: "series", r: 3}),
      Plot.tip(rows, Plot.pointer({x: "month", y: "value", stroke: "series",
        title: (d) => `${d.series}, ${d3.utcFormat("%B %Y")(d.month)}\n${moneyFull(d.value)}`}))
    ]
  });
}
```

## Filters

Click a region bar or a channel segment, or use the pickers. The filters apply to the charts and table below them.

```js
// The pickers are the single source of truth for the filters. Chart clicks
// set a picker's value and fire an input event, so every view stays in sync.
const regionInput = Inputs.select([null, ...kpis.regions.map((d) => d.region).sort()], {
  label: "Region", format: (d) => d ?? "All regions"
});
const channelInput = Inputs.select([null, ...channelOrder], {
  label: "Channel", format: (d) => d ?? "All channels"
});
function setFilter(input, value) {
  input.value = value;
  input.dispatchEvent(new Event("input", {bubbles: true}));
}
const clearButton = Inputs.button("Clear filters", {
  reduce: () => {
    setFilter(regionInput, null);
    setFilter(channelInput, null);
  }
});
```

```js
const region = Generators.input(regionInput);
const channel = Generators.input(channelInput);
```

<div class="filters">${regionInput}${channelInput}${clearButton}<span class="muted">Showing ${region ?? "all regions"}, ${channel ?? "all channels"}.</span></div>

<div class="grid grid-cols-2">
  <div class="card clickable">
    <h2>Attainment by region, ${kpis.period}</h2>
    <h3>Revenue as a share of target, worst first. Click a bar to filter</h3>
    ${resize((width) => attainmentChart(width, region))}
  </div>
  <div class="card clickable">
    <h2>Revenue by channel by quarter, ${region ?? "all regions"}</h2>
    <h3>Last four full quarters. Click a segment to filter the table</h3>
    ${resize((width) => channelChart(width, region, channel))}
  </div>
</div>

```js
function attainmentChart(width, selected) {
  const fig = Plot.plot({
    width,
    height: 240,
    marginLeft: 100,
    marginRight: 48,
    x: {label: "Attainment (% of target)", domain: [0, 1.15], tickFormat: "%", grid: true},
    y: {label: null, domain: kpis.regions.map((d) => d.region)},
    marks: [
      Plot.barX(kpis.regions, {
        y: "region", x: "attainment",
        fill: (d) => `var(--${band(d.attainment).key})`,
        fillOpacity: (d) => (selected && d.region !== selected ? 0.3 : 1)
      }),
      Plot.text(kpis.regions, {
        y: "region", x: "attainment", text: (d) => `${pct(d.attainment)} ${band(d.attainment).label}`,
        dx: 4, textAnchor: "start", fill: "currentColor"
      }),
      Plot.ruleX([1], {stroke: "currentColor", strokeDasharray: "4,3"}),
      Plot.tip(kpis.regions, Plot.pointerY({
        y: "region", x: "attainment",
        title: (d) => `${d.region}\n${pct(d.attainment)} of ${money(d.target)}\nRevenue ${moneyFull(d.revenue)}`
      }))
    ]
  });
  fig.addEventListener("click", () => {
    if (fig.value) setFilter(regionInput, fig.value.region === selected ? null : fig.value.region);
  });
  return fig;
}

function channelChart(width, selectedRegion, selectedChannel) {
  const rows = d3
    .flatRollup(
      channels.filter((d) => !selectedRegion || d.region === selectedRegion),
      (v) => d3.sum(v, (d) => d.revenue),
      (d) => d.quarter_start,
      (d) => d.quarter,
      (d) => d.channel
    )
    .map(([quarter_start, quarter, channel, revenue]) => ({quarter_start, quarter, channel, revenue}));
  if (!rows.length) return html`<div class="empty">No revenue for this filter.</div>`;
  const quarters = [...new Set(rows.sort((a, b) => d3.ascending(a.quarter_start, b.quarter_start)).map((d) => d.quarter))];
  const fig = Plot.plot({
    width,
    height: 240,
    marginLeft: 56,
    x: {label: null, domain: quarters},
    y: {label: "Revenue (USD)", grid: true, tickFormat: money},
    color: {domain: channelOrder, range: channelColors, legend: true},
    marks: [
      Plot.barY(rows, {
        x: "quarter", y: "revenue", fill: "channel", order: channelOrder,
        fillOpacity: (d) => (selectedChannel && d.channel !== selectedChannel ? 0.3 : 1),
        tip: true,
        title: (d) => `${d.channel}, ${d.quarter}\n${moneyFull(d.revenue)}`
      }),
      Plot.ruleY([0])
    ]
  });
  fig.addEventListener("click", () => {
    if (fig.value) setFilter(channelInput, fig.value.channel === selectedChannel ? null : fig.value.channel);
  });
  return fig;
}
```

## Top products, ${kpis.period}

```js
// Sum the product rows for the selected region and channel.
const productRows = d3
  .flatRollup(
    products.filter((d) => (!region || d.region === region) && (!channel || d.channel === channel)),
    (v) => ({units: d3.sum(v, (d) => d.units), revenue: d3.sum(v, (d) => d.revenue)}),
    (d) => d.product,
    (d) => d.category
  )
  .map(([product, category, {units, revenue}]) => ({product, category, units, revenue}))
  .sort((a, b) => b.revenue - a.revenue);
const search = view(Inputs.search(productRows, {placeholder: "Search products or categories"}));
```

```js
display(
  search.length
    ? Inputs.table(search.slice(0, 15), {
        columns: ["product", "category", "units", "revenue"],
        header: {product: "Product", category: "Category", units: "Units", revenue: "Revenue"},
        format: {units: count, revenue: moneyFull},
        align: {units: "right", revenue: "right"},
        sort: "revenue",
        reverse: true,
        rows: 16,
        select: false
      })
    : html`<div class="empty">No products for ${region ?? "all regions"} and ${channel ?? "all channels"}${productRows.length ? " match the search" : ""}.</div>`
);
display(html`<p class="muted">Top 15 of ${count(search.length)} products by revenue.</p>`);
```

---

<p class="muted">This whole dashboard is one Markdown file, <code>src/index.md</code>. The prose above quotes the data, so the words and the charts change together, and a change to either shows up as a plain diff in Git. The data was queried from the warehouse's <code>metrics</code> views when the site was built, at container start. It is a snapshot, so the spec's live error-rate panel is not here. Grafana is the right tool for a panel that refreshes every five seconds.</p>
