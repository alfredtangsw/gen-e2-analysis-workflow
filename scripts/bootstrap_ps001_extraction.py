"""PS-001 Phase 1: Data Extraction & Profiling bootstrap script."""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
from loguru import logger
import nbformat

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
WORKFORCE_RAW = WS / "shared/data/1_raw/workforce"
MORTALITY_RAW = WS / "shared/data/1_raw/mortality"
PS_DIR = WS / "problem-statements/ps-001-healthcare-system-baseline"
NOTEBOOKS_DIR = PS_DIR / "notebooks"
RESULTS_DIR = PS_DIR / "results/tables"
LOGS_DIR = PS_DIR / "logs/etl"
HANDOFFS_DIR = WS / "docs/agent-handoffs/extraction/ps-001-healthcare-system-baseline"

for d in [NOTEBOOKS_DIR, RESULTS_DIR, LOGS_DIR, HANDOFFS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = LOGS_DIR / f"extraction_{TS}.log"
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOG_PATH), level="DEBUG")
logger.info("PS-001 extraction started")

workforce_files = sorted(WORKFORCE_RAW.glob("*.csv"))
mortality_files = sorted(MORTALITY_RAW.glob("*.csv"))
logger.info(f"Workforce CSVs: {len(workforce_files)}, Mortality CSVs: {len(mortality_files)}")


def profile_csv(path: Path, domain: str) -> dict:
    logger.info(f"Profiling {domain}/{path.name}")
    try:
        df = pl.scan_csv(str(path), infer_schema_length=10000).collect()
        year_cols = [c for c in df.columns if c.strip().lower() in ("year", "data_year", "yr")]
        year_min = year_max = None
        if year_cols:
            yr = df[year_cols[0]].drop_nulls().cast(pl.Int64, strict=False).drop_nulls()
            if yr.len() > 0:
                year_min, year_max = int(yr.min()), int(yr.max())
        null_total = sum(df[c].null_count() for c in df.columns)
        return {
            "table_name": path.stem, "domain": domain,
            "row_count": df.height, "col_count": df.width,
            "year_min": year_min, "year_max": year_max,
            "null_count_total": null_total,
            "source_path": str(path), "status": "OK",
        }
    except Exception as exc:
        logger.error(f"FAILED {path.name}: {exc}")
        return {
            "table_name": path.stem, "domain": domain,
            "row_count": None, "col_count": None,
            "year_min": None, "year_max": None,
            "null_count_total": None,
            "source_path": str(path), "status": f"ERROR: {exc}",
        }


profiles = (
    [profile_csv(f, "workforce") for f in workforce_files]
    + [profile_csv(f, "mortality") for f in mortality_files]
)

profile_df = pl.DataFrame({
    "table_name": [p["table_name"] for p in profiles],
    "row_count": [p["row_count"] for p in profiles],
    "col_count": [p["col_count"] for p in profiles],
    "year_min": [p["year_min"] for p in profiles],
    "year_max": [p["year_max"] for p in profiles],
    "null_count_total": [p["null_count_total"] for p in profiles],
    "source_path": [p["source_path"] for p in profiles],
})
PROFILE_PATH = RESULTS_DIR / "ps001_data_profile.csv"
profile_df.write_csv(str(PROFILE_PATH))
logger.info(f"Profile CSV → {PROFILE_PATH}")
print(profile_df)

# Quality gates
failed_gates, warned_gates = [], []
for p in profiles:
    if p["status"] != "OK":
        failed_gates.append(f"{p['table_name']}: load error")
    elif (p["row_count"] or 0) == 0:
        failed_gates.append(f"{p['table_name']}: zero rows")
overall = "FAILED" if failed_gates else "PASSED"

# Handoff JSON
DATE_STAMP = datetime.now(timezone.utc).strftime("%Y%m%d")
NOW_ISO = datetime.now(timezone.utc).isoformat()
NB_PATH = NOTEBOOKS_DIR / "01_data_extraction.ipynb"

