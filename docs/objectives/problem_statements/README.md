# Analytics Problem Statements - Strategic Initiatives

## Overview

This directory contains strategic analytics problem statements for the Singapore Health Trends Analysis project. Each problem statement represents a complete analytical initiative from data extraction to actionable insights, focused on problems that can be solved end-to-end with available data and technical capabilities.

**Total Problem Statements**: 6  
**Last Updated**: 2026-04-08

---

## Data Reality Check (Step 1.5)

> This assessment constrains all problem statements to analyses that are **actually feasible** given confirmed data. Verified against [`docs/project-context/data-sources.md`](../../project-context/data-sources.md).

### Data Landscape Summary

**Primary Data Source**: Kaggle dataset `subhamjain/health-dataset-complete-singapore` (35 CSV tables, ~3.5 MB)  
**Data Quality**: 100% completeness, official MOH source via data.gov.sg

| Domain | Tables | Time Span | Granularity |
|--------|--------|-----------|-------------|
| Healthcare Workforce | 7 | 2006–2019 | Annual, national |
| Healthcare Facilities | 4 | 2009–2020 | Annual, national |
| Disease Burden / Mortality | 3 | 1990–2019 | Annual, age-standardized |
| Public Health & Prevention | 6 | 2003–2020 | Annual, national |
| Healthcare Utilization | 3 | 2006–2020 | Annual, by age/gender |
| Healthcare Expenditure | 1 | 2006–2018 | Annual, national |
| Nutrition Surveys | 3 | 2004, 2010 | Sparse (2 time points) |

**Temporal scope**: Annual aggregates only. Typical data lag: ~6–7 years (data ends 2019–2020; current year 2026).  
**Geographic scope**: National level only — no regional, district, or facility-level breakdowns available.

---

### ✅ FEASIBLE Analyses (Confirmed data supports these)

1. **Annual workforce trend analysis** by profession and sector (2006–2019)
2. **Time series forecasting** of workforce supply using 13–30 years of historical annual data
3. **30-year disease mortality trend analysis** (cancer, stroke, ischemic heart disease, 1990–2019)
4. **Healthcare facility and bed capacity trend analysis** (2009–2020)
5. **Hospital admission rate analysis** by age and gender (2006–2020)
6. **Government expenditure growth decomposition** (2006–2018)
7. **School public health program trend analysis** (vaccination uptake, obesity rates, dental health)
8. **Cross-sectional demand/supply gap analysis** using proxy occupancy metrics
9. **Demographic (age/gender) stratification** of utilization and mortality
10. **5-year mortality forecasting** using ARIMA/Prophet on 30-year disease burden series

---

### ❌ INFEASIBLE Analyses (Data does not support these)

| Analysis | Reason |
|----------|--------|
| Real-time outbreak detection | No daily or weekly data — annual aggregates only |
| Regional/geographic equity analysis | National aggregates only — no sub-national breakdowns |
| Facility-level performance benchmarking | No facility-level records |
| Socioeconomic health disparity analysis | No SES stratification in dataset |
| Ethnicity-based health disparity analysis | No ethnicity/race breakdown available |
| Individual patient journey analysis | No individual-level records |
| Clinical quality metrics | No clinical outcomes or process data |
| Healthcare episode-level cost analysis | Aggregate national expenditure only |
| Seasonal/intraday utilization patterns | Annual granularity only |
| Primary care vs specialist referral pathways | No pathway or referral data |

---

### Predictive Analytics (1)

**[PS-006: Five-Year Disease Burden Forecasting and Mortality Projection](ps-006-disease-burden-forecasting.md)**
- **Description**: Develop time series forecasting models to project mortality and disease burden for major diseases (cancer, stroke, heart disease) over the next 5 years, enabling proactive healthcare capacity planning and resource allocation
- **Priority**: P1 (High)
- **Estimated Sprints**: 5-7
- **Platform**: HEALIX/Databricks
- **Dependencies**: PS-002 (recommended but not required)
- **Key Deliverables**: Forecasting models, 5-year projection report, interactive forecast dashboard, capacity planning tool, forecast monitoring system

---

### Descriptive Analytics (2)

**[PS-002: National Disease Burden Temporal Trends Analysis](ps-002-disease-burden-temporal-trends.md)**
- **Description**: Analyze 30-year mortality trends (1990-2019) for major diseases to identify shifting disease burden patterns and inform public health program prioritization
- **Priority**: P0 (Critical)
- **Estimated Sprints**: 3-5
- **Platform**: HEALIX/Databricks
- **Dependencies**: None
- **Key Deliverables**: Trend analysis report, interactive trend explorer dashboard, curated disease burden dataset, policy brief

**[PS-005: Healthcare Equity and Disparities Analysis](ps-005-healthcare-equity-disparities.md)**
- **Description**: Quantify healthcare access and outcome disparities across demographic groups and geographic regions to identify underserved populations
- **Priority**: P2 (Medium)
- **Estimated Sprints**: 4-5
- **Platform**: HEALIX/Databricks
- **Dependencies**: None
- **Key Deliverables**: Equity assessment report, disparity metrics dashboard, priority intervention areas

---

### Diagnostic Analytics (2)

