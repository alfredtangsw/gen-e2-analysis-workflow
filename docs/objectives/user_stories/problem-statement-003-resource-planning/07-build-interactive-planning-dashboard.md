# User Story: 7 — Build Interactive Planning Dashboard

**As a** MOH executive sponsor,  
**I want** a self-contained, single-file interactive HTML dashboard that consolidates all PS-003 planning outputs across 6 tabs — with filters, charts, and summary tables —  
**so that** I can explore planning scenarios, review cost estimates, and share findings without needing any server infrastructure.

## 1. 🎯 Acceptance Criteria

The dashboard is a single HTML file saved to `results/exports/moh_integrated_resource_planning_dashboard.html`. It is self-contained (all JS, CSS, and data embedded inline — no external dependencies). It opens correctly in Chrome and Safari without any server.

**6 required tabs:**

| Tab | Title | Key Content |
|-----|-------|-------------|
| 1 | Executive Summary | 4 KPI cards (nurses gap 2030, beds gap 2030, cost estimate 2030, RAG status); system balance scorecard table; key findings bullets |
| 2 | Workforce Planning | Supply vs demand lines (nurses + doctors); hiring targets bar chart 2022–2035; scenario filter (principal / high / low) |
| 3 | Facility Capacity | Required vs trend supply beds (3 scenarios); commissioning milestones table; beds/10k comparison to WHO benchmark |
| 4 | Staff-Facility Alignment | Nurse:bed ratio heatmap (year × scenario); traffic-light legend; first divergence year callout |
| 5 | Cost Estimate | Annual incremental workforce cost bar chart; cumulative cost line; cost as % of 2018 expenditure; scope disclaimer banner |
| 6 | Scenario Comparison | Sensitivity table (9-cell: 3 demographic × 3 rate assumption) for 2035 admissions; side-by-side workforce gap under 3 scenarios |

## 2. 🔒 Technical Constraints

- Dashboard built with `plotly.graph_objects` — figures serialized to JSON via `fig.to_json()` and embedded in HTML template
- Tab switching implemented with pure JavaScript (no React, no jQuery) — show/hide `<div>` blocks
- All data read from Stories 01–06 output CSV files at build time — do not recalculate in dashboard script
- File size target: ≤ 5 MB (use `include_plotlyjs='cdn'` for Plotly JS to reduce file size; note: this requires an internet connection to open — document this)
- **Fallback**: if offline use is required, use `include_plotlyjs=True` (embedded) — document trade-off
- Scope disclaimer banner on Cost Estimate tab (Tab 5): "Budget estimates cover workforce costs only. Infrastructure and consumables are excluded due to absence of unit cost data."
- Chart title format: `"[MOH-SG | Resource Planning | {Tab}]"`
- Data last updated date embedded in the footer: `Generated: {today ISO date} | Data: Kaggle SG Health Dataset 2006–2020`

## 3. 📚 Domain Knowledge References

- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — dashboard tab structure, KPI card definitions, colour conventions
- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — KPI definitions for executive summary cards

## 4. 📦 Dependencies

- All Story 01–06 output files in `results/tables/` and `results/exports/`
- `plotly` — all chart generation
- `polars` — data loading for build step
- Standard library `string.Template` or f-strings — HTML assembly
- `kaleido` — NOT needed here (HTML output, not PNG)

## 5. ✅ Implementation Tasks

**Data Loading (build-time)**
- ⬜ Load all required CSV inputs using Polars; convert to Python dicts / list-of-dicts for JSON embedding

**Tab 1 — Executive Summary**
- ⬜ Compute 4 KPI values: nurses gap 2030, beds gap 2030, cumulative cost 2030, overall RAG (worst of scorecard KPIs)
- ⬜ Build KPI card HTML (4 cards with colour-coded background: red/amber/green)
- ⬜ Embed system balance scorecard as styled HTML table
- ⬜ Add 3–5 key findings bullet points (hard-coded from analysis outputs)

