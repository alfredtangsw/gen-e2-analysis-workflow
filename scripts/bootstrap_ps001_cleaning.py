"""PS-001 Phase 2b: Data Cleaning — standardise, cast, filter, dedup, write parquets."""
import sys, json, re
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
from loguru import logger
import nbformat

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
RAW_WF = WS / "shared/data/1_raw/workforce"
RAW_MO = WS / "shared/data/1_raw/mortality"
PS_DIR = WS / "problem-statements/ps-001-healthcare-system-baseline"
INTERIM = PS_DIR / "data/3_interim"
RESULTS = PS_DIR / "results/tables"
LOGS = PS_DIR / "logs/etl"
HANDOFF_DIR = WS / "docs/agent-handoffs/data-cleaning/ps-001-healthcare-system-baseline"
NB_DIR = PS_DIR / "notebooks"
for d in [INTERIM, RESULTS, LOGS, HANDOFF_DIR, NB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"cleaning_{TS}.log"), level="DEBUG")
logger.info("PS-001 data cleaning started")

YEAR_MIN, YEAR_MAX = 2006, 2021
log_rows = []


def to_snake(name: str) -> str:
    """Convert column name to snake_case."""
    name = re.sub(r"[\s\-]+", "_", name.strip().lower())
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name


def try_cast_numeric(df: pl.DataFrame, col: str) -> pl.DataFrame:
    """Try to cast a String column to Float64 by stripping commas/spaces."""
    if df[col].dtype == pl.Utf8:
        try:
            cleaned = df.with_columns(
                pl.col(col).str.replace_all(",", "").str.strip_chars()
            )
            cast_attempt = cleaned.with_columns(
                pl.col(col).cast(pl.Float64, strict=False)
            )
            null_before = df[col].null_count()
            null_after = cast_attempt[col].null_count()
            if null_after <= null_before + 5:  # allow up to 5 new nulls from parsing
                return cast_attempt
        except Exception:
            pass
    return df


def clean_csv(path: Path, domain: str) -> dict:
    name = path.stem
    logger.info(f"--- cleaning {domain}/{path.name} ---")
    df = pl.read_csv(str(path), infer_schema_length=10000, truncate_ragged_lines=True)
    rows_before = df.height
    nulls_before = sum(df[c].null_count() for c in df.columns)

    transformations = []

    # 1. Standardise column names to snake_case
    rename_map = {c: to_snake(c) for c in df.columns}
    df = df.rename(rename_map)
    transformations.append("snake_case_columns")

    # 2. Trim whitespace from all string columns
    str_cols = [c for c in df.columns if df[c].dtype == pl.Utf8]
    if str_cols:
        df = df.with_columns([pl.col(c).str.strip_chars() for c in str_cols])
        transformations.append("strip_whitespace")

    # 3. Find and standardise year column → cast to Int32
    year_c = next((c for c in df.columns if "year" in c.lower()), None)
    if year_c and year_c != "year":
        df = df.rename({year_c: "year"})
    if "year" in df.columns:
        df = df.with_columns(pl.col("year").cast(pl.Int32, strict=False))
        transformations.append("cast_year_to_int32")
        # 4. Filter to analysis window
        df = df.filter(pl.col("year").is_between(YEAR_MIN, YEAR_MAX))
        transformations.append(f"filter_year_{YEAR_MIN}_{YEAR_MAX}")

    # 5. Try casting string numeric columns
    for c in df.columns:
        if df[c].dtype == pl.Utf8 and c != "year":
            df = try_cast_numeric(df, c)
    transformations.append("cast_numeric_strings")

    # 6. Drop exact duplicates
    before_dedup = df.height
    df = df.unique()
    if df.height < before_dedup:
        transformations.append(f"drop_{before_dedup - df.height}_duplicates")

    # 7. Drop rows where ALL non-year columns are null (beds dataset edge case)
    non_year = [c for c in df.columns if c != "year"]
    if non_year:
        df = df.filter(
            pl.any_horizontal([pl.col(c).is_not_null() for c in non_year])
        )
        transformations.append("drop_all_null_rows")

    rows_after = df.height
    nulls_after = sum(df[c].null_count() for c in df.columns)

    # Write parquet — prefix with domain to avoid name collision (same stem in workforce & mortality)
    out_path = INTERIM / f"{domain}_{name}_clean.parquet"
    df.write_parquet(str(out_path), compression="snappy")
    logger.info(f"Written: {out_path} ({rows_before}→{rows_after} rows)")

    return {
        "table_name": name, "domain": domain,
        "rows_before": rows_before, "rows_after": rows_after,
        "rows_dropped": rows_before - rows_after,
        "nulls_before": nulls_before, "nulls_after": nulls_after,
        "transformations_applied": "; ".join(transformations),
        "output_path": str(out_path),
    }


