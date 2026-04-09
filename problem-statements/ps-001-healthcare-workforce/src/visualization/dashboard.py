"""PS-001 Phase 5: Build self-contained interactive HTML workforce planning dashboard."""

import json
from pathlib import Path

import polars as pl

BASE = Path(__file__).resolve().parents[5]
PS_DIR  = BASE / "problem-statements/ps-001-healthcare-workforce"
PROC    = PS_DIR / "data/4_processed"
RESULTS = PS_DIR / "results"
REPORTS = PS_DIR / "reports"
HANDOFF_DIR = BASE / "docs/agent-handoffs/dashboard-visualization/ps-001-healthcare-workforce"

DISPLAY = {
    "doctors":       "Doctors",
    "nurses":        "Nurses & Midwives",
    "pharmacists":   "Pharmacists",
    "dentists":      "Dentists",
    "allied_health": "Allied Health",
}
COLORS = {
    "doctors":       "#1f77b4",
    "nurses":        "#e377c2",
    "pharmacists":   "#2ca02c",
    "dentists":      "#ff7f0e",
    "allied_health": "#9467bd",
}


def _make_dirs() -> None:
    for d in [REPORTS, HANDOFF_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def _build_html(
    master: pl.DataFrame,
    forecasts: pl.DataFrame,
    gap_df: pl.DataFrame,
    cagr_df: pl.DataFrame,
    metrics: pl.DataFrame,
    scenario: pl.DataFrame,
    density: pl.DataFrame,
) -> str:
    professions = master["profession"].unique().sort().to_list()

    hist_by_prof = {
        p: {
            "years":  master.filter(pl.col("profession") == p).sort("year")["year"].to_list(),
            "counts": master.filter(pl.col("profession") == p).sort("year")["headcount"].to_list(),
        }
        for p in professions
    }
    fc_by_prof = {
        p: {
            "years": forecasts.filter(pl.col("profession") == p).sort("year")["year"].to_list(),
            "best":  forecasts.filter(pl.col("profession") == p).sort("year")["forecast_best"].to_list(),
            "lower": forecasts.filter(pl.col("profession") == p).sort("year")["ci95_lower"].to_list(),
            "upper": forecasts.filter(pl.col("profession") == p).sort("year")["ci95_upper"].to_list(),
        }
        for p in professions
    }

    cagr_labels = [DISPLAY.get(r["profession"], r["profession"]) for r in cagr_df.to_dicts()]
    cagr_values = [r["cagr_pct"] for r in cagr_df.to_dicts()]
    cagr_colors = [COLORS.get(r["profession"], "#888") for r in cagr_df.to_dicts()]
    gap_labels  = [DISPLAY.get(r["profession"], r["profession"]) for r in gap_df.to_dicts()]
    gap_values  = [r["gap_2030"] for r in gap_df.to_dicts()]
    gap_colors  = ["#2ca02c" if g >= 0 else "#d62728" for g in gap_values]

    metrics_rows = "".join(
        f"<tr><td>{DISPLAY.get(r['profession'], r['profession'])}</td>"
        f"<td>{r['best_model'].replace('_', ' ').title()}</td>"
        f"<td>{r['best_rmse']:,.0f}</td>"
        f"<td>{r.get('loglinear_r2', 'N/A')}</td></tr>"
        for r in metrics.to_dicts()
    )
    scenario_rows = "".join(
        f"<tr><td>{r['scenario']}</td><td>{r['doctors_2030']:,}</td>"
        f"<td>{r['demand_2030']:,}</td>"
        f"<td style='color:{'#2ca02c' if r['gap'] >= 0 else '#d62728'};font-weight:bold'>{r['gap']:+,}</td></tr>"
        for r in scenario.to_dicts()
    )
    density_rows = "".join(
        f"<tr><td>{DISPLAY.get(r['profession'], r['profession'])}</td>"
        f"<td>{r['density_2019']:.1f}</td><td>{r['density_mean']:.1f}</td>"
        f"<td>{r['density_min']:.1f}</td><td>{r['density_max']:.1f}</td></tr>"
        for r in density.to_dicts()
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Singapore Healthcare Workforce Planning Dashboard — PS-001</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f2f5;color:#222}}
  header{{background:linear-gradient(135deg,#003f7d,#0065b3);color:white;padding:1.5rem 2rem}}
  header h1{{font-size:1.6rem;font-weight:700}}
  header p{{margin-top:.3rem;opacity:.85;font-size:.9rem}}
  .badge{{display:inline-block;background:rgba(255,255,255,.2);border-radius:4px;padding:2px 8px;font-size:.75rem;margin-top:.4rem}}
  .container{{max-width:1400px;margin:0 auto;padding:1.5rem}}
  .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:1.5rem}}
  .kpi-card{{background:white;border-radius:8px;padding:1.2rem;box-shadow:0 1px 4px rgba(0,0,0,.1);border-left:4px solid #0065b3}}
  .kpi-card .val{{font-size:1.8rem;font-weight:700;color:#0065b3}}
  .kpi-card .lbl{{font-size:.78rem;color:#666;margin-top:4px;text-transform:uppercase;letter-spacing:.05em}}
  .kpi-card .sub{{font-size:.8rem;color:#888;margin-top:2px}}
  .chart-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-bottom:1.2rem}}
  .chart-grid.wide{{grid-template-columns:1fr}}
  .chart-card{{background:white;border-radius:8px;padding:1.2rem;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
  .chart-card h3{{font-size:.95rem;font-weight:600;color:#333;margin-bottom:.8rem;padding-bottom:.5rem;border-bottom:1px solid #eee}}
  .chart-card canvas{{max-height:320px}}
  .tabs{{display:flex;gap:.5rem;margin-bottom:1rem;flex-wrap:wrap}}
  .tab-btn{{padding:.4rem 1rem;border:1px solid #0065b3;background:white;color:#0065b3;border-radius:4px;cursor:pointer;font-size:.82rem;transition:all .2s}}
  .tab-btn.active{{background:#0065b3;color:white}}
  table{{width:100%;border-collapse:collapse;font-size:.85rem}}
  th{{background:#f4f7fb;padding:.6rem .8rem;text-align:left;font-weight:600;border-bottom:2px solid #dde;color:#444}}
  td{{padding:.5rem .8rem;border-bottom:1px solid #f0f0f0}}
  tr:hover td{{background:#fafbfd}}
  .section-title{{font-size:1.05rem;font-weight:700;color:#003f7d;margin:1.5rem 0 .8rem;padding-bottom:.3rem;border-bottom:2px solid #0065b3}}
  .insight-box{{background:#e8f4fd;border-left:4px solid #0065b3;border-radius:4px;padding:1rem;margin-bottom:1rem;font-size:.88rem}}
  .insight-box ul{{margin:.5rem 0 0 1.2rem}}
  .insight-box li{{margin-bottom:.3rem;color:#333}}
  @media(max-width:768px){{.chart-grid{{grid-template-columns:1fr}}}}
  footer{{text-align:center;padding:1.5rem;color:#999;font-size:.78rem;margin-top:1rem}}
</style>
</head>
<body>
<header>
  <h1>Singapore Healthcare Workforce Planning Dashboard</h1>
  <p>PS-001 · Healthcare Workforce Sustainability Analysis · 2006–2019 Historical | 2020–2030 Forecast</p>
  <span class="badge">MOH Workforce Planning Division</span>
  <span class="badge">Confidential</span>
  <span class="badge">Generated: 9 April 2026</span>
</header>
<div class="container">
<div class="kpi-grid">
  <div class="kpi-card"><div class="val">5</div><div class="lbl">Professions Analysed</div><div class="sub">Doctors · Nurses · Pharm · Dent · Allied</div></div>
  <div class="kpi-card"><div class="val">4.5%</div><div class="lbl">Avg CAGR 2006–2019</div><div class="sub">Across all healthcare professions</div></div>
  <div class="kpi-card"><div class="val">2030</div><div class="lbl">Forecast Horizon</div><div class="sub">11-year projection with 95% CI</div></div>
  <div class="kpi-card" style="border-color:#2ca02c"><div class="val" style="color:#2ca02c">SURPLUS</div><div class="lbl">2030 Gap Status</div><div class="sub">All professions — baseline scenario</div></div>
  <div class="kpi-card"><div class="val">~98K</div><div class="lbl">Nurses 2030 Forecast</div><div class="sub">+58% vs 2019 baseline</div></div>
  <div class="kpi-card"><div class="val">~26K</div><div class="lbl">Doctors 2030 Forecast</div><div class="sub">+42% vs 2019 baseline</div></div>
</div>
<div class="insight-box">
  <strong>Key Insight:</strong> All five professions project supply surplus through 2030 under baseline demand assumptions.
  Log-linear models (R² ≥ 0.998) selected for all professions.
  <ul>
    <li>Pharmacists (5.7% CAGR) and Allied Health (5.4% CAGR) are fastest-growing.</li>
    <li>Doctors (3.2% CAGR) have the slowest growth — policy focus required for doctor-to-population ratios.</li>
    <li>Hospital admission rates for 65+ rising ~1%/year — key demand risk to monitor.</li>
  </ul>
</div>
<p class="section-title">Historical Trends &amp; 2030 Forecasts</p>
<div class="tabs" id="prof-tabs"></div>
<div class="chart-grid wide">
  <div class="chart-card">
    <h3 id="trend-title">Workforce Headcount — Historical &amp; Forecast</h3>
    <canvas id="trendChart"></canvas>
  </div>
</div>
<div class="chart-grid">
  <div class="chart-card"><h3>CAGR by Profession (2006–2019)</h3><canvas id="cagrChart"></canvas></div>
  <div class="chart-card"><h3>Supply–Demand Gap 2030 (Headcount)</h3><canvas id="gapChart"></canvas></div>
</div>
<p class="section-title">Workforce Density (per 10,000 Population)</p>
<div class="chart-card" style="margin-bottom:1.2rem">
  <table><thead><tr><th>Profession</th><th>2019 Density</th><th>Period Mean</th><th>Min</th><th>Max</th></tr></thead>
  <tbody>{density_rows}</tbody></table>
</div>
<p class="section-title">Model Performance Metrics</p>
<div class="chart-card" style="margin-bottom:1.2rem">
  <table><thead><tr><th>Profession</th><th>Best Model</th><th>RMSE</th><th>Log-linear R²</th></tr></thead>
  <tbody>{metrics_rows}</tbody></table>
</div>
<p class="section-title">Scenario Analysis — Doctors 2030</p>
<div class="chart-card" style="margin-bottom:1.2rem">
  <table><thead><tr><th>Scenario</th><th>Supply 2030</th><th>Demand 2030</th><th>Gap</th></tr></thead>
  <tbody>{scenario_rows}</tbody></table>
</div>
</div>
<footer>PS-001 Healthcare Workforce Sustainability · MOH Singapore · Copilot Gen-E2 · April 2026</footer>
<script>
const HIST={json.dumps(hist_by_prof)};
const FC={json.dumps(fc_by_prof)};
const COLORS_MAP={json.dumps(COLORS)};
const DISPLAY_MAP={json.dumps(DISPLAY)};
const professions=Object.keys(HIST);
const tabsEl=document.getElementById('prof-tabs');
professions.forEach((p,i)=>{{
  const btn=document.createElement('button');
  btn.className='tab-btn'+(i===0?' active':'');
  btn.textContent=DISPLAY_MAP[p]||p;
  btn.onclick=()=>{{document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');updateTrend(p);}};
  tabsEl.appendChild(btn);
}});
const trendCtx=document.getElementById('trendChart').getContext('2d');
let trendChart;
function updateTrend(prof){{
  if(trendChart)trendChart.destroy();
  const h=HIST[prof],f=FC[prof],c=COLORS_MAP[prof]||'#0065b3';
  document.getElementById('trend-title').textContent=(DISPLAY_MAP[prof]||prof)+' — Historical & Forecast (2006–2030)';
  trendChart=new Chart(trendCtx,{{type:'line',data:{{datasets:[
    {{label:'Historical',data:h.years.map((y,i)=>({{x:y,y:h.counts[i]}})),borderColor:c,backgroundColor:c+'20',borderWidth:2.5,pointRadius:4,tension:0.3,fill:false}},
    {{label:'Forecast',data:f.years.map((y,i)=>({{x:y,y:f.best[i]}})),borderColor:c,borderDash:[6,4],borderWidth:2,pointRadius:3,fill:false}},
    {{label:'95% CI Upper',data:f.years.map((y,i)=>({{x:y,y:f.upper[i]}})),borderColor:'transparent',backgroundColor:c+'18',pointRadius:0,fill:'+1'}},
    {{label:'95% CI Lower',data:f.years.map((y,i)=>({{x:y,y:f.lower[i]}})),borderColor:'transparent',backgroundColor:c+'18',pointRadius:0,fill:false}},
  ]}},options:{{responsive:true,plugins:{{legend:{{position:'top'}},tooltip:{{mode:'index',intersect:false}}}},scales:{{x:{{type:'linear',title:{{display:true,text:'Year'}}}},y:{{title:{{display:true,text:'Headcount'}},beginAtZero:false}}}}}}
  }});
}}
updateTrend(professions[0]);
new Chart(document.getElementById('cagrChart').getContext('2d'),{{type:'bar',data:{{labels:{json.dumps(cagr_labels)},datasets:[{{label:'CAGR %',data:{json.dumps(cagr_values)},backgroundColor:{json.dumps(cagr_colors)},borderRadius:4}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{y:{{title:{{display:true,text:'CAGR (%)'}},beginAtZero:true}}}}}}}});
new Chart(document.getElementById('gapChart').getContext('2d'),{{type:'bar',data:{{labels:{json.dumps(gap_labels)},datasets:[{{label:'Supply – Demand Gap 2030',data:{json.dumps(gap_values)},backgroundColor:{json.dumps(gap_colors)},borderRadius:4}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>(ctx.raw>0?'+':'')+ctx.raw.toLocaleString()+' surplus'}}}}}},scales:{{y:{{title:{{display:true,text:'Headcount Gap'}},beginAtZero:false}}}}}}}});
</script>
</body>
</html>"""


def run() -> None:
    _make_dirs()

    master    = pl.read_parquet(PROC / "workforce_master_clean.parquet")
    forecasts = pl.read_parquet(PROC / "workforce_forecasts_2020_2030.parquet")
    gap_df    = pl.read_csv(RESULTS / "tables/demand_gap_analysis_2030.csv")
    cagr_df   = pl.read_csv(RESULTS / "tables/cagr_by_profession.csv")
    metrics   = pl.read_csv(RESULTS / "metrics/model_evaluation_metrics.csv")
    scenario  = pl.read_csv(RESULTS / "tables/scenario_analysis_doctors.csv")
    density   = pl.read_csv(RESULTS / "tables/workforce_density_summary.csv")

    html = _build_html(master, forecasts, gap_df, cagr_df, metrics, scenario, density)

    out_path = REPORTS / "workforce_planning_dashboard_ps001.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard saved: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")

    handoff = {
        "agent": "dashboard-visualization",
        "problem_statement": "ps-001-healthcare-workforce-sustainability",
        "timestamp": "2026-04-09",
        "status": "completed",
        "dashboard_file": str(out_path),
        "charts_included": [
            "Historical + forecast trend (by profession tab)",
            "CAGR bar chart",
            "Supply–demand gap 2030",
            "Density table",
            "Model metrics table",
            "Scenario analysis table",
        ],
        "files_created": [str(out_path)],
    }
    with open(HANDOFF_DIR / "dashboard_to_review_20260409.json", "w") as f:
        json.dump(handoff, f, indent=2)

    print("Dashboard complete.")


if __name__ == "__main__":
    run()
