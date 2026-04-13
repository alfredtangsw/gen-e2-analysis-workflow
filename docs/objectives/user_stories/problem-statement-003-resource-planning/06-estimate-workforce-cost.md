# User Story: 6 — Workforce Cost Estimation

**As a** MOH Director of Finance,  
**I want** to estimate the annual incremental workforce cost of closing the nurse and doctor shortfalls identified in Story 03,  
**so that** I can include a budget envelope in the five-year financial plan and present a cost range to Treasury.

## 1. 🎯 Acceptance Criteria

- Incremental workforce cost computed for nurses and doctors for each year 2022–2035 under all 3 demographic scenarios
- Cost formula: `annual_cost = hiring_target_annual * median_monthly_salary * 12 * overhead_multiplier`
- Overhead multiplier covers employer CPF (17%), benefits, and training allowances — applied as 1.35× on base salary
- Total incremental cost expressed as: (a) SGD million per year, (b) cumulative SGD million to 2030, (c) cumulative SGD million to 2035
- Comparison against PS-001 government health expenditure baseline — incremental cost as a % of 2018 total govt health spend (to give relative scale)
- Scope explicitly bounded: "Workforce cost only — infrastructure and consumables excluded due to absence of unit cost data"
- Output: `results/tables/ps003_workforce_cost.csv` — columns: `year, profession, scenario, hiring_target, median_salary_sgd, annual_cost_sgd_m, cumulative_cost_sgd_m`
- Output: `results/exports/ps003_cost_summary.csv` — summary table: milestone years 2025, 2030, 2035 × profession × scenario

## 2. 🔒 Technical Constraints

- Salary values from `planning_constants` in config (`rn_median_wage_sgd = 4200`, `gp_median_wage_sgd = 8500`)
- Cost expressed in nominal SGD — clearly labelled as "nominal, not inflation-adjusted" in output CSV metadata row
- Overhead multiplier from `planning_constants.overhead_multiplier = 1.35`
- Hiring targets sourced from Story 03 `ps003_workforce_gap_timeseries.csv` — do not recompute gaps here
- Scope boundary statement must appear as a `notes` column value in the output CSV: `"Workforce cost only — excludes infrastructure, equipment, and consumables"`
- All cost figures in SGD millions (rounded to 2 decimal places)

## 3. 📚 Domain Knowledge References

- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — overhead methodology, CPF employer rate, cost formula
- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — salary benchmarks context

## 4. 📦 Dependencies

- Story 01: `planning_constants` (salary, overhead), `expenditure_baseline.csv` from PS-001 (for % comparison)
- Story 03: `ps003_workforce_gap_timeseries.csv` — hiring targets per year, profession, scenario
- `polars` — cost computation

## 5. ✅ Implementation Tasks

**Cost Computation**
- ⬜ Load `ps003_workforce_gap_timeseries.csv`; extract `hiring_target_annual` per year × profession × scenario
- ⬜ Join with salary map: `{nurse: 4200, doctor: 8500}` from config
- ⬜ Compute `annual_cost_sgd = hiring_target * salary * 12 * overhead_multiplier`
- ⬜ Convert to SGD millions: `annual_cost_sgd_m = annual_cost_sgd / 1_000_000`
- ⬜ Compute `cumulative_cost_sgd_m` as running total per profession × scenario

**Expenditure Comparison**
- ⬜ Load `expenditure_baseline.csv` from PS-001; extract 2018 total govt health expenditure
- ⬜ Compute `cost_as_pct_of_2018_expenditure = annual_cost_2030 / total_2018_expenditure * 100`
- ⬜ Add this ratio to the cost summary table as a reference column

**Output Tables**
- ⬜ Save full year-by-year table to `results/tables/ps003_workforce_cost.csv` with `notes` column
- ⬜ Extract milestone years 2025, 2030, 2035; save to `results/exports/ps003_cost_summary.csv`
- ⬜ Both files must include `scope_boundary` column: "Workforce only — excludes infrastructure and consumables"

**Logging**
- ⬜ Log 2030 and 2035 cumulative cost (principal scenario) per profession to `logs/etl/ps003_cost_estimation.log`
- ⬜ Log cost as % of 2018 expenditure

## 6. Notes