**Tab 2 — Workforce Planning**
- ⬜ Build Plotly figure: supply vs demand lines for nurses + doctors; add scenario filter using Plotly dropdown (updatemenus)
- ⬜ Build bar chart: annual hiring targets 2022–2035 per profession
- ⬜ Serialize both figures to JSON

**Tab 3 — Facility Capacity**
- ⬜ Build Plotly figure: 3-scenario lines + supply trend; commissioning trigger annotation
- ⬜ Add commissioning milestones as HTML table below chart

**Tab 4 — Staff-Facility Alignment**
- ⬜ Build Plotly heatmap from `ps003_staff_facility_alignment.csv`
- ⬜ Add traffic-light colour scale (discrete: red/amber/green)
- ⬜ Add "First divergence year" callout as HTML annotation below chart

**Tab 5 — Cost Estimate**
- ⬜ Build bar chart: annual cost by year and profession
- ⬜ Build line chart: cumulative cost trajectory
- ⬜ Add scope disclaimer banner as styled `<div>` at top of tab

**Tab 6 — Scenario Comparison**
- ⬜ Build Plotly table figure from `ps002_admission_sensitivity_2035.csv` (9-cell sensitivity)
- ⬜ Build side-by-side bar chart: workforce gap 2035 under 3 scenarios

**HTML Assembly**
- ⬜ Build HTML template with inline CSS for tabs; insert all figure JSONs and KPI card HTML
- ⬜ Add JavaScript for tab show/hide; add footer with data provenance and generation date
- ⬜ Write to `results/exports/moh_integrated_resource_planning_dashboard.html`

**Verification**
- ⬜ Open dashboard in browser; confirm all 6 tabs render without errors
- ⬜ Verify all charts display data (not empty)
- ⬜ Log file size to `logs/etl/ps003_dashboard_build.log`

## 6. Notes

- Using `include_plotlyjs='cdn'` is recommended for file size; document in the findings file that an internet connection is needed. For air-gapped environments, switch to embedded.
- The KPI cards in Tab 1 are the highest-read item in the dashboard — they must be correct and prominently styled.
- Tab ordering follows the analytical narrative: context (baseline) → workforce plan → facilities → alignment check → cost → scenario comparison. Do not reorder.
- The dashboard is the final handoff artefact for PS-003. Treat it as a stakeholder-facing product.

---

## Implementation Plan

### 1. Feature Overview

Build a single self-contained HTML dashboard with 6 tabs embedding Plotly charts (serialized to JSON), KPI cards, and styled HTML tables. Tab switching via pure JavaScript. All data read from Story 01–06 output CSVs at build time. Primary user: **MOH executive sponsor**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-003-healthcare-capacity/src/dashboard_builder.py
  - load_dashboard_data(results_dir, exports_dir, ps001_dir, ps002_dir) -> dict
  - build_kpi_cards_html(data) -> str
  - build_tab_html(tab_id, title, content_html) -> str
  - build_workforce_tab(data) -> tuple[str, list[str]]
  - build_facility_tab(data) -> tuple[str, list[str]]
  - build_alignment_tab(data) -> tuple[str, list[str]]
  - build_cost_tab(data) -> tuple[str, list[str]]
  - build_scenario_tab(data) -> tuple[str, list[str]]
  - render_dashboard(data, output_path) -> None

[CREATE] problem-statements/ps-003-healthcare-capacity/scripts/run_dashboard.py
  - Orchestrates dashboard build; writes HTML; logs file size
```

---

### 3. Code Generation Specifications

#### 3.1 `src/dashboard_builder.py`

```python
"""PS-003 interactive planning dashboard builder.

Produces a single self-contained HTML file with 6 tabs.
Plotly figures are serialized to JSON using fig.to_json() and embedded inline.
Tab switching: pure JavaScript show/hide of <div> blocks.
Plotly JS: include_plotlyjs='cdn' (requires internet connection to open dashboard).
"""

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import plotly.express as px
import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

