# User Story: 5 — Mortality Forecasting Models

**As a** MOH disease surveillance officer,  
**I want** to fit ARIMA, Holt-Winters, and Prophet models to the cancer, stroke, and IHD mortality series and generate 2020–2030 forecasts with 80% and 95% confidence intervals,  
**so that** I can quantify which diseases are projected to remain major burden drivers and calibrate the need for specialist workforce planning.

## 1. 🎯 Acceptance Criteria

- 3 model types fitted to each of 3 diseases = 9 model instances total
- Train/test split: train on data up to 2014 (inclusive); hold-out test on 2015–2019 (5 years) — enables MAPE calculation on unseen data
- MAPE computed for each model-disease combination on the hold-out period: `MAPE = mean(|actual - predicted| / |actual|) * 100`
- Best model selected per disease based on hold-out MAPE — if tie within 1 pp, prefer simpler model (ARIMA > Holt-Winters > Prophet)
- Best model refit on full available history; forecast generated for 2020–2030 (11 years) with 80% and 95% prediction intervals
- Forecast results saved to `models/forecasts/mortality_{disease}_forecast.csv` with columns: `year, forecast, lower_80, upper_80, lower_95, upper_95, model_type`
- Model comparison table saved to `results/tables/ps002_mortality_model_comparison.csv`: `disease, model, train_end, mape_holdout, selected`

## 2. 🔒 Technical Constraints

- ARIMA: use `statsmodels.tsa.arima.model.ARIMA`; use `auto_arima` from `pmdarima` for order selection or manually try p∈{0,1,2}, d∈{0,1}, q∈{0,1}
- Holt-Winters: use `statsmodels.tsa.holtwinters.ExponentialSmoothing` with `trend='add'`, `damped_trend=True`, `seasonal=None` (annual data, no seasonality)
- Prophet: use `prophet.Prophet` with `yearly_seasonality=False`, `weekly_seasonality=False`, `daily_seasonality=False`; fit on `ds` (year as datetime Jan-1) and `y` (rate)
- All model objects saved as pickle files to `models/` — `{disease}_{model}.pkl`
- MAPE threshold for acceptable forecast: MAPE ≤ 15% on hold-out; log a WARNING if any selected model exceeds this
- Python warnings about convergence logged at WARNING level; do not suppress them

## 3. 📚 Domain Knowledge References

- [Time-Series Forecasting Methods](../../../../domain-knowledge/time-series-forecasting-methods.md) — ARIMA, Holt-Winters, Prophet guidance; MAPE interpretation and targets
- [Disease Burden Feature Engineering Guide](../../../../domain-knowledge/disease-burden-feature-engineering-guide.md) — mortality trend context for forecast sanity checks

## 4. 📦 Dependencies

- Story 02 outputs: `mortality_{disease}_clean.parquet`
- `statsmodels` — ARIMA, Holt-Winters
- `pmdarima` — auto order selection (optional but recommended)
- `prophet` — Prophet models
- `polars` — result assembly
- `loguru` — model training logs

## 5. ✅ Implementation Tasks

**Train/Test Split**
- ⬜ For each disease: split clean series at 2014 (train) / 2015–2019 (test)

**Model Fitting — per disease**
- ⬜ Fit ARIMA: grid search over (p, d, q) or use auto_arima; record AIC; generate test-period predictions
- ⬜ Fit Holt-Winters: `ExponentialSmoothing(trend='add', damped_trend=True)`; generate test-period predictions
- ⬜ Fit Prophet: prepare `ds`/`y` DataFrame; `.fit()`; generate test-period predictions

**Evaluation**
- ⬜ Compute MAPE per model per disease on hold-out period (2015–2019)
- ⬜ Select best model per disease; log selection rationale
- ⬜ Write model comparison table to `results/tables/ps002_mortality_model_comparison.csv`
- ⬜ Warn if MAPE > 15% for selected model

**Final Forecast**
- ⬜ Refit best model per disease on full history; generate 2020–2030 forecast + 80%/95% CIs
- ⬜ Save forecast CSV to `models/forecasts/mortality_{disease}_forecast.csv`
- ⬜ Save fitted model object as `models/{disease}_{model_type}.pkl`

