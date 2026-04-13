# PS-002: Healthcare Demand Forecasting — Disease Burden & Demographic Projections

```yaml
problem_statement_id: PS-002
title: "Healthcare Demand Forecasting — Disease Burden & Demographic Projections"
analysis_category: Predictive Analytics
priority: P0 (Critical)
platform: Local (development) → HEALIX/Databricks
primary_language: Python (Polars + statsmodels/Prophet)
estimated_sprints: 3-4
status: Initialized
dependencies: PS-001
```

---

## STEP 1.5 — Data Reality Check (Applied to this PS)

**Source dataset**: `subhamjain/health-dataset-complete-singapore` (Kaggle, ~3.5 MB, 35 CSV tables)

### Data Domains Available for Forecasting

| Domain | Tables | Coverage | Granularity |
|---|---|---|---|
| Mortality — cancer | `age-standardised-mortality-rate-for-cancer.csv` | 1990–2019 (30 years) | Annual, national |
| Mortality — stroke | `age-standardised-mortality-rate-for-stroke.csv` | 1990–2019 (30 years) | Annual, national |
| Mortality — IHD | `age-standardised-mortality-rate-for-ischaemic-heart-disease.csv` | 1990–2019 (30 years) | Annual, national |
| Hospital admissions by age/sex | `hospital-admission-rate-by-age-and-sex.csv` | 2006–2020 | Annual, by age group and sex |
| LTC admissions | `residential-long-term-care-admissions.csv` | sparse (~25 records) | Annual, aggregate |
| Vaccination/immunisation | `vaccination-and-immunisation-of-students-annual.csv` | 2003–2020 | Annual, aggregate |
| Student health (obesity) | `common-health-problems-of-students-examined-obesity-annual.csv` | 2006–2020 | Annual, aggregate |

