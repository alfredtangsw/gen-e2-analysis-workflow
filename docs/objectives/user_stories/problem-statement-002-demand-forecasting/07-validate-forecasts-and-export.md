# User Story: 7 — Forecast Validation, Charts, and Demand Projections Export

**As a** MOH strategic planning lead,  
**I want** forecast accuracy results, confidence interval charts for all disease forecasts, and a final consolidated demand projections export,  
**so that** I can present credible, evidence-based demand scenarios to leadership and hand off quantified inputs to the PS-003 resource planning team.

## 1. 🎯 Acceptance Criteria

- Backtesting summary chart produced for each disease: actual vs hold-out predictions (2015–2019) with model name annotated — saved to `reports/figures/ps002_forecast/`
- Forward forecast charts produced for each disease: 2000–2030 historical + forecast with 80% and 95% shaded confidence intervals — saved to `reports/figures/ps002_forecast/`
- Admission volume projection chart produced: 2010–2035 line chart for all 3 demographic scenarios — saved to `reports/figures/ps002_forecast/`
- Validation summary table saved to `results/tables/ps002_forecast_validation.csv`: `disease, model, mape_holdout, mape_acceptable (T/F), forecast_horizon, ci_80_width_2030`
- Final export package saved to `results/exports/ps002_demand_projections_export.csv`: merged forecast + admission projection for use in PS-003, with all scenarios and confidence bounds
- Findings summary `results/exports/ps002_forecast_findings.md` written: key trend assertions, model performance notes, scenario range for 2030 and 2035 admissions, data limitations, handoff to PS-003

## 2. 🔒 Technical Constraints

- All forward-looking charts use Plotly — shaded CI areas via `go.Scatter(fill='tonexty')` technique
- Backtesting charts use Plotly with distinct line styles: solid = actual, dashed = predicted
- MAPE acceptable threshold = 15% (consistent with Story 05 threshold)
- Export CSV must include a `source_ps` column (`"PS-002"`) and a `generated_on` timestamp column for auditability
- Chart file naming convention: `ps002_forecast_{disease}.png`, `ps002_backtesting_{disease}.png`, `ps002_admission_scenarios.png`
- kaleido used for PNG export (`fig.write_image()`)

## 3. 📚 Domain Knowledge References

- [Time-Series Forecasting Methods](../../../../domain-knowledge/time-series-forecasting-methods.md) — MAPE interpretation, CI width guidance
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — how demand projections feed into bed and workforce gap calculations in PS-003

## 4. 📦 Dependencies

- Story 05 outputs: `models/forecasts/mortality_{disease}_forecast.csv` × 3 diseases, `ps002_mortality_model_comparison.csv`
- Story 06 outputs: `models/forecasts/admission_volume_projections.csv`, `ps002_admission_sensitivity_2035.csv`
- `plotly`, `kaleido` — chart generation
- `polars` — data assembly and CSV export

## 5. ✅ Implementation Tasks

**Backtesting Charts**
- ⬜ For each disease: load forecast CSV; filter to hold-out period 2015–2019; plot actual vs predicted → `ps002_backtesting_{disease}.png`
- ⬜ Annotate with MAPE value on chart

**Forward Forecast Charts**
- ⬜ For each disease: combine historical series + forecast; plot with shaded 80%/95% CI bands → `ps002_forecast_{disease}.png`
- ⬜ Add vertical dashed line at 2019 (last actual data point)
- ⬜ Add annotation: "Forecast: {model_type} | MAPE (hold-out): {mape:.1f}%"

**Admission Scenario Chart**
- ⬜ Load `admission_volume_projections.csv`; plot 3 scenario lines (principal, high, low) for 2010–2035 → `ps002_admission_scenarios.png`
- ⬜ Shade region between high and low scenarios with low opacity fill
- ⬜ Add vertical dashed line at 2021 (start of projection period)

**Validation Summary**
- ⬜ Assemble validation CSV from Story 05 model comparison data + CI width computation (2030 upper_95 - lower_95)
- ⬜ Write to `results/tables/ps002_forecast_validation.csv`

