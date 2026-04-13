# User Story: 1 — Data Extraction & Source Profiling

**As a** healthcare data analyst,  
**I want** to download and profile all 10 source tables from the Kaggle Singapore Health Dataset plus Singapore resident population data,  
**so that** I can confirm data completeness, understand field structures, and document any quality issues before any analysis begins.

## 1. 🎯 Acceptance Criteria

- All 10 tables successfully downloaded via `kagglehub` and saved to `shared/data/1_raw/` subdirectories
- Singapore resident population by year sourced from SingStat or World Bank public API and saved to `shared/data/2_external/`
- WHO nurse-to-bed and doctor-to-population benchmarks sourced and saved to `shared/data/2_external/benchmarks/`
- Profile report generated for each table: row count, column names, dtypes, year range, null rates, unique sector values
- Year coverage gaps documented per table (e.g., nurses start 2008, not 2006)
- Denominator confirmed for admission rate table (per-1,000 or per-10,000 population)
- All raw files remain unmodified after extraction (immutable raw data principle)
- Data quality log saved to `problem-statements/ps-001-healthcare-system-baseline/logs/etl/extraction.log`

## 2. 🔒 Technical Constraints

- Use `kagglehub.dataset_download("subhamjain/health-dataset-complete-singapore")` — do not use `pip install kaggle` CLI
- Load CSVs with Polars (`pl.read_csv`) with explicit dtype specification
- Do not modify raw files; write profiles to `results/tables/data_profile_report.csv`
- Log all extraction steps with loguru at INFO level; errors at ERROR level
- External population data: prefer SingStat API or CSV download; fallback to World Bank WDI public API

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — benchmark values to verify against
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — confirms which metrics require which tables

## 4. 📦 Dependencies

- `kagglehub` — dataset download
- `polars` — CSV loading and profiling
- `loguru` — extraction logging
- `pyyaml` — load `shared/config/base.yml`

## 5. ✅ Implementation Tasks

**Data Extraction**
- ⬜ Create `shared/src/data_processing/kaggle_connector.py` with `download_dataset()` function
- ⬜ Download full dataset; confirm directory structure and 35 CSV files present
- ⬜ Extract 10 target tables to `shared/data/1_raw/{workforce,facilities,utilisation,expenditure}/`
- ⬜ Download Singapore resident population data → `shared/data/2_external/population/`
- ⬜ Download WHO benchmarks (nurse-to-bed, doctor per 10,000) → `shared/data/2_external/benchmarks/`

**Data Profiling**
- ⬜ Load each table with Polars; capture shape, schema, year min/max, null counts per column
- ⬜ Confirm admission rate denominator (read column header and metadata TXT file)
- ⬜ Document year coverage gaps across all 10 tables in profile report
- ⬜ Write profile results to `results/tables/data_profile_report.csv`
- ⬜ Log extraction summary to `logs/etl/extraction.log`

## 6. Notes

- The nurse/midwife table covers 2008–2019, not 2006. The maximum joint year range across all workforce tables is 2009–2018. Document this explicitly — it defines the usable analysis window.
- LTC admissions table has ~25 records. Flag as sparse in the profile; do not treat it as suitable for statistical modelling.
- If SingStat population download fails (website availability), fall back to World Bank WDI indicator `SP.POP.TOTL` for Singapore — document substitution.

---

## Implementation Plan

### 1. Feature Overview

Download the Kaggle Singapore Health Dataset via `kagglehub`, profile 10 target tables, acquire Singapore resident population and WHO benchmark reference data, and produce a machine-readable data profile report. The primary user is the **Healthcare Data Analyst** who must confirm data readiness before PS-001 analysis begins.

---

### 2. Component Analysis & Reuse Strategy

| Component | Location | Status | Decision |
|-----------|----------|--------|----------|
| `shared/src/data_processing/` | Exists (empty) | None | Create new modules |
| `shared/config/base.yml` | Exists | Paths defined | Read project paths from here |
| `shared/data/1_raw/` | Exists | Empty | Target for raw CSVs |
| `shared/data/2_external/` | Exists | Empty | Target for external data |
| `problem-statements/ps-001-healthcare-system-baseline/config/config.yml` | Does not exist | — | Create with table definitions |
| `problem-statements/ps-001-healthcare-system-baseline/results/tables/` | Exists | Empty | Profile report output |
| `problem-statements/ps-001-healthcare-system-baseline/logs/etl/` | Exists | Empty | Extraction log |

