# User Story: 3 — Exploratory Workforce & Facility Trend Analysis

**As a** MOH workforce planner,  
**I want** to explore historical trends in healthcare workforce headcount and facility bed capacity across all professions and facility types,  
**so that** I can understand how the system has grown and identify where growth rates have diverged.

## 1. 🎯 Acceptance Criteria

- Workforce trend analysis covers all 5 core professions: doctors, nurses, pharmacists, dentists, allied health professionals — by sector (public/private/total) and year (2009–2019 joint window)
- Facility trend analysis covers total inpatient beds by facility type and primary care access points by year (2009–2020)
- For each profession and facility type: absolute headcount/count, YoY growth rate, and compound annual growth rate (CAGR) over the full available period are computed
- Professions and facility types are ranked by total growth and CAGR — top and bottom performers identified
- All trends plotted as time-series line charts (one chart per domain: workforce, facilities, primary care)
- Charts saved to `reports/figures/` as PNG at 150 dpi minimum
- Summary statistics table saved to `results/tables/workforce_trend_summary.csv` and `results/tables/facility_trend_summary.csv`

## 2. 🔒 Technical Constraints

- All calculations in Polars using method chaining — no loops over DataFrames
- CAGR formula: `((value_end / value_start) ^ (1 / n_years)) - 1`
- Charts built with Plotly (not matplotlib) — consistent with dashboard tech in PS-003
- Use `pl.Categorical` for profession and sector columns
- Analyse overlapping year range across tables: **2009–2018** (intersection of all major tables)

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — CAGR interpretation, benchmark densities
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — benchmark bed-to-population ratios for context

## 4. 📦 Dependencies

- `polars` — trend calculations
- `plotly` — chart generation
- Story 02 outputs: cleaned parquets in `data/4_processed/`

## 5. ✅ Implementation Tasks

**Workforce EDA**
- ⬜ Join all 5 profession tables on `year` and `sector`; compute total across all professions
- ⬜ Compute YoY growth rate per profession-sector pair
- ⬜ Compute CAGR 2009–2018 per profession-sector pair
- ⬜ Rank professions by CAGR; flag fastest and slowest growing
- ⬜ Write summary to `results/tables/workforce_trend_summary.csv`

**Facility EDA**
- ⬜ Load inpatient beds table; compute YoY change and CAGR by facility type
- ⬜ Load primary care table; compute YoY change in clinic counts
- ⬜ Write summary to `results/tables/facility_trend_summary.csv`

**Visualisation**
- ⬜ Create line chart: workforce headcount by profession and sector over time → `reports/figures/workforce_trends.png`
- ⬜ Create line chart: inpatient beds by facility type over time → `reports/figures/facility_trends.png`
- ⬜ Create bar chart: CAGR comparison across professions → `reports/figures/workforce_cagr.png`

## 6. Notes

- Public sector workforce is the primary planning concern; private sector provides context for overall system supply.
- Nurses are the single largest workforce category and the primary input to the bed-ratio calculations in PS-003. Ensure nurse trend is highlighted prominently.
- Chart Y-axes should include zero to avoid misleading visual compression of small changes.

---

## Implementation Plan

### 1. Feature Overview

Compute YoY growth rates and CAGR for all 5 workforce professions and inpatient bed types over the 2009–2018 joint window. Produce three Plotly charts and two summary CSV tables. Primary user: **MOH Workforce Planner**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-001-healthcare-system-baseline/src/trend_analysis.py
  - Function: compute_cagr(df, value_col, group_cols, year_col) -> pl.DataFrame
  - Function: compute_yoy_growth(df, value_col, group_cols, year_col) -> pl.DataFrame
  - Function: rank_by_cagr(df, group_col) -> pl.DataFrame

[CREATE] problem-statements/ps-001-healthcare-system-baseline/src/visualization.py
  - Function: plot_workforce_trends(df) -> go.Figure
  - Function: plot_facility_trends(df) -> go.Figure
  - Function: plot_cagr_comparison(df) -> go.Figure
  - Function: save_figure(fig, path) -> None

[CREATE] problem-statements/ps-001-healthcare-system-baseline/scripts/run_eda_workforce.py
  - Orchestrates trend computation and chart generation

[CREATE] problem-statements/ps-001-healthcare-system-baseline/tests/unit/test_trend_analysis.py
```

---

### 3. Code Generation Specifications

#### 3.1 `problem-statements/ps-001-healthcare-system-baseline/src/trend_analysis.py`

```python
"""Workforce and facility trend analysis functions.

Computes YoY growth rates, CAGR, and growth rankings using Polars.
All functions are pure (no side effects); inputs are not modified.
"""

from pathlib import Path

import polars as pl
from loguru import logger


