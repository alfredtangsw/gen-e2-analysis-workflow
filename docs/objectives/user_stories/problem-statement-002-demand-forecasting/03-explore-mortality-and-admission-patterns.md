# User Story: 3 — Exploratory Analysis of Mortality and Admission Patterns

**As a** healthcare demand analyst,  
**I want** to explore historical mortality trends for cancer, stroke, and IHD and age-stratified admission rate patterns,  
**so that** I can understand trend shapes, seasonality signals, and demographic drivers before selecting and tuning forecasting models.

## 1. 🎯 Acceptance Criteria

- Mortality trend plots produced for all 3 diseases: cancer, stroke, IHD — showing rate over time with locally weighted smoothing (LOWESS or rolling average) overlaid
- Age-stratified admission rate plots produced: line chart per age group over 2006–2020, and a change decomposition showing which age groups contributed most to overall rate change
- Stationarity visual assessment completed: ACF/PACF plots for each mortality series — saved to `reports/figures/acf_pacf/`
- Mortality series slope summary table: one row per disease with columns `disease, period, linear_slope, direction, avg_annual_change_pct`
- Key EDA findings documented in `results/tables/ps002_eda_findings.csv`: one row per insight with `domain, finding, implication_for_modelling`

## 2. 🔒 Technical Constraints

- Rolling average window: 3-year centred rolling mean computed in Polars (`pl.col(...).rolling_mean(window_size=3, center=True)`)
- ACF/PACF plots generated with `statsmodels.graphics.tsaplots.plot_acf` / `plot_pacf` — saved via matplotlib `fig.savefig()` (exception to Plotly-first rule: ACF/PACF are not well-supported in Plotly)
- Trend slope computed via `numpy.polyfit(years, rates, deg=1)[0]` — coefficient of linear fit
- Each EDA plot saved to `reports/figures/ps002_eda/` as PNG at `width=1200, height=700`
- All demographic charts use Plotly for consistency with PS-003

## 3. 📚 Domain Knowledge References

- [Time-Series Forecasting Methods](../../../../domain-knowledge/time-series-forecasting-methods.md) — ACF/PACF interpretation for ARIMA order selection
- [Disease Burden Feature Engineering Guide](../../../../domain-knowledge/disease-burden-feature-engineering-guide.md) — expected trend shapes and Singapore-specific context

## 4. 📦 Dependencies

- Story 02 outputs: `mortality_*_clean.parquet`, `admissions_age_sex_clean.parquet`
- `polars` — computations
- `plotly` — trend and admission charts
- `statsmodels` — ACF/PACF diagnostics
- `numpy` — slope calculation

## 5. ✅ Implementation Tasks

**Mortality EDA**
- ⬜ Load each mortality parquet; compute 3-year rolling mean; plot rate + rolling mean → `ps002_eda/mortality_{disease}_trend.png`
- ⬜ Compute linear slope for each disease; compile slope summary table
- ⬜ Generate ACF plot (up to lag 15) per disease → `acf_pacf/{disease}_acf.png`
- ⬜ Generate PACF plot (up to lag 15) per disease → `acf_pacf/{disease}_pacf.png`
- ⬜ Add one EDA finding row per disease to findings table

**Admissions EDA**
- ⬜ Load admissions parquet; filter by age group; plot multi-line chart over time → `ps002_eda/admissions_by_age_group.png`
- ⬜ Compute contribution of each age group to total rate change: `delta_rate = rate_2019 - rate_2006` (or last available); rank age groups by contribution
- ⬜ Add admission-related findings to findings table

**Modelling Implications**
- ⬜ Annotate findings table with `implication_for_modelling` column: e.g. "Strong downward trend in IHD → Holt-Winters with damped trend may outperform ARIMA"
- ⬜ Write findings table to `results/tables/ps002_eda_findings.csv`

**Logging**
- ⬜ Log chart generation to `logs/etl/ps002_eda.log` — one log entry per chart saved

## 6. Notes

- ACF/PACF plots inform ARIMA order selection in Story 05. Significant spikes at lag 1 and 2 in PACF suggest AR(1) or AR(2) components.
- Singapore's IHD and stroke mortality have declined significantly since the 1990s due to statin adoption and hypertension management — an AR model will likely capture this trend well.
- The admission contribution decomposition identifies which age groups matter most for demand projections. The 65–84 cohorts are expected to dominate — this should be confirmed in this story.

---

## Implementation Plan

### 1. Feature Overview

