# PS-001 User Stories: Healthcare System Baseline

**Problem Statement**: [PS-001 Healthcare System Baseline](../../../objectives/problem_statements/ps-001-healthcare-system-baseline.md)  
**Type**: Descriptive Analytics  
**Data Window**: 2006–2020 (varies by metric)  
**Status**: Defined — awaiting execution

---

## Story Index

| # | Title | Stage | Status |
|---|-------|-------|--------|
| [01](01-extract-and-profile-source-data.md) | Extract and Profile Source Data | Data Extraction | ⬜ Not Started |
| [02](02-validate-and-clean-source-data.md) | Validate and Clean Source Data | Data Validation & Cleaning | ⬜ Not Started |
| [03](03-explore-workforce-and-facility-trends.md) | Explore Workforce and Facility Trends | Exploratory Analysis | ⬜ Not Started |
| [04](04-analyse-utilisation-and-expenditure.md) | Analyse Utilisation and Expenditure | Exploratory Analysis | ⬜ Not Started |
| [05](05-engineer-baseline-metrics-and-ratios.md) | Engineer Baseline Metrics and Ratios | Feature Engineering | ⬜ Not Started |
| [06](06-build-system-balance-scorecard.md) | Build System Balance Scorecard | Analysis & Reporting | ⬜ Not Started |
| [07](07-produce-baseline-visualisations-and-report.md) | Produce Baseline Visualisations and Report | Visualisation & Handoff | ⬜ Not Started |

---

## Input Data

| Source | Tables | Years |
|--------|--------|-------|
| Kaggle `subhamjain/health-dataset-complete-singapore` | ~10 relevant tables (workforce, beds, admissions, expenditure, LTC) | 2006–2020 |
| SingStat (external) | Resident population by year | 2006–2020 |
| WHO GHO (external) | SEARO benchmark densities | Reference values |

---

## Key Outputs (Handoff to PS-002 and PS-003)

| File | Location | Consumer |
|------|----------|----------|
| `baseline_metrics.csv` | `results/tables/` | PS-002, PS-003 |
| `benchmark_comparison.csv` | `results/tables/` | PS-003 (dashboard) |
| `system_balance_scorecard.csv` | `results/tables/` | PS-003 (dashboard) |
| `system_balance_scorecard.html` | `results/exports/` | Stakeholder presentation |
| `ps001_findings_summary.md` | `results/exports/` | PS-002 team brief |
| All `*_clean.parquet` | `data/4_processed/` | PS-002 (admissions, mortality) |
| Chart PNGs × 6 | `reports/figures/` | PS-003 (dashboard) |

---

## Execution Order

Stories must be completed in sequence — each story depends on the previous stage's outputs.

```
Story 01 → Story 02 → Stories 03 & 04 (can run in parallel) → Story 05 → Story 06 → Story 07
```
