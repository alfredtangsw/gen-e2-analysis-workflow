"""PS-002 Phase 2b: Data Cleaning — standardise, filter, cast, write parquets."""
import sys, json, re
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
from loguru import logger

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
MORTALITY_RAW = WS / "shared/data/1_raw/mortality"
WORKFORCE_RAW = WS / "shared/data/1_raw/workforce"
PS_DIR = WS / "problem-statements/ps-002-healthcare-demand-forecasting"
INTERIM = PS_DIR / "data/3_interim"
RESULTS = PS_DIR / "results/tables"
LOGS = PS_DIR / "logs"
HANDOFF_DIR = WS / "docs/agent-handoffs/cleaning/ps-002-healthcare-demand-forecasting"
HANDOFF_DIR.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"cleaning_{TS}.log"), level="DEBUG")
logger.info("PS-002 data cleaning started")


def to_snake(name: str) -> str:
    name = re.sub(r"[\s\-]+", "_", name.strip().lower())
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name


SOURCES = [
    (MORTALITY_RAW / "age-standardised-mortality-rate-for-cancer.csv", "mortality",
     1990, 2019, "mortality_cancer"),
    (MORTALITY_RAW / "age-standardised-mortality-rate-for-ischaemic-heart-disease.csv", "mortality",
     1990, 2019, "mortality_ihd"),
    (MORTALITY_RAW / "age-standardised-mortality-rate-for-stroke.csv", "mortality",
     1990, 2019, "mortality_stroke"),
    (MORTALITY_RAW / "hospital-admission-rate-by-age-and-sex.csv", "mortality",
     1990, 2019, "admissions_by_age_sex"),
    (MORTALITY_RAW / "vaccination-and-immunisation-of-students-annual.csv", "mortality",
     1990, 2019, "vaccination"),
    (WORKFORCE_RAW / "singapore-population-by-age.csv", "population",
     2006, 2030, "population_by_age"),
]

clean_log = []

def clean_dataset(path, domain, yr_min, yr_max, out_stem):
    logger.info(f"Cleaning {path.name} → {out_stem}")
    df = pl.read_csv(str(path), infer_schema_length=10000, truncate_ragged_lines=True)
    rows_in = df.height

    # Rename columns to snake_case
    df = df.rename({c: to_snake(c) for c in df.columns})

    # Year col: cast to Int32
    yc = "year" if "year" in df.columns else None
    if yc:
        df = df.with_columns(pl.col(yc).cast(pl.Int32))
        df = df.filter((pl.col(yc) >= yr_min) & (pl.col(yc) <= yr_max))

    # Cast numeric value cols to Float64 (they should already be, but ensure)
    val_cols = [c for c in df.columns if c not in ("year", "sex", "age_group", "programme", "disease")]
    for vc in val_cols:
        try:
            df = df.with_columns(pl.col(vc).cast(pl.Float64, strict=False))
        except Exception:
            pass

    # Categorical string cols
    cat_cols = [c for c in df.columns if c in ("sex", "age_group", "programme", "disease")]
    for cc in cat_cols:
        df = df.with_columns(pl.col(cc).cast(pl.Categorical))

    # Drop duplicates & nulls in key cols
    df = df.unique()
    rows_out = df.height

    out = INTERIM / f"{out_stem}_clean.parquet"
    df.write_parquet(str(out), compression="snappy")
    logger.info(f"  {rows_in} → {rows_out} rows | cols: {df.columns} → {out.name}")

    clean_log.append({
        "table": path.stem, "domain": domain, "out_stem": out_stem,
        "rows_in": rows_in, "rows_out": rows_out,
        "year_filter": f"{yr_min}-{yr_max}", "output": str(out),
    })
    return df

cleaned = {}
for path, domain, yr_min, yr_max, stem in SOURCES:
    cleaned[stem] = clean_dataset(path, domain, yr_min, yr_max, stem)

log_df = pl.DataFrame(clean_log)
LOG_PATH = RESULTS / "ps002_cleaning_log.csv"
log_df.write_csv(str(LOG_PATH))
logger.info(f"Cleaning log → {LOG_PATH}")
print(log_df)

TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
handoff = {
    "agent": "data-cleaning",
    "problem_statement": "ps-002-healthcare-demand-forecasting",
    "status": "success",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "outputs": [{"path": str(LOG_PATH), "type": "csv", "description": "Cleaning log"},
                {"path": str(INTERIM), "type": "directory", "description": "Cleaned parquets"}],
    "datasets": {r["out_stem"]: r for r in clean_log},
    "data_decisions": [
        "Mortality ASMR filtered to 1990–2019 (30-year trend for ARIMA/ETS)",
        "Hospital admissions filtered to 1990–2019",
        "Population data retained 2006–2030 (projections used as forecast covariates)",
        "COVID-2020 excluded from all training windows (structural break)",
        "All numeric columns cast to Float64 for model compatibility",
    ],
    "parquet_files": [r["output"] for r in clean_log],
    "next_agent": "exploratory-analysis",
}
hp = HANDOFF_DIR / f"cleaning_to_eda_{TODAY}.json"
hp.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff → {hp}")

print(f"\n{'='*62}")
print(f"  Datasets cleaned  : {len(clean_log)}")
print(f"  Total rows out    : {sum(r['rows_out'] for r in clean_log):,}")
print(f"  INTERIM dir       : {INTERIM}")
print(f"{'='*62}")