**Export Package**
- ⬜ Merge mortality forecasts + admission projections into single long-format CSV
- ⬜ Add columns: `source_ps = "PS-002"`, `generated_on = today's date ISO format`
- ⬜ Save to `results/exports/ps002_demand_projections_export.csv`

**Findings Summary**
- ⬜ Write `results/exports/ps002_forecast_findings.md`:
  - Section 1: Mortality forecast verdicts (one paragraph per disease)
  - Section 2: Admission volume range (2030 low/principal/high figures)
  - Section 3: Scenario comparison (2035 sensitivity table summary)
  - Section 4: Model performance (MAPE table summary)
  - Section 5: Limitations (only 3 diseases; flat rate assumption; no LTC forecast)
  - Section 6: Handoff to PS-003 (list files in export package + what each contains)

## 6. Notes

- The findings summary serves as a non-technical brief that PS-003 passes to planning stakeholders. Keep it under 2 pages.
- The 2035 high-scenario admission volume is the primary stress-test number for PS-003's bed and workforce gap calculations.
- CI width at 2030 is a useful signal of forecast confidence: ARIMA CIs widen rapidly beyond 5–7 years; Prophet's CIs tend to be wider overall. Note this in findings.

---

## Implementation Plan

### 1. Feature Overview

Produce backtesting charts, forward forecast charts with CI shading, admission scenario chart, and the consolidated export package. Write a stakeholder forecast findings summary. Primary user: **MOH strategic planning lead**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-002-disease-burden/src/forecast_visualization.py
  - plot_backtesting_chart(actual_df, forecast_df, disease, mape, figures_dir) -> None
  - plot_forward_forecast(historical_df, forecast_df, disease, model_type, mape, figures_dir) -> None
  - plot_admission_scenarios(projections_df, figures_dir) -> None

[CREATE] problem-statements/ps-002-disease-burden/scripts/run_forecast_export.py
  - Orchestrates all charts; writes validation CSV; final export CSV; findings MD
