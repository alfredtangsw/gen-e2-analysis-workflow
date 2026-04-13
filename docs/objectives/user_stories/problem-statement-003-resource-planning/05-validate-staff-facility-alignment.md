# User Story: 5 — Staff-Facility Alignment Validation

**As a** MOH systems integrator,  
**I want** to validate that projected workforce levels and projected bed levels maintain an adequate nurse-to-bed ratio across the planning horizon,  
**so that** I can confirm that workforce and facility expansion plans are being developed in tandem rather than in isolation.

## 1. 🎯 Acceptance Criteria

- Nurse:bed ratio computed for each year 2021–2035 under all 3 demographic scenarios using: `projected_nurse_supply / required_beds`
- Ratio compared against benchmark: 1 nurse per 4 beds = ratio ≤ 0.25 (inverted: > 4 beds per nurse = under-staffed)
- Traffic-light flag applied per year-scenario cell: 🟢 ratio ≥ 0.25 (adequate), 🟡 0.20–0.25 (monitor), 🔴 < 0.20 (critical shortage)
- Alignment heatmap generated: year (x-axis) × scenario (y-axis), colour = RAG status — saved to `reports/figures/ps003_planning/staff_facility_alignment_heatmap.png`
- A "first divergence year" identified per scenario: first year where principal CAGR supply, under standard growth assumptions, falls below the 🟡 threshold
- Summary table saved to `results/tables/ps003_staff_facility_alignment.csv`: `year, scenario, projected_nurses, required_beds, nurse_bed_ratio, rag_status`

## 2. 🔒 Technical Constraints

- Nurse:bed ratio must use projected nurse supply from Story 02 (historical CAGR scenario) and required beds from Story 04 (principal scenario for primary analysis; all 3 scenarios for sensitivity)
- RAG thresholds stored in `shared/config/base.yml` under `planning_constants.rag_green_threshold` (0.25) and `planning_constants.rag_amber_threshold` (0.20)
- Heatmap: use `plotly.express.imshow` with discrete colour scale — green/amber/red; x-axis = year, y-axis = scenario label
- Heatmap year range: 2020 (actual anchor) through 2035

## 3. 📚 Domain Knowledge References

- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — nurse:bed benchmark, RAG threshold interpretation
- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — staffing adequacy standards

## 4. 📦 Dependencies

- Story 02: `ps003_workforce_supply_projections.csv` — nurse projections by scenario and year
- Story 04: `ps003_bed_gap.csv` — required_beds by scenario and year
- Story 01: `planning_constants` — RAG thresholds
- `polars` — ratio computation and join
- `plotly`, `kaleido` — heatmap

## 5. ✅ Implementation Tasks

**Ratio Computation**
- ⬜ Load nurse supply projections (historical CAGR scenario); filter to nurses only
- ⬜ Load required beds (all 3 scenarios) from `ps003_bed_gap.csv`
- ⬜ Join on `year` and `scenario`; compute `nurse_bed_ratio = projected_nurses / required_beds`

**RAG Classification**
- ⬜ Apply RAG rule from config thresholds: `ratio >= 0.25 → "green"`, `0.20 <= ratio < 0.25 → "amber"`, `ratio < 0.20 → "red"`
- ⬜ Identify "first divergence year": first year where any scenario drops to amber or below

**Summary Table**
- ⬜ Save full year × scenario table with ratio and RAG to `ps003_staff_facility_alignment.csv`
- ⬜ Add metadata column: `benchmark_ratio = 0.25, benchmark_source = "WHO SEARO 2020"`

**Heatmap Chart**
- ⬜ Pivot table to year × scenario matrix; populate with RAG integer code (2=green, 1=amber, 0=red)
- ⬜ Plot `px.imshow` with discrete colour scale → `staff_facility_alignment_heatmap.png`
- ⬜ Add title: "[DRAFT] Staff-Facility Alignment | Nurse:Bed Ratio vs WHO Benchmark | MOH-SG"

