# Domain Knowledge: Healthcare Capacity & Utilization Metrics

## Overview

Healthcare capacity analytics quantifies the relationship between physical infrastructure (beds, clinics, facilities) and the actual demand placed on them by the population. This guide defines standard metrics, benchmarks, and feature engineering patterns for capacity optimisation and utilization gap analysis relevant to Singapore's public healthcare system.

## Related Problem Statements

- [PS-003: Healthcare Capacity Optimization](../objectives/problem_statements/ps-003-healthcare-capacity-optimization.md)
- [PS-001: Healthcare Workforce Sustainability](../objectives/problem_statements/ps-001-healthcare-workforce-sustainability.md)

## Related Stakeholders

- **Healthcare Service Planning Division, MOH**: Uses capacity metrics for national infrastructure investment decisions
- **Hospital Administrators**: Monitor bed occupancy and utilisation efficiency at facility level
- **Finance & Infrastructure Development, MOH**: Prioritises capital investment based on capacity gap analysis
- **Intermediate & Long-Term Care Planning, MOH**: Models non-acute capacity expansion

---

## Key Concepts and Terminology

### Bed Occupancy Rate (BOR)
**Definition**: Percentage of available inpatient beds occupied on average during a period  
**Relevance**: Primary efficiency metric for acute hospital capacity; high BOR signals over-demand  
**Formula**: `BOR = (Patient bed-days used / Total available bed-days) × 100`  
**Benchmarks**: 85% is considered optimal for Singapore public hospitals; >90% indicates strain; <75% suggests excess capacity

### Available Beds
**Definition**: Staffed, equipped beds that are maintained for immediate use  
**Relevance**: Denominator for BOR; adjusted for seasonal closures and renovation  
**Note**: Singapore dataset provides total licensed beds by facility type and sector (public/private/not-for-profit)

### Hospital Admission Rate
**Definition**: Number of inpatient admissions per 1,000 population in a defined period  
**Relevance**: Primary demand metric; tracks healthcare utilisation and population morbidity trends  
**Formula**: `Rate = (Admissions / Mid-year population) × 1,000`

### Case Mix Index (CMI)
**Definition**: Average relative weight of all cases treated by a hospital; measures complexity of care  
**Relevance**: Higher CMI indicates more resource-intensive patients; affects capacity planning  
**Note**: Not directly available in Kaggle dataset; can be approximated by admission demographics

### Length of Stay (LOS)
**Definition**: Average number of days a patient remains hospitalised  
**Relevance**: Directly determines bed-day demand; reducing LOS frees capacity  
**Formula**: `LOS = Total inpatient bed-days / Total admissions`

### Bed-Population Ratio
**Definition**: Number of hospital beds per 10,000 population  
**Relevance**: Cross-sectional measure of healthcare capacity relative to population need  
**Formula**: `Ratio = (Total beds / Population) × 10,000`  
**Benchmarks**: OECD average ~45 per 10,000; Singapore public sector ~20 per 10,000 (excluding private)

### Long-Term Care Bed Ratio
**Definition**: Residential long-term care beds per 1,000 population aged 65+  
**Relevance**: Critical for aging population planning; Singapore's elderly cohort is growing rapidly  
**Benchmark**: 40–60 per 1,000 elderly in high-income countries

### Primary Care Accessibility
**Definition**: Number of primary care general practitioner (GP) and polyclinic clinics per 10,000 population  
**Relevance**: First-line care availability reduces pressure on acute hospitals  
**Singapore context**: MOH targets a primary care density that enables walk-in access within 15 minutes

---

## Standard Metrics and KPIs

| Metric | Definition | Formula | Typical Range | Use Case | Data Available |
|--------|-----------|---------|--------------|----------|----------------|
| Bed Occupancy Rate (BOR) | % beds in use | `(bed-days used / available bed-days) × 100` | 75–90% | Capacity strain detection | Proxy from admission rate |
| Bed-Population Ratio | Beds per 10,000 pop | `(beds / population) × 10,000` | 15–60 | Cross-sectional comparison | ✅ Direct |
| Hospital Admission Rate | Admissions per 1,000 pop | `(admissions / population) × 1,000` | 100–200 | Demand trending | ✅ Direct (by age/sex) |
| Long-Term Care Admission Rate | LTC admissions per 1,000 elderly | `(LTC admissions / pop 65+) × 1,000` | 20–50 | Elderly care demand | ✅ Direct |
| Primary Care Density | GP + polyclinic clinics per 10,000 pop | `(primary clinics / population) × 10,000` | 5–15 | Access assessment | ✅ Direct |
| Capacity Growth Rate | Annual % change in beds | `(beds_t - beds_{t-1}) / beds_{t-1} × 100` | 2–5% | Supply trend | Computed |
| Utilisation-Capacity Ratio | Admission rate / bed ratio | `admission_rate / bed_ratio` | — | Gap detection proxy | Computed |

---

## Feature Engineering Guidance

### Temporal Features
- **Capacity trend (CAGR)**: Compound annual growth rate of beds over 5, 10-year windows
- **Utilisation trend**: Year-over-year change in admission rate by age group
- **Demand-Supply ratio**: Normalised admission rate divided by bed capacity
- **Lag features**: Beds at t-1, t-2 to capture delayed infrastructure response to demand

### Demand Driver Features
- **Elderly ratio**: Population aged 65+/total population — primary driver of acute and LTC demand
- **Age-specific admission rates**: Weighted contribution of each age group to total admissions
- **Demographic shift index**: Rate of change in elderly proportion YoY