**External data needed (publicly available — no credentials)**:
- Singapore resident population by age group, 2006–2020: SingStat / World Bank (required for per-capita denominators)
- SingStat population projections 2020–2035: [singstat.gov.sg](https://www.singstat.gov.sg/) public releases

### ✅ Feasible Analyses

- Time-series forecasting of age-standardised mortality rates for cancer, stroke, IHD (30 years of data is sufficient for ARIMA/Holt-Winters)
- Hospital admission rate forecasting by age group and sex (2006–2020 baseline, 15 years — sufficient for trend-based projection)
- Demographic-weighted demand projection: apply age-specific admission rate trends to SingStat population age-structure projections to estimate total future admission volumes
- Scenario analysis across 3 SingStat ageing trajectories (low, medium, high growth)
- Vaccination trend analysis as a contextual indicator (not a primary forecast variable)
- LTC admission trend observation (data too sparse for statistical forecasting — descriptive only)

### ❌ Infeasible Analyses (dropped — no data)

- Forecasting by **disease-specific admissions** (e.g., cancer admissions, diabetes admissions) — only mortality rates by disease are available; admission data is not disaggregated by diagnosis
- **Diabetes, dementia, respiratory, or falls/fractures** disease burden — no mortality or morbidity tables for these diseases in the dataset
- **ICU, step-down, or LTC bed-day projections** by disease — no length-of-stay, no ward-type breakdown, no diagnosis-linked admissions
- **Outpatient or primary care demand projection** — no outpatient visit volume data
- **Diagnostic volume forecasting** — no diagnostic activity data
- **Sub-national demand projection** — national aggregates only

---

## Executive Summary

Singapore's ageing population will materially increase healthcare demand — but by how much, and for which services? Without a quantified demand projection, any workforce or facility plan is an assumption, not a plan. By combining 30 years of disease mortality data and 15 years of age-stratified admission rates with SingStat population projections, we can forecast future hospital admission volumes by age group and project disease burden trajectories for the three major causes of death (cancer, stroke, ischaemic heart disease) through 2035. This gives MOH planners the demand-side evidence base required to size workforce and facility needs in PS-003.

---

## Problem Statement Hypothesis

> We believe that forecasting Singapore's hospital admission volumes by age group and disease burden trajectories for cancer, stroke, and IHD through 2035 — using verified historical data and public SingStat population projections — will give MOH healthcare planners a data-grounded demand estimate to replace current assumption-based headcount targets. We'll know we're successful when forecast accuracy on held-out 2017–2019 data achieves MAPE ≤ 15%, and planners can articulate which age groups drive the majority of projected admission growth.

---

## Objectives

**Objective 1 — Disease Mortality Trend Forecasting (Cancer, Stroke, IHD)**
- Fit time-series models (ARIMA, Holt-Winters) on 30-year age-standardised mortality rates for cancer, stroke, and IHD (1990–2019)
- Validate models by backtesting on 2015–2019 held-out data (MAPE ≤ 15% threshold)
- Generate 10-year projections (2020–2030) with 80% and 95% confidence intervals
- Produce three scenarios (optimistic trend improvement, baseline, pessimistic reversal) using parameter perturbation

**Objective 2 — Hospital Admission Volume Projection by Age Group**
- Analyse age-group-specific admission rate trends (2006–2020) to identify which age bands are growing fastest
- Obtain Singapore resident population projections by age group from SingStat public releases
- Project total annual hospital admissions: age-specific admission rate × projected population by age group, summed across all groups
- Quantify how much of admission growth is driven by population growth vs. ageing (demographic shift) vs. rate change

**Objective 3 — Forecast Validation and Uncertainty Communication**
- Backtest admission projection on 2018–2020 held-out data
- Report MAPE by age group
- Communicate uncertainty bands clearly — distinguish between model uncertainty and demographic scenario uncertainty
- Flag which projections are robust vs. which are highly sensitive to ageing assumptions

**Objective 4 — LTC Demand Contextual Assessment**
- Describe LTC admission trends from available sparse data (descriptive only — not forecasted)
- Contextualise LTC demand growth using the 65+ population projection as a proxy driver
- Flag LTC as a data gap requiring additional sourcing before quantitative forecasting is possible

---

## Key Questions to Answer

1. Are cancer, stroke, and IHD mortality rates improving, stable, or deteriorating — and what does trend extrapolation suggest through 2030?
2. How will total hospital admissions grow through 2035, and how much is attributable to population ageing vs. rate change?
3. Which age groups (e.g., 65–74, 75–84, 85+) will contribute the most to admission growth?
4. What is the range of plausible outcomes across optimistic and pessimistic demographic scenarios?
5. Is the LTC admission trajectory consistent with the 65+ population growth projection?

---

## Stakeholders and Value Proposition

**Primary Stakeholders**:
- Healthcare Planning Division, MOH — needs admission volume projections to size bed and facility requirements
- Workforce Planning Division, MOH — needs demand signal to justify headcount growth targets
- Disease Prevention & Control Division, MOH — needs disease burden trajectory to prioritise prevention programmes

**Business Value**:
- **Decision enabled**: Provides the demand-side numbers that PS-003's planning model converts into specific staff and bed requirements
- **Efficiency gain**: Replaces point estimates with confidence intervals — planners can explicitly communicate uncertainty to Finance Ministry
- **Quality improvement**: Demographic-weighted projection captures the non-linear effect of ageing that flat growth-rate assumptions miss

---

## Data Requirements

**Verified datasets** (all from `subhamjain/health-dataset-complete-singapore`):

| Dataset | File | Coverage | Use |
|---|---|---|---|
| Cancer mortality rate | `age-standardised-mortality-rate-for-cancer.csv` | 1990–2019 | Disease forecast |
| Stroke mortality rate | `age-standardised-mortality-rate-for-stroke.csv` | 1990–2019 | Disease forecast |
| IHD mortality rate | `age-standardised-mortality-rate-for-ischaemic-heart-disease.csv` | 1990–2019 | Disease forecast |
| Hospital admissions by age/sex | `hospital-admission-rate-by-age-and-sex.csv` | 2006–2020 | Admission projection |
| LTC admissions | `residential-long-term-care-admissions.csv` | sparse | Contextual only |

**External data required (publicly available — no credentials)**:
| Source | Data | Use |
|---|---|---|
| SingStat (singstat.gov.sg) | Resident population projections 2020–2035 by 5-year age band (low/medium/high scenarios) | Demographic weighting for admission projection |
| PS-001 output | `results/tables/utilisation_baseline.csv` | Historical admission rate baseline (already structured) |

**Known data limitations**:
- Disease data covers only cancer, stroke, IHD — **not** diabetes, dementia, respiratory, falls
- Admission data is not disaggregated by diagnosis — cannot link disease burden to service-type demand directly
- LTC admissions sparse — cannot statistically forecast; descriptive only
- All forecasts are national aggregate — no ward-type or facility-level disaggregation possible
- Population projections are external dependency; if SingStat data is unavailable, United Nations World Population Prospects can substitute

---

## Analytical Approach

**Disease burden forecasting**:
- ARIMA (statsmodels) for stationary or trend-stationary series
- Holt-Winters exponential smoothing for series with trend (cancer mortality shows long-term decline)
- Prophet (Meta) as a validation alternative — compare AIC and MAPE, use best performer
- Backtest: train on 1990–2014, test on 2015–2019

**Admission volume projection**:
- Cohort-component approach: rate × population, summed across age groups
- Run separately for each SingStat population scenario (low/medium/high growth)
- Decompose growth into: population size effect + age-structure shift effect + admission rate trend effect

**Platform**: Local Python (Polars for data processing; statsmodels/Prophet for modelling; Plotly for charts).  
**Language**: Python  
**Compute**: Minimal — all data fits in memory on a laptop

---

## Expected Outcomes and Deliverables

**Stakeholder Outcomes**:
- Quantified hospital admission volume projections (total and by age group) through 2035
- Disease mortality trajectory forecasts for cancer, stroke, IHD with confidence intervals
- A clear decomposition of how much admission growth is driven by demographics vs. rate changes

**Concrete Deliverables**:
- 📋 `results/metrics/disease_burden_forecast.csv` — annual projections for cancer/stroke/IHD mortality rates (2020–2030), with 80%/95% CI
- 📋 `results/metrics/admission_volume_projection.csv` — projected total and age-group admissions (2021–2035), 3 demographic scenarios
- 📋 `results/tables/forecast_validation_report.csv` — backtesting MAPE by model and disease
- 📋 `results/exports/demand_projections_for_planning.csv` — clean output formatted as PS-003 input
- 📊 `reports/figures/` — forecast charts with uncertainty bands for each disease and admission projection

---

## Dependencies and Assumptions

**Depends on**: PS-001 (utilisation baseline provides structured admission rate inputs)  
**Blocks**: PS-003 (demand projections are the primary planning model input)  
**Related to**: PS-001, PS-003

**Key Assumptions**:
- SingStat 2020–2035 population projections are publicly available and can be downloaded without a data sharing agreement
- Age-standardised mortality rates are interpretable as a proxy for disease burden intensity without diagnosis-linked admission data
- Admission rates by age group are stable enough for trend-based projection (to be validated in the backtesting step)

---

## Risks and Open Questions

- **Risk**: If SingStat population projections are not publicly downloadable, the UN World Population Prospects (public) will be substituted — this introduces a Singapore-specific accuracy trade-off; must be disclosed in outputs
- **Risk**: Only 3 diseases have mortality data; the forecasts cannot cover the full disease burden. Outputs must be clearly labelled as "cancer, stroke, IHD only" — not "all-cause"
- **Risk**: Admission data runs to 2020 (COVID-19 year) — 2020 may be a structural outlier; decision on whether to include or exclude must be documented
- **Open question**: Does the admission rate table use per-1,000 or per-10,000 denominator? Must confirm on first extraction before computing volumes
- **Open question**: Do the SingStat projections align with the same 5-year age bands as the admission table? If not, interpolation will be required

---

## Problem Statement Readiness Checklist

- [x] Data domains explicitly verified against `data-sources.md`
- [x] All infeasible analyses explicitly dropped with reason stated
- [x] External data dependency (SingStat) identified and flagged with a fallback (UN WPP)
- [x] Platform and technical feasibility confirmed (local Python/statsmodels/Prophet)
- [x] Problem statement can be decomposed into 5–10 user stories
- [x] Deliverable format and access method defined
- [x] PS-001 dependency and PS-003 downstream link both documented

---

## Priority Scoring

| Dimension | Score (1–5) | Rationale |
|---|---|---|
| Business Value | 5 | Demand projections are the non-negotiable foundation of any planning model |
| Feasibility | 4 | Data verified; one external dependency (SingStat) with identified fallback |
| Urgency | 5 | Blocks PS-003; must complete before resource planning can begin |
| **Total** | **14/15** | |
