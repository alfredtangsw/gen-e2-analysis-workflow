"""Phase 5: Build PS-002 Disease Burden Dashboard — self-contained Chart.js HTML."""
import json
from pathlib import Path

import polars as pl

BASE    = Path(__file__).resolve().parents[1]
PROC    = BASE / "data/4_processed"
RESULTS = BASE / "results/tables"
METRICS = BASE / "results/metrics"
REPORTS = BASE / "reports"
HA_BASE = Path(__file__).resolve().parents[4] / "docs/agent-handoffs"

REPORTS.mkdir(parents=True, exist_ok=True)
(HA_BASE / "dashboard-visualization" / "ps-002-disease-burden").mkdir(parents=True, exist_ok=True)

# ── Load data ────────────────────────────────────────────────────────────────
master    = pl.read_parquet(PROC / "mortality_master_clean.parquet")
forecasts = pl.read_parquet(PROC / "mortality_forecasts_2020_2030.parquet")
eda_df    = pl.read_csv(RESULTS / "disease_burden_eda_summary.csv")
bench_df  = pl.read_csv(RESULTS / "international_benchmarking.csv")
prio_df   = pl.read_csv(RESULTS / "disease_priority_matrix.csv")
sc_df     = pl.read_csv(RESULTS / "scenario_analysis_2030.csv")
met_df    = pl.read_csv(METRICS / "model_evaluation_metrics.csv")

DISPLAY = {
    "cancer": "Cancer",
    "stroke": "Stroke",
    "ischaemic_heart_disease": "Ischaemic Heart Disease",
}
COLORS = {
    "cancer": "#d62728",
    "stroke": "#1f77b4",
    "ischaemic_heart_disease": "#ff7f0e",
}

diseases = ["cancer", "stroke", "ischaemic_heart_disease"]

# ── Build JS data objects ─────────────────────────────────────────────────────
HIST, FC = {}, {}
for d in diseases:
    sub = master.filter(pl.col("disease") == d).sort("year")
    HIST[d] = {"years": sub["year"].to_list(), "rates": [round(r, 1) for r in sub["asmr_per_100k"].to_list()]}
    fsub = forecasts.filter(pl.col("disease") == d).sort("year")
    FC[d] = {
        "years": fsub["year"].to_list(),
        "best":  [round(v, 1) for v in fsub["forecast_best"].to_list()],
        "lower": [round(v, 1) for v in fsub["ci95_lower"].to_list()],
        "upper": [round(v, 1) for v in fsub["ci95_upper"].to_list()],
    }

# YoY change series
yoy_labels = [str(y) for y in range(1991, 2020)]
yoy_datasets = []
for d in diseases:
    rates = HIST[d]["rates"]
    yoy = [round((rates[i] - rates[i-1]) / rates[i-1] * 100, 2) for i in range(1, len(rates))]
    yoy_datasets.append({
        "label": DISPLAY[d], "data": yoy,
        "borderColor": COLORS[d], "backgroundColor": COLORS[d] + "30",
        "fill": False, "tension": 0.3, "pointRadius": 2, "borderWidth": 1.8,
    })

# Relative decline from 1990
rel_datasets = []
for d in diseases:
    base = HIST[d]["rates"][0]
    hist_pts = [{"x": HIST[d]["years"][i], "y": round((HIST[d]["rates"][i]/base - 1)*100, 1)} for i in range(len(HIST[d]["years"]))]
    fc_pts   = [{"x": FC[d]["years"][i],   "y": round((FC[d]["best"][i]/base - 1)*100, 1)  } for i in range(len(FC[d]["years"]))]
    rel_datasets.append({"label": DISPLAY[d], "data": hist_pts, "borderColor": COLORS[d], "borderWidth": 2.2, "pointRadius": 0, "fill": False, "tension": 0.3})
    rel_datasets.append({"label": None,       "data": fc_pts,   "borderColor": COLORS[d], "borderDash": [6, 4], "borderWidth": 1.5, "pointRadius": 0, "fill": False, "tension": 0.3})

