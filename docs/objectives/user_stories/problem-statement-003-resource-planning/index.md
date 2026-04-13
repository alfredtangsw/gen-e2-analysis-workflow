# PS-003 User Stories: Integrated Resource Planning

**Problem Statement**: [PS-003 Integrated Resource Planning](../../../objectives/problem_statements/ps-003-integrated-resource-planning.md)  
**Type**: Prescriptive Analytics + Dashboard  
**Planning Horizon**: 2021–2035  
**Status**: Defined — awaiting execution (depends on PS-001 and PS-002 completion)

---

## Story Index

| # | Title | Stage | Status |
|---|-------|-------|--------|
| [01](01-load-and-reconcile-planning-inputs.md) | Load and Reconcile Planning Inputs | Data Integration | ⬜ Not Started |
| [02](02-project-workforce-supply.md) | Project Workforce Supply | Supply Modelling | ⬜ Not Started |
| [03](03-compute-workforce-gap-and-hiring-targets.md) | Compute Workforce Gap and Hiring Targets | Gap Analysis | ⬜ Not Started |
| [04](04-compute-bed-gap-and-commissioning-plan.md) | Compute Bed Gap and Commissioning Plan | Gap Analysis | ⬜ Not Started |
| [05](05-validate-staff-facility-alignment.md) | Validate Staff-Facility Alignment | Alignment Check | ⬜ Not Started |
| [06](06-estimate-workforce-cost.md) | Estimate Workforce Cost | Cost Estimation | ⬜ Not Started |
| [07](07-build-interactive-planning-dashboard.md) | Build Interactive Planning Dashboard | Dashboard | ⬜ Not Started |

---

## Input Data (from PS-001 and PS-002)

| File | Source PS | Used In |
|------|-----------|---------|
| `baseline_metrics.csv` | PS-001 | Stories 02, 04 (CAGR values) |
| `benchmark_comparison.csv` | PS-001 | Story 01, Tab 1 |
| `system_balance_scorecard.csv` | PS-001 | Story 01, Tab 1 |
| `expenditure_baseline.csv` | PS-001 | Story 06 (expenditure comparison) |
| `admission_volume_projections.csv` | PS-002 | Stories 03, 04, 05 |
| `ps002_demand_projections_export.csv` | PS-002 | Story 01 (consolidated input) |
| `ps002_admission_sensitivity_2035.csv` | PS-002 | Tab 6 (scenario comparison) |

## External Constants (hard-coded from config)

| Constant | Value | Source |
|----------|-------|--------|
| ALOS | 5.1 days | MOH Health Statistics 2020 |
| Occupancy benchmark | 85% | WHO SEARO |
| Nurse:bed benchmark | 0.25 (1 per 4 beds) | WHO SEARO |
| RN median wage | SGD 4,200/month | MOM OWS 2020 |
| GP median wage | SGD 8,500/month | MOM OWS 2020 |
| Overhead multiplier | 1.35× | WHO methodology |
| Nurse attrition | 8% p.a. | MOH Annual Report |
| Doctor attrition | 3% p.a. | MOH Annual Report |
| Construction lead time | 5 years | Infrastructure planning convention |

---

## Key Outputs

| File | Location | Format |
|------|----------|--------|
| `ps003_workforce_supply_projections.csv` | `results/tables/` | Long CSV |
| `ps003_workforce_gap.csv` (milestones) | `results/tables/` | Summary CSV |
| `ps003_workforce_gap_timeseries.csv` | `results/tables/` | Long CSV |
| `ps003_bed_gap.csv` | `results/tables/` | Long CSV |
| `ps003_commissioning_milestones.csv` | `results/tables/` | Summary CSV |
| `ps003_staff_facility_alignment.csv` | `results/tables/` | Heatmap CSV |
| `ps003_workforce_cost.csv` | `results/tables/` | Long CSV |
| `ps003_cost_summary.csv` | `results/exports/` | Milestone summary |
| `moh_integrated_resource_planning_dashboard.html` | `results/exports/` | Self-contained HTML |

---

## Scope Boundary

> **Budget estimates cover workforce costs only.** Infrastructure and consumables are excluded due to the absence of unit cost data in the available dataset.

---

## Execution Order

Stories 03 and 04 can run in parallel after Story 02 is complete. Story 05 depends on both 03 and 04. Stories 06 and 07 are sequential after Story 05.

```
Story 01 → Story 02 → Stories 03 & 04 (parallel) → Story 05 → Story 06 → Story 07
```

**Prerequisite**: PS-001 and PS-002 must be fully completed before PS-003 Story 01 begins.
