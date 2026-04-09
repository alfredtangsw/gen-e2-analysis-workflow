# Prepare & Integrate Equity Analysis Datasets (Lifecycle Stage: Data Preparation)

**Story ID**: PS-005-US-02  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P0 (Critical)  
**Effort Estimate**: M (4 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Data Engineer preparing health equity datasets**,  
I want **to integrate and standardize demographic health data with consistent demographic categorizations and unified schemas**,  
So that **equity analysts can perform disparity assessments comparing utilization and outcomes across demographic groups**.

---

## 🎯 Acceptance Criteria

1. **Schema standardization**
   - Unified schema: `year`, `demographic_group`, `age_group`, `sex`, `metric_type`, `metric_value`
   - Demographic categories standardized
   - Data types enforced

2. **Data integration**
   - Utilization and outcome data integrated
   - Common demographic groups aligned
   - Time periods aligned

3. **Derived metrics**
   - Rate ratios: high-use group / low-use group
   - Disparity indices calculated
   - Reference group defined (e.g., overall population average)

4. **Output**
   - Integrated: `shared/data/3_interim/equity_analysis_integrated.parquet`
   - Schema: `shared/data/schemas/equity_integrated_schema.yml`
   - Test coverage: ≥80%

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9
- **Primary Library**: Polars 0.20+
- **Logging**: loguru
- **Testing**: pytest ≥80% coverage

---

## 📚 Domain Knowledge References

- [Domain Knowledge Research](../../../problem_statements/DOMAIN_KNOWLEDGE_RESEARCH.md#equity-analysis-methods)
- [Problem Statement PS-005](../../../problem_statements/ps-005-healthcare-equity-disparities.md#objective-1)

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`, `pydantic>=2.5.0`, `loguru>=0.7.0`

### Internal Dependencies
- **Upstream**: PS-005-US-01 (Extract equity data - BLOCKING)
- **Data Sources**: `shared/data/1_raw/equity/**/*.csv`

---

## ✅ Implementation Tasks

### Schema Standardization
- [ ] Define unified demographic schema
- [ ] Standardize age group categories
- [ ] Standardize sex categories
- [ ] Map source data to standard schema

### Data Integration
- [ ] Load all demographic health datasets
- [ ] Align demographic categories
- [ ] Join utilization and outcome data
- [ ] Handle missing demographic combinations

### Derived Metrics
- [ ] Calculate reference group averages
- [ ] Calculate rate ratios for each demographic
- [ ] Compute absolute disparities
- [ ] Flag significant disparities

### Testing & Documentation
- [ ] Unit tests
- [ ] Validation tests
- [ ] Docstrings

---

## 📌 Notes

**Polars Integration**:
```python
import polars as pl

df_util = pl.read_csv("shared/data/1_raw/equity/utilization/admissions.csv")

# Calculate rate ratios
df_equity = (
    df_util.with_columns([
        pl.col('admission_rate').mean().alias('reference_rate')
    ])
    .with_columns([
        (pl.col('admission_rate') / pl.col('reference_rate')).alias('rate_ratio')
    ])
)

# Flag disparities (rate ratio >1.5 or <0.67)
df_equity = df_equity.with_columns([
    ((pl.col('rate_ratio') > 1.5) | (pl.col('rate_ratio') < 0.67)).alias('disparity_flag')
])
```

---

## Implementation Plan

### 1. Feature Overview

Integrate the extracted demographic health utilisation and outcome data into a single standardised Polars DataFrame with a unified schema. Compute derived equity metrics (rate ratios, absolute disparities, disparity flags) ready for statistical analysis in US-03 through US-08.

**Primary User Role**: Data Engineer preparing health equity datasets

**Key Deliverable**: `shared/data/3_interim/equity_analysis_integrated.parquet` with unified `[year, demographic_type, demographic_group, metric_type, metric_value, reference_value, rate_ratio, absolute_disparity, disparity_flag]` schema.

---

### 2. Component Analysis & Reuse Strategy

| Component | Location | Action | Justification |
|-----------|----------|--------|---------------|
| Extraction outputs | `shared/data/1_raw/equity/` | Reuse | Direct upstream dependency (US-01) |
| `validation.py` | `shared/src/data_processing/` | Reuse | `null_rate_report`, `validate_schema` |
| `equity_extractor.py` | `ps-005/src/` | Reuse | Import constants for column names |
| `equity_preparation.py` | `ps-005/src/` | **Create** | Standardisation, integration, derived metrics |
| `equity_integrated_schema.yml` | `shared/data/schemas/` | **Create** | Schema for interim output |
| `test_equity_preparation.py` | `ps-005/tests/unit/` | **Create** | ≥80% coverage |

---

### 3. ML Model Evaluation & Selection

Not applicable — this is a data preparation story.

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/src/equity_preparation.py`**
  - Functions: `standardise_admissions(df: pl.DataFrame) -> pl.DataFrame`, `compute_rate_ratios(df: pl.DataFrame, ref_group: str) -> pl.DataFrame`, `integrate_equity_datasets(utilization_dir: Path, output_path: Path) -> pl.DataFrame`
  - Dependencies: `polars`, `loguru`, `pathlib`
  - Config: `shared/config/base.yml`
  - Logging: `logs/etl/equity_preparation_{timestamp}.log`

- **[CREATE] `shared/data/schemas/equity_integrated_schema.yml`**
  - Defines unified schema, accepted demographic values, rate_ratio ranges

- **[MODIFY] `problem-statements/ps-005-healthcare-equity-disparities/src/equity_extractor.py`**
  - Export column name constants for reuse by preparation module

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_preparation.py`**
  - Tests for standardise_admissions, compute_rate_ratios, disparity flagging

---

### 5. Data Pipeline

**Inputs**: `shared/data/1_raw/equity/utilization/admissions_by_age_sex.csv`

**Transformations**:
1. Load admissions CSV with `pl.read_csv()`
2. Normalise column names (lowercase, strip)
3. Cast: `year → Int32`, `age_group → Categorical`, `sex → Categorical`, rate column → `Float64`
4. Compute reference group values (overall average or reference demographic)
5. Compute rate ratios: `rate / reference_rate`
6. Compute absolute disparities: `rate - reference_rate`
7. Flag significant disparities: `rate_ratio > 1.5 OR rate_ratio < 0.67`
8. Write to `shared/data/3_interim/equity_analysis_integrated.parquet`

**Output schema**:
```
year             Int32
demographic_type  Categorical  ("age_group" | "sex")
demographic_group Categorical  (e.g. "25-34", "65+", "Male")
metric_type      Categorical  ("admission_rate")
metric_value     Float64
reference_value  Float64
rate_ratio       Float64
absolute_disparity Float64
disparity_flag   Boolean
```

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/src/equity_preparation.py

from pathlib import Path
from datetime import datetime

import polars as pl
from loguru import logger


# Reference groups for rate ratio denominator
AGE_REFERENCE_GROUP = "25-44 years"   # Lowest-risk age band; adjust if actual label differs
SEX_REFERENCE_GROUP = "Male"           # Standard epidemiological reference


def _setup_logging(log_dir: str = "logs/etl") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(
        Path(log_dir) / f"equity_preparation_{ts}.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO",
    )


def standardise_admissions(df: pl.DataFrame) -> pl.DataFrame:
    """
    Normalise the raw admissions-by-age-and-sex table into a long format
    with consistent column names and types.

    Args:
        df: Raw admissions DataFrame (from 1_raw/equity/utilization/).

    Returns:
        Long-format DataFrame with columns:
        [year, demographic_type, demographic_group, metric_type, metric_value]
    """
    df = df.rename({c: c.strip().lower().replace(" ", "_") for c in df.columns})
    df = df.with_columns(pl.col("year").cast(pl.Int32))

    # Detect rate column (the numeric non-year, non-demographic column)
    dim_cols = ["year", "age_group", "sex"]
    rate_cols = [c for c in df.columns if c not in dim_cols]
    if len(rate_cols) != 1:
        logger.warning(f"Expected 1 rate column, found: {rate_cols}")
    rate_col = rate_cols[0] if rate_cols else "admission_rate"

    df = df.rename({rate_col: "metric_value"})
    df = df.with_columns(pl.col("metric_value").cast(pl.Float64))

    # Produce two long-format views: one per demographic dimension
    frames = []
    for dem_type, dem_col in [("age_group", "age_group"), ("sex", "sex")]:
        if dem_col not in df.columns:
            logger.warning(f"Column '{dem_col}' not found, skipping")
            continue
        frame = df.select(["year", dem_col, "metric_value"]).rename({dem_col: "demographic_group"})
        frame = frame.with_columns([
            pl.lit(dem_type).cast(pl.Categorical).alias("demographic_type"),
            pl.lit("admission_rate").cast(pl.Categorical).alias("metric_type"),
            pl.col("demographic_group").cast(pl.Categorical),
        ])
        frames.append(frame)

    result = pl.concat(frames)
    logger.info(f"Standardised admissions: {result.shape[0]} long-format rows")
    return result


def compute_rate_ratios(
    df: pl.DataFrame,
    ref_group_by_type: dict[str, str] | None = None,
) -> pl.DataFrame:
    """
    Compute rate ratios and absolute disparities relative to reference groups.

    Args:
        df: Long-format standardised DataFrame with [year, demographic_type,
            demographic_group, metric_type, metric_value].
        ref_group_by_type: Mapping from demographic_type to reference group label.
            Defaults to {"age_group": AGE_REFERENCE_GROUP, "sex": SEX_REFERENCE_GROUP}.

    Returns:
        DataFrame with added columns: reference_value, rate_ratio,
        absolute_disparity, disparity_flag.
    """
    if ref_group_by_type is None:
        ref_group_by_type = {
            "age_group": AGE_REFERENCE_GROUP,
            "sex": SEX_REFERENCE_GROUP,
        }

    result_frames = []
    for dem_type, ref_group in ref_group_by_type.items():
        subset = df.filter(pl.col("demographic_type") == dem_type)
        if subset.is_empty():
            continue

        # Reference values per year
        ref_vals = (
            subset
            .filter(pl.col("demographic_group") == ref_group)
            .select(["year", "metric_type", "metric_value"])
            .rename({"metric_value": "reference_value"})
        )

        if ref_vals.is_empty():
            # Fall back to overall average if reference group not found
            logger.warning(
                f"Reference group '{ref_group}' not found for {dem_type}; "
                f"using annual mean as reference"
            )
            ref_vals = (
                subset
                .group_by(["year", "metric_type"])
                .agg(pl.col("metric_value").mean().alias("reference_value"))
            )

        merged = subset.join(ref_vals, on=["year", "metric_type"], how="left")
        merged = merged.with_columns([
            (pl.col("metric_value") / pl.col("reference_value")).alias("rate_ratio"),
            (pl.col("metric_value") - pl.col("reference_value")).alias("absolute_disparity"),
        ])
        merged = merged.with_columns(
            ((pl.col("rate_ratio") > 1.5) | (pl.col("rate_ratio") < 0.67))
            .alias("disparity_flag")
        )
        result_frames.append(merged)

    if not result_frames:
        raise ValueError("No demographic types processed; check input DataFrame")

    combined = pl.concat(result_frames)
    logger.info(
        f"Rate ratios computed: {combined.shape[0]} rows, "
        f"{combined['disparity_flag'].sum()} flagged disparities"
    )
    return combined


def integrate_equity_datasets(
    utilization_dir: Path,
    output_path: Path,
) -> pl.DataFrame:
    """
    Orchestrate loading, standardisation, rate ratio computation, and saving.

    Args:
        utilization_dir: Directory containing raw equity utilization CSVs.
        output_path: Destination path for integrated parquet file.

    Returns:
        Integrated equity DataFrame.
    """
    _setup_logging()
    logger.info(f"Integrating equity datasets from {utilization_dir}")

    admissions_path = utilization_dir / "admissions_by_age_sex.csv"
    if not admissions_path.exists():
        raise FileNotFoundError(
            f"Admissions file not found: {admissions_path}. Run US-01 extraction first."
        )

    raw_df = pl.read_csv(admissions_path)
    long_df = standardise_admissions(raw_df)
    equity_df = compute_rate_ratios(long_df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    equity_df.write_parquet(output_path)
    logger.info(f"✓ Integrated dataset saved: {output_path} ({equity_df.shape[0]} rows)")
    return equity_df
```

#### 6.2 Data Schema

```yaml
# shared/data/schemas/equity_integrated_schema.yml
equity_analysis_integrated:
  required_columns:
    - year
    - demographic_type
    - demographic_group
    - metric_type
    - metric_value
    - reference_value
    - rate_ratio
    - absolute_disparity
    - disparity_flag
  column_types:
    year: Int32
    demographic_type: Categorical
    demographic_group: Categorical
    metric_type: Categorical
    metric_value: Float64
    reference_value: Float64
    rate_ratio: Float64
    absolute_disparity: Float64
    disparity_flag: Boolean
  constraints:
    rate_ratio_positive: true
    year_range: [2006, 2020]
```

#### 6.3 Data Validation

```python
import polars as pl
from loguru import logger


def validate_integrated_equity(df: pl.DataFrame) -> bool:
    """Validate integrated equity DataFrame before downstream analysis."""
    required = [
        "year", "demographic_type", "demographic_group",
        "metric_type", "metric_value", "reference_value",
        "rate_ratio", "absolute_disparity", "disparity_flag",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    null_pct = (df.null_count() / df.shape[0] * 100).to_dicts()[0]
    critical_nulls = {k: v for k, v in null_pct.items() if k in required and v > 0}
    if critical_nulls:
        logger.error(f"Nulls in critical columns: {critical_nulls}")
        raise ValueError("Null values found in required columns")

    neg_ratios = df.filter(pl.col("rate_ratio") < 0).shape[0]
    if neg_ratios > 0:
        logger.warning(f"{neg_ratios} negative rate ratios detected")

    logger.info(f"Validation passed: {df.shape[0]} rows, 0 critical nulls")
    return True
```

---

### 7. Domain-Driven Feature Engineering

**Step 1 — Domain knowledge**: Disparity Ratio (Rate Ratio) and Absolute Disparity defined in `health-equity-metrics-kpis.md`

**Step 2 — Data availability**:
| Feature | Available | Notes |
|---------|-----------|-------|
| Age disparity ratio | ✅ | `rate_age_i / rate_ref_age` |
| Sex disparity ratio | ✅ | `rate_female / rate_male` |
| Absolute disparity | ✅ | `rate_i - rate_ref` |
| SES disparity ratio | ❌ | Dataset has no SES data |
| Ethnicity ratio | ❌ | Not in dataset |

**Step 3 — Disparity flag thresholds** (from domain knowledge):
- `rate_ratio > 1.5` → high utilisation disparity (potential overuse or elevated need)
- `rate_ratio < 0.67` → low utilisation disparity (potential access barrier)

---

### 10. Testing Strategy

```python
# problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_preparation.py

import polars as pl
import pytest
from problem_statements.ps_005.src.equity_preparation import (
    standardise_admissions,
    compute_rate_ratios,
)


@pytest.fixture
def raw_admissions_df():
    return pl.DataFrame({
        "year": [2010, 2010, 2010, 2015, 2015, 2015],
        "age_group": ["25-44 years", "45-64 years", "65+ years"] * 2,
        "sex": ["Male", "Male", "Male", "Female", "Female", "Female"],
        "admission_rate": [100.0, 200.0, 500.0, 90.0, 210.0, 520.0],
    })


def test_standardise_admissions_produces_long_format(raw_admissions_df):
    result = standardise_admissions(raw_admissions_df)
    assert "demographic_type" in result.columns
    assert "demographic_group" in result.columns
    assert "metric_value" in result.columns
    assert result.shape[0] > raw_admissions_df.shape[0]  # Long format


def test_compute_rate_ratios_adds_required_columns(raw_admissions_df):
    long_df = standardise_admissions(raw_admissions_df)
    result = compute_rate_ratios(
        long_df,
        ref_group_by_type={"age_group": "25-44 years", "sex": "Male"},
    )
    for col in ["rate_ratio", "absolute_disparity", "disparity_flag"]:
        assert col in result.columns


def test_disparity_flag_set_for_high_ratio(raw_admissions_df):
    long_df = standardise_admissions(raw_admissions_df)
    result = compute_rate_ratios(
        long_df,
        ref_group_by_type={"age_group": "25-44 years", "sex": "Male"},
    )
    # 65+ / 25-44 = 500/100 = 5.0 >> 1.5, must be flagged
    elderly = result.filter(
        (pl.col("demographic_type") == "age_group")
        & (pl.col("demographic_group") == "65+ years")
        & (pl.col("year") == 2010)
    )
    assert elderly["disparity_flag"][0] is True
```

---

### 11. Implementation Steps

**Phase 1 — Schema Standardisation**
- [ ] Inspect actual column names in `admissions_by_age_sex.csv`; update rename mapping
- [ ] Identify exact age group labels (e.g. `"25-44 years"`, `"25-44"`) and update `AGE_REFERENCE_GROUP`
- [ ] Run `standardise_admissions()` and print schema + sample rows

**Phase 2 — Integration & Derived Metrics**
- [ ] Run `compute_rate_ratios()` with default reference groups
- [ ] Inspect output: confirm `rate_ratio` plausible (elderly >> 1.0, young ≈ 1.0)
- [ ] Check `disparity_flag` counts — expect flagged for elderly and possibly specific sex
- [ ] Write integrated parquet to `shared/data/3_interim/equity_analysis_integrated.parquet`

**Phase 3 — Validation & Testing**
- [ ] Run `validate_integrated_equity()` on output
- [ ] Run `pytest --cov` on `test_equity_preparation.py`
- [ ] Confirm schema YAML written to `shared/data/schemas/equity_integrated_schema.yml`

---

### 12. Adaptive Implementation Strategy

- If actual age group labels differ from `"25-44 years"` → update `AGE_REFERENCE_GROUP` constant dynamically from the data
- If `sex` column missing → reduce to age-only analysis; document limitation
- If reference group has zero values in some years → fall back to annual mean (already implemented)

---

### 14. Data Quality & Validation

| Check | Expected | Action |
|-------|----------|--------|
| Nulls in rate_ratio | 0% | Raise if > 0 |
| Negative rate values | 0 | Raise |
| Years present | 2006–2020 | Warn if any year missing |
| Unique demographic groups | ≥ 4 age groups, 2 sex | Warn if fewer |
| Parquet file size | > 5 KB | Warn if smaller (likely empty) |

---

### 20. Security & Privacy

All data is aggregated population statistics. No PII/PHI. Parquet stored in `shared/data/3_interim/` which is git-ignored via `.gitignore`.

---

### 21. Version Control

- Branch: `feature/ps-005-equity-data-preparation`
- Commits:
  - `feat(ps-005): add equity_preparation standardise and rate_ratio functions`
  - `test(ps-005): add unit tests for equity preparation with disparity flag checks`
