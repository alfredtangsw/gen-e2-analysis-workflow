# Analytics Problem Statements - Strategic Initiatives

## Overview

This directory contains the analytics problem statements for the Singapore MOH Healthcare Resource Planning project. All three problem statements form a **sequential pipeline** — each one feeds the next. They are grounded entirely in the verified Kaggle Singapore Health Dataset (`subhamjain/health-dataset-complete-singapore`, ~3.5 MB, 35 CSV tables, 2006–2020) plus identified public external sources.

**Total Problem Statements**: 3  
**Last Updated**: 2026-04-13  
**Data Source**: [data-sources.md](../../project-context/data-sources.md)

---

## Data Reality Summary (STEP 1.5)

Before any problem statement was written, the following feasibility constraints were confirmed:

### ✅ What the data supports

- Annual workforce headcount by profession and sector (2006–2019)
- Annual inpatient bed counts by facility type (2009–2020)
- Annual hospital admission rates by age group and sex (2006–2020)
- 30-year age-standardised mortality rates for cancer, stroke, IHD (1990–2019)
- Total government health expenditure (2006–2018, aggregate only)
- LTC admissions (sparse, ~25 records — descriptive observation only)

### ❌ What the data does NOT support (dropped from all PS)

- Bed occupancy rates (bed counts exist; patient-days do not)
- Expenditure by category (workforce/infrastructure/supplies) — total only
- Diagnosis-linked hospital admissions — admission table has no diagnosis field
- ICU, step-down, or ward-type-specific beds — not separated in the dataset
- Diabetes, dementia, respiratory disease burden — no tables in dataset
- Consumables, supplies, test kit volumes — absent entirely
- Sub-national or facility-level analysis — national aggregates only
- Real-time or sub-annual analysis — annual data only

---

## Problem Statement Pipeline

> **Execute in this order**: PS-001 → PS-002 → PS-003

| # | Problem Statement | Category | Priority | Estimated Sprints | Status |
|---|---|---|---|---|---|
| [PS-001](ps-001-healthcare-system-baseline.md) | Healthcare System Baseline — Workforce, Capacity & Utilisation | Descriptive | P0 | 2–3 | Initialized |
| [PS-002](ps-002-healthcare-demand-forecasting.md) | Healthcare Demand Forecasting — Disease Burden & Demographic Projections | Predictive | P0 | 3–4 | Initialized |
| [PS-003](ps-003-integrated-resource-planning.md) | Integrated Resource Planning & Budget Dashboard | Prescriptive | P0 | 4–5 | Initialized |

**Total estimated effort**: 9–12 sprints

---

## Descriptive Analytics (1)

**[PS-001: Healthcare System Baseline — Workforce, Capacity & Utilisation](ps-001-healthcare-system-baseline.md)**
- **Description**: Construct an integrated historical baseline (2006–2020) of workforce headcount, facility bed capacity, hospital admission rates, and total government expenditure. Compute staff-to-bed ratios and admissions-per-bed proxies, benchmarked against WHO standards, to identify structural imbalances in the current system.
- **Priority**: P0 (Critical)
- **Estimated Sprints**: 2–3
- **Platform**: Local → HEALIX/Databricks
- **Dependencies**: None
- **Key Deliverables**: Workforce baseline CSV, facility baseline CSV, utilisation baseline CSV, system balance scorecard CSV, trend charts

---

## Predictive Analytics (1)

**[PS-002: Healthcare Demand Forecasting — Disease Burden & Demographic Projections](ps-002-healthcare-demand-forecasting.md)**
- **Description**: Forecast cancer, stroke, and IHD mortality rate trajectories (2020–2030) and project total hospital admission volumes by age group (2021–2035) using SingStat population projections applied to PS-001 historical admission rates. Produce three demographic scenarios (low/medium/high ageing).
- **Priority**: P0 (Critical)
- **Estimated Sprints**: 3–4
- **Platform**: Local → HEALIX/Databricks
- **Dependencies**: PS-001
- **Key Deliverables**: Disease burden forecast CSV, admission volume projection CSV, forecast validation report, demand projections export for PS-003

---

## Prescriptive Analytics (1)

