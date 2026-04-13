# Disease Burden & Mortality Trends: Feature Engineering Guide

**Domain**: Disease Burden Analysis & Epidemiological Metrics  
**Purpose**: Reference guide for mortality trend analysis, disease burden calculation, and epidemiological feature engineering  
**Related Problem Statements**: PS-002 (Demand Forecasting)  
**Last Updated**: 2026-04-13

---

## Overview

Disease burden analytics quantifies the impact of diseases on population health through mortality and morbidity metrics. This guide defines standard epidemiological metrics, calculation formulas, and feature engineering patterns for temporal trend analysis.

## Core Metrics & Definitions

### 1. Disability-Adjusted Life Years (DALYs)

**Definition**: Comprehensive measure combining years of life lost (YLL) and years lived with disability (YLD)

**Formula**:
```
DALY = YLL + YLD
```

**Unit**: Years of healthy life lost

**Purpose**: Enable comparison of disease burden across different conditions (e.g., infectious vs. chronic diseases)

**Interpretation**:
- 1 DALY = 1 lost year of healthy life
- Higher DALYs = greater disease burden
- Used for priority-setting and resource allocation

---

### 2. Years of Life Lost (YLL)

**Definition**: Years of life lost due to premature mortality

**Formula**:
```
YLL = Number of deaths × Reference life expectancy at age of death
```

**Reference Standard**: WHO standard life expectancy tables

**Calculation Example**:
- Death at age 50
- Reference life expectancy: 85 years
- YLL = 1 death × (85 - 50) = 35 years

**Polars Implementation**:
```python
import polars as pl

df = df.with_columns([
    ((pl.col('reference_life_expectancy') - pl.col('age_at_death')) * pl.col('death_count'))
    .alias('YLL')
])
```

---

### 3. Years Lived with Disability (YLD)

**Definition**: Years lived in states of less than full health

**Formula**:
```
YLD = Prevalence × Disability weight × Duration
```

**Disability Weights**: Range 0 (perfect health) to 1 (equivalent to death)

**Example**:
- 1,000 cases of diabetes
- Disability weight: 0.049 (mild disability)
- Duration: 30 years (chronic condition)
- YLD = 1,000 × 0.049 × 30 = 1,470 years

**Comorbidity Adjustment** (multiplicative model):
```
Combined_disability_weight = 1 - (1 - w1) × (1 - w2) × ... × (1 - wn)
```

---

### 4. Age-Standardized Mortality Rate (ASMR)

**Definition**: Mortality rate adjusted for age distribution differences to enable fair comparisons

**Direct Standardization Method**:
```
ASMR = Σ[(deaths_i / population_i) × standard_population_i] / Σ(standard_population_i) × 100,000
```
where `i` = age group

**Unit**: Deaths per 100,000 population

**Standard Populations**:
- WHO World Standard Population 2000-2025
- Segi World Population (older standard)

**Polars Implementation**:
```python
# Load standard population weights
std_pop = pl.read_csv('data/2_external/who_standard_population.csv')

# Calculate age-specific rates
df_rates = df.group_by(['year', 'age_group']).agg([
    (pl.col('deaths').sum() / pl.col('population').sum() * 100000).alias('age_specific_rate')
])

# Join with standard population
df_asmr = df_rates.join(std_pop, on='age_group', how='left')

# Calculate ASMR
df_asmr = df_asmr.group_by('year').agg([
    (pl.col('age_specific_rate') * pl.col('std_population')).sum() / pl.col('std_population').sum()
    .alias('ASMR')
])
```

---

### 5. Standardized Mortality Ratio (SMR)

**Definition**: Ratio of observed to expected deaths

**Formula**:
```
SMR = (Observed deaths / Expected deaths) × 100
```

**Interpretation**:
- SMR > 100: Higher mortality than expected
- SMR = 100: Mortality as expected
- SMR < 100: Lower mortality than expected

**Use Cases**:
- Identify high-risk populations
- Evaluate healthcare quality (hospital SMRs)
- Geographic comparisons

---

### 6. Crude Mortality Rate

**Definition**: Total deaths per population without age adjustment

**Formula**:
```
CMR = (Total deaths / Total population) × 100,000
```

**Unit**: Deaths per 100,000 population

**Limitation**: Confounded by age structure (older populations have higher crude rates)

**When to Use**: Descriptive analysis within single population over time

---

### 7. Cause-Specific Mortality Rate

**Definition**: Deaths from a specific cause per population

**Formula**:
```
CSMR = (Deaths from cause X / Total population) × 100,000
```

**ICD Classification**: Uses ICD-10 or ICD-11 codes