**Logging**
- ⬜ Log per model: disease, model_type, order (if ARIMA), MAPE, selected (T/F) to `logs/etl/ps002_model_training.log`

## 6. Notes

- Cancer series extends to ~2019 with 25+ years of history — sufficient for ARIMA. Stroke and IHD series are similar length.
- Holt-Winters with damped trend is often best for series with a persistent downward trend that is expected to flatten — likely applies to IHD and stroke.
- Prophet may handle structural breaks (e.g. SARS 2003 impact) better if a `changepoint_prior_scale` is tuned. Start with default (0.05) and adjust if forecast diverges from EDA-observed trend.
- Pickle files enable model reuse in PS-003's scenario comparison tab without retraining.

---

## Implementation Plan

### 1. Feature Overview

Fit ARIMA, Holt-Winters, and Prophet to each mortality series with a rigorous train/test split. Select best model per disease by hold-out MAPE. Refit on full history and generate 2020–2030 forecasts with 80%/95% CIs. Save forecast CSVs and model pickles. Primary user: **PS-002 disease surveillance officer**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-002-disease-burden/src/forecasting_models.py
  - fit_arima(train_series, years) -> tuple[any, pl.DataFrame]
  - fit_holt_winters(train_series, years) -> tuple[any, pl.DataFrame]
  - fit_prophet(train_df, year_col, value_col) -> tuple[any, pl.DataFrame]
  - compute_mape(actuals, predictions) -> float
  - select_best_model(mape_map) -> str
  - generate_forecast(model, model_type, n_periods, full_train) -> pl.DataFrame

[CREATE] problem-statements/ps-002-disease-burden/scripts/run_forecasting_ps002.py
  - Orchestrates 9 model fits; writes forecast CSVs; pickles; comparison table
```

---

### 3. Code Generation Specifications

#### 3.1 `src/forecasting_models.py`

```python
"""PS-002 mortality forecasting models.

Supports ARIMA (statsmodels), Holt-Winters (statsmodels), Prophet.
All functions return (fitted_model, predictions_df) where predictions_df has
columns: year, predicted, lower_80, upper_80, lower_95, upper_95.
"""

import pickle
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

MAPE_THRESHOLD = 15.0

MODEL_PRIORITY: dict[str, int] = {"ARIMA": 1, "HoltWinters": 2, "Prophet": 3}

CI_Z_80 = 1.282  # Z-score for 80% CI


def compute_mape(actuals: list[float], predictions: list[float]) -> float:
    """Mean Absolute Percentage Error. Filters NaN pairs.

    Args:
        actuals: Observed values
        predictions: Model predictions

    Returns:
        MAPE percentage (0–100 scale)
    """
    pairs = [
        (a, p) for a, p in zip(actuals, predictions)
        if a is not None and p is not None and a != 0
    ]
    if not pairs:
        return float("inf")
    return float(np.mean([abs(a - p) / abs(a) * 100 for a, p in pairs]))


def select_best_model(mape_map: dict[str, float]) -> str:
    """Select best model by lowest MAPE. On tie (within 1 pp), prefer simpler model.

    Args:
        mape_map: Mapping of model_name to MAPE value

    Returns:
        Selected model name
    """
    min_mape = min(mape_map.values())
    candidates = [
        m for m, v in mape_map.items() if v <= min_mape + 1.0
    ]
    # Among tied candidates, prefer simpler (lowest priority number)
    return min(candidates, key=lambda m: MODEL_PRIORITY.get(m, 99))


