"""PS-002 Phase 1: Data Extraction & Profiling.

Source data:
  shared/data/1_raw/mortality/   — mortality & admission CSVs
  shared/data/1_raw/workforce/   — population CSV (Singapore population by age)
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
from loguru import logger
import nbformat

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
MORTALITY_RAW = WS / "shared/data/1_raw/mortality"
WORKFORCE_RAW = WS / "shared/data/1_raw/workforce"
PS_DIR = WS / "problem-statements/ps-002-healthcare-demand-forecasting"
NB_DIR = PS_DIR / "notebooks"
RESULTS = PS_DIR / "results/tables"
LOGS = PS_DIR / "logs"
HANDOFF_DIR = WS / "docs/agent-handoffs/extraction/ps-002-healthcare-demand-forecasting"

for d in [NB_DIR, RESULTS, LOGS, HANDOFF_DIR,
          PS_DIR / "data/3_interim", PS_DIR / "data/4_processed",
          PS_DIR / "reports/figures", PS_DIR / "reports/dashboards",
          PS_DIR / "models"]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"extraction_{TS}.log"), level="DEBUG")
logger.info("PS-002 data extraction started")

# Source files
MORTALITY_FILES = sorted(MORTALITY_RAW.glob("*.csv"))
POPULATION_FILE = WORKFORCE_RAW / "singapore-population-by-age.csv"

logger.info(f"Mortality/Admission CSVs: {len(MORTALITY_FILES)}")
logger.info(f"Population file exists: {POPULATION_FILE.exists()}")


def profile_csv(path: Path, domain: str) -> dict:
    logger.info(f"Profiling {domain}/{path.name}")
    try:
        df = pl.read_csv(str(path), infer_schema_length=10000, truncate_ragged_lines=True)
        year_col = next((c for c in df.columns if c.strip().lower() in ("year", "data_year", "yr")), None)
        year_min = year_max = None
        if year_col:
            yr = df[year_col].drop_nulls().cast(pl.Int64, strict=False).drop_nulls()
            if yr.len() > 0:
                year_min, year_max = int(yr.min()), int(yr.max())
        null_total = sum(df[c].null_count() for c in df.columns)
        return {
            "table_name": path.stem, "domain": domain,
            "row_count": df.height, "col_count": df.width,
            "year_min": year_min, "year_max": year_max,
            "null_count_total": null_total,
            "source_path": str(path), "status": "OK",
            "columns": df.columns,
        }
    except Exception as exc:
        logger.error(f"FAILED {path.name}: {exc}")
        return {
            "table_name": path.stem, "domain": domain,
            "row_count": None, "col_count": None,
            "year_min": None, "year_max": None,
            "null_count_total": None,
            "source_path": str(path), "status": f"ERROR: {exc}",
            "columns": [],
        }


all_files = [(f, "mortality") for f in MORTALITY_FILES]
if POPULATION_FILE.exists():
    all_files.append((POPULATION_FILE, "population"))

profiles = [profile_csv(f, d) for f, d in all_files]

# Summary
for p in profiles:
    logger.info(f"  {p['table_name']}: {p['row_count']} rows | {p['year_min']}-{p['year_max']} | cols={p['columns']}")

# Profile CSV
profile_df = pl.DataFrame({
    "table_name": [p["table_name"] for p in profiles],
    "domain": [p["domain"] for p in profiles],
    "row_count": [p["row_count"] for p in profiles],
    "col_count": [p["col_count"] for p in profiles],
    "year_min": [p["year_min"] for p in profiles],
    "year_max": [p["year_max"] for p in profiles],
    "null_count_total": [p["null_count_total"] for p in profiles],
    "source_path": [p["source_path"] for p in profiles],
})
PROFILE_PATH = RESULTS / "ps002_data_profile.csv"
profile_df.write_csv(str(PROFILE_PATH))
logger.info(f"Profile CSV → {PROFILE_PATH}")
print(profile_df)

# Quality gate
failed = [p["table_name"] for p in profiles if p["status"] != "OK" or (p["row_count"] or 0) == 0]
gate = "FAILED" if failed else "PASSED"

# Notebook
NB_PATH = NB_DIR / "01_data_extraction.ipynb"
cells_src = [
    f"# PS-002 Healthcare Demand Forecasting — Data Extraction\nimport polars as pl\nfrom pathlib import Path\nWS = Path('{WS}')\nMORTALITY_RAW = WS / 'shared/data/1_raw/mortality'\nWORKFORCE_RAW = WS / 'shared/data/1_raw/workforce'\nPS_DIR = WS / 'problem-statements/ps-002-healthcare-demand-forecasting'\nprint('Paths set')",
    "mortality_files = sorted(MORTALITY_RAW.glob('*.csv'))\npop_file = WORKFORCE_RAW / 'singapore-population-by-age.csv'\nprint('Mortality/Admission files:', [f.name for f in mortality_files])\nprint('Population file exists:', pop_file.exists())",
    "# Load and inspect each mortality/admission file\nfor f in mortality_files:\n    df = pl.read_csv(str(f), infer_schema_length=10000)\n    print(f'\\n{f.name}: {df.shape}')\n    print(df.head(3))",
    "# Load population\npop = pl.read_csv(str(pop_file))\nprint('Population:', pop.shape)\nprint(pop.head(5))",
    "# Profile summary\nprofile = pl.read_csv(str(PS_DIR / 'results/tables/ps002_data_profile.csv'))\nprint(profile)",
]
nb = nbformat.v4.new_notebook()
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}
nbformat.write(nb, str(NB_PATH))

# Handoff JSON
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
NOW = datetime.now(timezone.utc).isoformat()
handoff = {
    "agent": "data-extractor",
    "problem_statement": "ps-002-healthcare-demand-forecasting",
    "status": "success" if not failed else "failed",
    "timestamp": NOW,
    "outputs": [
        {"path": str(PROFILE_PATH), "type": "csv", "description": "Data profile summary"},
        {"path": str(NB_PATH), "type": "notebook", "description": "Extraction notebook"},
    ],
    "source_files": [str(f) for f, _ in all_files],
    "extraction_summary": {
        "total_files": len(profiles),
        "total_rows": sum(p["row_count"] or 0 for p in profiles),
        "mortality_files": len(MORTALITY_FILES),
        "date_range": {
            "start": str(min((p["year_min"] for p in profiles if p["year_min"]), default="unknown")),
            "end": str(max((p["year_max"] for p in profiles if p["year_max"]), default="unknown")),
        },
    },
    "validation_results": {"overall_status": gate, "blocking_issues": failed},
    "dataset_descriptions": {
        "age-standardised-mortality-rate-for-cancer": "Annual age-standardised cancer mortality rates by sex/cause",
        "age-standardised-mortality-rate-for-ischaemic-heart-disease": "Annual IHD mortality rates",
        "age-standardised-mortality-rate-for-stroke": "Annual stroke mortality rates",
        "hospital-admission-rate-by-age-and-sex": "Hospital admission rates by age group and sex",
        "vaccination-and-immunisation-of-students-annual": "Annual student vaccination rates",
        "singapore-population-by-age": "Annual Singapore population by 5-year age band",
    },
    "recommended_cleaning_steps": [
        "Standardise column names to snake_case",
        "Cast year to Int32",
        "Filter to consistent analysis window (1990–2019 for mortality; 2006–2019 for admissions)",
        "Exclude 2020 data due to COVID-19 structural break",
        "Cast numeric value columns from String where needed",
    ],
    "notes": f"{len(profiles)} datasets profiled. Gate: {gate}.",
}
HANDOFF_PATH = HANDOFF_DIR / f"extraction_to_validation_{TODAY}.json"
HANDOFF_PATH.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff JSON → {HANDOFF_PATH}")

print(f"\n{'='*62}")
print(f"  Datasets profiled  : {len(profiles)}")
print(f"  Total rows         : {sum(p['row_count'] or 0 for p in profiles):,}")
print(f"  Quality gate       : {gate}")
print(f"  PROFILE CSV        : {PROFILE_PATH}")
print(f"  HANDOFF JSON       : {HANDOFF_PATH}")
print(f"  NOTEBOOK           : {NB_PATH}")
print(f"{'='*62}")