**Example**:
- Cardiovascular disease deaths: 2,500
- Population: 5,000,000
- CSMR = (2,500 / 5,000,000) × 100,000 = 50 per 100,000

---

### 8. Proportional Mortality

**Definition**: Percentage of all deaths attributable to a specific cause

**Formula**:
```
Proportional Mortality (%) = (Deaths from cause X / Total deaths) × 100
```

**Use Cases**:
- Identify leading causes of death
- Prioritize public health interventions
- Track epidemiological transition (infectious → chronic diseases)

---

## Trend Analysis Methodologies

### Annual Percent Change (APC)

**Purpose**: Quantify year-over-year change in mortality rates

**Formula**:
```
APC = [(Rate_year2 / Rate_year1) - 1] × 100
```

**Interpretation**:
- APC > 0: Increasing trend
- APC < 0: Decreasing trend

**Polars Implementation**:
```python
df = df.sort('year').with_columns([
    ((pl.col('ASMR') / pl.col('ASMR').shift(1)) - 1) * 100
    .alias('APC')
])
```

---

### Average Annual Percent Change (AAPC)

**Purpose**: Summarize long-term trends with single metric

**Formula**:
```
AAPC = (exp[Σ(w_i × log(1 + APC_i / 100))] - 1) × 100
```
where `w_i` = weight for each segment

**Use Case**: Summarize 30-year trend in single number

---

### Joinpoint Regression

**Purpose**: Identify change points in mortality trends

**Method**:
1. Fit piecewise linear regression with varying number of joinpoints
2. Select model with best fit (e.g., BIC criterion)
3. Estimate APC for each segment

**Example**: Lung cancer mortality
- 1990-2005: APC = +2.5% (increasing)
- 2005-2015: APC = -1.8% (decreasing) ← *joinpoint at 2005*
- 2015-2023: APC = -3.2% (accelerating decrease)

**Python Package**: `pyjoinpoint` or R's `joinpoint`

---

### Age-Period-Cohort (APC) Models

**Purpose**: Separate effects of:
- **Age**: Risk by current age
- **Period**: Calendar time effects (e.g., medical advances, policy changes)
- **Birth cohort**: Effects specific to year of birth

**Model**:
```
log(Rate) = Age effect + Period effect + Cohort effect
```

**Challenge**: Identifiability problem (Age = Period - Cohort)

**Solutions**:
- Constrained models
- Drift parameter interpretation

---

## Feature Engineering Patterns

### Temporal Features

#### Rolling Averages (Smoothing)

```python
import polars as pl

# 3-year moving average
df = df.sort('year').with_columns([
    pl.col('ASMR').rolling_mean(window_size=3, min_periods=1)
    .over('disease')
    .alias('ASMR_3yr_avg')
])

# 5-year moving average
df = df.with_columns([
    pl.col('ASMR').rolling_mean(window_size=5, min_periods=3)
    .over('disease')
    .alias('ASMR_5yr_avg')
])
```

#### Lagged Features

```python
# Prior year rate
df = df.sort('year').with_columns([
    pl.col('ASMR').shift(1).over('disease').alias('ASMR_lag1')
])

# 5-year lagged rate
df = df.with_columns([
    pl.col('ASMR').shift(5).over('disease').alias('ASMR_lag5')
])
```

#### Growth Metrics

```python
# Year-over-year % change
df = df.sort('year').with_columns([
    ((pl.col('ASMR') / pl.col('ASMR').shift(1)) - 1) * 100
    .over('disease')
    .alias('ASMR_yoy_pct_change')
])

# Compound Annual Growth Rate (CAGR)
# CAGR = (Ending Value / Beginning Value) ^ (1/number of years) - 1
df_cagr = df.group_by('disease').agg([
    pl.col('ASMR').filter(pl.col('year') == pl.col('year').max()).first().alias('ending_rate'),
    pl.col('ASMR').filter(pl.col('year') == pl.col('year').min()).first().alias('beginning_rate'),
    (pl.col('year').max() - pl.col('year').min()).alias('years')
]).with_columns([
    (((pl.col('ending_rate') / pl.col('beginning_rate')) ** (1 / pl.col('years'))) - 1) * 100
    .alias('CAGR')
])
```

---

### Age-Related Features

#### Age Group-Specific Rates

```python
# Calculate rates by age group
df_age_rates = df.group_by(['year', 'disease', 'age_group']).agg([
    (pl.col('deaths').sum() / pl.col('population').sum() * 100000).alias('age_specific_rate')
])
```

#### Premature Mortality Indicator

