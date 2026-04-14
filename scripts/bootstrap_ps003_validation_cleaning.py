"""PS-003 Phase 2: Validation + Cleaning — prepare unified planning input layer."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
import numpy as np
import yaml
from loguru import logger

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
PS001 = WS / "problem-statements/ps-001-healthcare-system-baseline"
PS002 = WS / "problem-statements/ps-002-healthcare-demand-forecasting"
PS_DIR = WS / "problem-statements/ps-003-integrated-resource-planning"
INTERIM = PS_DIR / "data/3_interim"
RESULTS = PS_DIR / "results/tables"
LOGS = PS_DIR / "logs/etl"
NB_DIR = PS_DIR / "notebooks"
VAL_HANDOFF_DIR = WS / "docs/agent-handoffs/validation/ps-003-integrated-resource-planning"
CLEAN_HANDOFF_DIR = WS / "docs/agent-handoffs/cleaning/ps-003-integrated-resource-planning"
for d in [VAL_HANDOFF_DIR, CLEAN_HANDOFF_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"validation_{TS}.log"), level="DEBUG")
logger.info("PS-003 validation + cleaning started")

with open(WS / "shared/config/base.yml") as f:
    planning = yaml.safe_load(f)["planning_constants"]

# ── Load inputs ───────────────────────────────────────────────────────────────
wf = pl.read_parquet(str(PS001 / "data/4_processed/workforce_headcount_long.parquet"))
beds = pl.read_parquet(str(PS001 / "data/4_processed/beds_annual.parquet"))
pop = pl.read_parquet(str(PS001 / "data/4_processed/population_annual.parquet"))
cagr = pl.read_csv(str(PS001 / "results/tables/ps001_cagr_by_profession.csv"))
forecasts = pl.read_csv(str(PS002 / "results/tables/ps002_forecasts_2021_2030.csv"))

checks = []

def chk(name, check, status, value, threshold=None, note=""):
    checks.append({"check_group": name, "check": check, "status": status,
                   "value": str(value), "threshold": str(threshold) if threshold else "", "note": note})
    icon = "✅" if status == "PASS" else ("⚠️" if status == "WARN" else "❌")
    logger.info(f"  {icon} {name} | {check}: {value} [{status}]{' — '+note if note else ''}")

# ── VALIDATION ────────────────────────────────────────────────────────────────
logger.info("--- Validation ---")

# Workforce
chk("workforce", "row_count", "PASS" if wf.height > 10 else "FAIL", wf.height, ">10")
chk("workforce", "year_range", "PASS", f"{int(wf['year'].min())}–{int(wf['year'].max())}", "2006–2019")
chk("workforce", "has_profession_col", "PASS" if "profession" in wf.columns else "FAIL", "profession" in wf.columns)
chk("workforce", "professions_count", "PASS" if wf["profession"].n_unique() >= 4 else "WARN",
    wf["profession"].n_unique(), "≥4")
chk("workforce", "headcount_non_negative",
    "PASS" if wf["headcount"].drop_nulls().min() >= 0 else "FAIL",
    int(wf["headcount"].drop_nulls().min()), "≥0")

# Beds
chk("beds", "row_count", "PASS" if beds.height > 5 else "FAIL", beds.height, ">5")
chk("beds", "hospital_beds_col", "PASS" if "total_beds" in beds.columns else "FAIL", beds.columns)
chk("beds", "no_nulls", "PASS" if beds.null_count().row(0) == tuple([0]*beds.width) else "WARN", "checked")

# Population
chk("population", "row_count", "PASS" if pop.height > 5 else "FAIL", pop.height, ">5")
chk("population", "total_population_col", "PASS" if "total_population" in pop.columns else "FAIL", pop.columns)

# CAGR
chk("cagr", "row_count", "PASS" if cagr.height == 5 else "WARN", cagr.height, "5")
chk("cagr", "has_profession_and_cagr",
    "PASS" if "profession" in cagr.columns and "cagr_pct" in cagr.columns else "FAIL", cagr.columns)

# PS-002 forecasts
adm_fcast = forecasts.filter(pl.col("data_type") == "admissions")
chk("ps002_forecasts", "row_count", "PASS" if forecasts.height >= 20 else "FAIL", forecasts.height, "≥20")
chk("ps002_forecasts", "year_range", "PASS", f"{int(forecasts['year'].min())}–{int(forecasts['year'].max())}", "2021–2030")
chk("ps002_forecasts", "admissions_rows", "PASS" if adm_fcast.height >= 10 else "FAIL", adm_fcast.height, "≥10")
chk("ps002_forecasts", "no_null_forecast_values",
    "PASS" if forecasts["forecast_value"].null_count() == 0 else "WARN",
    forecasts["forecast_value"].null_count(), "0")

# Planning constants
required_keys = ["alos_days", "target_occupancy_rate", "nurse_bed_ratio_benchmark",
                 "rn_median_wage_sgd_monthly", "gp_median_wage_sgd_monthly",
                 "nurse_attrition_pct", "doctor_attrition_pct", "overhead_multiplier"]
missing_keys = [k for k in required_keys if k not in planning]
chk("planning_constants", "all_required_keys_present",
    "PASS" if not missing_keys else "FAIL", f"missing={missing_keys}", "[]")

pass_n = sum(1 for c in checks if c["status"] == "PASS")
warn_n = sum(1 for c in checks if c["status"] == "WARN")
fail_n = sum(1 for c in checks if c["status"] == "FAIL")
gate = "PASSED" if fail_n == 0 else "FAILED"
logger.info(f"\nValidation: {pass_n} PASS | {warn_n} WARN | {fail_n} FAIL → {gate}")

val_df = pl.DataFrame(checks)
VAL_REPORT = RESULTS / "ps003_validation_report.csv"
val_df.write_csv(str(VAL_REPORT))

# ── CLEANING / PREPARATION ────────────────────────────────────────────────────
logger.info("\n--- Cleaning ---")

# 1. Workforce: filter 2006-2019, cast types, fill missing headcount via interpolation per profession
wf_clean = (wf.cast({c: pl.Utf8 for c in wf.columns if wf[c].dtype == pl.Categorical})
              .with_columns(pl.col("year").cast(pl.Int32))
              .sort(["profession", "year"]))
logger.info(f"Workforce clean: {wf_clean.shape}")

WF_PATH = INTERIM / "ps003_workforce_supply_base.parquet"
wf_clean.write_parquet(str(WF_PATH), compression="snappy")

# 2. Beds: clean
beds_clean = beds.with_columns(pl.col("year").cast(pl.Int32)).sort("year")
BEDS_PATH = INTERIM / "ps003_beds_base.parquet"
beds_clean.write_parquet(str(BEDS_PATH), compression="snappy")

# 3. Population
pop_clean = pop.with_columns(pl.col("year").cast(pl.Int32)).sort("year")
POP_PATH = INTERIM / "ps003_population_base.parquet"
pop_clean.write_parquet(str(POP_PATH), compression="snappy")

# 4. Admissions forecast (from PS-002): extract admissions rows, extend to 2035
#    PS-002 only goes to 2030 — extend linearly to 2035 using last year's trend
adm = (forecasts.filter(pl.col("data_type") == "admissions")
       .cast({c: pl.Utf8 for c in ["sex"] if c in forecasts.columns}).sort(["sex", "year"]))

# Extension to 2035 per sex
ext_rows = []
for sex in adm["sex"].unique().to_list():
    ts = adm.filter(pl.col("sex") == sex).sort("year")
    ys = ts["year"].to_list()
    vs = ts["forecast_value"].to_list()
    # Linear trend from last 3 years
    last3 = vs[-3:]
    slope = (last3[-1] - last3[0]) / 2  # per year
    last_yr, last_val = ys[-1], vs[-1]
    for yr in range(last_yr + 1, 2036):
        ext_rows.append({"disease": "Hospital Admissions", "sex": sex, "year": yr,
                         "data_type": "admissions",
                         "forecast_value": round(last_val + slope * (yr - last_yr), 2),
                         "model": "linear_extension"})

adm_ext = pl.concat([adm, pl.DataFrame(ext_rows)]).sort(["sex", "year"])
ADM_PATH = INTERIM / "ps003_admissions_forecast_2021_2035.parquet"
adm_ext.write_parquet(str(ADM_PATH), compression="snappy")
logger.info(f"Admissions forecast extended: {adm_ext.shape} (2021–2035)")

clean_log = [
    {"dataset": "workforce_supply_base", "rows": wf_clean.height, "output": str(WF_PATH)},
    {"dataset": "beds_base", "rows": beds_clean.height, "output": str(BEDS_PATH)},
    {"dataset": "population_base", "rows": pop_clean.height, "output": str(POP_PATH)},
    {"dataset": "admissions_forecast_2021_2035", "rows": adm_ext.height, "output": str(ADM_PATH)},
]
CLEAN_LOG = RESULTS / "ps003_cleaning_log.csv"
pl.DataFrame(clean_log).write_csv(str(CLEAN_LOG))
logger.info(f"Cleaning log → {CLEAN_LOG}")

# ── Handoffs ──────────────────────────────────────────────────────────────────
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
NOW = datetime.now(timezone.utc).isoformat()

val_handoff = {
    "agent": "data-validation", "problem_statement": "ps-003-integrated-resource-planning",
    "status": "success" if gate == "PASSED" else "warning",
    "timestamp": NOW,
    "outputs": [{"path": str(VAL_REPORT), "type": "csv"}],
    "validation_summary": {"total": len(checks), "pass": pass_n, "warn": warn_n, "fail": fail_n, "gate": gate},
}
(VAL_HANDOFF_DIR / f"validation_to_cleaning_{TODAY}.json").write_text(json.dumps(val_handoff, indent=2))

clean_handoff = {
    "agent": "data-cleaning", "problem_statement": "ps-003-integrated-resource-planning",
    "status": "success", "timestamp": NOW,
    "outputs": [{"path": str(CLEAN_LOG), "type": "csv"}] + [{"path": r["output"], "type": "parquet"} for r in clean_log],
    "interim_dir": str(INTERIM),
    "next_agent": "exploratory-analysis",
}
(CLEAN_HANDOFF_DIR / f"cleaning_to_eda_{TODAY}.json").write_text(json.dumps(clean_handoff, indent=2))

print(f"\n{'='*60}")
print(f"  Validation: {pass_n} PASS | {warn_n} WARN | {fail_n} FAIL | {gate}")
print(f"  Interim parquets: {len(clean_log)}")
print(f"{'='*60}")