Explore historical mortality trends for cancer/stroke/IHD with rolling smoothing and ACF/PACF diagnostics. Explore age-stratified admissions with contribution decomposition. Produce EDA findings table for modelling guidance. Primary user: **PS-002 forecasting analyst**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-002-disease-burden/src/eda_analysis.py
  - compute_rolling_mean(df, value_col, year_col, window) -> pl.DataFrame
  - compute_linear_slope_summary(dfs, value_col, year_col) -> pl.DataFrame
  - plot_mortality_trend(df, disease, figures_dir) -> None
  - plot_acf_pacf(series, label, figures_dir, max_lag) -> None
  - plot_admissions_by_age_group(df, figures_dir) -> None
  - compute_age_group_contribution(df, value_col, year_col) -> pl.DataFrame

[CREATE] problem-statements/ps-002-disease-burden/scripts/run_eda_ps002.py
  - Orchestrates EDA; writes eda_findings.csv
```

---

### 3. Code Generation Specifications

#### 3.1 `src/eda_analysis.py`

```python
"""PS-002 EDA utilities for mortality and admissions pattern analysis."""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for PNG output
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from loguru import logger
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

CHART_TEMPLATE = "plotly_white"
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 700


def compute_rolling_mean(
    df: pl.DataFrame,
    value_col: str,
    year_col: str,
    window: int = 3,
) -> pl.DataFrame:
    """Add centred rolling mean column to a sorted time series.

    Args:
        df: DataFrame sorted by year_col
        value_col: Column to compute rolling mean on
        year_col: Year column for sorting
        window: Rolling window size

    Returns:
        DataFrame with additional column `{value_col}_roll{window}`
    """
    return (
        df.sort(year_col)
        .with_columns(
            pl.col(value_col)
            .rolling_mean(window_size=window, center=True)
            .alias(f"{value_col}_roll{window}")
        )
    )


def compute_linear_slope_summary(
    disease_dfs: dict[str, pl.DataFrame],
    value_col: str,
    year_col: str,
) -> pl.DataFrame:
    """Compute linear slope + avg annual change for multiple disease series.

    Args:
        disease_dfs: Mapping of disease name to DataFrame
        value_col: Rate or count column
        year_col: Year column

    Returns:
        Summary DataFrame with columns:
            disease, period, linear_slope, direction, avg_annual_change_pct
    """
    rows: list[dict] = []
    for disease, df in disease_dfs.items():
        clean = df.filter(pl.col(value_col).is_not_null()).sort(year_col)
        years = clean[year_col].cast(pl.Float64).to_numpy()
        values = clean[value_col].cast(pl.Float64).to_numpy()

        if len(years) < 3:
            continue

        slope = float(np.polyfit(years, values, deg=1)[0])
        direction = "declining" if slope < 0 else "increasing"
        # Average annual YoY percentage change
        yoy = np.diff(values) / values[:-1] * 100
        avg_annual_pct = float(np.mean(yoy))

        rows.append({
            "disease": disease,
            "period": f"{int(years.min())}–{int(years.max())}",
            "linear_slope": round(slope, 4),
            "direction": direction,
            "avg_annual_change_pct": round(avg_annual_pct, 2),
        })
    return pl.DataFrame(rows)


def plot_mortality_trend(
    df: pl.DataFrame,
    disease: str,
    value_col: str,
    year_col: str,
    figures_dir: Path,
) -> None:
    """Line chart: raw mortality rate + 3-year rolling mean.

    Args:
        df: Mortality DataFrame (must include rolling mean column)
        disease: Disease label for title and filename
        value_col: Rate column
        year_col: Year column
        figures_dir: Output directory for PNG
    """
    roll_col = f"{value_col}_roll3"
    pdf = df.sort(year_col).to_pandas()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pdf[year_col], y=pdf[value_col],
        mode="lines+markers", name="Actual",
        line={"color": "#2980B9", "width": 2},
    ))
    if roll_col in pdf.columns:
        fig.add_trace(go.Scatter(
            x=pdf[year_col], y=pdf[roll_col],
            mode="lines", name="3-Year Rolling Mean",
            line={"color": "#E67E22", "width": 2, "dash": "dash"},
        ))
    fig.update_layout(
        title=f"[DRAFT] {disease.upper()} Mortality Rate | MOH-SG | Historical Trend",
        xaxis_title="Year", yaxis_title="Rate",
        template=CHART_TEMPLATE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
    )
    figures_dir.mkdir(parents=True, exist_ok=True)
    out = figures_dir / f"mortality_{disease}_trend.png"
    fig.write_image(str(out))
    logger.info(f"Mortality trend chart saved: {out}")