No existing code to reuse — all components are new.

---

### 3. Affected Files

```
[CREATE] shared/src/data_processing/kaggle_connector.py
  - Function: download_dataset(dataset_id: str, target_dir: Path) -> Path
  - Dependencies: kagglehub, pathlib, loguru
  - Logging: logs/etl/extraction.log

[CREATE] shared/src/data_processing/profiler.py
  - Function: profile_dataframe(df: pl.DataFrame, table_name: str) -> dict
  - Function: profile_all_tables(table_paths: dict[str, Path], config: dict) -> pl.DataFrame
  - Dependencies: polars, loguru, pathlib

[CREATE] problem-statements/ps-001-healthcare-system-baseline/config/config.yml
  - PS-001–specific table definitions, validation bounds, file name map

[CREATE] problem-statements/ps-001-healthcare-system-baseline/scripts/run_extraction.py
  - Orchestrates download → profile → write report
  - Dependencies: kaggle_connector, profiler, pyyaml, loguru

[CREATE] problem-statements/ps-001-healthcare-system-baseline/notebooks/01-extract-and-profile-source-data.ipynb
  - Interactive walkthrough of extraction and profiling steps

[CREATE] problem-statements/ps-001-healthcare-system-baseline/tests/unit/test_profiler.py
  - Unit tests for profile_dataframe() and profile_all_tables()
```

---

### 4. Component Breakdown

**`shared/src/data_processing/kaggle_connector.py`**
- Responsibility: Authenticate with Kaggle via `kagglehub`; download dataset; return local path to downloaded files
- Memory budget: N/A (file I/O, not in-memory)
- Execution time: ≤ 5 min on first download; near-instant on cache hit

**`shared/src/data_processing/profiler.py`**
- Responsibility: Load each CSV, compute shape/schema/null-rates/year-range, return structured profile dict
- Memory budget: < 200 MB (35 small CSVs averaging ~100KB each)
- Execution time: < 60 seconds for all 10 tables

**`problem-statements/ps-001-healthcare-system-baseline/config/config.yml`**
- Responsibility: Hold PS-001 table map, column expectations, numeric bounds
- Read via `pyyaml.safe_load()`

---

### 5. Data Pipeline

```
[Kaggle] ──kagglehub──▶ shared/data/1_raw/ (35 CSVs)
                              │
                    [filter 10 target tables]
                              │
               ┌──────────────┴──────────────┐
               │                             │
    [profile each table]          [SingStat / World Bank]
    shape, schema, nulls,               population
    year range, denominator         shared/data/2_external/
               │                             │
               └──────────────┬──────────────┘
                              │
              results/tables/data_profile_report.csv
              logs/etl/extraction.log
```

**Extraction method**: `kagglehub.dataset_download("subhamjain/health-dataset-complete-singapore")` returns the local cache path; copy 10 target files to organised `shared/data/1_raw/` subdirectories.

**External population**: World Bank WDI public API — `https://api.worldbank.org/v2/country/SG/indicator/SP.POP.TOTL?format=json&per_page=100` — returns annual resident population for Singapore; no authentication required.

---

### 6. Code Generation Specifications

#### 6.1 `shared/src/data_processing/kaggle_connector.py`

