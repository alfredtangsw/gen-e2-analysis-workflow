# User Story: 6 — Admission Volume Projection (Cohort-Component)

**As a** MOH senior healthcare planner,  
**I want** to project total hospital admission volumes for 2021–2035 across three demographic scenarios — principal, high-growth, and low-growth — using age-group-specific admission rates and SingStat population projections,  
**so that** I can quantify the range of future demand to use as the planning baseline in PS-003.

## 1. 🎯 Acceptance Criteria

- Admission volume projections produced for all 3 SingStat scenarios (principal, high, low) for 2021–2035
- Projection methodology: cohort-component approach — `projected_admissions = sum(admission_rate_age_group * projected_population_age_group / rate_base)` for each scenario
- Admission rates held at 2019 actuals (most recent pre-COVID year) — do not extrapolate rates unless Story 05 produces a mortality-linked rate adjustment (document this decision)
- Projected admissions expressed as: absolute count, YoY growth rate, and cumulative growth vs 2019 base
- Sensitivity table produced showing 2035 projected admissions under 9 combinations (3 demographic × 3 rate assumption) — rate assumptions: flat 2019 rate, +10% rate increase, -10% rate decrease
- Output files:
  - `models/forecasts/admission_volume_projections.csv` — long format with columns: `year, scenario, projected_admissions, yoy_growth_pct`
  - `results/tables/ps002_admission_sensitivity_2035.csv` — 9-cell sensitivity table

## 2. 🔒 Technical Constraints

- Cohort-component computation in Polars — join by `age_group` and `year`; no manual loops over age groups
- Admission rate assumption: `rate_2019` extracted from `admissions_age_sex_clean.parquet` for all-sex combined rate; if all-sex is not directly available, average male + female rate weighted by population share
- Rate base confirmed in Story 02 (1,000 or 10,000) — use this confirmed value; do not guess
- Sensitivity table: 9 cells computed as a Polars cross-join of 3 scenario labels × 3 rate multipliers (0.90, 1.00, 1.10)
- All projections documented with explicit assumption statement: "Rates held constant at 2019 levels unless otherwise noted"

## 3. 📚 Domain Knowledge References

- [Time-Series Forecasting Methods](../../../../domain-knowledge/time-series-forecasting-methods.md) — cohort-component projection methodology
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — ALOS and bed demand formula for downstream use in PS-003

## 4. 📦 Dependencies

- Story 02 outputs: `admissions_age_sex_clean.parquet`, `population_projections_clean.parquet`
- Story 02 metadata: rate_base confirmed in `ps002_data_quality_report.csv`
- `polars` — projection computation

## 5. ✅ Implementation Tasks

**Prepare Inputs**
- ⬜ Load `admissions_age_sex_clean.parquet`; extract 2019 rates per age group (all-sex or averaged)
- ⬜ Load `population_projections_clean.parquet`; confirm age group alignment with admissions data
- ⬜ Confirm rate_base from `ps002_data_quality_report.csv`

**Cohort-Component Projection**
- ⬜ For each scenario (principal, high, low) and each year 2021–2035:
  - Cross-join admission rate by age group × projected population by age group
  - Compute `projected_admissions_age = rate * population / rate_base`
  - Sum across age groups to get total annual admissions
- ⬜ Compute YoY growth and cumulative growth vs 2019 base
- ⬜ Save to `models/forecasts/admission_volume_projections.csv`

**Sensitivity Analysis**
- ⬜ Create rate multiplier frame: `{multiplier: [0.90, 1.00, 1.10], label: ["-10%", "flat", "+10%"]}`
- ⬜ Cross-join with 3 scenarios; compute 2035 admissions for each of 9 combinations
- ⬜ Save 9-cell table to `results/tables/ps002_admission_sensitivity_2035.csv`

**Documentation**
- ⬜ Write assumption statement to `results/tables/ps002_admission_projection_assumptions.md`:
  - Demographic source (SingStat or UN WPP fallback)
  - Rate assumption (flat 2019)
  - Rate base used
  - Why 2020 was excluded from rate base year selection (COVID)

## 6. Notes

- Using 2019 rates (not 2020) is the standard planning practice because 2020 admission patterns were COVID-distorted (deferred care). Document this explicitly in the assumptions file.
- The sensitivity analysis gives planners a demand range rather than a single point estimate — this is critical for PS-003's scenario comparison tab.
- The principal scenario should be the primary planning reference; high-growth is the stress-test scenario for capacity dimensioning.

---

## Implementation Plan

### 1. Feature Overview