- "Nominal SGD" labelling is important — leadership will likely ask "is this adjusted for inflation?" The honest answer is no, and that should be visible in the output.
- The percentage of 2018 expenditure comparison gives easy context: e.g. "Closing the nurse shortfall will require an incremental spend equivalent to approximately X% of our 2018 total health budget per year."
- Do not estimate infrastructure costs — there is no unit cost data in the dataset and estimating it without data would be irresponsible. State this limitation clearly.

---

## Implementation Plan

### 1. Feature Overview

Compute incremental annual workforce cost for closing nurse and doctor shortfalls, expressed in nominal SGD millions. Produce cumulative cost trajectory and expenditure comparison. Write full cost timeseries and milestone summary CSVs. Primary user: **MOH Director of Finance**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-003-healthcare-capacity/src/cost_estimator.py
  - compute_annual_workforce_cost(gap_df, constants) -> pl.DataFrame
  - compute_cumulative_cost(cost_df) -> pl.DataFrame
  - compare_to_expenditure_baseline(cost_df, expenditure_df) -> pl.DataFrame

[CREATE] problem-statements/ps-003-healthcare-capacity/scripts/run_cost_estimation.py
  - Orchestrates cost pipeline; writes full and milestone CSVs
```

---

### 3. Code Generation Specifications

#### 3.1 `src/cost_estimator.py`

```python
"""PS-003 workforce cost estimation.

Formula: annual_cost = hiring_target_annual * salary_monthly * 12 * overhead_multiplier
All costs in nominal SGD millions (no inflation adjustment).
SCOPE: Workforce costs only — excludes infrastructure and consumables.
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

SCOPE_BOUNDARY = "Workforce cost only — excludes infrastructure, equipment, and consumables"
MONTHS_PER_YEAR = 12
SGD_TO_MILLIONS = 1_000_000.0

SALARY_MAP_KEYS = {
    "nurses": "rn_median_wage_sgd",
    "doctors": "gp_median_wage_sgd",
}


def compute_annual_workforce_cost(
    gap_timeseries: pl.DataFrame,
    constants: dict,
    year_col: str = "year",
    profession_col: str = "profession",
    hiring_col: str = "hiring_target_annual",
    scenario_col: str = "scenario",
) -> pl.DataFrame:
    """Compute annual incremental workforce cost per profession and year.

    Args:
        gap_timeseries: Output of run_gap_analysis.py (all years, professions, scenarios)
        constants: planning_constants dict
        year_col: Year column
        profession_col: Profession column
        hiring_col: Annual hiring target column
        scenario_col: Scenario column

    Returns:
        DataFrame with: year, profession, scenario, hiring_target, median_salary_sgd,
            annual_cost_sgd_m, notes, scope_boundary
    """
    overhead = float(constants["overhead_multiplier"])
    rows: list[dict] = []

    for row in gap_timeseries.to_dicts():
        profession = row.get(profession_col, "")
        salary_key = SALARY_MAP_KEYS.get(profession)
        if salary_key is None:
            continue  # Only nurses and doctors have salary data

        salary = float(constants.get(salary_key, 0))
        hiring = max(0.0, float(row.get(hiring_col, 0) or 0))

        annual_cost = hiring * salary * MONTHS_PER_YEAR * overhead
        annual_cost_m = round(annual_cost / SGD_TO_MILLIONS, 2)

        rows.append({
            year_col: row[year_col],
            profession_col: profession,
            scenario_col: row.get(scenario_col, "cagr_historical"),
            "hiring_target": round(hiring),
            "median_salary_sgd": int(salary),
            "annual_cost_sgd_m": annual_cost_m,
            "notes": "Nominal SGD — not inflation-adjusted",
            "scope_boundary": SCOPE_BOUNDARY,
        })

    df = pl.DataFrame(rows)
    logger.info(f"Workforce cost computed: {len(df)} rows")
    return df


def compute_cumulative_cost(
    cost_df: pl.DataFrame,
    cost_col: str = "annual_cost_sgd_m",
    year_col: str = "year",
    profession_col: str = "profession",
    scenario_col: str = "scenario",
) -> pl.DataFrame:
    """Add running cumulative cost per profession and scenario.

    Args:
        cost_df: Output of compute_annual_workforce_cost
        cost_col: Annual cost column
        year_col: Year column
        profession_col: Profession column
        scenario_col: Scenario column

    Returns:
        DataFrame with added cumulative_cost_sgd_m column
    """
    return cost_df.sort([profession_col, scenario_col, year_col]).with_columns(
        pl.col(cost_col).cum_sum().over([profession_col, scenario_col]).alias("cumulative_cost_sgd_m")
    )


def compare_to_expenditure_baseline(
    cost_df: pl.DataFrame,
    expenditure_df: pl.DataFrame,
    reference_year: int = 2018,
    cost_year: int = 2030,
    cost_col: str = "annual_cost_sgd_m",
    year_col: str = "year",
    exp_value_col: str = "expenditure",
) -> pl.DataFrame:
    """Compute incremental cost as percentage of 2018 government health expenditure.

    Args:
        cost_df: Workforce cost DataFrame
        expenditure_df: PS-001 expenditure data with year and expenditure columns
        reference_year: Base expenditure year (default 2018)
        cost_year: Year to extract cost from (default 2030)
        cost_col: Cost column
        year_col: Year column in both DataFrames
        exp_value_col: Expenditure value column in expenditure_df

    Returns:
        Summary DataFrame with cost comparison ratios
    """
    # Get 2018 total govt health expenditure
    exp_row = expenditure_df.filter(pl.col(year_col).cast(pl.Int32) == reference_year)
    if len(exp_row) == 0:
        logger.warning(f"No expenditure data for {reference_year}; skipping comparison")
        return pl.DataFrame()

    total_exp_sgd_m = float(exp_row[exp_value_col][0])
    if total_exp_sgd_m < 1000:  # likely in millions already
        pass
    else:
        total_exp_sgd_m = total_exp_sgd_m / SGD_TO_MILLIONS

    rows: list[dict] = []
    for profession in ["nurses", "doctors"]:
        cost_row = cost_df.filter(
            (pl.col(year_col) == cost_year) & (pl.col("profession") == profession)
        )
        if len(cost_row) == 0:
            continue
        annual_m = float(cost_row[cost_col][0])
        pct = round(annual_m / total_exp_sgd_m * 100, 2) if total_exp_sgd_m > 0 else None
        rows.append({
            "profession": profession,
            "annual_cost_sgd_m": annual_m,
            "reference_expenditure_year": reference_year,
            "total_health_exp_sgd_m": total_exp_sgd_m,
            "cost_as_pct_of_expenditure": pct,
        })
        logger.info(
            f"Cost [{profession}] at {cost_year}: SGD {annual_m:.1f}M "
            f"({pct}% of {reference_year} health expenditure)"
        )

    return pl.DataFrame(rows)
```

#### 3.2 `scripts/run_cost_estimation.py`

```python
"""PS-003 Story 06 — Workforce Cost Estimation.

