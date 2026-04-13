# User Story: 5 — Engineer Baseline Metrics & System Ratios

**As a** MOH policy analyst,  
**I want** to construct derived metrics including per-capita workforce density, per-capita bed density, growth indices, and staff-to-bed balance ratios,  
**so that** I can compare Singapore's system configuration against WHO benchmarks and identify structural imbalances.

## 1. 🎯 Acceptance Criteria

- Per-capita workforce density computed for each profession: `headcount / resident_population * 10,000` — for each year and sector
- Per-capita bed density computed by facility type: `beds / resident_population * 10,000` — for each year
- Growth index computed for each metric: `value / value_base_year * 100` — base year = 2009 (earliest year where all tables overlap)
- Staff-to-bed ratio (balance metric) computed: `nurses_public / total_public_beds`, `doctors_public / total_public_beds`
- All derived metrics saved to `results/tables/baseline_metrics.csv` with columns: year, metric_name, value, metric_type
- A companion `results/tables/benchmark_comparison.csv` table comparing 2018 Singapore actuals vs WHO SEARO benchmarks

## 2. 🔒 Technical Constraints

- All derivations in Polars — use `.with_columns()` chaining; do not collect intermediate DataFrames mid-pipeline
- Resident population sourced from Story 01's `shared/data/2_external/population/` — must use the same denominator series throughout
- WHO SEARO benchmarks hard-coded as a small reference dictionary: `{nurses_per_10k: 22.8, doctors_per_10k: 2.3, beds_per_10k: 21}` — cite WHO GHO 2020 in code comments
- Growth index base year is 2009; if any table starts after 2009, use table's earliest available year and document this
- Staff-to-bed ratios use public sector only (direct government control); private sector provided for reference only

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — WHO benchmark values, interpretation guidelines
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — nurse:bed ratio benchmark (1 nurse per 4 beds = 0.25 ratio inverted = 4 beds per nurse)

## 4. 📦 Dependencies

- `polars` — all computations
- Cleaned parquets from Story 02: `workforce_*_clean.parquet`, `facilities_clean.parquet`
- External: `shared/data/2_external/population/singapore_resident_population.csv`

## 5. ✅ Implementation Tasks

**Per-Capita Density**
- ⬜ Load population series; join with workforce tables on `year`; compute `workers_per_10k` per profession per sector
- ⬜ Load population series; join with beds table on `year`; compute `beds_per_10k` per facility type
- ⬜ Stack all density metrics into long format: columns `year, metric_name, sector, value`

**Growth Index**
- ⬜ For each metric series, compute growth index with 2009 = 100 using `.with_columns(value / first_value * 100)`
- ⬜ Join growth index to long-format density table; add column `growth_index`

**Balance Ratios**
- ⬜ Compute `nurses_per_bed_public = nurses_public_headcount / total_public_beds` for each year (2009–2018)
- ⬜ Compute `doctors_per_bed_public = doctors_public_headcount / total_public_beds` for each year
- ⬜ Append balance ratios to metrics table with `metric_type = "balance_ratio"`

**Benchmark Comparison**
- ⬜ Create `benchmark_comparison.csv` with columns: `metric`, `singapore_2018`, `who_searo_benchmark`, `gap_pct`, `above_below_benchmark`
- ⬜ Compute `gap_pct = (singapore_2018 - benchmark) / benchmark * 100`; flag direction
- ⬜ Save to `results/tables/benchmark_comparison.csv`

**Final Output**
- ⬜ Save complete metrics to `results/tables/baseline_metrics.csv`
- ⬜ Log row counts and null check for each derived column

## 6. Notes

- The benchmark comparison table is the key deliverable for this story — it directly feeds the System Balance Scorecard in Story 06 and the executive dashboard in PS-003.
- Growth indices are used in Story 07's visualisation to overlay workforce, beds, and admissions on a common scale.
- Do not model private sector in balance ratios — planning authority covers public system only.

---

## Implementation Plan

### 1. Feature Overview

Compute per-capita workforce and bed density, growth indices (base year 2009=100), staff-to-bed balance ratios, and a benchmark comparison table. Primary user: **MOH Policy Analyst**. Outputs feed directly into PS-003.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-001-healthcare-system-baseline/src/metrics_engine.py
  - Function: compute_density_per_10k(df, value_col, population_df, group_cols) -> pl.DataFrame
  - Function: compute_growth_index(df, value_col, group_cols, base_year) -> pl.DataFrame
  - Function: compute_balance_ratios(nurses_df, doctors_df, beds_df) -> pl.DataFrame
  - Function: build_benchmark_comparison(metrics_df, benchmarks) -> pl.DataFrame