```python
# Deaths before age 70
df = df.with_columns([
    pl.when(pl.col('age_at_death') < 70)
    .then(pl.col('deaths'))
    .otherwise(0)
    .alias('premature_deaths')
])

# Premature mortality rate
df_premature = df.group_by(['year', 'disease']).agg([
    (pl.col('premature_deaths').sum() / pl.col('population').sum() * 100000)
    .alias('premature_mortality_rate')
])
```

#### Age Structure Impact

```python
# Difference between crude and age-standardized rates
df = df.with_columns([
    (pl.col('crude_rate') - pl.col('ASMR')).alias('age_structure_effect')
])
```

---

### Geographical Features

#### Urban vs. Rural Rates

```python
df_geo = df.group_by(['year', 'disease', 'urban_rural']).agg([
    (pl.col('deaths').sum() / pl.col('population').sum() * 100000).alias('mortality_rate')
])

# Calculate urban-rural gap
df_gap = df_geo.pivot(
    values='mortality_rate',
    index=['year', 'disease'],
    columns='urban_rural',
    aggregate_function='first'
).with_columns([
    (pl.col('Urban') - pl.col('Rural')).alias('urban_rural_gap')
])
```

#### Regional Variation

```python
# Coefficient of variation across regions
df_regional_cv = df.group_by(['year', 'disease']).agg([
    (pl.col('ASMR').std() / pl.col('ASMR').mean() * 100).alias('regional_CV')
])
```

---

### Categorical Encodings

#### ICD Chapter Grouping

```python
# Map ICD-10 codes to chapter groups
icd_chapter_mapping = {
    'A00-B99': 'Infectious diseases',
    'C00-D48': 'Neoplasms',
    'I00-I99': 'Circulatory diseases',
    'J00-J99': 'Respiratory diseases',
    'K00-K93': 'Digestive diseases',
    # ... etc
}

df = df.with_columns([
    pl.col('icd10_code').map_dict(icd_chapter_mapping).cast(pl.Categorical).alias('disease_group')
])
```

#### Age Group Categories

```python
# Standard WHO age groups
df = df.with_columns([
    pl.when(pl.col('age') < 5).then(pl.lit('0-4'))
    .when(pl.col('age') < 15).then(pl.lit('5-14'))
    .when(pl.col('age') < 25).then(pl.lit('15-24'))
    .when(pl.col('age') < 45).then(pl.lit('25-44'))
    .when(pl.col('age') < 65).then(pl.lit('45-64'))
    .when(pl.col('age') < 85).then(pl.lit('65-84'))
    .otherwise(pl.lit('85+'))
    .cast(pl.Categorical)
    .alias('age_group_who')
])
```

---

## Data Quality Considerations

### Common Data Quality Issues

1. **Vital Registration Incompleteness**
   - Many countries <90% death registration coverage
   - **Impact**: Underestimation of mortality burden
   - **Solution**: Completeness adjustment factors

2. **Ill-Defined Causes of Death**
   - "Old age", "cardiac arrest", "respiratory failure" (non-specific)
   - **Threshold**: <20% garbage codes acceptable
   - **Solution**: Statistical redistribution algorithms

3. **ICD Coding Quality**
   - Miscoding of underlying vs. immediate cause
   - **Impact**: Misattribution of deaths
   - **Solution**: Clinical review, coding training

4. **Age Heaping**
   - Age reported in multiples of 5 or 10
   - **Detection**: Whipple's Index, Myers' Blended Index
   - **Solution**: Smoothing algorithms

5. **Neonatal & Child Death Under-reporting**
   - Especially in low-resource settings
   - **Impact**: Underestimated child mortality
   - **Solution**: Capture-recapture methods, household surveys

### Validation Approaches

#### Data Quality Index

```python
# Calculate % garbage codes
df_quality = df.group_by('year').agg([
    (pl.col('icd10_code').filter(pl.col('icd10_code').is_in(GARBAGE_CODES)).count() / 
     pl.col('icd10_code').count() * 100)
    .alias('garbage_code_pct')
])

# Flag years with poor quality
df_quality = df_quality.with_columns([
    (pl.col('garbage_code_pct') > 20).alias('quality_flag')
])
```

#### Triangulation with Multiple Sources

```python
# Compare vital registration with hospital discharge data
df_comparison = df_vital_reg.join(
    df_hospital_discharge,
    on=['year', 'disease'],
    how='outer',
    suffix='_hospital'
).with_columns([
    (pl.col('deaths') / pl.col('deaths_hospital') * 100).alias('concordance_pct')
])
```

---

## International Benchmarks

### WHO Global Health Estimates (GHE)

- **Coverage**: 195 countries, 2000-2021
- **Disease Categories**: 23 Global Burden of Disease groups
- **Age Groups**: <1, 1-4, then 5-year groups to 85+
- **Metrics**: Deaths, DALYs, YLLs, YLDs by cause, age, sex