CHART_TEMPLATE = "plotly_white"
GENERATED_ON = date.today().isoformat()
FOOTER_TEXT = (
    f"Generated: {GENERATED_ON} | Data: Kaggle SG Health Dataset 2006–2020 | "
    "MOH-SG Internal Use Only"
)
COST_DISCLAIMER = (
    "Budget estimates cover workforce costs only. Infrastructure and consumables are "
    "excluded due to absence of unit cost data."
)
PLOTLY_CDN = "https://cdn.plot.ly/plotly-latest.min.js"


CSS = """
body { font-family: Arial, sans-serif; margin: 0; background: #f5f6fa; color: #2c3e50; }
.header { background: #1a237e; color: white; padding: 18px 30px; }
.header h1 { margin: 0; font-size: 20px; }
.tab-bar { background: #283593; display: flex; }
.tab-btn { color: #ccc; border: none; background: transparent; padding: 12px 24px;
           font-size: 14px; cursor: pointer; }
.tab-btn.active { color: white; border-bottom: 3px solid #64b5f6; font-weight: bold; }
.tab-content { display: none; padding: 24px; }
.tab-content.active { display: block; }
.kpi-row { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.kpi-card { flex: 1; min-width: 160px; background: white; border-radius: 6px;
            padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); text-align: center; }
.kpi-card .value { font-size: 28px; font-weight: bold; margin: 8px 0; }
.kpi-card .label { font-size: 11px; color: #777; text-transform: uppercase; }
.kpi-card.red { border-top: 4px solid #e74c3c; }
.kpi-card.amber { border-top: 4px solid #f39c12; }
.kpi-card.green { border-top: 4px solid #27ae60; }
.kpi-card.blue { border-top: 4px solid #2980b9; }
table.data-table { width: 100%; border-collapse: collapse; background: white;
                   box-shadow: 0 1px 4px rgba(0,0,0,0.1); border-radius: 6px; }
table.data-table th { background: #283593; color: white; padding: 10px 14px;
                      font-size: 12px; text-align: left; }
table.data-table td { padding: 8px 14px; border-bottom: 1px solid #eee; font-size: 12px; }
table.data-table tr:last-child td { border-bottom: none; }
.disclaimer-banner { background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px;
                     padding: 12px 16px; margin-bottom: 16px; font-size: 13px; color: #856404; }
.footer { text-align: center; padding: 12px; font-size: 11px; color: #888;
          border-top: 1px solid #ddd; margin-top: 24px; }
"""

JS = """
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + tabId).classList.add('active');
    document.querySelector('[data-tab="' + tabId + '"]').classList.add('active');
}
window.onload = function() { showTab(1); };
"""


def _fig_json(fig: go.Figure) -> str:
    """Serialize Plotly figure to JSON string for embedding."""
    return fig.to_json()


def _embed_chart(fig: go.Figure, div_id: str) -> str:
    """Produce an HTML snippet that renders a Plotly figure in a div."""
    fig_json = _fig_json(fig)
    return f'<div id="{div_id}"></div><script>Plotly.newPlot("{div_id}", {fig_json});</script>'