[CREATE] problem-statements/ps-001-healthcare-system-baseline/scripts/run_feature_engineering.py
[CREATE] problem-statements/ps-001-healthcare-system-baseline/tests/unit/test_metrics_engine.py
```

---

### 3. Code Generation Specifications

#### 3.1 `src/metrics_engine.py`

```python
"""Baseline metrics feature engineering for PS-001.

Computes per-capita density, growth indices, and benchmark comparisons.
WHO SEARO benchmarks (2020): nurses/10k=22.8, doctors/10k=2.3, beds/10k=21.
"""

from typing import Any

import polars as pl
from loguru import logger

# WHO SEARO benchmarks — WHO GHO 2020
WHO_SEARO_BENCHMARKS: dict[str, float] = {
    "nurses_per_10k": 22.8,
    "doctors_per_10k": 2.3,
    "beds_per_10k": 21.0,
}


def compute_density_per_10k(
    df: pl.DataFrame,
    value_col: str,
    population_df: pl.DataFrame,
    group_cols: list[str],
    year_col: str = "year",
    metric_name: str | None = None,
) -> pl.DataFrame:
    """Compute per-10,000 population density for a workforce or facility metric.

    Args:
        df: DataFrame with value_col and year_col
        value_col: Column to normalise by population
        population_df: Contains year_col and 'population' column
        group_cols: Additional grouping columns (e.g. ["profession", "sector"])
        year_col: Year column name
        metric_name: Name for the resulting density column; defaults to
            "{value_col}_per_10k"

    Returns:
        DataFrame with additional column: {metric_name}_per_10k
    """
    output_col = metric_name or f"{value_col}_per_10k"
    joined = df.join(
        population_df.select([year_col, "population"]),
        on=year_col,
        how="left",
    )
    result = joined.with_columns(
        (pl.col(value_col) / pl.col("population") * 10_000.0)
        .cast(pl.Float32)
        .alias(output_col)
    )
    logger.info(
        f"Density computed: {output_col} for {result[group_cols[0]].n_unique()} "
        f"unique {group_cols[0]} values"
    )
    return result


def compute_growth_index(
    df: pl.DataFrame,
    value_col: str,
    group_cols: list[str],
    base_year: int = 2009,
    year_col: str = "year",
) -> pl.DataFrame:
    """Compute growth index (base year = 100) for a metric.

    Formula: index_t = value_t / value_{base_year} * 100

    Args:
        df: Input DataFrame sorted by year within groups
        value_col: Numeric column to index
        group_cols: Grouping columns
        base_year: Reference year where index = 100
        year_col: Year column name

    Returns:
        DataFrame with additional column: {value_col}_index
    """
    base = (
        df.filter(pl.col(year_col) == base_year)
        .select([*group_cols, pl.col(value_col).alias("base_value")])
    )
    merged = df.join(base, on=group_cols, how="left")
    result = merged.with_columns(
        (pl.col(value_col) / pl.col("base_value") * 100.0)
        .cast(pl.Float32)
        .alias(f"{value_col}_index")
    ).drop("base_value")

    logger.info(f"Growth index computed for {value_col} (base year: {base_year})")
    return result


def compute_balance_ratios(
    nurses_public: pl.DataFrame,
    doctors_public: pl.DataFrame,
    beds_df: pl.DataFrame,
    year_col: str = "year",
    headcount_col: str = "headcount",
    beds_col: str = "beds",
) -> pl.DataFrame:
    """Compute nurse:bed and doctor:bed ratios for public sector.

    Args:
        nurses_public: Nurses DataFrame filtered to Public sector
        doctors_public: Doctors DataFrame filtered to Public sector
        beds_df: Inpatient beds DataFrame (total, all facility types)
        year_col: Year column name
        headcount_col: Headcount column name
        beds_col: Beds column name

    Returns:
        DataFrame with columns: year, nurse_headcount, doctor_headcount,
        total_beds, nurses_per_bed, doctors_per_bed
    """
    nurse_annual = (
        nurses_public.group_by(year_col)
        .agg(pl.col(headcount_col).sum().alias("nurse_headcount"))
    )
    doctor_annual = (
        doctors_public.group_by(year_col)
        .agg(pl.col(headcount_col).sum().alias("doctor_headcount"))
    )
    beds_annual = (
        beds_df.group_by(year_col)
        .agg(pl.col(beds_col).sum().alias("total_beds"))
    )

    result = (
        nurse_annual
        .join(doctor_annual, on=year_col, how="inner")
        .join(beds_annual, on=year_col, how="inner")
        .with_columns([
            (pl.col("nurse_headcount") / pl.col("total_beds")).alias("nurses_per_bed"),
            (pl.col("doctor_headcount") / pl.col("total_beds")).alias("doctors_per_bed"),
        ])
        .sort(year_col)
    )

    logger.info(
        f"Balance ratios computed for {len(result)} years. "
        f"Latest nurses/bed = {result['nurses_per_bed'][-1]:.3f}"
    )
    return result


