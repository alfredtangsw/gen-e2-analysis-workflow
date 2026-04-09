# Analyze Health Outcome Disparities (Lifecycle Stage: Exploratory Data Analysis)

**Story ID**: PS-005-US-04  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P0 (Critical)  
**Effort Estimate**: M (5 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Population Health Strategist evaluating outcome equity**,  
I want **to assess health outcome disparities (mortality, disease burden) across demographic groups**,  
So that **I can identify populations with worse health outcomes and link outcome inequities to potential access or care quality disparities**.

---

## 🎯 Acceptance Criteria

1. **Outcome disparities quantified**
   - Mortality rate ratios by demographics
   - Disease burden (DALY) disparities if data available
   - Standardized mortality ratios (SMR)
   - Statistical significance testing

2. **Demographic outcome patterns**
   - High-mortality demographics identified
   - Outcome gaps vs reference groups
   - Age-sex-specific outcome disparities
   - Disease-specific outcome equity

3. **Utilization-outcome linkage**
   - Correlation: utilization disparities vs outcome disparities
   - Paradoxes identified: high utilization but poor outcomes (quality issue?)
   - Access gaps: low utilization AND poor outcomes (access barrier)

4. **Deliverables**
   - Output: `results/tables/outcome_disparity_analysis.csv`
   - Figures: Outcome disparity charts
   - Report: Health outcome equity assessment

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9
- **Primary Library**: Polars 0.20+
- **Statistical Analysis**: scipy
- **Visualization**: Matplotlib
- **Logging**: loguru
- **Testing**: pytest ≥80% coverage

---

## 📚 Domain Knowledge References

- [Domain Knowledge Research](../../../problem_statements/DOMAIN_KNOWLEDGE_RESEARCH.md#outcome-disparity-metrics)
- [Disease Burden Guide](../../../../domain_knowledge/disease-burden-feature-engineering-guide.md#standardized-mortality-ratio-smr)
- [Problem Statement PS-005](../../../problem_statements/ps-005-healthcare-equity-disparities.md#objective-2)

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`, `scipy>=1.11.0`, `matplotlib>=3.8.0`, `loguru>=0.7.0`

### Internal Dependencies
- **Upstream**: PS-005-US-03 (Utilization disparities - parallel OK)
- **Data Sources**: `shared/data/3_interim/equity_analysis_integrated.parquet`

---

## ✅ Implementation Tasks

### Outcome Disparity Calculation
- [ ] Calculate mortality rate ratios
- [ ] Calculate SMRs (observed/expected deaths)
- [ ] Disease burden disparities (if DALY data available)
- [ ] Statistical significance tests

### Pattern Analysis
- [ ] Identify high-mortality demographics
- [ ] Quantify outcome gaps vs reference groups
- [ ] Age-sex-disease interaction analysis

### Utilization-Outcome Linkage
- [ ] Correlate utilization disparities with outcome disparities
- [ ] Identify quality paradoxes (high use, poor outcomes)
- [ ] Identify access gaps (low use, poor outcomes)

### Visualization
- [ ] Outcome disparity charts
- [ ] 2×2 matrix: utilization vs outcomes
- [ ] Save figures

### Testing & Documentation
- [ ] Unit tests
- [ ] Docstrings
- [ ] Outcome equity report

---

## 📌 Notes

**SMR Calculation**:
```python
SMR = (Observed deaths / Expected deaths) × 100
```

**Utilization-Outcome Matrix**:
- High utilization + Good outcomes: Effective care
- High utilization + Poor outcomes: Quality concerns
- Low utilization + Good outcomes: Healthy population
- Low utilization + Poor outcomes: **Access barrier** (priority intervention)

---

## Implementation Plan

### 1. Feature Overview

Compute mortality outcome disparities across sex (the only demographic stratification available in the Singapore mortality tables) and link them to utilisation disparities from US-03. Quantify Standardised Mortality Ratios (SMR), identify demographic groups with poor outcomes relative to their utilisation levels, and produce a utilisation-outcome 2×2 matrix for intervention targeting.

**Primary User Role**: Population Health Strategist evaluating outcome equity

**Key Deliverable**: `results/tables/outcome_disparity_analysis.csv` + scatter matrix figure in `reports/figures/ps-005/`.

**Data Constraint**: Age-stratified mortality is available only at the national level for cancer, stroke, and IHD. Sex-stratified breakdowns may be limited; analysis adapts to available columns.

---

### 2. Component Analysis & Reuse Strategy

| Component | Action | Justification |
|-----------|--------|---------------|
| `equity_analysis_integrated.parquet` | Reuse | Contains utilisation rate_ratio from US-02 |
| `shared/data/1_raw/equity/outcomes/*.csv` | Reuse | Mortality tables from US-01 |
| `utilization_disparity_analysis.py` | Reuse `calculate_disparity_significance()` | Avoids code duplication |
| `outcome_disparity_analysis.py` | **Create** | Outcome-specific SMR, linkage, matrix |
| `test_outcome_disparity.py` | **Create** | ≥80% coverage |

---

### 3. ML Model Evaluation & Selection

Not applicable — statistical descriptive/inferential analysis only.

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/src/outcome_disparity_analysis.py`**
  - Functions: `load_mortality_tables(outcomes_dir: Path) -> dict[str, pl.DataFrame]`, `compute_smr(df: pl.DataFrame, ref_group: str) -> pl.DataFrame`, `build_utilization_outcome_matrix(utilization_df: pl.DataFrame, outcome_df: pl.DataFrame) -> pl.DataFrame`, `run_outcome_disparity_analysis(data_path: Path, outcomes_dir: Path, output_dir: Path) -> pl.DataFrame`
  - Dependencies: `polars`, `scipy`, `matplotlib`, `loguru`
  - Logging: `logs/analysis/outcome_disparity_{timestamp}.log`

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_outcome_disparity.py`**

---

### 5. Data Pipeline

**Sources**:
- `shared/data/1_raw/equity/outcomes/mortality_{cancer,stroke,ihd}.csv` — age-standardised rate by year
- `shared/data/3_interim/equity_analysis_integrated.parquet` — utilisation disparities

**Steps**:
1. Load all mortality CSVs, normalise column names
2. Detect demographic columns (sex breakdowns if present); fall back to aggregate if not
3. Compute mortality disparity ratios: `rate_sex_i / rate_reference_sex`
4. Compute SMR where reference is lowest-rate group
5. Join utilisation rate_ratio (from parquet) with mortality rate_ratio on available keys
6. Classify each group into 2×2 matrix quadrant
7. Write output CSV and 2×2 scatter plot

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/src/outcome_disparity_analysis.py

from pathlib import Path
from datetime import datetime

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy import stats
from loguru import logger


def _setup_logging(log_dir: str = "logs/analysis") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(Path(log_dir) / f"outcome_disparity_{ts}.log", rotation="10 MB", level="INFO")


def load_mortality_tables(outcomes_dir: Path) -> dict[str, pl.DataFrame]:
    """
    Load all mortality CSVs from the outcomes directory.

    Returns:
        Dict mapping disease name to normalised DataFrame.
    """
    tables = {}
    for csv_path in sorted(outcomes_dir.glob("mortality_*.csv")):
        disease = csv_path.stem.replace("mortality_", "")
        df = pl.read_csv(csv_path)
        df = df.rename({c: c.strip().lower().replace(" ", "_") for c in df.columns})
        df = df.with_columns(pl.col("year").cast(pl.Int32))
        tables[disease] = df
        logger.info(f"Loaded mortality table '{disease}': {df.shape[0]} rows")
    if not tables:
        logger.warning(f"No mortality CSVs found in {outcomes_dir}")
    return tables


def compute_smr(
    df: pl.DataFrame,
    rate_col: str,
    group_col: str | None = None,
    ref_group: str | None = None,
) -> pl.DataFrame:
    """
    Compute Standardised Mortality Ratio (observed / expected).

    If group_col is None, computes temporal SMR relative to first year.
    Otherwise computes group SMR relative to ref_group.

    Args:
        df: Mortality DataFrame with year and rate column.
        rate_col: Name of mortality rate column.
        group_col: Optional demographic group column.
        ref_group: Reference group for disparity ratio; uses lowest-rate group if None.

    Returns:
        DataFrame with added smr and mortality_disparity_ratio columns.
    """
    if group_col is not None and group_col in df.columns:
        if ref_group is None:
            grp_means = df.group_by(group_col).agg(pl.col(rate_col).mean().alias("mean"))
            ref_group = grp_means.sort("mean")[group_col][0]
            logger.info(f"Reference group for SMR: {ref_group}")
        ref_vals = (
            df.filter(pl.col(group_col) == ref_group)
            .select(["year", rate_col])
            .rename({rate_col: "ref_rate"})
        )
        df = df.join(ref_vals, on="year", how="left")
        df = df.with_columns([
            (pl.col(rate_col) / pl.col("ref_rate")).alias("mortality_disparity_ratio"),
            (pl.col(rate_col) / pl.col("ref_rate")).alias("smr"),
        ])
    else:
        # Temporal reference: first available year
        base_rate = df.sort("year")[rate_col][0]
        df = df.with_columns([
            (pl.col(rate_col) / base_rate).alias("mortality_disparity_ratio"),
            (pl.col(rate_col) / base_rate).alias("smr"),
        ])
    return df


def build_utilization_outcome_matrix(
    utilization_summary: pl.DataFrame,
    outcome_summary: pl.DataFrame,
    group_col: str = "demographic_group",
) -> pl.DataFrame:
    """
    Build 2x2 utilisation-outcome matrix for intervention prioritisation.

    Args:
        utilization_summary: DataFrame with [demographic_group, mean_rate_ratio].
        outcome_summary: DataFrame with [demographic_group, mean_mortality_ratio].
        group_col: Join key column name.

    Returns:
        DataFrame with quadrant classification per demographic group.
    """
    merged = utilization_summary.join(
        outcome_summary,
        on=group_col,
        how="inner",
        suffix="_outcome",
    )

    merged = merged.with_columns(
        pl.when(
            (pl.col("mean_rate_ratio") > 1.0) & (pl.col("mean_mortality_ratio") <= 1.0)
        ).then(pl.lit("High utilisation / Good outcomes (Effective care)"))
        .when(
            (pl.col("mean_rate_ratio") > 1.0) & (pl.col("mean_mortality_ratio") > 1.0)
        ).then(pl.lit("High utilisation / Poor outcomes (Quality concern)"))
        .when(
            (pl.col("mean_rate_ratio") <= 1.0) & (pl.col("mean_mortality_ratio") <= 1.0)
        ).then(pl.lit("Low utilisation / Good outcomes (Healthy population)"))
        .otherwise(pl.lit("Low utilisation / Poor outcomes (ACCESS BARRIER — PRIORITY)"))
        .alias("intervention_quadrant")
    )
    logger.info(
        f"Intervention matrix built: {merged.shape[0]} groups classified into quadrants"
    )
    return merged


def plot_utilization_outcome_scatter(
    matrix_df: pl.DataFrame,
    output_path: Path | None = None,
) -> None:
    """2x2 scatter plot with quadrant annotations."""
    pdf = matrix_df.to_pandas()
    fig, ax = plt.subplots(figsize=(9, 8))

    quadrant_colours = {
        "High utilisation / Good outcomes (Effective care)": "#2166ac",
        "High utilisation / Poor outcomes (Quality concern)": "#d73027",
        "Low utilisation / Good outcomes (Healthy population)": "#4dac26",
        "Low utilisation / Poor outcomes (ACCESS BARRIER — PRIORITY)": "#b2182b",
    }

    for quadrant, colour in quadrant_colours.items():
        subset = pdf[pdf["intervention_quadrant"] == quadrant]
        ax.scatter(
            subset["mean_rate_ratio"],
            subset["mean_mortality_ratio"],
            c=colour, s=120, label=quadrant, zorder=3,
        )
        for _, row in subset.iterrows():
            ax.annotate(
                row["demographic_group"],
                (row["mean_rate_ratio"], row["mean_mortality_ratio"]),
                fontsize=8, ha="left",
            )

    ax.axhline(y=1.0, color="grey", linestyle="--", linewidth=1)
    ax.axvline(x=1.0, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Utilisation Rate Ratio vs Reference", fontweight="bold")
    ax.set_ylabel("Mortality Rate Ratio vs Reference", fontweight="bold")
    ax.set_title("Utilisation–Outcome Matrix by Demographic Group", fontweight="bold")
    ax.legend(loc="best", fontsize=7)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Utilisation-outcome scatter saved: {output_path}")
    plt.show()
    plt.close()


def run_outcome_disparity_analysis(
    data_path: Path,
    outcomes_dir: Path,
    output_dir: Path,
) -> pl.DataFrame:
    """
    Run full outcome disparity pipeline and produce output artefacts.

    Args:
        data_path: Path to equity_analysis_integrated.parquet.
        outcomes_dir: Directory with raw mortality CSVs.
        output_dir: Directory for results tables.

    Returns:
        Outcome disparity DataFrame.
    """
    _setup_logging()
    tables_dir = output_dir / "tables"
    figures_dir = output_dir.parent / "reports" / "figures" / "ps-005"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Load and compute mortality disparities
    mort_tables = load_mortality_tables(outcomes_dir)
    outcome_frames = []
    for disease, mort_df in mort_tables.items():
        rate_col = [c for c in mort_df.columns if c not in ["year"] and "rate" in c]
        if not rate_col:
            logger.warning(f"No rate column found in {disease}, skipping")
            continue
        mort_df = compute_smr(mort_df, rate_col=rate_col[0])
        mort_df = mort_df.with_columns(pl.lit(disease).alias("disease"))
        outcome_frames.append(mort_df)

    if not outcome_frames:
        logger.warning("No outcome data processed; output will be empty")
        return pl.DataFrame()

    outcome_df = pl.concat(outcome_frames, how="diagonal")

    # Aggregate mortality disparity across diseases per year
    outcome_summary = (
        outcome_df
        .group_by("year")
        .agg(pl.col("mortality_disparity_ratio").mean().round(4).alias("mean_mortality_ratio"))
    )

    # Load utilisation summary
    util_df = pl.read_parquet(data_path)
    util_summary = (
        util_df
        .filter(pl.col("demographic_type") == "age_group")
        .group_by("demographic_group")
        .agg(pl.col("rate_ratio").mean().round(4).alias("mean_rate_ratio"))
    )

    outcome_df.write_csv(tables_dir / "outcome_disparity_analysis.csv")
    logger.info(f"Outcome disparity analysis saved: {tables_dir / 'outcome_disparity_analysis.csv'}")

    return outcome_df
```

---

### 7. Domain-Driven Feature Engineering

| Metric | Formula | Data Available |
|--------|---------|----------------|
| Mortality Disparity Ratio | `rate_group / rate_reference` | ✅ (national aggregates) |
| SMR | `observed / expected` (via rate ratio) | ✅ |
| Utilisation-Outcome linkage | Join on year/group | ✅ (age group only if sex-split mortality available) |
| SES-adjusted mortality | Requires SES data | ❌ |

---

### 10. Testing Strategy

```python
# problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_outcome_disparity.py

import polars as pl
import pytest
from problem_statements.ps_005.src.outcome_disparity_analysis import (
    compute_smr,
    build_utilization_outcome_matrix,
)


def test_compute_smr_temporal_baseline():
    df = pl.DataFrame({"year": [2010, 2015, 2020], "mortality_rate": [100.0, 90.0, 80.0]})
    result = compute_smr(df, rate_col="mortality_rate")
    # SMR for first year = 1.0 (baseline)
    assert result.filter(pl.col("year") == 2010)["smr"][0] == pytest.approx(1.0)
    # SMR for 2020 = 80/100 = 0.8
    assert result.filter(pl.col("year") == 2020)["smr"][0] == pytest.approx(0.8)


def test_build_utilization_outcome_matrix_quadrant_access_barrier():
    util_df = pl.DataFrame({"demographic_group": ["Elderly"], "mean_rate_ratio": [0.5]})
    outcome_df = pl.DataFrame({"demographic_group": ["Elderly"], "mean_mortality_ratio": [2.0]})
    result = build_utilization_outcome_matrix(util_df, outcome_df)
    assert "ACCESS BARRIER" in result["intervention_quadrant"][0]


def test_build_matrix_effective_care_quadrant():
    util_df = pl.DataFrame({"demographic_group": ["Adults"], "mean_rate_ratio": [1.5]})
    outcome_df = pl.DataFrame({"demographic_group": ["Adults"], "mean_mortality_ratio": [0.8]})
    result = build_utilization_outcome_matrix(util_df, outcome_df)
    assert "Effective care" in result["intervention_quadrant"][0]
```

---

### 11. Implementation Steps

**Phase 1 — Load & Inspect Mortality Data**
- [ ] Run `load_mortality_tables()` on `shared/data/1_raw/equity/outcomes/`
- [ ] Inspect actual column names and check if sex-stratified mortality present
- [ ] If sex column absent → proceed with temporal SMR only; document limitation

**Phase 2 — Compute Outcome Disparities**
- [ ] Run `compute_smr()` for each disease table
- [ ] Calculate average mortality trend across diseases per year

**Phase 3 — Utilisation-Outcome Linkage**
- [ ] Load utilisation data from parquet (US-02 output)
- [ ] Attempt join on available demographic keys
- [ ] Build 2×2 intervention matrix if both dimensions available

**Phase 4 — Output & Testing**
- [ ] Write `results/tables/outcome_disparity_analysis.csv`
- [ ] Generate and save scatter plot
- [ ] Run pytest ≥80% coverage

---

### 12. Adaptive Implementation Strategy

- If mortality tables have no sex column → perform temporal SMR only and note the limitation clearly in the output CSV and notebook
- If `equity_analysis_integrated.parquet` lacks matching group keys for join → present utilisation and outcome analyses separately without linkage
- If all 3 diseases show similar patterns → create composite disease burden index as single outcome indicator

---

### 20. Security & Privacy

Aggregated data only. Results saved to `results/` (git-ignored).

---

### 21. Version Control

- Branch: `feature/ps-005-outcome-disparity-analysis`
- Commits:
  - `feat(ps-005): add outcome disparity analysis with SMR and utilisation-outcome matrix`
  - `test(ps-005): add unit tests for SMR and quadrant classification`
