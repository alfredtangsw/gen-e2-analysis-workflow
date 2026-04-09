# Domain Knowledge: Health Equity Metrics & KPIs

## Overview

Health equity analysis quantifies disparities in healthcare access, utilisation, and health outcomes across demographic groups. This guide defines standard equity metrics, calculation methods, and analytical frameworks for identifying underserved populations in Singapore's healthcare system.

**Important Data Constraint**: The available Singapore dataset (`subhamjain/health-dataset-complete-singapore`) provides demographic stratification by **age group** and **sex only**. Socioeconomic status and ethnicity data are **not available** in this dataset, which significantly limits the scope of equity analysis possible. All metrics in this guide are constrained to age and sex stratification unless external data is obtained.

## Related Problem Statements

- [PS-005: Healthcare Access Equity & Demographic Disparities Analysis](../objectives/problem_statements/ps-005-healthcare-equity-disparities.md)
- [PS-002: National Disease Burden Temporal Trends Analysis](../objectives/problem_statements/ps-002-disease-burden-temporal-trends.md)

## Related Stakeholders

- **Population Health Strategy Division, MOH**: Health equity policy formulation
- **Public Health & Preventive Medicine, MOH**: Community health program targeting
- **Healthcare Financing Division, MOH**: Subsidy targeting and financial access barriers
- **Community Health Organizations (NGOs, VWOs)**: Vulnerable population outreach

---

## Key Concepts and Terminology

### Health Disparity
**Definition**: A difference in health outcomes or health determinants between population subgroups  
**Relevance**: Identifies unequal burden of disease or unequal access to care  
**Example**: Elderly women have significantly higher hospital admission rates than elderly men for certain conditions

### Health Inequity
**Definition**: Health disparities that are avoidable, unnecessary, and unjust  
**Distinction from disparity**: Not all disparities are inequitable (e.g., higher admission rates in older age groups may be clinically appropriate); inequity implies systemic disadvantage  
**Relevance**: Equity analysis must distinguish clinically expected variation from systemic disadvantage

### Age-Standardisation
**Definition**: Statistical technique to remove confounding effect of different age distributions when comparing populations  
**Relevance**: Essential for comparing outcomes across time periods or groups with different age structures  
**Method**: Direct standardisation using WHO standard population weights  
**Formula**: `ASR = Σ(stratum-specific rate × standard population weight for stratum)`

### Disparity Ratio (Rate Ratio)
**Definition**: Ratio of health outcome rates between two groups  
**Formula**: `DR = Rate_disadvantaged_group / Rate_advantaged_group`  
**Interpretation**: DR = 1.0 means no disparity; DR > 1.0 means higher burden in disadvantaged group  
**Example**: If elderly (65+) admission rate = 400/1,000 and young adult (20–34) rate = 60/1,000, DR = 6.7

### Absolute Disparity (Rate Difference)
**Definition**: Arithmetic difference in rates between two groups  
**Formula**: `AD = Rate_highest_group - Rate_lowest_group`  
**Relevance**: Captures public health burden magnitude; important for resource targeting  
**Note**: Use alongside ratio; a large ratio with a small absolute difference may not be the priority

### Concentration Index
**Definition**: Measures degree to which health inequality is systematically associated with a socioeconomic indicator  
**Formula**: `CI = (2 / μ) × Cov(health_variable, socioeconomic_rank)`  
**Range**: −1 (all illness in lowest SES) to +1 (all illness in highest SES); 0 = perfect equality  
**Data Constraint**: Cannot be computed without SES data in the current dataset

### Excess Mortality (Preventable Deaths)
**Definition**: Deaths that would not have occurred if the disadvantaged group had the same mortality rate as the reference group  
**Formula**: `Excess deaths = (rate_disadvantaged - rate_reference) × population_disadvantaged`  
**Relevance**: Quantifies the public health cost of disparities in actionable terms

---

## Standard Metrics and KPIs

