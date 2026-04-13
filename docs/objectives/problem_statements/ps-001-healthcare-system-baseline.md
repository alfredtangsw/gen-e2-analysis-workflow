# PS-001: Healthcare System Baseline — Workforce, Capacity & Utilisation

```yaml
problem_statement_id: PS-001
title: "Healthcare System Baseline — Workforce, Capacity & Utilisation"
analysis_category: Descriptive Analytics
priority: P0 (Critical)
platform: Local (development) → HEALIX/Databricks
primary_language: Python (Polars)
estimated_sprints: 2-3
status: Initialized
dependencies: None
```

---

## STEP 1.5 — Data Reality Check (Applied to this PS)

**Source dataset**: `subhamjain/health-dataset-complete-singapore` (Kaggle, ~3.5 MB, 35 CSV tables)

### Data Domains Available for this PS

| Domain | Tables | Coverage | Granularity |
|---|---|---|---|
| Workforce headcount | 7 tables (doctors, nurses, pharmacists, dentists, allied health, optometrists, midwives) | 2006–2019 | Annual, by sector (public/private) |
| Facility beds | 1 table: `health-facilities-and-beds-in-inpatient-facilities-public-not-for-profit-private.csv` | 2009–2020 | Annual, by facility type and sector |
| Primary care points | 1 table: `health-facilities-primary-care-dental-clinics-and-pharmacies.csv` | 2009–2020 | Annual, by clinic type |
| Hospital admissions | 1 table: `hospital-admission-rate-by-age-and-sex.csv` | 2006–2020 | Annual, by age group and sex |
| LTC admissions | 1 table: `residential-long-term-care-admissions.csv` | sparse, ~25 records | Annual, aggregate |
| Government expenditure | 1 table: `government-health-expenditure.csv` | 2006–2018 | Annual, **total only** |

### ✅ Feasible Analyses

- Workforce headcount trends by profession and sector (2006–2019)
- Workforce-to-population ratios by profession per year
- Bed capacity trends by facility type (acute, community, private) (2009–2020)
- Hospital admission rate trends by age group and sex (2006–2020)
- Admissions-per-bed proxy utilisation ratio (derived from admissions + bed count, same year)
- Government expenditure trend and cost per admission proxy (2006–2018)
- Staff-to-bed ratio trends by year (derived: workforce ÷ reported beds)
- Benchmarking against WHO nurse-to-bed / doctor-to-population standards (sourced externally)

### ❌ Infeasible Analyses (dropped — no data)

- Bed occupancy rates — **not in dataset** (only headcounts and bed counts; no patient-days or occupancy %)
- Expenditure by category (workforce vs infrastructure vs supplies) — **total govt spend only**
- ICU, step-down, or ward-type-specific bed breakdowns beyond facility-level groupings
- Supplies, consumables, or test kit inventory — **no data**
- Length-of-stay by diagnosis — **not in dataset**
- Real-time or sub-annual analysis — **annual data only**
- Regional/facility-level breakdown — **national aggregates only**

---

## Executive Summary

Currently, MOH directors and workforce planners lack a unified view of how Singapore's healthcare workforce, facility capacity, and utilisation have co-evolved over time. Data exists in separate reports across divisions, making it impossible to assess whether the system is **balanced** — whether staffing levels are appropriate for the facilities operated, and whether those facilities are being used commensurately with available capacity. By constructing an integrated historical baseline from the verified MOH Kaggle dataset (2006–2020), we can quantify workforce-to-bed ratios, trend trajectories, and utilisation proxies across all major healthcare domains, enabling evidence-based gap identification before any forecasting begins.

---

## Problem Statement Hypothesis

> We believe that integrating Singapore's workforce headcount, facility bed capacity, hospital admission rates, and government expenditure into a single time-series baseline for MOH planners and analysts will reveal whether the healthcare system is structurally balanced over the 2006–2020 period. We'll know we're successful when analysts can identify, with data, which profession-facility combinations are under-staffed or over-supplied relative to utilisation trends.