Run: python problem-statements/ps-003-healthcare-capacity/scripts/run_cost_estimation.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_003_healthcare_capacity.src.planning_loader import load_planning_constants
from problem_statements.ps_003_healthcare_capacity.src.cost_estimator import (
    compare_to_expenditure_baseline,
    compute_annual_workforce_cost,
    compute_cumulative_cost,
)

PS001_DIR = PROJECT_ROOT / "problem-statements" / "ps-001-healthcare-system-baseline"
PS_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PS_DIR / "results" / "tables"
EXPORTS_DIR = PS_DIR / "results" / "exports"
LOG_DIR = PS_DIR / "logs" / "etl"
CONFIG_PATH = PROJECT_ROOT / "shared" / "config" / "base.yml"

for d in (RESULTS_DIR, EXPORTS_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

logger.add(str(LOG_DIR / "ps003_cost_estimation.log"), level="INFO", rotation="10 MB")

MILESTONE_YEARS = [2025, 2030, 2035]


def main() -> None:
    logger.info("=== PS-003 Story 06: Workforce Cost Estimation ===")

    constants = load_planning_constants(CONFIG_PATH)
    gap_ts = pl.read_csv(str(RESULTS_DIR / "ps003_workforce_gap_timeseries.csv"))

    # Annual costs
    cost_df = compute_annual_workforce_cost(gap_ts, constants)
    cost_df = compute_cumulative_cost(cost_df)
    cost_df.write_csv(str(RESULTS_DIR / "ps003_workforce_cost.csv"))
    logger.info(f"Workforce cost saved: {RESULTS_DIR / 'ps003_workforce_cost.csv'}")

    # Milestone summary
    milestone_df = cost_df.filter(pl.col("year").cast(pl.Int32).is_in(MILESTONE_YEARS))
    milestone_df.write_csv(str(EXPORTS_DIR / "ps003_cost_summary.csv"))
    logger.info(f"Cost milestone summary: {EXPORTS_DIR / 'ps003_cost_summary.csv'}")

    # Expenditure comparison
    exp_path = PS001_DIR / "results" / "exports" / "expenditure_baseline.csv"
    if exp_path.exists():
        exp_df = pl.read_csv(str(exp_path))
        exp_candidates = [c for c in exp_df.columns if "expend" in c.lower() or "spend" in c.lower()]
        if exp_candidates:
            comparison = compare_to_expenditure_baseline(
                cost_df, exp_df, exp_value_col=exp_candidates[0]
            )
            if len(comparison) > 0:
                comparison.write_csv(str(EXPORTS_DIR / "ps003_cost_vs_expenditure.csv"))
    else:
        logger.warning(f"Expenditure baseline not found: {exp_path} — skipping comparison")

    # Log key values
    for profession in ["nurses", "doctors"]:
        for year in [2030, 2035]:
            row = cost_df.filter(
                (pl.col("year").cast(pl.Int32) == year) & (pl.col("profession") == profession)
            )
            if len(row) > 0:
                logger.info(
                    f"[{profession}] {year}: "
                    f"annual={row['annual_cost_sgd_m'][0]:.1f}M SGD, "
                    f"cumulative={row['cumulative_cost_sgd_m'][0]:.1f}M SGD"
                )


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_cost_estimator.py
import polars as pl
import pytest


def test_compute_annual_workforce_cost_formula():
    from problem_statements.ps_003_healthcare_capacity.src.cost_estimator import compute_annual_workforce_cost
    gap = pl.DataFrame({
        "year": [2025], "profession": ["nurses"], "scenario": ["cagr_historical"],
        "hiring_target_annual": [100.0],
    })
    constants = {
        "rn_median_wage_sgd": 4200,
        "gp_median_wage_sgd": 8500,
        "overhead_multiplier": 1.35,
    }
    result = compute_annual_workforce_cost(gap, constants)
    expected = 100 * 4200 * 12 * 1.35 / 1_000_000
    assert result["annual_cost_sgd_m"][0] == pytest.approx(expected, abs=0.01)


def test_compute_cumulative_cost_monotonic():
    from problem_statements.ps_003_healthcare_capacity.src.cost_estimator import compute_cumulative_cost
    df = pl.DataFrame({
        "year": [2025, 2026, 2027],
        "profession": ["nurses"] * 3,
        "scenario": ["cagr_historical"] * 3,
        "annual_cost_sgd_m": [10.0, 12.0, 15.0],
    })
    result = compute_cumulative_cost(df)
    assert result["cumulative_cost_sgd_m"].to_list() == pytest.approx([10.0, 22.0, 37.0])


def test_scope_boundary_in_output():
    from problem_statements.ps_003_healthcare_capacity.src.cost_estimator import (
        compute_annual_workforce_cost, SCOPE_BOUNDARY,
    )
    gap = pl.DataFrame({
        "year": [2025], "profession": ["nurses"], "scenario": ["cagr_historical"],
        "hiring_target_annual": [50.0],
    })
    constants = {"rn_median_wage_sgd": 4200, "gp_median_wage_sgd": 8500, "overhead_multiplier": 1.35}
    result = compute_annual_workforce_cost(gap, constants)
    assert result["scope_boundary"][0] == SCOPE_BOUNDARY
```

---

### 5. Implementation Steps

- [ ] Create `src/cost_estimator.py`
- [ ] Create `scripts/run_cost_estimation.py`
- [ ] Run: `python scripts/run_cost_estimation.py`
- [ ] Verify `ps003_workforce_cost.csv` exists with `annual_cost_sgd_m` and `cumulative_cost_sgd_m` columns
- [ ] Verify `ps003_cost_summary.csv` has 2030 and 2035 rows
- [ ] Check log for 2030 and 2035 cumulative cost values per profession
- [ ] Verify `scope_boundary` column present with correct text
- [ ] Run unit tests: `pytest tests/unit/test_cost_estimator.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-003-story-06-cost-estimation
git commit -m "feat(ps-003): add cost_estimator module with nominal SGD cost formula"
git commit -m "feat(ps-003): add run_cost_estimation script with milestone summary and expenditure comparison"
```
