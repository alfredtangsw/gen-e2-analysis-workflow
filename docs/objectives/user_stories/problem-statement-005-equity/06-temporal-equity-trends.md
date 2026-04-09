# Analyze Temporal Equity Trends (Lifecycle Stage: Advanced Analysis)

**Story ID**: PS-005-US-06  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P0 (Critical)  
**Effort Estimate**: M (4 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Population Health Strategist evaluating equity progress**,  
I want **to analyze whether healthcare disparities are widening or narrowing over time (2006-2020)**,  
So that **I can assess the effectiveness of equity interventions and identify persistent or worsening inequities requiring policy action**.

---

## 🎯 Acceptance Criteria

1. **Temporal disparity trends**
   - Rate ratio trends over time
   - Gini coefficient trends (increasing = widening inequality)
   - Absolute vs relative disparity trends
   - Statistical trend tests (increasing/decreasing/stable)

2. **Convergence/divergence analysis**
   - Convergence: disparities narrowing (equity improving)
   - Divergence: disparities widening (equity worsening)
   - Persistent gaps: stable disparities
   - Demographic-specific trends

3. **Policy impact assessment** (if intervention timing known)
   - Pre-post analysis around policy changes
   - Differential trends: demographics benefiting vs not

4. **Deliverables**
   - Output: `results/tables/equity_temporal_trends.csv`
   - Figures: Disparity trend charts, convergence plots
   - Report: Equity progress assessment

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9
- **Primary Library**: Polars 0.20+
- **Statistical Analysis**: scipy, statsmodels
- **Visualization**: Matplotlib
- **Logging**: loguru
- **Testing**: pytest ≥80% coverage

---

## 📚 Domain Knowledge References

- [Domain Knowledge Research](../../../problem_statements/DOMAIN_KNOWLEDGE_RESEARCH.md#equity-trend-analysis)
- [Problem Statement PS-005](../../../problem_statements/ps-005-healthcare-equity-disparities.md#objective-3)

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`, `scipy>=1.11.0`, `statsmodels>=0.14.0`, `matplotlib>=3.8.0`, `loguru>=0.7.0`

### Internal Dependencies
- **Upstream**: PS-005-US-03, PS-005-US-04 (Disparity analyses - BLOCKING)
- **Data Sources**: `shared/data/3_interim/equity_analysis_integrated.parquet`

---

## ✅ Implementation Tasks

### Trend Calculations
- [ ] Calculate disparity metrics for each year
- [ ] Rate ratio trends by demographic
- [ ] Gini coefficient time series
- [ ] Absolute disparity trends

### Convergence Analysis
- [ ] Test for convergence: disparities narrowing?
- [ ] Identify diverging demographics
- [ ] Persistent gap quantification
- [ ] Statistical trend tests (Mann-Kendall, linear regression)

### Policy Impact (if applicable)
- [ ] Identify known policy interventions
- [ ] Pre-post comparison
- [ ] Interrupted time series analysis (if warranted)

### Visualization
- [ ] Trend lines: disparities over time
- [ ] Convergence/divergence charts
- [ ] Save figures

### Testing & Documentation
- [ ] Unit tests
- [ ] Docstrings
- [ ] Equity progress report

---

## 📌 Notes

**Convergence Test**:
- Slope of (demographic rate / reference rate) over time
- Negative slope = convergence (gap closing)
- Positive slope = divergence (gap widening)
- Zero slope = persistent gap

**Expected Findings**:
- Some disparities may narrow (targeted interventions working)
- Some may persist (structural barriers remain)
- Some may widen (new challenges or differential policy impacts)

---

## Implementation Plan

### 1. Feature Overview

Analyse whether healthcare disparities in Singapore are widening or narrowing across the 2006–2020 period. Compute yearly Gini coefficient time series, disparity ratio trends per demographic group, and apply Mann-Kendall monotonic trend tests to identify statistically significant convergence or divergence.

**Primary User Role**: Population Health Strategist evaluating equity progress

**Key Deliverable**: `results/tables/equity_temporal_trends.csv` with trend slope, Mann-Kendall Tau, and p-value per group, plus time-series charts in `reports/figures/ps-005/`.

---

### 2. Component Analysis & Reuse Strategy

| Component | Action | Justification |
|-----------|--------|---------------|
| `equity_analysis_integrated.parquet` | Reuse | Yearly rate_ratio per group from US-02 |
| `calculate_gini_coefficient()` from `utilization_disparity_analysis.py` | Reuse | Avoids duplicate implementation |
| `equity_temporal_trends.py` | **Create** | Trend tests, convergence/divergence logic |
| `test_equity_temporal_trends.py` | **Create** | Unit tests |

---

### 3. ML Model Evaluation & Selection

Not applicable — statistical trend analysis (Mann-Kendall + linear regression).

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/src/equity_temporal_trends.py`**
  - Functions: `compute_yearly_gini(df: pl.DataFrame) -> pl.DataFrame`, `compute_disparity_trends(df: pl.DataFrame) -> pl.DataFrame`, `mann_kendall_trend_test(values: list[float]) -> tuple[float, float, str]`, `run_temporal_equity_analysis(data_path: Path, output_dir: Path) -> pl.DataFrame`
  - Dependencies: `polars`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `loguru`
  - Logging: `logs/analysis/equity_temporal_{timestamp}.log`

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_temporal_trends.py`**

---

### 5. Data Pipeline

**Input**: `shared/data/3_interim/equity_analysis_integrated.parquet`

**Steps**:
1. Load parquet, filter `demographic_type == "age_group"`
2. For each year: compute Gini coefficient over rate values across groups
3. For each demographic group: extract `rate_ratio` series across years (one value per year)
4. Apply Mann-Kendall test to each group's rate_ratio series
5. Fit OLS regression (`rate_ratio ~ year`) to get slope, R²
6. Classify: slope < −0.01 → `"Converging"`, slope > 0.01 → `"Diverging"`, else `"Stable"`
7. Output: `results/tables/equity_temporal_trends.csv`
8. Figures: Gini time series, rate ratio trends per group → `reports/figures/ps-005/`

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/src/equity_temporal_trends.py

from pathlib import Path
from datetime import datetime

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from loguru import logger

# Import shared Gini function
from problem_statements.ps_005.src.utilization_disparity_analysis import (
    calculate_gini_coefficient,
)


def _setup_logging(log_dir: str = "logs/analysis") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(Path(log_dir) / f"equity_temporal_{ts}.log", rotation="10 MB", level="INFO")


def mann_kendall_trend_test(
    values: list[float],
) -> tuple[float, float, str]:
    """
    Non-parametric Mann-Kendall monotonic trend test.

    Args:
        values: Time-ordered series of values (one per year).

    Returns:
        Tuple of (tau, p_value, direction) where direction is one of
        'Increasing', 'Decreasing', or 'No trend'.
    """
    n = len(values)
    if n < 4:
        return 0.0, 1.0, "Insufficient data"

    arr = np.array(values, dtype=float)
    s = 0
    for k in range(n - 1):
        for j in range(k + 1, n):
            s += np.sign(arr[j] - arr[k])

    # Variance under H0 with no ties
    var_s = n * (n - 1) * (2 * n + 5) / 18.0
    if var_s == 0:
        return 0.0, 1.0, "No trend"

    z = (s - np.sign(s)) / float(np.sqrt(var_s))
    p_val = 2 * (1 - stats.norm.cdf(abs(z)))
    tau = s / (0.5 * n * (n - 1))

    if p_val < 0.05:
        direction = "Increasing" if s > 0 else "Decreasing"
    else:
        direction = "No trend"

    logger.debug(f"Mann-Kendall: tau={tau:.3f}, p={p_val:.4f}, dir={direction}")
    return round(float(tau), 4), round(float(p_val), 6), direction


def compute_yearly_gini(
    df: pl.DataFrame,
    rate_col: str = "metric_value",
    group_col: str = "demographic_group",
    year_col: str = "year",
) -> pl.DataFrame:
    """
    Compute Gini coefficient for each year across demographic groups.

    Args:
        df: Long-format DataFrame with [year, demographic_group, metric_value].
        rate_col: Column containing the utilisation rate.
        group_col: Demographic group column.
        year_col: Year column.

    Returns:
        DataFrame with columns [year, gini_coefficient].
    """
    years = sorted(df[year_col].unique().to_list())
    gini_rows = []
    for yr in years:
        rates = df.filter(pl.col(year_col) == yr)[rate_col].to_list()
        gini = calculate_gini_coefficient(rates)
        gini_rows.append({"year": yr, "gini_coefficient": gini})

    result = pl.DataFrame(gini_rows).with_columns(pl.col("year").cast(pl.Int32))
    logger.info(f"Gini time series computed: {len(years)} years")
    return result


def compute_disparity_trends(
    df: pl.DataFrame,
    ratio_col: str = "rate_ratio",
    group_col: str = "demographic_group",
    year_col: str = "year",
    slope_threshold: float = 0.01,
) -> pl.DataFrame:
    """
    Compute OLS slope and Mann-Kendall test for each demographic group's
    disparity ratio trend over time.

    Args:
        df: Long-format equity DataFrame.
        ratio_col: Column containing yearly disparity ratios.
        group_col: Demographic group column.
        year_col: Year column.
        slope_threshold: Minimum slope magnitude to classify as converging/diverging.

    Returns:
        DataFrame with trend summary per group.
    """
    groups = df[group_col].unique().to_list()
    trend_rows = []

    for group in groups:
        subset = df.filter(pl.col(group_col) == group).sort(year_col)
        ratios = subset[ratio_col].to_list()
        years = subset[year_col].to_list()

        if len(ratios) < 4:
            logger.warning(f"Insufficient data for trend test: {group} ({len(ratios)} years)")
            continue

        # OLS slope via scipy
        slope, intercept, r_value, p_ols, _ = stats.linregress(years, ratios)

        # Mann-Kendall
        mk_tau, mk_p, mk_dir = mann_kendall_trend_test(ratios)

        # Classify convergence
        if slope < -slope_threshold and mk_p < 0.05:
            convergence = "Converging (equity improving)"
        elif slope > slope_threshold and mk_p < 0.05:
            convergence = "Diverging (equity worsening)"
        else:
            convergence = "Stable (persistent gap)"

        trend_rows.append({
            "demographic_group": group,
            "ols_slope": round(float(slope), 6),
            "ols_r_squared": round(float(r_value ** 2), 4),
            "ols_p_value": round(float(p_ols), 6),
            "mk_tau": mk_tau,
            "mk_p_value": mk_p,
            "mk_direction": mk_dir,
            "convergence_status": convergence,
            "mean_ratio": round(float(sum(ratios) / len(ratios)), 4),
            "ratio_change_total": round(float(ratios[-1] - ratios[0]), 4),
        })

    result = pl.DataFrame(trend_rows).sort("ols_slope")
    logger.info(
        f"Trend analysis: {len(result)} groups analysed; "
        f"converging={result.filter(pl.col('convergence_status').str.contains('Converging')).shape[0]}, "
        f"diverging={result.filter(pl.col('convergence_status').str.contains('Diverging')).shape[0]}"
    )
    return result


def plot_disparity_trends(
    df: pl.DataFrame,
    ratio_col: str = "rate_ratio",
    group_col: str = "demographic_group",
    year_col: str = "year",
    output_path: Path | None = None,
) -> None:
    """Line chart of disparity ratio trends over time per demographic group."""
    pdf = df.to_pandas()
    fig, ax = plt.subplots(figsize=(12, 6))
    for group in pdf[group_col].unique():
        subset = pdf[pdf[group_col] == group].sort_values(year_col)
        ax.plot(subset[year_col], subset[ratio_col], marker="o", linewidth=1.5, label=group)
    ax.axhline(y=1.0, color="black", linestyle="--", linewidth=1, label="Equity (1.0)")
    ax.set_xlabel("Year", fontweight="bold")
    ax.set_ylabel("Disparity Ratio vs Reference Group", fontweight="bold")
    ax.set_title("Temporal Trends in Healthcare Disparity Ratios", fontweight="bold")
    ax.legend(fontsize=8, bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Trend chart saved: {output_path}")
    plt.show()
    plt.close()


def plot_gini_timeseries(
    gini_df: pl.DataFrame,
    output_path: Path | None = None,
) -> None:
    """Line chart of Gini coefficient over time."""
    pdf = gini_df.to_pandas()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(pdf["year"], pdf["gini_coefficient"], marker="o", color="#2166ac", linewidth=2)
    ax.set_xlabel("Year", fontweight="bold")
    ax.set_ylabel("Gini Coefficient", fontweight="bold")
    ax.set_title("Healthcare Utilisation Gini Coefficient (2006–2020)", fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Gini time series chart saved: {output_path}")
    plt.show()
    plt.close()


def run_temporal_equity_analysis(
    data_path: Path,
    output_dir: Path,
) -> pl.DataFrame:
    """
    Full temporal equity trend pipeline.

    Args:
        data_path: Path to equity_analysis_integrated.parquet.
        output_dir: Root results directory.

    Returns:
        Trend summary DataFrame.
    """
    _setup_logging()
    tables_dir = output_dir / "tables"
    figures_dir = output_dir.parent / "reports" / "figures" / "ps-005"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    df = pl.read_parquet(data_path)
    age_df = df.filter(pl.col("demographic_type") == "age_group")

    if age_df.is_empty():
        raise ValueError("No age_group rows in integrated dataset")

    gini_df = compute_yearly_gini(age_df)
    gini_df.write_csv(tables_dir / "gini_timeseries.csv")

    trend_df = compute_disparity_trends(age_df)
    trend_df.write_csv(tables_dir / "equity_temporal_trends.csv")
    logger.info(f"Temporal trends saved: {tables_dir / 'equity_temporal_trends.csv'}")

    plot_disparity_trends(
        age_df,
        output_path=figures_dir / "disparity_ratio_trends.png",
    )
    plot_gini_timeseries(
        gini_df,
        output_path=figures_dir / "gini_coefficient_timeseries.png",
    )
    return trend_df
```

---

### 7. Domain-Driven Feature Engineering

| Metric | Formula | Available |
|--------|---------|----------|
| Gini time series | Per-year Gini over age groups | ✅ |
| OLS slope of rate_ratio | `Δratio / Δyear` | ✅ |
| Mann-Kendall Tau | Non-parametric trend statistic | ✅ |
| Interrupted time series | Requires known policy intervention date | ⚠️ (document if known, otherwise skip) |

---

### 10. Testing Strategy

```python
# problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_temporal_trends.py

import pytest
from problem_statements.ps_005.src.equity_temporal_trends import mann_kendall_trend_test


def test_mann_kendall_increasing_trend():
    values = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
    tau, p_val, direction = mann_kendall_trend_test(values)
    assert direction == "Increasing"
    assert p_val < 0.05
    assert tau > 0


def test_mann_kendall_decreasing_trend():
    values = [2.0, 1.8, 1.6, 1.4, 1.2, 1.0, 0.8]
    tau, p_val, direction = mann_kendall_trend_test(values)
    assert direction == "Decreasing"
    assert tau < 0


def test_mann_kendall_no_trend():
    values = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    tau, p_val, direction = mann_kendall_trend_test(values)
    assert direction == "No trend"
    assert p_val >= 0.05


def test_mann_kendall_insufficient_data():
    values = [1.0, 1.2, 1.1]
    tau, p_val, direction = mann_kendall_trend_test(values)
    assert direction == "Insufficient data"
```

---

### 11. Implementation Steps

**Phase 1 — Gini Time Series**
- [ ] Run `compute_yearly_gini()` on age_group subset
- [ ] Plot Gini coefficient 2006–2020; identify if trend is upward (worsening equity)

**Phase 2 — Group-Level Trend Analysis**
- [ ] Run `compute_disparity_trends()` for all age groups
- [ ] Review convergence_status column — expect elderly group likely Stable or Diverging

**Phase 3 — Sex Dimension**
- [ ] Repeat trend analysis for `demographic_type == "sex"` subset

**Phase 4 — Output & Testing**
- [ ] Write `results/tables/equity_temporal_trends.csv` and `gini_timeseries.csv`
- [ ] Generate figures; run pytest ≥80% coverage

---

### 12. Adaptive Implementation Strategy

- If insufficient years per group for Mann-Kendall (< 4) → report `"Insufficient data"` in convergence_status
- If Gini shows no trend → focus analysis on comparing first and last 3-year averages rather than full trend
- If data ends at 2019 rather than 2020 → update year range in output; document in README

---

### 20. Security & Privacy

Aggregated data only. Results saved to `results/` (git-ignored).

---

### 21. Version Control

- Branch: `feature/ps-005-temporal-equity-trends`
- Commits:
  - `feat(ps-005): add Mann-Kendall trend test and Gini time series analysis`
  - `test(ps-005): add unit tests for mann_kendall_trend_test`
