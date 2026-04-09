# Extract Demographic Health Utilization & Outcome Data (Lifecycle Stage: Data Extraction)

**Story ID**: PS-005-US-01  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P0 (Critical)  
**Effort Estimate**: S (2 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Data Engineer supporting health equity analysis**,  
I want **to extract utilization and outcome data stratified by demographics (age, sex, ethnicity if available) from the Kaggle dataset**,  
So that **population health strategists have verified demographic health data for disparity analysis and equity assessments**.

---

## 🎯 Acceptance Criteria

1. **Demographic utilization data extracted**
   - Downloaded: `hospital-admission-rate-by-age-and-sex.csv` (216 records)
   - Demographic stratifications preserved: age groups, sex
   - Stored in `shared/data/1_raw/equity/utilization/`

2. **Health outcome data extracted**
   - Mortality data by demographics (if available with demographic breakdowns)
   - Disease burden data by demographics
   - Stored in `shared/data/1_raw/equity/outcomes/`

3. **Data validation passed**
   - Schema validation: demographic columns present
   - Completeness: 0% missing values
   - Demographic categories validated: age groups, sex categories consistent
   - Time coverage: 2006-2020

4. **Extraction documented**
   - Validation log: `logs/etl/equity_extraction_YYYYMMDD.log`
   - Schema: `shared/data/schemas/equity_raw_schema.yml`
   - Test coverage: ≥80%

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9
- **Primary Library**: Polars 0.20+ (MANDATORY)
- **Extraction Method**: KaggleHub API
- **Logging**: loguru
- **Testing**: pytest ≥80% coverage

---

## 📚 Domain Knowledge References

- [Domain Knowledge Research](../../../problem_statements/DOMAIN_KNOWLEDGE_RESEARCH.md#health-equity-metrics) - Equity and disparity metrics
- [Data Sources](../../../../project_context/data-sources.md#healthcare-utilization) - Demographic health data specifications

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`, `pydantic>=2.5.0`, `kagglehub>=0.2.0`, `loguru>=0.7.0`, `pyyaml>=6.0`

### Internal Dependencies
- **Upstream**: None (first story in epic)
- **Data Sources**: Kaggle dataset
- **Config Files**: `config/databricks.yml`, `shared/config/base.yml`

---

## ✅ Implementation Tasks

### Data Extraction
- [ ] Configure KaggleHub authentication
- [ ] Create extraction script: `shared/src/data_processing/extract_equity_data.py`
- [ ] Extract hospital admission rate by age and sex
- [ ] Extract mortality data with demographic breakdowns (if available)
- [ ] Save to appropriate directories

### Validation
- [ ] Define schemas for demographic health data
- [ ] Validate demographic stratifications present
- [ ] Validate completeness
- [ ] Validate value ranges

### Testing & Documentation
- [ ] Unit tests
- [ ] Integration tests
- [ ] Docstrings
- [ ] Update README

---

## 📌 Notes

**Expected Tables**:
- `hospital-admission-rate-by-age-and-sex.csv` (216 records, 2006-2020)
- Potentially: disease-specific mortality by demographics

**Polars Extraction**:
```python
import polars as pl
from loguru import logger
import kagglehub

dataset_path = kagglehub.dataset_download(
    "subhamjain/health-dataset-complete-singapore"
)

df_admissions = pl.read_csv(
    f"{dataset_path}/hospital-admission-rate-by-age-and-sex/hospital-admission-rate-by-age-and-sex.csv"
)

assert df_admissions.null_count().sum_horizontal()[0] == 0
logger.info(f"✓ Demographic admissions extracted: {len(df_admissions)} records")
```

---

## Implementation Plan

### 1. Feature Overview

Extract two demographic-stratified health datasets from the Kaggle Singapore Health Dataset: hospital admission rates by age and sex (the primary utilisation equity signal), plus available mortality tables with demographic breakdowns. All data is stored in the raw layer for downstream equity analysis.

**Primary User Role**: Data Engineer supporting health equity analysis

**Key Deliverable**: `shared/data/1_raw/equity/` directory containing validated demographic health CSVs covering 2006–2020, with an extraction log and schema YAML.

---

### 2. Component Analysis & Reuse Strategy

| Component | Location | Action | Justification |
|-----------|----------|--------|---------------|
| `kaggle_extractor.py` | `shared/src/data_processing/` | Reuse | Already implements KaggleHub download with retry |
| `validation.py` | `shared/src/data_processing/` | Reuse | `validate_schema`, `null_rate_report`, `write_quality_report` |
| `config.py` (utils) | `shared/src/utils/` | Reuse | `load_config`, `setup_logger` |
| `shared/config/base.yml` | `shared/config/` | Reuse | Project root paths, logging config |
| `equity_extractor.py` | `problem-statements/ps-005-healthcare-equity-disparities/src/` | **Create** | Equity-specific table selection and path mapping |
| `equity_raw_schema.yml` | `shared/data/schemas/` | **Create** | Schema validation for equity tables |
| `test_equity_extractor.py` | `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/` | **Create** | ≥80% coverage requirement |

---

### 3. ML Model Evaluation & Selection

Not applicable — this is a data extraction story.

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/src/equity_extractor.py`**
  - Functions: `extract_equity_tables(output_dir: Path) -> dict[str, pl.DataFrame]`, `validate_demographic_columns(df: pl.DataFrame, expected_cols: list[str]) -> bool`
  - Dependencies: `polars`, `kagglehub`, `loguru`, `pathlib`
  - Config: `shared/config/base.yml`
  - Logging: `logs/etl/equity_extraction_{timestamp}.log`

- **[CREATE] `shared/data/schemas/equity_raw_schema.yml`**
  - Defines required columns, expected dtypes, year range constraints

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_extractor.py`**
  - Tests schema validation and demographic column detection

---

### 5. Data Pipeline

**Source**: `subhamjain/health-dataset-complete-singapore` via `kagglehub.dataset_download()`

**Tables**:
| File | Records | Demographic Cols | Period |
|------|---------|-----------------|--------|
| `hospital-admission-rate-by-age-and-sex.csv` | 216 | `age_group`, `sex` | 2006–2020 |
| `age-standardised-mortality-rate-for-cancer.csv` | 30 | `sex` (if split) | 1990–2019 |
| `age-standardised-mortality-rate-for-stroke.csv` | 30 | `sex` (if split) | 1990–2019 |

**Extraction flow**:
1. Authenticate via `~/.kaggle/kaggle.json` or env vars
2. `kagglehub.dataset_download()` → local cache
3. Locate equity-relevant tables using path mapping
4. Load each CSV with `pl.read_csv()` + schema enforcement
5. Validate demographic columns present and non-null
6. Write to `shared/data/1_raw/equity/utilization/` and `shared/data/1_raw/equity/outcomes/`
7. Write quality report to `logs/etl/equity_extraction_{timestamp}.log`

**Error handling**: Authentication failures raise `RuntimeError` with guidance; missing tables log a warning and continue; schema failures raise `ValueError`.

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/src/equity_extractor.py

from pathlib import Path
from datetime import datetime
from typing import Optional

import polars as pl
import kagglehub
from loguru import logger


DATASET_ID = "subhamjain/health-dataset-complete-singapore"

EQUITY_TABLE_MAP: dict[str, str] = {
    "admissions_by_age_sex": (
        "hospital-admission-rate-by-age-and-sex/"
        "hospital-admission-rate-by-age-and-sex.csv"
    ),
    "mortality_cancer": (
        "age-standardised-mortality-rate-for-cancer/"
        "age-standardised-mortality-rate-for-cancer.csv"
    ),
    "mortality_stroke": (
        "age-standardised-mortality-rate-for-stroke/"
        "age-standardised-mortality-rate-for-stroke.csv"
    ),
    "mortality_ihd": (
        "age-standardised-mortality-rate-for-ischaemic-heart-disease/"
        "age-standardised-mortality-rate-for-ischaemic-heart-disease.csv"
    ),
}


def _setup_logging(log_dir: str = "logs/etl") -> None:
    """Configure loguru for equity extraction."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(
        Path(log_dir) / f"equity_extraction_{ts}.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO",
    )


def validate_demographic_columns(
    df: pl.DataFrame,
    expected_cols: list[str],
) -> bool:
    """
    Validate that required demographic columns are present.

    Args:
        df: DataFrame to validate.
        expected_cols: List of required column names.

    Returns:
        True if all columns present and non-empty.

    Raises:
        ValueError: If any expected column is missing.
    """
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing demographic columns: {missing}")
    null_counts = df.select([pl.col(c).null_count().alias(c) for c in expected_cols])
    for col in expected_cols:
        nulls = null_counts[col][0]
        if nulls > 0:
            logger.warning(f"Column '{col}' has {nulls} nulls")
    logger.info(f"Demographic columns validated: {expected_cols}")
    return True


def extract_equity_tables(
    output_dir: Path,
    log_dir: str = "logs/etl",
) -> dict[str, pl.DataFrame]:
    """
    Download and extract equity-relevant tables from Kaggle dataset.

    Args:
        output_dir: Root directory for raw equity data outputs.
        log_dir: Directory for extraction logs.

    Returns:
        Dict mapping table name to loaded pl.DataFrame.

    Raises:
        RuntimeError: If Kaggle download fails.
        ValueError: On schema or demographic column validation failure.
    """
    _setup_logging(log_dir)
    logger.info(f"Starting equity data extraction → {output_dir}")

    try:
        dataset_path = Path(kagglehub.dataset_download(DATASET_ID))
    except Exception as exc:
        logger.error(f"Kaggle download failed: {exc}")
        raise RuntimeError(
            "Ensure ~/.kaggle/kaggle.json exists or KAGGLE_USERNAME/"
            "KAGGLE_KEY env vars are set."
        ) from exc

    utilization_dir = output_dir / "utilization"
    outcomes_dir = output_dir / "outcomes"
    utilization_dir.mkdir(parents=True, exist_ok=True)
    outcomes_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, pl.DataFrame] = {}

    for table_key, rel_path in EQUITY_TABLE_MAP.items():
        src = dataset_path / rel_path
        if not src.exists():
            logger.warning(f"Table not found, skipping: {src}")
            continue

        df = pl.read_csv(src, infer_schema_length=1000)
        # Normalise column names: lowercase, strip whitespace, replace spaces with _
        df = df.rename({c: c.strip().lower().replace(" ", "_") for c in df.columns})

        # Year validation
        if "year" in df.columns:
            df = df.with_columns(pl.col("year").cast(pl.Int32))

        # Demographic validation
        if table_key == "admissions_by_age_sex":
            validate_demographic_columns(df, ["year", "age_group", "sex"])
            dest = utilization_dir / f"{table_key}.csv"
        else:
            validate_demographic_columns(df, ["year"])
            dest = outcomes_dir / f"{table_key}.csv"

        df.write_csv(dest)
        logger.info(f"✓ {table_key}: {df.shape[0]} rows → {dest}")
        results[table_key] = df

    logger.info(f"Extraction complete: {len(results)} tables extracted")
    return results
```

#### 6.2 Data Schema

```yaml
# shared/data/schemas/equity_raw_schema.yml
admissions_by_age_sex:
  required_columns: [year, age_group, sex, admission_rate]
  column_types:
    year: Int32
    age_group: Categorical
    sex: Categorical
    admission_rate: Float64
  constraints:
    year_range: [2006, 2020]
    admission_rate_min: 0
equity_mortality:
  required_columns: [year, mortality_rate]
  column_types:
    year: Int32
    mortality_rate: Float64
  constraints:
    year_range: [1990, 2019]
```

#### 6.3 Data Validation

```python
import polars as pl
from loguru import logger


def profile_equity_dataframe(df: pl.DataFrame, name: str) -> dict[str, object]:
    """Generate data quality profile for equity extraction validation."""
    n_rows, n_cols = df.shape
    null_pct = (df.null_count() / n_rows * 100).to_dicts()[0]
    dupes = int(df.is_duplicated().sum())

    profile = {
        "table": name,
        "shape": (n_rows, n_cols),
        "null_percentages": null_pct,
        "duplicate_rows": dupes,
        "duplicate_pct": round(dupes / n_rows * 100, 2),
    }
    logger.info(f"{name}: {n_rows} rows, {dupes} dupes, nulls={null_pct}")
    return profile
```

#### 6.4 Library Patterns

```python
# Categorical dtype optimisation for low-cardinality demographic columns
df = df.with_columns([
    pl.col("age_group").cast(pl.Categorical),
    pl.col("sex").cast(pl.Categorical),
])

# Year range filter
df_filtered = df.filter(pl.col("year").is_between(2006, 2020))
```

#### 6.6 Package Management

```bash
uv pip install polars>=0.20.0 kagglehub>=0.2.0 loguru>=0.7.0 pyyaml>=6.0
uv pip freeze > requirements.txt
```

---

### 7. Domain-Driven Feature Engineering

**Step 1 — Relevant domain knowledge**: `docs/domain-knowledge/health-equity-metrics-kpis.md`
- Key fields: `year`, `age_group`, `sex`, `admission_rate`
- Reference population: overall (all-cause) rate for rate-ratio denominator

**Step 2 — Data availability**:
| Feature | Source Field | Available |
|---------|-------------|----------|
| Age group stratification | `age_group` in admissions CSV | ✅ |
| Sex stratification | `sex` in admissions CSV | ✅ |
| Temporal coverage 2006–2020 | `year` column | ✅ |
| SES / ethnicity | Not in dataset | ❌ — excluded |

**Step 3 — Selected features**: `year`, `age_group`, `sex`, `admission_rate` — all directly available; no derived features at extraction stage.

---

### 10. Testing Strategy

**Unit Tests** (`problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_extractor.py`)

```python
import polars as pl
import pytest
from problem_statements.ps_005.src.equity_extractor import validate_demographic_columns


def test_validate_demographic_columns_passes():
    df = pl.DataFrame({"year": [2010], "age_group": ["25-34"], "sex": ["Male"]})
    assert validate_demographic_columns(df, ["year", "age_group", "sex"]) is True


def test_validate_demographic_columns_raises_on_missing():
    df = pl.DataFrame({"year": [2010]})
    with pytest.raises(ValueError, match="Missing demographic columns"):
        validate_demographic_columns(df, ["year", "age_group", "sex"])


def test_profile_equity_dataframe_no_nulls():
    df = pl.DataFrame({"year": [2010, 2011], "admission_rate": [120.5, 130.2]})
    from problem_statements.ps_005.src.equity_extractor import profile_equity_dataframe
    profile = profile_equity_dataframe(df, "test")
    assert profile["shape"] == (2, 2)
    assert profile["duplicate_rows"] == 0
```

**Data Quality Tests**
- Schema: year Int32, age_group Categorical, sex Categorical
- Completeness: 0% nulls in required columns
- Year range: 2006–2020 for admissions
- Demographic values: sex ∈ {"Male", "Female"} or equivalent normalised forms
- Row count: admissions CSV should have ≥100 records across years

---

### 11. Implementation Steps

**Phase 1 — Data Extraction**
- [ ] Confirm `~/.kaggle/kaggle.json` or env vars `KAGGLE_USERNAME` / `KAGGLE_KEY` are set
- [ ] Run `extract_equity_tables(Path("shared/data/1_raw/equity"))` and verify file writes
- [ ] Inspect actual column names in `hospital-admission-rate-by-age-and-sex.csv` and update `EQUITY_TABLE_MAP` if needed
- [ ] Run `profile_equity_dataframe()` on each extracted table
- [ ] Write `shared/data/schemas/equity_raw_schema.yml`

**Phase 2 — Validation**
- [ ] Check age group categories are consistent across years
- [ ] Verify sex categories: normalise to `["Male", "Female"]`
- [ ] Verify 0% nulls in `year`, `age_group`, `sex`, rate column
- [ ] Verify year range 2006–2020

**Phase 3 — Testing & Documentation**
- [ ] Write and run unit tests (target ≥80% coverage)
- [ ] Update README in `problem-statements/ps-005-healthcare-equity-disparities/`
- [ ] Confirm extraction log exists at `logs/etl/equity_extraction_*.log`

---

### 12. Adaptive Implementation Strategy

After running extraction:
- If column names differ from expected → update rename mapping and schema YAML before proceeding
- If admission data has `sex` column with values other than Male/Female → add normalisation step in US-02
- If mortality tables have no demographic breakdown → document limitation and exclude from disparity analysis; only admissions data can be used
- If row count < 100 for admissions → flag data freshness issue and check dataset version

---

### 13. Code Generation Order

1. `shared/data/schemas/equity_raw_schema.yml` (schema definition)
2. `problem-statements/ps-005-healthcare-equity-disparities/src/equity_extractor.py` (core extraction)
3. `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_extractor.py` (tests)
4. Run extraction script, inspect outputs
5. Update YAML schema with actual column names discovered

---

### 14. Data Quality & Validation

| Check | Expected | Action on Failure |
|-------|----------|------------------|
| Null rate in key columns | 0% | Raise error, do not proceed |
| Year range (admissions) | 2006–2020 | Log warning, clip out-of-range rows |
| Duplicate rows | 0 | Log and deduplicate before saving |
| Sex cardinality | 2 (Male/Female) | Log unexpected values for manual review |
| Age group cardinality | 5–10 distinct groups | Log if fewer than 4 groups |

---

### 18. Success Metrics & Monitoring

- **Extraction success**: All expected tables present in `shared/data/1_raw/equity/`
- **Data completeness**: 0% nulls in demographic columns
- **Validation pass**: Schema YAML enforced without errors
- **Test coverage**: ≥80% as measured by `pytest --cov`
- **Log artefact**: `logs/etl/equity_extraction_*.log` created with record counts

---

### 19. References

- [health-equity-metrics-kpis.md](../../../../domain-knowledge/health-equity-metrics-kpis.md)
- [data-sources.md](../../../../project-context/data-sources.md)
- [ps-005-healthcare-equity-disparities.md](../../../problem_statements/ps-005-healthcare-equity-disparities.md)
- [shared/src/data_processing/kaggle_extractor.py](../../../../../../shared/src/data_processing/kaggle_extractor.py)

---

### 20. Security & Privacy

**PII/PHI Assessment**: The extracted dataset contains exclusively **aggregated population statistics** (rates per 1,000 or per 100,000 population). No individual-level records exist. No PII/PHI handling is required.

**Credential management**:
- Kaggle credentials via `~/.kaggle/kaggle.json` or `.env` file (`KAGGLE_USERNAME`, `KAGGLE_KEY`)
- `.env` is in `.gitignore` — never commit
- Rotate Kaggle API keys via `kaggle.com/account` if compromised

**Data retention**: Raw CSVs stored in `shared/data/1_raw/equity/` — excluded from version control via `.gitignore`.

---

### 21. Version Control

- Branch: `feature/ps-005-equity-data-extraction`
- Commits:
  - `feat(ps-005): add equity extractor with admission-by-age-sex support`
  - `test(ps-005): add unit tests for equity_extractor validate_demographic_columns`
  - `docs(ps-005): update equity raw schema YAML`
- Pre-merge: `pytest --cov ≥80%`, `ruff check .`, schema YAML validated

---

### 23. Quality Metrics

**Self-assessment**:
- [x] All file paths reference actual project locations
- [x] All functions fully implemented (no stubs)
- [x] All code blocks have imports and error handling
- [x] Test assertions with expected values included
- [x] Domain features mapped to data sources
- [x] Security requirements addressed
- [x] Data constraints (age/sex only, no SES) documented