**[PS-001: Healthcare Workforce Sustainability Analysis](ps-001-healthcare-workforce-sustainability.md)**
- **Description**: Analyze healthcare workforce trends and identify factors contributing to sustainability challenges in manpower planning
- **Priority**: P0 (Critical)
- **Estimated Sprints**: 4-6
- **Platform**: HEALIX/Databricks
- **Dependencies**: None
- **Key Deliverables**: Workforce sustainability report, shortage risk assessment, workforce planning dashboard

**[PS-004: Healthcare Expenditure Drivers Analysis](ps-004-healthcare-expenditure-drivers.md)**
- **Description**: Identify and quantify key drivers of healthcare expenditure growth to inform cost containment strategies
- **Priority**: P0 (Critical)
- **Estimated Sprints**: 4-5
- **Platform**: HEALIX/Databricks
- **Dependencies**: None
- **Key Deliverables**: Expenditure driver analysis report, cost projection models, policy recommendations

---

### Prescriptive Analytics (1)

**[PS-003: Healthcare Capacity Optimization](ps-003-healthcare-capacity-optimization.md)**
- **Description**: Optimize allocation of healthcare resources (beds, facilities, workforce) across the system to maximize access and efficiency
- **Priority**: P1 (High)
- **Estimated Sprints**: 5-7
- **Platform**: HEALIX/Databricks
- **Dependencies**: PS-001 (workforce data), PS-006 (demand forecasts - recommended)
- **Key Deliverables**: Capacity optimization models, resource allocation recommendations, scenario planning tool

---

## Problem Statement Priority Matrix

| Priority | Problem Statements | Rationale |
|----------|-------------------|-----------|
| **P0 (Critical)** | PS-001 (4.4), PS-004 (4.4), PS-002 (4.0) | Highest combined business value, feasibility, and urgency; foundational analyses |
| **P1 (High)** | PS-003 (3.8), PS-006 (3.7) | High business value; benefit from P0 outputs or require optimization expertise |
| **P2 (Medium)** | PS-005 (2.4) | Important for equity mission but significantly constrained by missing SES/ethnicity data |

---

## Problem Statement Dependencies Graph

```
PS-002 (Disease Trends)
   ↓ (recommended input)
PS-006 (Disease Forecasting)
   ↓ (demand projections)
PS-003 (Capacity Optimization)
   ↑ (workforce data)
PS-001 (Workforce Sustainability)

PS-004 (Expenditure Drivers) ← independent
PS-005 (Equity Analysis) ← independent
```

**Legend**:
- **Solid arrows (↓)**: Recommended sequencing for maximum value
- **Independent**: Can be executed in parallel without dependencies

---

## Recommended Execution Sequence

### Phase 1: Foundational Analysis (Quarters 1-2) — P0 Critical
1. **PS-001**: Healthcare Workforce Sustainability (4-6 sprints) — start immediately
   - Provides workforce supply context for capacity planning
   
2. **PS-004**: Healthcare Expenditure Drivers (4-5 sprints) — start in parallel with PS-001
   - Aligns with annual budget cycles; Finance Ministry priority
   
3. **PS-002**: Disease Burden Temporal Trends (3-5 sprints) — start Sprint 1-2 in parallel
   - Establishes baseline disease landscape; feeds PS-006 forecasting

### Phase 2: Predictive & Optimization (Quarters 2-3) — P1 High
4. **PS-006**: Disease Burden Forecasting (5-7 sprints) — start after PS-002 completes
   - Converts PS-002 trends into 5-year demand projections

5. **PS-003**: Healthcare Capacity Optimization (5-7 sprints) — start after PS-001 initiated
   - Leverages PS-001 workforce constraints and PS-006 demand forecasts

### Phase 3: Equity Analysis (Quarters 3-4) — P2 Medium
6. **PS-005**: Healthcare Equity Analysis (4-5 sprints) — defer; data enhancement recommended first
   - Low priority until richer SES/ethnicity data is obtained from MOH

---

## Problem Statement Status

| ID | Title | Status | Priority | Score | Sprints | Platform |
|----|-------|--------|----------|-------|---------|----------|
| PS-001 | Healthcare Workforce Sustainability | Draft | P0 (Critical) | 4.4 | 4-6 | HEALIX/Databricks |
| PS-002 | Disease Burden Temporal Trends | Draft | P0 (Critical) | 4.0 | 3-5 | HEALIX/Databricks |
| PS-003 | Healthcare Capacity Optimization | Draft | P1 (High) | 3.8 | 5-7 | HEALIX/Databricks |
| PS-004 | Healthcare Expenditure Drivers | Draft | P0 (Critical) | 4.4 | 4-5 | HEALIX/Databricks |
| PS-005 | Healthcare Equity Disparities | Draft | P2 (Medium) | 2.4 | 4-5 | HEALIX/Databricks |
| PS-006 | Disease Burden Forecasting | Draft | P1 (High) | 3.7 | 5-7 | HEALIX/Databricks |

> Scores computed as `(BV × 0.4) + (F × 0.3) + (U × 0.3)`. See [PRIORITIZATION.md](PRIORITIZATION.md) for full scoring rationale.

---

## Data Sources Reference

All problem statements are constrained by data documented in:
- **Primary Data Source**: [Kaggle Health Dataset - Singapore](../project_context/data-sources.md)
- **Dataset**: `subhamjain/health-dataset-complete-singapore`
- **Coverage**: 1990-2020 (varies by table)
- **Tables**: 35 data tables across workforce, facilities, disease burden, utilization, expenditure

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