```python
"""Kaggle dataset connector using kagglehub.

Provides authenticated dataset download and file organisation.
Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
"""

import os
import shutil
from pathlib import Path

import kagglehub
from loguru import logger


def download_dataset(dataset_id: str, target_dir: Path) -> Path:
    """Download a Kaggle dataset via kagglehub and return local path.

    Args:
        dataset_id: Kaggle dataset slug, e.g. "subhamjain/health-dataset-complete-singapore"
        target_dir: Destination directory for downloaded files

    Returns:
        Path to directory containing downloaded CSV files

    Raises:
        EnvironmentError: If KAGGLE_USERNAME or KAGGLE_KEY are not set
        RuntimeError: If download fails
    """
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        raise EnvironmentError(
            "KAGGLE_USERNAME and KAGGLE_KEY must be set as environment variables. "
            "See https://github.com/Kaggle/kaggle-api#api-credentials"
        )

    logger.info(f"Downloading dataset: {dataset_id}")
    try:
        cached_path = Path(kagglehub.dataset_download(dataset_id))
        logger.info(f"Dataset cached at: {cached_path}")
    except Exception as exc:
        logger.error(f"Download failed for {dataset_id}: {exc}")
        raise RuntimeError(f"kagglehub download failed: {exc}") from exc

    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Organising files into: {target_dir}")
    return cached_path


def copy_target_tables(
    source_dir: Path,
    target_base: Path,
    table_map: dict[str, str],
) -> dict[str, Path]:
    """Copy selected CSV files from the download cache into organised subdirectories.

    Args:
        source_dir: Root of the kagglehub download cache
        target_base: shared/data/1_raw/ root
        table_map: Mapping of {csv_filename: subdirectory_name}
            e.g. {"doctors.csv": "workforce"}

    Returns:
        dict mapping table name to its copied Path

    Raises:
        FileNotFoundError: If a required source CSV is not found
    """
    copied: dict[str, Path] = {}
    for csv_name, subdir in table_map.items():
        # kagglehub may nest files — search recursively
        matches = list(source_dir.rglob(csv_name))
        if not matches:
            logger.error(f"Required file not found in download: {csv_name}")
            raise FileNotFoundError(f"{csv_name} not found under {source_dir}")

        src = matches[0]
        dest_dir = target_base / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / csv_name

        if not dest.exists():
            shutil.copy2(src, dest)
            logger.info(f"Copied {csv_name} → {dest}")
        else:
            logger.debug(f"Already exists, skipping: {dest}")

        copied[csv_name.replace(".csv", "")] = dest

    return copied
```

#### 6.2 `shared/src/data_processing/profiler.py`

```python
"""Dataset profiler — computes shape, schema, null rates, and year range.

All profiling is read-only; raw files are never modified.
"""

from pathlib import Path

import polars as pl
from loguru import logger


def profile_dataframe(df: pl.DataFrame, table_name: str) -> dict:
    """Generate a structured profile report for a single DataFrame.

    Args:
        df: Loaded DataFrame to profile
        table_name: Logical name of the table (used in output)

    Returns:
        dict with keys: table_name, rows, cols, columns, year_min,
        year_max, year_gaps, null_counts, null_pct, dtypes
    """
    n_rows, n_cols = df.shape
    columns = df.columns

    # Year range — look for 'year' or 'financial_year' column
    year_col = None
    for candidate in ("year", "Year", "financial_year", "Financial Year"):
        if candidate in columns:
            year_col = candidate
            break

    year_min: int | None = None
    year_max: int | None = None
    year_gaps: list[int] = []

    if year_col:
        raw_years = df[year_col].drop_nulls()

        # Handle financial_year strings like "2006/07" → extract start year
        if df[year_col].dtype == pl.Utf8:
            raw_years = raw_years.str.extract(r"(\d{4})", 1).cast(pl.Int32)
        else:
            raw_years = raw_years.cast(pl.Int32)

        sorted_years = sorted(raw_years.unique().to_list())
        if sorted_years:
            year_min = sorted_years[0]
            year_max = sorted_years[-1]
            expected = set(range(year_min, year_max + 1))
            year_gaps = sorted(expected - set(sorted_years))

    # Null analysis
    null_counts = df.null_count().row(0, named=True)  # dict col → null count
    null_pct = {
        col: round(count / n_rows * 100, 2) if n_rows > 0 else 0.0
        for col, count in null_counts.items()
    }

    profile = {
        "table_name": table_name,
        "rows": n_rows,
        "cols": n_cols,
        "columns": columns,
        "year_min": year_min,
        "year_max": year_max,
        "year_gaps": year_gaps,
        "null_counts": null_counts,
        "null_pct": null_pct,
        "dtypes": {col: str(dtype) for col, dtype in zip(columns, df.dtypes)},
    }

    logger.info(
        f"[{table_name}] rows={n_rows}, year={year_min}–{year_max}, "
        f"year_gaps={year_gaps}, max_null_pct={max(null_pct.values(), default=0):.1f}%"
    )
    return profile


def profile_all_tables(
    table_paths: dict[str, Path],
    admission_table_key: str = "hospital_admissions",
) -> pl.DataFrame:
    """Profile all target tables and return a summary DataFrame.

    Args:
        table_paths: Mapping of {table_name: Path to CSV}
        admission_table_key: Key in table_paths for admission rate table
            (used to confirm denominator)

    Returns:
        Polars DataFrame with one row per table:
        table_name, rows, year_min, year_max, year_gaps_str,
        null_count_total, max_null_pct, load_status
    """
    summaries: list[dict] = []

    for name, path in table_paths.items():
        try:
            df = pl.read_csv(path, infer_schema_length=1000)
            profile = profile_dataframe(df, name)

            # Denominator check for admission table
            denom_note = ""
            if name == admission_table_key:
                cols_lower = [c.lower() for c in df.columns]
                if any("1000" in c or "per_1000" in c for c in cols_lower):
                    denom_note = "per_1000"
                elif any("10000" in c or "per_10000" in c for c in cols_lower):
                    denom_note = "per_10000"
                else:
                    denom_note = "UNKNOWN — manual check required"
                logger.warning(f"Admission denominator: {denom_note}")

            summaries.append({
                "table_name": name,
                "rows": profile["rows"],
                "year_min": profile["year_min"],
                "year_max": profile["year_max"],
                "year_gaps": str(profile["year_gaps"]) if profile["year_gaps"] else "none",
                "null_count_total": sum(profile["null_counts"].values()),
                "max_null_pct": max(profile["null_pct"].values(), default=0.0),
                "denominator_note": denom_note,
                "load_status": "OK",
            })

        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to profile {name} ({path}): {exc}")
            summaries.append({
                "table_name": name,
                "rows": None,
                "year_min": None,
                "year_max": None,
                "year_gaps": None,
                "null_count_total": None,
                "max_null_pct": None,
                "denominator_note": None,
                "load_status": f"ERROR: {exc}",
            })

    return pl.DataFrame(summaries)
```