def load_dashboard_data(
    ps003_results_dir: Path,
    ps003_exports_dir: Path,
    ps001_results_dir: Path,
    ps002_forecasts_dir: Path,
    ps002_results_dir: Path,
) -> dict[str, Any]:
    """Load all required CSV outputs at dashboard build time.

    Args:
        ps003_results_dir: PS-003 results/tables/ directory
        ps003_exports_dir: PS-003 results/exports/ directory
        ps001_results_dir: PS-001 results/tables/ directory
        ps002_forecasts_dir: PS-002 models/forecasts/ directory
        ps002_results_dir: PS-002 results/tables/ directory

    Returns:
        Dict of named DataFrames; missing files log a warning and return empty DataFrame
    """
    def safe_read_csv(path: Path, name: str) -> pl.DataFrame:
        if path.exists():
            return pl.read_csv(str(path))
        logger.warning(f"Dashboard data missing: {path} ({name})")
        return pl.DataFrame()

    return {
        "scorecard": safe_read_csv(ps001_results_dir / "system_balance_scorecard.csv", "scorecard"),
        "workforce_gap": safe_read_csv(ps003_results_dir / "ps003_workforce_gap_timeseries.csv", "workforce_gap"),
        "workforce_gap_milestone": safe_read_csv(ps003_results_dir / "ps003_workforce_gap.csv", "gap_milestone"),
        "supply_projections": safe_read_csv(ps003_results_dir / "ps003_workforce_supply_projections.csv", "supply"),
        "bed_gap": safe_read_csv(ps003_results_dir / "ps003_bed_gap.csv", "bed_gap"),
        "commissioning_milestones": safe_read_csv(ps003_results_dir / "ps003_commissioning_milestones.csv", "commissioning"),
        "alignment": safe_read_csv(ps003_results_dir / "ps003_staff_facility_alignment.csv", "alignment"),
        "cost": safe_read_csv(ps003_results_dir / "ps003_workforce_cost.csv", "cost"),
        "cost_summary": safe_read_csv(ps003_exports_dir / "ps003_cost_summary.csv", "cost_summary"),
        "admission_sensitivity": safe_read_csv(ps002_results_dir / "ps002_admission_sensitivity_2035.csv", "sensitivity"),
        "admission_projections": safe_read_csv(ps002_forecasts_dir / "admission_volume_projections.csv", "admissions"),
    }


def _kpi_card(value: str, label: str, colour: str = "blue") -> str:
    return (
        f'<div class="kpi-card {colour}">'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'</div>'
    )


def _df_to_html_table(df: pl.DataFrame, cols: list[str] | None = None) -> str:
    if len(df) == 0:
        return "<p><em>Data not available</em></p>"
    display_df = df.select(cols) if cols else df
    header = "".join(f"<th>{c}</th>" for c in display_df.columns)
    rows = ""
    for row in display_df.to_dicts():
        cells = "".join(f"<td>{v}</td>" for v in row.values())
        rows += f"<tr>{cells}</tr>"
    return f'<table class="data-table"><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>'


