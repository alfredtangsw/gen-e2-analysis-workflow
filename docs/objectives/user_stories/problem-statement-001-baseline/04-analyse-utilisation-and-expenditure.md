# User Story: 4 — Utilisation & Expenditure Trend Analysis

**As a** MOH healthcare financing analyst,  
**I want** to analyse historical hospital admission rates by age group and sex alongside government expenditure trends,  
**so that** I can identify which demographic groups are driving utilisation growth and how expenditure has tracked against service demand.

## 1. 🎯 Acceptance Criteria

- Admission rates analysed by age group and sex for 2006–2020 — YoY trends computed for each cell (age group × sex × year)
- Age groups ranked by admission rate level and growth rate — the top 3 highest-rate and fastest-growing groups identified
- Admissions-per-bed proxy ratio computed for 2009–2018 (overlapping years where both tables available): `total_estimated_admissions / total_beds`
- Government expenditure per estimated-admission proxy computed for 2006–2018: `total_govt_expenditure_sgd / estimated_total_admissions`
- LTC admissions plotted as a time series with observation-only note (no statistical modelling)
- All trend outputs saved to `results/tables/utilisation_baseline.csv` and `results/tables/expenditure_baseline.csv`
- Charts saved to `reports/figures/` (admission rate heatmap by age/sex, expenditure trend line)

## 2. 🔒 Technical Constraints

- All computations in Polars
- `estimated_total_admissions` = national admission rate × Singapore resident population ÷ rate_base (1,000 or 10,000) — must use confirmed denominator from Story 02
- Expenditure trends expressed in constant SGD where possible (note: raw data is nominal; deflation requires CPI data which is not in the dataset — report nominal and flag this limitation)
- LTC section must include explicit note: "sparse data (~25 records); descriptive observation only"
- Admission rate heatmap: use Plotly `px.imshow` with year on x-axis, age group on y-axis

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — benchmark admission rates for context
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — ALOS and bed occupancy context for interpreting admission-per-bed proxy

## 4. 📦 Dependencies

- `polars` — rate calculations and joins
- `plotly` — heatmap and trend charts
- Story 02 outputs: `hospital_admissions_clean.parquet`, `facilities_clean.parquet`, `expenditure_clean.parquet`
- Story 01 outputs: `shared/data/2_external/population/` — resident population by year

## 5. ✅ Implementation Tasks

**Utilisation Analysis**
- ⬜ Load `hospital_admissions_clean.parquet`; compute YoY change in rate per age group × sex
- ⬜ Rank age groups by rate level (latest year) and by growth rate (2006–2020 CAGR)
- ⬜ Compute `estimated_total_admissions` = rate × population / rate_base, aggregated annually
- ⬜ Join with beds table on year; compute `admissions_per_bed` proxy
- ⬜ Write to `results/tables/utilisation_baseline.csv`

**Expenditure Analysis**
- ⬜ Load `expenditure_clean.parquet`; compute YoY growth in total govt health expenditure
- ⬜ Compute `expenditure_per_admission_proxy` = total spend / estimated admissions
- ⬜ Write to `results/tables/expenditure_baseline.csv`
- ⬜ Add explicit commentary field: `expenditure_category: "Total government only — no category breakdown available"`

**LTC Analysis**
- ⬜ Load `ltc_admissions_clean.parquet`; plot time series
- ⬜ Add annotation on chart: "Sparse data — descriptive observation only"

**Visualisation**
- ⬜ Heatmap: admission rates by age group and year → `reports/figures/admission_rate_heatmap.png`
- ⬜ Line chart: govt expenditure and expenditure-per-admission proxy → `reports/figures/expenditure_trend.png`
- ⬜ Line chart: LTC admissions → `reports/figures/ltc_trend.png`

## 6. Notes

- The 65+ age groups (65–74, 75–84, 85+) are expected to show the highest admission rates. These groups will be the primary demand driver in PS-002's demographic projection.
- The admissions-per-bed proxy is not an occupancy rate — it is a volume-to-capacity ratio that gives a directional signal only. Label clearly in outputs.
- Nominal expenditure trends will slightly overstate real growth due to inflation. Note this limitation prominently.

---

## Implementation Plan

### 1. Feature Overview

Compute age-stratified hospital utilisation trends, the admissions-per-bed proxy, the expenditure-per-admission proxy, and produce a heatmap and expenditure chart. Primary user: **MOH Healthcare Financing Analyst**.

---

### 2. Affected Files