handoff = {
    "agent": "data-extractor",
    "problem_statement": "ps-001-healthcare-system-baseline",
    "status": "success" if not failed_gates else "failed",
    "timestamp": NOW_ISO,
    "outputs": [
        {"path": str(PROFILE_PATH), "type": "csv", "description": "Column-level profile of all source datasets"},
        {"path": str(NB_PATH), "type": "notebook", "description": "Extraction and profiling notebook"},
    ],
    "source_files": [str(f) for f in workforce_files + mortality_files],
    "extraction_summary": {
        "total_files": len(profiles),
        "total_rows": sum(p["row_count"] or 0 for p in profiles),
        "workforce_files": len(workforce_files),
        "mortality_files": len(mortality_files),
        "date_range": {
            "start": str(min((p["year_min"] for p in profiles if p["year_min"]), default="unknown")),
            "end": str(max((p["year_max"] for p in profiles if p["year_max"]), default="unknown")),
        },
    },
    "validation_results": {
        "overall_status": overall,
        "quality_flags": warned_gates,
        "blocking_issues": failed_gates,
    },
    "recommended_cleaning_steps": [
        "Standardise year column names across all tables",
        "Verify population age-band alignment between workforce and population datasets",
        "Cast numeric columns from String where inferred incorrectly",
    ],
    "notes": f"{len(profiles)} datasets profiled. Profile CSV: {PROFILE_PATH}.",
}
HANDOFF_PATH = HANDOFFS_DIR / f"extraction_to_validation_{DATE_STAMP}.json"
HANDOFF_PATH.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff JSON → {HANDOFF_PATH}")

# Build notebook via nbformat
cells_src = [
    (
        "# PS-001 Phase 1 — Data Extraction & Profiling\n"
        "import sys\nfrom pathlib import Path\nimport polars as pl\nfrom loguru import logger\n"
        "print('polars', pl.__version__)"
    ),
    (
        f"WS = Path('{WS}')\n"
        "WORKFORCE_RAW = WS / 'shared/data/1_raw/workforce'\n"
        "MORTALITY_RAW = WS / 'shared/data/1_raw/mortality'\n"
        "PS_DIR = WS / 'problem-statements/ps-001-healthcare-system-baseline'\n"
        "RESULTS_DIR = PS_DIR / 'results/tables'\n"
        "print('Paths set')"
    ),
    (
        "workforce_files = sorted(WORKFORCE_RAW.glob('*.csv'))\n"
        "mortality_files = sorted(MORTALITY_RAW.glob('*.csv'))\n"
        "print('Workforce:', [f.name for f in workforce_files])\n"
        "print('Mortality:', [f.name for f in mortality_files])"
    ),
    (
        "def profile_csv(path, domain):\n"
        "    df = pl.scan_csv(str(path), infer_schema_length=10000).collect()\n"
        "    year_cols = [c for c in df.columns if c.strip().lower() in ('year','data_year','yr')]\n"
        "    yr_min = yr_max = None\n"
        "    if year_cols:\n"
        "        yr = df[year_cols[0]].drop_nulls().cast(pl.Int64, strict=False).drop_nulls()\n"
        "        if yr.len() > 0: yr_min, yr_max = int(yr.min()), int(yr.max())\n"
        "    return {'table_name': path.stem, 'domain': domain, 'row_count': df.height,\n"
        "            'col_count': df.width, 'year_min': yr_min, 'year_max': yr_max,\n"
        "            'null_count_total': sum(df[c].null_count() for c in df.columns),\n"
        "            'source_path': str(path)}\n"
        "print('profile_csv() defined')"
    ),
    (
        "profiles = ([profile_csv(f, 'workforce') for f in workforce_files]\n"
        "           + [profile_csv(f, 'mortality') for f in mortality_files])\n"
        "for p in profiles:\n"
        "    print(f\"{p['table_name']}: {p['row_count']} rows x {p['col_count']} cols | {p['year_min']}-{p['year_max']}\")"
    ),
    (
        "profile_df = pl.DataFrame({k: [p[k] for p in profiles]\n"
        "    for k in ['table_name','row_count','col_count','year_min','year_max','null_count_total','source_path']})\n"
        "profile_df.write_csv(str(RESULTS_DIR / 'ps001_data_profile.csv'))\n"
        "print(profile_df)"
    ),
]

nb = nbformat.v4.new_notebook()
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}
nbformat.write(nb, str(NB_PATH))
logger.info(f"Notebook written → {NB_PATH}")

total_rows = sum(p["row_count"] or 0 for p in profiles)
print(f"\n{'='*62}")
print(f"  Datasets profiled : {len(profiles)}")
print(f"  Total rows        : {total_rows:,}")
print(f"  Quality gate      : {overall}")
print(f"  Blocking issues   : {failed_gates or 'None'}")
print(f"  PROFILE CSV  : {PROFILE_PATH}")
print(f"  HANDOFF JSON : {HANDOFF_PATH}")
print(f"  NOTEBOOK     : {NB_PATH}")
print(f"{'='*62}")
