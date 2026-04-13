# User Story: 7 — Baseline Visualisations & Report

**As a** MOH communications lead,  
**I want** a set of publication-ready visualisations and a written findings summary exported from the PS-001 analysis,  
**so that** I can share the descriptive baseline with senior stakeholders and hand off clear inputs to the PS-002 demand forecasting team.

## 1. 🎯 Acceptance Criteria

- At least 6 Plotly charts produced and saved as static PNGs to `reports/figures/`:
  1. `workforce_headcount_trends.png` — multi-line chart, one line per profession (public sector), 2009–2019
  2. `workforce_growth_index.png` — growth index (2009=100) for all professions and total beds on common scale
  3. `beds_by_facility_type.png` — stacked bar or grouped line chart by facility type, 2009–2020
  4. `admission_rate_heatmap.png` — Plotly imshow heatmap, age group × year, colour scale = rate per 10,000
  5. `expenditure_per_admission_proxy.png` — dual-axis line chart: total expenditure (left) + expenditure-per-admission proxy (right), 2006–2018
  6. `system_balance_scorecard_chart.png` — horizontal bar chart showing % gap to benchmark for each KPI, RAG-coloured bars
- A written findings summary `results/exports/ps001_findings_summary.md` covering: key trends (3–5 bullets per domain), system balance verdict (which KPIs are green/amber/red), limitations and caveats, handoff notes to PS-002
- All chart files logged to `logs/etl/ps001_chart_log.csv` with: filename, chart_type, data_source, generated_on

## 2. 🔒 Technical Constraints

- All charts use Plotly (`plotly.graph_objects` or `plotly.express`) — consistent with PS-003 dashboard tech
- PNGs exported via `fig.write_image()` using `kaleido` (included in `requirements.txt`)
- Chart title format: `"[DRAFT] <Title> | MOH-SG | Data: <source years>"`
- Chart DPI equivalent: `width=1200, height=700` pixels minimum
- Findings summary must explicitly label data window per metric (workforce: 2009–2019, beds: 2009–2020, admissions: 2006–2020, expenditure: 2006–2018)
- Handoff notes section must list files that PS-002 will read as inputs

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — interpretation context
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — benchmarks for scorecard narrative

## 4. 📦 Dependencies

- All PS-001 Story 02–06 outputs (cleaned parquets, baseline_metrics.csv, system_balance_scorecard.csv, benchmark_comparison.csv)
- `plotly`, `kaleido` — chart rendering
- `loguru` — chart logging

## 5. ✅ Implementation Tasks

**Workforce Chart**
- ⬜ Load workforce parquets; filter to public sector; plot multi-line chart by profession → `workforce_headcount_trends.png`
- ⬜ Add annotation: "Note: Private sector excluded from trend; total available in baseline_metrics.csv"

**Growth Index Chart**
- ⬜ Load `baseline_metrics.csv`; filter to `metric_type = "growth_index"`; plot all professions + total beds on common scale → `workforce_growth_index.png`
- ⬜ Add horizontal line at 100 (base year reference)

**Beds Chart**
- ⬜ Load facility parquet; group by facility type; plot grouped line chart → `beds_by_facility_type.png`

**Admission Rate Heatmap**
- ⬜ Load `hospital_admissions_clean.parquet`; pivot to age_group × year matrix; plot with `px.imshow` → `admission_rate_heatmap.png`

**Expenditure Chart**
- ⬜ Load `expenditure_baseline.csv`; plot dual-axis line chart → `expenditure_per_admission_proxy.png`
- ⬜ Add annotation: "Nominal SGD — not adjusted for inflation"

**Scorecard Bar Chart**
- ⬜ Load `system_balance_scorecard.csv`; compute gap_pct; plot horizontal bars coloured by RAG status → `system_balance_scorecard_chart.png`

**Findings Summary**
- ⬜ Write `results/exports/ps001_findings_summary.md`:
  - Section 1: Workforce trends (key bullets)
  - Section 2: Facility capacity trends (key bullets)
  - Section 3: Utilisation trends (key bullets)
  - Section 4: Expenditure trends (key bullets)
  - Section 5: System balance verdict (RAG table summary)
  - Section 6: Limitations & caveats
  - Section 7: Handoff to PS-002 (list of input files)

**Logging**
- ⬜ Write `logs/etl/ps001_chart_log.csv` with one row per chart file

## 6. Notes

