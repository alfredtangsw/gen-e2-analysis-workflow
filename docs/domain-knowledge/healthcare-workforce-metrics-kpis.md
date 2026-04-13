# Healthcare Workforce Planning: Metrics & KPIs

**Domain**: Healthcare Workforce Planning  
**Purpose**: Reference guide for workforce analytics, capacity ratios, and planning benchmarks  
**Related Problem Statements**: PS-001 (Baseline), PS-003 (Resource Planning)  
**Last Updated**: 2026-04-13

---

## Overview

Healthcare workforce analytics focuses on ensuring adequate supply of healthcare professionals to meet population health needs. This document defines key metrics, calculation methods, and international benchmarks for workforce planning.

## Key Performance Indicators (KPIs)

### 1. Health Workers Density

**Definition**: Number of health professionals per 10,000 population

**Formula**:
```
Density = (Number of health workers / Total population) × 10,000
```

**Unit**: Health workers per 10,000 population

**Common Categories**:
- Physicians (medical doctors)
- Nurses and midwives
- Dentists
- Pharmacists
- Community health workers

**Benchmarks**:
- **WHO Minimum Threshold**: 44.5 health workers per 10,000 for essential health service coverage
- **UHC Target**: 80-100+ health workers per 10,000
- **Singapore (2023)**: ~90 total health workers per 10,000

---

### 2. Physicians Density

**Definition**: Number of practicing physicians per 10,000 population

**Formula**:
```
Physicians Density = (Number of practicing physicians / Total population) × 10,000
```

**Benchmarks**:
- **WHO Minimum**: 10 physicians per 10,000
- **OECD Average (2024)**: ~34 physicians per 10,000
- **Singapore (2023)**: ~25 physicians per 10,000
- **High-Income Target**: 30-40 per 10,000

---

### 3. Nurses & Midwives Density

**Definition**: Number of practicing nurses and midwives per 10,000 population

**Formula**:
```
Nursing Density = (Number of practicing nurses & midwives / Total population) × 10,000
```

**Benchmarks**:
- **WHO Minimum**: 30 nurses/midwives per 10,000
- **OECD Range**: 50-180 per 10,000 (varies widely)
- **Singapore (2023)**: ~65 nurses per 10,000
- **High-Income Target**: 80-120 per 10,000

---

### 4. Workforce Turnover Rate

**Definition**: Percentage of healthcare workers leaving their positions within a year

**Formula**:
```
Turnover Rate (%) = (Number of separations / Average number of employees) × 100
```

**Interpretation**:
- **15-20%**: Typical baseline for healthcare sector
- **>25%**: Indicates retention issues
- **<10%**: Indicates low workforce mobility (could be positive or negative)

**Segmentation**: Calculate separately by:
- Job category (physicians, nurses, allied health)
- Sector (public vs. private)
- Geographic region (urban vs. rural)

---

### 5. Vacancy Rate

**Definition**: Percentage of unfilled healthcare positions

**Formula**:
```
Vacancy Rate (%) = (Number of vacant positions / Total authorized positions) × 100
```

**Critical Thresholds**:
- **<5%**: Healthy vacancy level (normal recruitment lag)
- **5-10%**: Moderate shortage
- **>10%**: Severe staffing shortage

**Use Cases**:
- Identify specialties with critical shortages
- Geographic gap analysis (urban vs. rural vacancies)
- Inform recruitment strategy

---

### 6. Staff-to-Population Ratios

**Definition**: Balance between healthcare workforce and population served

**Common Ratios**:
- **Doctor-to-population**: 1:300-500 (urban primary care), 1:800-1200 (rural)
- **Nurse-to-patient** (hospital): 1:4-6 (general ward), 1:1-2 (ICU)
- **Specialist ratios**: Varies by specialty (e.g., 1:10,000 for cardiologists)

**Formula**:
```
Staff Ratio = Population served / Number of staff
```

---

## Calculation Methodologies

### Age-Standardization for Workforce Density

**Purpose**: Account for different age distributions when comparing regions

**Method**:
```
Std_Density = Σ[(workers_i / population_i) × std_population_i] / Σ(std_population_i) × 10,000
```
where `i` = age group

**Standard Population**: Use WHO World Standard Population 2000-2025

---

### Full-Time Equivalent (FTE) Adjustment

**Purpose**: Convert part-time workers to full-time equivalents

**Formula**:
```
FTE = Σ(hours_worked / standard_full_time_hours)
```

**Example**:
- 1 full-time physician (40 hrs/week) = 1.0 FTE
- 2 part-time physicians (20 hrs/week each) = 1.0 FTE

