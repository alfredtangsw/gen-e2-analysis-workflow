# User Story: 4 — Feature Engineering for Time-Series Forecasting

**As a** healthcare forecasting engineer,  
**I want** to engineer temporal features from mortality and admissions data — including lag variables, rolling statistics, and growth acceleration metrics —  
**so that** the forecasting models have well-constructed inputs that capture trend momentum and seasonal structure.

## 1. 🎯 Acceptance Criteria

- Lag features created for each mortality series: `rate_lag1`, `rate_lag2`, `rate_lag3` (1-, 2-, 3-year lags)
- Rolling statistics created for each mortality series: `rate_rollmean3`, `rate_rollmean5`, `rate_rollstd3`
- Growth rate and acceleration features: `rate_yoy_pct = (rate / rate_lag1 - 1) * 100`, `rate_acceleration = rate_yoy_pct - shift(rate_yoy_pct, 1)`
- Admission index constructed: `admission_index = estimated_admissions / population * 10000` — expressed as a rate per 10k, segregated by age group
- Feature matrix for mortality forecasting saved to `data/4_processed/mortality_{disease}_features.parquet` for each disease
- Feature matrix for admissions saved to `data/4_processed/admissions_features.parquet`
- A feature importance note file saved to `results/tables/ps002_feature_notes.md` describing each feature and its modelling rationale

## 2. 🔒 Technical Constraints

- All features computed in Polars using `.with_columns()` chaining — no pandas for feature engineering
- Lag features: use `pl.col(...).shift(n)` where n is the number of years to lag
- Rolling statistics: use `pl.col(...).rolling_mean(window_size=n, min_periods=n)` — do not use partial windows
- Age-indexed admission features must preserve age group as a column (not row index) for downstream join compatibility
- Final feature frames must have no trailing nulls from lags in the last rows — document nulls created by lagging in the feature notes

## 3. 📚 Domain Knowledge References

- [Time-Series Forecasting Methods](../../../../domain-knowledge/time-series-forecasting-methods.md) — lag selection guidance, rolling window considerations
- [Disease Burden Feature Engineering Guide](../../../../domain-knowledge/disease-burden-feature-engineering-guide.md) — rate normalisation and index construction patterns

## 4. 📦 Dependencies

- Story 02 outputs: `mortality_*_clean.parquet`, `admissions_age_sex_clean.parquet`, `population_projections_clean.parquet`
- `polars` — all feature engineering

## 5. ✅ Implementation Tasks

**Mortality Feature Engineering**
- ⬜ For each disease (cancer, stroke, IHD):
  - Load clean parquet
  - Compute `rate_lag1`, `rate_lag2`, `rate_lag3` using `.shift()`
  - Compute `rate_rollmean3` (window=3), `rate_rollmean5` (window=5)
  - Compute `rate_rollstd3` (window=3)
  - Compute `rate_yoy_pct = (rate / rate_lag1 - 1) * 100`
  - Compute `rate_acceleration = rate_yoy_pct - rate_yoy_pct.shift(1)`
  - Save to `data/4_processed/mortality_{disease}_features.parquet`

**Admission Feature Engineering**
- ⬜ Load admissions by age/sex; compute `estimated_admissions = rate * population_by_age / rate_base`
- ⬜ Compute `admission_index = estimated_admissions / total_population * 10000`
- ⬜ Compute lag1 and rolling mean 3 for estimated admissions per age group
- ⬜ Save to `data/4_processed/admissions_features.parquet`

**Feature Notes**
- ⬜ Write `results/tables/ps002_feature_notes.md` with a table: `feature_name, type, formula, rationale, modelling_use`
- ⬜ Note which rows are NaN due to lag/window requirements and how models should handle these (drop rows with NaN before training)

**Logging**
- ⬜ Log feature shapes (rows × cols) and null counts per feature to `logs/etl/ps002_feature_engineering.log`

## 6. Notes

- Lag features are used as additional regressors in the Prophet model (external regressors argument). Ensure they are computed for both history and future periods.
- Rolling standard deviation (`rate_rollstd3`) captures volatility in the mortality trend — used to construct confidence interval context in Story 05.
- For ARIMA and Holt-Winters models in Story 05, only the raw cleaned rate series is required as input — the lag and rolling features primarily serve features-based models or Prophet.