```
[MODIFY] problem-statements/ps-001-healthcare-system-baseline/src/trend_analysis.py
  - Add: compute_estimated_admissions(admissions_df, population_df, rate_base) -> pl.DataFrame
  - Add: compute_admissions_per_bed(admissions_df, beds_df) -> pl.DataFrame

[MODIFY] problem-statements/ps-001-healthcare-system-baseline/src/visualization.py
  - Add: plot_admission_rate_heatmap(df) -> go.Figure
  - Add: plot_expenditure_trend(df) -> go.Figure

[CREATE] problem-statements/ps-001-healthcare-system-baseline/scripts/run_eda_utilisation.py
```

---

### 3. Code Generation Specifications

#### 3.1 Add to `src/trend_analysis.py`

```python
def compute_estimated_admissions(
    admissions_df: pl.DataFrame,
    population_df: pl.DataFrame,
    rate_col: str = "rate",
    rate_base: int = 1000,
    year_col: str = "year",
) -> pl.DataFrame:
    """Estimate total annual admissions from rate × population / rate_base.

    Args:
        admissions_df: Contains rate_col and year_col (aggregated across age/sex)
        population_df: Contains year_col and 'population' column
        rate_col: Name of the admission rate column
        rate_base: Denominator used in rate calculation (1000 or 10000)
        year_col: Year column name

    Returns:
        DataFrame with columns: year, estimated_admissions
    """
    if rate_base not in (1000, 10000):
        raise ValueError(f"rate_base must be 1000 or 10000, got {rate_base}")

    # Aggregate to annual total rate (sum across age/sex)
    annual_rate = (
        admissions_df
        .group_by(year_col)
        .agg(pl.col(rate_col).sum().alias("total_rate"))
    )

    joined = annual_rate.join(
        population_df.select([year_col, "population"]),
        on=year_col,
        how="inner",
    )

    result = joined.with_columns(
        (pl.col("total_rate") * pl.col("population") / rate_base)
        .cast(pl.Float64)
        .alias("estimated_admissions")
    )
    logger.info(
        f"Estimated admissions computed for {len(result)} years "
        f"(rate_base={rate_base})"
    )
    return result.select([year_col, "estimated_admissions"])


def compute_admissions_per_bed(
    estimated_admissions_df: pl.DataFrame,
    beds_df: pl.DataFrame,
    year_col: str = "year",
) -> pl.DataFrame:
    """Compute admissions-per-bed proxy for overlapping years.

    Note: This is a volume-to-capacity ratio, NOT an occupancy rate.

    Args:
        estimated_admissions_df: Output of compute_estimated_admissions()
        beds_df: Cleaned beds DataFrame with 'beds' column (total public beds)
        year_col: Year column name

    Returns:
        DataFrame with year, estimated_admissions, total_beds, admissions_per_bed
    """
    total_beds = (
        beds_df
        .group_by(year_col)
        .agg(pl.col("beds").sum().alias("total_beds"))
    )

    joined = estimated_admissions_df.join(total_beds, on=year_col, how="inner")
    result = joined.with_columns(
        (pl.col("estimated_admissions") / pl.col("total_beds"))
        .alias("admissions_per_bed")
    ).sort(year_col)

    logger.info(f"Admissions-per-bed proxy computed for {len(result)} years")
    return result
```

#### 3.2 Add to `src/visualization.py`