## 6. Notes

- This story answers a critical policy question: are we planning workforce and facilities together, or separately? If the ratios deteriorate rapidly, it signals that facilities are expanding faster than workforce training pipelines can fill.
- The "first divergence year" is a headline metric for the executive summary — state it plainly: "Under the principal scenario, nurse staffing adequacy falls below the amber threshold in [year]."
- If all scenarios remain green throughout 2021–2035, this is a positive finding (workforce growing adequately relative to bed demand) — worth highlighting, not just assuming.

---

## Implementation Plan

### 1. Feature Overview

Compute nurse:bed ratio per year and scenario. Apply RAG classification from config thresholds. Identify first divergence year. Produce alignment summary CSV and a RAG heatmap. Primary user: **MOH systems integrator**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-003-healthcare-capacity/src/alignment_validator.py
  - compute_nurse_bed_ratio(supply_df, beds_df) -> pl.DataFrame
  - classify_rag(ratio, green_threshold, amber_threshold) -> str
  - apply_rag_to_alignment(alignment_df, constants) -> pl.DataFrame
  - find_first_divergence_year(alignment_df) -> dict[str, int | None]

[CREATE] problem-statements/ps-003-healthcare-capacity/scripts/run_alignment_validation.py
  - Orchestrates ratio computation; writes summary CSV and heatmap
```

---

### 3. Code Generation Specifications

#### 3.1 `src/alignment_validator.py`

```python
"""PS-003 staff-facility alignment validation.

Nurse:bed ratio = projected_nurse_supply / required_beds.
RAG thresholds from planning_constants in base.yml.
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


def compute_nurse_bed_ratio(
    nurse_supply: pl.DataFrame,
    beds_df: pl.DataFrame,
    supply_col: str = "projected_headcount",
    beds_col: str = "required_beds",
    year_col: str = "year",
    scenario_col: str = "scenario",
) -> pl.DataFrame:
    """Compute nurse:bed ratio per year and scenario.

    Joins nurse supply (historical CAGR) on year; joins beds (all scenarios) on year+scenario.

    Args:
        nurse_supply: Nurse supply projections (single scenario: historical CAGR)
        beds_df: Required beds DataFrame (year, scenario, required_beds)
        supply_col: Nurse headcount column in nurse_supply
        beds_col: Required beds column in beds_df
        year_col: Year column
        scenario_col: Scenario column in beds_df

    Returns:
        DataFrame with: year, scenario, projected_nurses, required_beds, nurse_bed_ratio
    """
    nurses = nurse_supply.select([
        pl.col(year_col).alias("year"),
        pl.col(supply_col).alias("projected_nurses"),
    ])

    combined = beds_df.join(nurses, on="year", how="left").with_columns(
        (pl.col("projected_nurses") / pl.col(beds_col)).round(4).alias("nurse_bed_ratio")
    )

    logger.info(
        f"Nurse:bed ratio computed for {combined[scenario_col].n_unique()} scenarios, "
        f"{combined['year'].n_unique()} years"
    )
    return combined


def classify_rag(ratio: float, green_threshold: float, amber_threshold: float) -> str:
    """Classify a nurse:bed ratio value as green/amber/red.

    Args:
        ratio: Nurse:bed ratio
        green_threshold: >= this → "green"
        amber_threshold: >= this and < green → "amber"; else → "red"

    Returns:
        "green" | "amber" | "red"
    """
    if ratio >= green_threshold:
        return "green"
    elif ratio >= amber_threshold:
        return "amber"
    return "red"


def apply_rag_to_alignment(
    alignment_df: pl.DataFrame,
    constants: dict,
    ratio_col: str = "nurse_bed_ratio",
) -> pl.DataFrame:
    """Apply RAG classification to each row of the alignment DataFrame.

    Args:
        alignment_df: Output of compute_nurse_bed_ratio
        constants: planning_constants dict with rag_green_threshold, rag_amber_threshold
        ratio_col: Nurse:bed ratio column

    Returns:
        DataFrame with added rag_status column and metadata columns
    """
    green = float(constants["rag_green_threshold"])
    amber = float(constants["rag_amber_threshold"])

    rag_values = [
        classify_rag(r, green, amber)
        for r in alignment_df[ratio_col].to_list()
    ]

    return alignment_df.with_columns([
        pl.Series("rag_status", rag_values),
        pl.lit(green).alias("benchmark_ratio"),
        pl.lit("WHO SEARO 2020").alias("benchmark_source"),
    ])


def find_first_divergence_year(
    alignment_df: pl.DataFrame,
    year_col: str = "year",
    scenario_col: str = "scenario",
    rag_col: str = "rag_status",
) -> dict[str, int | None]:
    """Find first year where RAG status drops to amber or red per scenario.

    Args:
        alignment_df: Alignment DataFrame with rag_status column
        year_col: Year column
        scenario_col: Scenario column
        rag_col: RAG status column

    Returns:
        Dict mapping scenario → first divergence year (None if always green)
    """
    result: dict[str, int | None] = {}
    for scenario in alignment_df[scenario_col].unique().to_list():
        sub = alignment_df.filter(pl.col(scenario_col) == scenario).sort(year_col)
        divergence_rows = sub.filter(pl.col(rag_col).is_in(["amber", "red"]))
        if len(divergence_rows) > 0:
            first_year = int(divergence_rows[year_col][0])
            result[str(scenario)] = first_year
            logger.warning(
                f"First staff-facility divergence [{scenario}]: year {first_year} "
                f"(status: {divergence_rows[rag_col][0]})"
            )
        else:
            result[str(scenario)] = None
            logger.info(f"No divergence through 2035 for scenario: {scenario}")
    return result
```

#### 3.2 `scripts/run_alignment_validation.py`

```python
"""PS-003 Story 05 — Staff-Facility Alignment Validation.