---

## Implementation Plan

### 1. Feature Overview

Engineer lag, rolling, and acceleration features for each mortality series using Polars `.shift()` and `.rolling_mean()`. Build the admissions feature matrix with age-group indices. Save feature parquets and a feature notes markdown. Primary user: **PS-002 model engineer**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-002-disease-burden/src/feature_engineer.py
  - add_lag_features(df, value_col, lags) -> pl.DataFrame
  - add_rolling_features(df, value_col, windows) -> pl.DataFrame
  - add_yoy_acceleration(df, value_col) -> pl.DataFrame
  - build_mortality_features(disease, processed_dir) -> pl.DataFrame
  - build_admission_features(processed_dir) -> pl.DataFrame

[CREATE] problem-statements/ps-002-disease-burden/scripts/run_feature_engineering_ps002.py
  - Orchestrates feature building; saves parquets and feature notes
```

---

### 3. Code Generation Specifications

#### 3.1 `src/feature_engineer.py`

```python
"""PS-002 time-series feature engineering.

All transformations use Polars — no pandas usage for feature columns.
Lag/rolling features create null rows at the start of the series;
drop these before model training (document in feature_notes.md).
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


def add_lag_features(
    df: pl.DataFrame,
    value_col: str,
    lags: list[int],
) -> pl.DataFrame:
    """Add n-period lag columns to a sorted time series DataFrame.

    Args:
        df: DataFrame sorted by year; must have value_col
        value_col: Column to lag
        lags: List of lag periods (1, 2, 3 = 1-year, 2-year, 3-year lag)

    Returns:
        DataFrame with additional columns `{value_col}_lag{n}` per lag
    """
    lag_exprs = [
        pl.col(value_col).shift(n).alias(f"{value_col}_lag{n}")
        for n in lags
    ]
    return df.with_columns(lag_exprs)


def add_rolling_features(
    df: pl.DataFrame,
    value_col: str,
    windows: list[int],
) -> pl.DataFrame:
    """Add rolling mean and rolling std columns.

    Args:
        df: DataFrame sorted by year
        value_col: Column to compute rolling statistics on
        windows: List of window sizes (e.g. [3, 5] → rollmean3, rollmean5)

    Returns:
        DataFrame with additional rolling mean and std columns
    """
    exprs: list[pl.Expr] = []
    for w in windows:
        exprs.append(
            pl.col(value_col)
            .rolling_mean(window_size=w, min_periods=w)
            .alias(f"{value_col}_rollmean{w}")
        )
    exprs.append(
        pl.col(value_col)
        .rolling_std(window_size=3, min_periods=3)
        .alias(f"{value_col}_rollstd3")
    )
    return df.with_columns(exprs)


def add_yoy_acceleration(
    df: pl.DataFrame,
    value_col: str,
) -> pl.DataFrame:
    """Add year-over-year percentage change and acceleration features.

    Args:
        df: DataFrame sorted by year; must contain `{value_col}_lag1`
        value_col: Base column; requires _lag1 to already be computed

    Returns:
        DataFrame with `{value_col}_yoy_pct` and `{value_col}_acceleration`
    """
    lag1 = f"{value_col}_lag1"
    if lag1 not in df.columns:
        raise ValueError(f"Cannot compute YoY: '{lag1}' col not found. Run add_lag_features first.")

    yoy_col = f"{value_col}_yoy_pct"
    accel_col = f"{value_col}_acceleration"

    return df.with_columns([
        ((pl.col(value_col) / pl.col(lag1) - 1) * 100).alias(yoy_col),
    ]).with_columns([
        (pl.col(yoy_col) - pl.col(yoy_col).shift(1)).alias(accel_col),
    ])


def build_mortality_features(
    disease: str,
    processed_dir: Path,
    lags: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> pl.DataFrame:
    """Load a mortality clean parquet and engineer all feature columns.

    Args:
        disease: One of "cancer", "stroke", "ihd"
        processed_dir: Path to data/4_processed/ directory
        lags: Lag periods to compute (default: [1, 2, 3])
        rolling_windows: Rolling windows (default: [3, 5])

    Returns:
        Feature-enriched DataFrame
    """
    if lags is None:
        lags = [1, 2, 3]
    if rolling_windows is None:
        rolling_windows = [3, 5]

    src = processed_dir / f"mortality_{disease}_clean.parquet"
    df = pl.read_parquet(str(src))

    # Detect year and value columns
    year_col = next((c for c in df.columns if "year" in c.lower()), None)
    value_col = next(
        (c for c in df.columns if any(kw in c.lower() for kw in ("rate", "deaths", "number"))),
        None,
    )
    if not year_col or not value_col:
        raise ValueError(f"Cannot find year/value cols in {src}. Cols: {df.columns}")

    df = df.sort(year_col)
    df = add_lag_features(df, value_col, lags)
    df = add_rolling_features(df, value_col, rolling_windows)
    df = add_yoy_acceleration(df, value_col)

    null_rows = df.filter(pl.col(f"{value_col}_lag1").is_null()).shape[0]
    logger.info(
        f"Mortality [{disease}] features: {df.shape}; "
        f"{null_rows} leading null rows from lagging (drop before training)"
    )
    return df


def build_admission_features(
    processed_dir: Path,
    rate_base: int = 1000,
) -> pl.DataFrame:
    """Build admission feature matrix with index and lag features per age group.

    Args:
        processed_dir: Path to data/4_processed/ directory
        rate_base: Admission rate denominator (1000 or 10000)

    Returns:
        Feature DataFrame with lag1 and rollmean3 per age group
    """
    adm = pl.read_parquet(str(processed_dir / "admissions_age_sex_clean.parquet"))

    year_col = next((c for c in adm.columns if "year" in c.lower()), "year")
    age_col = next((c for c in adm.columns if "age" in c.lower()), None)
    value_col = next(
        (c for c in adm.columns if any(kw in c.lower() for kw in ("rate", "number", "admission"))),
        None,
    )

    if not age_col or not value_col:
        raise ValueError(f"Cannot find age/value columns. Cols: {adm.columns}")

    # Compute lag1 and rollmean3 per age group
    adm = (
        adm.sort([age_col, year_col])
        .with_columns([
            pl.col(value_col).shift(1).over(age_col).alias(f"{value_col}_lag1"),
            pl.col(value_col).rolling_mean(window_size=3, min_periods=3)
            .over(age_col).alias(f"{value_col}_rollmean3"),
        ])
    )

    logger.info(f"Admission features: {adm.shape}, rate_base={rate_base}")
    return adm
```

#### 3.2 `scripts/run_feature_engineering_ps002.py`

```python
"""PS-002 Story 04 — Time-Series Feature Engineering.