```python
def plot_admission_rate_heatmap(
    df: pl.DataFrame,
    age_col: str = "age_group",
    year_col: str = "year",
    rate_col: str = "rate",
) -> go.Figure:
    """Plotly heatmap: admission rates by age group and year.

    Args:
        df: Admission rate DataFrame with age_group, year, rate columns
        age_col: Column for y-axis (row labels)
        year_col: Column for x-axis (column labels)
        rate_col: Numeric column for cell colour intensity

    Returns:
        Plotly Figure (imshow heatmap)
    """
    import plotly.express as px

    # Pivot: age_group as rows, year as columns
    pivot = (
        df.filter(pl.col("sex") == "Total") if "sex" in df.columns else df
    )
    pivot_pd = (
        pivot.select([age_col, year_col, rate_col])
        .to_pandas()
        .pivot(index=age_col, columns=year_col, values=rate_col)
    )

    fig = px.imshow(
        pivot_pd,
        labels={"x": "Year", "y": "Age Group", "color": "Rate per 1,000"},
        title="[DRAFT] Hospital Admission Rates by Age Group | MOH-SG",
        color_continuous_scale="Blues",
        template=CHART_TEMPLATE,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
    )
    return fig


def plot_expenditure_trend(
    expenditure_df: pl.DataFrame,
    admissions_df: pl.DataFrame | None = None,
    year_col: str = "year",
    exp_col: str = "expenditure",
) -> go.Figure:
    """Line chart: government expenditure with optional expenditure-per-admission overlay.

    Args:
        expenditure_df: Contains year and expenditure columns
        admissions_df: Optional — if provided, compute expenditure/admission ratio
        year_col: Year column names (must match in both DataFrames)
        exp_col: Expenditure column name

    Returns:
        Plotly Figure with one or two traces
    """
    pdf = expenditure_df.to_pandas()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pdf[year_col], y=pdf[exp_col],
        name="Total Govt Health Expenditure (SGD)",
        mode="lines+markers",
        line={"color": "#2980B9"},
    ))

    if admissions_df is not None:
        joined = expenditure_df.join(
            admissions_df.select([year_col, "estimated_admissions"]),
            on=year_col, how="inner"
        )
        ratio_pdf = joined.with_columns(
            (pl.col(exp_col) / pl.col("estimated_admissions") * 1000)
            .alias("exp_per_1000_admissions")
        ).to_pandas()

        fig.add_trace(go.Scatter(
            x=ratio_pdf[year_col],
            y=ratio_pdf["exp_per_1000_admissions"],
            name="Expenditure per 1,000 Admissions (proxy)",
            mode="lines+markers",
            line={"color": "#E67E22", "dash": "dash"},
            yaxis="y2",
        ))
        fig.update_layout(
            yaxis2={
                "title": "Expenditure per 1,000 Admissions (SGD, proxy)",
                "overlaying": "y",
                "side": "right",
            }
        )

    fig.update_layout(
        title="[DRAFT] Government Health Expenditure Trend | MOH-SG | Nominal SGD",
        xaxis_title="Year",
        yaxis_title="Total Expenditure (SGD)",
        annotations=[{
            "text": "Note: Nominal SGD — not adjusted for inflation",
            "xref": "paper", "yref": "paper",
            "x": 0, "y": -0.15, "showarrow": False,
            "font": {"size": 11, "color": "grey"},
        }],
        template=CHART_TEMPLATE,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
    )
    return fig
```

#### 3.3 `scripts/run_eda_utilisation.py`