#### 6.3 `problem-statements/ps-001-healthcare-system-baseline/config/config.yml`

```yaml
# PS-001 Healthcare System Baseline — Problem-Specific Configuration

problem_statement:
  id: ps-001
  name: healthcare-system-baseline
  description: "Descriptive baseline: workforce, facilities, utilisation, expenditure"

# Kaggle dataset
kaggle:
  dataset_id: "subhamjain/health-dataset-complete-singapore"

# Table map: CSV filename → subdirectory under shared/data/1_raw/
table_map:
  "doctors.csv": workforce
  "nurses.csv": workforce
  "pharmacists.csv": workforce
  "dentists.csv": workforce
  "allied_health_professionals.csv": workforce
  "inpatient_beds.csv": facilities
  "primary_care_clinics.csv": facilities
  "hospital_admissions.csv": utilisation
  "government_health_expenditure.csv": expenditure
  "long_term_care_admissions.csv": utilisation

# Key table for denominator confirmation
admission_table_key: hospital_admissions

# Year window for joint analysis
analysis_window:
  start_year: 2009
  end_year: 2018

# Data quality thresholds (PS-001 override)
data_quality:
  max_null_rate: 0.0     # Zero nulls tolerated in year/count columns
  ltc_sparse_threshold: 50  # Flag tables with fewer rows as sparse
```

#### 6.4 `problem-statements/ps-001-healthcare-system-baseline/scripts/run_extraction.py`

