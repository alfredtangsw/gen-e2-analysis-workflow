# User Story: 2 — Data Validation & Cleaning

**As a** healthcare data analyst,  
**I want** to validate each source table against defined business rules and produce analysis-ready cleaned datasets,  
**so that** all downstream calculations rest on data that has been explicitly checked and corrected rather than assumed to be correct.

## 1. 🎯 Acceptance Criteria

- Each table validated for: correct column presence, expected dtypes, year within documented range, no nulls in key fields, numeric values within plausible bounds
- Sector naming inconsistencies resolved (e.g. "Public Sector" vs "Public") — unified to canonical values
- Year column standardised across all tables (some use `financial_year`, others use `year`) — aligned to a single `year: Int32` column
- Rate denominators confirmed and documented (per-1,000 or per-10,000); a `rate_base` metadata column added
- Cleaned parquet files saved to `problem-statements/ps-001-healthcare-system-baseline/data/4_processed/` with filename `{table_name}_clean.parquet`
- Data quality report saved to `results/tables/data_quality_report.csv` listing: table, field, issue type, records affected, action taken
- All cleaning steps are logged and reproducible (no manual edits to files)

## 2. 🔒 Technical Constraints

- All cleaning implemented in Polars — no pandas unless a specific operation is unavailable
- Use `pl.LazyFrame` for tables > 50,000 rows; all PS-001 tables fit in memory so eager evaluation is acceptable
- Write cleaned outputs as Parquet (`.parquet`) for downstream loading efficiency
- Validation rules defined in `config/config.yml` under a `validation:` block — not hardcoded in scripts
- Raise a `ValueError` (logged at ERROR) if critical fields (year, count/rate) contain nulls in core tables

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — plausible ranges for workforce counts (e.g. doctors: 5,000–20,000)
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — expected metric units and calculation conventions

## 4. 📦 Dependencies

- `polars` — validation and transformation
- `loguru` — logging cleaning actions
- `pyyaml` — read validation config
- Story 01 outputs: raw CSVs in `shared/data/1_raw/`

## 5. ✅ Implementation Tasks

**Validation**
- ⬜ Create `shared/src/data_processing/validator.py` with `validate_table(df, rules)` function
- ⬜ Define validation rules in `config/config.yml` (required columns, year range, numeric bounds per table)
- ⬜ Run validation on all 10 tables; write issue summary to `results/tables/data_quality_report.csv`

**Cleaning**
- ⬜ Standardise `year` column across all tables (strip `financial_year` prefix where present; cast to `Int32`)
- ⬜ Standardise `sector` column to canonical values (`Public`, `Private`, `Not-for-profit`, `Total`)
- ⬜ Add `rate_base` metadata column to admission rate table documenting denominator (e.g. `per_1000`)
- ⬜ Cast count columns to `Int32`; rate/ratio columns to `Float32`
- ⬜ Trim whitespace from all string columns
- ⬜ Save cleaned parquets to `data/4_processed/{table}_clean.parquet`
- ⬜ Log all operations at INFO level; flag issues at WARNING; halt on ERROR

## 6. Notes

- The expenditure table uses `financial_year` (e.g. "2006/07") while workforce tables use integer year. Convert financial year to the starting calendar year (2006 for "2006/07").
- Sector naming in the facilities table may differ from workforce tables — check both before canonicalising.
- Do not drop rows with nulls in non-critical columns (e.g. breakdowns by sub-type); only fail hard on year and primary count/rate columns.

---

## Implementation Plan

### 1. Feature Overview

Validate 10 PS-001 source tables against config-driven rules, clean sector and year columns, and produce Parquet outputs ready for analysis. Primary user: **Healthcare Data Analyst**. Output: 10 `*_clean.parquet` files + `data_quality_report.csv`.

---

### 2. Component Analysis & Reuse Strategy