Run: python problem-statements/ps-002-disease-burden/scripts/run_feature_engineering_ps002.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_002_disease_burden.src.feature_engineer import (
    build_admission_features,
    build_mortality_features,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
RESULTS_DIR = PS_DIR / "results" / "tables"
LOG_DIR = PS_DIR / "logs" / "etl"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.add(str(LOG_DIR / "ps002_feature_engineering.log"), level="INFO", rotation="10 MB")

DISEASES = ["cancer", "stroke", "ihd"]
FEATURE_NOTES = """# PS-002 Feature Engineering Notes

| feature_name | type | formula | rationale | modelling_use |
|---|---|---|---|---|
| rate_lag1 | lag | shift(1) | Prior year rate | ARIMA regressor / Prophet external |
| rate_lag2 | lag | shift(2) | 2-year memory | Captures slower trend decay |
| rate_lag3 | lag | shift(3) | 3-year memory | Long-cycle disease patterns |
| rate_rollmean3 | rolling | rolling_mean(3) | Smooth local trend | Feature for trend direction |
| rate_rollmean5 | rolling | rolling_mean(5) | Stable trend estimate | Stable baseline for acceleration |
| rate_rollstd3 | rolling | rolling_std(3) | Volatility signal | CI calibration reference in Story 05 |
| rate_yoy_pct | derived | (rate/lag1 - 1)*100 | Annual growth rate | Model residual diagnostics |
| rate_acceleration | derived | yoy_pct - shift(yoy_pct,1) | 2nd derivative | Detect structural inflection |

## Null rows from lagging
Lag/rolling features produce NaN in leading rows:
- lag1: 1 null row; lag2: 2; lag3: 3; rollmean3: 2; rollmean5: 4
- Drop rows with NaN in target lag column before training ARIMA/HoltWinters/Prophet
- For Prophet: provide lag features as `add_regressor()` columns (requires values for future dates too)
"""


def main() -> None:
    logger.info("=== PS-002 Story 04: Feature Engineering ===")

    for disease in DISEASES:
        try:
            feat_df = build_mortality_features(disease, PROCESSED_DIR)
            out = PROCESSED_DIR / f"mortality_{disease}_features.parquet"
            feat_df.write_parquet(str(out), compression="snappy")
            logger.info(f"Mortality features [{disease}]: {feat_df.shape} → {out}")
        except (FileNotFoundError, ValueError) as exc:
            logger.error(f"Skipping {disease}: {exc}")

    # Admissions features
    try:
        adm_feat = build_admission_features(PROCESSED_DIR)
        out_adm = PROCESSED_DIR / "admissions_features.parquet"
        adm_feat.write_parquet(str(out_adm), compression="snappy")
        logger.info(f"Admission features: {adm_feat.shape} → {out_adm}")
    except (FileNotFoundError, ValueError) as exc:
        logger.error(f"Admission feature engineering failed: {exc}")

    # Feature notes
    notes_path = RESULTS_DIR / "ps002_feature_notes.md"
    notes_path.write_text(FEATURE_NOTES, encoding="utf-8")
    logger.info(f"Feature notes: {notes_path}")
    logger.info("Feature engineering complete.")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_feature_engineer.py
import polars as pl
import pytest


def test_add_lag_features_creates_lag_cols():
    from problem_statements.ps_002_disease_burden.src.feature_engineer import add_lag_features
    df = pl.DataFrame({"rate": [10.0, 20.0, 30.0, 40.0, 50.0]})
    result = add_lag_features(df, "rate", [1, 2])
    assert "rate_lag1" in result.columns
    assert "rate_lag2" in result.columns
    assert result["rate_lag1"][1] == pytest.approx(10.0)
    assert result["rate_lag2"][2] == pytest.approx(10.0)


def test_add_rolling_features_respects_min_periods():
    from problem_statements.ps_002_disease_burden.src.feature_engineer import add_rolling_features
    df = pl.DataFrame({"rate": [1.0, 2.0, 3.0, 4.0, 5.0]})
    result = add_rolling_features(df, "rate", [3])
    # rollmean3 first two rows should be null (min_periods=3)
    assert result["rate_rollmean3"][0] is None
    assert result["rate_rollmean3"][1] is None
    assert result["rate_rollmean3"][2] == pytest.approx(2.0)


def test_add_yoy_acceleration_requires_lag1():
    from problem_statements.ps_002_disease_burden.src.feature_engineer import add_yoy_acceleration
    df = pl.DataFrame({"rate": [100.0, 90.0, 81.0]})
    with pytest.raises(ValueError, match="lag1"):
        add_yoy_acceleration(df, "rate")


def test_add_yoy_pct_correct_computation():
    from problem_statements.ps_002_disease_burden.src.feature_engineer import (
        add_lag_features, add_yoy_acceleration,
    )
    df = pl.DataFrame({"rate": [100.0, 90.0, 81.0]})
    df = add_lag_features(df, "rate", [1])
    df = add_yoy_acceleration(df, "rate")
    # YoY from 100 → 90 = -10%
    assert df["rate_yoy_pct"][1] == pytest.approx(-10.0)
```

---

### 5. Implementation Steps

- [ ] Create `src/feature_engineer.py`
- [ ] Create `scripts/run_feature_engineering_ps002.py`
- [ ] Run: `python scripts/run_feature_engineering_ps002.py`
- [ ] Verify 3 mortality feature parquets exist in `data/4_processed/`
- [ ] Verify `admissions_features.parquet` exists
- [ ] Open one feature parquet — confirm lag and rolling columns present with expected nulls in leading rows
- [ ] Verify `ps002_feature_notes.md` written to `results/tables/`
- [ ] Run unit tests: `pytest tests/unit/test_feature_engineer.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-002-story-04-ts-features
git commit -m "feat(ps-002): add feature_engineer module with lag/rolling/acceleration features"
git commit -m "feat(ps-002): add run_feature_engineering_ps002 script and feature notes"
```