def build_executive_tab(data: dict) -> str:
    """Tab 1 — Executive Summary."""
    # KPI values
    gap_df = data["workforce_gap_milestone"]
    nurses_2030_gap = "N/A"
    beds_2030_gap = "N/A"
    cost_2030 = "N/A"
    overall_rag = "N/A"

    if len(gap_df) > 0:
        n_row = gap_df.filter(
            (pl.col("year").cast(pl.Int32) == 2030) & (pl.col("profession") == "nurses")
        )
        if len(n_row) > 0:
            g = int(n_row["gap"][0])
            nurses_2030_gap = f"{g:+,}"

    bed_df = data["bed_gap"]
    if len(bed_df) > 0:
        b_row = bed_df.filter(
            (pl.col("year").cast(pl.Int32) == 2030) & (pl.col("scenario") == "principal")
        )
        if len(b_row) > 0:
            bg = int(b_row["gap"][0])
            beds_2030_gap = f"{bg:+,}"

    cost_df = data["cost_summary"]
    if len(cost_df) > 0:
        c_row = cost_df.filter(pl.col("year").cast(pl.Int32) == 2030)
        if len(c_row) > 0:
            total = float(c_row["annual_cost_sgd_m"].sum())
            cost_2030 = f"SGD {total:.0f}M"

    scorecard = data["scorecard"]
    if len(scorecard) > 0 and "rag_status" in scorecard.columns:
        rag_counts = scorecard["rag_status"].value_counts()
        worst = "red" if "red" in scorecard["rag_status"].to_list() else \
                "amber" if "amber" in scorecard["rag_status"].to_list() else "green"
        overall_rag = f"{worst.upper()} ({rag_counts.shape[0]} KPIs assessed)"

    kpis = (
        _kpi_card(nurses_2030_gap, "Nurses Gap 2030", "red" if nurses_2030_gap.startswith("-") else "green") +
        _kpi_card(beds_2030_gap, "Beds Gap 2030 (Principal)", "red" if beds_2030_gap.startswith("-") or (beds_2030_gap not in ("N/A",) and int(beds_2030_gap.replace("+", "").replace(",", "")) > 0) else "green") +
        _kpi_card(cost_2030, "Annual Workforce Cost 2030", "amber") +
        _kpi_card(overall_rag, "System Balance RAG", "red" if "RED" in overall_rag else "amber" if "AMBER" in overall_rag else "green")
    )

    scorecard_html = _df_to_html_table(scorecard, ["kpi_label", "singapore_2018", "who_searo_benchmark", "gap_pct", "rag_status"]) if len(scorecard) > 0 else "<p>Scorecard data unavailable</p>"

    findings = """
    <ul>
      <li>Singapore's 2018 nurse density is below the WHO SEARO benchmark, indicating a systemic workforce gap.</li>
      <li>Under the principal demographic scenario, required hospital beds exceed current trend supply by 2027–2029.</li>
      <li>Closing the nurse shortfall by 2030 requires incremental annual workforce spending of ~SGD 100–400M.</li>
      <li>Staff-facility alignment remains adequate through mid-2020s; deterioration accelerates post-2028 under high-growth scenario.</li>
      <li>Planning for new hospital commissioning should commence by 2025 to meet 2030 demand.</li>
    </ul>"""

    return f'<div class="kpi-row">{kpis}</div><h3>System Balance Scorecard (2018)</h3>{scorecard_html}<h3>Key Findings</h3>{findings}'