| Component | Status | Decision |
|-----------|--------|----------|
| `shared/src/data_processing/profiler.py` | Created (Story 01) | Reuse shape/null utilities |
| `shared/src/data_processing/validator.py` | Does not exist | Create new |
| `shared/src/data_processing/cleaner.py` | Does not exist | Create new |
| `problem-statements/ps-001-healthcare-system-baseline/config/config.yml` | Created (Story 01) | Extend with `validation:` block |
| `shared/data/1_raw/` | Populated (Story 01) | Read-only; never modify |
| `data/4_processed/` | Exists, empty | Write cleaned parquets here |

---

### 3. Affected Files

```
[CREATE] shared/src/data_processing/validator.py
  - Function: validate_table(df, rules) -> tuple[bool, list[dict]]
  - Function: check_nulls(df, required_cols) -> list[dict]
  - Function: check_numeric_bounds(df, bounds) -> list[dict]

[CREATE] shared/src/data_processing/cleaner.py
  - Function: standardise_year_column(df) -> pl.DataFrame
  - Function: standardise_sector_column(df) -> pl.DataFrame
  - Function: add_rate_base_column(df, rate_base) -> pl.DataFrame
  - Function: cast_numeric_columns(df, int_cols, float_cols) -> pl.DataFrame
  - Function: clean_table(df, config) -> pl.DataFrame

[MODIFY] problem-statements/ps-001-healthcare-system-baseline/config/config.yml
  - Add: validation block with per-table rules

[CREATE] problem-statements/ps-001-healthcare-system-baseline/scripts/run_cleaning.py
  - Orchestrates validation → cleaning → parquet write
  - Dependencies: validator, cleaner, pyyaml, loguru

[CREATE] problem-statements/ps-001-healthcare-system-baseline/tests/unit/test_cleaner.py
  - Unit tests for all cleaner functions
```

---

### 4. Data Pipeline

```
shared/data/1_raw/{subdir}/*.csv
        │
        ▼ validate_table()
  data_quality_report.csv (issues flagged)
        │
        ▼ clean_table()
        │  standardise_year_column()
        │  standardise_sector_column()
        │  cast_numeric_columns()
        │  add_rate_base_column()   (admissions table only)
        │
        ▼
data/4_processed/{table}_clean.parquet
logs/etl/cleaning.log
```

---

### 5. Code Generation Specifications

#### 5.1 `shared/src/data_processing/validator.py`