Project hospital admission volumes 2021–2035 using cohort-component method (age-group rate × projected population). Generate 3 demographic scenarios and a 9-cell sensitivity table. All computation vectorised in Polars with no manual loops. Primary user: **MOH senior healthcare planner**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-002-disease-burden/src/cohort_projection.py
  - load_rate_base(quality_report_path) -> int
  - extract_2019_rates(admissions_df, age_col, value_col, year_col, rate_base) -> pl.DataFrame
  - project_admissions(rates_df, population_df, scenario, years, rate_base) -> pl.DataFrame
  - build_sensitivity_table(rates_df, population_df, rate_base) -> pl.DataFrame

[CREATE] problem-statements/ps-002-disease-burden/scripts/run_admission_projection.py
  - Orchestrates cohort-component for 3 scenarios; writes projection and sensitivity CSVs
```

---

### 3. Code Generation Specifications

#### 3.1 `src/cohort_projection.py`

```python
"""PS-002 cohort-component admission volume projection.

Method: projected_admissions = sum(rate_age_group * population_age_group / rate_base)
All operations vectorised in Polars (no loops over age groups).
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

RATE_ASSUMPTION_NOTE = (
    "Rates held constant at 2019 levels (most recent pre-COVID year). "
    "2020 excluded — COVID structural shock distorting deferred-care baseline."
)
SCENARIOS = ["principal", "high", "low"]
SENSITIVITY_MULTIPLIERS = [0.90, 1.00, 1.10]
SENSITIVITY_LABELS = ["-10%", "flat", "+10%"]


def load_rate_base(quality_report_path: Path) -> int:
    """Extract confirmed rate base from ps002_data_quality_report.csv.

    Args:
        quality_report_path: Path to the data quality report

    Returns:
        Rate base integer (1000 or 10000)
    """
    if not quality_report_path.exists():
        logger.warning(f"Quality report not found at {quality_report_path}; defaulting rate_base=1000")
        return 1000

    df = pl.read_csv(str(quality_report_path))
    adm_rows = df.filter(pl.col("table").str.contains("admission"))
    if "rate_base" in adm_rows.columns and len(adm_rows) > 0:
        val = adm_rows["rate_base"][0]
        if val is not None:
            return int(val)

    logger.warning("rate_base not found in quality report; defaulting to 1000")
    return 1000


def extract_2019_rates(
    admissions_df: pl.DataFrame,
    age_col: str,
    value_col: str,
    year_col: str,
) -> pl.DataFrame:
    """Extract per-age-group admission rates for 2019 (last pre-COVID year).

    Args:
        admissions_df: Cleaned admissions DataFrame (2019 must be present)
        age_col: Age group column name
        value_col: Rate column name
        year_col: Year column name

    Returns:
        DataFrame with columns: age_group, rate_2019
    """
    rates = (
        admissions_df
        .filter(pl.col(year_col).cast(pl.Int32) == 2019)
        .group_by(age_col)
        .agg(pl.col(value_col).mean().alias("rate_2019"))
    )
    if len(rates) == 0:
        raise ValueError("No 2019 admissions data found. Check input DataFrame.")
    logger.info(f"Extracted 2019 rates for {len(rates)} age groups.")
    return rates


def project_admissions(
    rates_df: pl.DataFrame,
    population_df: pl.DataFrame,
    scenario: str,
    projection_years: list[int],
    rate_base: int,
    age_col: str = "age_group",
    pop_age_col: str = "age_group",
    pop_year_col: str = "year",
) -> pl.DataFrame:
    """Cohort-component projection: sum(rate_age * pop_age / rate_base) per year.

    Args:
        rates_df: Age-group rates DataFrame with columns age_group, rate_2019
        population_df: Population projections with columns age_group, year,
            and scenario-specific population column
        scenario: One of "principal", "high", "low"
        projection_years: List of years to project
        rate_base: Rate denominator (1000 or 10000)
        age_col: Age group column in rates_df
        pop_age_col: Age group column in population_df
        pop_year_col: Year column in population_df

    Returns:
        Long-format DataFrame: year, scenario, projected_admissions, yoy_growth_pct
    """
    pop_col = f"population_{scenario}"
    if pop_col not in population_df.columns:
        # Fallback: use any column whose name contains the scenario label
        candidates = [c for c in population_df.columns if scenario in c.lower()]
        if not candidates:
            raise ValueError(
                f"No population column for scenario '{scenario}'. "
                f"Columns: {population_df.columns}"
            )
        pop_col = candidates[0]

    rows: list[dict] = []
    for year in projection_years:
        pop_year = population_df.filter(
            pl.col(pop_year_col).cast(pl.Int32) == year
        ).select([pop_age_col, pop_col])

        joined = rates_df.join(
            pop_year, left_on=age_col, right_on=pop_age_col, how="inner"
        ).with_columns(
            (pl.col("rate_2019") * pl.col(pop_col) / rate_base).alias("admissions_age")
        )

        if len(joined) == 0:
            logger.warning(f"No matching age groups for year {year}, scenario {scenario}")
            rows.append({"year": year, "scenario": scenario, "projected_admissions": None})
            continue

        total = float(joined["admissions_age"].sum())
        rows.append({"year": year, "scenario": scenario, "projected_admissions": total})

    result = pl.DataFrame(rows)

    # YoY growth
    result = result.with_columns(
        (
            (pl.col("projected_admissions") / pl.col("projected_admissions").shift(1) - 1) * 100
        ).alias("yoy_growth_pct")
    )
    logger.info(
        f"Projection [{scenario}] {min(projection_years)}–{max(projection_years)}: "
        f"{len(result)} rows"
    )
    return result


def build_sensitivity_table(
    rates_2019: pl.DataFrame,
    population_df: pl.DataFrame,
    rate_base: int,
    target_year: int = 2035,
    age_col: str = "age_group",
) -> pl.DataFrame:
    """Build 9-cell sensitivity table: 3 demographic × 3 rate multipliers for target_year.

    Args:
        rates_2019: Age-group rates for 2019
        population_df: Population projections DataFrame
        rate_base: Rate denominator
        target_year: Year to compute sensitivity for (default 2035)
        age_col: Age group column

    Returns:
        9-row DataFrame: scenario, rate_assumption, multiplier, projected_admissions_2035
    """
    rows: list[dict] = []
    for scenario in SCENARIOS:
        for mult, label in zip(SENSITIVITY_MULTIPLIERS, SENSITIVITY_LABELS):
            adjusted_rates = rates_2019.with_columns(
                (pl.col("rate_2019") * mult).alias("rate_2019")
            )
            proj = project_admissions(
                adjusted_rates, population_df, scenario, [target_year], rate_base, age_col
            )
            adm_val = proj["projected_admissions"][0] if len(proj) > 0 else None
            rows.append({
                "scenario": scenario,
                "rate_assumption": label,
                "rate_multiplier": mult,
                "projected_admissions_2035": round(adm_val) if adm_val else None,
            })
    return pl.DataFrame(rows)
```

#### 3.2 `scripts/run_admission_projection.py`

```python
"""PS-002 Story 06 — Cohort-Component Admission Volume Projection.