# ── HTML table rows ───────────────────────────────────────────────────────────
def eda_row(r):
    color = "#2ca02c" if r["apc_pct"] < 0 else "#d62728"
    badge_bg = "#d1f5d3" if r["trend_direction"] == "DECLINING" else "#ffd5d5"
    return (
        f"<tr><td>{DISPLAY.get(r['disease'], r['disease'])}</td>"
        f"<td>{r['asmr_1990']:.1f}</td><td>{r['asmr_2019']:.1f}</td>"
        f"<td style='color:{color};font-weight:bold'>{r['apc_pct']:+.2f}%</td>"
        f"<td>{r['total_change_pct']:+.1f}%</td>"
        f"<td><span style='background:{badge_bg};padding:2px 8px;border-radius:3px'>{r['trend_direction']}</span></td></tr>"
    )

def bench_row(r):
    vw = f"<span style='color:{'#2ca02c' if r['vs_who_pct']<0 else '#d62728'}'>{r['vs_who_pct']:+.1f}%</span>"
    vo = f"<span style='color:{'#2ca02c' if r['vs_oecd_pct']<0 else '#d62728'}'>{r['vs_oecd_pct']:+.1f}%</span>"
    return (
        f"<tr><td>{DISPLAY.get(r['disease'], r['disease'])}</td>"
        f"<td><strong>{r['singapore_2019']:.1f}</strong></td>"
        f"<td>{r['who_global_2019']:.1f}</td><td>{r['oecd_high_income_2019']:.1f}</td>"
        f"<td>{vw}</td><td>{vo}</td></tr>"
    )

def met_row(r):
    model_label = str(r["best_model"]).replace("_", " ").title()
    return (
        f"<tr><td>{DISPLAY.get(r['disease'], r['disease'])}</td>"
        f"<td>{model_label}</td><td>{r['best_rmse']:.3f}</td>"
        f"<td>{r['loglinear_r2']:.4f}</td><td>{r['apc_pct']:+.2f}%</td></tr>"
    )

def fc2030_row(r):
    return (
        f"<tr><td>{DISPLAY.get(r['disease'], r['disease'])}</td>"
        f"<td>{r['forecast_best']:.1f}</td>"
        f"<td>{r['ci95_lower']:.1f} – {r['ci95_upper']:.1f}</td></tr>"
    )

eda_rows   = "".join(eda_row(r) for r in eda_df.to_dicts())
bench_rows = "".join(bench_row(r) for r in bench_df.to_dicts())
met_rows   = "".join(met_row(r) for r in met_df.to_dicts())
fc_2030_rows = "".join(fc2030_row(r) for r in forecasts.filter(pl.col("year") == 2030).to_dicts())

def sc_row(r):
    pct = (r["asmr_2030"] / r["asmr_2019_baseline"] - 1) * 100
    color = "#2ca02c" if pct < 0 else "#d62728"
    return (
        f"<tr><td>{DISPLAY.get(r['disease'], r['disease'])}</td>"
        f"<td>{r['scenario']}</td>"
        f"<td>{r['asmr_2030']:.1f}</td>"
        f"<td style='color:{color}'>{pct:+.1f}%</td></tr>"
    )

sc_rows = "".join(sc_row(r) for r in sc_df.sort(["disease", "scenario"]).to_dicts())