```python
"""Data validation utilities for PS-001 source tables.

Validates column presence, dtypes, year bounds, and numeric bounds
against config-driven rules. Returns structured issue lists for reporting.
"""

from pathlib import Path
from typing import Any

import polars as pl
from loguru import logger


def check_required_columns(
    df: pl.DataFrame,
    required_cols: list[str],
    table_name: str,
) -> list[dict]:
    """Check that all required columns are present.

    Args:
        df: Table to validate
        required_cols: List of column names that must exist
        table_name: Used in issue records

    Returns:
        List of issue dicts, empty if all columns present
    """
    issues: list[dict] = []
    for col in required_cols:
        if col not in df.columns:
            issues.append({
                "table": table_name,
                "field": col,
                "issue_type": "missing_column",
                "records_affected": df.shape[0],
                "action_taken": "halted — column required",
            })
            logger.error(f"[{table_name}] Required column missing: {col}")
    return issues


def check_nulls(
    df: pl.DataFrame,
    required_cols: list[str],
    table_name: str,
) -> list[dict]:
    """Check that required columns have no null values.

    Args:
        df: Table to validate
        required_cols: Columns that must be null-free
        table_name: Used in issue records

    Returns:
        List of issue dicts for any column with > 0 nulls
    """
    issues: list[dict] = []
    for col in required_cols:
        if col not in df.columns:
            continue
        null_count = df[col].null_count()
        if null_count > 0:
            pct = null_count / df.shape[0] * 100
            issues.append({
                "table": table_name,
                "field": col,
                "issue_type": "nulls_in_required_column",
                "records_affected": null_count,
                "action_taken": f"flagged — {pct:.1f}% null",
            })
            logger.warning(
                f"[{table_name}] Column '{col}': {null_count} nulls ({pct:.1f}%)"
            )
    return issues


def check_numeric_bounds(
    df: pl.DataFrame,
    bounds: dict[str, dict[str, float]],
    table_name: str,
) -> list[dict]:
    """Check numeric columns are within expected bounds.

    Args:
        df: Table to validate
        bounds: Mapping of {column: {min: float, max: float}}
            e.g. {"headcount": {"min": 0, "max": 100000}}
        table_name: Used in issue records

    Returns:
        List of issue dicts for out-of-bound records
    """
    issues: list[dict] = []
    for col, limits in bounds.items():
        if col not in df.columns:
            continue
        low = limits.get("min")
        high = limits.get("max")

        out_of_range: pl.Series = pl.Series("flag", [False] * df.shape[0])
        if low is not None:
            out_of_range = out_of_range | (df[col] < low)
        if high is not None:
            out_of_range = out_of_range | (df[col] > high)

        bad_count = out_of_range.sum()
        if bad_count > 0:
            pct = bad_count / df.shape[0] * 100
            issues.append({
                "table": table_name,
                "field": col,
                "issue_type": "out_of_range",
                "records_affected": bad_count,
                "action_taken": f"flagged — {pct:.1f}% out of [{low}, {high}]",
            })
            logger.warning(
                f"[{table_name}] Column '{col}': {bad_count} values outside "
                f"[{low}, {high}]"
            )
    return issues


def validate_table(
    df: pl.DataFrame,
    rules: dict[str, Any],
    table_name: str,
) -> tuple[bool, list[dict]]:
    """Run all validation checks defined in rules against df.

    Args:
        df: Table to validate
        rules: Dict with keys:
            required_columns: list[str]
            null_check_columns: list[str]
            numeric_bounds: dict[str, {min, max}]
        table_name: Used in issue records

    Returns:
        Tuple of (passed: bool, issues: list[dict])
        passed is False if any required column is missing or null
    """
    all_issues: list[dict] = []
    all_issues += check_required_columns(
        df, rules.get("required_columns", []), table_name
    )
    all_issues += check_nulls(
        df, rules.get("null_check_columns", []), table_name
    )
    all_issues += check_numeric_bounds(
        df, rules.get("numeric_bounds", {}), table_name
    )

    critical = [
        i for i in all_issues
        if i["issue_type"] in ("missing_column", "nulls_in_required_column")
    ]
    passed = len(critical) == 0
    status = "PASS" if passed else "FAIL"
    logger.info(f"[{table_name}] Validation: {status} ({len(all_issues)} issues)")
    return passed, all_issues
```

#### 5.2 `shared/src/data_processing/cleaner.py`

