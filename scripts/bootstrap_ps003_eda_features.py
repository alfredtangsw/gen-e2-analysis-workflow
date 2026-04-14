"""PS-003 Phase 3: EDA + Feature Engineering.

Computes:
  - Workforce supply projections 2021-2035 (CAGR extrapolation, by profession)
  - Workforce demand projections 2021-2035 (WHO benchmarks × admissions)
  - Workforce gap and annual hiring targets (with attrition)
  - Bed demand projections 2021-2035 (ALOS formula)
  - Bed gap (demand minus supply trajectory)
  - Staff-facility alignment check (nurse:bed ratio per year)
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
import numpy as np
import yaml
from loguru import logger

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import kaleido  # noqa
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
PS001 = WS / "problem-statements/ps-001-healthcare-system-baseline"
PS_DIR = WS / "problem-statements/ps-003-integrated-resource-planning"
INTERIM = PS_DIR / "data/3_interim"
PROCESSED = PS_DIR / "data/4_processed"
RESULTS = PS_DIR / "results/tables"
FIGS = PS_DIR / "reports/figures"
LOGS = PS_DIR / "logs/etl"
NB_DIR = PS_DIR / "notebooks"
EDA_HANDOFF_DIR = WS / "docs/agent-handoffs/exploratory-analysis/ps-003-integrated-resource-planning"
FEAT_HANDOFF_DIR = WS / "docs/agent-handoffs/feature-engineering/ps-003-integrated-resource-planning"
for d in [EDA_HANDOFF_DIR, FEAT_HANDOFF_DIR, FIGS]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"eda_features_{TS}.log"), level="DEBUG")
logger.info("PS-003 EDA + Feature Engineering started")

with open(WS / "shared/config/base.yml") as f:
    P = yaml.safe_load(f)["planning_constants"]

FORECAST_YEARS = list(range(2021, 2036))

# ── Load inputs ───────────────────────────────────────────────────────────────
wf = pl.read_parquet(str(INTERIM / "ps003_workforce_supply_base.parquet"))
beds = pl.read_parquet(str(INTERIM / "ps003_beds_base.parquet"))
pop = pl.read_parquet(str(INTERIM / "ps003_population_base.parquet"))
adm_fcast = pl.read_parquet(str(INTERIM / "ps003_admissions_forecast_2021_2035.parquet"))
cagr_df = pl.read_csv(str(PS001 / "results/tables/ps001_cagr_by_profession.csv"))
logger.info(f"WF: {wf.shape} | Beds: {beds.shape} | Adm fcast: {adm_fcast.shape}")

# ── Derive average admission rate (Male+Female) ───────────────────────────────
adm_total = (adm_fcast.group_by("year")
             .agg(pl.col("forecast_value").mean().alias("avg_admission_rate_per_1000"))
             .sort("year"))
logger.info(f"Avg admission rate: {adm_total.shape}")

# Population projection: extend PS-001 pop to 2035 via linear trend (last 5 years)
pop_vals = pop.sort("year")["total_population"].to_list()
pop_yrs  = pop.sort("year")["year"].to_list()
# Fit linear slope on 2015-2021
slope_pop = np.polyfit([y for y in pop_yrs if y >= 2015],
                       [v for y, v in zip(pop_yrs, pop_vals) if y >= 2015], 1)
pop_proj_rows = []
for yr in FORECAST_YEARS:
    pop_proj_rows.append({"year": yr, "total_population": float(np.polyval(slope_pop, yr))})
pop_proj = pl.DataFrame(pop_proj_rows).with_columns(
    pl.col("year").cast(pl.Int32),
    pl.col("total_population").cast(pl.Int64),
)
pop_all = pl.concat([pop.filter(pl.col("year") < 2021), pop_proj]).sort("year")
logger.info(f"Population projected to 2035: {pop_all.shape}")

# ── Merge pop into adm_total to get absolute admission volume ─────────────────
adm_merged = adm_total.join(pop_proj, on="year").with_columns(
    (pl.col("avg_admission_rate_per_1000") * pl.col("total_population") / 1000)
    .alias("total_admissions")
).sort("year")

# ── OBJECTIVE 1: Workforce Supply Projection 2021-2035 ───────────────────────
# Use CAGR per profession to extrapolate from 2019 headcount
PROF_WAGES = {
    "nurses": P["rn_median_wage_sgd_monthly"],
    "doctors": P["gp_median_wage_sgd_monthly"],
    "pharmacists": P["pharmacist_wage_sgd_monthly"],
    "allied_health_professionals": P["allied_health_wage_sgd_monthly"],
    "dentists": P["allied_health_wage_sgd_monthly"],  # use allied health as proxy
}
PROF_ATTRITION = {
    "nurses": P["nurse_attrition_pct"] / 100,
    "doctors": P["doctor_attrition_pct"] / 100,
    "pharmacists": P["pharmacist_attrition_pct"] / 100,
    "allied_health_professionals": P["allied_health_attrition_pct"] / 100,
    "dentists": P["allied_health_attrition_pct"] / 100,
}

professions = cagr_df["profession"].to_list()
cagr_map = dict(zip(cagr_df["profession"].to_list(), cagr_df["cagr_pct"].to_list()))

# Get 2019 headcount per profession
wf_2019 = (wf.filter(pl.col("year") == 2019)
             .select(["profession", "headcount"])
             .to_dicts())
hc_2019 = {r["profession"]: r["headcount"] for r in wf_2019 if r["headcount"] is not None}
logger.info(f"2019 headcount: {hc_2019}")

supply_rows = []
for prof in professions:
    base_hc = hc_2019.get(prof)
    if base_hc is None:
        logger.warning(f"No 2019 headcount for {prof}, skipping")
        continue
    cagr = cagr_map.get(prof, 0) / 100
    for yr in FORECAST_YEARS:
        projected = base_hc * ((1 + cagr) ** (yr - 2019))
        supply_rows.append({"year": yr, "profession": prof, "supply_headcount": round(projected, 0),
                             "base_headcount_2019": base_hc, "cagr_pct": cagr_map.get(prof, 0),
                             "projection_type": "cagr_trend_continuation"})

supply_df = pl.DataFrame(supply_rows).with_columns(pl.col("year").cast(pl.Int32))
SUPPLY_PATH = PROCESSED / "ps003_workforce_supply_projection.parquet"
supply_df.write_parquet(str(SUPPLY_PATH), compression="snappy")
logger.info(f"Supply projection: {supply_df.shape} → {SUPPLY_PATH}")

# ── OBJECTIVE 2: Workforce Demand Projection 2021-2035 ───────────────────────
# Nurses: WHO benchmark nurses_per_10k_population
# Doctors: WHO benchmark doctors_per_10k_population
# Others: proportional to nurse hiring (apply historical staff-mix ratios)
STAFF_MIX = {p: hc_2019.get(p, 0) / hc_2019.get("nurses", 1) for p in professions}
logger.info(f"Staff mix ratios (relative to nurses): {STAFF_MIX}")

demand_rows = []
for row in adm_merged.to_dicts():
    yr = row["year"]
    pop_val = row["total_population"]
    pop_10k = pop_val / 10000

    # Required beds (Obj 4 formula used here as denominator for nurse demand)
    total_adm = row["total_admissions"]
    required_beds = total_adm * P["alos_days"] / (365 * P["target_occupancy_rate"])

    for prof in professions:
        if prof == "nurses":
            # WHO: nurse_bed_ratio_benchmark nurses per bed
            required = required_beds * P["nurse_bed_ratio_benchmark"]
        elif prof == "doctors":
            required = pop_10k * P["doctors_per_10k_benchmark"]
        else:
            # Scale other professions by their historical mix ratio relative to nurses
            nurse_required = required_beds * P["nurse_bed_ratio_benchmark"]
            required = nurse_required * STAFF_MIX.get(prof, 0.2)

        demand_rows.append({"year": yr, "profession": prof,
                             "demand_headcount": round(required, 0),
                             "required_beds": round(required_beds, 0),
                             "total_admissions": round(total_adm, 0)})

demand_df = pl.DataFrame(demand_rows).with_columns(pl.col("year").cast(pl.Int32))
DEMAND_PATH = PROCESSED / "ps003_workforce_demand_projection.parquet"
demand_df.write_parquet(str(DEMAND_PATH), compression="snappy")
logger.info(f"Demand projection: {demand_df.shape} → {DEMAND_PATH}")

# ── OBJECTIVE 3: Workforce Gap + Hiring Targets ───────────────────────────────
gap_rows = []
for prof in professions:
    s = supply_df.filter(pl.col("profession") == prof).sort("year")
    d = demand_df.filter(pl.col("profession") == prof).sort("year")
    joined = s.join(d, on="year").to_dicts()
    attrition = PROF_ATTRITION.get(prof, 0.05)
    prev_hc = hc_2019.get(prof, 0)

    for row in joined:
        yr = row["year"]
        supply = row["supply_headcount"]
        demand = row["demand_headcount"]
        gap = demand - supply
        # Hiring needed = gap + attrition replacement on current supply
        annual_hire = max(0, gap + supply * attrition)
        # Flag if hire target > 1.5× historical CAGR growth
        hist_growth = supply * abs(row.get("cagr_pct", 0) / 100)
        flag = annual_hire > hist_growth * 1.5 and annual_hire > 50
        gap_rows.append({
            "year": yr, "profession": prof,
            "supply_headcount": supply, "demand_headcount": demand,
            "gap": round(gap, 0), "annual_hiring_target": round(annual_hire, 0),
            "attrition_rate_pct": attrition * 100,
            "policy_intervention_needed": flag,
        })

gap_df = pl.DataFrame(gap_rows).with_columns(pl.col("year").cast(pl.Int32))
GAP_PATH = PROCESSED / "ps003_workforce_gap.parquet"
gap_df.write_parquet(str(GAP_PATH), compression="snappy")
logger.info(f"Gap analysis: {gap_df.shape} → {GAP_PATH}")

# ── OBJECTIVE 4: Bed Demand + Gap ─────────────────────────────────────────────
# Bed supply: extrapolate PS-001 bed growth CAGR to 2035
beds_vals = beds.sort("year")["total_beds"].to_list()
beds_yrs  = beds.sort("year")["year"].to_list()
bed_cagr = ((beds_vals[-1] / beds_vals[0]) ** (1 / (beds_yrs[-1] - beds_yrs[0])) - 1) if beds_vals[0] > 0 else 0
last_beds, last_yr = beds_vals[-1], beds_yrs[-1]
logger.info(f"Bed CAGR: {bed_cagr*100:.2f}% | Last known: {last_beds} beds in {last_yr}")

bed_rows = []
for row in adm_merged.to_dicts():
    yr = row["year"]
    total_adm = row["total_admissions"]
    required_beds = total_adm * P["alos_days"] / (365 * P["target_occupancy_rate"])
    projected_beds = last_beds * ((1 + bed_cagr) ** (yr - last_yr))
    bed_gap = required_beds - projected_beds
    bed_rows.append({
        "year": yr, "required_beds": round(required_beds, 0),
        "projected_beds_supply": round(projected_beds, 0),
        "bed_gap": round(bed_gap, 0),
        "total_admissions": round(total_adm, 0),
    })

bed_df = pl.DataFrame(bed_rows).with_columns(pl.col("year").cast(pl.Int32))
BED_PATH = PROCESSED / "ps003_bed_gap.parquet"
bed_df.write_parquet(str(BED_PATH), compression="snappy")
logger.info(f"Bed gap: {bed_df.shape} → {BED_PATH}")

# ── OBJECTIVE 5: Staff-Facility Alignment ────────────────────────────────────
nurse_supply = supply_df.filter(pl.col("profession") == "nurses").sort("year")
align_rows = []
for i, row in enumerate(nurse_supply.to_dicts()):
    yr = row["year"]
    nurse_hc = row["supply_headcount"]
    bed_row = bed_df.filter(pl.col("year") == yr).to_dicts()
    if not bed_row:
        continue
    proj_beds = bed_row[0]["projected_beds_supply"]
    req_beds  = bed_row[0]["required_beds"]
    actual_ratio = nurse_hc / proj_beds if proj_beds > 0 else 0
    benchmark    = P["nurse_bed_ratio_benchmark"]
    aligned = abs(actual_ratio - benchmark) / benchmark <= 0.20  # within 20% of benchmark
    align_rows.append({
        "year": yr, "nurse_supply_headcount": round(nurse_hc, 0),
        "projected_beds": round(proj_beds, 0), "required_beds": round(req_beds, 0),
        "nurse_bed_ratio_actual": round(actual_ratio, 4),
        "nurse_bed_ratio_benchmark": benchmark,
        "within_20pct_of_benchmark": aligned,
        "alignment_status": "ALIGNED" if aligned else "DIVERGED",
    })

align_df = pl.DataFrame(align_rows).with_columns(pl.col("year").cast(pl.Int32))
ALIGN_PATH = PROCESSED / "ps003_staff_facility_alignment.parquet"
align_df.write_parquet(str(ALIGN_PATH), compression="snappy")
logger.info(f"Alignment check: {align_df.shape} → {ALIGN_PATH}")
diverged_years = align_df.filter(pl.col("alignment_status") == "DIVERGED")["year"].to_list()
logger.info(f"Diverged years: {diverged_years}")

# ── EDA summary ───────────────────────────────────────────────────────────────
eda_rows = []
for prof in professions:
    s = gap_df.filter(pl.col("profession") == prof)
    eda_rows.append({
        "profession": prof,
        "supply_2021": int(s.filter(pl.col("year") == 2021)["supply_headcount"].to_list()[0] if s.filter(pl.col("year") == 2021).height else 0),
        "demand_2035": int(s.filter(pl.col("year") == 2035)["demand_headcount"].to_list()[0] if s.filter(pl.col("year") == 2035).height else 0),
        "gap_2035": int(s.filter(pl.col("year") == 2035)["gap"].to_list()[0] if s.filter(pl.col("year") == 2035).height else 0),
        "peak_hire_year": int(s.sort("annual_hiring_target", descending=True)["year"].to_list()[0]) if s.height else 0,
        "policy_flag_years": s.filter(pl.col("policy_intervention_needed") == True).height,
    })
eda_df = pl.DataFrame(eda_rows)
EDA_PATH = RESULTS / "ps003_eda_summary.csv"
eda_df.write_csv(str(EDA_PATH))
logger.info(f"EDA summary:\n{eda_df}")

# ── Figures ───────────────────────────────────────────────────────────────────
if HAS_PLOTLY:
    COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    # Fig 1: Workforce supply vs demand by profession
    fig1 = make_subplots(rows=1, cols=2, subplot_titles=["Workforce: Supply vs Demand (Nurses)", "Bed Gap 2021–2035"])
    for i, prof in enumerate(["nurses", "doctors"]):
        show = i == 0
        s = supply_df.filter(pl.col("profession") == prof).sort("year")
        d = demand_df.filter(pl.col("profession") == prof).sort("year")
        fig1.add_trace(go.Scatter(x=[int(v) for v in s["year"].to_list()],
                                   y=[float(v) for v in s["supply_headcount"].to_list()],
                                   name=f"{prof} supply", line=dict(color=COLORS[i]), showlegend=show), row=1, col=1)
        fig1.add_trace(go.Scatter(x=[int(v) for v in d["year"].to_list()],
                                   y=[float(v) for v in d["demand_headcount"].to_list()],
                                   name=f"{prof} demand", line=dict(color=COLORS[i], dash="dash"), showlegend=show), row=1, col=1)
    # Bed gap
    fig1.add_trace(go.Bar(x=[int(v) for v in bed_df["year"].to_list()],
                          y=[float(v) for v in bed_df["bed_gap"].to_list()],
                          name="Bed Gap", marker_color="#d62728"), row=1, col=2)
    fig1.update_layout(template="plotly_white", height=420, title="PS-003 Gap Analysis 2021–2035")
    P1 = str(FIGS / "ps003_gap_analysis.png")
    fig1.write_image(P1, width=1200, height=420, scale=1.5)
    logger.info(f"Fig1 → {P1}")

    # Fig 2: Nurse:bed alignment
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=[int(v) for v in align_df["year"].to_list()],
                               y=[float(v) for v in align_df["nurse_bed_ratio_actual"].to_list()],
                               name="Actual Ratio", mode="lines+markers"))
    fig2.add_hline(y=P["nurse_bed_ratio_benchmark"], line_dash="dash", line_color="red",
                   annotation_text=f"WHO Benchmark ({P['nurse_bed_ratio_benchmark']})")
    fig2.update_layout(title="Nurse:Bed Ratio Alignment 2021–2035",
                       xaxis_title="Year", yaxis_title="Nurses per Bed",
                       template="plotly_white", height=420)
    P2 = str(FIGS / "ps003_nurse_bed_alignment.png")
    fig2.write_image(P2, width=1000, height=420, scale=1.5)
    logger.info(f"Fig2 → {P2}")
else:
    P1 = P2 = "skipped"

# ── Notebook ──────────────────────────────────────────────────────────────────
import nbformat
NB_PATH = NB_DIR / "03_eda_features.ipynb"
cells_src = [
    f"# PS-003 EDA & Feature Engineering\nimport polars as pl\nfrom pathlib import Path\nPS_DIR = Path('{PS_DIR}')\nPROCESSED = PS_DIR / 'data/4_processed'\nRESULTS = PS_DIR / 'results/tables'",
    "supply = pl.read_parquet(str(PROCESSED / 'ps003_workforce_supply_projection.parquet'))\ndemand = pl.read_parquet(str(PROCESSED / 'ps003_workforce_demand_projection.parquet'))\ngap = pl.read_parquet(str(PROCESSED / 'ps003_workforce_gap.parquet'))\nprint('Supply:', supply.shape, '| Demand:', demand.shape, '| Gap:', gap.shape)",
    "beds = pl.read_parquet(str(PROCESSED / 'ps003_bed_gap.parquet'))\nalign = pl.read_parquet(str(PROCESSED / 'ps003_staff_facility_alignment.parquet'))\nprint('Beds gap:', beds.shape, '| Alignment:', align.shape)\nprint(align.head(5))",
    "eda = pl.read_csv(str(RESULTS / 'ps003_eda_summary.csv'))\nprint('EDA Summary:')\nprint(eda)",
    "# Gap 2035 by profession\nprint('Workforce gap at 2035:')\nprint(gap.filter(pl.col('year') == 2035).select(['profession','supply_headcount','demand_headcount','gap','annual_hiring_target']))",
]
nb = nbformat.v4.new_notebook()
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}
nbformat.write(nb, str(NB_PATH))

# ── Handoffs ──────────────────────────────────────────────────────────────────
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
NOW = datetime.now(timezone.utc).isoformat()
out_list = [{"path": str(p), "type": "parquet"} for p in [SUPPLY_PATH, DEMAND_PATH, GAP_PATH, BED_PATH, ALIGN_PATH]]
out_list += [{"path": str(EDA_PATH), "type": "csv"}, {"path": str(NB_PATH), "type": "notebook"},
             {"path": P1, "type": "png"}, {"path": P2, "type": "png"}]

for hdir, agent, next_a in [
    (EDA_HANDOFF_DIR, "exploratory-analysis", "feature-engineer"),
    (FEAT_HANDOFF_DIR, "feature-engineer", "model-forecasting"),
]:
    h = {"agent": agent, "problem_statement": "ps-003-integrated-resource-planning",
         "status": "success", "timestamp": NOW, "outputs": out_list, "next_agent": next_a,
         "key_findings": [
             f"Nurse demand 2035: {eda_df.filter(pl.col('profession')=='nurses')['demand_2035'].to_list()}",
             f"Diverged alignment years: {diverged_years}",
         ]}
    (hdir / f"{agent}_handoff_{TODAY}.json").write_text(json.dumps(h, indent=2))

print(f"\n{'='*60}")
print(f"  Processed parquets : 5")
print(f"  EDA summary rows   : {eda_df.height}")
print(f"  Diverged years     : {diverged_years}")
print(eda_df)
print(f"{'='*60}")