### IHME Global Burden of Disease (GBD 2023)

- **Coverage**: 204 countries/territories
- **Diseases**: 463 diseases and injuries
- **Risk Factors**: 88 environmental, behavioral, metabolic risks
- **Uncertainty Intervals**: 95% UI for all estimates
- **Update Frequency**: Annual with complete time series re-estimation

### Singapore Context

**Top Causes of Death (2021)**:
1. Cancer (28% of deaths)
2. Pneumonia (18%)
3. Cardiovascular disease (17%)
4. External causes (injuries, 5%)

**Leading Cancer Types**:
- Lung cancer
- Colorectal cancer  
- Breast cancer (females)

**Age-Standardized Death Rate**: ~350 per 100,000 (2021)

---

## Calculation Examples

### Example 1: Age-Standardized Mortality Rate

```python
import polars as pl

# Load data
df_deaths = pl.read_csv('data/1_raw/mortality_data.csv')
std_pop = pl.read_csv('data/2_external/who_standard_population.csv')

# Calculate age-specific rates
df_rates = df_deaths.group_by(['year', 'disease', 'age_group']).agg([
    (pl.col('deaths').sum()).alias('total_deaths'),
    (pl.col('population').mean()).alias('avg_population')
]).with_columns([
    (pl.col('total_deaths') / pl.col('avg_population') * 100000).alias('age_specific_rate')
])

# Join with standard population
df_asmr = df_rates.join(std_pop, on='age_group', how='left')

# Calculate ASMR
df_asmr = df_asmr.group_by(['year', 'disease']).agg([
    (pl.col('age_specific_rate') * pl.col('std_population_weight')).sum()
    .alias('ASMR_per_100k')
])

print(df_asmr)
```

### Example 2: DALY Calculation

```python
# YLL calculation
df_yll = df_deaths.with_columns([
    (pl.col('deaths') * (pl.col('reference_life_expectancy') - pl.col('age_at_death')))
    .alias('YLL')
])

# YLD calculation (requires prevalence data)
df_yld = df_prevalence.with_columns([
    (pl.col('prevalent_cases') * pl.col('disability_weight') * pl.col('avg_duration'))
    .alias('YLD')
])

# Combine to DALY
df_burden = df_yll.join(df_yld, on=['year', 'disease'], how='outer')
df_burden = df_burden.with_columns([
    (pl.col('YLL').fill_null(0) + pl.col('YLD').fill_null(0)).alias('DALY')
])
```

---

## Authoritative Sources

### 1. IHME Global Burden of Disease Study 2023
- **URL**: https://www.healthdata.org/research-analysis/gbd
- **Content**: Most comprehensive disease burden data globally
- **Methodology**: Bayesian meta-regression (DisMod-MR 2.1)
- **GBD Results Tool**: https://vizhub.healthdata.org/gbd-results/

### 2. WHO Global Health Estimates
- **URL**: https://www.who.int/data/global-health-estimates
- **Content**: Mortality and disease burden by cause, age, sex, country (2000-2021)
- **Methods**: Direct standardization, ICD-10 coding

### 3. SEER Cancer Statistics Review
- **URL**: https://seer.cancer.gov/statistics/
- **Content**: Age-adjustment methodologies, standard populations
- **Relevance**: Cancer burden metrics

### 4. WHO Methods and Data Sources for Global Burden of Disease Estimates 2000-2019
- **Document**: Technical paper
- **Content**: DALY methodology, disability weights, life tables

### 5. Singapore Ministry of Health Statistical Reports
- **URL**: https://www.moh.gov.sg/resources-statistics
- **Content**: Mortality statistics, principal causes of death, age-standardized rates
- **Frequency**: Annual

---

## References

1. Murray, C. J., et al. (2020). "Global burden of 87 risk factors in 204 countries and territories, 1990–2019: a systematic analysis for the Global Burden of Disease Study 2019." *The Lancet*, 396(10258), 1223-1249.

2. WHO (2021). *WHO methods and data sources for global burden of disease estimates 2000-2019*. Geneva: World Health Organization.

3. Ahmad, O. B., et al. (2001). *Age standardization of rates: a new WHO standard*. Geneva: World Health Organization.

4. Kim, H. J., et al. (2000). "Permutation tests for joinpoint regression with applications to cancer rates." *Statistics in Medicine*, 19(3), 335-351.

5. Salomon, J. A., et al. (2015). "Disability weights for the Global Burden of Disease 2013 study." *The Lancet Global Health*, 3(11), e712-e723.
