# User Story: 4 — Bed Demand Projection and Capacity Gap Analysis

**As a** MOH infrastructure planning manager,  
**I want** to compute required inpatient bed capacity for 2021–2035 based on projected admissions and then compare this against the historical capacity growth trend,  
**so that** I can identify how many additional beds are needed and when commissioning windows must begin given typical 3–5 year hospital construction lead times.

## 1. 🎯 Acceptance Criteria

- Required bed levels computed for 2021–2035 using `required_beds = projected_admissions * ALOS / 365 / occupancy_rate_benchmark` for all 3 demographic scenarios
- Historical capacity growth trend extrapolated (using PS-001 CAGR for beds) as a supply baseline
- Bed gap computed = `required_beds - trend_supply_beds` for each year and scenario
- Commissioning milestone table generated: identify the first year each scenario exceeds supply capacity — this is the "commissioning trigger year"; then back-calculate the `planning_start_year = trigger_year - 5` (default construction lead time)
- Output: `results/tables/ps003_bed_gap.csv` — columns: `year, scenario, required_beds, trend_supply_beds, gap, commissioning_trigger (bool)`
- Output: `results/tables/ps003_commissioning_milestones.csv` — columns: `scenario, trigger_year, planning_start_year, gap_at_trigger, new_beds_needed`
- Chart: required vs trend supply beds for all 3 scenarios → `reports/figures/ps003_planning/bed_capacity_gap.png`

## 2. 🔒 Technical Constraints

- `ALOS = 5.1` days and `occupancy_rate_benchmark = 0.85` from `planning_constants` config
- Bed supply extrapolation uses the same CAGR-compounding method as Story 02 workforce supply — source CAGR from `baseline_metrics.csv` for beds (facility type = total or acute)
- Construction lead time default = 5 years — stored as `planning_constants.construction_lead_time_years`
- Commissioning trigger: first year where `required_beds > trend_supply_beds` for at least 2 consecutive years (to avoid single-year noise triggering the flag)
- Bed gap units: absolute (number of beds); percentage of supply; and beds per 10,000 population (to enable benchmark comparison)

## 3. 📚 Domain Knowledge References

- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — bed demand formula, construction lead time, WHO beds/10k benchmark (21)
- [Time-Series Forecasting Methods](../../../../domain-knowledge/time-series-forecasting-methods.md) — CAGR extrapolation methodology

## 4. 📦 Dependencies

- Story 01: `admission_volume_projections.csv`, `planning_constants`, `baseline_metrics.csv` (bed CAGR)
- `polars` — gap computation
- `plotly`, `kaleido` — chart

## 5. ✅ Implementation Tasks

**Required Beds**
- ⬜ Load `admission_volume_projections.csv`; for each scenario and year compute `required_beds`
- ⬜ Add `beds_per_10k = required_beds / projected_population * 10000` column

**Supply Extrapolation**
- ⬜ Load bed CAGR from `baseline_metrics.csv`; extrapolate from 2020 actuals using compound growth formula
- ⬜ Compute `trend_supply_beds` for 2021–2035

**Gap and Milestones**
- ⬜ Compute `gap = required_beds - trend_supply_beds`; flag as `gap_positive = True` where gap > 0
- ⬜ Identify commissioning trigger year per scenario: first of 2+ consecutive years with positive gap
- ⬜ Back-calculate `planning_start_year = trigger_year - construction_lead_time_years`
- ⬜ Compute `new_beds_needed = gap at 2035 (high scenario)`
- ⬜ Save gap series to `ps003_bed_gap.csv`
- ⬜ Save milestones to `ps003_commissioning_milestones.csv`

**Chart**
- ⬜ Plot: required beds (3 scenario lines) + trend supply (single line) → `bed_capacity_gap.png`
- ⬜ Shade gap between high scenario and supply in red
- ⬜ Annotate commissioning trigger year for principal scenario with vertical marker and label

## 6. Notes

- The construction lead time of 5 years means if demand exceeds supply in 2028, planning must begin in 2023 — this urgency message is critical for the executive summary tab.
- The high-scenario required beds sets the stress-test ceiling. The principal scenario is the planning reference. The dashboard's Facility Capacity tab will show all three.
- Beds/10k in 2035 should be compared against the WHO benchmark of 21/10k. If Singapore's required beds/10k falls below this, flag as "below international standard" in the commissioning milestones table.

---

## Implementation Plan

### 1. Feature Overview

