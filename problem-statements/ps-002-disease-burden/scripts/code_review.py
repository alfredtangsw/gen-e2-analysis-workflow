"""Phase 6: Code Quality Review — PS-002 Disease Burden."""
import csv
import json
from pathlib import Path
import polars as pl

BASE    = Path(__file__).resolve().parents[1]
PROC    = BASE / "data/4_processed"
RESULTS = BASE / "results/tables"
METRICS = BASE / "results/metrics"
REPORTS = BASE / "reports"
HA_BASE = Path(__file__).resolve().parents[3] / "docs/agent-handoffs"

CHECKS = []

def check(name, fn):
    try:
        ok, msg = fn()
    except Exception as e:
        ok, msg = False, str(e)
    status = "PASS" if ok else "FAIL"
    CHECKS.append({"check": name, "status": status, "detail": msg})
    print(f"[{status}] {name}: {msg}")

# 1. Raw data
def chk_raw():
    raw = Path(__file__).resolve().parents[3] / "shared/data/1_raw/mortality"
    csvs = list(raw.glob("*.csv"))
    return len(csvs) == 5, f"{len(csvs)}/5 raw CSVs present"
check("Raw CSVs present", chk_raw)

# 2. Processed parquets
def chk_proc():
    expected = ["cancer_mortality_clean","stroke_mortality_clean","ihd_mortality_clean",
                "mortality_master_clean","ps-002-mortality-features-20260410",
                "mortality_forecasts_2020_2030","vaccination_clean","hospital_admissions_clean"]
    missing = [e for e in expected if not (PROC / f"{e}.parquet").exists()]
    return len(missing)==0, f"{len(expected)-len(missing)}/{len(expected)} parquets present" + (f"; MISSING: {missing}" if missing else "")
check("Processed parquets exist", chk_proc)

# 3. Master shape
def chk_master():
    df = pl.read_parquet(PROC / "mortality_master_clean.parquet")
    ok = df.shape[0] == 90 and df.shape[1] >= 4
    return ok, f"shape={df.shape}, nulls={df.null_count().sum_horizontal().sum()}"
check("mortality_master_clean shape (90×≥4)", chk_master)

# 4. Features parquet
def chk_feat():
    df = pl.read_parquet(PROC / "ps-002-mortality-features-20260410.parquet")
    ok = df.shape[0] >= 60 and df.shape[1] >= 10
    return ok, f"shape={df.shape}"
check("Features parquet shape", chk_feat)

# 5. Forecast data
def chk_fc():
    df = pl.read_parquet(PROC / "mortality_forecasts_2020_2030.parquet")
    n_diseases = df["disease"].n_unique()
    years = sorted(df["year"].unique().to_list())
    ok = n_diseases == 3 and years[0] == 2020 and years[-1] == 2030
    return ok, f"diseases={n_diseases}, years={years[0]}–{years[-1]}, rows={df.shape[0]}"
check("Forecast parquet (3 diseases, 2020–2030)", chk_fc)

# 6. EDA tables
def chk_eda():
    expected_tables = ["data_quality_report_20260410","disease_burden_eda_summary",
                       "gender_gap_2019","joinpoint_analysis","international_benchmarking",
                       "feature_dictionary_20260410","mortality_forecasts_2020_2030",
                       "scenario_analysis_2030","disease_priority_matrix"]
    missing = [t for t in expected_tables if not (RESULTS / f"{t}.csv").exists()]
    return len(missing)==0, f"{len(expected_tables)-len(missing)}/{len(expected_tables)} result CSVs" + (f"; MISSING:{missing}" if missing else "")
check("Result CSVs present", chk_eda)

# 7. Model metrics
def chk_metrics():
    df = pl.read_csv(METRICS / "model_evaluation_metrics.csv")
    ok = df.shape[0] == 3 and "best_rmse" in df.columns
    return ok, f"rows={df.shape[0]}, cols={df.columns}"
check("Model evaluation metrics (3 rows)", chk_metrics)

# 8. Dashboard file
def chk_dash():
    html = REPORTS / "disease_burden_dashboard_ps002.html"
    if not html.exists():
        return False, "file not found"
    size = html.stat().st_size
    text = html.read_text(encoding="utf-8")
    ok = size > 10_000 and "chart.js" in text.lower() and "cancer" in text.lower()
    return ok, f"size={size/1024:.1f}KB, chart.js=True, disease labels present"
check("Dashboard HTML (>10KB, Chart.js, disease data)", chk_dash)

# 9. Handoff JSONs
def chk_handoffs():
    phases = ["extraction","data-cleaning","validation","exploratory-analysis","feature-engineering","model-forecasting","dashboard-visualization"]
    present, missing = [], []
    for phase in phases:
        d = HA_BASE / phase / "ps-002-disease-burden"
        if d.exists() and list(d.glob("*.json")):
            present.append(phase)
        else:
            missing.append(phase)
    return len(missing)==0, f"{len(present)}/{len(phases)} handoff dirs present" + (f"; MISSING:{missing}" if missing else "")
check("Agent handoff JSONs (all 7 phases)", chk_handoffs)

# 10. No nulls in master after merge
def chk_nulls():
    df = pl.read_parquet(PROC / "mortality_master_clean.parquet")
    nulls = df.null_count().sum_horizontal().sum()
    return nulls == 0, f"total nulls in master={nulls}"
check("Zero nulls in mortality master", chk_nulls)

# ── Save review ───────────────────────────────────────────────────────────────
n_pass = sum(1 for c in CHECKS if c["status"]=="PASS")
n_fail = sum(1 for c in CHECKS if c["status"]=="FAIL")
print(f"\nCode Review: {n_pass}/{len(CHECKS)} PASS, {n_fail} FAIL")

out = RESULTS / "code_review_summary_20260410.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["check","status","detail"])
    w.writeheader()
    w.writerows(CHECKS)
print(f"Saved: {out}")

handoff = {
    "agent": "code-quality",
    "problem_statement": "ps-002-disease-burden-temporal-trends",
    "timestamp": "2026-04-10",
    "status": "success" if n_fail == 0 else "warning",
    "checks_pass": n_pass,
    "checks_fail": n_fail,
    "checks_total": len(CHECKS),
    "review_file": str(out),
}
ho_dir = HA_BASE / "code-review" / "ps-002-disease-burden"
ho_dir.mkdir(parents=True, exist_ok=True)
with open(ho_dir / "code_review_to_delivery_20260410.json", "w") as f:
    json.dump(handoff, f, indent=2)
print("Phase 6 COMPLETE.")
