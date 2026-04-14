"""PS-001 Phase 2a: Data Validation."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
from loguru import logger
import nbformat

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
RAW_WF = WS / "shared/data/1_raw/workforce"
RAW_MO = WS / "shared/data/1_raw/mortality"
PS_DIR = WS / "problem-statements/ps-001-healthcare-system-baseline"
RESULTS = PS_DIR / "results/tables"
LOGS = PS_DIR / "logs/etl"
HANDOFF_DIR = WS / "docs/agent-handoffs/validation/ps-001-healthcare-system-baseline"
for d in [RESULTS, LOGS, HANDOFF_DIR, PS_DIR / "notebooks"]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"validation_{TS}.log"), level="DEBUG")
logger.info("PS-001 data validation started")

NUMERIC_TYPES = (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16,
                 pl.UInt32, pl.UInt64, pl.Float32, pl.Float64)
records = []

def rec(table, check, status, detail):
    records.append({"table_name": table, "check_name": check, "status": status, "detail": str(detail)})
    sym = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}.get(status, "·")
    logger.info(f"{sym} [{status}] {table:<45} {check:<25} {str(detail)[:70]}")

def year_col(df):
    return next((c for c in df.columns if "year" in c.lower()), None)

def validate(path, domain):
    name = path.stem
    logger.info(f"--- validating {domain}/{path.name} ---")
    try:
        df = pl.read_csv(str(path), infer_schema_length=10000, truncate_ragged_lines=True)
    except Exception as e:
        rec(name, "file_readable", "FAIL", str(e)); return None

    rec(name, "file_readable", "PASS", f"{df.height} rows × {df.width} cols")

    # year continuity
    yc = year_col(df)
    if yc:
        years = sorted(df[yc].drop_nulls().cast(pl.Int32).to_list())
        gaps = sorted(set(range(years[0], years[-1]+1)) - set(years))
        if gaps:
            rec(name, "year_continuity", "FAIL", f"Missing years: {gaps}")
        else:
            rec(name, "year_continuity", "PASS", f"Continuous {years[0]}–{years[-1]}")
    else:
        rec(name, "year_continuity", "WARN", "No year column found")

    # null rates
    total_cells = df.height * df.width
    nulls = sum(df[c].null_count() for c in df.columns)
    rate = nulls / total_cells if total_cells > 0 else 0
    status = "FAIL" if rate > 0.20 else ("WARN" if rate > 0.05 else "PASS")
    rec(name, "null_rate", status, f"{nulls} nulls ({rate:.1%})")

    # duplicates
    dupes = df.height - df.unique().height
    rec(name, "duplicates", "WARN" if dupes > 0 else "PASS", f"{dupes} duplicate rows")

    # numeric negatives
    neg_issues = []
    for c in df.columns:
        if df[c].dtype in NUMERIC_TYPES and "year" not in c.lower():
            n_neg = df.filter(pl.col(c) < 0).height
            if n_neg > 0: neg_issues.append(f"{c}: {n_neg} negatives")
    rec(name, "numeric_ranges", "FAIL" if neg_issues else "PASS",
        "; ".join(neg_issues) if neg_issues else "All non-negative")

    return df

all_files = list(RAW_WF.glob("*.csv")) + list(RAW_MO.glob("*.csv"))
dfs = {}
for f in sorted(all_files):
    domain = "workforce" if f.parent == RAW_WF else "mortality"
    dfs[f.stem] = validate(f, domain)

# Cross-file year overlap
year_ranges = {}
for name, df in dfs.items():
    if df is None: continue
    yc = year_col(df)
    if yc:
        years = df[yc].drop_nulls().cast(pl.Int32).to_list()
        if years: year_ranges[name] = (min(years), max(years))

if year_ranges:
    ov_start = max(r[0] for r in year_ranges.values())
    ov_end   = min(r[1] for r in year_ranges.values())
    if ov_start <= ov_end:
        rec("cross_file", "year_overlap", "PASS", f"All overlap {ov_start}–{ov_end}")
    else:
        rec("cross_file", "year_overlap", "WARN", f"No common overlap: {year_ranges}")

# Write report CSV
df_report = pl.DataFrame(records)
report_path = RESULTS / "ps001_validation_report.csv"
df_report.write_csv(str(report_path))
logger.info(f"Validation report → {report_path}")

# Summary
total = len(records)
passed = sum(1 for r in records if r["status"] == "PASS")
warned = sum(1 for r in records if r["status"] == "WARN")
failed = sum(1 for r in records if r["status"] == "FAIL")
blocking = [r for r in records if r["status"] == "FAIL"]
gate = "PASSED" if failed == 0 else "FAILED"
logger.info(f"Quality gate: {gate} | PASS={passed} WARN={warned} FAIL={failed}")

# Notebook
NB_PATH = PS_DIR / "notebooks/02_data_validation.ipynb"
nb = nbformat.v4.new_notebook()
cells_src = [
    "import polars as pl\nfrom pathlib import Path\nWS = Path('/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow')\nRAW_WF = WS/'shared/data/1_raw/workforce'\nRAW_MO = WS/'shared/data/1_raw/mortality'\nprint('Paths set')",
    "report = pl.read_csv(str(WS/'problem-statements/ps-001-healthcare-system-baseline/results/tables/ps001_validation_report.csv'))\nprint(report)",
    "print(report.group_by('status').agg(pl.len().alias('count')))",
]
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}
nbformat.write(nb, str(NB_PATH))

# Handoff JSON
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
handoff = {
    "agent": "data-validation", "problem_statement": "ps-001-healthcare-system-baseline",
    "status": "success" if failed == 0 else "success_with_warnings",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "outputs": [
        {"path": str(report_path), "type": "csv", "description": "Validation report"},
        {"path": str(NB_PATH), "type": "notebook", "description": "Validation notebook"},
    ],
    "validation_summary": {"total_checks": total, "passed": passed, "warned": warned, "failed": failed},
    "blocking_issues": blocking,
    "recommended_cleaning_steps": [
        "Standardise column names to snake_case",
        "Cast year to Int32, filter to 2006–2021",
        "Cast string numeric columns to Float64",
        "Drop duplicate rows",
        "Investigate and handle null values in beds dataset",
    ],
    "year_ranges": {k: list(v) for k, v in year_ranges.items()},
    "notes": f"{len(all_files)} files validated. Gate: {gate}.",
}
HANDOFF_PATH = HANDOFF_DIR / f"validation_to_cleaning_{TODAY}.json"
HANDOFF_PATH.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff JSON → {HANDOFF_PATH}")

print(f"\n{'='*60}")
print(f"  Total checks : {total} | PASS={passed} WARN={warned} FAIL={failed}")
print(f"  Gate         : {gate}")
print(f"  REPORT CSV   : {report_path}")
print(f"  HANDOFF JSON : {HANDOFF_PATH}")
print(f"  NOTEBOOK     : {NB_PATH}")
print(f"{'='*60}")
