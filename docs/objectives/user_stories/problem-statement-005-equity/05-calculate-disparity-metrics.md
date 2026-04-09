# Calculate Health Equity Disparity Metrics (Lifecycle Stage: Feature Engineering)

**Story ID**: PS-005-US-05  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P0 (Critical)  
**Effort Estimate**: M (4-5 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Population Health Equity Analyst**,  
I want **to calculate standardized disparity metrics (disparity ratios, concentration indices, Gini coefficients) comparing health outcomes and utilization across demographic groups**,  
So that **I can quantify the magnitude of health inequities and track progress toward equity goals using internationally recognized methodologies**.

---

## 🎯 Acceptance Criteria

1. **Disparity ratios calculated**
   - Utilization disparity ratio: `(utilization_group_A / utilization_group_B)` 
   - Mortality disparity ratio: `(mortality_rate_group_A / mortality_rate_group_B)`
   - Reference group selection documented (e.g., lowest-risk age group, male vs female)
   - Ratios calculated for all demographic comparisons (age groups, gender)

2. **Concentration indices computed**
   - Concentration index: measures inequality in health variable distribution across socioeconomic/demographic ranking
   - Formula: `C = (2/μ) * Cov(health_variable, fractional_rank) / n`
   - Range: -1 to +1 (0 = perfect equality, positive = pro-rich/advantaged, negative = pro-poor/disadvantaged)
   - Calculated for key outcomes: mortality, utilization, disease prevalence

3. **Statistical significance tested**
   - Confidence intervals calculated for disparity ratios (bootstrap or analytical methods)
   - Test if disparity ratio significantly different from 1.0 (equity)
   - Test if concentration index significantly different from 0 (equity)

4. **Data output requirement**
   - Output file: `results/tables/equity_disparity_metrics.csv`
   - Format: CSV (metric_type, demographic_comparison, disparity_ratio, concentration_index, ci_lower, ci_upper, p_value, interpretation)
   - Equity visualization: `reports/figures/disparity_metrics_forest_plot.png`

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9
- **Primary Library**: Polars 0.20+ (MANDATORY)
- **Statistics**: scipy.stats for bootstrap, significance tests
- **Logging**: loguru
- **Testing**: pytest with ≥80% coverage

---

## 📚 Domain Knowledge References

- [Problem Statement PS-005](../../../problem_statements/ps-005-healthcare-equity-disparities.md#objectives) - Objective 3: Diagnose inequities with standardized metrics
- Health equity literature: WHO Health Equity Assessment Toolkit (HEAT), Concentration Index methodology

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`: Data processing
- `scipy>=1.11.0`: Statistical tests, bootstrap
- `matplotlib>=3.8.0`: Forest plots
- `loguru>=0.7.0`: Logging

### Internal Dependencies
- **Upstream**: 
  - PS-005-US-03 (Utilization disparities - BLOCKING)
  - PS-005-US-04 (Outcome disparities - BLOCKING)
- **Data Sources**: 
  - `shared/data/3_interim/equity_analysis_integrated.parquet`
- **Config Files**: `config/analysis.yml` (reference groups, significance thresholds)

---

## ✅ Implementation Tasks

### Reference Group Selection
- [ ] Define reference groups for disparity ratios:
  - Age: 25-44 years (prime working age, typically lowest risk)
  - Gender: Male (standard in epidemiology, though arbitrary)
  - Document rationale for reference group choice

### Disparity Ratio Calculation
- [ ] Calculate utilization disparity ratios:
  - For each age group vs reference: `ratio = utilization_age_i / utilization_age_ref`
  - For gender: `ratio = utilization_female / utilization_male`
  
- [ ] Calculate mortality disparity ratios:
  - Age-specific: Compare each age group to reference
  - Gender: Female vs male mortality rates
  
- [ ] Interpret ratios:
  - Ratio = 1.0: Equity (no disparity)
  - Ratio > 1.0: Group has higher utilization/mortality than reference
  - Ratio < 1.0: Group has lower utilization/mortality than reference

### Concentration Index Calculation
- [ ] Rank population by socioeconomic proxy (age as proxy, or use admission rate as health need ranking)
- [ ] Calculate fractional rank: `r_i = (2i - 1) / (2n)` where i is rank position
- [ ] Calculate concentration index: `C = (2/μ) * Σ[(y_i - μ) * r_i] / n`
  - Where μ = mean health variable, y_i = individual health outcome
  
- [ ] Alternatively, use regression method:
  - Regress health variable on fractional rank
  - C = β * (2σ_r / μ)

### Gini Coefficient (Optional)
- [ ] Calculate Gini coefficient for utilization distribution across groups
- [ ] Formula: `G = (Σ Σ |x_i - x_j|) / (2n² * mean(x))`
- [ ] Interpret: 0 = perfect equality, 1 = perfect inequality

### Statistical Significance
- [ ] Bootstrap confidence intervals:
  - Resample data 1,000 times with replacement
  - Calculate disparity ratio for each bootstrap sample
  - 95% CI: 2.5th and 97.5th percentiles
  
- [ ] Test significance:
  - Disparity ratio: CI excludes 1.0 → significant disparity
  - Concentration index: t-test if C significantly different from 0

### Interpretation & Classification
- [ ] Classify disparity magnitude:
  - Minimal: ratio 0.8-1.2 (±20%)
  - Moderate: ratio 0.5-0.8 or 1.2-2.0
  - Large: ratio <0.5 or >2.0
  
- [ ] Priority ranking: rank demographic comparisons by disparity magnitude

### Visualization
- [ ] Forest plot: disparity ratios with 95% CI error bars
- [ ] Concentration curves: cumulative health vs cumulative population rank
- [ ] Equity gap charts: bar chart showing gap magnitude per demographic
- [ ] Export figures

### Testing & Validation
- [ ] Unit tests for disparity ratio calculation
- [ ] Validate concentration index: compare against published examples
- [ ] Test bootstrap: ensure CI width reasonable
- [ ] Test edge cases: perfect equality, extreme inequality

### Documentation
- [ ] Docstrings (Google style)
- [ ] Methodology document: `results/equity_metrics_methodology.md`
  - Reference group selection rationale
  - Concentration index calculation method
  - Bootstrap procedure details
  - Interpretation guidelines
- [ ] Equity metrics glossary: explain metrics to non-technical stakeholders
- [ ] Update data dictionary

---

## 📌 Notes

**Disparity Ratio Calculation (Polars)**:
```python
import polars as pl

# Reference group: age 25-44
ref_utilization = df.filter(pl.col('age_group') == '25-44').select('utilization_rate').mean()

# Calculate ratios for all age groups
df_disparity = (
    df.group_by('age_group').agg([
        pl.col('utilization_rate').mean().alias('mean_utilization')
    ])
    .with_columns([
        (pl.col('mean_utilization') / ref_utilization).alias('disparity_ratio')
    ])
)
```

**Concentration Index (Python)**:
```python
import numpy as np
import polars as pl

# Prepare data
df_sorted = df.sort('socioeconomic_rank')  # or age as proxy
y = df_sorted['health_outcome'].to_numpy()
n = len(y)
mu = y.mean()

# Fractional rank
r = np.array([(2*i - 1) / (2*n) for i in range(1, n+1)])

# Concentration index
C = (2 / mu) * np.sum((y - mu) * r) / n

logger.info(f"Concentration Index: {C:.4f}")
# Interpretation: C>0 (pro-rich), C<0 (pro-poor), C≈0 (equity)
```

**Bootstrap Confidence Intervals**:
```python
from scipy.stats import bootstrap
import numpy as np

def disparity_ratio(sample):
    group_a = sample[sample['group'] == 'A']['outcome'].mean()
    group_b = sample[sample['group'] == 'B']['outcome'].mean()
    return group_a / group_b

# Bootstrap
rng = np.random.default_rng()
bootstrap_result = bootstrap(
    (df,), 
    disparity_ratio, 
    n_resamples=1000, 
    confidence_level=0.95,
    random_state=rng
)

ci_lower, ci_upper = bootstrap_result.confidence_interval
logger.info(f"Disparity Ratio: {ratio:.2f} (95% CI: {ci_lower:.2f}-{ci_upper:.2f})")
```

**Expected Metrics** (hypotheses):
- **Age disparities**: Elderly (65+) likely have 3-5x higher utilization than 25-44 (expected due to health needs)
- **Gender disparities**: Women may have 1.2-1.5x higher primary care utilization (reproductive health, longer life expectancy)
- **Concentration index**: Likely near 0 for Singapore (universal healthcare system promotes equity)

**Interpretation Guidelines**:
| Metric | Value | Interpretation | Action |
|--------|-------|----------------|--------|
| Disparity Ratio | 0.8-1.2 | Minimal disparity | Monitor |
| Disparity Ratio | 1.2-2.0 or 0.5-0.8 | Moderate disparity | Investigate causes |
| Disparity Ratio | >2.0 or <0.5 | Large disparity | Priority intervention target |
| Concentration Index | -0.2 to +0.2 | Relatively equitable | Maintain |
| Concentration Index | >0.2 or <-0.2 | Significant inequality | Policy review needed |

**Limitations**:
- Limited socioeconomic stratification in data (may miss income/education disparities)
- Age as proxy for socioeconomic rank is imperfect
- National-level analysis misses geographic inequities
- Some disparities may be clinically justified (e.g., elderly having higher utilization due to greater health needs)

---

## Implementation Plan

### 1. Feature Overview

Calculate standardised disparity metrics (disparity ratios, concentration indices, and bootstrap confidence intervals) for all demographic comparisons (age groups and sex). Produce internationally recognised equity indicators that can be tracked over time and compared against benchmarks.

**Primary User Role**: Population Health Equity Analyst

**Key Deliverable**: `results/tables/equity_disparity_metrics.csv` with columns `[metric_type, demographic_comparison, disparity_ratio, ci_lower, ci_upper, p_value, interpretation]` and a forest plot figure.

---

### 2. Component Analysis & Reuse Strategy

| Component | Action | Justification |
|-----------|--------|---------------|
| `equity_analysis_integrated.parquet` | Reuse | All disparity ratios already computed |
| `calculate_disparity_significance()` from `utilization_disparity_analysis.py` | Reuse | Avoids duplicate t-test code |
| `equity_disparity_metrics.py` | **Create** | Bootstrap CI, concentration index, forest plot |
| `test_equity_disparity_metrics.py` | **Create** | Unit tests for CI and concentration index |

---

### 3. ML Model Evaluation & Selection

Not applicable — statistical feature engineering story.

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/src/equity_disparity_metrics.py`**
  - Functions: `bootstrap_disparity_ci(group_rates: list[float], ref_rates: list[float], n_boot: int = 1000) -> tuple[float, float, float]`, `calculate_concentration_index(health_var: list[float], rank_var: list[float]) -> float`, `compile_disparity_metrics(integrated_df: pl.DataFrame) -> pl.DataFrame`, `plot_forest_plot(metrics_df: pl.DataFrame, output_path: Path) -> None`
  - Dependencies: `polars`, `numpy`, `scipy`, `matplotlib`, `loguru`
  - Logging: `logs/analysis/equity_metrics_{timestamp}.log`

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_disparity_metrics.py`**

---

### 5. Data Pipeline

**Input**: `shared/data/3_interim/equity_analysis_integrated.parquet`

**Steps**:
1. Load parquet, filter to `demographic_type` ∈ {`"age_group"`, `"sex"`}
2. For each demographic comparison (group vs reference):
   a. Compute disparity ratio (already in parquet column `rate_ratio`)
   b. Bootstrap CI: resample `metric_value` series 1,000 times, compute 2.5th/97.5th percentile of ratio
   c. Compute p-value from Welch t-test
   d. Interpret: `"Equitable"` (CI includes 1.0), `"Higher burden"` (CI > 1.0), `"Under-utilised"` (CI < 1.0)
3. Compute concentration index (age rank proxy):
   a. Rank age groups by mean rate (proxy for need ranking)
   b. Apply `CI = (2 / mean) * cov(health_var, rank) / n`
4. Output: `results/tables/equity_disparity_metrics.csv`
5. Figure: Forest plot → `reports/figures/ps-005/disparity_metrics_forest_plot.png`

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/src/equity_disparity_metrics.py

from pathlib import Path
from datetime import datetime

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from scipy import stats
from loguru import logger


def _setup_logging(log_dir: str = "logs/analysis") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(Path(log_dir) / f"equity_metrics_{ts}.log", rotation="10 MB", level="INFO")


def bootstrap_disparity_ci(
    group_rates: list[float],
    ref_rates: list[float],
    n_boot: int = 1000,
    alpha: float = 0.05,
    random_seed: int = 42,
) -> tuple[float, float, float]:
    """
    Compute bootstrap confidence interval for the disparity ratio.

    Estimates ratio = mean(group_rates) / mean(ref_rates) and its uncertainty
    via non-parametric bootstrap resampling.

    Args:
        group_rates: Yearly rates for the demographic group of interest.
        ref_rates: Yearly rates for the reference group.
        n_boot: Number of bootstrap replicates.
        alpha: Significance level (default 0.05 for 95% CI).
        random_seed: RNG seed for reproducibility.

    Returns:
        Tuple of (point_estimate, ci_lower, ci_upper).
    """
    rng = np.random.default_rng(random_seed)
    g = np.array(group_rates, dtype=float)
    r = np.array(ref_rates, dtype=float)

    if len(g) == 0 or len(r) == 0 or r.mean() == 0:
        return 0.0, 0.0, 0.0

    point_est = g.mean() / r.mean()
    boot_ratios = np.zeros(n_boot)
    for i in range(n_boot):
        g_sample = rng.choice(g, size=len(g), replace=True)
        r_sample = rng.choice(r, size=len(r), replace=True)
        denom = r_sample.mean()
        boot_ratios[i] = g_sample.mean() / denom if denom != 0 else np.nan

    boot_ratios = boot_ratios[~np.isnan(boot_ratios)]
    ci_lower = float(np.percentile(boot_ratios, 100 * alpha / 2))
    ci_upper = float(np.percentile(boot_ratios, 100 * (1 - alpha / 2)))
    logger.debug(f"Bootstrap CI: {point_est:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]")
    return round(point_est, 4), round(ci_lower, 4), round(ci_upper, 4)


def calculate_concentration_index(
    health_var: list[float],
    rank_var: list[float],
) -> float:
    """
    Compute Concentration Index measuring association between a health variable
    and a ranking variable (e.g., age group rank as proxy for need level).

    Formula: CI = (2 / mu) * Cov(health_var, fractional_rank)

    Args:
        health_var: Health outcomes/rates per group.
        rank_var: Socioeconomic or need-based rank per group (fractional: (2i-1)/(2n)).

    Returns:
        Concentration index in [-1, 1]; 0 = perfect equality.
    """
    h = np.array(health_var, dtype=float)
    r = np.array(rank_var, dtype=float)
    if len(h) != len(r) or h.mean() == 0:
        return 0.0
    ci = (2.0 / h.mean()) * float(np.cov(h, r, ddof=1)[0][1])
    return round(ci, 4)


def _interpret_disparity(
    point_est: float,
    ci_lower: float,
    ci_upper: float,
) -> str:
    """Assign equity interpretation based on CI position relative to 1.0."""
    if ci_lower > 1.0:
        return "Higher burden than reference (statistically significant)"
    if ci_upper < 1.0:
        return "Lower burden than reference (statistically significant)"
    return "Not significantly different from reference (equitable)"


def compile_disparity_metrics(
    integrated_df: pl.DataFrame,
    n_boot: int = 1000,
) -> pl.DataFrame:
    """
    Compile a full disparity metrics table from the integrated equity DataFrame.

    Produces one row per demographic_group comparison for both age_group and sex.

    Args:
        integrated_df: Output of integrate_equity_datasets() parquet.
        n_boot: Bootstrap replicates for CI estimation.

    Returns:
        Metrics DataFrame with standard disparity columns.
    """
    results = []

    for dem_type in ["age_group", "sex"]:
        subset = integrated_df.filter(pl.col("demographic_type") == dem_type)
        if subset.is_empty():
            continue

        # Identify reference group (lowest mean rate)
        grp_means = (
            subset
            .group_by("demographic_group")
            .agg(pl.col("metric_value").mean().alias("m"))
        )
        ref_group = grp_means.sort("m")["demographic_group"][0]
        ref_rates = subset.filter(pl.col("demographic_group") == ref_group)["metric_value"].to_list()

        groups = subset["demographic_group"].unique().to_list()
        # Apply Bonferroni correction
        alpha_corrected = 0.05 / max(len(groups) - 1, 1)

        for group in groups:
            grp_rates = subset.filter(pl.col("demographic_group") == group)["metric_value"].to_list()
            point, ci_lo, ci_hi = bootstrap_disparity_ci(
                grp_rates, ref_rates, n_boot=n_boot
            )
            t_stat, p_val = stats.ttest_ind(grp_rates, ref_rates, equal_var=False)

            results.append({
                "metric_type": "admission_rate_ratio",
                "demographic_type": dem_type,
                "demographic_comparison": f"{group} vs {ref_group}",
                "demographic_group": group,
                "reference_group": ref_group,
                "disparity_ratio": point,
                "ci_lower": ci_lo,
                "ci_upper": ci_hi,
                "p_value": round(float(p_val), 6),
                "significant_bonferroni": bool(float(p_val) < alpha_corrected),
                "interpretation": _interpret_disparity(point, ci_lo, ci_hi),
            })

        # Concentration index with age rank proxy
        if dem_type == "age_group":
            latest = (
                subset
                .filter(pl.col("year") == int(subset["year"].max()))
                .sort("demographic_group")
            )
            health_vals = latest["metric_value"].to_list()
            n = len(health_vals)
            frac_ranks = [(2 * i - 1) / (2 * n) for i in range(1, n + 1)]
            ci_val = calculate_concentration_index(health_vals, frac_ranks)
            logger.info(f"Concentration Index (age_group): {ci_val:.4f}")

    metrics_df = pl.DataFrame(results)
    logger.info(f"Disparity metrics compiled: {metrics_df.shape[0]} comparisons")
    return metrics_df


def plot_forest_plot(
    metrics_df: pl.DataFrame,
    output_path: Path | None = None,
) -> None:
    """
    Forest plot of disparity ratios with 95% bootstrap CIs.
    Vertical line at 1.0 = equity reference.
    """
    df = metrics_df.sort("disparity_ratio").to_pandas()
    fig, ax = plt.subplots(figsize=(10, max(6, len(df) * 0.45)))

    y_pos = range(len(df))
    colours = [
        "#d73027" if row["ci_lower"] > 1.0 else
        ("#4575b4" if row["ci_upper"] < 1.0 else "#999999")
        for _, row in df.iterrows()
    ]
    ax.errorbar(
        x=df["disparity_ratio"],
        y=list(y_pos),
        xerr=[
            df["disparity_ratio"] - df["ci_lower"],
            df["ci_upper"] - df["disparity_ratio"],
        ],
        fmt="o",
        color="black",
        ecolor=colours,
        elinewidth=2,
        capsize=4,
        markersize=6,
    )
    ax.axvline(x=1.0, color="black", linestyle="--", linewidth=1.2)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df["demographic_comparison"], fontsize=9)
    ax.set_xlabel("Disparity Ratio (95% Bootstrap CI)", fontweight="bold")
    ax.set_title("Health Equity Disparity Metrics — Forest Plot", fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Forest plot saved: {output_path}")
    plt.show()
    plt.close()
```

---

### 7. Domain-Driven Feature Engineering

| Metric | Formula | Available |
|--------|---------|----------|
| Disparity Ratio w/ bootstrap CI | `mean_group / mean_ref` ± bootstrap | ✅ |
| Concentration Index (age proxy) | `(2/μ) * Cov(rate, frac_rank)` | ✅ (age rank) |
| Bonferroni-corrected p-value | `p < 0.05 / n_groups` | ✅ |
| SES Concentration Index | Requires SES data | ❌ |
| Theil index | Requires individual-level data | ❌ |

---

### 10. Testing Strategy

```python
# problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_equity_disparity_metrics.py

import pytest
import numpy as np
from problem_statements.ps_005.src.equity_disparity_metrics import (
    bootstrap_disparity_ci,
    calculate_concentration_index,
)


def test_bootstrap_ci_equal_groups_near_one():
    rates = [100.0, 110.0, 105.0, 95.0, 100.0]
    point, lo, hi = bootstrap_disparity_ci(rates, rates, n_boot=500)
    assert 0.9 <= point <= 1.1
    assert lo <= point <= hi


def test_bootstrap_ci_twice_as_high():
    ref = [100.0, 100.0, 100.0, 100.0]
    grp = [200.0, 200.0, 200.0, 200.0]
    point, lo, hi = bootstrap_disparity_ci(grp, ref, n_boot=200)
    assert point == pytest.approx(2.0, abs=0.1)
    assert lo > 1.5  # CI should clearly exclude 1.0


def test_concentration_index_perfect_equality():
    # Equal rates -> CI ~= 0
    health_var = [100.0, 100.0, 100.0, 100.0]
    rank_var = [0.125, 0.375, 0.625, 0.875]
    ci = calculate_concentration_index(health_var, rank_var)
    assert abs(ci) < 0.05


def test_concentration_index_pro_high_rank():
    # Higher ranked groups have higher rates -> positive CI
    health_var = [50.0, 100.0, 200.0, 400.0]
    rank_var = [0.125, 0.375, 0.625, 0.875]
    ci = calculate_concentration_index(health_var, rank_var)
    assert ci > 0
```

---

### 11. Implementation Steps

**Phase 1 — Load & Reference Group Selection**
- [ ] Load `equity_analysis_integrated.parquet`; confirm `age_group` and `sex` rows present
- [ ] Log reference group auto-detection for each demographic type

**Phase 2 — Metric Computation**
- [ ] Run `compile_disparity_metrics()` with 1,000 bootstrap runs
- [ ] Inspect CIs — elderly age group should have wide CI > 1.0
- [ ] Compute concentration index for age group dimension

**Phase 3 — Output & Visualisation**
- [ ] Write `results/tables/equity_disparity_metrics.csv`
- [ ] Generate forest plot → `reports/figures/ps-005/disparity_metrics_forest_plot.png`
- [ ] Run pytest ≥80% coverage

---

### 12. Adaptive Implementation Strategy

- If bootstrap produces NaN values (zero reference rates) → `bootstrap_disparity_ci` returns `(0, 0, 0)`; rows excluded from forest plot
- If sex group has insufficient years (<4) → note that Welch t-test has low power; report bootstrap CI only
- If concentration index absolute value < 0.05 → document that age-based utilisation is near-equitable

---

### 20. Security & Privacy

Aggregated data. Results in `results/` (git-ignored).

---

### 21. Version Control

- Branch: `feature/ps-005-equity-disparity-metrics`
- Commits:
  - `feat(ps-005): add bootstrap CI and concentration index for disparity metrics`
  - `test(ps-005): add unit tests for bootstrap_disparity_ci and concentration_index`