```

---

### 3. Code Generation Specifications

#### 3.1 `src/forecast_visualization.py`

```python
"""PS-002 forecast chart generation.

All forward-looking charts use Plotly with go.Scatter(fill='tonexty') for CI shading.
Backtesting charts use dashed lines for predictions vs solid actuals.
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

CHART_TEMPLATE = "plotly_white"
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 700
COLOUR_ACTUAL = "#2980B9"
COLOUR_FORECAST = "#E74C3C"
COLOUR_CI_80 = "rgba(231,76,60,0.15)"
COLOUR_CI_95 = "rgba(231,76,60,0.08)"


def _save(fig: go.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(path))
    logger.info(f"Chart saved: {path}")


def plot_backtesting_chart(
    actual_df: pl.DataFrame,
    forecast_df: pl.DataFrame,
    disease: str,
    mape: float,
    figures_dir: Path,
    year_col: str = "year",
    actual_col: str = "rate",
    pred_col: str = "predicted",
) -> None:
    """Backtesting chart: actual vs hold-out predictions (2015–2019).

    Args:
        actual_df: Historical actuals for hold-out period
        forecast_df: Hold-out predictions
        disease: Disease name for chart title and filename
        mape: Hold-out MAPE for annotation
        figures_dir: Output directory
        year_col: Year column name
        actual_col: Actual rate column name
        pred_col: Predicted column name in forecast_df
    """
    act_pd = actual_df.sort(year_col).to_pandas()
    fcast_pd = forecast_df.sort(year_col).to_pandas()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=act_pd[year_col], y=act_pd[actual_col], mode="lines+markers",
        name="Actual", line={"color": COLOUR_ACTUAL, "width": 2},
    ))
    fig.add_trace(go.Scatter(
        x=fcast_pd[year_col], y=fcast_pd[pred_col], mode="lines+markers",
        name="Predicted (hold-out)", line={"color": COLOUR_FORECAST, "width": 2, "dash": "dash"},
    ))
    fig.update_layout(
        title=(
            f"[DRAFT] {disease.upper()} Mortality — Backtesting (2015–2019) | "
            f"MAPE: {mape:.1f}% | MOH-SG"
        ),
        xaxis_title="Year", yaxis_title="Rate",
        template=CHART_TEMPLATE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
    )
    _save(fig, figures_dir / f"ps002_backtesting_{disease}.png")


def plot_forward_forecast(
    historical_df: pl.DataFrame,
    forecast_df: pl.DataFrame,
    disease: str,
    model_type: str,
    mape: float,
    figures_dir: Path,
    year_col: str = "year",
    actual_col: str = "rate",
) -> None:
    """Forward forecast chart: full history + 2020–2030 with 80/95% CI shading.

    Args:
        historical_df: Full historical series (all available years)
        forecast_df: Forecast DataFrame with columns year, forecast, lower_80, upper_80,
            lower_95, upper_95
        disease: Disease name
        model_type: Model name for annotation
        mape: Hold-out MAPE for annotation
        figures_dir: Output directory
        year_col: Year column
        actual_col: Historical rate column
    """
    hist_pd = historical_df.sort(year_col).to_pandas()
    fc_pd = forecast_df.sort(year_col).to_pandas()

    # Convert "forecast" col if named differently
    fc_y_col = "forecast" if "forecast" in fc_pd.columns else "predicted"

    fig = go.Figure()

    # 95% CI (outer shaded area — lower trace first, then fill above)
    fig.add_trace(go.Scatter(
        x=fc_pd[year_col].tolist(), y=fc_pd["lower_95"].tolist(),
        mode="lines", line={"width": 0}, showlegend=False, name="lower_95",
    ))
    fig.add_trace(go.Scatter(
        x=fc_pd[year_col].tolist(), y=fc_pd["upper_95"].tolist(),
        fill="tonexty", fillcolor=COLOUR_CI_95,
        mode="lines", line={"width": 0}, name="95% CI",
    ))

    # 80% CI
    fig.add_trace(go.Scatter(
        x=fc_pd[year_col].tolist(), y=fc_pd["lower_80"].tolist(),
        mode="lines", line={"width": 0}, showlegend=False, name="lower_80",
    ))
    fig.add_trace(go.Scatter(
        x=fc_pd[year_col].tolist(), y=fc_pd["upper_80"].tolist(),
        fill="tonexty", fillcolor=COLOUR_CI_80,
        mode="lines", line={"width": 0}, name="80% CI",
    ))

    # Historical actuals
    fig.add_trace(go.Scatter(
        x=hist_pd[year_col], y=hist_pd[actual_col], mode="lines+markers",
        name="Historical", line={"color": COLOUR_ACTUAL, "width": 2},
    ))

    # Forecast mean
    fig.add_trace(go.Scatter(
        x=fc_pd[year_col], y=fc_pd[fc_y_col], mode="lines",
        name=f"Forecast ({model_type})", line={"color": COLOUR_FORECAST, "width": 2},
    ))

    # Vertical line at last actual
    fig.add_vline(x=2019, line_dash="dash", line_color="grey",
                  annotation_text="Last actual (2019)")
    fig.add_annotation(
        text=f"Model: {model_type} | MAPE (hold-out): {mape:.1f}%",
        xref="paper", yref="paper", x=0.01, y=0.97,
        showarrow=False, font_size=11,
    )

    fig.update_layout(
        title=f"[DRAFT] {disease.upper()} Mortality Forecast 2020–2030 | MOH-SG",
        xaxis_title="Year", yaxis_title="Rate",
        template=CHART_TEMPLATE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
    )
    _save(fig, figures_dir / f"ps002_forecast_{disease}.png")


def plot_admission_scenarios(
    projections_df: pl.DataFrame,
    figures_dir: Path,
    year_col: str = "year",
    value_col: str = "projected_admissions",
    scenario_col: str = "scenario",
) -> None:
    """Admission volume projection chart: 3 scenario lines with shaded band.

    Args:
        projections_df: Output of run_admission_projection.py
        figures_dir: Output directory
        year_col: Year column
        value_col: Projected admissions column
        scenario_col: Scenario column
    """
    pdl = projections_df.to_pandas()
    scenario_colours = {
        "principal": "#2980B9",
        "high": "#E74C3C",
        "low": "#27AE60",
    }

    fig = go.Figure()

    # Shade between high and low
    high = pdl[pdl[scenario_col] == "high"].sort_values(year_col)
    low = pdl[pdl[scenario_col] == "low"].sort_values(year_col)

    if len(high) > 0 and len(low) > 0:
        fig.add_trace(go.Scatter(
            x=low[year_col].tolist(), y=low[value_col].tolist(),
            mode="lines", line={"width": 0}, showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=high[year_col].tolist(), y=high[value_col].tolist(),
            fill="tonexty", fillcolor="rgba(41,128,184,0.10)",
            mode="lines", line={"width": 0}, name="High–Low range",
        ))

    for scenario in ["principal", "high", "low"]:
        sub = pdl[pdl[scenario_col] == scenario].sort_values(year_col)
        if len(sub) == 0:
            continue
        fig.add_trace(go.Scatter(
            x=sub[year_col], y=sub[value_col],
            mode="lines+markers", name=scenario.title(),
            line={"color": scenario_colours.get(scenario, "#888"), "width": 2},
        ))

    fig.add_vline(x=2021, line_dash="dash", line_color="grey",
                  annotation_text="Projection start")
    fig.update_layout(
        title="[DRAFT] Projected Hospital Admissions 2021–2035 | Demographic Scenarios | MOH-SG",
        xaxis_title="Year", yaxis_title="Projected Admissions",
        template=CHART_TEMPLATE, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
    )
    _save(fig, figures_dir / "ps002_admission_scenarios.png")
```

#### 3.2 `scripts/run_forecast_export.py`

```python
"""PS-002 Story 07 — Forecast Validation, Charts, and Export.