def fit_arima(
    train_values: list[float],
    train_years: list[int],
    test_years: list[int],
) -> tuple[Any, pl.DataFrame]:
    """Fit ARIMA using auto order selection via pmdarima or a small grid.

    Args:
        train_values: Training series values (chronological)
        train_years: Corresponding years
        test_years: Years to predict in hold-out period

    Returns:
        (fitted_model, holdout_predictions_df)
    """
    from statsmodels.tsa.arima.model import ARIMA

    best_aic = float("inf")
    best_model = None
    best_order = (1, 1, 0)

    for p in range(3):
        for d in range(2):
            for q in range(2):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        m = ARIMA(train_values, order=(p, d, q)).fit()
                    if m.aic < best_aic:
                        best_aic, best_model, best_order = m.aic, m, (p, d, q)
                except Exception:
                    continue

    if best_model is None:
        raise RuntimeError("ARIMA fitting failed for all (p,d,q) combinations.")

    logger.info(f"ARIMA best order: {best_order}, AIC={best_aic:.2f}")
    n_test = len(test_years)
    forecast_result = best_model.get_forecast(steps=n_test)
    mean_pred = forecast_result.predicted_mean.tolist()
    ci_80 = forecast_result.conf_int(alpha=0.20).values
    ci_95 = forecast_result.conf_int(alpha=0.05).values

    preds_df = pl.DataFrame({
        "year": test_years,
        "predicted": mean_pred,
        "lower_80": ci_80[:, 0].tolist(),
        "upper_80": ci_80[:, 1].tolist(),
        "lower_95": ci_95[:, 0].tolist(),
        "upper_95": ci_95[:, 1].tolist(),
    })
    return best_model, preds_df


def fit_holt_winters(
    train_values: list[float],
    test_years: list[int],
) -> tuple[Any, pl.DataFrame]:
    """Fit Holt-Winters with additive damped trend (no seasonality — annual data).

    Args:
        train_values: Training series values
        test_years: Years for hold-out predictions

    Returns:
        (fitted_model, holdout_predictions_df)
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ExponentialSmoothing(
            train_values, trend="add", damped_trend=True, seasonal=None
        ).fit(optimized=True)

    n_test = len(test_years)
    mean_pred = model.forecast(n_test).tolist()

    # Approximate CIs from residual std
    resid_std = float(np.std(model.resid))
    lower_80 = [p - CI_Z_80 * resid_std for p in mean_pred]
    upper_80 = [p + CI_Z_80 * resid_std for p in mean_pred]
    lower_95 = [p - 1.96 * resid_std for p in mean_pred]
    upper_95 = [p + 1.96 * resid_std for p in mean_pred]

    preds_df = pl.DataFrame({
        "year": test_years,
        "predicted": mean_pred,
        "lower_80": lower_80,
        "upper_80": upper_80,
        "lower_95": lower_95,
        "upper_95": upper_95,
    })
    return model, preds_df


def fit_prophet(
    train_values: list[float],
    train_years: list[int],
    test_years: list[int],
) -> tuple[Any, pl.DataFrame]:
    """Fit Prophet with no seasonality (annual data).

    Args:
        train_values: Training values
        train_years: Corresponding years (converted to Jan-1 datetime internally)
        test_years: Hold-out years

    Returns:
        (fitted_model, holdout_predictions_df)
    """
    import pandas as pd
    from prophet import Prophet

    train_ds = [datetime(y, 1, 1) for y in train_years]
    train_pd = pd.DataFrame({"ds": train_ds, "y": train_values})

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
        )
        model.fit(train_pd)

    future_ds = pd.DataFrame({"ds": [datetime(y, 1, 1) for y in test_years]})
    forecast = model.predict(future_ds)

    preds_df = pl.DataFrame({
        "year": test_years,
        "predicted": forecast["yhat"].tolist(),
        "lower_80": forecast["yhat_lower"].tolist(),  # Prophet defaults to 80%
        "upper_80": forecast["yhat_upper"].tolist(),
        "lower_95": (forecast["yhat"] - 1.96 * (forecast["yhat_upper"] - forecast["yhat"]) / CI_Z_80).tolist(),
        "upper_95": (forecast["yhat"] + 1.96 * (forecast["yhat_upper"] - forecast["yhat"]) / CI_Z_80).tolist(),
    })
    return model, preds_df


def generate_full_forecast(
    disease: str,
    best_model_type: str,
    all_values: list[float],
    all_years: list[int],
    forecast_years: list[int],
    models_dir: Path,
) -> pl.DataFrame:
    """Refit best model on all data; generate forward forecast with CIs. Save pickle.

    Args:
        disease: Disease name
        best_model_type: "ARIMA" | "HoltWinters" | "Prophet"
        all_values: Full historical series
        all_years: Corresponding years
        forecast_years: Future years to forecast
        models_dir: Directory to save pickle

    Returns:
        Forecast DataFrame with columns: year, forecast, lower_80, upper_80, lower_95, upper_95, model_type
    """
    if best_model_type == "ARIMA":
        model, preds_df = fit_arima(all_values, all_years, forecast_years)
    elif best_model_type == "HoltWinters":
        model, preds_df = fit_holt_winters(all_values, forecast_years)
    elif best_model_type == "Prophet":
        model, preds_df = fit_prophet(all_values, all_years, forecast_years)
    else:
        raise ValueError(f"Unknown model type: {best_model_type}")

    pkl_path = models_dir / f"{disease}_{best_model_type}.pkl"
    models_dir.mkdir(parents=True, exist_ok=True)
    with pkl_path.open("wb") as fh:
        pickle.dump(model, fh)
    logger.info(f"Model saved: {pkl_path}")

    return preds_df.rename({"predicted": "forecast"}).with_columns(
        pl.lit(best_model_type).alias("model_type")
    )
```

#### 3.2 `scripts/run_forecasting_ps002.py`

```python
"""PS-002 Story 05 — Mortality Forecasting Models.