---

## Objectives

**Objective 1 — Workforce Headcount Trend Analysis (2006–2019)**
- Quantify growth in headcount for each profession (doctors, nurses, pharmacists, dentists, allied health) by sector (public vs private)
- Compute year-on-year growth rates and cumulative growth index (base 2006 = 100)
- Calculate workforce-per-10,000-population ratios using Singapore population estimates

**Objective 2 — Facility Capacity Trend Analysis (2009–2020)**
- Track total beds by facility type (acute hospitals, community hospitals, nursing homes, private hospitals) over time
- Track primary care access points (polyclinics, GP clinics, dental clinics) over time
- Compute beds-per-10,000-population ratios by year

**Objective 3 — Utilisation Proxy Analysis (2006–2020)**
- Analyse hospital admission rates by age group and sex over time
- Derive admissions-per-bed proxy for facility load (total admissions ÷ total beds, same year)
- Identify demographic groups with the highest and fastest-growing admission rates
- Analyse long-term care admission trends from available sparse data

**Objective 4 — System Balance Assessment**
- Compute staff-to-bed ratios by year (nurses-per-bed, doctors-per-bed) from workforce + facility tables
- Compare derived ratios against WHO reference benchmarks (sourced from `shared/data/2_external/`)
- Flag years where ratios diverge significantly from benchmarks
- Compute expenditure-per-admission proxy (govt expenditure ÷ estimated total admissions) for cost trend analysis

---

## Key Questions to Answer

1. How has each healthcare profession grown relative to the population (2006–2019)?
2. Have bed capacity additions kept pace with workforce growth and admission rate growth (2009–2019)?
3. Which age groups are driving the highest and fastest-growing hospital admission rates?
4. Are nurse-to-bed and doctor-to-bed ratios improving, worsening, or stable over time?
5. Is government health expenditure growing faster or slower than admission volumes?

---

## Stakeholders and Value Proposition

**Primary Stakeholders**:
- Workforce Planning Division, MOH — needs a baseline to justify hiring plans
- Healthcare Planning Division, MOH — needs capacity trends to underpin infrastructure decisions
- Healthcare Financing Division, MOH — needs expenditure-per-admission trends for budget framing

**Business Value**:
- **Decision enabled**: Provides the evidence base for PS-002 forecasting and PS-003 planning — no planning can proceed without it
- **Efficiency gain**: Replaces manually reconciled, siloed spreadsheets with a single auditable dataset
- **Risk reduction**: Identifies structural imbalances *before* they are projected forward into multi-year plans

---

## Data Requirements

**Verified datasets** (all sourced from `subhamjain/health-dataset-complete-singapore`):

| Dataset | File | Coverage | Use |
|---|---|---|---|
| Doctors | `number-of-doctors.csv` | 2006–2019, sector | Workforce trend |
| Nurses & Midwives | `number-of-nurses-and-midwives.csv` | 2008–2019, sector | Workforce trend |
| Pharmacists | `number-of-pharmacists.csv` | 2006–2019, sector | Workforce trend |
| Dentists | `number-of-dentists.csv` | 2006–2019, sector | Workforce trend |
| Allied Health | `number-of-allied-health-professionals.csv` | 2006–2019, sector | Workforce trend |
| Inpatient beds | `health-facilities-and-beds-in-inpatient-facilities-public-not-for-profit-private.csv` | 2009–2020 | Capacity trend |
| Primary care | `health-facilities-primary-care-dental-clinics-and-pharmacies.csv` | 2009–2020 | Access points |
| Hospital admissions | `hospital-admission-rate-by-age-and-sex.csv` | 2006–2020 | Utilisation proxy |
| LTC admissions | `residential-long-term-care-admissions.csv` | sparse | LTC utilisation |
| Govt expenditure | `government-health-expenditure.csv` | 2006–2018, total | Cost trend |