| Metric | Definition | Formula | Interpretation | Data Available |
|--------|-----------|---------|---------------|----------------|
| Disparity Ratio (age) | Rate ratio by age group | `Rate_65+ / Rate_20-34` | >1 = elderly burden | ✅ Direct |
| Disparity Ratio (sex) | Rate ratio by sex | `Rate_male / Rate_female` | >1 = male disadvantage | ✅ Direct |
| Absolute Rate Difference | Highest minus lowest group rate | `Rate_max - Rate_min` | Raw burden gap | ✅ Computed |
| Age-Standardised Rate | Age-adjusted rate for fair comparison | Direct standardisation formula | Controls for age structure | ✅ Computed |
| Temporal Disparity Trend | Change in disparity ratio over time | `DR_t - DR_{t-5}` | Narrowing/widening gap | ✅ Computed |
| Preventable Burden | Deaths/cases attributable to disparity | Excess rate × population | Health equity impact | ✅ Computed |
| Utilisation Equity Ratio | Actual utilisation / expected utilisation | `observed / age-sex-expected` | Under/over-utilisation | ✅ Computed |

---

## Feature Engineering Guidance

### Age Group Features
```python
import polars as pl

df = df.with_columns([
    # Disparity ratio: elderly vs working-age
    (pl.col('admission_rate_65plus') / pl.col('admission_rate_20_64'))
    .alias('elderly_disparity_ratio'),

    # Absolute gap: highest minus lowest age group rate
    (pl.col('admission_rate_65plus') - pl.col('admission_rate_0_14'))
    .alias('age_absolute_disparity'),

    # Normalised deviation from overall mean
    ((pl.col('admission_rate_by_group') - pl.col('mean_admission_rate'))
    / pl.col('mean_admission_rate'))
    .alias('deviation_from_mean'),
])
```

### Sex-Based Disparity Features
```python
df = df.with_columns([
    # Male-to-female disparity ratio
    (pl.col('admission_rate_male') / pl.col('admission_rate_female'))
    .alias('sex_disparity_ratio'),

    # Sex gap (absolute)
    (pl.col('admission_rate_male') - pl.col('admission_rate_female'))
    .alias('sex_absolute_gap'),
])
```

### Temporal Equity Trend Features
```python
# Disparity change: is inequity widening or narrowing?
df = df.with_columns([
    (pl.col('elderly_disparity_ratio') - pl.col('elderly_disparity_ratio').shift(5))
    .alias('disparity_5yr_change'),

    # Rolling mean disparity
    pl.col('elderly_disparity_ratio')
    .rolling_mean(window_size=3)
    .alias('disparity_rolling_3yr'),
])
```

### Expected vs Observed Utilisation
A key equity analysis technique: compare observed utilisation against demographically expected utilisation.
```python
# Compute age-sex standardised expected rate
# (requires external population structure data from Singstat)
df = df.with_columns([
    (pl.col('observed_admissions') / pl.col('expected_admissions_age_sex_adjusted'))
    .alias('standardised_utilisation_ratio'),
    # >1 = over-utilisation; <1 = under-utilisation relative to demographic need
])
```

---

## Analytical Methodologies

### Demographic Disparity Analysis (Available Data)
1. **Extract** hospital admission rate table stratified by age and sex (2006–2020)
2. **Pivot** to wide format: one row per year, columns per age-sex stratum
3. **Compute** rate ratios and absolute gaps across all age group pairs
4. **Test** statistical significance using chi-squared test or rate ratio confidence intervals
5. **Trend** each disparity metric over the 14-year period (2006–2020)