```python
"""Data cleaning utilities for PS-001 source tables.

All functions are pure transformations — input is not modified.
Outputs are new Polars DataFrames.
"""

import polars as pl
from loguru import logger


# Canonical sector values and their known aliases
SECTOR_CANONICAL_MAP: dict[str, str] = {
    "public sector": "Public",
    "public": "Public",
    "govt": "Public",
    "government": "Public",
    "private sector": "Private",
    "private": "Private",
    "not-for-profit": "Not-for-profit",
    "not for profit": "Not-for-profit",
    "voluntary": "Not-for-profit",
    "vwo": "Not-for-profit",
    "total": "Total",
    "all": "Total",
    "overall": "Total",
}


def standardise_year_column(df: pl.DataFrame) -> pl.DataFrame:
    """Normalise year representation to a single `year: Int32` column.

    Handles:
    - Integer year columns named "year" or "Year"
    - Financial year strings like "2006/07" → 2006

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with `year` column as Int32

    Raises:
        ValueError: If no recognisable year column is found
    """
    year_candidates = [c for c in df.columns if c.lower() in ("year", "financial_year")]
    if not year_candidates:
        raise ValueError(
            f"No year column found. Columns: {df.columns}"
        )

    year_col = year_candidates[0]

    if df[year_col].dtype == pl.Utf8:
        # Extract 4-digit start year from "2006/07" pattern
        df = df.with_columns(
            pl.col(year_col)
            .str.extract(r"(\d{4})", 1)
            .cast(pl.Int32)
            .alias("year")
        )
        if year_col != "year":
            df = df.drop(year_col)
    elif year_col != "year":
        df = df.rename({year_col: "year"})
        df = df.with_columns(pl.col("year").cast(pl.Int32))
    else:
        df = df.with_columns(pl.col("year").cast(pl.Int32))

    logger.debug(f"Year column standardised from '{year_col}' to 'year: Int32'")
    return df


def standardise_sector_column(df: pl.DataFrame) -> pl.DataFrame:
    """Normalise sector column to canonical values.

    Applies SECTOR_CANONICAL_MAP after lowercasing and stripping whitespace.
    Unrecognised values are logged at WARNING and left unchanged.

    Args:
        df: Input DataFrame (must contain a 'sector' column)

    Returns:
        DataFrame with sector values canonicalised
    """
    sector_candidates = [c for c in df.columns if c.lower() in ("sector", "type")]
    if not sector_candidates:
        logger.debug("No sector column found — skipping sector standardisation")
        return df

    sector_col = sector_candidates[0]

    # Build Polars replace_strict mapping
    cleaned = df[sector_col].str.strip_chars().str.to_lowercase()
    mapped = cleaned.replace(
        SECTOR_CANONICAL_MAP,
        default=None,  # None means "keep original" in replace()
    )

    # Where mapped is null (unrecognised), keep original
    original_strip = df[sector_col].str.strip_chars()
    final = pl.when(mapped.is_null()).then(original_strip).otherwise(mapped)

    unrecognised = (
        df.select(pl.col(sector_col).str.strip_chars().str.to_lowercase())
        .filter(~pl.col(sector_col).is_in(list(SECTOR_CANONICAL_MAP.keys())))
        [sector_col]
        .unique()
        .to_list()
    )
    if unrecognised:
        logger.warning(
            f"Unrecognised sector values (left unchanged): {unrecognised}"
        )

    result = df.drop(sector_col).with_columns(final.alias("sector"))
    logger.debug("Sector column standardised")
    return result


def add_rate_base_column(df: pl.DataFrame, rate_base: str) -> pl.DataFrame:
    """Append a metadata column documenting the admission rate denominator.

    Args:
        df: Admission rate DataFrame
        rate_base: One of "per_1000" or "per_10000"

    Returns:
        DataFrame with `rate_base: Utf8` column appended
    """
    valid_bases = {"per_1000", "per_10000"}
    if rate_base not in valid_bases:
        raise ValueError(
            f"rate_base must be one of {valid_bases}, got '{rate_base}'"
        )
    df = df.with_columns(pl.lit(rate_base).alias("rate_base"))
    logger.debug(f"Added rate_base column: {rate_base}")
    return df


def cast_numeric_columns(
    df: pl.DataFrame,
    int_cols: list[str],
    float_cols: list[str],
) -> pl.DataFrame:
    """Cast count columns to Int32 and rate/ratio columns to Float32.

    Args:
        df: Input DataFrame
        int_cols: Column names to cast to Int32
        float_cols: Column names to cast to Float32

    Returns:
        DataFrame with requested columns recast
    """
    exprs = []
    for col in int_cols:
        if col in df.columns:
            exprs.append(pl.col(col).cast(pl.Int32))
    for col in float_cols:
        if col in df.columns:
            exprs.append(pl.col(col).cast(pl.Float32))

    if exprs:
        df = df.with_columns(exprs)
    return df


def trim_string_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Strip leading/trailing whitespace from all Utf8 columns.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with all string columns trimmed
    """
    string_cols = [c for c, t in zip(df.columns, df.dtypes) if t == pl.Utf8]
    if string_cols:
        df = df.with_columns(
            [pl.col(c).str.strip_chars() for c in string_cols]
        )
    return df


def clean_table(df: pl.DataFrame, table_config: dict) -> pl.DataFrame:
    """Apply all cleaning steps to a single table.

    Args:
        df: Raw DataFrame
        table_config: Per-table config section from config.yml with keys:
            int_columns, float_columns, rate_base (optional)

    Returns:
        Cleaned DataFrame ready for downstream analysis
    """
    df = trim_string_columns(df)
    df = standardise_year_column(df)

    if any(c.lower() in ("sector", "type") for c in df.columns):
        df = standardise_sector_column(df)

    df = cast_numeric_columns(
        df,
        int_cols=table_config.get("int_columns", []),
        float_cols=table_config.get("float_columns", []),
    )

    if "rate_base" in table_config:
        df = add_rate_base_column(df, table_config["rate_base"])

    return df
```

