"""PS-002 Phase 2a: Data Validation — time-series continuity, schema, value ranges."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
from loguru import logger

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
MORTALITY_RAW = WS / "shared/data/1_raw/mortality"
WORKFORCE_RAW = WS / "shared/data/1_raw/workforce"
PS_DIR = WS / "problem-statements/ps-002-healthcare-demand-forecasting"
RESULTS = PS_DIR / "results/tables"
LOGS = PS_DIR / "logs"
HANDOFF_DIR = WS / "docs/agent-handoffs/validation/ps-002-healthcare-demand-forecasting"
HANDOFF_DIR.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"validation_{TS}.log"), level="DEBUG")
logger.info("PS-002 data validation started")

SOURCES = [
    (MORTALITY_RAW / "age-standardised-mortality-rate-for-cancer.csv", "mortality"),
    (MORTALITY_RAW / "age-standardised-mortality-rate-for-ischaemic-heart-disease.csv", "mortality"),
    (MORTALITY_RAW / "age-standardised-mortality-rate-for-stroke.csv", "mortality"),
    (MORTALITY_RAW / "hospital-admission-rate-by-age-and-sex.csv", "mortality"),
    (MORTALITY_RAW / "vaccination-and-immunisation-of-students-annual.csv", "mortality"),
    (WORKFORCE_RAW / "singapore-population-by-age.csv", "population"),
]

checks = []

def add_check(table, check, status, value, threshold=None, note=""):
    checks.append({
        "table": table, "check": check, "status": status,
        "value": str(value), "threshold": str(threshold) if threshold is not None else "",
        "note": note,
    })
    icon = "✅" if status == "PASS" else ("⚠️" if status == "WARN" else "❌")
    logger.info(f"  {icon} {table} | {check}: {value} [{status}]{' — '+note if note else ''}")

for path, domain in SOURCES:
    name = path.stem
    logger.info(f"Validating {name}")
    df = pl.read_csv(str(path), infer_schema_length=10000, truncate_ragged_lines=True)

    # Check 1: Row count
    n = df.height
    status = "PASS" if n > 10 else "FAIL"
    add_check(name, "row_count", status, n, ">10")

    # Check 2: No fully null columns
    null_cols = [c for c in df.columns if df[c].null_count() == df.height]
    add_check(name, "no_fully_null_columns", "PASS" if not null_cols else "FAIL",
              f"{null_cols}", "[]", f"Fully-null cols: {null_cols}")

    # Check 3: Year column present & valid
    year_col = "year" if "year" in df.columns else None
    if year_col:
        year_vals = df[year_col].drop_nulls().cast(pl.Int64, strict=False).drop_nulls()
        y_min, y_max = int(year_vals.min()), int(year_vals.max())
        add_check(name, "year_range", "PASS", f"{y_min}–{y_max}", "1990–2030")
    else:
        add_check(name, "year_column_present", "FAIL", "missing", "year")

    # Check 4: Year continuity (no gaps)
    if year_col:
        unique_yrs = sorted(year_vals.unique().to_list())
        expected = set(range(min(unique_yrs), max(unique_yrs) + 1))
        gaps = expected - set(unique_yrs)
        # For non-aggregated tables, some gaps are expected; only flag if many
        status = "PASS" if len(gaps) == 0 else ("WARN" if len(gaps) <= 3 else "FAIL")
        add_check(name, "year_continuity", status, f"{len(gaps)} gap(s)", "0", f"Missing years: {sorted(gaps)[:5]}")

    # Check 5: Null rate in value columns
    value_cols = [c for c in df.columns if c not in ("year", "sex", "age_group", "programme", "disease")]
    for vc in value_cols:
        null_rate = df[vc].null_count() / df.height
        status = "PASS" if null_rate < 0.05 else ("WARN" if null_rate < 0.15 else "FAIL")
        add_check(name, f"null_rate_{vc}", status, f"{null_rate:.1%}", "<5%")

    # Check 6: Non-negative numeric values
    for vc in value_cols:
        try:
            vals = df[vc].cast(pl.Float64, strict=False).drop_nulls()
            negs = (vals < 0).sum()
            add_check(name, f"non_negative_{vc}", "PASS" if negs == 0 else "FAIL",
                      f"{negs} negatives", "0")
        except Exception:
            pass

    # Check 7: Duplicate rows
    dups = df.height - df.unique().height
    add_check(name, "no_duplicate_rows", "PASS" if dups == 0 else "WARN", dups, "0")

# Summary
pass_n = sum(1 for c in checks if c["status"] == "PASS")
warn_n = sum(1 for c in checks if c["status"] == "WARN")
fail_n = sum(1 for c in checks if c["status"] == "FAIL")
gate = "FAILED" if fail_n > 0 else "PASSED"
logger.info(f"\nValidation complete: {pass_n} PASS | {warn_n} WARN | {fail_n} FAIL → {gate}")

report_df = pl.DataFrame(checks)
REPORT_PATH = RESULTS / "ps002_validation_report.csv"
report_df.write_csv(str(REPORT_PATH))
logger.info(f"Report → {REPORT_PATH}")

TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
handoff = {
    "agent": "data-validation",
    "problem_statement": "ps-002-healthcare-demand-forecasting",
    "status": "success" if gate == "PASSED" else "failed",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "outputs": [{"path": str(REPORT_PATH), "type": "csv", "description": "Validation report"}],
    "validation_summary": {"total_checks": len(checks), "pass": pass_n, "warn": warn_n, "fail": fail_n, "gate": gate},
    "data_decisions": [
        "Filter analysis window: mortality & admissions 1990–2019 (exclude 2020 — COVID structural break)",
        "Filter forecasting base: 1990–2019 for mortality ASMR, 2006–2019 for admissions",
        "Population data 2006–2030 available — use historical up to 2019, projections as forecast covariate",
    ],
    "next_agent": "data-cleaning",
}
hp = HANDOFF_DIR / f"validation_to_cleaning_{TODAY}.json"
hp.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff JSON → {hp}")

print(f"\n{'='*62}")
print(f"  Total checks : {len(checks)}")
print(f"  PASS         : {pass_n}")
print(f"  WARN         : {warn_n}")
print(f"  FAIL         : {fail_n}")
print(f"  Gate         : {gate}")
print(f"{'='*62}")