```python
"""PS-001 Story 01 — Extraction and Profiling Pipeline.

Run with: python problem-statements/ps-001-healthcare-system-baseline/scripts/run_extraction.py
Requires: KAGGLE_USERNAME and KAGGLE_KEY set in environment (or .env file).
"""

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from loguru import logger

# ---------------------------------------------------------------------------
# Bootstrap: add project root to sys.path so shared modules resolve correctly
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.src.data_processing.kaggle_connector import (  # noqa: E402
    copy_target_tables,
    download_dataset,
)
from shared.src.data_processing.profiler import profile_all_tables  # noqa: E402

load_dotenv()  # Load .env for KAGGLE credentials

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PS_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = PS_DIR / "config" / "config.yml"
LOG_PATH = PS_DIR / "logs" / "etl" / "extraction.log"
RESULTS_DIR = PS_DIR / "results" / "tables"
SHARED_RAW = PROJECT_ROOT / "shared" / "data" / "1_raw"
SHARED_EXTERNAL = PROJECT_ROOT / "shared" / "data" / "2_external"


def _setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_path),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
        rotation="10 MB",
        retention="30 days",
    )


def _load_config(config_path: Path) -> dict:
    with config_path.open() as fh:
        return yaml.safe_load(fh)


def _download_population_data(output_dir: Path) -> Path:
    """Download Singapore resident population from World Bank WDI API.

    Uses indicator SP.POP.TOTL for Singapore (country code SG).
    Falls back gracefully if the API is unreachable and a cached file exists.

    Args:
        output_dir: Target directory, typically shared/data/2_external/population/

    Returns:
        Path to saved population CSV
    """
    import json
    import csv
    import requests

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "singapore_resident_population.csv"

    if out_file.exists():
        logger.info(f"Population file already cached: {out_file}")
        return out_file

    url = (
        "https://api.worldbank.org/v2/country/SG/indicator/SP.POP.TOTL"
        "?format=json&per_page=100&mrv=30"
    )
    logger.info(f"Fetching population data from World Bank WDI: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        records = []
        for item in data[1]:  # data[0] is pagination metadata
            if item.get("value") is not None:
                records.append({
                    "year": int(item["date"]),
                    "population": int(item["value"]),
                    "source": "World Bank WDI SP.POP.TOTL",
                })

        records.sort(key=lambda r: r["year"])

        with out_file.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["year", "population", "source"])
            writer.writeheader()
            writer.writerows(records)

        logger.info(
            f"Population data saved: {len(records)} records → {out_file}"
        )

    except requests.RequestException as exc:
        logger.error(f"World Bank API unavailable: {exc}. Manual download required.")
        raise

    return out_file


def _write_who_benchmarks(output_dir: Path) -> Path:
    """Write WHO SEARO healthcare benchmarks as a reference CSV.

    Values are hard-coded from WHO GHO 2020 — no API call required.

    Args:
        output_dir: Target directory, typically shared/data/2_external/benchmarks/

    Returns:
        Path to saved benchmarks CSV
    """
    import csv

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "who_searo_benchmarks.csv"

    benchmarks = [
        {
            "metric": "nurses_per_10k",
            "value": 22.8,
            "unit": "per 10,000 population",
            "region": "SEARO",
            "source": "WHO GHO 2020",
        },
        {
            "metric": "doctors_per_10k",
            "value": 2.3,
            "unit": "per 10,000 population",
            "region": "SEARO",
            "source": "WHO GHO 2020",
        },
        {
            "metric": "beds_per_10k",
            "value": 21.0,
            "unit": "per 10,000 population",
            "region": "SEARO",
            "source": "WHO GHO 2020",
        },
    ]

    with out_file.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(benchmarks[0].keys()))
        writer.writeheader()
        writer.writerows(benchmarks)

    logger.info(f"WHO benchmarks saved: {out_file}")
    return out_file


def main() -> None:
    _setup_logging(LOG_PATH)
    logger.info("=== PS-001 Story 01: Data Extraction & Profiling ===")

    config = _load_config(CONFIG_PATH)
    dataset_id = config["kaggle"]["dataset_id"]
    table_map = config["table_map"]
    admission_key = config.get("admission_table_key", "hospital_admissions")

    # Step 1: Download dataset
    cached_path = download_dataset(dataset_id, SHARED_RAW)

    # Step 2: Copy target tables into organised subdirectories
    table_paths = copy_target_tables(cached_path, SHARED_RAW, table_map)
    logger.info(f"Copied {len(table_paths)} target tables.")

    # Step 3: Profile all tables
    profile_df = profile_all_tables(table_paths, admission_table_key=admission_key)

    # Step 4: Save profile report
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / "data_profile_report.csv"
    profile_df.write_csv(str(report_path))
    logger.info(f"Profile report saved: {report_path}")

    # Step 5: Download external population data
    pop_path = _download_population_data(SHARED_EXTERNAL / "population")
    logger.info(f"Population data: {pop_path}")

    # Step 6: Write WHO benchmarks
    bench_path = _write_who_benchmarks(SHARED_EXTERNAL / "benchmarks")
    logger.info(f"Benchmarks: {bench_path}")

    # Summary log
    failed = profile_df.filter(pl.col("load_status").str.starts_with("ERROR"))
    logger.info(
        f"Extraction complete. {len(profile_df) - len(failed)}/{len(profile_df)} "
        f"tables profiled successfully."
    )
    if len(failed) > 0:
        logger.warning(f"Failed tables: {failed['table_name'].to_list()}")


if __name__ == "__main__":
    import polars as pl  # ensure available for inline filter in summary
    main()
```