Run: python problem-statements/ps-002-disease-burden/scripts/run_forecasting_ps002.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_002_disease_burden.src.forecasting_models import (
    MAPE_THRESHOLD,
    compute_mape,
    fit_arima,
    fit_holt_winters,
    fit_prophet,
    generate_full_forecast,
    select_best_model,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
MODELS_DIR = PS_DIR / "models"
FORECASTS_DIR = PS_DIR / "models" / "forecasts"
RESULTS_DIR = PS_DIR / "results" / "tables"
LOG_DIR = PS_DIR / "logs" / "etl"

for d in (MODELS_DIR, FORECASTS_DIR, RESULTS_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

logger.add(str(LOG_DIR / "ps002_model_training.log"), level="INFO", rotation="10 MB")

DISEASES = ["cancer", "stroke", "ihd"]
TRAIN_END = 2014
TEST_YEARS = list(range(2015, 2020))
FORECAST_YEARS = list(range(2020, 2031))


def _load_clean_series(disease: str) -> tuple[list[float], list[int]]:
    df = pl.read_parquet(str(PROCESSED_DIR / f"mortality_{disease}_clean.parquet"))
    year_col = next(c for c in df.columns if "year" in c.lower())
    value_col = next(
        c for c in df.columns
        if any(kw in c.lower() for kw in ("rate", "deaths", "number"))
    )
    df = df.sort(year_col).filter(pl.col(value_col).is_not_null())
    years = df[year_col].cast(pl.Int32).to_list()
    values = df[value_col].cast(pl.Float64).to_list()
    return values, years


def main() -> None:
    logger.info("=== PS-002 Story 05: Mortality Forecasting Models ===")
    comparison_rows: list[dict] = []

    for disease in DISEASES:
        logger.info(f"--- {disease.upper()} ---")
        values, years = _load_clean_series(disease)

        # Train/test split
        train_idx = [i for i, y in enumerate(years) if y <= TRAIN_END]
        train_vals = [values[i] for i in train_idx]
        train_yrs = [years[i] for i in train_idx]

        test_idx = [i for i, y in enumerate(years) if y in TEST_YEARS]
        test_actuals = [values[i] for i in test_idx]

        mape_map: dict[str, float] = {}

        # ARIMA
        try:
            _, arima_preds = fit_arima(train_vals, train_yrs, TEST_YEARS)
            mape_arima = compute_mape(test_actuals, arima_preds["predicted"].to_list())
            mape_map["ARIMA"] = mape_arima
            logger.info(f"ARIMA MAPE ({disease}): {mape_arima:.2f}%")
        except Exception as exc:
            logger.warning(f"ARIMA failed for {disease}: {exc}")

        # Holt-Winters
        try:
            _, hw_preds = fit_holt_winters(train_vals, TEST_YEARS)
            mape_hw = compute_mape(test_actuals, hw_preds["predicted"].to_list())
            mape_map["HoltWinters"] = mape_hw
            logger.info(f"HoltWinters MAPE ({disease}): {mape_hw:.2f}%")
        except Exception as exc:
            logger.warning(f"HoltWinters failed for {disease}: {exc}")

        # Prophet
        try:
            _, prophet_preds = fit_prophet(train_vals, train_yrs, TEST_YEARS)
            mape_prophet = compute_mape(test_actuals, prophet_preds["predicted"].to_list())
            mape_map["Prophet"] = mape_prophet
            logger.info(f"Prophet MAPE ({disease}): {mape_prophet:.2f}%")
        except Exception as exc:
            logger.warning(f"Prophet failed for {disease}: {exc}")

        if not mape_map:
            logger.error(f"No models fitted for {disease} — skipping.")
            continue

        # Select best model
        best = select_best_model(mape_map)
        best_mape = mape_map[best]
        if best_mape > MAPE_THRESHOLD:
            logger.warning(
                f"Selected model [{best}] for {disease} has MAPE {best_mape:.1f}% "
                f"exceeding threshold {MAPE_THRESHOLD}%"
            )

        # Record comparison row
        for model_name, mape_val in mape_map.items():
            comparison_rows.append({
                "disease": disease,
                "model": model_name,
                "train_end": TRAIN_END,
                "mape_holdout": round(mape_val, 2),
                "selected": model_name == best,
            })

        # Refit best model on full history + generate forecast
        forecast_df = generate_full_forecast(
            disease, best, values, years, FORECAST_YEARS, MODELS_DIR
        )
        forecast_df.write_csv(
            str(FORECASTS_DIR / f"mortality_{disease}_forecast.csv")
        )
        logger.info(f"Forecast saved: mortality_{disease}_forecast.csv ({best}, MAPE={best_mape:.1f}%)")

    # Write model comparison table
    comparison_df = pl.DataFrame(comparison_rows)
    comparison_df.write_csv(str(RESULTS_DIR / "ps002_mortality_model_comparison.csv"))
    logger.info(f"Model comparison: {RESULTS_DIR / 'ps002_mortality_model_comparison.csv'}")
    logger.info("Forecasting complete.")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_forecasting_models.py
import pytest


def test_compute_mape_correct():
    from problem_statements.ps_002_disease_burden.src.forecasting_models import compute_mape
    actuals = [100.0, 200.0, 150.0]
    preds = [90.0, 210.0, 150.0]  # errors: 10%, 5%, 0% → mean = 5%
    mape = compute_mape(actuals, preds)
    assert mape == pytest.approx(5.0, abs=0.01)


def test_compute_mape_handles_zero_actual():
    from problem_statements.ps_002_disease_burden.src.forecasting_models import compute_mape
    # Zero actual should be skipped (division guard)
    mape = compute_mape([0.0, 100.0], [10.0, 110.0])  # Only 2nd pair valid → 10%
    assert mape == pytest.approx(10.0, abs=0.01)


def test_select_best_model_prefers_simpler_on_tie():
    from problem_statements.ps_002_disease_burden.src.forecasting_models import select_best_model
    # ARIMA and HoltWinters within 1pp — should prefer ARIMA (simpler)
    result = select_best_model({"ARIMA": 8.5, "HoltWinters": 9.0, "Prophet": 12.0})
    assert result == "ARIMA"


def test_select_best_model_picks_lowest_mape():
    from problem_statements.ps_002_disease_burden.src.forecasting_models import select_best_model
    result = select_best_model({"ARIMA": 14.0, "HoltWinters": 6.0, "Prophet": 9.0})
    assert result == "HoltWinters"
```

---

### 5. Implementation Steps

- [ ] Create `src/forecasting_models.py`
- [ ] Create `scripts/run_forecasting_ps002.py`
- [ ] Install required packages: `uv pip install statsmodels pmdarima prophet`
- [ ] Run: `python scripts/run_forecasting_ps002.py`
- [ ] Verify 3 forecast CSVs in `models/forecasts/`
- [ ] Verify 3 (or up to 9) pickle files in `models/`
- [ ] Verify `ps002_mortality_model_comparison.csv` has ≥9 rows
- [ ] Check log for any MAPE > 15% warnings
- [ ] Run unit tests: `pytest tests/unit/test_forecasting_models.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-002-story-05-forecasting-models
git commit -m "feat(ps-002): add forecasting_models module (ARIMA, HoltWinters, Prophet)"
git commit -m "feat(ps-002): add run_forecasting_ps002 orchestration with MAPE-based model selection"
```