Run: python problem-statements/ps-002-disease-burden/scripts/run_forecast_export.py
"""

import sys
from datetime import date
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_002_disease_burden.src.forecast_visualization import (
    plot_admission_scenarios,
    plot_backtesting_chart,
    plot_forward_forecast,
)

PS_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PS_DIR / "data" / "4_processed"
FORECASTS_DIR = PS_DIR / "models" / "forecasts"
RESULTS_DIR = PS_DIR / "results" / "tables"
EXPORTS_DIR = PS_DIR / "results" / "exports"
FIGURES_DIR = PS_DIR / "reports" / "figures" / "ps002_forecast"
LOG_DIR = PS_DIR / "logs" / "etl"

for d in (RESULTS_DIR, EXPORTS_DIR, FIGURES_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

logger.add(str(LOG_DIR / "ps002_forecast_export.log"), level="INFO", rotation="10 MB")

DISEASES = ["cancer", "stroke", "ihd"]
HOLDOUT_YEARS = list(range(2015, 2020))
MAPE_THRESHOLD = 15.0


def _auto_cols(df: pl.DataFrame) -> tuple[str, str]:
    year_col = next(c for c in df.columns if "year" in c.lower())
    rate_col = next(
        c for c in df.columns if any(kw in c.lower() for kw in ("rate", "deaths", "number"))
    )
    return year_col, rate_col


def main() -> None:
    logger.info("=== PS-002 Story 07: Forecast Validation & Export ===")
    today = date.today().isoformat()

    model_comparison = pl.read_csv(str(RESULTS_DIR / "ps002_mortality_model_comparison.csv"))
    validation_rows: list[dict] = []
    export_frames: list[pl.DataFrame] = []

    for disease in DISEASES:
        fc_path = FORECASTS_DIR / f"mortality_{disease}_forecast.csv"
        if not fc_path.exists():
            logger.warning(f"Forecast CSV missing for {disease}: {fc_path}")
            continue

        fc_df = pl.read_csv(str(fc_path))
        hist_df = pl.read_parquet(str(PROCESSED_DIR / f"mortality_{disease}_clean.parquet"))
        year_col, rate_col = _auto_cols(hist_df)

        # Get model info
        best_row = model_comparison.filter(
            (pl.col("disease") == disease) & pl.col("selected")
        )
        model_type = best_row["model"][0] if len(best_row) > 0 else "Unknown"
        mape = float(best_row["mape_holdout"][0]) if len(best_row) > 0 else float("nan")

        # Backtesting chart — use holdout prediction from forecast (first n rows may overlap)
        holdout_actual = hist_df.filter(
            pl.col(year_col).cast(pl.Int32).is_in(HOLDOUT_YEARS)
        )
        holdout_fc = fc_df.filter(pl.col("year").cast(pl.Int32).is_in(HOLDOUT_YEARS))
        if len(holdout_actual) > 0 and len(holdout_fc) > 0:
            holdout_renamed = holdout_actual.rename({rate_col: "rate"})
            plot_backtesting_chart(holdout_renamed, holdout_fc, disease, mape, FIGURES_DIR)

        # Forward forecast chart
        hist_renamed = hist_df.rename({year_col: "year", rate_col: "rate"}).select(["year", "rate"])
        plot_forward_forecast(hist_renamed, fc_df, disease, model_type, mape, FIGURES_DIR)

        # Compute CI width at 2030
        ci_2030_row = fc_df.filter(pl.col("year").cast(pl.Int32) == 2030)
        ci_width_2030 = None
        if len(ci_2030_row) > 0 and "upper_95" in fc_df.columns and "lower_95" in fc_df.columns:
            ci_width_2030 = float(ci_2030_row["upper_95"][0] - ci_2030_row["lower_95"][0])

        validation_rows.append({
            "disease": disease,
            "model": model_type,
            "mape_holdout": round(mape, 2),
            "mape_acceptable": mape <= MAPE_THRESHOLD,
            "forecast_horizon": "2020–2030",
            "ci_80_width_2030": round(ci_width_2030, 4) if ci_width_2030 else None,
        })

        # Add to export frame
        export_frames.append(
            fc_df.with_columns([
                pl.lit(disease).alias("disease"),
                pl.lit("mortality_forecast").alias("data_type"),
                pl.lit("PS-002").alias("source_ps"),
                pl.lit(today).alias("generated_on"),
            ])
        )

    # Admission scenario chart
    admissions_proj_path = FORECASTS_DIR / "admission_volume_projections.csv"
    if admissions_proj_path.exists():
        proj_df = pl.read_csv(str(admissions_proj_path))
        plot_admission_scenarios(proj_df, FIGURES_DIR)
        export_frames.append(
            proj_df.rename({"projected_admissions": "forecast"}).with_columns([
                pl.lit("all").alias("disease"),
                pl.lit("admission_projection").alias("data_type"),
                pl.lit("PS-002").alias("source_ps"),
                pl.lit(today).alias("generated_on"),
            ])
        )

    # Validation summary
    pl.DataFrame(validation_rows).write_csv(str(RESULTS_DIR / "ps002_forecast_validation.csv"))
    logger.info("Forecast validation summary written.")

    # Export package
    if export_frames:
        export_df = pl.concat(export_frames, how="diagonal")
        export_df.write_csv(str(EXPORTS_DIR / "ps002_demand_projections_export.csv"))
        logger.info(f"Export package: {EXPORTS_DIR / 'ps002_demand_projections_export.csv'}")

    # Principal 2030 and 2035 admission values for findings
    proj_summary = {}
    if admissions_proj_path.exists():
        proj_df = pl.read_csv(str(admissions_proj_path))
        for yr in [2030, 2035]:
            for scen in ["principal", "high", "low"]:
                row = proj_df.filter(
                    (pl.col("year").cast(pl.Int32) == yr) & (pl.col("scenario") == scen)
                )
                if len(row) > 0:
                    proj_summary[f"{scen}_{yr}"] = round(float(row["projected_admissions"][0]))

    # Findings summary
    findings = f"""# PS-002 Forecast Findings Summary