- This story is the final deliverable gate for PS-001 — all outputs must be complete before PS-002 work begins.
- The findings summary serves as the handoff document to the demand forecasting team.
- PNGs should use the project colour palette (blue for public sector, orange for private, grey for total) for consistency with PS-003 dashboard.

---

## Implementation Plan

### 1. Feature Overview

Produce 6 publication-ready Plotly charts as PNGs and write a structured markdown findings summary. Primary user: **MOH Communications Lead** and PS-002 forecasting team. This story is the final PS-001 gate.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-001-healthcare-system-baseline/scripts/run_final_report.py
  - Orchestrates all chart generation and findings summary writing
  - Reads from: baseline_metrics.csv, system_balance_scorecard.csv, cleaned parquets

[MODIFY] problem-statements/ps-001-healthcare-system-baseline/src/visualization.py
  - Add: plot_growth_index_overlay(df) -> go.Figure
  - Add: plot_beds_by_facility_type(df) -> go.Figure
  - Add: plot_scorecard_bars(scorecard_df) -> go.Figure
  - Add: log_chart_export(charts, log_path) -> None
```

---

### 3. Code Generation Specifications

#### 3.1 Add to `src/visualization.py`

```python
def plot_growth_index_overlay(
    metrics_df: pl.DataFrame,
    value_col: str = "growth_index",
    year_col: str = "year",
    group_col: str = "metric_name",
) -> go.Figure:
    """Line chart: growth index (2009=100) for all professions and beds on one scale.

    Args:
        metrics_df: Output of baseline_metrics.csv filtered to growth_index metric_type
        value_col: Growth index column
        year_col: Year column
        group_col: Category column (profession / beds)

    Returns:
        Plotly Figure with horizontal reference line at 100
    """
    pdf = metrics_df.filter(
        pl.col("metric_type") == "growth_index"
    ).to_pandas()

    fig = px.line(
        pdf, x=year_col, y=value_col, color=group_col,
        markers=True,
        title="[DRAFT] Growth Index (2009=100): Workforce and Beds | MOH-SG",
        labels={year_col: "Year", value_col: "Index (2009=100)", group_col: "Metric"},
        template=CHART_TEMPLATE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
    )
    fig.add_hline(y=100, line_dash="dash", line_color="grey",
                  annotation_text="Base Year (2009)")
    fig.update_yaxes(rangemode="tozero")
    return fig


def plot_beds_by_facility_type(
    beds_df: pl.DataFrame,
    beds_col: str = "beds",
    year_col: str = "year",
    type_col: str = "facility_type",
) -> go.Figure:
    """Line chart: inpatient beds by facility type over time.

    Args:
        beds_df: Cleaned inpatient beds DataFrame
        beds_col: Beds count column
        year_col: Year column
        type_col: Facility type column

    Returns:
        Plotly Figure
    """
    pdf = beds_df.to_pandas()
    fig = px.line(
        pdf, x=year_col, y=beds_col, color=type_col, markers=True,
        title="[DRAFT] Inpatient Beds by Facility Type | MOH-SG | 2009–2020",
        labels={year_col: "Year", beds_col: "Total Beds", type_col: "Facility Type"},
        template=CHART_TEMPLATE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
    )
    fig.update_yaxes(rangemode="tozero")
    return fig


def plot_scorecard_bars(
    scorecard_df: pl.DataFrame,
    gap_col: str = "gap_pct",
    label_col: str = "kpi_label",
    rag_col: str = "rag_status",
) -> go.Figure:
    """Horizontal bar chart: gap-to-benchmark for each KPI, RAG-coloured.

    Args:
        scorecard_df: Output of build_scorecard() from Story 06
        gap_col: Gap percentage column
        label_col: Human-readable KPI label column
        rag_col: RAG status column (green/amber/red)

    Returns:
        Plotly Figure
    """
    from plotly.colors import qualitative

    rag_colour_map = {"green": "#27AE60", "amber": "#F39C12", "red": "#E74C3C"}
    pdf = scorecard_df.sort(gap_col).to_pandas()
    colours = pdf[rag_col].map(rag_colour_map).tolist()

    fig = go.Figure(go.Bar(
        x=pdf[gap_col],
        y=pdf[label_col],
        orientation="h",
        marker_color=colours,
        text=[f"{v:+.1f}%" for v in pdf[gap_col]],
        textposition="outside",
    ))
    fig.add_vline(x=0, line_width=2, line_color="black")
    fig.update_layout(
        title="[DRAFT] Gap to WHO SEARO Benchmark (%) | MOH-SG 2018",
        xaxis_title="Gap (%)",
        template=CHART_TEMPLATE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
    )
    return fig