**External reference required**:
- Singapore resident population by year (SingStat or World Bank public data) — needed for per-capita ratios
- WHO nurse-to-bed and doctor-to-population reference benchmarks

**Known data limitations**:
- No occupancy rates — utilisation proxied from admission rates and bed counts only
- Expenditure is total government spend only — no category breakdown
- Some workforce tables start in 2008 (nurses) or later, limiting the earliest joint-variable years
- LTC admissions only ~25 records; suitable for trend observation, not statistical modelling
- All data is national aggregate only — no regional or facility-level breakdown

---

## Analytical Approach

Descriptive time-series analysis using Polars:
- Load each CSV, standardise year column, validate data types and ranges
- Join workforce, facility, and utilisation tables on `year`
- Compute derived metrics (ratios, growth rates, growth index)
- Compare against externally sourced benchmarks
- Output as clean parquet files for PS-002 and PS-003 consumption

**Platform**: Local Python (Polars + Plotly). Compute requirements are minimal (~3.5 MB data).
**Language**: Python (Polars primary; pandas only if Polars lacks join functionality)
**Batch processing**: All analysis is static batch at annual granularity

---

## Expected Outcomes and Deliverables

**Stakeholder Outcomes**:
- A single, auditable view of how workforce, beds, and admissions have moved together over 15 years
- Identification of specific years or professions where ratios diverged from WHO benchmarks
- A structured dataset ready for PS-002 forecasting and PS-003 planning

**Concrete Deliverables**:
- 📋 `results/tables/workforce_baseline.csv` — headcount by profession, sector, year (2006–2019)
- 📋 `results/tables/facility_baseline.csv` — beds and access points by type, year (2009–2020)
- 📋 `results/tables/utilisation_baseline.csv` — admission rates by age group, sex, year (2006–2020)
- 📋 `results/tables/expenditure_baseline.csv` — total govt spend by year (2006–2018)
- 📋 `results/metrics/system_balance_scorecard.csv` — staff-to-bed ratios, admissions-per-bed, expenditure-per-admission by year; benchmark flags
- 📊 `reports/figures/` — 5–8 publication-quality trend charts (workforce, capacity, utilisation, ratios)

---

## Dependencies and Assumptions

**Depends on**: None  
**Blocks**: PS-002 (demand forecasting needs admission rate baselines), PS-003 (planning model needs staff-to-bed ratios)  
**Related to**: PS-002, PS-003

**Key Assumptions**:
- Singapore resident population figures will be sourced from SingStat or World Bank (publicly available; no API key required)
- WHO benchmarks will be sourced from public WHO GHO data (no credentials required)
- The admission rate table reports per-1,000 population (to be verified on extraction)

---

## Risks and Open Questions

- **Risk**: Nurse and allied health data begin in 2008, not 2006 — the baseline joint dataset will be limited to 2009–2018 for full multi-variable analysis (the intersection of all table coverages)
- **Risk**: LTC admission record count is sparse (~25 records); trend analysis will be limited to observation only
- **Open question**: Do the profession tables include only registered headcount, or also active practitioners? (Affects ratio interpretation)
- **Open question**: Does the inpatient beds table separate acute from step-down beds within the same facility? (Affects staff-to-bed ratio specificity)

---

## Problem Statement Readiness Checklist

- [x] Data domains explicitly verified against `data-sources.md`
- [x] All infeasible analyses explicitly dropped with reason stated
- [x] Platform and technical feasibility confirmed (local Python/Polars)
- [x] Problem statement can be decomposed into 5–10 user stories
- [x] Deliverable format and access method defined
- [x] Feeds directly into PS-002 and PS-003

---

## Priority Scoring

| Dimension | Score (1–5) | Rationale |
|---|---|---|
| Business Value | 5 | Without a baseline, PS-002 and PS-003 have no foundation |
| Feasibility | 5 | All data explicitly in verified Kaggle dataset; tiny files |
| Urgency | 5 | Must complete first — blocks both downstream PS |
| **Total** | **15/15** | |