Generated: {today}

## 1. Mortality Forecast Verdicts
{chr(10).join(
    f"- **{d.upper()}**: Best model = {r.get('model', 'N/A')}, "
    f"Hold-out MAPE = {r.get('mape_holdout', 'N/A')}% "
    f"({'Acceptable' if r.get('mape_acceptable') else 'EXCEEDS THRESHOLD'})"
    for d, r in zip(DISEASES, validation_rows) if r
)}

## 2. Admission Volume Range (2030)
- Low scenario: {proj_summary.get('low_2030', 'N/A'):,} admissions
- Principal scenario: {proj_summary.get('principal_2030', 'N/A'):,} admissions
- High scenario: {proj_summary.get('high_2030', 'N/A'):,} admissions

## 3. Admission Volume Range (2035)
- Low: {proj_summary.get('low_2035', 'N/A'):,} | Principal: {proj_summary.get('principal_2035', 'N/A'):,} | High: {proj_summary.get('high_2035', 'N/A'):,}

## 4. Model Performance Summary
| Disease | Model | MAPE | Acceptable |
|---------|-------|------|-----------|
{chr(10).join(
    f"| {r['disease']} | {r.get('model')} | {r.get('mape_holdout')} | {'Yes' if r.get('mape_acceptable') else 'No'} |"
    for r in validation_rows
)}