### Sector Decomposition Features
- **Public sector share**: Public beds / total beds — measures government capacity commitment
- **Private sector growth**: Private bed CAGR — signals market response to unmet public demand
- **Sector-gap**: Difference in capacity growth rates between public and private sectors

### Derived Efficiency Metrics
```python
import polars as pl

df = df.with_columns([
    # Demand-supply proxy ratio (higher = more strain)
    (pl.col('admission_rate_per_1000') / pl.col('beds_per_10000'))
    .alias('utilisation_capacity_ratio'),

    # YoY bed growth
    ((pl.col('beds') - pl.col('beds').shift(1)) / pl.col('beds').shift(1) * 100)
    .alias('bed_growth_pct'),

    # Elderly demand index
    (pl.col('admission_rate_65plus') * pl.col('elderly_population_share'))
    .alias('elderly_demand_index'),
])
```

### Domain-Specific Patterns

#### Lagged Infrastructure Response
Healthcare infrastructure investment decisions are made 3–5 years before capacity comes online. Feature engineering should capture this lag:
- Create rolling 3-year demand growth to predict future capacity requirements
- Compare demand trend at t-3 against capacity change at t

#### Sector Shift Pattern
Singapore has seen increasing private sector capacity as public capacity constrains. Modelling the private sector "safety valve" effect is important:
- Engineer `private_share_growth_rate` as signal of public sector strain

---

## Data Quality Considerations

### Proxy BOR Estimation
The Kaggle dataset does not provide direct bed-days or BOR. Use admission rate × average LOS as a proxy. Acknowledge this limitation explicitly.
- **Detection**: Missing direct occupancy data
- **Mitigation**: `proxy_BOR = admission_rate × assumed_ALOS / bed_days_available`; assume ALOS based on MOH published reports (5–6 days for Singapore acute hospitals)

### Sector Naming Inconsistency
The dataset uses slightly varying labels ("Public Sector" / "Public") across tables.
- **Detection**: Value counts check after loading
- **Mitigation**: Normalise to `public` / `private` / `nfp` (not-for-profit) using string cleaning

### Population Denominator
Capacity metrics require population data not in the Kaggle dataset.
- **Mitigation**: Use Singapore Singstat population figures (public, easily accessible); 2006–2019 annual estimates

---

## Analytical Methodologies

### Capacity Gap Analysis
1. Calculate observed demand (admission rate × population)
2. Estimate capacity in bed-days (beds × 365 × target BOR)
3. Gap = demand − capacity; positive gap = shortage
4. Project gap using demographic trend extrapolation

### Shift-Share Analysis
Decompose capacity changes into:
- **National growth effect**: How much change is due to overall population growth?
- **Sector mix effect**: How much is from the shift between public/private/LTC?
- **Competitive effect**: Residual (specific sector outperformance or underperformance)

### Regression-Based Utilisation Modelling
Use historical admission rates as the dependent variable with age cohort distribution, beds per capita, and year as predictors:
```python
from statsmodels.regression.linear_model import OLS
# Polars → pandas for statsmodels
X = df_pd[['elderly_share', 'beds_per_10k', 'year_trend']]
y = df_pd['admission_rate']
model = OLS(y, sm.add_constant(X)).fit()
```

---

## Common Pitfalls and Best Practices

### Pitfalls to Avoid
- **Confusing licensed vs. operational beds**: Use staffed operational beds; licensed beds overstate capacity
- **Ignoring sector mix**: Aggregating public + private masks very different access dynamics
- **Static population denominator**: Always use year-specific population estimates, not a single base year
- **BOR > 100%**: Can occur with hallway beds/surge; cap at 100% for planning purposes

### Best Practices
- **Segment by facility type**: Acute hospital, community hospital, and long-term care have very different optimal BOR targets
- **Age-stratified analysis**: 65+ cohort drives disproportionate demand; always report age-specific trends
- **Cross-verify with workforce data**: Capacity is bounded by staffing; link PS-003 analysis to PS-001 workforce projections

---

## References and Sources

- **MOH Singapore — Health Facts**: https://www.moh.gov.sg/resources-statistics/singapore-health-facts — Annual capacity and utilisation statistics
- **OECD Health Statistics**: https://stats.oecd.org/index.aspx?DataSetCode=HEALTH_STAT — International benchmarks for beds, admissions, LOS
- **WHO Health System Performance**: https://www.who.int/data/gho/data/themes/topics/indicator-groups/indicator-group-details/GHO/hospital-beds — Global bed ratios
- **Aiken et al. (2014)**: Nurse-to-patient ratios and capacity strain — *The Lancet*
- **Singapore Singstat Population Data**: https://www.singstat.gov.sg/find-data/search-by-theme/population/population-and-population-structure

---

## Cross-References

### Related Domain Knowledge Files
- [Healthcare Workforce Metrics & KPIs](healthcare-workforce-metrics-kpis.md) — Workforce supply constraints on capacity
- [Time Series Forecasting Methods](time-series-forecasting-methods.md) — Methods for projecting future capacity needs

### Related Data Dictionary Entries
- [Disease Data Dictionary](../data-dictionary/disease_data.md) — Utilisation tables schema
- [External Reference Dictionary](../data-dictionary/external_reference.md) — Population denominator sources

---

## Metadata

**Created**: 2026-04-08  
**Last Updated**: 2026-04-08  
**Updated By**: GitHub Copilot (automated generation)  
**Update Reason**: Initial creation to support PS-003 Healthcare Capacity Optimization user stories  
**Version**: 1.0