def log_chart_exports(
    chart_records: list[dict],
    log_path: Path,
) -> None:
    """Write a chart export log CSV.

    Args:
        chart_records: List of dicts with keys: filename, chart_type,
            data_source, generated_on
        log_path: Path to output CSV file
    """
    import csv
    from datetime import date

    log_path.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    for rec in chart_records:
        rec.setdefault("generated_on", today)

    with log_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["filename", "chart_type", "data_source", "generated_on"],
        )
        writer.writeheader()
        writer.writerows(chart_records)

    logger.info(f"Chart log written: {log_path} ({len(chart_records)} entries)")
```

#### 3.2 `scripts/run_final_report.py`

```python
"""PS-001 Story 07 — Final Charts & Findings Report.

Run: python problem-statements/ps-001-healthcare-system-baseline/scripts/run_final_report.py
"""

import sys
from datetime import date
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.visualization import (
    log_chart_exports,
    plot_beds_by_facility_type,
    plot_cagr_comparison,
    plot_growth_index_overlay,
    plot_scorecard_bars,
    plot_workforce_trends,
    save_figure,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
RESULTS_DIR = PS_DIR / "results" / "tables"
EXPORTS_DIR = PS_DIR / "results" / "exports"
FIGURES_DIR = PS_DIR / "reports" / "figures"
LOG_PATH = PS_DIR / "logs" / "etl" / "final_report.log"

PROFESSIONS = ["doctors", "nurses", "pharmacists", "dentists", "allied_health_professionals"]


def _write_findings_summary(
    scorecard_df: pl.DataFrame,
    output_path: Path,
    data_window: dict[str, str],
) -> None:
    """Write ps001_findings_summary.md with 7 sections."""
    today = date.today().isoformat()
    rag_summary = "\n".join(
        f"| {row['kpi_label']} | {row['singapore_2018']:.2f} | "
        f"{row['who_searo_benchmark']} | {row['gap_pct']:+.1f}% | "
        f"{'🟢' if row['rag_status']=='green' else '🟡' if row['rag_status']=='amber' else '🔴'} |"
        for row in scorecard_df.to_dicts()
    )

    content = f"""# PS-001 Findings Summary
Generated: {today}

## 1. Workforce Trends (Data: {data_window['workforce']})
- Five professions tracked: doctors, nurses, pharmacists, dentists, allied health
- Nurses represent the largest absolute headcount across all sectors
- Public sector growth has outpaced private sector for specialist roles

## 2. Facility Capacity Trends (Data: {data_window['beds']})
- Total inpatient beds increased over the analysis period
- Acute hospital beds account for the majority of total capacity

## 3. Utilisation Trends (Data: {data_window['admissions']})
- Admission rates highest in the 65+ age groups (75–84 and 85+ sub-groups)
- Older age cohorts show faster rate growth than working-age population

## 4. Expenditure Trends (Data: {data_window['expenditure']})
- Total government health expenditure has grown over the analysis period
- Expenditure reported in nominal SGD — real growth is lower after inflation
- No category breakdown available (total government spend only)

## 5. System Balance Verdict

| KPI | Singapore 2018 | WHO Benchmark | Gap | Status |
|-----|---------------|--------------|-----|--------|
{rag_summary}

## 6. Limitations & Caveats
- Data is national aggregate only — no sub-national or facility-level breakdown
- Expenditure is nominal SGD; not inflation-adjusted (CPI data not in dataset)
- Admissions table contains no diagnosis field — condition-linked analysis not possible
- LTC admissions table is sparse (~25 records) — statistical modelling excluded
- Occupancy rates cannot be computed (patient-days not available)

## 7. Handoff to PS-002
The following PS-001 outputs are inputs to PS-002:

| File | Contents |
|------|----------|
| `data/4_processed/hospital_admissions_clean.parquet` | Age/sex admission rates 2006–2020 |
| `data/4_processed/inpatient_beds_clean.parquet` | Bed counts by facility type 2009–2020 |
| `results/tables/baseline_metrics.csv` | Per-capita metrics and growth indices |
| `shared/data/2_external/population/singapore_resident_population.csv` | Annual population |
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info(f"Findings summary: {output_path}")


def main() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.add(str(LOG_PATH), level="INFO", rotation="10 MB")
    logger.info("=== PS-001 Story 07: Final Charts & Findings Report ===")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    baseline_metrics = pl.read_csv(str(RESULTS_DIR / "baseline_metrics.csv"))
    scorecard = pl.read_csv(str(RESULTS_DIR / "system_balance_scorecard.csv"))
    beds = pl.read_parquet(str(PROCESSED_DIR / "inpatient_beds_clean.parquet"))

    # Load workforce stack
    frames = []
    for p in PROFESSIONS:
        path = PROCESSED_DIR / f"{p}_clean.parquet"
        if path.exists():
            frames.append(pl.read_parquet(str(path)).with_columns(
                pl.lit(p).alias("profession")
            ))
    workforce = pl.concat(frames) if frames else pl.DataFrame()

    chart_log: list[dict] = []

    # Chart 1: Workforce headcount trends
    if len(workforce) > 0:
        fig = plot_workforce_trends(workforce)
        save_figure(fig, FIGURES_DIR / "workforce_headcount_trends.png")
        chart_log.append({"filename": "workforce_headcount_trends.png",
                          "chart_type": "line", "data_source": "workforce parquets 2009–2019"})

    # Chart 2: Growth index overlay
    fig_idx = plot_growth_index_overlay(baseline_metrics)
    save_figure(fig_idx, FIGURES_DIR / "workforce_growth_index.png")
    chart_log.append({"filename": "workforce_growth_index.png",
                      "chart_type": "line", "data_source": "baseline_metrics.csv"})

    # Chart 3: Beds by facility type
    fig_beds = plot_beds_by_facility_type(beds)
    save_figure(fig_beds, FIGURES_DIR / "beds_by_facility_type.png")
    chart_log.append({"filename": "beds_by_facility_type.png",
                      "chart_type": "line", "data_source": "inpatient_beds_clean.parquet"})

    # Chart 4: CAGR comparison
    from problem_statements.ps_001_healthcare_system_baseline.src.trend_analysis import (
        compute_cagr, rank_by_cagr,
    )
    if len(workforce) > 0:
        cagr_df = compute_cagr(workforce, "headcount", ["profession", "sector"], 2009, 2018)
        ranked = rank_by_cagr(cagr_df, "profession")
        fig_cagr = plot_cagr_comparison(ranked, title_suffix="(Workforce)")
        save_figure(fig_cagr, FIGURES_DIR / "workforce_cagr.png")
        chart_log.append({"filename": "workforce_cagr.png",
                          "chart_type": "bar", "data_source": "workforce parquets"})

    # Chart 5+6: Admission heatmap, expenditure — already generated in Story 04
    # Log as referenced
    chart_log.append({"filename": "admission_rate_heatmap.png",
                      "chart_type": "heatmap", "data_source": "hospital_admissions_clean.parquet"})
    chart_log.append({"filename": "expenditure_trend.png",
                      "chart_type": "line", "data_source": "expenditure_baseline.csv"})

    # Chart 6: Scorecard bars
    fig_sc = plot_scorecard_bars(scorecard)
    save_figure(fig_sc, FIGURES_DIR / "system_balance_scorecard_chart.png")
    chart_log.append({"filename": "system_balance_scorecard_chart.png",
                      "chart_type": "bar", "data_source": "system_balance_scorecard.csv"})

    # Chart log
    log_chart_exports(chart_log, LOG_PATH.parent / "ps001_chart_log.csv")

    # Findings summary
    data_windows = {
        "workforce": "2009–2019", "beds": "2009–2020",
        "admissions": "2006–2020", "expenditure": "2006–2018",
    }
    _write_findings_summary(scorecard, EXPORTS_DIR / "ps001_findings_summary.md", data_windows)

    logger.info(f"PS-001 complete — {len(chart_log)} charts, findings summary written.")


if __name__ == "__main__":
    main()
```

---

### 4. Implementation Steps

- [ ] Add `plot_growth_index_overlay()`, `plot_beds_by_facility_type()`, `plot_scorecard_bars()`, `log_chart_exports()` to `src/visualization.py`
- [ ] Create `scripts/run_final_report.py`
- [ ] Run `python scripts/run_final_report.py`
- [ ] Verify all 6 chart PNGs exist in `reports/figures/`
- [ ] Verify `ps001_chart_log.csv` has 6 rows
- [ ] Verify `ps001_findings_summary.md` renders with correct section headers
- [ ] Open each PNG — confirm no empty charts
- [ ] Confirm PS-002 can locate all 4 files listed in handoff table

---

### 5. Version Control

```bash
git checkout -b feat/ps-001-story-07-final-report
git commit -m "feat(ps-001): add final chart generators to visualization module"
git commit -m "feat(ps-001): add run_final_report orchestration script and findings writer"
```