---

### Workforce Forecasting Models

### Stock-Flow Model

**Purpose**: Project future workforce supply

**Formula**:
```
Supply_t = Supply_(t-1) + Inflows_t - Outflows_t
```

**Inflows**:
- New graduates from medical/nursing schools
- Foreign-trained professionals (immigration)
- Re-entrants (return from career break)

**Outflows**:
- Retirements (age-based)
- Deaths (mortality tables)
- Emigration (to other countries)
- Career changes (exit from profession)

**Projection Period**: Typically 10-20 years

---

### Demand Forecasting

**Population-Based Needs Assessment**:
```
Required_Workers = Population × Service_utilization_rate × Time_per_service / Available_time_per_worker
```

**Disease Burden-Based**:
```
Required_Specialists = Disease_prevalence × % requiring specialist care / Specialist_capacity
```

---

### Gap Analysis

**Purpose**: Compare supply vs. demand

**Formula**:
```
Gap = Projected_Demand - Projected_Supply
Gap_Rate (%) = (Gap / Projected_Demand) × 100
```

**Segmentation**:
- By specialty (general practice, surgery, pediatrics, etc.)
- By geography (region, urban/rural)
- By sector (public, private, community)

---

## Feature Engineering Patterns

### Time-Based Features

```python
import polars as pl

# Year-over-year growth rate
df = df.with_columns([
    ((pl.col('workforce_count') / pl.col('workforce_count').shift(1)) - 1)
    .over('occupation')
    .alias('yoy_growth_rate')
])

# Rolling 3-year average (smoothing)
df = df.with_columns([
    pl.col('density').rolling_mean(window_size=3, by='year')
    .over('occupation')
    .alias('density_3yr_avg')
])

# Retirement cohort projection
df = df.with_columns([
    pl.when(pl.col('age') >= 60)
    .then(pl.lit(1))
    .otherwise(pl.lit(0))
    .alias('retirement_cohort_5yr')
])
```

### Derived Metrics

```python
# Dependency ratio
df = df.with_columns([
    (pl.col('population_65plus') / pl.col('working_age_workforce'))
    .alias('dependency_ratio')
])

# Workforce sustainability index
df = df.with_columns([
    (pl.col('new_entrants') / pl.col('expected_retirements'))
    .alias('sustainability_index')
])

# Geographic maldistribution index
df_geo = df.group_by('region').agg([
    (pl.col('density_urban').mean() / pl.col('density_rural').mean())
    .alias('maldistribution_index')
])

# Skill-mix ratio
df = df.with_columns([
    (pl.col('specialist_count') / pl.col('generalist_count'))
    .alias('skill_mix_ratio')
])
```

### Categorical Encodings

```python
# Encode sector
df = df.with_columns([
    pl.col('sector').cast(pl.Categorical)
])

# Create location category
df = df.with_columns([
    pl.when(pl.col('population_density') > 5000)
    .then(pl.lit('Urban'))
    .when(pl.col('population_density') > 1000)
    .then(pl.lit('Suburban'))
    .otherwise(pl.lit('Rural'))
    .cast(pl.Categorical)
    .alias('location_category')
])

# Binary full-time indicator
df = df.with_columns([
    (pl.col('hours_per_week') >= 35).alias('is_fulltime')
])
```

---

## Data Quality Considerations

### Common Issues

1. **Incomplete Workforce Registries**
   - Inactive practitioners not removed
   - Retired professionals still listed
   - **Impact**: Overestimation of available workforce

2. **Dual Employment**
   - Professionals working in multiple facilities
   - Counted multiple times in datasets
   - **Impact**: Overestimation by 10-20%

3. **Private Sector Data Gaps**
   - Less comprehensive reporting than public sector
   - **Impact**: Underestimation of total workforce capacity

4. **Migration Data**
   - Inflows/outflows of foreign-trained workers not tracked
   - **Impact**: Inaccurate supply projections

5. **Specialty Misclassification**
   - Self-reported specialty vs. actual practice
   - **Impact**: Incorrect specialty-specific workforce counts

### Validation Approaches

**Cross-Reference with Professional Licensing Boards**:
```python
# Validate against active license registry
df_valid = df.join(
    license_registry.filter(pl.col('status') == 'Active'),
    on='license_number',
    how='inner'
)
```

**Triangulate with Payroll Data**:
```python
# Compare self-reported employment with HR records
df_verified = df.join(payroll_data, on='employee_id', how='left')
df_discrepancies = df_verified.filter(pl.col('payroll_match').is_null())
```

