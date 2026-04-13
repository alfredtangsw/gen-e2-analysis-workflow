# TODO — Gen-E2 Analysis Workflow

> Format: `[ ] Task description (owner)` | Priority: 🔴 P0 · 🟠 P1 · 🟡 P2

Last updated: 2026-04-13

**Project goal**: Integrated MOH resource planning — workforce hiring targets, bed capacity milestones, and workforce cost estimates co-planned against projected healthcare demand.

**Dataset**: Kaggle `subhamjain/health-dataset-complete-singapore` (~3.5 MB, 35 CSVs, 2006–2020) + public external sources (SingStat, WHO GHO, MOM wages).

**Three-PS pipeline** (sequential): PS-001 → PS-002 → PS-003

---

## 🏗️ Infrastructure & Environment

- [x] Initialize project folder structure
- [x] Create and activate Python virtual environment (`.venv` via `uv`)
- [x] Create `requirements.txt` with all project dependencies
- [x] Create `shared/config/base.yml`
- [x] Install dependencies via `uv pip install -r requirements.txt`
- [x] Updated `.gitignore` (excludes raw data, model artifacts, Kaggle credentials)
- [ ] 🟠 Create `.env.example` with Kaggle API key template
- [ ] 🟠 Create `pyproject.toml` with `ruff` linting configuration
- [ ] 🟡 Add `.gitattributes` for line ending normalisation

---

## 📦 Shared Infrastructure (`shared/`)

- [ ] 🔴 Create `shared/src/data_processing/kaggle_connector.py` — download `subhamjain/health-dataset-complete-singapore` via `kagglehub`
- [ ] 🔴 Create `shared/src/data_processing/loader.py` — Polars CSV loader with schema validation and dtype enforcement
- [ ] 🔴 Create `shared/src/data_processing/validator.py` — null rate checks, year range checks, numeric range checks
- [ ] 🟠 Create `shared/src/utils/config_loader.py` — YAML config loader
- [ ] 🟠 Create `shared/src/utils/logger.py` — loguru logger factory
- [ ] 🟡 Create `shared/src/visualization/plot_utils.py` — shared Plotly chart helpers
- [ ] 🟠 Create raw data subdirs: `shared/data/1_raw/{workforce,facilities,utilisation,mortality,expenditure}/`
- [ ] 🟠 Add `shared/data/2_external/benchmarks/` for WHO and SingStat reference data
- [ ] 🟠 Unit tests for `loader.py` and `validator.py` in `shared/tests/unit/`

---

## 📊 PS-001: Healthcare System Baseline — Workforce, Capacity & Utilisation

> **Goal**: Build the integrated historical baseline (2006–2020). Output is the input to PS-002 and PS-003.
> **Data**: All from verified Kaggle dataset. Singapore population from SingStat/World Bank (public).

### Data Extraction
- [ ] 🔴 Download Kaggle dataset via `kagglehub` and place CSVs in `shared/data/1_raw/`
- [ ] 🔴 Load and validate all 7 workforce tables (doctors, nurses, pharmacists, dentists, allied health, optometrists, midwives)
- [ ] 🔴 Load and validate inpatient beds table and primary care facilities table
- [ ] 🔴 Load and validate hospital admission rates by age/sex table
- [ ] 🔴 Load and validate government expenditure table
- [ ] 🟠 Load LTC admissions table (sparse — flag low record count)
- [ ] 🟠 Download Singapore resident population by year from SingStat or World Bank → `shared/data/2_external/`
- [ ] 🟠 Download WHO nurse-to-bed and doctor-to-population benchmarks → `shared/data/2_external/benchmarks/`

### Analysis
- [ ] 🔴 Build `results/tables/workforce_baseline.csv` — headcount by profession, sector, year; YoY growth rate; growth index (2006=100)
- [ ] 🔴 Build `results/tables/facility_baseline.csv` — beds by facility type, year; beds per 10,000 population
- [ ] 🔴 Build `results/tables/utilisation_baseline.csv` — admission rates by age group, sex, year
- [ ] 🔴 Build `results/tables/expenditure_baseline.csv` — total govt spend by year; expenditure-per-admission proxy
- [ ] 🔴 Build `results/metrics/system_balance_scorecard.csv` — nurses-per-bed, doctors-per-bed by year; benchmark flags
- [ ] 🟠 Generate 5–8 trend charts → `reports/figures/`
- [ ] 🟠 Save data quality report → `results/tables/data_quality_report.csv`

---

## 📊 PS-002: Healthcare Demand Forecasting — Disease Burden & Demographic Projections

> **Goal**: Forecast cancer/stroke/IHD mortality (2020–2030) and project hospital admissions by age group (2021–2035) across 3 demographic scenarios.
> **Data**: Kaggle mortality tables + hospital admissions table + SingStat population projections (external, public).
> **Scope note**: Only cancer, stroke, IHD have mortality data. Admission data is NOT disaggregated by diagnosis.

### Data Acquisition
- [ ] 🔴 Download SingStat 2020–2035 population projections by 5-year age band (low/medium/high scenarios) → `shared/data/2_external/`
  - Fallback if unavailable: UN World Population Prospects (public) — document substitution explicitly
- [ ] 🔴 Confirm admission rate table denominator (per-1,000 or per-10,000) on first extraction
- [ ] 🟠 Confirm SingStat age band alignment with admission table age groups; document interpolation if needed

### Disease Burden Forecasting
- [ ] 🔴 Fit ARIMA models on cancer, stroke, IHD mortality rates (train 1990–2014, test 2015–2019)
- [ ] 🔴 Fit Holt-Winters models as comparison — select best per disease by MAPE
- [ ] 🔴 Run Prophet as validation alternative — compare MAPE
- [ ] 🔴 Generate 2020–2030 projections with 80%/95% CI for best-performing model per disease
- [ ] 🔴 Save to `results/metrics/disease_burden_forecast.csv`
- [ ] 🟠 Save `results/tables/forecast_validation_report.csv` (MAPE by model and disease)

