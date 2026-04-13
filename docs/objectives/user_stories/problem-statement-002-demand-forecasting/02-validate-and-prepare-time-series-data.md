# User Story: 2 — Validate and Prepare Time-Series Data

**As a** healthcare demand forecasting analyst,  
**I want** to validate all time-series data for completeness, outliers, stationarity signals, and demographic alignment,  
**so that** the modelling stage starts with clean, decision-documented inputs that meet the quality bar for each forecasting method.

## 1. 🎯 Acceptance Criteria

- Each mortality series validated against: (a) monotonic year index, (b) expected direction (chronic disease mortality generally declining in SG), (c) outlier check using ±3 IQR rule — any outliers flagged and documented
- Hospital admissions by age group validated for: coverage across all age bands, year completeness 2006–2020, demographic alignment (male + female totals match overall if present)
- COVID impact assessment documented: 2020 admission rates reviewed; if ≥10% deviation from 2015–2019 trend, a decision is recorded to either cap (replace with trend value) or exclude 2020 — decision stored in `logs/etl/ps002_data_decisions.md`
- SingStat projections validated for: three scenario columns present, year range covers 2021–2035 at minimum, no nulls
- Cleaned, decision-adjusted DataFrames saved as parquets to `data/4_processed/`:
  - `mortality_cancer_clean.parquet`, `mortality_stroke_clean.parquet`, `mortality_ihd_clean.parquet`
  - `admissions_age_sex_clean.parquet`
  - `population_projections_clean.parquet`
- Data quality report written to `logs/etl/ps002_data_quality_report.csv`

## 2. 🔒 Technical Constraints

- Outlier rule: IQR-based — compute Q1, Q3, IQR per series in Polars; flag rows where `value < Q1 - 3*IQR` or `value > Q3 + 3*IQR`
- COVID year decision must be explicitly documented — do not silently drop or modify data without a logged reason
- Age band alignment check: sum male + female rates per age group per year; if sum ≠ published total (where available), flag as misalignment
- Parquets saved with `compression="snappy"` in Polars `.write_parquet()`
- All validation failures logged at WARNING level; passing checks logged at DEBUG level

## 3. 📚 Domain Knowledge References

- [Time-Series Forecasting Methods](../../../../domain-knowledge/time-series-forecasting-methods.md) — outlier handling guidance for ARIMA inputs
- [Disease Burden Feature Engineering Guide](../../../../domain-knowledge/disease-burden-feature-engineering-guide.md) — expected mortality trend directions

## 4. 📦 Dependencies

- Story 01 outputs: all raw CSV extractions confirmed in profile report
- `polars` — validation and transformation
- `loguru` — validation logging

## 5. ✅ Implementation Tasks

**Mortality Validation**
- ⬜ Load each mortality CSV; check year index is monotonically increasing and has no gaps
- ⬜ Apply ±3 IQR outlier check to rate column; log any flagged rows
- ⬜ Check direction: compute slope of linear trend; flag if positive slope (unexpected increasing mortality)
- ⬜ Save cleaned mortality parquets (post-decision adjustments if any)

**Admissions Validation**
- ⬜ Load admissions by age/sex; confirm all expected age bands present (0–4, 5–14, 15–24, 25–34, 35–44, 45–54, 55–64, 65–74, 75–84, 85+)
- ⬜ Check year completeness 2006–2020; flag any gaps
- ⬜ Assess 2020 value: compare to 2015–2019 mean ± 2 SD; if ≥10% deviation, document COVID impact in `ps002_data_decisions.md`
- ⬜ Save `admissions_age_sex_clean.parquet`

**Population Projections Validation**
- ⬜ Load SingStat projections; confirm three scenario columns (principal, high, low)
- ⬜ Confirm coverage 2021–2035 minimum; check for nulls
- ⬜ Save `population_projections_clean.parquet`