Compute required inpatient beds 2021–2035 for all 3 demographic scenarios. Extrapolate supply trend using bed CAGR from PS-001. Identify commissioning trigger years and back-calculate planning start dates. Produce gap CSV, milestones CSV, and capacity chart. Primary user: **MOH infrastructure planning manager**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-003-healthcare-capacity/src/bed_gap_analyser.py
  - compute_trend_supply_beds(baseline_metrics_df, constants, projection_years) -> pl.DataFrame
  - compute_bed_gap(required_df, supply_df) -> pl.DataFrame
  - identify_commissioning_triggers(gap_df, lead_time_years) -> pl.DataFrame

[CREATE] problem-statements/ps-003-healthcare-capacity/scripts/run_bed_gap_analysis.py
  - Orchestrates bed gap; writes CSVs and chart
```

---

### 3. Code Generation Specifications

#### 3.1 `src/bed_gap_analyser.py`

```python
"""PS-003 inpatient bed gap analysis and commissioning trigger detection.

Required beds: projected_admissions * ALOS / 365 / occupancy_rate (already in gap_analyser)
Supply: CAGR-extrapolated from 2020 actuals using PS-001 bed CAGR.
Commissioning trigger: first year with 2+ consecutive years of required > supply.
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

WHO_BEDS_PER_10K = 21.0  # WHO SEARO benchmark


def compute_trend_supply_beds(
    baseline_metrics: pl.DataFrame,
    constants: dict,
    projection_years: list[int],
    base_year: int = 2020,
    beds_cagr_key: str = "beds",
) -> pl.DataFrame:
    """Extrapolate inpatient bed supply using CAGR from PS-001 baseline_metrics.

    Args:
        baseline_metrics: PS-001 baseline_metrics.csv
        constants: planning_constants dict
        projection_years: Years to project
        base_year: Base year for extrapolation
        beds_cagr_key: Key to match beds CAGR in baseline_metrics

    Returns:
        DataFrame with columns: year, trend_supply_beds
    """
    # Extract beds CAGR
    cagr_row = (
        baseline_metrics
        .filter(
            pl.col("metric_type") == "cagr" if "metric_type" in baseline_metrics.columns
            else pl.lit(True)
        )
        .filter(pl.col("dimension").str.to_lowercase().str.contains("bed") if "dimension" in baseline_metrics.columns
                else pl.col("profession").str.to_lowercase().str.contains("bed") if "profession" in baseline_metrics.columns
                else pl.lit(True))
    )

    beds_cagr = float(cagr_row["value"][0]) if len(cagr_row) > 0 and "value" in cagr_row.columns else 0.02
    logger.info(f"Beds CAGR from baseline_metrics: {beds_cagr:.3f}")

    # Base beds at 2020 (from baseline metrics value for beds in last available year)
    base_beds_row = baseline_metrics.filter(
        (pl.col("year").cast(pl.Int32) == base_year) if "year" in baseline_metrics.columns
        else pl.lit(True)
    ).filter(
        pl.col("dimension").str.to_lowercase().str.contains("bed") if "dimension" in baseline_metrics.columns else pl.lit(True)
    )
    base_beds = float(base_beds_row["value"][0]) if len(base_beds_row) > 0 and "value" in base_beds_row.columns else 12000.0
    logger.info(f"Base beds at {base_year}: {base_beds:.0f}")

    rows = []
    for year in projection_years:
        supply = base_beds * (1.0 + beds_cagr) ** (year - base_year)
        rows.append({"year": year, "trend_supply_beds": round(supply)})

    return pl.DataFrame(rows)


def compute_bed_gap(
    required_df: pl.DataFrame,
    supply_df: pl.DataFrame,
    required_col: str = "required_beds",
    supply_col: str = "trend_supply_beds",
    year_col: str = "year",
    scenario_col: str = "scenario",
) -> pl.DataFrame:
    """Compute bed gap per year and scenario.

    Args:
        required_df: Required beds (year, scenario, required_beds columns)
        supply_df: Trend supply beds (year, trend_supply_beds)
        required_col: Required beds column
        supply_col: Supply beds column
        year_col: Year column
        scenario_col: Scenario column

    Returns:
        DataFrame with: year, scenario, required_beds, trend_supply_beds, gap, gap_positive
    """
    combined = required_df.join(supply_df, on=year_col, how="left").with_columns([
        (pl.col(required_col) - pl.col(supply_col)).alias("gap"),
    ]).with_columns(
        (pl.col("gap") > 0).alias("gap_positive")
    )
    return combined


def identify_commissioning_triggers(
    gap_df: pl.DataFrame,
    lead_time_years: int = 5,
    year_col: str = "year",
    scenario_col: str = "scenario",
    gap_positive_col: str = "gap_positive",
) -> pl.DataFrame:
    """Identify first commissioning trigger year per scenario.

    Trigger: first of 2+ consecutive years with gap > 0.
    Back-calculate planning_start_year = trigger_year - lead_time_years.

    Args:
        gap_df: Output of compute_bed_gap
        lead_time_years: Hospital construction lead time (default: 5)
        year_col: Year column
        scenario_col: Scenario column
        gap_positive_col: Boolean column indicating positive gap

    Returns:
        DataFrame with: scenario, trigger_year, planning_start_year,
            gap_at_trigger, new_beds_needed (gap at 2035)
    """
    rows: list[dict] = []

    for scenario in gap_df[scenario_col].unique().to_list():
        sub = gap_df.filter(pl.col(scenario_col) == scenario).sort(year_col)
        years = sub[year_col].to_list()
        flags = sub[gap_positive_col].to_list()
        gaps = sub["gap"].to_list()

        trigger_year = None
        for i in range(1, len(years)):
            if flags[i] and flags[i - 1]:
                trigger_year = years[i - 1]  # First of 2 consecutive
                gap_at_trigger = gaps[i - 1]
                break

        # Beds needed = gap at 2035 (high-stress endpoint)
        last_positive = [g for g, f in zip(gaps, flags) if f]
        new_beds_needed = round(last_positive[-1]) if last_positive else 0

        who_beds_10k_note = None
        last_required_row = gap_df.filter(
            (pl.col(scenario_col) == scenario)
        ).sort(year_col, descending=True)
        if len(last_required_row) > 0 and "required_beds" in last_required_row.columns:
            last_req = float(last_required_row["required_beds"][0])
            # Rough 2035 population for comparison — use 6 million as Singapore estimate
            beds_per_10k_2035 = last_req / 6_000_000 * 10_000
            if beds_per_10k_2035 < WHO_BEDS_PER_10K:
                who_beds_10k_note = (
                    f"BELOW international standard: {beds_per_10k_2035:.1f} vs WHO {WHO_BEDS_PER_10K}/10k"
                )

        rows.append({
            "scenario": scenario,
            "trigger_year": trigger_year,
            "planning_start_year": (trigger_year - lead_time_years) if trigger_year else None,
            "gap_at_trigger": gap_at_trigger if trigger_year else None,
            "new_beds_needed": new_beds_needed,
            "who_benchmark_note": who_beds_10k_note or "Within WHO standard",
        })

    return pl.DataFrame(rows)
```

#### 3.2 `scripts/run_bed_gap_analysis.py`

```python
"""PS-003 Story 04 — Bed Gap and Commissioning Plan.