### Admission Volume Projection
- [ ] 🔴 Apply age-specific admission rate trends to SingStat population projections (cohort-component method)
- [ ] 🔴 Run for all 3 demographic scenarios (low/medium/high)
- [ ] 🔴 Decompose admission growth: population size effect + age-structure shift + rate trend
- [ ] 🔴 Backtest on 2018–2020 (note: 2020 COVID outlier — document inclusion/exclusion decision)
- [ ] 🔴 Save to `results/metrics/admission_volume_projection.csv`
- [ ] 🔴 Save clean PS-003 input to `results/exports/demand_projections_for_planning.csv`

### LTC
- [ ] 🟠 Describe LTC admission trend (descriptive only — not forecasted due to sparse data)
- [ ] 🟠 Contextualise using 65+ population projection as proxy driver

---

## 📊 PS-003: Integrated Resource Planning & Budget Dashboard

> **Goal**: Convert demand projections into hiring targets and bed gap milestones. Validate staff-facility alignment. Estimate workforce cost. Deliver as a self-contained 6-tab HTML dashboard.
> **Inputs**: PS-001 outputs + PS-002 outputs + 4 external public data sources (WHO benchmarks, MOM wages, Singapore Health Statistics LOS, MOH Annual Report attrition rates).
> **Budget scope**: Workforce cost ONLY — infrastructure and supplies have no data source.

### Assumptions to Source Before Building
- [ ] 🔴 Source Singapore average acute hospital length of stay (Singapore Health Statistics or MOH Annual Report, public)
  - Fallback: WHO/OECD average of 5.1 days — document if used
- [ ] 🔴 Source healthcare worker attrition rates by profession (MOH Annual Report, public)
  - Fallback: flat 5% if not found — document if used
- [ ] 🔴 Source median annual salary by healthcare occupation from MOM Occupational Wages Survey (public)
- [ ] 🔴 Source WHO nurse-to-bed and doctor-to-population/bed benchmarks (WHO GHO, public)

### Planning Models
- [ ] 🔴 Build workforce supply projection: extrapolate PS-001 growth rates to 2035 (two supply assumptions: trend continues / no net new hires)
- [ ] 🔴 Build workforce demand projection: apply WHO benchmarks to PS-002 admission projections → required headcount by profession, year, scenario
- [ ] 🔴 Build workforce gap = demand − supply; convert to annual gross hiring targets (gap + attrition)
- [ ] 🔴 Flag profession-years where gap requires above-historical-trend hiring → policy action required
- [ ] 🔴 Build bed demand: PS-002 admissions × LOS ÷ (365 × 85% occupancy target)
- [ ] 🔴 Build bed supply projection: extrapolate PS-001 bed growth to 2035
- [ ] 🔴 Build bed gap = required − projected; identify 5-year commissioning windows
- [ ] 🔴 Build staff-facility alignment check: projected nurses ÷ projected beds vs WHO benchmark by year and scenario; generate traffic-light flags
- [ ] 🟠 Build workforce cost estimate: (current headcount + cumulative hires) × salary × 1.35 overhead, by profession and year

### Dashboard (6 Tabs)
- [ ] 🔴 Tab 1: Executive Summary — KPI cards (nurse gap yr1/yr5/yr10, bed gap yr5/yr10, 10-yr workforce cost, largest profession gap)
- [ ] 🔴 Tab 2: Workforce Plan — required vs projected headcount by profession; annual hiring targets; policy-action flags
- [ ] 🔴 Tab 3: Facility Capacity Plan — required vs projected beds by year/scenario; 5-year commissioning milestones
- [ ] 🔴 Tab 4: Staff-Facility Alignment — heatmap of nurse-to-bed ratio vs benchmark by year/scenario; alignment flags
- [ ] 🔴 Tab 5: Workforce Cost Estimate — area chart by profession per year; cumulative cost; expenditure-per-admission trend context
- [ ] 🟠 Tab 6: Scenario Comparison — toggle low/medium/high scenarios; unified view of nurse gap, bed gap, cost
- [ ] 🔴 Export `reports/dashboards/moh_resource_planning_dashboard.html` (self-contained, single file)

### Deliverables
- [ ] 🔴 `results/metrics/workforce_gap_analysis.csv`
- [ ] 🔴 `results/metrics/bed_gap_analysis.csv`
- [ ] 🔴 `results/tables/staff_facility_alignment.csv`
- [ ] 🟠 `results/exports/workforce_cost_estimate.xlsx`

### Testing & Quality
- [ ] 🟠 Integration test: beds × (4 nurses/bed) = required nurses — verify model arithmetic is consistent
- [ ] 🟡 Dashboard acceptance test in Chrome, Firefox, Safari
- [ ] 🟡 Code review of planning model calculations

---

## 📖 Documentation

- [x] PS-001, PS-002, PS-003 problem statement definitions (data-verified)
- [x] Problem statements README with portfolio checklist and priority scores
- [x] `docs/index.md` updated
- [ ] 🟠 Update `docs/data-dictionary/index.md` with Kaggle dataset tables
- [ ] 🟡 Update `README.md` to describe the 3-PS pipeline

---

## 🔒 Security & DevOps

- [x] `.gitignore` excludes `.env`, `.venv/`, `*.pkl`, `*.parquet`, raw data
- [ ] 🟠 Create `.env.example` with `KAGGLE_USERNAME` and `KAGGLE_KEY` template
- [ ] 🟡 Document credential-free access option (kagglehub caches after first download)