## 5. Limitations
- Only 3 diseases (cancer, stroke, IHD) modelled; communicable diseases excluded
- Admission rate held flat at 2019 — no disease-specific rate adjustment applied
- LTC admissions not modelled (sparse data, <50 records)
- Projections beyond 2030 have wide CIs — treat with caution

## 6. Handoff to PS-003
| File | Contents |
|------|---------|
| `models/forecasts/admission_volume_projections.csv` | 3-scenario admissions 2021–2035 |
| `results/exports/ps002_demand_projections_export.csv` | Merged mortality + admissions export |
| `results/tables/ps002_admission_sensitivity_2035.csv` | 9-cell sensitivity table for scenario comparison |
| `models/forecasts/mortality_*_forecast.csv` | Per-disease mortality forecasts 2020–2030 |
"""
    findings_path = EXPORTS_DIR / "ps002_forecast_findings.md"
    findings_path.write_text(findings, encoding="utf-8")
    logger.info(f"Findings summary: {findings_path}")
    logger.info("PS-002 forecast export complete.")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_forecast_visualization.py
import polars as pl
from pathlib import Path
import pytest


def test_plot_admission_scenarios_creates_file(tmp_path):
    from problem_statements.ps_002_disease_burden.src.forecast_visualization import (
        plot_admission_scenarios,
    )
    proj = pl.DataFrame({
        "year": [2021, 2022, 2021, 2022, 2021, 2022],
        "scenario": ["principal", "principal", "high", "high", "low", "low"],
        "projected_admissions": [100.0, 105.0, 110.0, 115.0, 90.0, 92.0],
    })
    plot_admission_scenarios(proj, tmp_path)
    assert (tmp_path / "ps002_admission_scenarios.png").exists()
```

---

### 5. Implementation Steps

- [ ] Create `src/forecast_visualization.py`
- [ ] Create `scripts/run_forecast_export.py`
- [ ] Run: `python scripts/run_forecast_export.py`
- [ ] Verify backtesting PNGs for each disease in `reports/figures/ps002_forecast/`
- [ ] Verify forward forecast PNGs with CI shading visible
- [ ] Verify `ps002_admission_scenarios.png` with 3 scenario lines
- [ ] Verify `ps002_forecast_validation.csv` has ≥3 rows
- [ ] Verify `ps002_demand_projections_export.csv` and `ps002_forecast_findings.md` written
- [ ] Run unit tests: `pytest tests/unit/test_forecast_visualization.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-002-story-07-forecast-export
git commit -m "feat(ps-002): add forecast_visualization module with CI-shaded charts"
git commit -m "feat(ps-002): add run_forecast_export orchestration and findings summary"
```
