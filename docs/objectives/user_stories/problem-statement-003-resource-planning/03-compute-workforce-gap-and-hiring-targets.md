# User Story: 3 — Workforce Demand Projection and Gap Analysis

**As a** MOH Deputy Secretary for Manpower,  
**I want** to compute required workforce levels for 2021–2035 based on projected admission volumes and WHO benchmark staffing ratios, then compare this demand against the supply projections to produce annual hiring targets,  
**so that** I can plan medical school intake and recruitment campaigns with a quantified, evidence-grounded shortfall number for each year.

## 1. 🎯 Acceptance Criteria

- Workforce demand computed for nurses and doctors using WHO SEARO benchmark method for each year 2021–2035 and each demographic scenario (principal, high, low)
- Demand formula: `required_nurses = projected_admissions * ALOS / 365 * beds_needed_per_admission * nurse_bed_ratio_benchmark`, simplified to: `required_nurses = projected_beds_needed * (nurses_per_bed_benchmark)`
- Workforce gap = `supply (historical CAGR scenario)` minus `demand` for each year and profession
- Annual hiring target = `gap / years_to_close (default: 5)` + `attrition_replacement` — output as both absolute headcount and percentage of current workforce
- Gap and hiring targets tabulated for 2025, 2030, 2035 (milestone years) in `results/tables/ps003_workforce_gap.csv`
- Full year-by-year gap series saved to `results/tables/ps003_workforce_gap_timeseries.csv`
- Chart: workforce supply vs demand (nurses and doctors) for principal scenario → `reports/figures/ps003_planning/workforce_gap_chart.png`

## 2. 🔒 Technical Constraints

