# Build Health Equity Monitor Dashboard (Lifecycle Stage: Visualization)

**Story ID**: PS-005-US-09  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P0 (Critical)  
**Effort Estimate**: L (7-8 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Population Health Strategist monitoring health equity progress**,  
I want **an interactive dashboard displaying utilization/outcome disparities, temporal equity trends, and priority populations**,  
So that **I can track equity metrics, identify emerging disparities, and communicate equity gaps to policymakers and stakeholders**.

---

## 🎯 Acceptance Criteria

1. **Core visualizations**
   - Disparity overview: rate ratios by demographic
   - Utilization patterns: demographic breakdowns
   - Outcome disparities: mortality/disease burden gaps
   - Temporal trends: equity progress over time
   - Priority populations: vulnerability matrix

2. **Interactive features**
   - Demographic selector: age group, sex
   - Metric toggle: utilization vs outcomes
   - Time period selector
   - Disparity threshold filters
   - Priority population drill-down

3. **User experience**
   - Responsive design
   - Tooltips with metrics
   - Export capabilities
   - Auto-generated insights
   - Help documentation

4. **Deployment**
   - Dashboard deployed and accessible
   - User documentation
   - Code documentation

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9; Dash/Plotly on cloud
- **Primary Library**: Plotly Dash
- **Data Backend**: Polars 0.20+
- **Visualization**: Plotly
- **Logging**: loguru
- **Testing**: pytest ≥80% coverage

---

## 📚 Domain Knowledge References

- [Problem Statement PS-005](../../../problem_statements/ps-005-healthcare-equity-disparities.md) - Dashboard objectives

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`, `plotly>=5.18.0`, `dash>=2.14.0`, `dash-bootstrap-components>=1.5.0`, `gunicorn>=21.0.0`, `loguru>=0.7.0`

### Internal Dependencies
- **Upstream**: PS-005-US-03 through PS-005-US-08 (All analyses - BLOCKING)
- **Data Sources**: All PS-005 results tables
- **Config Files**: `config/dashboard.yml`

---

## ✅ Implementation Tasks

### Dashboard Architecture
- [ ] Initialize Dash app
- [ ] Multi-tab layout: Overview, Utilization, Outcomes, Trends, Priorities
- [ ] Data loading and caching
- [ ] Component hierarchy

### Core Visualizations
- [ ] Disparity charts: rate ratios
- [ ] Demographic profiles
- [ ] Lorenz curves
- [ ] Trend lines
- [ ] Priority matrix

### Interactive Features
- [ ] Demographic filters
- [ ] Metric toggles
- [ ] Time period slider
- [ ] Disparity threshold selector
- [ ] Priority drill-down

### Data Callbacks
- [ ] Filter data
- [ ] Update charts
- [ ] Generate narratives
- [ ] Export functionality

### Styling & UX
- [ ] Bootstrap theme
- [ ] Tooltips
- [ ] Loading indicators
- [ ] Error handling

### Deployment
- [ ] Dockerize
- [ ] Deploy to cloud
- [ ] HTTPS and authentication
- [ ] Performance optimization

### Testing & Documentation
- [ ] Unit tests
- [ ] Integration tests
- [ ] User guide
- [ ] Technical documentation

---

## 📌 Notes

**Dashboard Tabs**:
1. **Overview**: Key equity metrics, summary
2. **Utilization**: Utilization disparities by demographics
3. **Outcomes**: Outcome disparities
4. **Trends**: Temporal equity progress
5. **Priorities**: Vulnerable populations and recommendations
6. **About**: Methodology, definitions

**Key Features**:
- **Disparity Alerts**: Red flags for disparities >50% (rate ratio >1.5 or <0.67)
- **Trend Indicators**: Up/down arrows for improving/worsening equity
- **Priority Filter**: Focus on top priority populations
- **Comparator**: Select reference group for disparity calculations

**Success Metrics**:
- Dashboard loads <3 seconds
- Interactive updates <1 second
- Mobile responsive
- Positive stakeholder feedback

---

## Implementation Plan

### 1. Feature Overview

Build an interactive Plotly Dash multi-tab dashboard displaying all PS-005 equity analysis results: disparity overview, utilisation patterns, outcome gaps, temporal equity trends, and priority population matrix. The dashboard reads from pre-computed results CSVs and parquet files and enables stakeholders to explore equity gaps by demographic dimension, metric, and time period.

**Primary User Role**: Population Health Strategist monitoring health equity progress

**Key Deliverable**: `problem-statements/ps-005-healthcare-equity-disparities/dashboard/app.py` — a self-contained Dash application executable locally, with all tabs and callbacks wired.

---

### 2. Component Analysis & Reuse Strategy

| Component | Action | Justification |
|-----------|--------|---------------|
| All `results/tables/*.csv` | Reuse | Pre-computed outputs from US-03 through US-08 |
| `equity_analysis_integrated.parquet` | Reuse | Backbone for interactive disparity plots |
| `dash`, `plotly`, `dash-bootstrap-components` | Reuse (installed) | UI framework in requirements.txt |
| `dashboard/app.py` | **Create** | Main Dash app entry point |
| `dashboard/data_loader.py` | **Create** | Cached data loading utilities |
| `dashboard/callbacks.py` | **Create** | All Dash callback logic (separated for testability) |
| `dashboard/layout.py` | **Create** | Tab layout definitions |
| `tests/unit/test_data_loader.py` | **Create** | Unit tests for data loading |

---

### 3. ML Model Evaluation & Selection

Not applicable — visualisation/dashboard story.

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/dashboard/app.py`**
  - Entry point; initialises Dash app and server
  - Imports layout from `layout.py`, registers callbacks from `callbacks.py`

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/dashboard/data_loader.py`**
  - Functions: `load_all_equity_data(results_dir: Path) -> dict[str, pl.DataFrame]`, `get_demographic_options(df: pl.DataFrame) -> list[dict]`
  - Uses `functools.lru_cache` for in-process caching

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/dashboard/layout.py`**
  - Function: `build_layout() -> dbc.Container`
  - Five tabs: Overview, Utilisation Disparities, Outcome Gaps, Temporal Trends, Priority Populations

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/dashboard/callbacks.py`**
  - Registers all `@app.callback` handlers for each tab's interactive elements

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_data_loader.py`**

---

### 5. Data Pipeline (Dashboard Backend)

**Data sources** (all pre-computed, read-only):
| File | Used in Tab |
|------|-------------|
| `equity_analysis_integrated.parquet` | Utilisation, Outcome |
| `results/tables/utilization_disparity_analysis.csv` | Overview, Utilisation |
| `results/tables/outcome_disparity_analysis.csv` | Outcome Gaps |
| `results/tables/equity_temporal_trends.csv` | Temporal Trends |
| `results/tables/equity_disparity_metrics.csv` | Overview |
| `results/tables/equity_barrier_diagnosis.csv` | Priority Populations |
| `results/tables/vulnerable_population_priorities.csv` | Priority Populations |

**Data loading**: All files loaded on app startup via `load_all_equity_data()` into an in-memory dict. Flask/Dash serves from this cached dict. No database or live query needed given small data size (~few hundred rows).

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/dashboard/data_loader.py

from pathlib import Path
from functools import lru_cache
from typing import Any

import polars as pl
from loguru import logger


EXPECTED_FILES: dict[str, str] = {
    "integrated": "shared/data/3_interim/equity_analysis_integrated.parquet",
    "utilization_disparity": "results/tables/utilization_disparity_analysis.csv",
    "outcome_disparity": "results/tables/outcome_disparity_analysis.csv",
    "temporal_trends": "results/tables/equity_temporal_trends.csv",
    "disparity_metrics": "results/tables/equity_disparity_metrics.csv",
    "barrier_diagnosis": "results/tables/equity_barrier_diagnosis.csv",
    "priority_populations": "results/tables/vulnerable_population_priorities.csv",
}


def load_all_equity_data(project_root: Path) -> dict[str, pl.DataFrame]:
    """
    Load all equity analysis artefacts into memory.

    Args:
        project_root: Absolute path to the project workspace root.

    Returns:
        Dict mapping data key to loaded DataFrame. Missing files are logged
        as warnings and excluded from the result (dashboard degrades gracefully).
    """
    data: dict[str, pl.DataFrame] = {}
    for key, rel_path in EXPECTED_FILES.items():
        full_path = project_root / rel_path
        if not full_path.exists():
            logger.warning(f"Data file not found (tab will be disabled): {full_path}")
            continue
        try:
            if full_path.suffix == ".parquet":
                df = pl.read_parquet(full_path)
            else:
                df = pl.read_csv(full_path)
            data[key] = df
            logger.info(f"Loaded '{key}': {df.shape[0]} rows")
        except Exception as exc:
            logger.error(f"Failed to load '{key}' from {full_path}: {exc}")
    return data


def get_demographic_options(df: pl.DataFrame, col: str = "demographic_group") -> list[dict[str, str]]:
    """
    Build Dash dropdown options from unique values in a demographic column.

    Args:
        df: DataFrame containing the column.
        col: Column name for demographic groups.

    Returns:
        List of {"label": ..., "value": ...} dicts for Dash dropdowns.
    """
    if col not in df.columns:
        return []
    unique_vals = sorted(df[col].unique().to_list())
    return [{"label": v, "value": v} for v in unique_vals]
```

```python
# problem-statements/ps-005-healthcare-equity-disparities/dashboard/layout.py

import dash_bootstrap_components as dbc
from dash import dcc, html


def build_layout() -> dbc.Container:
    """Build the full multi-tab dashboard layout."""
    return dbc.Container(
        fluid=True,
        children=[
            dbc.Row(
                dbc.Col(
                    html.H1(
                        "Singapore Health Equity Monitor",
                        className="text-center my-3",
                        style={"color": "#2166ac", "fontWeight": "bold"},
                    )
                )
            ),
            dbc.Row(
                dbc.Col(
                    html.P(
                        "Healthcare access and outcome disparities by age group and sex — 2006–2020",
                        className="text-center text-muted mb-3",
                    )
                )
            ),
            dbc.Tabs(
                id="main-tabs",
                active_tab="tab-overview",
                children=[
                    dbc.Tab(label="Overview", tab_id="tab-overview"),
                    dbc.Tab(label="Utilisation Disparities", tab_id="tab-utilisation"),
                    dbc.Tab(label="Outcome Gaps", tab_id="tab-outcomes"),
                    dbc.Tab(label="Temporal Trends", tab_id="tab-trends"),
                    dbc.Tab(label="Priority Populations", tab_id="tab-priorities"),
                ],
            ),
            html.Div(id="tab-content", className="mt-4"),
        ],
    )
```

```python
# problem-statements/ps-005-healthcare-equity-disparities/dashboard/app.py

from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output
from loguru import logger

from dashboard.layout import build_layout
from dashboard.data_loader import load_all_equity_data
from dashboard import callbacks  # registers all callbacks via import

# ── Project root detection ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # adjust depth to workspace root

# ── App initialisation ─────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Health Equity Monitor — Singapore",
    suppress_callback_exceptions=True,
)
server = app.server  # expose Flask server for deployment

# ── Data loading ───────────────────────────────────────────────────────────
DATA = load_all_equity_data(PROJECT_ROOT)
logger.info(f"Dashboard data loaded: {list(DATA.keys())}")

# ── Layout ─────────────────────────────────────────────────────────────────
app.layout = build_layout()


# ── Tab switcher callback ──────────────────────────────────────────────────
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab"),
)
def render_tab_content(active_tab: str) -> dash.development.base_component.Component:
    """Render content for the active tab."""
    from dashboard.callbacks import (
        render_overview,
        render_utilisation,
        render_outcomes,
        render_trends,
        render_priorities,
    )
    tab_renderers = {
        "tab-overview": render_overview,
        "tab-utilisation": render_utilisation,
        "tab-outcomes": render_outcomes,
        "tab-trends": render_trends,
        "tab-priorities": render_priorities,
    }
    renderer = tab_renderers.get(active_tab)
    if renderer is None:
        return dash.html.P("Tab not found")
    return renderer(DATA)


if __name__ == "__main__":
    app.run(debug=True, port=8050)
```

```python
# problem-statements/ps-005-healthcare-equity-disparities/dashboard/callbacks.py

from typing import Any

import plotly.express as px
import polars as pl
from dash import dcc, html
import dash_bootstrap_components as dbc


def _empty_tab(message: str) -> html.Div:
    """Return a placeholder when data is unavailable for a tab."""
    return html.Div(
        dbc.Alert(f"{message} — run upstream analysis steps first.",
                  color="warning"),
        className="p-4",
    )


def render_overview(data: dict[str, pl.DataFrame]) -> html.Div:
    """Overview tab: KPI cards and disparity summary bar chart."""
    if "utilization_disparity" not in data:
        return _empty_tab("Utilisation disparity data not available")

    df = data["utilization_disparity"]
    max_ratio = float(df["mean_rate_ratio"].max())
    min_ratio = float(df["mean_rate_ratio"].min())
    n_flagged = int(df.filter(pl.col("years_flagged") > 0).shape[0])

    kpi_cards = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4(f"{max_ratio:.2f}×", className="text-danger"),
                html.P("Maximum rate ratio", className="text-muted"),
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4(f"{min_ratio:.2f}×", className="text-primary"),
                html.P("Minimum rate ratio", className="text-muted"),
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4(str(n_flagged), className="text-warning"),
                html.P("Groups with significant disparity", className="text-muted"),
            ])
        ]), width=3),
    ], className="mb-4")

    fig = px.bar(
        df.sort("mean_rate_ratio").to_pandas(),
        x="mean_rate_ratio",
        y="demographic_group",
        orientation="h",
        title="Mean Utilisation Rate Ratio by Age Group",
        labels={"mean_rate_ratio": "Rate Ratio (vs reference)", "demographic_group": "Age Group"},
        color="mean_rate_ratio",
        color_continuous_scale="RdBu_r",
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color="black", annotation_text="Equity")

    return html.Div([kpi_cards, dcc.Graph(figure=fig)])


def render_utilisation(data: dict[str, pl.DataFrame]) -> html.Div:
    """Utilisation Disparities tab: time-series line chart by demographic group."""
    if "integrated" not in data:
        return _empty_tab("Integrated equity data not available")

    df = (
        data["integrated"]
        .filter(pl.col("demographic_type") == "age_group")
        .to_pandas()
    )
    fig = px.line(
        df,
        x="year",
        y="rate_ratio",
        color="demographic_group",
        markers=True,
        title="Utilisation Rate Ratio Over Time by Age Group",
        labels={"rate_ratio": "Rate Ratio", "year": "Year"},
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="black", annotation_text="Equity")
    return html.Div(dcc.Graph(figure=fig))


def render_outcomes(data: dict[str, pl.DataFrame]) -> html.Div:
    """Outcome Gaps tab."""
    if "outcome_disparity" not in data:
        return _empty_tab("Outcome disparity data not available")
    df = data["outcome_disparity"].to_pandas()
    fig = px.line(
        df,
        x="year",
        y="mortality_disparity_ratio",
        color="disease" if "disease" in df.columns else None,
        markers=True,
        title="Mortality Disparity Ratio Over Time",
        labels={"mortality_disparity_ratio": "Mortality Ratio", "year": "Year"},
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="black")
    return html.Div(dcc.Graph(figure=fig))


def render_trends(data: dict[str, pl.DataFrame]) -> html.Div:
    """Temporal Trends tab: disparity convergence/divergence summary."""
    if "temporal_trends" not in data:
        return _empty_tab("Temporal trend data not available")
    df = data["temporal_trends"].to_pandas()
    fig = px.bar(
        df.sort_values("ols_slope"),
        x="ols_slope",
        y="demographic_group",
        orientation="h",
        color="convergence_status",
        title="Disparity Trend Slope by Age Group (OLS)",
        labels={"ols_slope": "Trend Slope (disparity ratio / year)",
                "demographic_group": "Age Group"},
    )
    fig.add_vline(x=0.0, line_dash="dash", line_color="black")
    return html.Div(dcc.Graph(figure=fig))


def render_priorities(data: dict[str, pl.DataFrame]) -> html.Div:
    """Priority Populations tab: ranked priority table and scatter matrix."""
    if "priority_populations" not in data:
        return _empty_tab("Priority population data not available")
    df = data["priority_populations"].to_pandas()
    fig = px.scatter(
        df,
        x="disparity_score",
        y="impact_score",
        size="composite_score",
        color="urgency_score",
        text="demographic_group",
        title="Vulnerable Population Priority Matrix",
        labels={"disparity_score": "Disparity Score",
                "impact_score": "Impact Score",
                "composite_score": "Priority Score"},
        color_continuous_scale="Reds",
    )
    fig.update_traces(textposition="top center")
    fig.add_hline(y=0.5, line_dash="dash", line_color="grey")
    fig.add_vline(x=0.5, line_dash="dash", line_color="grey")

    table = dbc.Table.from_dataframe(
        df[["priority_rank", "demographic_group", "barrier_type",
            "composite_score", "convergence_status"]]
        if "barrier_type" in df.columns else
        df[["priority_rank", "demographic_group", "composite_score"]],
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
    )
    return html.Div([dcc.Graph(figure=fig), html.Hr(), table])
```

---

### 7. Domain-Driven Feature Engineering

All dashboard charts are driven by pre-computed equity metrics from US-03 through US-08. No new feature engineering at dashboard stage — the dashboard is a read-only presentation layer.

---

### 8. API Endpoints & Data Contracts

Not applicable — local Dash app only. If deploying to Databricks or cloud:
- Serve via `gunicorn dashboard.app:server --bind 0.0.0.0:8050`
- Databricks: use Databricks Apps or a cluster-attached web server port

---

### 9. Styling & Visualization

**Theme**: `dbc.themes.BOOTSTRAP` — clean, responsive
**Colour palette**:
- Equity reference lines: `#000000` dashed
- High disparity: `#d73027` (red)
- Low disparity: `#4575b4` (blue)
- Neutral: `#74add1`

**Charts per tab**:
| Tab | Chart Type | Plotly Type |
|-----|-----------|-------------|
| Overview | Rate ratio bar + KPI cards | `px.bar` |
| Utilisation | Rate ratio trend lines | `px.line` |
| Outcome Gaps | Mortality ratio trends | `px.line` |
| Temporal Trends | Slope bar (convergence) | `px.bar` |
| Priority Populations | Bubble priority matrix + table | `px.scatter` |

**Interactive features**: Tab switching (no page reload), hover tooltips on all charts, reference line annotations.

---

### 10. Testing Strategy

```python
# problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_data_loader.py

from pathlib import Path
import polars as pl
import pytest
from dashboard.data_loader import get_demographic_options, load_all_equity_data


def test_get_demographic_options_returns_sorted_list():
    df = pl.DataFrame({"demographic_group": ["65+ years", "25-44 years", "45-64 years"]})
    options = get_demographic_options(df)
    labels = [o["label"] for o in options]
    assert labels == sorted(labels)  # must be sorted


def test_get_demographic_options_empty_when_col_missing():
    df = pl.DataFrame({"year": [2010, 2011]})
    options = get_demographic_options(df, col="demographic_group")
    assert options == []


def test_load_all_equity_data_handles_missing_files(tmp_path: Path):
    # Empty project root — no files exist; should return empty dict without raising
    result = load_all_equity_data(tmp_path)
    assert isinstance(result, dict)
    # All files missing — result should be empty (all warnings logged)
    assert len(result) == 0
```

---

### 11. Implementation Steps

**Phase 1 — Data Backend**
- [ ] Create `dashboard/` directory under `problem-statements/ps-005-healthcare-equity-disparities/`
- [ ] Implement `data_loader.py` — run `load_all_equity_data()` and confirm all files load
- [ ] Note any missing files (upstream analysis steps not yet complete) and stub with empty DataFrames for dashboard development

**Phase 2 — Layout**
- [ ] Implement `layout.py` with 5-tab structure
- [ ] Run `python app.py` and confirm tab navigation renders without errors

**Phase 3 — Callbacks (one tab at a time)**
- [ ] Overview tab: KPI cards and rate ratio bar chart
- [ ] Utilisation tab: Rate ratio time series
- [ ] Outcome Gaps tab: Mortality ratio chart
- [ ] Temporal Trends tab: Slope bar chart
- [ ] Priority Populations tab: Bubble matrix + table

**Phase 4 — Polish & Testing**
- [ ] Add loading spinners: `dcc.Loading` wrapper on all `dcc.Graph` elements
- [ ] Add `_empty_tab()` fallback for any missing data files
- [ ] Run `pytest tests/unit/test_data_loader.py --cov` ≥80%
- [ ] Manual UAT: load all 5 tabs, hover tooltips, check KPI card values

**Phase 5 — Deployment (optional at prototype stage)**
- [ ] Run locally: `python dashboard/app.py`
- [ ] Confirm `http://localhost:8050` loads without JS console errors

---

### 12. Adaptive Implementation Strategy

- If upstream results CSVs are not yet available → `load_all_equity_data()` logs warnings and returns partial dict; affected tabs show `_empty_tab()` message — dashboard still runs
- If Plotly version incompatibility → pin `plotly==5.18.0` in requirements.txt and run `uv pip install plotly==5.18.0`
- If dashboard loads too slowly (>3s) → add `dcc.Store` component to cache filtered DataFrames client-side

---

### 13. Code Generation Order

1. `dashboard/data_loader.py` — data loading utilities
2. `dashboard/layout.py` — tab structure
3. `dashboard/callbacks.py` — all render functions
4. `dashboard/app.py` — app init + tab switcher callback
5. `tests/unit/test_data_loader.py` — data loader unit tests

---

### 14. Data Quality & Validation

Dashboard is read-only — data validation occurs upstream (US-01 through US-08). Dashboard-level checks:
- Log warning if expected file missing on startup
- Show `_empty_tab()` message rather than crashing on missing data
- Validate that `demographic_group` column exists before building dropdown options

---

### 20. Security & Privacy

- **PII/PHI**: None — all aggregated population statistics
- **Authentication**: Not required for local prototype; add HTTP Basic Auth or Databricks access controls for any shared deployment
- **Credentials**: No credentials required; dashboard reads local files only
- **Port**: Default 8050 (localhost only); do not expose without auth if deploying to shared infrastructure

---

### 21. Version Control

- Branch: `feature/ps-005-equity-dashboard`
- Commits:
  - `feat(ps-005): add equity dashboard skeleton with 5-tab layout`
  - `feat(ps-005): wire all dashboard callbacks and chart renderers`
  - `test(ps-005): add unit tests for equity dashboard data_loader`

---

### 22. Multi-Agent Orchestration

Not applicable for this story — single-agent dashboard build.

---

### 6.6 Package Management

```bash
uv pip install plotly>=5.18.0 dash>=2.14.0 dash-bootstrap-components>=1.5.0 gunicorn>=21.0.0
uv pip freeze > requirements.txt
```