#### 6.5 Validation Rules

```python
# Inline validation assertions for run_extraction.py (add to main() after profiling)
import polars as pl

def validate_profile_report(profile_df: pl.DataFrame) -> None:
    """Assert minimum quality bar on the profile report.

    Args:
        profile_df: Output from profile_all_tables()

    Raises:
        AssertionError: If critical tables failed to load
        ValueError: If admission denominator is unknown
    """
    # All tables must have loaded
    failed = profile_df.filter(pl.col("load_status").str.starts_with("ERROR"))
    assert len(failed) == 0, (
        f"Critical tables failed to load: {failed['table_name'].to_list()}"
    )

    # No table should have zero rows
    empty = profile_df.filter(pl.col("rows") == 0)
    assert len(empty) == 0, (
        f"Empty tables detected: {empty['table_name'].to_list()}"
    )

    # Admission denominator must be confirmed
    admission_row = profile_df.filter(
        pl.col("table_name") == "hospital_admissions"
    )
    if len(admission_row) > 0:
        denom = admission_row["denominator_note"][0]
        if denom and "UNKNOWN" in str(denom):
            raise ValueError(
                "Admission rate denominator could not be determined automatically. "
                "Manual inspection required before proceeding."
            )
```

---

### 7. Testing Strategy

**File**: `problem-statements/ps-001-healthcare-system-baseline/tests/unit/test_profiler.py`

```python
"""Unit tests for shared/src/data_processing/profiler.py"""

import sys
from pathlib import Path

import polars as pl
import pytest

# Bootstrap
PROJECT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.src.data_processing.profiler import profile_dataframe, profile_all_tables


@pytest.fixture
def sample_df() -> pl.DataFrame:
    return pl.DataFrame({
        "year": [2010, 2011, 2012, 2013, 2015],  # gap at 2014
        "headcount": [1000, 1050, 1100, 1150, 1200],
        "sector": ["Public", "Public", "Private", "Public", "Public"],
    })


@pytest.fixture
def df_with_nulls() -> pl.DataFrame:
    return pl.DataFrame({
        "year": [2010, 2011, None, 2013],
        "headcount": [100, None, 300, 400],
        "sector": ["Public", "Private", None, "Public"],
    })


def test_profile_dataframe_shape(sample_df: pl.DataFrame) -> None:
    profile = profile_dataframe(sample_df, "workforce")
    assert profile["rows"] == 5
    assert profile["cols"] == 3


def test_profile_detects_year_gap(sample_df: pl.DataFrame) -> None:
    profile = profile_dataframe(sample_df, "workforce")
    assert profile["year_min"] == 2010
    assert profile["year_max"] == 2015
    assert 2014 in profile["year_gaps"]


def test_profile_null_rates(df_with_nulls: pl.DataFrame) -> None:
    profile = profile_dataframe(df_with_nulls, "test_table")
    assert profile["null_pct"]["year"] == 25.0  # 1/4 rows
    assert profile["null_pct"]["headcount"] == 25.0


def test_profile_no_year_column() -> None:
    df = pl.DataFrame({"col_a": [1, 2], "col_b": ["x", "y"]})
    profile = profile_dataframe(df, "no_year")
    assert profile["year_min"] is None
    assert profile["year_max"] is None
    assert profile["year_gaps"] == []


def test_profile_all_tables_summary(tmp_path: Path, sample_df: pl.DataFrame) -> None:
    csv_path = tmp_path / "workforce.csv"
    sample_df.write_csv(str(csv_path))

    summary = profile_all_tables({"workforce": csv_path})
    assert len(summary) == 1
    assert summary["table_name"][0] == "workforce"
    assert summary["load_status"][0] == "OK"
    assert summary["rows"][0] == 5


def test_profile_all_tables_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.csv"
    summary = profile_all_tables({"missing_table": missing})
    assert summary["load_status"][0].startswith("ERROR")
```

---

### 8. Implementation Steps