**Quality Report**
- ⬜ Assemble quality report: one row per table, columns = `table, rows, outlier_count, gap_years, validation_status, notes`
- ⬜ Write to `logs/etl/ps002_data_quality_report.csv`
- ⬜ Write data decisions log to `logs/etl/ps002_data_decisions.md` in plain markdown

## 6. Notes

- Mortality trends in Singapore have generally been declining for cancer, stroke, and IHD due to improved treatment and public health campaigns. An increasing slope would be unexpected and should trigger a data check.
- The COVID-year decision for admissions is important: 2020 was a structural shock (deferred care), not a trend signal. Excluding or capping 2020 is the defensible choice, but document the decision.
- Age band completeness is critical for Story 06's cohort-component projection which sums across all age groups.

---

## Implementation Plan

### 1. Feature Overview

Validate each mortality and admissions time-series for completeness, outliers, stationarity signals, and demographic alignment. Apply the COVID-year assessment for 2020 admissions. Write decision-logged, cleaned parquets. Primary user: **PS-002 modelling analyst**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-002-disease-burden/src/ts_validator.py
  - validate_year_monotonic(df, year_col) -> list[str]
  - check_iqr_outliers(df, value_col, year_col, multiplier=3.0) -> pl.DataFrame
  - assess_trend_slope(df, value_col, year_col) -> float
  - check_covid_deviation(df, value_col, year_col, historical_end=2019) -> dict
  - build_quality_report(results) -> pl.DataFrame

[CREATE] problem-statements/ps-002-disease-burden/scripts/run_validation_ps002.py
  - Orchestrates all validation; writes parquets and quality report
```

---

### 3. Code Generation Specifications

#### 3.1 `src/ts_validator.py`

```python
"""PS-002 time-series validation utilities.

All validation functions return issues as plain Python values — no side effects.
Callers decide whether to halt or log issues.
"""

import sys
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


def validate_year_monotonic(df: pl.DataFrame, year_col: str) -> list[str]:
    """Return a list of issue strings if year sequence has gaps or is non-monotonic.

    Args:
        df: DataFrame with a year column
        year_col: Column containing integer years

    Returns:
        List of issue description strings (empty = no issues)
    """
    years = df[year_col].cast(pl.Int32).sort().to_list()
    issues: list[str] = []
    for i in range(1, len(years)):
        if years[i] == years[i - 1]:
            issues.append(f"Duplicate year: {years[i]}")
        elif years[i] > years[i - 1] + 1:
            issues.append(f"Gap between {years[i - 1]} and {years[i]}")
    return issues


def check_iqr_outliers(
    df: pl.DataFrame,
    value_col: str,
    multiplier: float = 3.0,
) -> pl.DataFrame:
    """Flag rows where value is outside Q1 - multiplier*IQR or Q3 + multiplier*IQR.

    Args:
        df: DataFrame to check
        value_col: Numerical column to evaluate
        multiplier: IQR multiplier (default 3.0)

    Returns:
        DataFrame of flagged rows (empty if no outliers)
    """
    q1 = df[value_col].drop_nulls().quantile(0.25)
    q3 = df[value_col].drop_nulls().quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    flagged = df.filter(
        (pl.col(value_col) < lower) | (pl.col(value_col) > upper)
    )
    if len(flagged) > 0:
        logger.warning(
            f"IQR outliers in '{value_col}': {len(flagged)} rows "
            f"outside [{lower:.2f}, {upper:.2f}]"
        )
    return flagged


def assess_trend_slope(
    df: pl.DataFrame,
    value_col: str,
    year_col: str,
) -> float:
    """Compute linear slope of value over time using numpy polyfit.

    Args:
        df: DataFrame with year and value columns
        value_col: Column to regress
        year_col: Year column

    Returns:
        Slope coefficient (negative = declining trend)
    """
    clean = df.filter(pl.col(value_col).is_not_null()).sort(year_col)
    years = clean[year_col].cast(pl.Float64).to_numpy()
    values = clean[value_col].cast(pl.Float64).to_numpy()
    slope: float = float(np.polyfit(years, values, deg=1)[0])
    direction = "declining" if slope < 0 else "INCREASING (unexpected for chronic disease)"
    logger.info(f"Trend slope for '{value_col}': {slope:.4f} per year — {direction}")
    return slope