### Age-Standardisation Procedure
Use direct standardisation with WHO World Standard Population (2000–2025):
```python
# Example Polars implementation
who_weights = pl.DataFrame({
    'age_group': ['0-4', '5-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65+'],
    'standard_weight': [0.0886, 0.1721, 0.1716, 0.1482, 0.1200, 0.0875, 0.0653, 0.0467]
})
df_std = df.join(who_weights, on='age_group').with_columns([
    (pl.col('age_specific_rate') * pl.col('standard_weight')).alias('weighted_rate')
]).group_by('year').agg(pl.col('weighted_rate').sum().alias('age_std_rate'))
```

### Concentration Curve (Without SES)
Without SES data, use **age** as the ranking variable to construct a modified concentration curve:
1. Rank population groups by admission burden (lowest to highest)  
2. Plot cumulative % population (x-axis) vs cumulative % of admissions (y-axis)
3. Deviation from the diagonal = inequality; Gini-like index from area between curves

---

## Data Constraints and Mitigation

| Missing Data | Impact on Analysis | Mitigation |
|-------------|-------------------|------------|
| Socioeconomic status | Cannot analyse income-related disparities | Focus on age/sex; flag as limitation; recommend future data collection |
| Ethnicity/race | Cannot analyse Chinese/Malay/Indian/Others disparities | Flag as major limitation; reference published MOH ethnicity data for context |
| Regional/district data | Cannot assess geographic equity | National-level analysis only; recommend MOH regional data request |
| Individual-level records | Cannot control for comorbidities | Use population-level rates; acknowledge ecological fallacy risk |

**Recommendation**: Engage MOH to obtain NEHR (National Electronic Health Record) aggregated statistics by ethnicity and housing type (proxy for SES) before PS-005 full scope delivery.

---

## Common Pitfalls and Best Practices

### Pitfalls to Avoid
- **Conflating disparity with inequity**: Higher age-related admission rates may be clinically appropriate; investigate whether they represent unmet need or appropriate care
- **Ignoring multiple dimensions simultaneously**: Age and sex effects interact; always compute joint age-sex stratified rates, not just marginal effects
- **Comparing rates without age-standardisation**: Raw rates confounded by Singapore's aging population structure

### Best Practices
- **Always compute both ratio and absolute disparities**: A ratio can be high with small absolute burden; policy targeting uses absolute numbers
- **Track trends over time**: A snapshot disparity without trend is less actionable; 14 years of data enables meaningful trend analysis
- **Reference clinical norms**: Consult healthcare literature for expected male-female utilisation differences by condition before labelling them as inequities
- **Communicate uncertainty**: Disparity ratios based on small denominators have wide confidence intervals; always report CIs

---

## References and Sources

- **WHO Health Equity Assessment Toolkit**: https://www.who.int/data/gho/health-equity — Global health equity metrics framework
- **MOH Singapore Health Disparities**: https://www.moh.gov.sg/resources-statistics — Singapore-specific health equity context
- **Wagstaff A et al. (1991)**: On the measurement of inequalities in health. *Social Science & Medicine* — Concentration index methodology
- **Mackenbach JP, Kunst AE (1997)**: Measuring the magnitude of socioeconomic inequalities in health — Rate ratio and rate difference methods
- **Singapore Ministry of Social and Family Development**: https://www.msf.gov.sg — SES proxy indicators for Singapore

---

## Cross-References

### Related Domain Knowledge Files
- [Disease Burden Feature Engineering Guide](disease-burden-feature-engineering-guide.md) — Mortality rate calculation for outcome disparity
- [Healthcare Capacity & Utilization Metrics](healthcare-capacity-utilization-metrics-kpis.md) — Access and utilisation denominators

### Related Data Dictionary Entries
- [Disease Data Dictionary](../data-dictionary/disease_data.md) — Hospital admission rate table schema
- [External Reference Dictionary](../data-dictionary/external_reference.md) — WHO standard population weights

---

## Metadata

**Created**: 2026-04-08  
**Last Updated**: 2026-04-08  
**Updated By**: GitHub Copilot (automated generation)  
**Update Reason**: Initial creation to support PS-005 Healthcare Equity user stories  
**Version**: 1.0