def compute_yoy_growth(
    df: pl.DataFrame,
    value_col: str,
    group_cols: list[str],
    year_col: str = "year",
) -> pl.DataFrame:
    """Compute year-over-year absolute and percentage growth.

    Args:
        df: Input DataFrame (must be sorted by year within groups)
        value_col: Numeric column to compute growth for
        group_cols: Columns defining groups, e.g. ["profession", "sector"]
        year_col: Name of the year column

    Returns:
        DataFrame with additional columns:
        - {value_col}_growth_abs: Absolute YoY change
        - {value_col}_growth_pct: Percentage YoY change
    """
    df_sorted = df.sort([year_col, *group_cols])
    return df_sorted.with_columns([
        (
            pl.col(value_col).diff().over(group_cols)
        ).alias(f"{value_col}_growth_abs"),
        (
            pl.col(value_col).diff().over(group_cols) /
            pl.col(value_col).shift(1).over(group_cols) * 100.0
        ).alias(f"{value_col}_growth_pct"),
    ])


def compute_cagr(
    df: pl.DataFrame,
    value_col: str,
    group_cols: list[str],
    start_year: int,
    end_year: int,
    year_col: str = "year",
) -> pl.DataFrame:
    """Compute Compound Annual Growth Rate (CAGR) for each group.

    Formula: CAGR = (value_end / value_start) ^ (1 / n_years) - 1

    Args:
        df: Input DataFrame
        value_col: Numeric column to compute CAGR for
        group_cols: Grouping columns
        start_year: Base year (inclusive)
        end_year: End year (inclusive)
        year_col: Name of the year column

    Returns:
        DataFrame with one row per group: group_cols + [cagr, start_value, end_value]
    """
    n_years = end_year - start_year
    if n_years <= 0:
        raise ValueError(f"end_year ({end_year}) must be > start_year ({start_year})")

    start = (
        df.filter(pl.col(year_col) == start_year)
        .select([*group_cols, pl.col(value_col).alias("start_value")])
    )
    end = (
        df.filter(pl.col(year_col) == end_year)
        .select([*group_cols, pl.col(value_col).alias("end_value")])
    )

    merged = start.join(end, on=group_cols, how="inner")
    result = merged.with_columns([
        (
            (pl.col("end_value") / pl.col("start_value")).pow(1.0 / n_years) - 1.0
        ).alias("cagr"),
        pl.lit(start_year).alias("start_year"),
        pl.lit(end_year).alias("end_year"),
    ])

    logger.info(
        f"CAGR computed for {len(result)} groups "
        f"({start_year}–{end_year}, {n_years} years)"
    )
    return result


def rank_by_cagr(
    cagr_df: pl.DataFrame,
    group_col: str,
    cagr_col: str = "cagr",
) -> pl.DataFrame:
    """Rank groups by CAGR descending; add rank and fastest/slowest flag.

    Args:
        cagr_df: Output of compute_cagr()
        group_col: Column containing group labels
        cagr_col: Name of the CAGR column

    Returns:
        DataFrame with added columns: rank, growth_tier
    """
    ranked = cagr_df.with_columns(
        pl.col(cagr_col).rank(descending=True).alias("rank")
    ).sort("rank")

    n = len(ranked)
    tiers = (
        ["Fastest"] +
        ["Mid"] * max(0, n - 2) +
        (["Slowest"] if n > 1 else [])
    )
    return ranked.with_columns(pl.Series("growth_tier", tiers))


def load_profession_tables(
    processed_dir: Path,
    professions: list[str],
) -> pl.DataFrame:
    """Load all workforce profession parquets and stack into a single DataFrame.

    Args:
        processed_dir: Directory containing *_clean.parquet files
        professions: List of profession table name stems
            e.g. ["doctors", "nurses", "pharmacists"]

    Returns:
        Stacked DataFrame with added 'profession' column

    Raises:
        FileNotFoundError: If any parquet file is missing
    """
    frames: list[pl.DataFrame] = []
    for profession in professions:
        path = processed_dir / f"{profession}_clean.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Parquet not found: {path}")
        df = pl.read_parquet(str(path)).with_columns(
            pl.lit(profession).alias("profession")
        )
        frames.append(df)
        logger.debug(f"Loaded {profession}: {df.shape[0]} rows")

    combined = pl.concat(frames)
    logger.info(f"Workforce tables stacked: {combined.shape}")
    return combined
```

#### 3.2 `problem-statements/ps-001-healthcare-system-baseline/src/visualization.py`

```python
"""Plotly chart generation utilities for PS-001 EDA.

All chart functions return a go.Figure — not side-effecting.
save_figure() handles PNG export via kaleido.
"""

from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from loguru import logger

CHART_TEMPLATE = "plotly_white"
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 700