def render_dashboard(data: dict, output_path: Path) -> None:
    """Assemble all tabs into a single HTML file and write to disk.

    Args:
        data: Dict of DataFrames from load_dashboard_data
        output_path: Path for the output HTML file
    """
    # Build per-tab content
    tab_defs = [
        (1, "Executive Summary", build_executive_tab(data)),
        (2, "Workforce Planning", _build_workforce_tab_content(data)),
        (3, "Facility Capacity", _build_facility_tab_content(data)),
        (4, "Staff-Facility Alignment", _build_alignment_tab_content(data)),
        (5, "Cost Estimate", _build_cost_tab_content(data)),
        (6, "Scenario Comparison", _build_scenario_tab_content(data)),
    ]

    tab_buttons = "".join(
        f'<button class="tab-btn" data-tab="{tid}" onclick="showTab({tid})">{title}</button>'
        for tid, title, _ in tab_defs
    )
    tab_contents = "".join(
        f'<div class="tab-content" id="tab-{tid}"><h2>{title}</h2>{content}</div>'
        for tid, title, content in tab_defs
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MOH-SG Integrated Resource Planning Dashboard</title>
<script src="{PLOTLY_CDN}"></script>
<style>{CSS}</style>
</head>
<body>
<div class="header"><h1>MOH-SG | Integrated Healthcare Resource Planning Dashboard [DRAFT]</h1></div>
<div class="tab-bar">{tab_buttons}</div>
{tab_contents}
<div class="footer">{FOOTER_TEXT}</div>
<script>{JS}</script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    size_kb = output_path.stat().st_size / 1024
    logger.info(f"Dashboard written: {output_path} ({size_kb:.0f} KB)")
    if size_kb > 5120:
        logger.warning("Dashboard exceeds 5 MB target — consider switching to embedded Plotly JS")


def _build_workforce_tab_content(data: dict) -> str:
    gap = data["workforce_gap"]
    if len(gap) == 0:
        return "<p>Workforce gap data unavailable.</p>"

    # Supply vs demand chart
    fig = go.Figure()
    for profession in ["nurses", "doctors"]:
        sub = gap.filter(pl.col("profession") == profession).sort("year").to_pandas()
        if len(sub) == 0:
            continue
        fig.add_trace(go.Scatter(x=sub["year"], y=sub["supply"], name=f"{profession.title()} Supply", mode="lines"))
        fig.add_trace(go.Scatter(x=sub["year"], y=sub["demand"], name=f"{profession.title()} Demand", mode="lines", line={"dash": "dash"}))

    fig.update_layout(
        title="[MOH-SG | Resource Planning | Workforce] Supply vs Demand",
        template=CHART_TEMPLATE, width=1100, height=500,
    )

    # Hiring targets bar
    milestone = data["workforce_gap_milestone"]
    fig2 = go.Figure()
    if len(milestone) > 0 and "hiring_target_annual" in milestone.columns:
        for profession in ["nurses", "doctors"]:
            sub = milestone.filter(pl.col("profession") == profession).sort("year").to_pandas()
            if len(sub) > 0:
                fig2.add_trace(go.Bar(x=sub["year"].astype(str), y=sub["hiring_target_annual"], name=profession.title()))
        fig2.update_layout(
            title="[MOH-SG | Resource Planning | Workforce] Annual Hiring Targets",
            barmode="group", template=CHART_TEMPLATE, width=1100, height=400,
        )

    return _embed_chart(fig, "chart-workforce") + _embed_chart(fig2, "chart-hiring")


def _build_facility_tab_content(data: dict) -> str:
    bed_gap = data["bed_gap"]
    milestones = data["commissioning_milestones"]
    if len(bed_gap) == 0:
        return "<p>Bed gap data unavailable.</p>"

    fig = go.Figure()
    for scenario in ["principal", "high", "low"]:
        sub = bed_gap.filter(pl.col("scenario") == scenario).sort("year").to_pandas()
        if len(sub) > 0:
            fig.add_trace(go.Scatter(x=sub["year"], y=sub["required_beds"], mode="lines", name=f"Required ({scenario.title()})"))
    if "trend_supply_beds" in bed_gap.columns:
        supply = bed_gap.filter(pl.col("scenario") == "principal").sort("year").to_pandas()
        fig.add_trace(go.Scatter(x=supply["year"], y=supply["trend_supply_beds"], mode="lines", name="Trend Supply", line={"dash": "dash", "color": "grey"}))
    fig.update_layout(
        title="[MOH-SG | Resource Planning | Facility] Bed Capacity Gap",
        template=CHART_TEMPLATE, width=1100, height=500,
    )

    milestones_html = _df_to_html_table(milestones) if len(milestones) > 0 else "<p>Commissioning milestones unavailable</p>"
    return _embed_chart(fig, "chart-beds") + "<h3>Commissioning Milestones</h3>" + milestones_html


def _build_alignment_tab_content(data: dict) -> str:
    alignment = data["alignment"]
    if len(alignment) == 0:
        return "<p>Alignment data unavailable.</p>"

    rag_map = {"green": 2, "amber": 1, "red": 0}
    aligned = alignment
    if "rag_status" in aligned.columns:
        aligned = aligned.with_columns(
            pl.col("rag_status").replace(rag_map).alias("rag_int")
        )

    scenarios = sorted(aligned["scenario"].unique().to_list()) if "scenario" in aligned.columns else []
    years = sorted(aligned["year"].unique().cast(pl.Int32).to_list()) if "year" in aligned.columns else []

    if scenarios and years and "rag_int" in aligned.columns:
        matrix = []
        for s in scenarios:
            row = []
            for y in years:
                c = aligned.filter((pl.col("scenario") == s) & (pl.col("year").cast(pl.Int32) == y))["rag_int"]
                row.append(int(c[0]) if len(c) > 0 else -1)
            matrix.append(row)

        fig = go.Figure(go.Heatmap(
            z=matrix, x=years, y=scenarios,
            colorscale=[[0, "#E74C3C"], [0.5, "#F39C12"], [1, "#27AE60"]],
            zmin=0, zmax=2,
            colorbar={"tickvals": [0, 1, 2], "ticktext": ["Red", "Amber", "Green"]},
        ))
        fig.update_layout(
            title="[MOH-SG | Resource Planning | Alignment] Nurse:Bed Ratio RAG",
            template=CHART_TEMPLATE, width=1100, height=400,
        )
        return _embed_chart(fig, "chart-alignment")

    return "<p>Insufficient alignment data to build heatmap.</p>"


def _build_cost_tab_content(data: dict) -> str:
    cost = data["cost"]
    disclaimer = f'<div class="disclaimer-banner">{COST_DISCLAIMER}</div>'
    if len(cost) == 0:
        return disclaimer + "<p>Cost data unavailable.</p>"

    fig = go.Figure()
    for profession in ["nurses", "doctors"]:
        sub = cost.filter(pl.col("profession") == profession).sort("year").to_pandas()
        if len(sub) > 0:
            fig.add_trace(go.Bar(x=sub["year"].astype(str), y=sub.get("annual_cost_sgd_m", []), name=profession.title()))
    fig.update_layout(
        title="[MOH-SG | Resource Planning | Cost] Annual Incremental Workforce Cost (SGD M)",
        barmode="stack", template=CHART_TEMPLATE, width=1100, height=450,
    )

    # Cumulative line
    fig2 = go.Figure()
    if "cumulative_cost_sgd_m" in cost.columns:
        for profession in ["nurses", "doctors"]:
            sub = cost.filter(pl.col("profession") == profession).sort("year").to_pandas()
            if len(sub) > 0:
                fig2.add_trace(go.Scatter(x=sub["year"], y=sub["cumulative_cost_sgd_m"], mode="lines+markers", name=profession.title()))
    fig2.update_layout(
        title="[MOH-SG | Resource Planning | Cost] Cumulative Workforce Cost (SGD M)",
        template=CHART_TEMPLATE, width=1100, height=400,
    )

    return disclaimer + _embed_chart(fig, "chart-cost-annual") + _embed_chart(fig2, "chart-cost-cumulative")


def _build_scenario_tab_content(data: dict) -> str:
    sensitivity = data["admission_sensitivity"]
    admissions = data["admission_projections"]

    content = ""
    if len(sensitivity) > 0:
        sens_html = _df_to_html_table(sensitivity)
        content += f"<h3>2035 Admission Volume Sensitivity (3 Demographic × 3 Rate Scenarios)</h3>{sens_html}"

    if len(admissions) > 0 and "scenario" in admissions.columns:
        fig = go.Figure()
        for scenario in ["principal", "high", "low"]:
            sub = admissions.filter(pl.col("scenario") == scenario).sort("year").to_pandas()
            if len(sub) > 0:
                fig.add_trace(go.Scatter(x=sub["year"], y=sub.get("projected_admissions", []), mode="lines+markers", name=scenario.title()))
        fig.update_layout(
            title="[MOH-SG | Resource Planning | Scenarios] Projected Admissions 2021–2035",
            template=CHART_TEMPLATE, width=1100, height=450,
        )
        content += _embed_chart(fig, "chart-scenarios")

    return content or "<p>Scenario data unavailable.</p>"
```

#### 3.2 `scripts/run_dashboard.py`

```python
"""PS-003 Story 07 — Build Interactive Planning Dashboard.

Run: python problem-statements/ps-003-healthcare-capacity/scripts/run_dashboard.py
"""

import sys
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_003_healthcare_capacity.src.dashboard_builder import (
    load_dashboard_data,
    render_dashboard,
)

PS001_DIR = PROJECT_ROOT / "problem-statements" / "ps-001-healthcare-system-baseline"
PS002_DIR = PROJECT_ROOT / "problem-statements" / "ps-002-disease-burden"
PS_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PS_DIR / "results" / "tables"
EXPORTS_DIR = PS_DIR / "results" / "exports"
LOG_DIR = PS_DIR / "logs" / "etl"
OUTPUT_PATH = EXPORTS_DIR / "moh_integrated_resource_planning_dashboard.html"

LOG_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
logger.add(str(LOG_DIR / "ps003_dashboard_build.log"), level="INFO", rotation="10 MB")


def main() -> None:
    logger.info("=== PS-003 Story 07: Interactive Dashboard Build ===")

    data = load_dashboard_data(
        ps003_results_dir=RESULTS_DIR,
        ps003_exports_dir=EXPORTS_DIR,
        ps001_results_dir=PS001_DIR / "results" / "tables",
        ps002_forecasts_dir=PS002_DIR / "models" / "forecasts",
        ps002_results_dir=PS002_DIR / "results" / "tables",
    )

    render_dashboard(data, OUTPUT_PATH)

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    logger.info(f"Dashboard complete: {OUTPUT_PATH} | Size: {size_kb:.0f} KB")
    logger.info(f"Note: Dashboard uses Plotly CDN — internet connection required to open.")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_dashboard_builder.py
from pathlib import Path
import polars as pl


def test_render_dashboard_creates_file(tmp_path):
    from problem_statements.ps_003_healthcare_capacity.src.dashboard_builder import render_dashboard
    data = {
        "scorecard": pl.DataFrame(),
        "workforce_gap": pl.DataFrame(),
        "workforce_gap_milestone": pl.DataFrame(),
        "supply_projections": pl.DataFrame(),
        "bed_gap": pl.DataFrame(),
        "commissioning_milestones": pl.DataFrame(),
        "alignment": pl.DataFrame(),
        "cost": pl.DataFrame(),
        "cost_summary": pl.DataFrame(),
        "admission_sensitivity": pl.DataFrame(),
        "admission_projections": pl.DataFrame(),
    }
    out = tmp_path / "dashboard.html"
    render_dashboard(data, out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Executive Summary" in content
    assert "Workforce Planning" in content
    assert "Plotly" in content or "plotly" in content


def test_render_dashboard_has_6_tabs(tmp_path):
    from problem_statements.ps_003_healthcare_capacity.src.dashboard_builder import render_dashboard
    data = {k: pl.DataFrame() for k in [
        "scorecard", "workforce_gap", "workforce_gap_milestone", "supply_projections",
        "bed_gap", "commissioning_milestones", "alignment", "cost", "cost_summary",
        "admission_sensitivity", "admission_projections",
    ]}
    out = tmp_path / "dashboard.html"
    render_dashboard(data, out)
    content = out.read_text(encoding="utf-8")
    for tab in ["Executive Summary", "Workforce Planning", "Facility Capacity",
                "Staff-Facility Alignment", "Cost Estimate", "Scenario Comparison"]:
        assert tab in content, f"Tab '{tab}' not found in dashboard HTML"
```

---

### 5. Implementation Steps

- [ ] Create `src/dashboard_builder.py`
- [ ] Create `scripts/run_dashboard.py`
- [ ] Ensure all Story 01–06 output CSVs exist (run in order)
- [ ] Run: `python scripts/run_dashboard.py`
- [ ] Open `results/exports/moh_integrated_resource_planning_dashboard.html` in browser
- [ ] Click each tab — confirm all 6 render without JavaScript errors
- [ ] Verify charts display data in tabs 2–6
- [ ] Check dashboard file size — log confirms ≤ 5 MB (CDN mode)
- [ ] Note in findings: "Requires internet connection to open (Plotly CDN)"
- [ ] Run unit tests: `pytest tests/unit/test_dashboard_builder.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-003-story-07-dashboard
git commit -m "feat(ps-003): add dashboard_builder with 6-tab HTML dashboard and embedded Plotly"
git commit -m "feat(ps-003): add run_dashboard script and dashboard build log"
```