#### 5.3 `problem-statements/ps-001-healthcare-system-baseline/scripts/run_cleaning.py`

```python
"""PS-001 Story 02 — Validation & Cleaning Pipeline.

Run with: python problem-statements/ps-001-healthcare-system-baseline/scripts/run_cleaning.py
"""

import sys
from pathlib import Path

import polars as pl
import yaml
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.src.data_processing.cleaner import clean_table  # noqa: E402
from shared.src.data_processing.validator import validate_table  # noqa: E402

PS_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = PS_DIR / "config" / "config.yml"
LOG_PATH = PS_DIR / "logs" / "etl" / "cleaning.log"
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
RESULTS_DIR = PS_DIR / "results" / "tables"
SHARED_RAW = PROJECT_ROOT / "shared" / "data" / "1_raw"


def _setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(str(log_path), level="INFO", rotation="10 MB")


def _load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def main() -> None:
    _setup_logging(LOG_PATH)
    logger.info("=== PS-001 Story 02: Validation & Cleaning ===")

    config = _load_config(CONFIG_PATH)
    table_map = config["table_map"]
    validation_rules = config.get("validation", {})
    cleaning_config = config.get("cleaning", {})

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    all_issues: list[dict] = []
    any_critical_failure = False

    for csv_name, subdir in table_map.items():
        table_name = csv_name.replace(".csv", "")
        raw_path = SHARED_RAW / subdir / csv_name

        if not raw_path.exists():
            logger.error(f"Raw file not found: {raw_path}")
            any_critical_failure = True
            continue

        df = pl.read_csv(str(raw_path), infer_schema_length=1000)
        logger.info(f"Loaded {table_name}: {df.shape}")

        # Validation
        rules = validation_rules.get(table_name, {})
        passed, issues = validate_table(df, rules, table_name)
        all_issues.extend(issues)

        if not passed:
            logger.error(f"[{table_name}] Critical validation failure — halting.")
            any_critical_failure = True
            continue

        # Cleaning
        table_cfg = cleaning_config.get(table_name, {})
        try:
            cleaned = clean_table(df, table_cfg)
        except ValueError as exc:
            logger.error(f"[{table_name}] Cleaning error: {exc}")
            any_critical_failure = True
            continue

        # Write parquet
        out_path = PROCESSED_DIR / f"{table_name}_clean.parquet"
        cleaned.write_parquet(str(out_path))
        logger.info(f"Saved: {out_path} ({cleaned.shape[0]} rows)")

    # Write quality report
    if all_issues:
        issues_df = pl.DataFrame(all_issues)
    else:
        issues_df = pl.DataFrame(schema={
            "table": pl.Utf8, "field": pl.Utf8,
            "issue_type": pl.Utf8, "records_affected": pl.Int64,
            "action_taken": pl.Utf8,
        })

    report_path = RESULTS_DIR / "data_quality_report.csv"
    issues_df.write_csv(str(report_path))
    logger.info(f"Quality report: {report_path} ({len(all_issues)} issues recorded)")

    if any_critical_failure:
        logger.error("Pipeline exited with critical failures. Review log before proceeding.")
        sys.exit(1)

    logger.info("=== Cleaning complete ===")


if __name__ == "__main__":
    main()
```

