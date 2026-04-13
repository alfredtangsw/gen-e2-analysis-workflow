# PS-002 User Stories: Healthcare Demand Forecasting

**Problem Statement**: [PS-002 Healthcare Demand Forecasting](../../../objectives/problem_statements/ps-002-healthcare-demand-forecasting.md)  
**Type**: Predictive Analytics  
**Data Window**: 1990–2020 (mortality); 2006–2020 (admissions); 2021–2035 (projections)  
**Status**: Defined — awaiting execution

---

## Story Index

| # | Title | Stage | Status |
|---|-------|-------|--------|
| [01](01-extract-and-profile-forecasting-source-data.md) | Extract and Profile Forecasting Source Data | Data Extraction | ⬜ Not Started |
| [02](02-validate-and-prepare-time-series-data.md) | Validate and Prepare Time-Series Data | Data Validation & Cleaning | ⬜ Not Started |
| [03](03-explore-mortality-and-admission-patterns.md) | Explore Mortality and Admission Patterns | Exploratory Analysis | ⬜ Not Started |
| [04](04-engineer-time-series-features.md) | Engineer Time-Series Features | Feature Engineering | ⬜ Not Started |
| [05](05-fit-mortality-forecasting-models.md) | Fit Mortality Forecasting Models | Modelling | ⬜ Not Started |
| [06](06-project-admission-volumes.md) | Project Admission Volumes (Cohort-Component) | Modelling | ⬜ Not Started |
| [07](07-validate-forecasts-and-export.md) | Validate Forecasts and Export Demand Projections | Validation & Reporting | ⬜ Not Started |

---

## Input Data

| Source | Tables | Years |
|--------|--------|-------|
| Kaggle `subhamjain/health-dataset-complete-singapore` | Mortality (cancer, stroke, IHD), admissions by age/sex | 1990–2020 |
| SingStat (external) | Population projections — principal, high, low | 2021–2035 |
| UN WPP 2022 (fallback) | Population projections if SingStat unavailable | 2021–2035 |

---

## Key Constraints

- **Only 3 diseases forecasted**: cancer, stroke, IHD — all others excluded (no data)
- **No LTC statistical forecast**: LTC data is too sparse (~25 records); descriptive observation only
- **Flat rate assumption** for admission projections: 2019 actuals held constant; sensitivity tests at ±10%
- **COVID exclusion**: 2020 admission volumes treated as outlier; 2019 rates used as base

---

## Key Outputs (Handoff to PS-003)

| File | Location | Consumer |
|------|----------|----------|
| `mortality_{disease}_forecast.csv` × 3 | `models/forecasts/` | PS-003 (workforce cost estimates) |
| `admission_volume_projections.csv` | `models/forecasts/` | PS-003 (bed and workforce gap calc) |
| `ps002_admission_sensitivity_2035.csv` | `results/tables/` | PS-003 (scenario comparison tab) |
| `ps002_demand_projections_export.csv` | `results/exports/` | PS-003 (primary planning input) |
| `ps002_forecast_findings.md` | `results/exports/` | PS-003 planning team brief |
| Forecast chart PNGs × 7 | `reports/figures/ps002_forecast/` | PS-003 (dashboard) |

---

## Execution Order

```
Story 01 → Story 02 → Story 03 → Story 04 → Stories 05 & 06 (can run in parallel) → Story 07
```