def build_benchmark_comparison(
    metrics_2018: dict[str, float],
    benchmarks: dict[str, float] | None = None,
) -> pl.DataFrame:
    """Create a benchmark comparison table.

    Args:
        metrics_2018: Singapore 2018 values keyed by metric name
            e.g. {"nurses_per_10k": 18.5, "doctors_per_10k": 2.1}
        benchmarks: Reference values; defaults to WHO_SEARO_BENCHMARKS

    Returns:
        DataFrame: metric, singapore_2018, who_benchmark, gap_pct, above_below_benchmark
    """
    bmarks = benchmarks or WHO_SEARO_BENCHMARKS
    rows: list[dict[str, Any]] = []

    for metric, benchmark in bmarks.items():
        sg_value = metrics_2018.get(metric)
        if sg_value is None:
            logger.warning(f"No Singapore value for metric: {metric} — skipping")
            continue
        gap_pct = (sg_value - benchmark) / benchmark * 100.0
        rows.append({
            "metric": metric,
            "singapore_2018": round(sg_value, 3),
            "who_searo_benchmark": benchmark,
            "gap_pct": round(gap_pct, 2),
            "above_below_benchmark": "above" if gap_pct >= 0 else "below",
        })

    comparison = pl.DataFrame(rows)
    logger.info(
        f"Benchmark comparison: {len(comparison)} metrics, "
        f"{(comparison['above_below_benchmark'] == 'above').sum()} above benchmark"
    )
    return comparison
