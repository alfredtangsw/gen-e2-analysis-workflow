"""PS-003 Phase 4: Prescriptive Analytics — Workforce Cost Estimation.

Computes:
  - Annual workforce cost per profession (headcount × salary × overhead)
  - Attrition replacement cost trajectory 2021-2035
  - Total workforce cost summary
  - Context vs government health expenditure trend
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
import numpy as np
import yaml
from loguru import logger

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
PS001 = WS / "problem-statements/ps-001-healthcare-system-baseline"
PS_DIR = WS / "problem-statements/ps-003-integrated-resource-planning"
PROCESSED = PS_DIR / "data/4_processed"
RESULTS = PS_DIR / "results/tables"
METRICS = PS_DIR / "results/metrics"
EXPORTS = PS_DIR / "results/exports"
LOGS = PS_DIR / "logs/etl"
NB_DIR = PS_DIR / "notebooks"
HANDOFF_DIR = WS / "docs/agent-handoffs/model-forecasting/ps-003-integrated-resource-planning"
for d in [METRICS, EXPORTS, HANDOFF_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"cost_estimation_{TS}.log"), level="DEBUG")
logger.info("PS-003 workforce cost estimation started")

with open(WS / "shared/config/base.yml") as f:
    P = yaml.safe_load(f)["planning_constants"]

OVERHEAD = P["overhead_multiplier"]
# Annual salary = monthly × 12 × overhead
SALARY_ANN = {
    "nurses":                    P["rn_median_wage_sgd_monthly"] * 12 * OVERHEAD,
    "doctors":                   P["gp_median_wage_sgd_monthly"] * 12 * OVERHEAD,
    "pharmacists":               P["pharmacist_wage_sgd_monthly"] * 12 * OVERHEAD,
    "allied_health_professionals": P["allied_health_wage_sgd_monthly"] * 12 * OVERHEAD,
    "dentists":                  P["allied_health_wage_sgd_monthly"] * 12 * OVERHEAD,
    "allied_health":             P["allied_health_wage_sgd_monthly"] * 12 * OVERHEAD,
}
ATTRITION = {
    "nurses": P["nurse_attrition_pct"] / 100,
    "doctors": P["doctor_attrition_pct"] / 100,
    "pharmacists": P["pharmacist_attrition_pct"] / 100,
    "allied_health_professionals": P["allied_health_attrition_pct"] / 100,
    "dentists": P["allied_health_attrition_pct"] / 100,
    "allied_health": P["allied_health_attrition_pct"] / 100,
}

# ── Load supply projections ───────────────────────────────────────────────────
supply = pl.read_parquet(str(PROCESSED / "ps003_workforce_supply_projection.parquet"))
gap_df = pl.read_parquet(str(PROCESSED / "ps003_workforce_gap.parquet"))

# ── Workforce Total Cost (existing headcount × salary) ───────────────────────
cost_rows = []
for row in supply.to_dicts():
    yr = row["year"]
    prof = row["profession"]
    hc = row["supply_headcount"]
    salary = SALARY_ANN.get(prof, SALARY_ANN["allied_health"])
    attrition_rate = ATTRITION.get(prof, 0.05)

    total_cost_sgd = hc * salary
    attrition_hires = hc * attrition_rate
    attrition_cost_sgd = attrition_hires * salary

    cost_rows.append({
        "year": yr, "profession": prof,
        "supply_headcount": round(hc, 0),
        "annual_salary_sgd": round(salary, 0),
        "total_workforce_cost_sgd_m": round(total_cost_sgd / 1_000_000, 2),
        "attrition_hires_per_year": round(attrition_hires, 0),
        "attrition_replacement_cost_sgd_m": round(attrition_cost_sgd / 1_000_000, 2),
    })

cost_df = pl.DataFrame(cost_rows).with_columns(pl.col("year").cast(pl.Int32))
COST_PATH = METRICS / "ps003_workforce_cost.csv"
cost_df.write_csv(str(COST_PATH))
logger.info(f"Workforce cost → {COST_PATH}")

# ── Aggregate cost by year (all professions) ──────────────────────────────────
annual_cost = (cost_df.group_by("year")
               .agg([
                   pl.col("total_workforce_cost_sgd_m").sum().alias("total_cost_sgd_m"),
                   pl.col("attrition_replacement_cost_sgd_m").sum().alias("attrition_cost_sgd_m"),
                   pl.col("attrition_hires_per_year").sum().alias("total_attrition_hires"),
                   pl.col("supply_headcount").sum().alias("total_workforce"),
               ])
               .sort("year"))
ANN_PATH = METRICS / "ps003_annual_cost_summary.csv"
annual_cost.write_csv(str(ANN_PATH))
logger.info(f"Annual cost summary:\n{annual_cost.head(5)}")

# ── Cost per profession at 2025, 2030, 2035 ──────────────────────────────────
snapshot_rows = []
for yr in [2025, 2030, 2035]:
    sub = cost_df.filter(pl.col("year") == yr)
    for row in sub.to_dicts():
        snapshot_rows.append(row)
snap_df = pl.DataFrame(snapshot_rows)
SNAP_PATH = METRICS / "ps003_cost_snapshots.csv"
snap_df.write_csv(str(SNAP_PATH))

# ── Stakeholder export ────────────────────────────────────────────────────────
export = annual_cost.with_columns([
    (pl.col("total_cost_sgd_m") / 1000).alias("total_cost_sgd_b"),
    (pl.col("attrition_cost_sgd_m") / 1000).alias("attrition_cost_sgd_b"),
]).select(["year", "total_workforce", "total_attrition_hires",
           "total_cost_sgd_m", "attrition_cost_sgd_m",
           "total_cost_sgd_b", "attrition_cost_sgd_b"])
EXPORT_PATH = EXPORTS / "ps003_workforce_cost_2021_2035.csv"
export.write_csv(str(EXPORT_PATH))
logger.info(f"Export → {EXPORT_PATH}")

# Log key metrics
logger.info("=== Key Cost Metrics ===")
for yr in [2021, 2025, 2030, 2035]:
    row = annual_cost.filter(pl.col("year") == yr).to_dicts()
    if row:
        r = row[0]
        logger.info(f"  {yr}: workforce={r['total_workforce']:.0f} | "
                    f"total cost S${r['total_cost_sgd_m']:,.0f}M | "
                    f"attrition hires={r['total_attrition_hires']:.0f}")

# ── Hiring targets summary (from gap_df) ─────────────────────────────────────
hiring_summary = (gap_df.group_by(["year"])
                  .agg(pl.col("annual_hiring_target").sum().alias("total_annual_hires"))
                  .sort("year"))
HIRE_PATH = METRICS / "ps003_hiring_targets.csv"
hiring_summary.write_csv(str(HIRE_PATH))

# ── Notebook ──────────────────────────────────────────────────────────────────
import nbformat
NB_PATH = NB_DIR / "04_cost_estimation.ipynb"
cells_src = [
    f"# PS-003 Workforce Cost Estimation\nimport polars as pl\nfrom pathlib import Path\nPS_DIR = Path('{PS_DIR}')\nMETRICS = PS_DIR / 'results/metrics'\nEXPORTS = PS_DIR / 'results/exports'",
    "cost = pl.read_csv(str(METRICS / 'ps003_workforce_cost.csv'))\nann = pl.read_csv(str(METRICS / 'ps003_annual_cost_summary.csv'))\nprint('Cost rows:', cost.shape)\nprint(ann)",
    "# 2035 forecast\nprint('2035 workforce cost by profession:')\nprint(cost.filter(pl.col('year') == 2035).select(['profession','supply_headcount','total_workforce_cost_sgd_m','attrition_replacement_cost_sgd_m']))",
    "print('Total annual cost trajectory:')\nprint(ann.select(['year','total_workforce','total_cost_sgd_m','attrition_cost_sgd_m']))",
]
nb = nbformat.v4.new_notebook()
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}
nbformat.write(nb, str(NB_PATH))

# ── Handoff ───────────────────────────────────────────────────────────────────
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
handoff = {
    "agent": "model-forecasting",
    "problem_statement": "ps-003-integrated-resource-planning",
    "status": "success",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "outputs": [{"path": str(p), "type": "csv"} for p in [COST_PATH, ANN_PATH, SNAP_PATH, HIRE_PATH, EXPORT_PATH]]
               + [{"path": str(NB_PATH), "type": "notebook"}],
    "key_metrics": {
        "total_workforce_2035": int(annual_cost.filter(pl.col("year") == 2035)["total_workforce"].to_list()[0]),
        "total_cost_2035_sgd_m": float(annual_cost.filter(pl.col("year") == 2035)["total_cost_sgd_m"].to_list()[0]),
        "attrition_hires_2021": float(annual_cost.filter(pl.col("year") == 2021)["total_attrition_hires"].to_list()[0]),
    },
    "note": "Workforce cost = supply headcount × annual salary × overhead. Costs labelled as WORKFORCE COST ESTIMATE — not total healthcare budget.",
    "next_agent": "dashboard-visualization",
}
HP = HANDOFF_DIR / f"cost_to_dashboard_{TODAY}.json"
HP.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff → {HP}")

print(f"\n{'='*60}")
print(f"  Cost rows          : {cost_df.height}")
print(f"  Annual cost rows   : {annual_cost.height}")
print(f"  Export             : {EXPORT_PATH}")
print(f"{'='*60}")
print(annual_cost.select(["year","total_workforce","total_cost_sgd_m","attrition_cost_sgd_m"]))