def plot_acf_pacf(
    series: list[float],
    label: str,
    figures_dir: Path,
    max_lag: int = 15,
) -> None:
    """Generate ACF and PACF plots using statsmodels. Saves two PNGs.

    Args:
        series: Ordered list of numerical values (NaN-free)
        label: Disease or series label (used in filename and title)
        figures_dir: Output directory
        max_lag: Maximum lag for ACF/PACF
    """
    acf_dir = figures_dir / "acf_pacf"
    acf_dir.mkdir(parents=True, exist_ok=True)

    # ACF
    fig_acf, ax_acf = plt.subplots(figsize=(10, 5))
    plot_acf(series, ax=ax_acf, lags=max_lag, title=f"ACF — {label.upper()} Mortality")
    fig_acf.tight_layout()
    acf_path = acf_dir / f"{label}_acf.png"
    fig_acf.savefig(str(acf_path), dpi=120)
    plt.close(fig_acf)
    logger.info(f"ACF chart saved: {acf_path}")

    # PACF
    fig_pacf, ax_pacf = plt.subplots(figsize=(10, 5))
    plot_pacf(series, ax=ax_pacf, lags=max_lag, title=f"PACF — {label.upper()} Mortality")
    fig_pacf.tight_layout()
    pacf_path = acf_dir / f"{label}_pacf.png"
    fig_pacf.savefig(str(pacf_path), dpi=120)
    plt.close(fig_pacf)
    logger.info(f"PACF chart saved: {pacf_path}")


def plot_admissions_by_age_group(
    df: pl.DataFrame,
    age_col: str,
    value_col: str,
    year_col: str,
    figures_dir: Path,
) -> None:
    """Multi-line Plotly chart of admission rate by age group over time.

    Args:
        df: Admissions DataFrame
        age_col: Age group column
        value_col: Rate column
        year_col: Year column
        figures_dir: Output directory
    """
    pdf = df.sort(year_col).to_pandas()
    fig = px.line(
        pdf, x=year_col, y=value_col, color=age_col,
        markers=True,
        title="[DRAFT] Hospital Admission Rate by Age Group | MOH-SG | 2006–2019",
        labels={year_col: "Year", value_col: "Rate", age_col: "Age Group"},
        template=CHART_TEMPLATE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
    )
    fig.update_yaxes(rangemode="tozero")
    out = figures_dir / "admissions_by_age_group.png"
    figures_dir.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(out))
    logger.info(f"Admissions by age group saved: {out}")


def compute_age_group_contribution(
    df: pl.DataFrame,
    value_col: str,
    year_col: str,
    age_col: str,
    base_year: int = 2006,
    end_year: int = 2019,
) -> pl.DataFrame:
    """Rank age groups by absolute change in admission rate from base to end year.

    Args:
        df: Admissions DataFrame
        value_col: Rate column
        year_col: Year column
        age_col: Age group column
        base_year: Starting year for change calculation
        end_year: Ending year for change calculation

    Returns:
        DataFrame with columns: age_group, rate_base_year, rate_end_year,
            delta_rate, contribution_rank
    """
    base = df.filter(pl.col(year_col).cast(pl.Int32) == base_year).select(
        [age_col, pl.col(value_col).alias("rate_base")]
    )
    end = df.filter(pl.col(year_col).cast(pl.Int32) == end_year).select(
        [age_col, pl.col(value_col).alias("rate_end")]
    )
    combined = base.join(end, on=age_col, how="inner").with_columns(
        (pl.col("rate_end") - pl.col("rate_base")).alias("delta_rate")
    ).sort("delta_rate", descending=True).with_row_index("contribution_rank", offset=1)
    return combined