```python
"""PS-001 Story 04 — Utilisation & Expenditure EDA.

Run: python problem-statements/ps-001-healthcare-system-baseline/scripts/run_eda_utilisation.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.trend_analysis import (
    compute_admissions_per_bed,
    compute_estimated_admissions,
    compute_yoy_growth,
)
from problem_statements.ps_001_healthcare_system_baseline.src.visualization import (
    plot_admission_rate_heatmap,
    plot_expenditure_trend,
    save_figure,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
RESULTS_DIR = PS_DIR / "results" / "tables"
FIGURES_DIR = PS_DIR / "reports" / "figures"
EXTERNAL_DIR = PROJECT_ROOT / "shared" / "data" / "2_external"
LOG_PATH = PS_DIR / "logs" / "etl" / "eda_utilisation.log"


def main() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.add(str(LOG_PATH), level="INFO", rotation="10 MB")
    logger.info("=== PS-001 Story 04: Utilisation & Expenditure EDA ===")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Load cleaned data
    admissions = pl.read_parquet(str(PROCESSED_DIR / "hospital_admissions_clean.parquet"))
    beds = pl.read_parquet(str(PROCESSED_DIR / "inpatient_beds_clean.parquet"))
    expenditure = pl.read_parquet(str(PROCESSED_DIR / "government_health_expenditure_clean.parquet"))
    population = pl.read_csv(str(EXTERNAL_DIR / "population" / "singapore_resident_population.csv"))

    # Determine rate_base from parquet metadata column
    rate_base_val = admissions["rate_base"][0] if "rate_base" in admissions.columns else "per_1000"
    rate_base_int = 1000 if "1000" in str(rate_base_val) else 10000
    logger.info(f"Using rate_base: {rate_base_val} ({rate_base_int})")

    # Utilisation computations
    admissions_yoy = compute_yoy_growth(admissions, "rate", ["age_group", "sex"])
    estimated = compute_estimated_admissions(admissions, population, rate_base=rate_base_int)
    proxy = compute_admissions_per_bed(estimated, beds)

    # Save utilisation baseline
    utilisation_out = proxy.join(
        admissions_yoy.group_by("year").agg(pl.col("rate").mean().alias("avg_admission_rate")),
        on="year", how="left"
    )
    utilisation_out.with_columns(
        pl.lit("Volume-to-capacity ratio — NOT an occupancy rate").alias("proxy_note")
    ).write_csv(str(RESULTS_DIR / "utilisation_baseline.csv"))

    # Expenditure baseline
    exp_out = expenditure.with_columns(
        pl.lit("Total government only — no category breakdown available").alias("expenditure_category")
    )
    exp_out.write_csv(str(RESULTS_DIR / "expenditure_baseline.csv"))

    # Charts
    fig_heatmap = plot_admission_rate_heatmap(admissions)
    save_figure(fig_heatmap, FIGURES_DIR / "admission_rate_heatmap.png")

    fig_exp = plot_expenditure_trend(expenditure, estimated)
    save_figure(fig_exp, FIGURES_DIR / "expenditure_trend.png")

    # LTC (sparse — observation only)
    ltc_path = PROCESSED_DIR / "long_term_care_admissions_clean.parquet"
    if ltc_path.exists():
        ltc = pl.read_parquet(str(ltc_path))
        logger.warning(
            f"LTC table: {ltc.shape[0]} records — sparse; descriptive observation only"
        )

    logger.info("=== Utilisation EDA complete ===")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_utilisation.py

import sys
from pathlib import Path
import polars as pl
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.trend_analysis import (
    compute_estimated_admissions,
    compute_admissions_per_bed,
)


@pytest.fixture
def admissions_df() -> pl.DataFrame:
    return pl.DataFrame({
        "year": [2010, 2011],
        "rate": [100.0, 110.0],  # combined rate per 1000
    })


@pytest.fixture
def population_df() -> pl.DataFrame:
    return pl.DataFrame({
        "year": [2010, 2011],
        "population": [5_000_000, 5_100_000],
    })


@pytest.fixture
def beds_df() -> pl.DataFrame:
    return pl.DataFrame({
        "year": [2010, 2011],
        "beds": [10000, 10500],
        "facility_type": ["Acute", "Acute"],
    })


def test_estimated_admissions_calculation(
    admissions_df: pl.DataFrame, population_df: pl.DataFrame
) -> None:
    result = compute_estimated_admissions(admissions_df, population_df, rate_base=1000)
    # 100 * 5_000_000 / 1000 = 500_000
    assert abs(result["estimated_admissions"][0] - 500_000.0) < 1.0


def test_estimated_admissions_invalid_rate_base(
    admissions_df: pl.DataFrame, population_df: pl.DataFrame
) -> None:
    with pytest.raises(ValueError, match="rate_base must be"):
        compute_estimated_admissions(admissions_df, population_df, rate_base=500)


def test_admissions_per_bed(
    population_df: pl.DataFrame, admissions_df: pl.DataFrame, beds_df: pl.DataFrame
) -> None:
    estimated = compute_estimated_admissions(admissions_df, population_df, rate_base=1000)
    result = compute_admissions_per_bed(estimated, beds_df)
    # 500000 / 10000 = 50
    assert abs(result["admissions_per_bed"][0] - 50.0) < 0.1
    assert "proxy_note" not in result.columns  # proxy label is added in the script, not here
```

---

### 5. Implementation Steps

- [ ] Add `compute_estimated_admissions()` and `compute_admissions_per_bed()` to `src/trend_analysis.py`
- [ ] Add `plot_admission_rate_heatmap()` and `plot_expenditure_trend()` to `src/visualization.py`
- [ ] Create `scripts/run_eda_utilisation.py`
- [ ] Run `pytest tests/unit/test_utilisation.py -v`
- [ ] Run `python scripts/run_eda_utilisation.py`
- [ ] Verify `utilisation_baseline.csv` and `expenditure_baseline.csv` in `results/tables/`
- [ ] Confirm `admission_rate_heatmap.png` shows 65+ groups in darkest blue band

---

### 6. Version Control

```bash
git checkout -b feat/ps-001-story-04-utilisation-eda
git commit -m "feat(ps-001): add utilisation computation functions to trend_analysis"
git commit -m "feat(ps-001): add admission heatmap and expenditure chart to visualization"
git commit -m "feat(ps-001): add run_eda_utilisation orchestration script"
git commit -m "test(ps-001): add utilisation unit tests"
```