def plot_workforce_trends(
    df: pl.DataFrame,
    value_col: str = "headcount",
    year_col: str = "year",
    profession_col: str = "profession",
    sector_filter: str = "Public",
) -> go.Figure:
    """Line chart: workforce headcount by profession (public sector) over time.

    Args:
        df: Stacked workforce DataFrame with profession and sector columns
        value_col: Numeric column for y-axis
        year_col: Year column for x-axis
        profession_col: Column for line grouping
        sector_filter: Filter to this sector value

    Returns:
        Plotly Figure
    """
    plot_df = df.filter(pl.col("sector") == sector_filter)
    pdf = plot_df.to_pandas()

    fig = px.line(
        pdf,
        x=year_col,
        y=value_col,
        color=profession_col,
        markers=True,
        title=f"[DRAFT] Healthcare Workforce Headcount ({sector_filter} Sector) | MOH-SG",
        labels={year_col: "Year", value_col: "Headcount", profession_col: "Profession"},
        template=CHART_TEMPLATE,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
    )
    fig.update_yaxes(rangemode="tozero")
    return fig


def plot_cagr_comparison(
    cagr_df: pl.DataFrame,
    group_col: str = "profession",
    cagr_col: str = "cagr",
    title_suffix: str = "",
) -> go.Figure:
    """Horizontal bar chart: CAGR comparison across professions or facility types.

    Bars are colour-coded green (positive CAGR) / red (negative CAGR).

    Args:
        cagr_df: Output of rank_by_cagr() — contains group_col and cagr_col
        group_col: Column for y-axis categories
        cagr_col: Column containing CAGR float values
        title_suffix: Appended to chart title

    Returns:
        Plotly Figure
    """
    pdf = cagr_df.sort(cagr_col).to_pandas()
    pdf["cagr_pct"] = pdf[cagr_col] * 100
    pdf["colour"] = pdf["cagr_pct"].apply(
        lambda v: "#27AE60" if v >= 0 else "#E74C3C"
    )

    fig = go.Figure(go.Bar(
        x=pdf["cagr_pct"],
        y=pdf[group_col],
        orientation="h",
        marker_color=pdf["colour"].tolist(),
        text=pdf["cagr_pct"].apply(lambda v: f"{v:.2f}%"),
        textposition="outside",
    ))
    fig.update_layout(
        title=f"[DRAFT] CAGR Comparison 2009–2018 {title_suffix} | MOH-SG",
        xaxis_title="CAGR (%)",
        yaxis_title=group_col.replace("_", " ").title(),
        template=CHART_TEMPLATE,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
    )
    return fig


def save_figure(fig: go.Figure, output_path: Path) -> None:
    """Export a Plotly figure as a PNG file using kaleido.

    Args:
        fig: Plotly figure to export
        output_path: Absolute path to output PNG file

    Raises:
        RuntimeError: If kaleido is not installed
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.write_image(
            str(output_path),
            width=DEFAULT_WIDTH,
            height=DEFAULT_HEIGHT,
            scale=2,  # 2x for ~150 dpi equivalent
        )
        logger.info(f"Chart saved: {output_path}")
    except Exception as exc:
        logger.error(f"Failed to save chart {output_path}: {exc}")
        raise RuntimeError(f"Chart export failed: {exc}") from exc
```

#### 3.3 `problem-statements/ps-001-healthcare-system-baseline/scripts/run_eda_workforce.py`

```python
"""PS-001 Story 03 — Workforce & Facility Trend EDA.