Run: python problem-statements/ps-003-healthcare-capacity/scripts/run_alignment_validation.py
"""

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_003_healthcare_capacity.src.planning_loader import load_planning_constants
from problem_statements.ps_003_healthcare_capacity.src.alignment_validator import (
    apply_rag_to_alignment,
    compute_nurse_bed_ratio,
    find_first_divergence_year,
)

PS_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PS_DIR / "results" / "tables"
FIGURES_DIR = PS_DIR / "reports" / "figures" / "ps003_planning"
LOG_DIR = PS_DIR / "logs" / "etl"
CONFIG_PATH = PROJECT_ROOT / "shared" / "config" / "base.yml"

for d in (RESULTS_DIR, FIGURES_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

logger.add(str(LOG_DIR / "ps003_alignment.log"), level="INFO", rotation="10 MB")


def main() -> None:
    logger.info("=== PS-003 Story 05: Staff-Facility Alignment ===")

    constants = load_planning_constants(CONFIG_PATH)

    supply = pl.read_csv(str(RESULTS_DIR / "ps003_workforce_supply_projections.csv"))
    beds = pl.read_csv(str(RESULTS_DIR / "ps003_bed_gap.csv"))

    # Filter nurse historical CAGR supply
    nurse_supply = supply.filter(
        (pl.col("profession") == "nurses") & (pl.col("scenario") == "cagr_historical")
    )

    alignment = compute_nurse_bed_ratio(nurse_supply, beds)
    alignment = apply_rag_to_alignment(alignment, constants)
    alignment.write_csv(str(RESULTS_DIR / "ps003_staff_facility_alignment.csv"))
    logger.info(f"Alignment saved: {RESULTS_DIR / 'ps003_staff_facility_alignment.csv'}")

    # First divergence year
    divergence = find_first_divergence_year(alignment)
    for scenario, year in divergence.items():
        if year:
            logger.info(f"DIVERGENCE [{scenario}]: first amber/red year = {year}")
        else:
            logger.info(f"All GREEN [{scenario}] through 2035")

    # Heatmap
    # Map RAG to numeric for imshow
    rag_numeric_map = {"green": 2, "amber": 1, "red": 0}
    alignment = alignment.with_columns(
        pl.col("rag_status").replace(rag_numeric_map).alias("rag_numeric")
    )

    scenarios = sorted(alignment["scenario"].unique().to_list())
    years = sorted(alignment["year"].unique().to_list())

    # Build matrix: rows=scenarios, cols=years
    matrix = []
    for scenario in scenarios:
        row = []
        for year in years:
            cell = alignment.filter(
                (pl.col("scenario") == scenario) & (pl.col("year") == year)
            )["rag_numeric"]
            row.append(int(cell[0]) if len(cell) > 0 else -1)
        matrix.append(row)

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=years,
        y=scenarios,
        colorscale=[[0.0, "#E74C3C"], [0.5, "#F39C12"], [1.0, "#27AE60"]],
        zmin=0, zmax=2,
        showscale=True,
        colorbar={"tickvals": [0, 1, 2], "ticktext": ["Red (Critical)", "Amber (Monitor)", "Green (Adequate)"]},
    ))
    fig.update_layout(
        title="[DRAFT] Staff-Facility Alignment | Nurse:Bed Ratio vs WHO Benchmark | MOH-SG",
        xaxis_title="Year", yaxis_title="Scenario",
        template="plotly_white", width=1200, height=500,
    )
    chart_path = FIGURES_DIR / "staff_facility_alignment_heatmap.png"
    fig.write_image(str(chart_path))
    logger.info(f"Heatmap: {chart_path}")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_alignment_validator.py
import polars as pl
import pytest


def test_classify_rag_green():
    from problem_statements.ps_003_healthcare_capacity.src.alignment_validator import classify_rag
    assert classify_rag(0.30, green_threshold=0.25, amber_threshold=0.20) == "green"


def test_classify_rag_amber():
    from problem_statements.ps_003_healthcare_capacity.src.alignment_validator import classify_rag
    assert classify_rag(0.22, green_threshold=0.25, amber_threshold=0.20) == "amber"


def test_classify_rag_red():
    from problem_statements.ps_003_healthcare_capacity.src.alignment_validator import classify_rag
    assert classify_rag(0.15, green_threshold=0.25, amber_threshold=0.20) == "red"


def test_apply_rag_adds_rag_status_column():
    from problem_statements.ps_003_healthcare_capacity.src.alignment_validator import apply_rag_to_alignment
    df = pl.DataFrame({"year": [2025], "scenario": ["principal"], "nurse_bed_ratio": [0.27]})
    constants = {"rag_green_threshold": 0.25, "rag_amber_threshold": 0.20}
    result = apply_rag_to_alignment(df, constants)
    assert result["rag_status"][0] == "green"


def test_find_first_divergence_detects_amber():
    from problem_statements.ps_003_healthcare_capacity.src.alignment_validator import find_first_divergence_year
    df = pl.DataFrame({
        "year": [2025, 2026, 2027],
        "scenario": ["principal"] * 3,
        "rag_status": ["green", "amber", "red"],
    })
    result = find_first_divergence_year(df)
    assert result["principal"] == 2026
```

---

### 5. Implementation Steps

- [ ] Create `src/alignment_validator.py`
- [ ] Create `scripts/run_alignment_validation.py`
- [ ] Run: `python scripts/run_alignment_validation.py`
- [ ] Verify `ps003_staff_facility_alignment.csv` exists with `rag_status` column
- [ ] Review log: check first divergence year messages
- [ ] Verify `staff_facility_alignment_heatmap.png` exists with colour-coded cells
- [ ] Run unit tests: `pytest tests/unit/test_alignment_validator.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-003-story-05-alignment-validation
git commit -m "feat(ps-003): add alignment_validator with RAG classification and divergence detection"
git commit -m "feat(ps-003): add run_alignment_validation script and RAG heatmap"
```