- Use principal demographic scenario as primary; compute demand for all 3 scenarios for sensitivity table in Story 07
- Benchmark densities from `planning_constants` in config — do not hard-code in script
- Demand computation must flow through projected beds as intermediate (ensures alignment with Story 04's bed gap analysis): `required_beds = projected_admissions * ALOS / 365 / occupancy_rate_benchmark`
- `occupancy_rate_benchmark = 0.85` (from `planning_constants`)
- Multi-year closing period is configurable: default 5 years (2030 target from planning perspective); add as `planning_constants.gap_close_years = 5` in config

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — staffing ratio benchmarks, hiring target interpretation
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — full demand-gap formula, occupancy and ALOS context

## 4. 📦 Dependencies

- Story 01: `planning_constants` dict, `admission_volume_projections.csv`
- Story 02: `ps003_workforce_supply_projections.csv`
- `polars` — gap computation

## 5. ✅ Implementation Tasks

**Demand Computation**
- ⬜ Load `admission_volume_projections.csv` for principal scenario
- ⬜ Compute `required_beds = projected_admissions * ALOS / 365 / occupancy_rate_benchmark` for each year
- ⬜ Compute `required_nurses = required_beds * nurse_bed_ratio_benchmark` (nurses per bed)
- ⬜ Compute `required_doctors = required_beds * doctor_bed_ratio_benchmark` (where doctor ratio = 1 doctor per 10 beds as a planning proxy — cite source in comment)

**Gap Analysis**
- ⬜ Load `ps003_workforce_supply_projections.csv`; filter to historical CAGR scenario
- ⬜ Join supply and demand on `year`; compute gap = `supply - demand` per profession
- ⬜ Compute `hiring_target_annual = (-gap / gap_close_years) + attrition_loss` where gap is negative (shortfall)
- ⬜ Flag years where gap < 0 (shortage) vs > 0 (surplus)

**Milestone Summary**
- ⬜ Extract rows for 2025, 2030, 2035; compute summary columns: `gap_headcount, hiring_target_annual, gap_as_pct_of_supply`
- ⬜ Save milestone summary to `results/tables/ps003_workforce_gap.csv`
- ⬜ Save full year series to `results/tables/ps003_workforce_gap_timeseries.csv`

**Chart**
- ⬜ Plot supply and demand lines for nurses and doctors (principal scenario) → `ps003_planning/workforce_gap_chart.png`
- ⬜ Shade gap region: red if demand > supply, green if supply ≥ demand
- ⬜ Add milestone annotations at 2025, 2030, 2035

## 6. Notes

- The doctor:bed ratio of 1 doctor per 10 beds is a planning proxy — it is lower than the nurse ratio but acceptable as a conservative estimate pending actual Singapore staffing data. Document explicitly.
- The hiring target output is the key policy-actionable metric: "We need to hire X more nurses per year for the next 5 years to meet demand by 2030." Keep this number prominently labelled in outputs.
- Milestone year summaries (2025, 2030, 2035) are used directly in the dashboard's Workforce Planning tab and the Executive Summary tab.

---

## Implementation Plan

### 1. Feature Overview

Compute required nurse and doctor workforce levels from projected admissions and benchmark ratios. Compare against supply to compute annual hiring targets. Produce milestone summary and gap timeseries CSV plus a gap chart. Primary user: **MOH Deputy Secretary for Manpower**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-003-healthcare-capacity/src/gap_analyser.py
  - compute_required_beds(admissions_df, constants) -> pl.DataFrame
  - compute_required_workforce(beds_df, constants) -> pl.DataFrame
  - compute_workforce_gap(supply_df, demand_df, constants) -> pl.DataFrame
  - extract_milestone_summary(gap_df, milestone_years) -> pl.DataFrame

[CREATE] problem-statements/ps-003-healthcare-capacity/scripts/run_gap_analysis.py
  - Orchestrates workforce demand → gap → hiring targets; writes CSVs and chart
```

---

### 3. Code Generation Specifications

#### 3.1 `src/gap_analyser.py`

```python
"""PS-003 workforce demand computation and gap analysis.

Demand flows: projected_admissions → required_beds → required_nurses/doctors.
Gap = supply (historical CAGR) - demand.
Hiring target = (-gap / gap_close_years) + attrition_replacement (when gap < 0).
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

DOCTOR_BED_RATIO = 0.10  # 1 doctor per 10 beds (planning proxy — MOH Annual Report)
MILESTONE_YEARS = [2025, 2030, 2035]


def compute_required_beds(
    admissions_df: pl.DataFrame,
    constants: dict,
    scenario: str = "principal",
    year_col: str = "year",
    admissions_col: str = "projected_admissions",
    scenario_col: str = "scenario",
) -> pl.DataFrame:
    """Compute required inpatient beds from projected admissions.

    Formula: required_beds = projected_admissions * ALOS / 365 / occupancy_rate

    Args:
        admissions_df: Admission projections (long format with scenario column)
        constants: planning_constants dict
        scenario: Demographic scenario to use (default: "principal")
        year_col: Year column name
        admissions_col: Projected admissions column name
        scenario_col: Scenario column name

    Returns:
        DataFrame with columns: year, required_beds
    """
    alos = float(constants["alos_days"])
    occ = float(constants["occupancy_rate_benchmark"])

    df = admissions_df.filter(pl.col(scenario_col) == scenario) if scenario_col in admissions_df.columns else admissions_df

    return df.with_columns(
        (pl.col(admissions_col) * alos / 365.0 / occ).round(0).cast(pl.Int64).alias("required_beds")
    ).select([year_col, "required_beds"])


def compute_required_workforce(
    beds_df: pl.DataFrame,
    constants: dict,
    year_col: str = "year",
    beds_col: str = "required_beds",
) -> pl.DataFrame:
    """Compute required nurses and doctors from required beds.

    Args:
        beds_df: DataFrame with year and required_beds columns
        constants: planning_constants dict
        year_col: Year column name
        beds_col: Required beds column name

    Returns:
        DataFrame with year, required_beds, required_nurses, required_doctors
    """
    nurse_ratio = float(constants["nurse_bed_ratio_benchmark"])

    return beds_df.with_columns([
        (pl.col(beds_col) * nurse_ratio).round(0).cast(pl.Int64).alias("required_nurses"),
        (pl.col(beds_col) * DOCTOR_BED_RATIO).round(0).cast(pl.Int64).alias("required_doctors"),
    ])


def compute_workforce_gap(
    supply_df: pl.DataFrame,
    demand_df: pl.DataFrame,
    constants: dict,
    profession: str,
    supply_headcount_col: str = "projected_headcount",
    supply_year_col: str = "year",
    demand_year_col: str = "year",
) -> pl.DataFrame:
    """Compute annual gap and hiring targets for a single profession.

    Args:
        supply_df: Supply projections filtered to one profession and scenario
        demand_df: Required workforce per year
        constants: planning_constants dict
        profession: "nurses" or "doctors"
        supply_headcount_col: Supply headcount column
        supply_year_col: Year column in supply_df
        demand_year_col: Year column in demand_df

    Returns:
        DataFrame with: year, supply, demand, gap, shortage_flag,
            hiring_target_annual, gap_as_pct_of_supply
    """
    gap_close_years = float(constants["gap_close_years"])

    demand_col = f"required_{profession}"
    attrition_col = "attrition_loss"

    supply = supply_df.select([
        pl.col(supply_year_col).alias("year"),
        pl.col(supply_headcount_col).alias("supply"),
        pl.col(attrition_col) if attrition_col in supply_df.columns else pl.lit(0).alias(attrition_col),
    ])

    demand = demand_df.select([
        pl.col(demand_year_col).alias("year"),
        pl.col(demand_col).alias("demand"),
    ])

    combined = supply.join(demand, on="year", how="inner").with_columns([
        (pl.col("supply") - pl.col("demand")).alias("gap"),
        (pl.col("gap").is_negative() if "gap" in supply.columns else pl.lit(False)).alias("placeholder"),
    ]).drop("placeholder")

    return combined.with_columns([
        (pl.col("gap") < 0).alias("shortage_flag"),
        # hiring_target: apply only when gap is negative (shortfall)
        (
            ((-pl.col("gap") / gap_close_years) + pl.col(attrition_col))
            .clip(lower_bound=0)
        ).alias("hiring_target_annual"),
        (pl.col("gap") / pl.col("supply") * 100).round(1).alias("gap_as_pct_of_supply"),
    ]).with_columns(
        pl.lit(profession).alias("profession")
    )


def extract_milestone_summary(
    gap_df: pl.DataFrame,
    milestone_years: list[int] | None = None,
    year_col: str = "year",
) -> pl.DataFrame:
    """Extract gap and hiring target for milestone years only.

    Args:
        gap_df: Output of compute_workforce_gap (stacked across professions)
        milestone_years: Years to extract (default: [2025, 2030, 2035])
        year_col: Year column name

    Returns:
        Filtered DataFrame for milestone years with summary columns
    """
    if milestone_years is None:
        milestone_years = MILESTONE_YEARS
    return gap_df.filter(pl.col(year_col).cast(pl.Int32).is_in(milestone_years))
```

#### 3.2 `scripts/run_gap_analysis.py`

```python
"""PS-003 Story 03 — Workforce Gap and Hiring Targets.

Run: python problem-statements/ps-003-healthcare-capacity/scripts/run_gap_analysis.py
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_003_healthcare_capacity.src.planning_loader import load_planning_constants
from problem_statements.ps_003_healthcare_capacity.src.gap_analyser import (
    compute_required_beds,
    compute_required_workforce,
    compute_workforce_gap,
    extract_milestone_summary,
)

PS002_DIR = PROJECT_ROOT / "problem-statements" / "ps-002-disease-burden"
PS_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PS_DIR / "results" / "tables"
FIGURES_DIR = PS_DIR / "reports" / "figures" / "ps003_planning"
LOG_DIR = PS_DIR / "logs" / "etl"
CONFIG_PATH = PROJECT_ROOT / "shared" / "config" / "base.yml"

for d in (RESULTS_DIR, FIGURES_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

logger.add(str(LOG_DIR / "ps003_gap_analysis.log"), level="INFO", rotation="10 MB")


def main() -> None:
    logger.info("=== PS-003 Story 03: Workforce Gap Analysis ===")

    constants = load_planning_constants(CONFIG_PATH)

    admissions = pl.read_csv(
        str(PS002_DIR / "models" / "forecasts" / "admission_volume_projections.csv")
    )
    supply = pl.read_csv(str(PS_DIR / "results" / "tables" / "ps003_workforce_supply_projections.csv"))

    # Compute required beds (principal scenario)
    beds = compute_required_beds(admissions, constants, scenario="principal")
    demand = compute_required_workforce(beds, constants)

    gap_frames: list[pl.DataFrame] = []
    for profession in ["nurses", "doctors"]:
        supply_filtered = supply.filter(
            (pl.col("profession") == profession) & (pl.col("scenario") == "cagr_historical")
        )
        gap_df = compute_workforce_gap(supply_filtered, demand, constants, profession)
        gap_frames.append(gap_df)

    all_gaps = pl.concat(gap_frames)

    # Write timeseries
    ts_path = RESULTS_DIR / "ps003_workforce_gap_timeseries.csv"
    all_gaps.write_csv(str(ts_path))
    logger.info(f"Gap timeseries: {ts_path}")

    # Milestone summary
    milestone = extract_milestone_summary(all_gaps)
    ms_path = RESULTS_DIR / "ps003_workforce_gap.csv"
    milestone.write_csv(str(ms_path))
    logger.info(f"Milestone summary: {ms_path}")

    # Chart — supply vs demand for nurses and doctors
    fig = go.Figure()
    colours = {"nurses": "#2980B9", "doctors": "#E74C3C"}
    for profession in ["nurses", "doctors"]:
        sub = all_gaps.filter(pl.col("profession") == profession).sort("year").to_pandas()
        colour = colours[profession]
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["supply"], mode="lines",
            name=f"{profession.title()} Supply", line={"color": colour, "width": 2},
        ))
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["demand"], mode="lines",
            name=f"{profession.title()} Demand",
            line={"color": colour, "width": 2, "dash": "dash"},
        ))
        # Shade gap red where shortage
        shortage = sub[sub["shortage_flag"]]
        if len(shortage) > 0:
            fig.add_trace(go.Scatter(
                x=shortage["year"].tolist() + shortage["year"].tolist()[::-1],
                y=shortage["demand"].tolist() + shortage["supply"].tolist()[::-1],
                fill="toself", fillcolor="rgba(231,76,60,0.2)",
                mode="none", name=f"{profession.title()} Shortage Zone", showlegend=True,
            ))

    for yr in [2025, 2030, 2035]:
        fig.add_vline(x=yr, line_dash="dot", line_color="grey",
                      annotation_text=str(yr), annotation_font_size=10)

    fig.update_layout(
        title="[DRAFT] Workforce Supply vs Demand | Nurses & Doctors | MOH-SG 2021–2035",
        xaxis_title="Year", yaxis_title="Headcount",
        template="plotly_white", width=1200, height=700,
    )
    chart_path = FIGURES_DIR / "workforce_gap_chart.png"
    fig.write_image(str(chart_path))
    logger.info(f"Gap chart: {chart_path}")

    # Log key metrics
    nurses_2030 = milestone.filter(
        (pl.col("year") == 2030) & (pl.col("profession") == "nurses")
    )
    if len(nurses_2030) > 0:
        gap_val = int(nurses_2030["gap"][0])
        hiring = int(nurses_2030["hiring_target_annual"][0])
        logger.info(f"Nurses gap at 2030: {gap_val:+,} | Annual hiring target: {hiring:,}/yr")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_gap_analyser.py