Run: python problem-statements/ps-001-healthcare-system-baseline/scripts/run_eda_workforce.py
"""

import sys
from pathlib import Path

import polars as pl
import yaml
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.trend_analysis import (  # noqa: E402
    compute_cagr,
    compute_yoy_growth,
    load_profession_tables,
    rank_by_cagr,
)
from problem_statements.ps_001_healthcare_system_baseline.src.visualization import (  # noqa: E402
    plot_cagr_comparison,
    plot_workforce_trends,
    save_figure,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
RESULTS_DIR = PS_DIR / "results" / "tables"
FIGURES_DIR = PS_DIR / "reports" / "figures"
LOG_PATH = PS_DIR / "logs" / "etl" / "eda_workforce.log"

PROFESSIONS = ["doctors", "nurses", "pharmacists", "dentists", "allied_health_professionals"]
START_YEAR, END_YEAR = 2009, 2018


def main() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.add(str(LOG_PATH), level="INFO", rotation="10 MB")
    logger.info("=== PS-001 Story 03: Workforce & Facility Trend EDA ===")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # --- Workforce ---
    workforce_df = load_profession_tables(PROCESSED_DIR, PROFESSIONS)
    workforce_yoy = compute_yoy_growth(
        workforce_df, "headcount", ["profession", "sector"]
    )
    cagr_df = compute_cagr(
        workforce_df, "headcount", ["profession", "sector"], START_YEAR, END_YEAR
    )
    ranked = rank_by_cagr(cagr_df, "profession")

    summary = workforce_yoy.group_by(["profession", "sector"]).agg([
        pl.col("headcount").mean().alias("avg_headcount"),
        pl.col("headcount_growth_pct").mean().alias("avg_yoy_pct"),
        pl.col("headcount").min().alias("min_headcount"),
        pl.col("headcount").max().alias("max_headcount"),
    ])
    summary.write_csv(str(RESULTS_DIR / "workforce_trend_summary.csv"))
    logger.info(f"Workforce summary: {RESULTS_DIR / 'workforce_trend_summary.csv'}")

    # --- Facility ---
    beds_path = PROCESSED_DIR / "inpatient_beds_clean.parquet"
    if beds_path.exists():
        beds_df = pl.read_parquet(str(beds_path))
        beds_cagr = compute_cagr(
            beds_df, "beds", ["facility_type"], START_YEAR, min(END_YEAR, 2020)
        )
        beds_ranked = rank_by_cagr(beds_cagr, "facility_type")
        beds_ranked.write_csv(str(RESULTS_DIR / "facility_trend_summary.csv"))
        logger.info("Facility summary written.")

    # --- Charts ---
    fig_workforce = plot_workforce_trends(workforce_df)
    save_figure(fig_workforce, FIGURES_DIR / "workforce_trends.png")

    fig_cagr = plot_cagr_comparison(ranked, title_suffix="(Workforce)")
    save_figure(fig_cagr, FIGURES_DIR / "workforce_cagr.png")

    logger.info("=== EDA complete ===")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# problem-statements/ps-001-healthcare-system-baseline/tests/unit/test_trend_analysis.py

import sys
from pathlib import Path
import polars as pl
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.trend_analysis import (
    compute_cagr,
    compute_yoy_growth,
    rank_by_cagr,
)


@pytest.fixture
def simple_df() -> pl.DataFrame:
    return pl.DataFrame({
        "year": [2009, 2010, 2011, 2012],
        "headcount": [1000, 1100, 1210, 1331],
        "profession": ["nurses"] * 4,
        "sector": ["Public"] * 4,
    })


def test_yoy_growth_percentage(simple_df: pl.DataFrame) -> None:
    result = compute_yoy_growth(simple_df, "headcount", ["profession", "sector"])
    pcts = result["headcount_growth_pct"].drop_nulls().to_list()
    # All should be ~10%
    for pct in pcts:
        assert abs(pct - 10.0) < 0.01


def test_cagr_value(simple_df: pl.DataFrame) -> None:
    result = compute_cagr(simple_df, "headcount", ["profession", "sector"], 2009, 2012)
    cagr_val = result["cagr"][0]
    # 1331/1000 ^ (1/3) - 1 = 0.10
    assert abs(cagr_val - 0.10) < 0.001


def test_cagr_invalid_years(simple_df: pl.DataFrame) -> None:
    with pytest.raises(ValueError, match="end_year"):
        compute_cagr(simple_df, "headcount", ["profession", "sector"], 2012, 2009)


def test_rank_by_cagr() -> None:
    cagr_df = pl.DataFrame({
        "profession": ["nurses", "doctors", "pharmacists"],
        "cagr": [0.10, 0.05, 0.08],
    })
    result = rank_by_cagr(cagr_df, "profession")
    assert result["rank"][0] == 1  # fastest
    assert result["growth_tier"][0] == "Fastest"
    assert result["growth_tier"][-1] == "Slowest"
```

---

### 5. Implementation Steps

- [ ] Create `problem-statements/ps-001-healthcare-system-baseline/src/__init__.py`
- [ ] Create `src/trend_analysis.py`
- [ ] Create `src/visualization.py`
- [ ] Create `scripts/run_eda_workforce.py`
- [ ] Run `pytest tests/unit/test_trend_analysis.py -v` — all 4 tests must pass
- [ ] Run `python scripts/run_eda_workforce.py`
- [ ] Verify: `workforce_trend_summary.csv`, `facility_trend_summary.csv` in `results/tables/`
- [ ] Verify: `workforce_trends.png`, `workforce_cagr.png` in `reports/figures/`
- [ ] Inspect CAGR chart — nurses should appear as top or second-fastest growing profession

---

### 6. Version Control

```bash
git checkout -b feat/ps-001-story-03-eda-workforce
git commit -m "feat(ps-001): add trend analysis and visualization modules"
git commit -m "feat(ps-001): add workforce EDA orchestration script"
git commit -m "test(ps-001): add trend analysis unit tests"
```