Run: python problem-statements/ps-003-healthcare-capacity/scripts/run_bed_gap_analysis.py
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_003_healthcare_capacity.src.planning_loader import load_planning_constants
from problem_statements.ps_003_healthcare_capacity.src.gap_analyser import compute_required_beds
from problem_statements.ps_003_healthcare_capacity.src.bed_gap_analyser import (
    compute_bed_gap,
    compute_trend_supply_beds,
    identify_commissioning_triggers,
)

PS001_DIR = PROJECT_ROOT / "problem-statements" / "ps-001-healthcare-system-baseline"
PS002_DIR = PROJECT_ROOT / "problem-statements" / "ps-002-disease-burden"
PS_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PS_DIR / "results" / "tables"
FIGURES_DIR = PS_DIR / "reports" / "figures" / "ps003_planning"
LOG_DIR = PS_DIR / "logs" / "etl"
CONFIG_PATH = PROJECT_ROOT / "shared" / "config" / "base.yml"

for d in (RESULTS_DIR, FIGURES_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

logger.add(str(LOG_DIR / "ps003_bed_gap.log"), level="INFO", rotation="10 MB")

PROJECTION_YEARS = list(range(2021, 2036))
SCENARIOS = ["principal", "high", "low"]


def main() -> None:
    logger.info("=== PS-003 Story 04: Bed Gap and Commissioning Plan ===")

    constants = load_planning_constants(CONFIG_PATH)
    baseline = pl.read_csv(str(PS001_DIR / "results" / "tables" / "baseline_metrics.csv"))
    admissions = pl.read_csv(
        str(PS002_DIR / "models" / "forecasts" / "admission_volume_projections.csv")
    )

    # Required beds per scenario
    required_frames: list[pl.DataFrame] = []
    for scenario in SCENARIOS:
        beds = compute_required_beds(admissions, constants, scenario=scenario)
        beds = beds.with_columns(pl.lit(scenario).alias("scenario"))
        required_frames.append(beds)
    all_required = pl.concat(required_frames)

    # Trend supply beds
    supply = compute_trend_supply_beds(baseline, constants, PROJECTION_YEARS)

    # Gap
    gap_df = compute_bed_gap(all_required, supply)
    gap_df.write_csv(str(RESULTS_DIR / "ps003_bed_gap.csv"))
    logger.info(f"Bed gap saved: {RESULTS_DIR / 'ps003_bed_gap.csv'}")

    # Commissioning milestones
    lead_time = int(constants.get("construction_lead_time_years", 5))
    milestones = identify_commissioning_triggers(gap_df, lead_time_years=lead_time)
    milestones.write_csv(str(RESULTS_DIR / "ps003_commissioning_milestones.csv"))
    logger.info(f"Commissioning milestones:\n{milestones}")

    # Chart
    fig = go.Figure()
    scenario_colours = {"principal": "#2980B9", "high": "#E74C3C", "low": "#27AE60"}
    gap_pd = gap_df.to_pandas()

    for scenario in SCENARIOS:
        sub = gap_pd[gap_pd["scenario"] == scenario]
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["required_beds"], mode="lines",
            name=f"Required ({scenario.title()})",
            line={"color": scenario_colours[scenario], "width": 2},
        ))

    supply_pd = supply.to_pandas()
    fig.add_trace(go.Scatter(
        x=supply_pd["year"], y=supply_pd["trend_supply_beds"], mode="lines",
        name="Trend Supply (CAGR)", line={"color": "#888", "width": 2, "dash": "dash"},
    ))

    # Shade high-scenario gap against supply
    high = gap_pd[gap_pd["scenario"] == "high"]
    fig.add_trace(go.Scatter(
        x=supply_pd["year"].tolist() + high["year"].tolist()[::-1],
        y=supply_pd["trend_supply_beds"].tolist() + high["required_beds"].tolist()[::-1],
        fill="toself", fillcolor="rgba(231,76,60,0.15)", mode="none",
        name="High-scenario demand gap",
    ))

    # Annotate principal commissioning trigger
    principal_trigger = milestones.filter(pl.col("scenario") == "principal")["trigger_year"][0] if len(milestones) > 0 else None
    if principal_trigger:
        fig.add_vline(
            x=principal_trigger, line_dash="dot", line_color="red",
            annotation_text=f"Commissioning trigger {principal_trigger}",
        )

    fig.update_layout(
        title="[DRAFT] Inpatient Bed Capacity Gap | 3 Demographic Scenarios | MOH-SG 2021–2035",
        xaxis_title="Year", yaxis_title="Beds",
        template="plotly_white", width=1200, height=700,
    )
    chart_path = FIGURES_DIR / "bed_capacity_gap.png"
    fig.write_image(str(chart_path))
    logger.info(f"Bed gap chart: {chart_path}")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_bed_gap_analyser.py