```

#### 3.2 `scripts/run_feature_engineering.py`

```python
"""PS-001 Story 05 — Baseline Metrics & System Ratios.

Run: python problem-statements/ps-001-healthcare-system-baseline/scripts/run_feature_engineering.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.metrics_engine import (
    WHO_SEARO_BENCHMARKS,
    build_benchmark_comparison,
    compute_balance_ratios,
    compute_density_per_10k,
    compute_growth_index,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
RESULTS_DIR = PS_DIR / "results" / "tables"
EXTERNAL_DIR = PROJECT_ROOT / "shared" / "data" / "2_external"
LOG_PATH = PS_DIR / "logs" / "etl" / "feature_engineering.log"

PROFESSIONS = ["doctors", "nurses", "pharmacists", "dentists", "allied_health_professionals"]
BASE_YEAR = 2009
ANALYSIS_END_YEAR = 2018


def main() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.add(str(LOG_PATH), level="INFO", rotation="10 MB")
    logger.info("=== PS-001 Story 05: Baseline Metrics & System Ratios ===")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    population = pl.read_csv(
        str(EXTERNAL_DIR / "population" / "singapore_resident_population.csv")
    )
    beds = pl.read_parquet(str(PROCESSED_DIR / "inpatient_beds_clean.parquet"))

    # 1. Per-capita density
    all_metrics: list[pl.DataFrame] = []
    for profession in PROFESSIONS:
        path = PROCESSED_DIR / f"{profession}_clean.parquet"
        if not path.exists():
            logger.warning(f"Missing: {path}")
            continue
        df = pl.read_parquet(str(path))
        density = compute_density_per_10k(
            df, "headcount", population, ["profession", "sector"],
            metric_name=f"{profession}_per_10k"
        )
        density_long = density.select([
            "year", "sector",
            pl.lit(profession).alias("metric_name"),
            pl.col(f"{profession}_per_10k").alias("value"),
        ]).with_columns(pl.lit("density_per_10k").alias("metric_type"))
        all_metrics.append(density_long)

    # Beds density
    beds_density = compute_density_per_10k(
        beds, "beds", population, ["facility_type"], metric_name="beds_per_10k"
    )
    beds_density_long = beds_density.select([
        "year",
        pl.lit("All").alias("sector"),
        pl.lit("beds").alias("metric_name"),
        pl.col("beds_per_10k").alias("value"),
    ]).with_columns(pl.lit("density_per_10k").alias("metric_type"))
    all_metrics.append(beds_density_long)

    # 2. Growth index
    indexed_metrics: list[pl.DataFrame] = []
    for frame in all_metrics:
        indexed = compute_growth_index(frame, "value", ["metric_name", "sector"], BASE_YEAR)
        indexed_metrics.append(indexed.rename({"value_index": "growth_index"}))

    baseline_metrics = pl.concat(indexed_metrics)
    baseline_metrics.write_csv(str(RESULTS_DIR / "baseline_metrics.csv"))
    logger.info(f"Baseline metrics: {baseline_metrics.shape}")

    # 3. Balance ratios
    nurses = pl.read_parquet(str(PROCESSED_DIR / "nurses_clean.parquet")).filter(
        pl.col("sector") == "Public"
    )
    doctors = pl.read_parquet(str(PROCESSED_DIR / "doctors_clean.parquet")).filter(
        pl.col("sector") == "Public"
    )
    ratios = compute_balance_ratios(nurses, doctors, beds)
    ratios_long = pl.concat([
        ratios.select(["year", pl.col("nurses_per_bed").alias("value")])
              .with_columns([pl.lit("nurses_per_bed_public").alias("metric_name"),
                             pl.lit("Public").alias("sector"),
                             pl.lit("balance_ratio").alias("metric_type")]),
        ratios.select(["year", pl.col("doctors_per_bed").alias("value")])
              .with_columns([pl.lit("doctors_per_bed_public").alias("metric_name"),
                             pl.lit("Public").alias("sector"),
                             pl.lit("balance_ratio").alias("metric_type")]),
    ])
    full_metrics = pl.concat([baseline_metrics, ratios_long])
    full_metrics.write_csv(str(RESULTS_DIR / "baseline_metrics.csv"))

    # 4. Benchmark comparison
    sg_2018 = full_metrics.filter(
        (pl.col("year") == ANALYSIS_END_YEAR) & (pl.col("metric_type") == "density_per_10k")
    )
    sg_values = {
        row["metric_name"].replace("_per_10k", "") + "_per_10k": row["value"]
        for row in sg_2018.to_dicts()
        if row["metric_name"].replace("_per_10k", "") + "_per_10k" in WHO_SEARO_BENCHMARKS
    }
    comparison = build_benchmark_comparison(sg_values)
    comparison.write_csv(str(RESULTS_DIR / "benchmark_comparison.csv"))
    logger.info(f"Benchmark comparison: {RESULTS_DIR / 'benchmark_comparison.csv'}")

    logger.info("=== Feature engineering complete ===")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_metrics_engine.py

import sys
from pathlib import Path
import polars as pl
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.metrics_engine import (
    build_benchmark_comparison,
    compute_balance_ratios,
    compute_density_per_10k,
    compute_growth_index,
)


@pytest.fixture
def workforce_df() -> pl.DataFrame:
    return pl.DataFrame({
        "year": [2009, 2010, 2011],
        "headcount": [10_000, 10_500, 11_000],
        "profession": ["nurses"] * 3,
        "sector": ["Public"] * 3,
    })


@pytest.fixture
def population_df() -> pl.DataFrame:
    return pl.DataFrame({
        "year": [2009, 2010, 2011],
        "population": [5_000_000, 5_100_000, 5_200_000],
    })


def test_density_per_10k(workforce_df, population_df) -> None:
    result = compute_density_per_10k(
        workforce_df, "headcount", population_df, ["profession", "sector"]
    )
    # 10000 / 5000000 * 10000 = 20.0
    assert abs(result["headcount_per_10k"][0] - 20.0) < 0.1


def test_growth_index_base_year_equals_100(workforce_df, population_df) -> None:
    result = compute_growth_index(workforce_df, "headcount", ["profession", "sector"], 2009)
    base_row = result.filter(pl.col("year") == 2009)
    assert abs(base_row["headcount_index"][0] - 100.0) < 0.01


def test_benchmark_comparison_gap_pct() -> None:
    metrics = {"nurses_per_10k": 22.8, "doctors_per_10k": 2.3, "beds_per_10k": 21.0}
    result = build_benchmark_comparison(metrics)
    assert len(result) == 3
    # All equal to benchmark → gap_pct = 0
    for row in result.to_dicts():
        assert abs(row["gap_pct"]) < 0.01


def test_benchmark_below() -> None:
    metrics = {"nurses_per_10k": 15.0}  # below 22.8
    result = build_benchmark_comparison(metrics)
    assert result["above_below_benchmark"][0] == "below"
    assert result["gap_pct"][0] < 0
```

---

### 5. Implementation Steps

- [ ] Create `src/metrics_engine.py`
- [ ] Create `scripts/run_feature_engineering.py`
- [ ] Run `pytest tests/unit/test_metrics_engine.py -v` — all 4 tests must pass
- [ ] Run `python scripts/run_feature_engineering.py`
- [ ] Verify `baseline_metrics.csv` contains columns: year, sector, metric_name, value, metric_type, growth_index
- [ ] Verify `benchmark_comparison.csv` contains 3 rows (nurses, doctors, beds)
- [ ] Check benchmark comparison: if Singapore nurses/10k < 22.8, direction should be "below"

---

### 6. Version Control

```bash
git checkout -b feat/ps-001-story-05-feature-engineering
git commit -m "feat(ps-001): add metrics engine with density, growth index, and balance ratios"
git commit -m "feat(ps-001): add run_feature_engineering orchestration script"
git commit -m "test(ps-001): add metrics engine unit tests"
```
