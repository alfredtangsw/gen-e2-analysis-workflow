# Analyze Healthcare Utilization Disparities (Lifecycle Stage: Exploratory Data Analysis)

**Story ID**: PS-005-US-03  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P0 (Critical)  
**Effort Estimate**: M (5 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Population Health Strategist assessing healthcare access equity**,  
I want **to quantify utilization disparities across demographic groups (age, sex) to identify underserved and overserved populations**,  
So that **I can recommend targeted interventions to reduce access barriers and improve healthcare equity**.

---

## 🎯 Acceptance Criteria

1. **Disparities quantified**
   - Rate ratios calculated: demographic group rate / reference rate
   - Absolute disparities: rate differences
   - Disparity magnitude rankings
   - Statistical significance testing

2. **Demographic patterns identified**
   - High-utilization demographics
   - Low-utilization (underserved) demographics
   - Age-sex interaction effects
   - Temporal trends in disparities

3. **Concentration metrics**
   - Lorenz curves: utilization concentration
   - Gini coefficient: inequality measure
   - Theil index: disparity decomposition

4. **Deliverables**
   - Output: `results/tables/utilization_disparity_analysis.csv`
   - Figures: Disparity charts, Lorenz curves
   - Report: Utilization equity assessment

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9
- **Primary Library**: Polars 0.20+
- **Statistical Analysis**: scipy, statsmodels
- **Visualization**: Matplotlib/Seaborn
- **Logging**: loguru
- **Testing**: pytest ≥80% coverage

---

## 📚 Domain Knowledge References

- [Domain Knowledge Research](../../../problem_statements/DOMAIN_KNOWLEDGE_RESEARCH.md#health-equity-disparity-metrics)
- [Problem Statement PS-005](../../../problem_statements/ps-005-healthcare-equity-disparities.md#objective-1)

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`, `scipy>=1.11.0`, `matplotlib>=3.8.0`, `seaborn>=0.13.0`, `loguru>=0.7.0`

### Internal Dependencies
- **Upstream**: PS-005-US-02 (Equity data prep - BLOCKING)
- **Data Sources**: `shared/data/3_interim/equity_analysis_integrated.parquet`

---

## ✅ Implementation Tasks

### Disparity Calculation
- [ ] Calculate rate ratios for each demographic group
- [ ] Calculate absolute disparities (rate differences)
- [ ] Rank demographics by disparity magnitude
- [ ] Statistical significance tests (chi-square, t-tests)

### Pattern Identification
- [ ] Identify high-utilization groups (rate ratio >1.5)
- [ ] Identify low-utilization groups (rate ratio <0.67)
- [ ] Analyze age-sex interactions
- [ ] Temporal trend analysis: disparities widening or narrowing?

### Concentration Analysis
- [ ] Calculate Lorenz curve coordinates
- [ ] Compute Gini coefficient
- [ ] Calculate Theil index
- [ ] Decompose inequality by demographic dimensions

### Visualization
- [ ] Rate ratio charts
- [ ] Lorenz curves
- [ ] Disparity heatmaps
- [ ] Save figures

### Testing & Documentation
- [ ] Unit tests
- [ ] Docstrings
- [ ] Equity assessment report

---

## 📌 Notes

**Rate Ratio Interpretation**:
- Rate ratio = 1.0: No disparity (equal utilization)
- Rate ratio > 1.5: High utilization (potential overuse or higher need)
- Rate ratio < 0.67: Low utilization (potential access barriers)

**Gini Coefficient**:
- 0 = Perfect equality
- 1 = Perfect inequality
- Healthcare typically Gini ~0.2-0.4

---

## Implementation Plan

### 1. Feature Overview

Quantify healthcare utilisation disparities across age groups and sex using admission rate data. Compute rate ratios, absolute disparities, Gini coefficient, and Lorenz curve coordinates. Test statistical significance for all disparity ratios. Deliver disparity rankings and concentration metrics to guide equity interventions.

**Primary User Role**: Population Health Strategist assessing healthcare access equity

**Key Deliverable**: `results/tables/utilization_disparity_analysis.csv` and Lorenz curve / disparity bar charts in `reports/figures/ps-005/`.

---

### 2. Component Analysis & Reuse Strategy

| Component | Location | Action | Justification |
|-----------|----------|--------|---------------|
| Integrated equity data | `shared/data/3_interim/equity_analysis_integrated.parquet` | Reuse | Upstream US-02 output |
| `health-equity-metrics-kpis.md` | `docs/domain-knowledge/` | Reference | Gini, Lorenz, rate ratio formulas |
| Visualization helpers pattern | See prompt reference | Adapt | `plot_line_trends`, `plot_bar_distribution` |
| `utilization_disparity_analysis.py` | `ps-005/src/` | **Create** | All disparity computation logic |
| `test_utilization_disparity.py` | `ps-005/tests/unit/` | **Create** | ≥80% coverage |

---

### 3. ML Model Evaluation & Selection

Not applicable — this is a statistical EDA story using descriptive and inferential statistics only.

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/src/utilization_disparity_analysis.py`**
  - Functions: `calculate_rate_ratios(df: pl.DataFrame) -> pl.DataFrame`, `calculate_gini_coefficient(rates: list[float]) -> float`, `calculate_lorenz_curve(rates: list[float]) -> tuple[list[float], list[float]]`, `calculate_disparity_significance(df: pl.DataFrame) -> pl.DataFrame`, `run_utilization_disparity_analysis(data_path: Path, output_dir: Path) -> pl.DataFrame`
  - Dependencies: `polars`, `scipy`, `numpy`, `matplotlib`, `seaborn`, `loguru`
  - Logging: `logs/analysis/utilization_disparity_{timestamp}.log`

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/notebooks/03-utilization-disparity-analysis.ipynb`**
  - Runs full analysis end-to-end with narrative

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_utilization_disparity.py`**

---

### 5. Data Pipeline

**Input**: `shared/data/3_interim/equity_analysis_integrated.parquet`

**Steps**:
1. Load parquet with `pl.read_parquet()`, filter `demographic_type ∈ {"age_group", "sex"}`
2. Compute per-year, per-group rate ratios (already in integrated data — verify and recompute if needed)
3. Aggregate: compute mean rate ratio across all years per group
4. Rank groups by mean rate ratio (descending)
5. Calculate Gini coefficient over group rates per year
6. Calculate Lorenz curve coordinates for most recent year
7. Statistical tests: t-test / Mann-Whitney U for each group vs reference
8. Output: `results/tables/utilization_disparity_analysis.csv`
9. Figures: bar chart (rate ratios), Lorenz curve → `reports/figures/ps-005/`

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/src/utilization_disparity_analysis.py

from pathlib import Path
from datetime import datetime
from typing import Union

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from loguru import logger


def _setup_logging(log_dir: str = "logs/analysis") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(
        Path(log_dir) / f"utilization_disparity_{ts}.log",
        rotation="10 MB",
        level="INFO",
    )


def calculate_gini_coefficient(rates: list[float]) -> float:
    """
    Calculate Gini coefficient for a distribution of rates.

    A value of 0 represents perfect equality; 1 represents maximum inequality.

    Args:
        rates: List of utilisation rates across demographic groups.

    Returns:
        Gini coefficient in [0, 1].
    """
    arr = np.array(sorted(rates), dtype=float)
    n = len(arr)
    if n == 0 or arr.sum() == 0:
        return 0.0
    cumulative = np.cumsum(arr)
    # Using the standard formula: G = (2 * sum(i * x_i)) / (n * sum(x)) - (n+1)/n
    indices = np.arange(1, n + 1)
    gini = (2.0 * np.dot(indices, arr)) / (n * cumulative[-1]) - (n + 1) / n
    return float(round(gini, 4))


def calculate_lorenz_curve(
    rates: list[float],
) -> tuple[list[float], list[float]]:
    """
    Compute Lorenz curve coordinates.

    Returns:
        Tuple of (cumulative_population_share, cumulative_rate_share),
        both starting at (0, 0).
    """
    arr = np.array(sorted(rates), dtype=float)
    n = len(arr)
    cum_pop = np.linspace(0, 1, n + 1)
    cum_rate = np.concatenate([[0.0], np.cumsum(arr) / arr.sum()])
    return cum_pop.tolist(), cum_rate.tolist()


def calculate_disparity_significance(
    df: pl.DataFrame,
    value_col: str = "metric_value",
    group_col: str = "demographic_group",
    ref_group: str | None = None,
) -> pl.DataFrame:
    """
    Test whether each demographic group's rate is significantly different
    from the reference group using a two-sample t-test.

    Args:
        df: Long-format DataFrame with columns [demographic_group, metric_value, year].
        value_col: Column containing the utilisation rate.
        group_col: Column identifying demographic groups.
        ref_group: Reference group label. If None, uses the group with lowest mean rate.

    Returns:
        DataFrame with columns [demographic_group, mean_rate, t_statistic, p_value,
        significant_at_05, effect_size_cohens_d].
    """
    groups = df[group_col].unique().to_list()

    if ref_group is None:
        means = df.group_by(group_col).agg(pl.col(value_col).mean().alias("mean"))
        ref_group = means.sort("mean")[group_col][0]
        logger.info(f"Auto-selected reference group: {ref_group}")

    ref_rates = df.filter(pl.col(group_col) == ref_group)[value_col].to_list()

    results = []
    for group in groups:
        group_rates = df.filter(pl.col(group_col) == group)[value_col].to_list()
        mean_rate = float(np.mean(group_rates))

        if group == ref_group or len(group_rates) < 2:
            results.append({
                "demographic_group": group,
                "mean_rate": mean_rate,
                "t_statistic": 0.0,
                "p_value": 1.0,
                "significant_at_05": False,
                "effect_size_cohens_d": 0.0,
            })
            continue

        t_stat, p_val = stats.ttest_ind(group_rates, ref_rates, equal_var=False)
        pooled_std = np.sqrt(
            (np.std(group_rates, ddof=1) ** 2 + np.std(ref_rates, ddof=1) ** 2) / 2
        )
        cohens_d = (
            (mean_rate - float(np.mean(ref_rates))) / pooled_std
            if pooled_std > 0 else 0.0
        )
        results.append({
            "demographic_group": group,
            "mean_rate": round(mean_rate, 2),
            "t_statistic": round(float(t_stat), 4),
            "p_value": round(float(p_val), 6),
            "significant_at_05": bool(p_val < 0.05),
            "effect_size_cohens_d": round(float(cohens_d), 4),
        })

    return pl.DataFrame(results)


def plot_disparity_bar(
    summary_df: pl.DataFrame,
    metric_col: str = "mean_rate_ratio",
    group_col: str = "demographic_group",
    title: str = "Utilisation Rate Ratios by Demographic Group",
    output_path: Path | None = None,
) -> None:
    """Horizontal bar chart of rate ratios by demographic group."""
    pdf = summary_df.sort(metric_col).to_pandas()
    fig, ax = plt.subplots(figsize=(10, 6))
    colours = [
        "#d73027" if v > 1.5 else ("#4575b4" if v < 0.67 else "#74add1")
        for v in pdf[metric_col]
    ]
    ax.barh(pdf[group_col], pdf[metric_col], color=colours)
    ax.axvline(x=1.0, color="black", linewidth=1.2, linestyle="--", label="Equity line (1.0)")
    ax.axvline(x=1.5, color="#d73027", linewidth=0.8, linestyle=":", label="High disparity (1.5)")
    ax.axvline(x=0.67, color="#4575b4", linewidth=0.8, linestyle=":", label="Low disparity (0.67)")
    ax.set_xlabel("Rate Ratio (vs reference group)", fontweight="bold")
    ax.set_title(title, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Disparity bar chart saved: {output_path}")
    plt.show()
    plt.close()


def plot_lorenz_curve(
    rates: list[float],
    title: str = "Lorenz Curve — Healthcare Utilisation by Age Group",
    output_path: Path | None = None,
) -> None:
    """Plot Lorenz curve with Gini annotation."""
    cum_pop, cum_rate = calculate_lorenz_curve(rates)
    gini = calculate_gini_coefficient(rates)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot(cum_pop, cum_rate, "b-", linewidth=2, label=f"Lorenz curve (Gini={gini:.3f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Perfect equality")
    ax.fill_between(cum_pop, cum_pop, cum_rate, alpha=0.15, color="blue")
    ax.set_xlabel("Cumulative population share", fontweight="bold")
    ax.set_ylabel("Cumulative utilisation share", fontweight="bold")
    ax.set_title(title, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Lorenz curve saved: {output_path}")
    plt.show()
    plt.close()


def run_utilization_disparity_analysis(
    data_path: Path,
    output_dir: Path,
) -> pl.DataFrame:
    """
    Full utilisation disparity analysis pipeline.

    Args:
        data_path: Path to equity_analysis_integrated.parquet.
        output_dir: Directory for results tables and figures.

    Returns:
        Disparity summary DataFrame.
    """
    _setup_logging()
    logger.info("Starting utilisation disparity analysis")

    df = pl.read_parquet(data_path)
    age_df = df.filter(pl.col("demographic_type") == "age_group")

    if age_df.is_empty():
        raise ValueError("No age_group rows found in integrated dataset")

    # Summary stats per group across all years
    summary = (
        age_df
        .group_by("demographic_group")
        .agg([
            pl.col("metric_value").mean().round(2).alias("mean_rate"),
            pl.col("metric_value").std().round(2).alias("std_rate"),
            pl.col("rate_ratio").mean().round(3).alias("mean_rate_ratio"),
            pl.col("absolute_disparity").mean().round(2).alias("mean_abs_disparity"),
            pl.col("disparity_flag").sum().alias("years_flagged"),
        ])
        .sort("mean_rate_ratio", descending=True)
    )

    # Statistical significance vs reference
    sig_df = calculate_disparity_significance(age_df, ref_group=None)
    summary = summary.join(sig_df, on="demographic_group", how="left")

    # Concentration metrics for most recent year
    latest_year = int(age_df["year"].max())
    latest_rates = (
        age_df
        .filter(pl.col("year") == latest_year)
        .sort("demographic_group")["metric_value"]
        .to_list()
    )
    gini = calculate_gini_coefficient(latest_rates)
    logger.info(f"Gini coefficient ({latest_year}): {gini:.4f}")

    # Save outputs
    tables_dir = output_dir / "tables"
    figures_dir = output_dir.parent / "reports" / "figures" / "ps-005"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    summary.write_csv(tables_dir / "utilization_disparity_analysis.csv")
    logger.info(f"Results saved: {tables_dir / 'utilization_disparity_analysis.csv'}")

    plot_disparity_bar(
        summary,
        output_path=figures_dir / "utilization_rate_ratios.png",
    )
    plot_lorenz_curve(
        latest_rates,
        output_path=figures_dir / "lorenz_curve_utilization.png",
    )

    logger.info(f"Analysis complete — Gini={gini:.4f}, {len(summary)} groups analysed")
    return summary
```

---

### 7. Domain-Driven Feature Engineering

**Computed metrics** (all grounded in `health-equity-metrics-kpis.md`):

| Metric | Formula | Data Source | Available |
|--------|---------|-------------|----------|
| Rate Ratio (age) | `rate_65+ / rate_25-44` | `metric_value`, `rate_ratio` in parquet | ✅ |
| Rate Ratio (sex) | `rate_female / rate_male` | Same | ✅ |
| Absolute Disparity | `rate_i - rate_ref` | `absolute_disparity` in parquet | ✅ |
| Gini Coefficient | Standard formula | Computed from yearly rates | ✅ |
| Lorenz Curve | Cumulative shares | Computed from yearly rates | ✅ |
| Concentration Index (SES) | Requires SES rank | Not available | ❌ |

---

### 10. Testing Strategy

```python
# problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_utilization_disparity.py

import pytest
from problem_statements.ps_005.src.utilization_disparity_analysis import (
    calculate_gini_coefficient,
    calculate_lorenz_curve,
)


def test_gini_perfect_equality():
    """Uniform distribution should give Gini ≈ 0."""
    rates = [100.0, 100.0, 100.0, 100.0]
    assert calculate_gini_coefficient(rates) == pytest.approx(0.0, abs=0.01)


def test_gini_high_inequality():
    """Concentrated distribution should give Gini > 0.3."""
    rates = [10.0, 10.0, 10.0, 500.0]
    gini = calculate_gini_coefficient(rates)
    assert gini > 0.3


def test_lorenz_curve_starts_and_ends_correctly():
    rates = [50.0, 100.0, 200.0, 300.0]
    cum_pop, cum_rate = calculate_lorenz_curve(rates)
    assert cum_pop[0] == pytest.approx(0.0)
    assert cum_pop[-1] == pytest.approx(1.0)
    assert cum_rate[0] == pytest.approx(0.0)
    assert cum_rate[-1] == pytest.approx(1.0)


def test_lorenz_curve_is_concave_below_equality_line():
    rates = [50.0, 100.0, 200.0, 300.0]
    cum_pop, cum_rate = calculate_lorenz_curve(rates)
    for p, r in zip(cum_pop, cum_rate):
        assert r <= p + 1e-9  # Lorenz curve is always at or below equality line
```

---

### 11. Implementation Steps

**Phase 1 — Load & Profile**
- [ ] Load `equity_analysis_integrated.parquet`; confirm `age_group` and `sex` demographic_type rows present
- [ ] Check distinct age group labels; verify reference group label matches actual data

**Phase 2 — Disparity Computation**
- [ ] Run `run_utilization_disparity_analysis()` end-to-end
- [ ] Review disparity summary table — spot-check `65+ years` rate_ratio > 3.0 expected
- [ ] Compute and log Gini coefficient

**Phase 3 — Statistical Significance**
- [ ] Run `calculate_disparity_significance()` for age groups
- [ ] Flag groups with p < 0.05 AND effect size |d| > 0.5 as analytically significant

**Phase 4 — Visualisation**
- [ ] Generate rate ratio bar chart and Lorenz curve
- [ ] Save to `reports/figures/ps-005/`

**Phase 5 — Output & Testing**
- [ ] Write `results/tables/utilization_disparity_analysis.csv`
- [ ] Run pytest with ≥80% coverage

---

### 12. Adaptive Implementation Strategy

- If `age_group` labels don't match `"25-44 years"` → infer reference group as lowest-rate group automatically (implemented)
- If < 3 years of data per group → t-test may be unreliable; switch to reporting only effect size and descriptive statistics
- If Gini < 0.05 → document that utilisation is near-equitable; pivot analysis to outcome disparities

---

### 14. Data Quality & Validation

| Check | Expected | Action |
|-------|----------|--------|
| Rows after filter | > 100 age_group rows | Error if < 50 |
| Rate values | All > 0 | Log and filter negatives |
| Rate ratios | All > 0 | Raise if negative found |
| Gini range | [0, 1] | Raise if outside range |
| Output CSV rows | 1 row per demographic_group | Validate count |

---

### 15. Statistical Analysis

**Methods**:
- Two-sample Welch t-test (unequal variance, small n) for group vs reference significance testing
- Cohen's d as effect size
- Gini coefficient as concentration measure
- Lorenz curve as visual inequality measure

**Significance level**: α = 0.05 with Bonferroni correction applied (`α_corrected = 0.05 / n_groups`) to control family-wise error

**Limitations**: Small temporal samples (15 data points per group) limit statistical power. Descriptive findings should be interpreted with caution.

---

### 20. Security & Privacy

Aggregated data only. No PII. Analysis outputs saved to `results/` which is git-ignored.

---

### 21. Version Control

- Branch: `feature/ps-005-utilization-disparity-analysis`
- Commits:
  - `feat(ps-005): add utilization disparity analysis with gini and lorenz`
  - `test(ps-005): add gini coefficient and lorenz curve unit tests`