**Periodic Workforce Surveys**:
- Conduct every 2-3 years
- Include practice patterns, workload, retirement intentions

**International Database Comparison**:
- WHO Global Health Workforce Observatory (GHWO)
- OECD Health Statistics

---

## Authoritative Sources

### 1. WHO Global Health Workforce Observatory (GHWO)
- **URL**: https://www.who.int/observatories/global-observatory-on-health-research-and-development/monitoring/health-workforce
- **Content**: Global workforce statistics, methodology guides, threshold densities
- **Update Frequency**: Annual

### 2. OECD Health Statistics 2025
- **URL**: https://data-explorer.oecd.org/
- **Content**: Healthcare human resources dataset with 40+ countries, time series 2000-2025
- **Key Indicators**: Physicians, nurses, dentists per 1000 population; graduates; international migration
- **Publication**: June 2025

### 3. WHO Health Workforce 2030 Strategy
- **Content**: Strategic framework for health workforce development
- **Key Metrics**: Threshold densities, education capacity, retention strategies
- **Policy Guidance**: Health labour market analysis, fiscal space for investment

### 4. OECD Joint Network of Senior Budget and Health Officials
- **URL**: https://www.oecd.org/en/networks/the-oecd-joint-network-of-senior-budget-and-health-officials.html
- **Content**: Fiscal planning for health workforce investment
- **Relevance**: Cost-effectiveness of workforce policies

### 5. Singapore Ministry of Health (MOH) Workforce Reports
- **Content**: Local workforce statistics, planning frameworks, Healthcare Manpower Development Programme (HMDP)
- **Relevance**: Singapore-specific benchmarks and policies

---

## Singapore-Specific Context

### Current Workforce Profile (2023)

- **Physicians**: ~25 per 10,000
- **Nurses**: ~65 per 10,000
- **Allied Health**: Growing emphasis (physiotherapists, occupational therapists)
- **Community Health Workers**: Expansion for aging population

### Policy Initiatives

- **HealthierSG Framework**: Shift to population health management
- **Community Health Assist Scheme (CHAS)**: Expanding primary care capacity
- **Foreign Medical Talent Scheme**: Managing controlled immigration

### Challenges

- **Aging Workforce**: 30%+ of physicians approaching retirement age
- **Geographic Imbalance**: Concentration in central/urban areas
- **Specialty Shortages**: Geriatrics, palliative care, psychiatry

---

## Example Use Cases

### UC-1: Calculate Workforce Gap

```python
import polars as pl

# Load workforce and population data
df_workforce = pl.read_csv('data/4_processed/workforce_data.csv')
df_population = pl.read_csv('data/4_processed/population_projections.csv')

# Calculate current density
df_current = df_workforce.join(df_population, on='year', how='inner')
df_current = df_current.with_columns([
    (pl.col('physician_count') / pl.col('total_population') * 10000)
    .alias('current_density')
])

# Define target density (WHO minimum)
target_density = 10.0

# Calculate gap
df_gap = df_current.with_columns([
    ((target_density * pl.col('total_population') / 10000) - pl.col('physician_count'))
    .alias('workforce_gap')
])

print(df_gap.select(['year', 'physician_count', 'current_density', 'workforce_gap']))
```

### UC-2: Forecast Future Supply

```python
# Simple stock-flow projection (5-year horizon)
def forecast_supply(initial_stock, annual_inflows, annual_outflows, years=5):
    supply_projection = []
    current_stock = initial_stock
    
    for year in range(years):
        new_stock = current_stock + annual_inflows - annual_outflows
        supply_projection.append({
            'year': 2024 + year,
            'supply': new_stock
        })
        current_stock = new_stock
    
    return pl.DataFrame(supply_projection)

# Example usage
projection = forecast_supply(
    initial_stock=15000,  # current physicians
    annual_inflows=800,   # graduates + immigration
    annual_outflows=500,  # retirements + emigration
    years=10
)
```

---

## References

1. WHO (2016). *Global strategy on human resources for health: Workforce 2030*. Geneva: World Health Organization.

2. OECD (2025). *Health at a Glance 2025: OECD Indicators*. Paris: OECD Publishing.

3. Scheffler, R. M., et al. (2018). "Forecasting imbalances in the global health labor market and devising policy responses." *Human Resources for Health*, 16(1), 5.

4. Ministry of Health Singapore (2023). *Healthcare Manpower Development Programme Report*.

5. Segal, L., & Bolton, T. (2009). "Issues facing the future health care workforce: the importance of demand modelling." *Australia and New Zealand Health Policy*, 6(1), 12.