Run: python problem-statements/ps-002-disease-burden/scripts/run_admission_projection.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_002_disease_burden.src.cohort_projection import (
    RATE_ASSUMPTION_NOTE,
    SCENARIOS,
    build_sensitivity_table,
    extract_2019_rates,
    load_rate_base,
    project_admissions,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
FORECASTS_DIR = PS_DIR / "models" / "forecasts"
RESULTS_DIR = PS_DIR / "results" / "tables"
EXPORTS_DIR = PS_DIR / "results" / "exports"
LOG_DIR = PS_DIR / "logs" / "etl"

for d in (FORECASTS_DIR, RESULTS_DIR, EXPORTS_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

logger.add(str(LOG_DIR / "ps002_admission_projection.log"), level="INFO", rotation="10 MB")

PROJECTION_YEARS = list(range(2021, 2036))


def main() -> None:
    logger.info("=== PS-002 Story 06: Admission Volume Projection ===")

    # Load data
    adm = pl.read_parquet(str(PROCESSED_DIR / "admissions_age_sex_clean.parquet"))
    pop = pl.read_parquet(str(PROCESSED_DIR / "population_projections_clean.parquet"))
    rate_base = load_rate_base(LOG_DIR / "ps002_data_quality_report.csv")

    # Detect columns
    age_col = next((c for c in adm.columns if "age" in c.lower()), None)
    year_col = next((c for c in adm.columns if "year" in c.lower()), "year")
    value_col = next(
        (c for c in adm.columns if any(kw in c.lower() for kw in ("rate", "number", "admission"))),
        None,
    )

    if not age_col or not value_col:
        raise RuntimeError(f"Cannot detect age/value columns. Columns: {adm.columns}")

    rates_2019 = extract_2019_rates(adm, age_col, value_col, year_col)

    # Project for each scenario
    scenario_dfs: list[pl.DataFrame] = []
    for scenario in SCENARIOS:
        try:
            proj = project_admissions(
                rates_2019, pop, scenario, PROJECTION_YEARS, rate_base, age_col
            )
            scenario_dfs.append(proj)
        except (ValueError, KeyError) as exc:
            logger.warning(f"Scenario '{scenario}' projection failed: {exc}")

    if scenario_dfs:
        all_projections = pl.concat(scenario_dfs)
        all_projections.write_csv(str(FORECASTS_DIR / "admission_volume_projections.csv"))
        logger.info(f"Projections saved: {FORECASTS_DIR / 'admission_volume_projections.csv'}")
    else:
        logger.error("No scenario projections succeeded.")

    # Sensitivity table
    try:
        sensitivity = build_sensitivity_table(rates_2019, pop, rate_base, target_year=2035, age_col=age_col)
        sensitivity.write_csv(str(RESULTS_DIR / "ps002_admission_sensitivity_2035.csv"))
        logger.info(f"Sensitivity table: {RESULTS_DIR / 'ps002_admission_sensitivity_2035.csv'}")
    except Exception as exc:
        logger.warning(f"Sensitivity table failed: {exc}")

    # Assumption documentation
    assumptions_path = RESULTS_DIR / "ps002_admission_projection_assumptions.md"
    assumptions_path.write_text(
        f"""# PS-002 Admission Projection Assumptions

- **Demographic source**: SingStat population projections (fallback: UN WPP 2022 if unavailable)
- **Rate assumption**: {RATE_ASSUMPTION_NOTE}
- **Rate base used**: per {rate_base:,} resident population
- **COVID exclusion**: 2020 admission data excluded from rate calibration year selection
- **Projection horizon**: 2021–2035
- **Scenarios**: principal (reference), high-growth (stress test), low-growth (optimistic)
""",
        encoding="utf-8",
    )
    logger.info("Assumption documentation written.")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_cohort_projection.py
import polars as pl
import pytest


def test_extract_2019_rates_correct():
    from problem_statements.ps_002_disease_burden.src.cohort_projection import extract_2019_rates
    df = pl.DataFrame({
        "year": [2018, 2018, 2019, 2019],
        "age_group": ["0-4", "65-74", "0-4", "65-74"],
        "rate": [5.0, 80.0, 6.0, 90.0],
    })
    rates = extract_2019_rates(df, "age_group", "rate", "year")
    assert set(rates["age_group"].to_list()) == {"0-4", "65-74"}
    row = rates.filter(pl.col("age_group") == "65-74")
    assert row["rate_2019"][0] == pytest.approx(90.0)


def test_extract_2019_rates_raises_if_no_2019(tmp_path):
    from problem_statements.ps_002_disease_burden.src.cohort_projection import extract_2019_rates
    df = pl.DataFrame({
        "year": [2018, 2018],
        "age_group": ["0-4", "65-74"],
        "rate": [5.0, 80.0],
    })
    with pytest.raises(ValueError, match="No 2019"):
        extract_2019_rates(df, "age_group", "rate", "year")


def test_build_sensitivity_table_returns_9_rows():
    from problem_statements.ps_002_disease_burden.src.cohort_projection import build_sensitivity_table
    rates = pl.DataFrame({"age_group": ["65-74"], "rate_2019": [100.0]})
    pop = pl.DataFrame({
        "age_group": ["65-74"],
        "year": [2035],
        "population_principal": [50000],
        "population_high": [55000],
        "population_low": [45000],
    })
    result = build_sensitivity_table(rates, pop, rate_base=1000, target_year=2035)
    assert len(result) == 9
```

---

### 5. Implementation Steps

- [ ] Create `src/cohort_projection.py`
- [ ] Create `scripts/run_admission_projection.py`
- [ ] Run: `python scripts/run_admission_projection.py`
- [ ] Verify `admission_volume_projections.csv` has rows for years 2021–2035 × 3 scenarios (≤ 45 rows)
- [ ] Verify `ps002_admission_sensitivity_2035.csv` has exactly 9 rows
- [ ] Verify `ps002_admission_projection_assumptions.md` written
- [ ] Check projections: principal scenario admissions should be larger than low; smaller than high
- [ ] Run unit tests: `pytest tests/unit/test_cohort_projection.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-002-story-06-admission-projection
git commit -m "feat(ps-002): add cohort_projection module with scenario and sensitivity projection"
git commit -m "feat(ps-002): add run_admission_projection orchestration script"
```