**[PS-003: Integrated Resource Planning & Budget Dashboard](ps-003-integrated-resource-planning.md)**
- **Description**: Convert PS-002 demand projections into year-by-year workforce and bed gap analyses, validate that staffing and facility plans are internally consistent (staff-to-bed balance), and estimate workforce cost using public salary benchmarks. Deliver as a self-contained 6-tab interactive HTML dashboard.
- **Priority**: P0 (Critical)
- **Estimated Sprints**: 4–5
- **Platform**: Local → HEALIX/Databricks
- **Dependencies**: PS-001, PS-002
- **Key Deliverables**: Workforce gap analysis CSV, bed gap analysis CSV, staff-facility alignment CSV, workforce cost estimate Excel, interactive HTML dashboard

---

## Portfolio Validation

| Check | Status |
|---|---|
| All data domains verified against `data-sources.md` | ✅ |
| No analyses proposed without a corresponding verified dataset | ✅ |
| Infeasible analyses explicitly dropped with reason | ✅ |
| External data dependencies identified with public fallbacks | ✅ |
| Platform feasibility confirmed (local Python/Polars) | ✅ |
| Problem statements are sequential and non-overlapping | ✅ |
| Budget scope clearly bounded (workforce cost only — not total system budget) | ✅ |
| Each PS decomposable into 5–10 user stories | ✅ |

---

## Priority Scoring Summary

| PS | Business Value | Feasibility | Urgency | Total |
|---|---|---|---|---|
| PS-001 | 5 | 5 | 5 | **15/15** |
| PS-002 | 5 | 4 | 5 | **14/15** |
| PS-003 | 5 | 4 | 5 | **14/15** |

---

## User Stories

Each problem statement has been decomposed into sprint-ready user stories following the data analysis lifecycle. 21 stories total across 3 PS.

| Problem Statement | Stories | Index |
|---|---|---|
| PS-001 Healthcare System Baseline | 7 stories | [View →](../user_stories/problem-statement-001-baseline/index.md) |
| PS-002 Healthcare Demand Forecasting | 7 stories | [View →](../user_stories/problem-statement-002-demand-forecasting/index.md) |
| PS-003 Integrated Resource Planning | 7 stories | [View →](../user_stories/problem-statement-003-resource-planning/index.md) |

### Execution Sequence

```
PS-001 (Baseline)          PS-002 (Forecasting)         PS-003 (Planning)
Story 01 → 02 → 03/04     Story 01 → 02 → 03 → 04     Story 01 → 02 → 03/04
→ 05 → 06 → 07  ━━━━━━━━━ → 05/06 → 07  ━━━━━━━━━━━━ → 05 → 06 → 07
```

**Key Constraint**: Annual granularity, national-level aggregation (no regional breakdowns, no real-time data)

---

## Technical Stack Reference

All problem statements use:
- **Platform**: HEALIX/Databricks (GCC Cloud Environment)
- **Primary Language**: Python 3.9+ (Databricks Runtime 13.3)
- **Data Processing**: Polars (mandatory), pandas (only when justified)
- **Package Management**: uv (NOT pip/conda)
- **Forecasting Libraries**: statsmodels, prophet, scikit-learn
- **Visualization**: Plotly (interactive), matplotlib/seaborn (static)

See [tech-stack.md](../project_context/tech-stack.md) for complete details.

---

## Problem Statement Lifecycle

### Statuses
- **Draft**: Initial problem statement created, pending stakeholder review
- **Approved**: Stakeholder sign-off obtained, ready for backlog
- **In Progress**: User stories created, sprints active
- **Completed**: All deliverables produced, stakeholder acceptance achieved
- **Archived**: No longer relevant or superseded by other work

### Update Triggers
Problem statements should be reviewed and updated when:
- New data sources become available
- Stakeholder priorities shift
- Technical capabilities change
- Related problem statements complete and provide new insights

---

## Document Management

**Owners**: 
- **Business Analyst**: Problem statement definition, stakeholder alignment
- **Data Analytics Team**: Technical feasibility validation, data verification
- **Project Manager**: Prioritization, sequencing, resource allocation

**Review Frequency**: Quarterly or when significant context changes occur

**Version Control**: All problem statements tracked in Git with change history

---

## Related Documentation

- **User Stories**: [docs/objectives/user_stories/](../user_stories/) - Tactical breakdown of problem statements
- **Data Dictionary**: [docs/data_dictionary/](../../data_dictionary/) - Dataset schemas and definitions
- **Domain Knowledge**: [docs/domain_knowledge/](../../domain_knowledge/) - Healthcare and analytics domain expertise
- **Project Context**: [docs/project_context/](../../project_context/) - Business objectives, data sources, tech stack

---

**Document Status**: Active  
**Last Updated**: 2026-03-13  
**Next Review**: 2026-06-13 (Quarterly)