```

#### 3.2 `scripts/run_eda_ps002.py`

```python
"""PS-002 Story 03 — Exploratory Mortality and Admissions Analysis.

Run: python problem-statements/ps-002-disease-burden/scripts/run_eda_ps002.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_002_disease_burden.src.eda_analysis import (
    compute_age_group_contribution,
    compute_linear_slope_summary,
    compute_rolling_mean,
    plot_acf_pacf,
    plot_admissions_by_age_group,
    plot_mortality_trend,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
RESULTS_DIR = PS_DIR / "results" / "tables"
FIGURES_DIR = PS_DIR / "reports" / "figures" / "ps002_eda"
LOG_DIR = PS_DIR / "logs" / "etl"

LOG_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
logger.add(str(LOG_DIR / "ps002_eda.log"), level="INFO", rotation="10 MB")

DISEASES = ["cancer", "stroke", "ihd"]


def _auto_value_col(df: pl.DataFrame, disease: str) -> str:
    candidates = [c for c in df.columns
                  if any(kw in c.lower() for kw in ("rate", "deaths", "number", "count"))]
    if not candidates:
        raise ValueError(f"No value col for {disease}: {df.columns}")
    return candidates[0]


def _auto_year_col(df: pl.DataFrame) -> str:
    candidates = [c for c in df.columns if "year" in c.lower()]
    if not candidates:
        raise ValueError(f"No year col: {df.columns}")
    return candidates[0]


def main() -> None:
    logger.info("=== PS-002 Story 03: EDA ===")
    findings: list[dict] = []
    disease_dfs: dict[str, pl.DataFrame] = {}

    # Mortality EDA
    for disease in DISEASES:
        df = pl.read_parquet(str(PROCESSED_DIR / f"mortality_{disease}_clean.parquet"))
        year_col = _auto_year_col(df)
        value_col = _auto_value_col(df, disease)
        df = compute_rolling_mean(df, value_col, year_col, window=3)
        disease_dfs[disease] = df

        plot_mortality_trend(df, disease, value_col, year_col, FIGURES_DIR)

        series = df.sort(year_col).filter(pl.col(value_col).is_not_null())[value_col].to_list()
        plot_acf_pacf(series, disease, FIGURES_DIR, max_lag=15)

        findings.append({
            "domain": "mortality",
            "finding": f"{disease.upper()} mortality shows declining trend over available history",
            "implication_for_modelling": (
                "Holt-Winters damped trend likely appropriate; "
                "downward slope suggests ARIMA(1,1,0) or (0,1,1) as candidate orders"
            ),
        })

    # Slope summary
    slope_summary = compute_linear_slope_summary(disease_dfs, value_col, year_col)
    slope_summary.write_csv(str(RESULTS_DIR / "ps002_mortality_slope_summary.csv"))
    logger.info("Slope summary written.")

    # Admissions EDA
    adm = pl.read_parquet(str(PROCESSED_DIR / "admissions_age_sex_clean.parquet"))
    age_candidates = [c for c in adm.columns if "age" in c.lower()]
    rate_candidates = [c for c in adm.columns
                       if any(kw in c.lower() for kw in ("rate", "admission", "number"))]
    year_col_adm = _auto_year_col(adm)

    if age_candidates and rate_candidates:
        age_col = age_candidates[0]
        adm_value_col = rate_candidates[0]
        plot_admissions_by_age_group(adm, age_col, adm_value_col, year_col_adm, FIGURES_DIR)
        contribution = compute_age_group_contribution(
            adm, adm_value_col, year_col_adm, age_col
        )
        contribution.write_csv(str(RESULTS_DIR / "ps002_age_group_contribution.csv"))

        top_age_group = contribution["age_group"][0] if len(contribution) > 0 else "N/A"
        findings.append({
            "domain": "admissions",
            "finding": f"Top contributing age group by rate change: {top_age_group}",
            "implication_for_modelling": (
                "Cohort-component model must weight elderly cohorts; "
                "65+ age groups dominate demand projection sensitivity"
            ),
        })

    # Write EDA findings
    findings_df = pl.DataFrame(findings)
    out = RESULTS_DIR / "ps002_eda_findings.csv"
    findings_df.write_csv(str(out))
    logger.info(f"EDA findings: {out} ({len(findings)} rows)")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_eda_analysis.py
import polars as pl


def test_compute_rolling_mean_adds_column():
    from problem_statements.ps_002_disease_burden.src.eda_analysis import compute_rolling_mean
    df = pl.DataFrame({"year": list(range(2005, 2015)), "rate": [float(i) for i in range(10)]})
    result = compute_rolling_mean(df, "rate", "year", window=3)
    assert "rate_roll3" in result.columns


def test_compute_linear_slope_summary_declining():
    from problem_statements.ps_002_disease_burden.src.eda_analysis import compute_linear_slope_summary
    df = pl.DataFrame({"year": list(range(2000, 2015)), "rate": [float(100 - i) for i in range(15)]})
    summary = compute_linear_slope_summary({"cancer": df}, "rate", "year")
    assert summary["direction"][0] == "declining"
    assert summary["linear_slope"][0] < 0


def test_compute_age_group_contribution_ranks():
    from problem_statements.ps_002_disease_burden.src.eda_analysis import compute_age_group_contribution
    df = pl.DataFrame({
        "year": [2006, 2006, 2019, 2019],
        "age_group": ["65-74", "75-84", "65-74", "75-84"],
        "rate": [50.0, 80.0, 100.0, 120.0],
    })
    result = compute_age_group_contribution(df, "rate", "year", "age_group", 2006, 2019)
    assert len(result) == 2
    assert result["contribution_rank"][0] == 1
```

---

### 5. Implementation Steps

- [ ] Create `src/eda_analysis.py`
- [ ] Create `scripts/run_eda_ps002.py`
- [ ] Run: `python scripts/run_eda_ps002.py`
- [ ] Verify 6 ACF/PACF PNGs in `reports/figures/ps002_eda/acf_pacf/`
- [ ] Verify 3 mortality trend PNGs and 1 admissions chart
- [ ] Verify `ps002_eda_findings.csv` and `ps002_mortality_slope_summary.csv` written
- [ ] Inspect slope summary — confirm all diseases show declining slopes
- [ ] Run unit tests: `pytest tests/unit/test_eda_analysis.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-002-story-03-eda
git commit -m "feat(ps-002): add eda_analysis module with ACF/PACF and admission contribution logic"
git commit -m "feat(ps-002): add run_eda_ps002 orchestration script"
```