import polars as pl
import pytest


def test_compute_required_beds_formula():
    from problem_statements.ps_003_healthcare_capacity.src.gap_analyser import compute_required_beds
    admissions = pl.DataFrame({
        "year": [2025], "projected_admissions": [730000.0], "scenario": ["principal"]
    })
    constants = {"alos_days": 5.0, "occupancy_rate_benchmark": 1.0}  # simplified
    beds = compute_required_beds(admissions, constants, scenario="principal")
    # required_beds = 730000 * 5 / 365 / 1.0 = 10000
    assert beds["required_beds"][0] == 10000


def test_compute_required_workforce_nurses_ratio():
    from problem_statements.ps_003_healthcare_capacity.src.gap_analyser import compute_required_workforce
    beds = pl.DataFrame({"year": [2025], "required_beds": [10000]})
    constants = {"nurse_bed_ratio_benchmark": 0.25}
    demand = compute_required_workforce(beds, constants)
    assert demand["required_nurses"][0] == 2500


def test_compute_workforce_gap_shortage_flag():
    from problem_statements.ps_003_healthcare_capacity.src.gap_analyser import compute_workforce_gap
    supply = pl.DataFrame({
        "year": [2025], "projected_headcount": [2000], "attrition_loss": [100]
    })
    demand = pl.DataFrame({"year": [2025], "required_nurses": [2500]})
    constants = {"gap_close_years": 5}
    gap = compute_workforce_gap(supply, demand, constants, "nurses")
    assert gap["shortage_flag"][0] is True
    assert gap["gap"][0] == -500
```

---

### 5. Implementation Steps

- [ ] Create `src/gap_analyser.py`
- [ ] Create `scripts/run_gap_analysis.py`
- [ ] Run: `python scripts/run_gap_analysis.py`
- [ ] Verify `ps003_workforce_gap_timeseries.csv` has years 2021–2035 × 2 professions = 30 rows
- [ ] Verify `ps003_workforce_gap.csv` has 6 rows (2025, 2030, 2035 × nurses, doctors)
- [ ] Verify `workforce_gap_chart.png` exists with supply/demand lines
- [ ] Check log for 2030 nurses gap value
- [ ] Run unit tests: `pytest tests/unit/test_gap_analyser.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-003-story-03-workforce-gap
git commit -m "feat(ps-003): add gap_analyser with beds→demand→gap→hiring pipeline"
git commit -m "feat(ps-003): add run_gap_analysis script with supply/demand chart"
```