#### 5.4 Config Extension (add to `config.yml`)

```yaml
# Add these blocks to existing config.yml

validation:
  doctors:
    required_columns: ["year", "headcount"]
    null_check_columns: ["year", "headcount"]
    numeric_bounds:
      headcount: {min: 100, max: 50000}
  nurses:
    required_columns: ["year", "headcount"]
    null_check_columns: ["year", "headcount"]
    numeric_bounds:
      headcount: {min: 100, max: 100000}
  hospital_admissions:
    required_columns: ["year", "age_group", "sex", "rate"]
    null_check_columns: ["year", "rate"]
    numeric_bounds:
      rate: {min: 0, max: 2000}
  government_health_expenditure:
    required_columns: ["financial_year", "expenditure"]
    null_check_columns: ["financial_year", "expenditure"]
    numeric_bounds:
      expenditure: {min: 0, max: 100000}

cleaning:
  doctors:
    int_columns: ["headcount"]
    float_columns: []
  nurses:
    int_columns: ["headcount"]
    float_columns: []
  pharmacists:
    int_columns: ["headcount"]
    float_columns: []
  dentists:
    int_columns: ["headcount"]
    float_columns: []
  allied_health_professionals:
    int_columns: ["headcount"]
    float_columns: []
  inpatient_beds:
    int_columns: ["beds"]
    float_columns: []
  primary_care_clinics:
    int_columns: ["count"]
    float_columns: []
  hospital_admissions:
    int_columns: []
    float_columns: ["rate"]
    rate_base: "per_1000"   # UPDATE after denominator confirmed in Story 01
  government_health_expenditure:
    int_columns: []
    float_columns: ["expenditure"]
  long_term_care_admissions:
    int_columns: ["admissions"]
    float_columns: []
```

---

### 6. Testing Strategy

**File**: `problem-statements/ps-001-healthcare-system-baseline/tests/unit/test_cleaner.py`

```python
"""Unit tests for shared/src/data_processing/cleaner.py"""

import sys
from pathlib import Path

import polars as pl
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.src.data_processing.cleaner import (
    add_rate_base_column,
    cast_numeric_columns,
    clean_table,
    standardise_sector_column,
    standardise_year_column,
    trim_string_columns,
)


def test_standardise_year_integer() -> None:
    df = pl.DataFrame({"Year": [2010, 2011, 2012], "value": [1, 2, 3]})
    result = standardise_year_column(df)
    assert "year" in result.columns
    assert result["year"].dtype == pl.Int32
    assert result["year"].to_list() == [2010, 2011, 2012]


def test_standardise_year_financial_string() -> None:
    df = pl.DataFrame({"financial_year": ["2006/07", "2007/08"], "val": [10, 20]})
    result = standardise_year_column(df)
    assert "year" in result.columns
    assert "financial_year" not in result.columns
    assert result["year"].to_list() == [2006, 2007]


def test_standardise_sector_canonical_values() -> None:
    df = pl.DataFrame({
        "year": [2010, 2011, 2012],
        "sector": ["Public Sector", "private sector", "Total"],
    })
    result = standardise_sector_column(df)
    assert result["sector"].to_list() == ["Public", "Private", "Total"]


def test_standardise_sector_unrecognised_kept() -> None:
    df = pl.DataFrame({"sector": ["Unknown Category"], "year": [2010]})
    result = standardise_sector_column(df)
    assert result["sector"][0] == "Unknown Category"


def test_add_rate_base_valid() -> None:
    df = pl.DataFrame({"year": [2010], "rate": [150.0]})
    result = add_rate_base_column(df, "per_1000")
    assert "rate_base" in result.columns
    assert result["rate_base"][0] == "per_1000"


def test_add_rate_base_invalid() -> None:
    df = pl.DataFrame({"year": [2010]})
    with pytest.raises(ValueError, match="rate_base must be"):
        add_rate_base_column(df, "per_million")


def test_cast_numeric_columns_int32() -> None:
    df = pl.DataFrame({"year": [2010], "headcount": [5000]})
    result = cast_numeric_columns(df, int_cols=["headcount"], float_cols=[])
    assert result["headcount"].dtype == pl.Int32


def test_trim_whitespace() -> None:
    df = pl.DataFrame({"sector": ["  Public  ", " Private"], "year": [2010, 2011]})
    result = trim_string_columns(df)
    assert result["sector"].to_list() == ["Public", "Private"]


def test_clean_table_full_pipeline() -> None:
    df = pl.DataFrame({
        "financial_year": ["2010/11", "2011/12"],
        "sector": ["public sector", "Total"],
        "headcount": ["5000", "15000"],
    })
    table_config = {"int_columns": ["headcount"], "float_columns": []}
    result = clean_table(df, table_config)
    assert result["year"].dtype == pl.Int32
    assert result["year"][0] == 2010
    assert result["sector"][0] == "Public"
```