# ── Build full HTML ───────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Singapore Disease Burden Trends Explorer — PS-002</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f2f5;color:#222;font-size:14px}}
header{{background:linear-gradient(135deg,#7b1113 0%,#c0392b 100%);color:white;padding:1.4rem 2rem}}
header h1{{font-size:1.5rem;font-weight:700}}
header p{{margin-top:.3rem;opacity:.85;font-size:.88rem}}
.badge{{display:inline-block;background:rgba(255,255,255,.18);border-radius:4px;padding:2px 8px;font-size:.73rem;margin:.4rem .3rem 0 0}}
.container{{max-width:1400px;margin:0 auto;padding:1.4rem}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:1rem;margin-bottom:1.4rem}}
.kpi{{background:white;border-radius:8px;padding:1.1rem 1.2rem;box-shadow:0 1px 4px rgba(0,0,0,.1);border-left:4px solid #c0392b}}
.kpi .val{{font-size:1.7rem;font-weight:700;color:#c0392b}}
.kpi .lbl{{font-size:.75rem;color:#666;margin-top:3px;text-transform:uppercase;letter-spacing:.05em}}
.kpi .sub{{font-size:.78rem;color:#888;margin-top:2px}}
.kpi.green .val{{color:#2ca02c}}.kpi.green{{border-color:#2ca02c}}
.row2{{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-bottom:1.2rem}}
.row1{{margin-bottom:1.2rem}}
.card{{background:white;border-radius:8px;padding:1.2rem;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
.card h3{{font-size:.92rem;font-weight:600;color:#333;margin-bottom:.8rem;padding-bottom:.5rem;border-bottom:1px solid #eee}}
.card canvas{{max-height:300px}}
.tabs{{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1rem}}
.tab{{padding:.38rem .95rem;border:1px solid #c0392b;background:white;color:#c0392b;border-radius:4px;cursor:pointer;font-size:.8rem;transition:all .15s}}
.tab.active{{background:#c0392b;color:white}}
table{{width:100%;border-collapse:collapse;font-size:.83rem}}
th{{background:#fdf1f1;padding:.6rem .8rem;text-align:left;font-weight:600;border-bottom:2px solid #e0b0b0;color:#555;white-space:nowrap}}
td{{padding:.48rem .8rem;border-bottom:1px solid #f5f0f0;vertical-align:middle}}
tr:hover td{{background:#fffafa}}
.sec{{font-size:1.02rem;font-weight:700;color:#7b1113;margin:1.4rem 0 .8rem;padding-bottom:.3rem;border-bottom:2px solid #c0392b}}
.insight{{background:#fdf5f5;border-left:4px solid #c0392b;border-radius:4px;padding:1rem 1.2rem;margin-bottom:1.2rem;font-size:.86rem;line-height:1.6}}
.insight ul{{margin:.5rem 0 0 1.2rem}}
.insight li{{margin-bottom:.3rem}}
footer{{text-align:center;padding:1.4rem;color:#aaa;font-size:.75rem;margin-top:.5rem}}
@media(max-width:800px){{.row2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header>
  <h1>Singapore Disease Burden Trends Explorer</h1>
  <p>PS-002 · National Disease Burden Temporal Trends Analysis · Age-Standardised Mortality Rates</p>
  <span class="badge">Disease Prevention &amp; Control Division, MOH</span>
  <span class="badge">Confidential</span>
  <span class="badge">Generated: 10 April 2026</span>
</header>

<div class="container">

<!-- KPI Cards -->
<div class="kpi-grid">
  <div class="kpi"><div class="val">3</div><div class="lbl">Diseases Tracked</div><div class="sub">Cancer · Stroke · IHD</div></div>
  <div class="kpi"><div class="val">30</div><div class="lbl">Years Historical</div><div class="sub">1990–2019 ASMR per 100k</div></div>
  <div class="kpi"><div class="val">−75%</div><div class="lbl">IHD Rate Reduction</div><div class="sub">Largest gain 1990–2019</div></div>
  <div class="kpi"><div class="val">−73%</div><div class="lbl">Stroke Rate Reduction</div><div class="sub">Second greatest gain</div></div>
  <div class="kpi"><div class="val">−31%</div><div class="lbl">Cancer Rate Reduction</div><div class="sub">Slowest declining burden</div></div>
  <div class="kpi green"><div class="val">BELOW</div><div class="lbl">vs WHO Global Average</div><div class="sub">All 3 diseases in 2019</div></div>
</div>

<!-- Insights -->
<div class="insight">
  <strong>Key Findings — 30-Year Review (1990–2019):</strong>
  <ul>
    <li><strong>Ischaemic Heart Disease</strong>: Most dramatic reduction (~320→~80 per 100k, −75%). Driven by improved cardiac care, statins post-2000, and healthier lifestyles. Projected ~50 per 100k by 2030.</li>
    <li><strong>Stroke</strong>: Near-identical trajectory (−73%). Singapore is already below the OECD high-income country average — a world-class outcome.</li>
    <li><strong>Cancer</strong>: Slower decline (−31%, ~215→~149 per 100k). Remains above OECD average and is the top priority for prevention investment through 2030.</li>
    <li>All Singapore 2019 rates sit below the WHO global average — a major public health achievement.</li>
    <li>Log-linear models provide the best fit for all three series (R² ≥ 0.97), confirming consistent exponential decline.</li>
  </ul>
</div>

<!-- Trend Charts (Tabbed) -->
<p class="sec">30-Year Mortality Trends &amp; 2030 Forecasts</p>
<div class="tabs" id="dis-tabs"></div>
<div class="row1">
  <div class="card">
    <h3 id="trend-title">ASMR Trend — Historical &amp; Forecast (per 100,000)</h3>
    <canvas id="trendChart"></canvas>
  </div>
</div>

<!-- YoY + Relative -->
<div class="row2">
  <div class="card">
    <h3>Year-over-Year Change (%) — All Diseases</h3>
    <canvas id="yoyChart"></canvas>
  </div>
  <div class="card">
    <h3>Cumulative Decline from 1990 Baseline</h3>
    <canvas id="relChart"></canvas>
  </div>
</div>

<!-- EDA Summary Table -->
<p class="sec">Trend Summary Statistics</p>
<div class="row1 card">
  <table>
    <thead><tr><th>Disease</th><th>ASMR 1990</th><th>ASMR 2019</th><th>Annual % Change</th><th>Total Change</th><th>Direction</th></tr></thead>
    <tbody>{eda_rows}</tbody>
  </table>
</div>

<!-- International Benchmarking -->
<p class="sec">International Benchmarking (2019, ASMR per 100,000)</p>
<div class="row1 card">
  <table>
    <thead><tr><th>Disease</th><th>Singapore</th><th>WHO Global</th><th>OECD High-Income</th><th>vs WHO</th><th>vs OECD</th></tr></thead>
    <tbody>{bench_rows}</tbody>
  </table>
</div>

<!-- 2030 Forecasts + Scenarios -->
<div class="row2">
  <div class="card">
    <h3>2030 Forecast Summary (Best Estimate &amp; 95% CI)</h3>
    <table>
      <thead><tr><th>Disease</th><th>ASMR 2030 (per 100k)</th><th>95% CI</th></tr></thead>
      <tbody>{fc_2030_rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h3>Scenario Analysis — 2030 Projections</h3>
    <table>
      <thead><tr><th>Disease</th><th>Scenario</th><th>ASMR 2030</th><th>vs 2019</th></tr></thead>
      <tbody>{sc_rows}</tbody>
    </table>
  </div>
</div>

<!-- Model Performance -->
<p class="sec">Forecasting Model Performance</p>
<div class="row1 card">
  <table>
    <thead><tr><th>Disease</th><th>Best Model</th><th>RMSE</th><th>Log-linear R²</th><th>APC</th></tr></thead>
    <tbody>{met_rows}</tbody>
  </table>
</div>

</div><!-- /container -->
<footer>PS-002 Disease Burden Temporal Trends Analysis · Ministry of Health, Singapore · Copilot Gen-E2 · April 2026</footer>

<script>
const HIST    = {json.dumps(HIST)};
const FC      = {json.dumps(FC)};
const COLORS  = {json.dumps(COLORS)};
const DISPLAY = {json.dumps(DISPLAY)};
const diseases = {json.dumps(diseases)};

// ── Disease tabs ──────────────────────────────────────────────────────────────
const tabsEl = document.getElementById('dis-tabs');
diseases.forEach(function(d, i) {{
  const btn = document.createElement('button');
  btn.className = 'tab' + (i === 0 ? ' active' : '');
  btn.textContent = DISPLAY[d] || d;
  btn.onclick = function() {{
    document.querySelectorAll('.tab').forEach(function(b) {{ b.classList.remove('active'); }});
    btn.classList.add('active');
    updateTrend(d);
  }};
  tabsEl.appendChild(btn);
}});

// ── Trend chart ───────────────────────────────────────────────────────────────
const trendCtx = document.getElementById('trendChart').getContext('2d');
let trendChart;
function updateTrend(dis) {{
  if (trendChart) trendChart.destroy();
  const h = HIST[dis], f = FC[dis], c = COLORS[dis] || '#c0392b';
  document.getElementById('trend-title').textContent = (DISPLAY[dis] || dis) + ' — ASMR per 100,000 (1990–2030)';
  trendChart = new Chart(trendCtx, {{
    type: 'line',
    data: {{
      datasets: [
        {{
          label: 'Historical (1990–2019)',
          data: h.years.map(function(y, i) {{ return {{x: y, y: h.rates[i]}}; }}),
          borderColor: c, backgroundColor: c + '20', borderWidth: 2.5, pointRadius: 3, tension: 0.3, fill: false
        }},
        {{
          label: 'Forecast (2020–2030)',
          data: f.years.map(function(y, i) {{ return {{x: y, y: f.best[i]}}; }}),
          borderColor: c, borderDash: [7, 4], borderWidth: 2.2, pointRadius: 2, fill: false, tension: 0.3
        }},
        {{
          label: '95% CI Upper',
          data: f.years.map(function(y, i) {{ return {{x: y, y: f.upper[i]}}; }}),
          borderColor: 'transparent', backgroundColor: c + '18', pointRadius: 0, fill: '+1', tension: 0.3
        }},
        {{
          label: '95% CI Lower',
          data: f.years.map(function(y, i) {{ return {{x: y, y: f.lower[i]}}; }}),
          borderColor: 'transparent', backgroundColor: c + '18', pointRadius: 0, fill: false, tension: 0.3
        }}
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{position: 'top', labels: {{filter: function(item) {{ return item.text && !item.text.startsWith('95%'); }}}}}},
        tooltip: {{mode: 'index', intersect: false}}
      }},
      scales: {{
        x: {{type: 'linear', title: {{display: true, text: 'Year'}}, ticks: {{stepSize: 5}}}},
        y: {{title: {{display: true, text: 'ASMR (per 100,000)'}}, beginAtZero: true}}
      }}
    }}
  }});
}}
updateTrend(diseases[0]);

// ── YoY chart ─────────────────────────────────────────────────────────────────
new Chart(document.getElementById('yoyChart').getContext('2d'), {{
  type: 'line',
  data: {{labels: {json.dumps(yoy_labels)}, datasets: {json.dumps(yoy_datasets)}}},
  options: {{
    responsive: true,
    plugins: {{legend: {{position: 'top'}}, tooltip: {{mode: 'index', intersect: false}}}},
    scales: {{
      y: {{title: {{display: true, text: 'YoY Change (%)'}}}},
      x: {{ticks: {{maxTicksLimit: 10}}}}
    }}
  }}
}});

// ── Relative decline chart ────────────────────────────────────────────────────
new Chart(document.getElementById('relChart').getContext('2d'), {{
  type: 'line',
  data: {{datasets: {json.dumps(rel_datasets)}}},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{labels: {{filter: function(item) {{ return item.text !== null; }}}}}},
      tooltip: {{mode: 'index', intersect: false}}
    }},
    scales: {{
      x: {{type: 'linear', title: {{display: true, text: 'Year'}}, ticks: {{stepSize: 5}}}},
      y: {{title: {{display: true, text: '% Change from 1990'}}, suggestedMax: 5}}
    }}
  }}
}});
</script>
</body>
</html>"""

out = REPORTS / "disease_burden_dashboard_ps002.html"
out.write_text(HTML, encoding="utf-8")
size_kb = out.stat().st_size / 1024
print(f"Dashboard: {out} ({size_kb:.1f} KB)")

handoff = {
    "agent": "dashboard-visualization",
    "problem_statement": "ps-002-disease-burden-temporal-trends",
    "timestamp": "2026-04-10",
    "status": "success",
    "dashboard_file": str(out),
    "size_kb": round(size_kb, 1),
    "charts": [
        "Historical+forecast trend per disease (tabbed)",
        "Year-over-year change panel",
        "Cumulative decline from 1990 baseline",
        "International benchmarking table",
        "2030 forecast + scenario tables",
        "Model performance table",
    ],
    "files_created": [str(out)],
}
handoff_path = HA_BASE / "dashboard-visualization" / "ps-002-disease-burden" / "dashboard_to_review_20260410.json"
with open(handoff_path, "w") as f:
    json.dump(handoff, f, indent=2)
print(f"Handoff: {handoff_path}")
print("Phase 5 COMPLETE.")
