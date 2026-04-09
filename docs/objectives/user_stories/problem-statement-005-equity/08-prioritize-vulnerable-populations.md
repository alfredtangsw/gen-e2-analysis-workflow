# Prioritize Vulnerable Demographic Populations (Lifecycle Stage: Feature Engineering & Insights)

**Story ID**: PS-005-US-08  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P0 (Critical)  
**Effort Estimate**: M (4 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Population Health Policy Director allocating equity program resources**,  
I want **to prioritize vulnerable demographic populations based on disparity magnitude, outcome impact, and intervention feasibility**,  
So that **I can target limited resources toward populations with greatest equity gaps and potential for improvement**.

---

## 🎯 Acceptance Criteria

1. **Vulnerability scoring framework**
   - Disparity magnitude score
   - Outcome impact score (absolute number affected)
   - Trend urgency score (widening vs narrowing disparities)
   - Intervention feasibility score

2. **Population prioritization**
   - Composite vulnerability score
   - Priority ranking: top vulnerable populations
   - Priority quadrants: high disparity + high impact
   - Quick wins identified

3. **Resource allocation recommendations**
   - Investment priorities by demographic
   - Intervention type recommendations
   - Estimated impact per population

4. **Deliverables**
   - Output: `results/tables/vulnerable_population_priorities.csv`
   - Figures: Priority matrix, vulnerability scores
   - Policy brief: Equity intervention priorities

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9
- **Primary Library**: Polars 0.20+
- **Visualization**: Matplotlib
- **Logging**: loguru
- **Testing**: pytest ≥80% coverage

---

## 📚 Domain Knowledge References

- [Domain Knowledge Research](../../../problem_statements/DOMAIN_KNOWLEDGE_RESEARCH.md#equity-prioritization)
- [Problem Statement PS-005](../../../problem_statements/ps-005-healthcare-equity-disparities.md#objective-5)

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.8.0`, `loguru>=0.7.0`

### Internal Dependencies
- **Upstream**: PS-005-US-03 through PS-005-US-07 (All equity analyses - BLOCKING)
- **Data Sources**: All PS-005 analysis outputs

---

## ✅ Implementation Tasks

### Scoring Framework
- [ ] Disparity magnitude: normalize rate ratios
- [ ] Outcome impact: affected population size
- [ ] Trend urgency: worsening disparities scored higher
- [ ] Feasibility: addressability of barriers

### Composite Scoring
- [ ] Weighted composite: 0.3×disparity + 0.3×impact + 0.2×urgency + 0.2×feasibility
- [ ] Rank populations by composite score
- [ ] Identify top 5-10 priority populations

### Priority Quadrants
- [ ] High disparity + high impact: URGENT
- [ ] High disparity + low impact: Targeted programs
- [ ] Low disparity + high impact: Maintenance
- [ ] Low disparity + low impact: Low priority

### Recommendations
- [ ] Intervention priorities
- [ ] Resource allocation suggestions
- [ ] Implementation roadmap

### Visualization
- [ ] Priority matrix scatter plot
- [ ] Vulnerability score charts
- [ ] Save figures

### Policy Brief
- [ ] Executive summary: top priorities
- [ ] Population profiles
- [ ] Recommendations

### Testing & Documentation
- [ ] Validate scoring logic
- [ ] Docstrings
- [ ] Policy brief

---

## 📌 Notes

**Composite Scoring Example**:
```python
priority_score = (
    0.3 * disparity_score +      # How large is the gap?
    0.3 * impact_score +          # How many people affected?
    0.2 * trend_urgency_score +   # Is it getting worse?
    0.2 * feasibility_score       # Can we address it?
)
```

**Expected Priorities**:
- Elderly populations (large disparities, high impact)
- Lower socioeconomic groups (if data shows disparities)
- Specific age-sex combinations with access barriers

---

## Implementation Plan

### 1. Feature Overview

Build a composite vulnerability scoring framework to rank demographic groups by equity intervention priority. Combine disparity magnitude, affected population burden, trend urgency, and modelled intervention feasibility into a weighted composite score. Output a ranked priority list and priority matrix quadrant chart to guide resource allocation decisions.

**Primary User Role**: Population Health Policy Director allocating equity program resources

**Key Deliverable**: `results/tables/vulnerable_population_priorities.csv` with composite scores and priority quadrant classification, plus a 2×2 scatter priority matrix in `reports/figures/ps-005/`.

---

### 2. Component Analysis & Reuse Strategy

| Component | Action | Justification |
|-----------|--------|---------------|
| `results/tables/equity_barrier_diagnosis.csv` | Reuse | Barrier typology and urgency from US-07 |
| `results/tables/utilization_disparity_analysis.csv` | Reuse | Rate ratios from US-03 |
| `results/tables/equity_temporal_trends.csv` | Reuse | Trend slope for urgency scoring from US-06 |
| `population_prioritization.py` | **Create** | Composite scoring, ranking, quadrant plot |
| `test_population_prioritization.py` | **Create** | ≥80% coverage |

---

### 3. ML Model Evaluation & Selection

Not applicable — rule-based composite scoring with min-max normalisation.

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/src/population_prioritization.py`**
  - Functions: `compute_disparity_score(ratios: list[float]) -> list[float]`, `compute_urgency_score(trend_df: pl.DataFrame) -> pl.DataFrame`, `compute_composite_priority(disparity_df: pl.DataFrame, trend_df: pl.DataFrame, barrier_df: pl.DataFrame, weights: dict[str, float]) -> pl.DataFrame`, `plot_priority_matrix(priority_df: pl.DataFrame, output_path: Path) -> None`, `run_population_prioritization(results_dir: Path, output_dir: Path) -> pl.DataFrame`
  - Dependencies: `polars`, `numpy`, `matplotlib`, `loguru`
  - Logging: `logs/analysis/population_prioritization_{timestamp}.log`

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_population_prioritization.py`**

---

### 5. Data Pipeline

**Inputs**:
- `results/tables/utilization_disparity_analysis.csv` — `mean_rate_ratio`, `mean_abs_disparity`
- `results/tables/equity_temporal_trends.csv` — `ols_slope`, `convergence_status`
- `results/tables/equity_barrier_diagnosis.csv` — `barrier_type`, `urgency`

**Scoring methodology**:
| Dimension | Weight | Source | Formula |
|-----------|--------|--------|---------|
| Disparity magnitude | 0.30 | `mean_rate_ratio` | Min-max normalised \|ratio - 1\| |
| Impact score | 0.30 | `mean_abs_disparity` | Min-max normalised absolute disparity |
| Trend urgency | 0.20 | `ols_slope` | Diverging=1.0, Stable=0.5, Converging=0.0 |
| Feasibility | 0.20 | `barrier_type` | Access=0.7, Quality=0.5, Systemic=0.3, Effective=0.1 |

Composite score = 0.30×disparity + 0.30×impact + 0.20×urgency + 0.20×feasibility

**Output**: ranked table + priority quadrant plot (x=disparity score, y=impact score, size=composite, colour=urgency)

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/src/population_prioritization.py

from pathlib import Path
from datetime import datetime

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from loguru import logger


# Scoring weights (must sum to 1.0)
DEFAULT_WEIGHTS: dict[str, float] = {
    "disparity": 0.30,
    "impact": 0.30,
    "urgency": 0.20,
    "feasibility": 0.20,
}

# Feasibility scores by barrier type (higher = more addressable)
FEASIBILITY_MAP: dict[str, float] = {
    "Access barrier": 0.70,
    "Quality concern": 0.50,
    "Healthy/preventive gap": 0.60,
    "Effective care": 0.10,
    "Systemic inequity": 0.30,
    "Unknown": 0.40,
}

URGENCY_MAP: dict[str, float] = {
    "Diverging (equity worsening)": 1.0,
    "Stable (persistent gap)": 0.5,
    "Converging (equity improving)": 0.0,
    "Unknown": 0.4,
    "Insufficient data": 0.3,
}


def _setup_logging(log_dir: str = "logs/analysis") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(
        Path(log_dir) / f"population_prioritization_{ts}.log",
        rotation="10 MB",
        level="INFO",
    )


def _minmax_normalise(values: list[float]) -> list[float]:
    """Min-max normalise a list to [0, 1]. Returns zeros if all values identical."""
    arr = np.array(values, dtype=float)
    lo, hi = arr.min(), arr.max()
    if hi == lo:
        return [0.0] * len(values)
    return ((arr - lo) / (hi - lo)).tolist()


def compute_composite_priority(
    disparity_df: pl.DataFrame,
    trend_df: pl.DataFrame,
    barrier_df: pl.DataFrame,
    weights: dict[str, float] | None = None,
) -> pl.DataFrame:
    """
    Compute composite vulnerability priority scores for each demographic group.

    Args:
        disparity_df: Must contain [demographic_group, mean_rate_ratio, mean_abs_disparity].
        trend_df: Must contain [demographic_group, convergence_status].
        barrier_df: Must contain [demographic_group, barrier_type].
        weights: Scoring weights dict; defaults to DEFAULT_WEIGHTS.

    Returns:
        Priority DataFrame sorted by composite_score descending, with rank.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError(f"Weights must sum to 1.0; got {sum(weights.values()):.4f}")

    # Merge all inputs
    merged = (
        disparity_df
        .select(["demographic_group", "mean_rate_ratio"])
        .join(
            trend_df.select(["demographic_group", "convergence_status"]),
            on="demographic_group",
            how="left",
        )
        .join(
            barrier_df.select(["demographic_group", "barrier_type"]),
            on="demographic_group",
            how="left",
        )
    )

    # Add absolute disparity if available
    if "mean_abs_disparity" in disparity_df.columns:
        merged = merged.join(
            disparity_df.select(["demographic_group", "mean_abs_disparity"]),
            on="demographic_group",
            how="left",
        )
    else:
        merged = merged.with_columns(pl.lit(0.0).alias("mean_abs_disparity"))

    merged = merged.with_columns([
        pl.col("convergence_status").fill_null("Unknown"),
        pl.col("barrier_type").fill_null("Unknown"),
    ])

    # Raw component values
    ratios = merged["mean_rate_ratio"].to_list()
    abs_disparities = merged["mean_abs_disparity"].to_list()
    convergence_statuses = merged["convergence_status"].to_list()
    barrier_types = merged["barrier_type"].to_list()

    # Normalised scores
    disparity_scores = _minmax_normalise([abs(r - 1.0) for r in ratios])
    impact_scores = _minmax_normalise(abs_disparities)
    urgency_scores = [
        URGENCY_MAP.get(s, 0.4) for s in convergence_statuses
    ]
    feasibility_scores = [
        FEASIBILITY_MAP.get(b, 0.4) for b in barrier_types
    ]

    composite = [
        round(
            weights["disparity"] * d
            + weights["impact"] * i
            + weights["urgency"] * u
            + weights["feasibility"] * f,
            4,
        )
        for d, i, u, f in zip(
            disparity_scores, impact_scores, urgency_scores, feasibility_scores
        )
    ]

    result = merged.with_columns([
        pl.Series("disparity_score", disparity_scores).round(4),
        pl.Series("impact_score", impact_scores).round(4),
        pl.Series("urgency_score", urgency_scores).round(4),
        pl.Series("feasibility_score", feasibility_scores).round(4),
        pl.Series("composite_score", composite),
    ]).sort("composite_score", descending=True)

    result = result.with_columns(
        pl.Series("priority_rank", list(range(1, result.shape[0] + 1)))
    )

    logger.info(
        f"Priority scoring complete: {result.shape[0]} groups ranked; "
        f"top group: {result['demographic_group'][0]} "
        f"(score={result['composite_score'][0]:.4f})"
    )
    return result


def plot_priority_matrix(
    priority_df: pl.DataFrame,
    output_path: Path | None = None,
) -> None:
    """
    2x2 priority matrix scatter plot:
    x = disparity_score, y = impact_score,
    marker size proportional to composite_score,
    colour by urgency level.
    """
    pdf = priority_df.to_pandas()

    urgency_colour_map = {
        "HIGH": "#d73027",
        "MEDIUM": "#fc8d59",
        "LOW": "#4575b4",
    }

    # Derive urgency label from urgency_score
    pdf["urgency_label"] = pdf["urgency_score"].apply(
        lambda s: "HIGH" if s >= 0.8 else ("MEDIUM" if s >= 0.4 else "LOW")
    )
    colours = [urgency_colour_map.get(u, "grey") for u in pdf["urgency_label"]]
    sizes = (pdf["composite_score"] * 800 + 50).clip(50, 800)

    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(
        pdf["disparity_score"],
        pdf["impact_score"],
        c=colours,
        s=sizes,
        alpha=0.75,
        edgecolors="black",
        linewidths=0.5,
        zorder=3,
    )

    for _, row in pdf.iterrows():
        ax.annotate(
            f"{row['demographic_group']}\n(#{int(row['priority_rank'])})",
            (row["disparity_score"], row["impact_score"]),
            fontsize=8,
            ha="center",
            va="bottom",
        )

    ax.axhline(y=0.5, color="grey", linestyle="--", linewidth=0.8)
    ax.axvline(x=0.5, color="grey", linestyle="--", linewidth=0.8)

    # Quadrant labels
    ax.text(0.25, 0.92, "Targeted programs", transform=ax.transAxes,
            fontsize=9, color="grey", ha="center")
    ax.text(0.75, 0.92, "URGENT — High priority", transform=ax.transAxes,
            fontsize=9, color="#d73027", ha="center", fontweight="bold")
    ax.text(0.25, 0.08, "Low priority", transform=ax.transAxes,
            fontsize=9, color="grey", ha="center")
    ax.text(0.75, 0.08, "Maintenance", transform=ax.transAxes,
            fontsize=9, color="grey", ha="center")

    ax.set_xlabel("Disparity Score (normalised)", fontweight="bold")
    ax.set_ylabel("Impact Score (normalised)", fontweight="bold")
    ax.set_title("Vulnerable Population Priority Matrix", fontweight="bold")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)

    # Legend patches
    import matplotlib.patches as mpatches
    legend_patches = [
        mpatches.Patch(color=c, label=l)
        for l, c in urgency_colour_map.items()
    ]
    ax.legend(handles=legend_patches, title="Urgency", loc="lower right")

    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Priority matrix saved: {output_path}")
    plt.show()
    plt.close()


def run_population_prioritization(
    results_dir: Path,
    output_dir: Path,
) -> pl.DataFrame:
    """
    Full prioritization pipeline.

    Args:
        results_dir: Contains upstream results tables.
        output_dir: Destination for priority outputs.

    Returns:
        Ranked priority DataFrame.
    """
    _setup_logging()
    tables_dir = output_dir / "tables"
    figures_dir = output_dir.parent / "reports" / "figures" / "ps-005"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    disparity_path = results_dir / "tables" / "utilization_disparity_analysis.csv"
    trend_path = results_dir / "tables" / "equity_temporal_trends.csv"
    barrier_path = results_dir / "tables" / "equity_barrier_diagnosis.csv"

    if not disparity_path.exists():
        raise FileNotFoundError(f"Missing: {disparity_path}. Run US-03 first.")

    disparity_df = pl.read_csv(disparity_path)
    trend_df = (
        pl.read_csv(trend_path)
        if trend_path.exists()
        else pl.DataFrame({"demographic_group": disparity_df["demographic_group"].to_list(),
                           "convergence_status": ["Unknown"] * disparity_df.shape[0]})
    )
    barrier_df = (
        pl.read_csv(barrier_path)
        if barrier_path.exists()
        else pl.DataFrame({"demographic_group": disparity_df["demographic_group"].to_list(),
                           "barrier_type": ["Unknown"] * disparity_df.shape[0]})
    )

    priority_df = compute_composite_priority(disparity_df, trend_df, barrier_df)
    priority_df.write_csv(tables_dir / "vulnerable_population_priorities.csv")
    logger.info(f"Priority table saved: {tables_dir / 'vulnerable_population_priorities.csv'}")

    plot_priority_matrix(
        priority_df,
        output_path=figures_dir / "priority_matrix.png",
    )
    return priority_df
```

---

### 7. Domain-Driven Feature Engineering

| Score Dimension | Formula | Data Available |
|-----------------|---------|----------------|
| Disparity magnitude | Min-max `\|rate_ratio - 1\|` | ✅ from US-03 |
| Impact (absolute burden) | Min-max `abs_disparity` | ✅ from US-03 |
| Trend urgency | URGENCY_MAP lookup on convergence_status | ✅ from US-06 |
| Feasibility | FEASIBILITY_MAP lookup on barrier_type | ✅ from US-07 |
| Population size weight | Actual population counts | ❌ Not in dataset |

*Note*: Population size weighting is not possible with available data. Impact score uses absolute rate difference as proxy.

---

### 10. Testing Strategy

```python
# problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_population_prioritization.py

import polars as pl
import pytest
from problem_statements.ps_005.src.population_prioritization import (
    compute_composite_priority,
    _minmax_normalise,
)


def test_minmax_normalise_basic():
    result = _minmax_normalise([0.0, 5.0, 10.0])
    assert result[0] == pytest.approx(0.0)
    assert result[1] == pytest.approx(0.5)
    assert result[2] == pytest.approx(1.0)


def test_minmax_normalise_all_equal():
    result = _minmax_normalise([5.0, 5.0, 5.0])
    assert all(v == 0.0 for v in result)


def test_weights_must_sum_to_one():
    disp_df = pl.DataFrame({"demographic_group": ["A"], "mean_rate_ratio": [1.5]})
    trend_df = pl.DataFrame({"demographic_group": ["A"], "convergence_status": ["Unknown"]})
    barrier_df = pl.DataFrame({"demographic_group": ["A"], "barrier_type": ["Access barrier"]})
    with pytest.raises(ValueError, match="Weights must sum to 1.0"):
        compute_composite_priority(
            disp_df, trend_df, barrier_df,
            weights={"disparity": 0.5, "impact": 0.5, "urgency": 0.5, "feasibility": 0.5},
        )


def test_composite_priority_rank_ordering():
    disp_df = pl.DataFrame({
        "demographic_group": ["Low risk", "High risk"],
        "mean_rate_ratio": [1.0, 5.0],
        "mean_abs_disparity": [0.0, 400.0],
    })
    trend_df = pl.DataFrame({
        "demographic_group": ["Low risk", "High risk"],
        "convergence_status": ["Converging (equity improving)", "Diverging (equity worsening)"],
    })
    barrier_df = pl.DataFrame({
        "demographic_group": ["Low risk", "High risk"],
        "barrier_type": ["Effective care", "Access barrier"],
    })
    result = compute_composite_priority(disp_df, trend_df, barrier_df)
    # High risk should be ranked 1 (highest priority)
    assert result["demographic_group"][0] == "High risk"
    assert result["priority_rank"][0] == 1
```

---

### 11. Implementation Steps

**Phase 1 — Data Loading**
- [ ] Confirm all three upstream CSVs exist (US-03, US-06, US-07 must be complete)
- [ ] Load and verify column names; adjust if naming differs from expected

**Phase 2 — Scoring**
- [ ] Run `compute_composite_priority()` with default weights
- [ ] Review top 3 ranked groups — expect elderly (65+) as #1 or #2
- [ ] Experiment with alternative weights (e.g. increase impact weight to 0.40); document rationale

**Phase 3 — Output & Visualisation**
- [ ] Write `results/tables/vulnerable_population_priorities.csv`
- [ ] Generate priority matrix plot → `reports/figures/ps-005/priority_matrix.png`

**Phase 4 — Testing**
- [ ] Run pytest with ≥80% coverage
- [ ] Validate weight sensitivity: results stable across reasonable weight variations

---

### 12. Adaptive Implementation Strategy

- If `mean_abs_disparity` column absent in US-03 output → set impact_scores to zeros (disparity magnitude becomes sole impact proxy)
- If fewer than 3 demographic groups → priority matrix loses visual meaning; present as ranked table only
- If top priority group is the reference group (ratio ≈ 1.0) → verify reference group is excluded from ranking or scored separately

---

### 20. Security & Privacy

Aggregated data only. Results in `results/` (git-ignored).

---

### 21. Version Control

- Branch: `feature/ps-005-population-prioritization`
- Commits:
  - `feat(ps-005): add composite vulnerability scoring and priority matrix`
  - `test(ps-005): add unit tests for composite_priority weight validation and rank ordering`