import polars as pl
import pytest


def test_compute_bed_gap_gap_column():
    from problem_statements.ps_003_healthcare_capacity.src.bed_gap_analyser import compute_bed_gap
    required = pl.DataFrame({
        "year": [2025], "scenario": ["principal"], "required_beds": [15000]
    })
    supply = pl.DataFrame({"year": [2025], "trend_supply_beds": [12000]})
    gap = compute_bed_gap(required, supply)
    assert gap["gap"][0] == 3000
    assert gap["gap_positive"][0] is True


def test_identify_commissioning_triggers_detects_consecutive():
    from problem_statements.ps_003_healthcare_capacity.src.bed_gap_analyser import identify_commissioning_triggers
    gap_df = pl.DataFrame({
        "year": [2022, 2023, 2024, 2025],
        "scenario": ["principal"] * 4,
        "gap": [-100, 200, 300, 400],
        "gap_positive": [False, True, True, True],
        "required_beds": [12000, 12200, 12400, 12600],
    })
    milestones = identify_commissioning_triggers(gap_df, lead_time_years=5)
    assert milestones["trigger_year"][0] == 2023
    assert milestones["planning_start_year"][0] == 2018
```

---

### 5. Implementation Steps

- [ ] Create `src/bed_gap_analyser.py`
- [ ] Create `scripts/run_bed_gap_analysis.py`
- [ ] Run: `python scripts/run_bed_gap_analysis.py`
- [ ] Verify `ps003_bed_gap.csv` has 45 rows (15 years × 3 scenarios)
- [ ] Verify `ps003_commissioning_milestones.csv` has 3 rows
- [ ] Check commissioning trigger years are plausible (2024–2030 range expected)
- [ ] Verify `bed_capacity_gap.png` exists
- [ ] Run unit tests: `pytest tests/unit/test_bed_gap_analyser.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-003-story-04-bed-gap
git commit -m "feat(ps-003): add bed_gap_analyser with supply extrapolation and trigger detection"
git commit -m "feat(ps-003): add run_bed_gap_analysis script with 3-scenario chart"
```