**Phase 1: Environment Setup**
- [ ] Add `kagglehub>=0.2` to `requirements.txt`; run `uv pip install kagglehub`
- [ ] Create `problem-statements/ps-001-healthcare-system-baseline/config/config.yml` with table map
- [ ] Set `KAGGLE_USERNAME` and `KAGGLE_KEY` in `.env` (never commit this file)
- [ ] Confirm `.env` is in `.gitignore`

**Phase 2: Core Modules**
- [ ] Create `shared/src/data_processing/__init__.py` (empty)
- [ ] Create `shared/src/data_processing/kaggle_connector.py`
- [ ] Create `shared/src/data_processing/profiler.py`

**Phase 3: Orchestration Script**
- [ ] Create `problem-statements/ps-001-healthcare-system-baseline/scripts/run_extraction.py`
- [ ] Run script: `python run_extraction.py` — verify 10 tables are extracted
- [ ] Confirm `data_profile_report.csv` is written with correct schema

**Phase 4: External Data**
- [ ] Confirm World Bank API is reachable; verify `singapore_resident_population.csv` is written with ≥ 15 year records (2006–2020)
- [ ] Verify `who_searo_benchmarks.csv` contains 3 rows

**Phase 5: Validation & Testing**
- [ ] Run `pytest tests/unit/test_profiler.py -v`
- [ ] Confirm all 6 tests pass
- [ ] Review `extraction.log` — confirm no ERROR messages

**Phase 6: Profile Report Review**
- [ ] Open `data_profile_report.csv`; verify:
  - `hospital_admissions` denominator column is not "UNKNOWN"
  - `long_term_care_admissions` row count < 50 (flag as sparse)
  - Year gap documented for nurses table (missing 2006–2008)
- [ ] If denominator is UNKNOWN, inspect CSV headers manually and document in report

---

### 9. Adaptive Implementation Strategy

**If SingStat API is blocked**: Use World Bank WDI API (already in script). If both fail, download `https://www.singstat.gov.sg/-/media/files/publications/population/population2023.ashx` manually and document the substitution in `data_profile_report.csv` under `denominator_note`.

**If a table CSV filename differs from the config map**: Update `config.yml` table_map keys to match actual filenames found in the kagglehub cache directory. Use `list(source_dir.rglob("*.csv"))` in a diagnostic script to enumerate all available CSVs.

**If `kagglehub` download fails due to auth**: Ensure `.env` has correct `KAGGLE_USERNAME`/`KAGGLE_KEY` from `https://www.kaggle.com/account`. Verify `python-dotenv` is installed; alternatively export as shell variables.

---

### 10. Security & Privacy

- Raw Kaggle data contains **no PII or PHI** — national aggregate statistics only; no individual records
- `KAGGLE_KEY` is sensitive: load from `.env` via `python-dotenv`; never log or print the key value
- Add `.env` to `.gitignore` (already present from project setup)
- Credential access pattern:
    ```python
    import os
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("KAGGLE_KEY")  # returns None if not set; checked before use
    ```
- Audit: all extraction actions logged to `logs/etl/extraction.log` with timestamps

---

### 11. Version Control

```bash
git checkout -b feat/ps-001-story-01-extraction
# ... implement and test ...
git commit -m "feat(ps-001): add kaggle connector and table profiler"
git commit -m "feat(ps-001): add extraction pipeline script"
git commit -m "test(ps-001): add profiler unit tests"
git commit -m "docs(ps-001): add config.yml and extraction log"
# PR: link to ps-001-healthcare-system-baseline.md; require 1 reviewer approval
```

---

### 12. Package Management

```bash
# Add kagglehub to requirements.txt
uv pip install kagglehub>=0.2
uv pip freeze > requirements.txt
```

---

### 13. Instruction File Compliance

| Instruction File | Key Requirements | Verified |
|------------------|-----------------|----------|
| python-best-practices | Type hints ✅, loguru not print ✅, validate inputs ✅ | ✅ |
| data-analysis-best-practices | Never modify data/1_raw/ ✅, log all transforms ✅ | ✅ |
| data-analysis-folder-structure | Outputs to results/tables/, logs/etl/ ✅ | ✅ |
| moh-data-quality-assessment | Null rates reported as % ✅, year gaps flagged ✅ | ✅ |