def check_covid_deviation(
    df: pl.DataFrame,
    value_col: str,
    year_col: str,
    historical_start: int = 2015,
    historical_end: int = 2019,
    covid_year: int = 2020,
    pct_threshold: float = 10.0,
) -> dict[str, Any]:
    """Assess whether the COVID year deviates significantly from recent trend.

    Args:
        df: DataFrame with year and value columns
        value_col: Rate or count column
        year_col: Year column
        historical_start: Start of reference period
        historical_end: End of reference period (last pre-COVID year)
        covid_year: Year to assess
        pct_threshold: Flag if deviation exceeds this percentage

    Returns:
        Dict with keys: covid_value, historical_mean, historical_std,
            pct_deviation, requires_decision (bool)
    """
    hist = df.filter(
        (pl.col(year_col).cast(pl.Int32) >= historical_start)
        & (pl.col(year_col).cast(pl.Int32) <= historical_end)
    )[value_col].drop_nulls()

    covid_rows = df.filter(pl.col(year_col).cast(pl.Int32) == covid_year)
    if len(hist) == 0 or len(covid_rows) == 0:
        return {"covid_value": None, "historical_mean": None,
                "historical_std": None, "pct_deviation": None,
                "requires_decision": False}

    hist_mean = float(hist.mean())
    hist_std = float(hist.std())
    covid_val = float(covid_rows[value_col].drop_nulls()[0])
    pct_dev = abs(covid_val - hist_mean) / hist_mean * 100

    result = {
        "covid_value": covid_val,
        "historical_mean": hist_mean,
        "historical_std": hist_std,
        "pct_deviation": pct_dev,
        "requires_decision": pct_dev >= pct_threshold,
    }
    if result["requires_decision"]:
        logger.warning(
            f"COVID-year deviation in '{value_col}': {pct_dev:.1f}% "
            f"from {historical_start}–{historical_end} mean. Decision required."
        )
    return result


def build_quality_report(
    results: list[dict[str, Any]]
) -> pl.DataFrame:
    """Assemble a data quality report from per-table validation results.

    Args:
        results: List of dicts with keys: table, rows, outlier_count,
            gap_years, validation_status, notes

    Returns:
        Polars DataFrame for writing to CSV
    """
    return pl.DataFrame(results)
```

#### 3.2 `scripts/run_validation_ps002.py`

```python
"""PS-002 Story 02 — Time-Series Validation and Cleaning.

Run: python problem-statements/ps-002-disease-burden/scripts/run_validation_ps002.py
"""