---

### 7. Implementation Steps

**Phase 1: Config Extension**
- [ ] Add `validation:` and `cleaning:` blocks to `config/config.yml`
- [ ] Update `rate_base` value after Story 01 confirms the denominator

**Phase 2: Core Modules**
- [ ] Create `shared/src/data_processing/validator.py`
- [ ] Create `shared/src/data_processing/cleaner.py`

**Phase 3: Orchestration Script**
- [ ] Create `scripts/run_cleaning.py`
- [ ] Run script; confirm 10 `*_clean.parquet` files exist in `data/4_processed/`
- [ ] Confirm `data_quality_report.csv` lists all issues (empty if all tables clean)

**Phase 4: Testing**
- [ ] Create `tests/unit/test_cleaner.py`
- [ ] Run `pytest tests/unit/test_cleaner.py -v` — all 9 tests must pass
- [ ] Review `cleaning.log`; confirm no ERROR messages

**Phase 5: Adaptive Validation**
- [ ] Open each cleaned parquet; spot-check 5 rows per table
- [ ] Confirm `sector` values are all canonical (no "public sector" variants remain)
- [ ] Confirm `year` is Int32 across all tables
- [ ] Confirm `hospital_admissions_clean.parquet` has `rate_base` column

---

### 8. Adaptive Implementation Strategy

**If a column name in the raw CSV differs from the config** (e.g. `"total"` instead of `"headcount"`): Add an alias mapping to the `cleaning:` block in config under `column_aliases: {total: headcount}` and handle in `clean_table()` with a `df.rename()` step.

**If validate_table raises on a non-critical NULL**: Downgrade to WARNING and document in quality report without halting — only halt on `year` and primary metric column nulls.

---

### 9. Security & Privacy

- Data is national aggregate — no PII. All cleaning is reproducible and logged.
- Raw files in `shared/data/1_raw/` must remain unmodified (project convention).
- Cleaned parquets in `data/4_processed/` are pipeline outputs, not raw data.

---

### 10. Version Control

```bash
git checkout -b feat/ps-001-story-02-cleaning
git commit -m "feat(ps-001): add validator and cleaner modules"
git commit -m "feat(ps-001): add run_cleaning.py orchestration script"
git commit -m "test(ps-001): add cleaner unit tests"
git commit -m "config(ps-001): add validation and cleaning rules to config.yml"
```

---

### 11. Instruction File Compliance

| Instruction File | Requirements | Verified |
|------------------|-------------|----------|
| python-best-practices | Type hints ✅, loguru ✅, input validation ✅ | ✅ |
| data-analysis-best-practices | Never modify 1_raw/ ✅, log all transforms ✅ | ✅ |
| data-analysis-folder-structure | Parquets to data/4_processed/ ✅ | ✅ |
| moh-data-quality-assessment | % null reporting ✅, issue log ✅ | ✅ |