all_files = [(f, "workforce") for f in sorted(RAW_WF.glob("*.csv"))] + \
            [(f, "mortality") for f in sorted(RAW_MO.glob("*.csv"))]

results = [clean_csv(path, domain) for path, domain in all_files]

# Write cleaning log CSV
log_df = pl.DataFrame({k: [r[k] for r in results] for k in
                        ["table_name", "rows_before", "rows_after", "rows_dropped",
                         "nulls_before", "nulls_after", "transformations_applied"]})
log_path = RESULTS / "ps001_cleaning_log.csv"
log_df.write_csv(str(log_path))
logger.info(f"Cleaning log → {log_path}")
print(log_df)

# Notebook
NB_PATH = NB_DIR / "03_data_cleaning.ipynb"
nb = nbformat.v4.new_notebook()
cells_src = [
    "import polars as pl\nfrom pathlib import Path\nWS = Path('/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow')\nINTERIM = WS/'problem-statements/ps-001-healthcare-system-baseline/data/3_interim'\nprint('Paths set')",
    "log = pl.read_csv(str(WS/'problem-statements/ps-001-healthcare-system-baseline/results/tables/ps001_cleaning_log.csv'))\nprint(log)",
    "# Inspect cleaned beds file\nbeds = pl.read_parquet(str(INTERIM/'health-facilities-and-beds-in-inpatient-facilities_clean.parquet'))\nprint(beds.schema)\nprint(beds.head(10))",
    "# Inspect nurses file\nnurses = pl.read_parquet(str(INTERIM/'number-of-nurses-and-midwives_clean.parquet'))\nprint(nurses.head())",
]
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}
nbformat.write(nb, str(NB_PATH))

# Handoff JSON
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
NOW = datetime.now(timezone.utc).isoformat()
outputs = [{"path": str(log_path), "type": "csv", "description": "Cleaning log"},
           {"path": str(NB_PATH), "type": "notebook", "description": "Cleaning notebook"}]
for r in results:
    outputs.append({"path": r["output_path"], "type": "parquet",
                    "description": f"Cleaned dataset: {r['table_name']}"})

handoff = {
    "agent": "data-cleaning", "problem_statement": "ps-001-healthcare-system-baseline",
    "status": "success", "timestamp": NOW,
    "outputs": outputs,
    "cleaned_parquets": [r["output_path"] for r in results],
    "cleaning_summary": {
        "total_tables": len(results),
        "total_rows_before": sum(r["rows_before"] for r in results),
        "total_rows_after":  sum(r["rows_after"] for r in results),
        "total_rows_dropped": sum(r["rows_dropped"] for r in results),
        "analysis_window": f"{YEAR_MIN}–{YEAR_MAX}",
    },
    "notes": f"{len(results)} datasets cleaned and written to {INTERIM}.",
}
HANDOFF_PATH = HANDOFF_DIR / f"cleaning_to_eda_{TODAY}.json"
HANDOFF_PATH.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff JSON → {HANDOFF_PATH}")

total_before = sum(r["rows_before"] for r in results)
total_after  = sum(r["rows_after"] for r in results)
print(f"\n{'='*60}")
print(f"  Tables cleaned   : {len(results)}")
print(f"  Rows before      : {total_before:,}")
print(f"  Rows after       : {total_after:,}")
print(f"  Rows dropped     : {total_before - total_after:,}")
print(f"  Parquets written : {INTERIM}")
print(f"  CLEANING LOG     : {log_path}")
print(f"  HANDOFF JSON     : {HANDOFF_PATH}")
print(f"{'='*60}")