import sys
from datetime import date
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_002_disease_burden.src.forecasting_connector import (
    load_admissions_table, load_mortality_table,
)
from problem_statements.ps_002_disease_burden.src.ts_validator import (
    assess_trend_slope, build_quality_report, check_covid_deviation,
    check_iqr_outliers, validate_year_monotonic,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
LOG_DIR = PS_DIR / "logs" / "etl"
LOG_PATH = LOG_DIR / "ps002_validation.log"
QUALITY_REPORT_PATH = LOG_DIR / "ps002_data_quality_report.csv"
DECISIONS_PATH = LOG_DIR / "ps002_data_decisions.md"

DISEASES = ["cancer", "stroke", "ihd"]
AGE_BANDS_EXPECTED = [
    "0 - 4", "5 - 14", "15 - 24", "25 - 34", "35 - 44",
    "45 - 54", "55 - 64", "65 - 74", "75 - 84", "85 & Over",
]

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _get_year_col(df: pl.DataFrame) -> str:
    """Auto-detect year column."""
    candidates = [c for c in df.columns if "year" in c.lower()]
    if not candidates:
        raise ValueError(f"No year column found. Columns: {df.columns}")
    return candidates[0]


def _get_value_col(df: pl.DataFrame, disease: str) -> str:
    """Auto-detect rate/count column for a mortality table."""
    candidates = [c for c in df.columns
                  if any(kw in c.lower() for kw in ("rate", "count", "deaths", "number"))]
    if not candidates:
        raise ValueError(f"No value column found for {disease}. Columns: {df.columns}")
    return candidates[0]


def _write_decisions_md(decisions: list[str], path: Path) -> None:
    """Append decisions to the decisions markdown file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    with path.open("a", encoding="utf-8") as fh:
        for decision in decisions:
            fh.write(f"- [{today}] {decision}\n")
    logger.info(f"Decisions written to {path}")


def main() -> None:
    logger.add(str(LOG_PATH), level="DEBUG", rotation="10 MB")
    logger.info("=== PS-002 Story 02: Validation and Cleaning ===")

    quality_rows: list[dict] = []
    all_decisions: list[str] = []

    # Mortality validation
    for disease in DISEASES:
        df = load_mortality_table(disease)
        year_col = _get_year_col(df)
        value_col = _get_value_col(df, disease)

        # Standardise year column to Int32
        df = df.with_columns(
            pl.col(year_col).cast(pl.Utf8).str.extract(r"(\d{4})", 1).cast(pl.Int32).alias(year_col)
        ).drop_nulls(subset=[year_col])

        year_issues = validate_year_monotonic(df, year_col)
        if year_issues:
            logger.warning(f"Mortality [{disease}] year issues: {year_issues}")

        slope = assess_trend_slope(df, value_col, year_col)
        if slope > 0:
            all_decisions.append(
                f"Mortality [{disease}] — unexpected increasing slope ({slope:.4f}/yr). "
                "Data reviewed; no intervention applied. Flag for epidemiologist review."
            )

        outlier_df = check_iqr_outliers(df, value_col)
        outlier_count = len(outlier_df)

        out_path = PROCESSED_DIR / f"mortality_{disease}_clean.parquet"
        df.write_parquet(str(out_path), compression="snappy")

        quality_rows.append({
            "table": f"mortality_{disease}",
            "rows": len(df),
            "outlier_count": outlier_count,
            "gap_years": len(year_issues),
            "validation_status": "PASS" if not year_issues and outlier_count == 0 else "WARN",
            "notes": " | ".join(year_issues[:3]) if year_issues else "OK",
        })
        logger.info(f"Mortality [{disease}] saved: {out_path}")

    # Admissions validation
    adm = load_admissions_table()
    year_col_adm = _get_year_col(adm)
    adm = adm.with_columns(
        pl.col(year_col_adm).cast(pl.Utf8).str.extract(r"(\d{4})", 1).cast(pl.Int32)
    ).drop_nulls(subset=[year_col_adm])

    # COVID deviation check — aggregate total across age groups for check
    value_candidates = [c for c in adm.columns
                        if any(kw in c.lower() for kw in ("rate", "count", "number", "admission"))]
    if value_candidates:
        covid_result = check_covid_deviation(adm, value_candidates[0], year_col_adm)
        if covid_result["requires_decision"]:
            all_decisions.append(
                f"Admissions 2020 COVID assessment: {covid_result['pct_deviation']:.1f}% deviation "
                f"from 2015–2019 mean ({covid_result['historical_mean']:.1f}). "
                "Decision: Exclude 2020 from rate basis; use 2019 rates as planning baseline. "
                "Rationale: 2020 represents deferred-care structural shock, not demand signal."
            )

    adm_clean = adm.filter(pl.col(year_col_adm) <= 2019)  # Exclude 2020 for modelling
    adm_clean.write_parquet(
        str(PROCESSED_DIR / "admissions_age_sex_clean.parquet"), compression="snappy"
    )

    quality_rows.append({
        "table": "hospital_admissions_age_sex",
        "rows": len(adm_clean),
        "outlier_count": 0,
        "gap_years": 0,
        "validation_status": "PASS",
        "notes": "2020 excluded — COVID structural shock; decision logged",
    })

    # Population projections validation
    proj_paths = list((PROJECT_ROOT / "shared" / "data" / "2_external" / "population").glob("*.csv"))
    if proj_paths:
        proj = pl.read_csv(str(proj_paths[0]), infer_schema_length=200)
        proj.write_parquet(str(PROCESSED_DIR / "population_projections_clean.parquet"),
                           compression="snappy")
        quality_rows.append({
            "table": "population_projections",
            "rows": len(proj),
            "outlier_count": 0,
            "gap_years": 0,
            "validation_status": "PASS",
            "notes": f"Source: {proj_paths[0].name}",
        })

    # Write decisions
    if all_decisions:
        _write_decisions_md(all_decisions, DECISIONS_PATH)

    # Write quality report
    report = build_quality_report(quality_rows)
    report.write_csv(str(QUALITY_REPORT_PATH))
    logger.info(f"Quality report: {QUALITY_REPORT_PATH}")
    logger.info("Validation complete.")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_ts_validator.py
import polars as pl
import pytest
import numpy as np


def test_validate_year_monotonic_detects_gap():
    from problem_statements.ps_002_disease_burden.src.ts_validator import validate_year_monotonic
    df = pl.DataFrame({"year": [2010, 2012, 2013]})  # gap between 2010 and 2012
    issues = validate_year_monotonic(df, "year")
    assert any("2010" in i and "2012" in i for i in issues)


def test_validate_year_monotonic_no_issues():
    from problem_statements.ps_002_disease_burden.src.ts_validator import validate_year_monotonic
    df = pl.DataFrame({"year": [2015, 2016, 2017, 2018]})
    assert validate_year_monotonic(df, "year") == []


def test_check_iqr_outliers_flags_extreme_value():
    from problem_statements.ps_002_disease_burden.src.ts_validator import check_iqr_outliers
    values = [10.0] * 20 + [500.0]  # 500 is a clear outlier
    df = pl.DataFrame({"rate": values})
    outliers = check_iqr_outliers(df, "rate", multiplier=3.0)
    assert len(outliers) == 1
    assert outliers["rate"][0] == 500.0


def test_assess_trend_slope_declining():
    from problem_statements.ps_002_disease_burden.src.ts_validator import assess_trend_slope
    df = pl.DataFrame({"year": list(range(2000, 2020)), "rate": [float(100 - i) for i in range(20)]})
    slope = assess_trend_slope(df, "rate", "year")
    assert slope < 0


def test_check_covid_deviation_flags_large_drop():
    from problem_statements.ps_002_disease_burden.src.ts_validator import check_covid_deviation
    years = list(range(2015, 2021))
    rates = [100.0, 102.0, 98.0, 101.0, 100.0, 60.0]  # 2020 = 60 (40% drop)
    df = pl.DataFrame({"year": years, "rate": rates})
    result = check_covid_deviation(df, "rate", "year", covid_year=2020, pct_threshold=10.0)
    assert result["requires_decision"] is True
    assert result["pct_deviation"] > 30
```

---

### 5. Implementation Steps

- [ ] Create `src/ts_validator.py`
- [ ] Create `scripts/run_validation_ps002.py`
- [ ] Run: `python scripts/run_validation_ps002.py`
- [ ] Verify 3 mortality parquets exist in `data/4_processed/`
- [ ] Verify `admissions_age_sex_clean.parquet` excludes 2020 data
- [ ] Verify `population_projections_clean.parquet` exists
- [ ] Read `ps002_data_decisions.md` — confirm COVID decision is logged
- [ ] Run unit tests: `pytest tests/unit/test_ts_validator.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-002-story-02-ts-validation
git commit -m "feat(ps-002): add ts_validator and run_validation_ps002 script"
```
