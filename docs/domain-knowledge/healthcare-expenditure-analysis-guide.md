# Domain Knowledge: Healthcare Expenditure Analysis

## Overview

Healthcare expenditure analytics quantifies how much a country spends on health, where that money goes, and what drives cost growth. This guide covers standard metrics, decomposition methodologies, international benchmarks, and feature engineering guidance for diagnosing Singapore's healthcare expenditure trends and identifying cost containment opportunities.

## Related Problem Statements

- [PS-004: Healthcare Expenditure Drivers & Cost Control](../objectives/problem_statements/ps-004-healthcare-expenditure-drivers.md)
- [PS-003: Healthcare Capacity Optimization](../objectives/problem_statements/ps-003-healthcare-capacity-optimization.md)

## Related Stakeholders

- **Healthcare Financing Division, MOH**: Budget forecasting and cost containment strategy
- **Policy & Strategy Group, MOH**: Healthcare financing policy design
- **Finance Ministry (Budget Office)**: National healthcare budget allocation
- **Healthcare Economists**: Research and international benchmarking

---

## Key Concepts and Terminology

### Total Health Expenditure (THE)
**Definition**: Sum of all spending on health activities by government, private insurers, and households  
**Formula**: `THE = Government Health Expenditure + Private Health Expenditure + Out-of-Pocket`  
**Relevance**: Top-level indicator of healthcare resource commitment  
**Singapore context**: THE has grown from ~3.5% GDP (2006) to ~4.5% GDP (2018)

### Government Health Expenditure (GHE)
**Definition**: Spending by government entities (MOH, restructured hospitals, polyclinics) on healthcare  
**Relevance**: Measures public commitment to healthcare; Singapore dataset provides this dimension directly  
**Note**: Includes subsidies, operating grants to public institutions, and MOH central programme expenditure

### Per Capita Health Expenditure
**Definition**: Total health expenditure divided by mid-year population  
**Formula**: `Per capita THE = THE / Population`  
**Relevance**: Normalises for population size; enables temporal and international comparisons  
**Benchmark**: Singapore ~SGD 2,500/year per capita (2018); OECD average ~USD 4,000

### Health Expenditure as % of GDP
**Definition**: THE expressed as a share of Gross Domestic Product  
**Relevance**: Controls for economic growth; widely used international comparator  
**Benchmark**: Singapore ~4.5% (2018); OECD average ~8.8%; WHO minimum recommendation ~5% for LMICs

### Compound Annual Growth Rate (CAGR)
**Definition**: Smooth annualised growth rate of expenditure over a multi-year period  
**Formula**: `CAGR = ((End Value / Start Value)^(1/n) - 1) × 100`  
**Relevance**: Summarises expenditure trend without year-to-year noise  
**Red flags**: CAGR > GDP growth rate signals unsustainable healthcare cost escalation

### Expenditure Decomposition
**Definition**: Statistical separation of total growth into component effects  
**Three standard components**:
1. **Volume effect (utilisation)**: Growth due to more cases/services
2. **Intensity effect (cost per case)**: Growth due to higher cost per service (technology, complexity)
3. **Demographic effect (population ageing)**: Growth due to changing age composition of the population  
**Formula**: `ΔTotal = Δvolume × price + volume × Δprice + Δpopulation × rate`

### Cost Containment
**Definition**: Policies and strategies to reduce or slow the growth of healthcare expenditure without compromising quality  
**Strategies**: Bulk procurement, fee schedules, clinical practice guidelines, shifting care to lower-cost settings  
**Relevance**: Central objective of PS-004; identify which expenditure drivers are amenable to intervention

---

## Standard Metrics and KPIs

| Metric | Definition | Formula | Typical Range | Use Case | Data Available |
|--------|-----------|---------|--------------|----------|----------------|
| THE as % GDP | Total health spending / GDP | `THE / GDP × 100` | 3–15% | Macro sustainability | ✅ Indirect |
| Government share | GHE / THE | `GHE / THE × 100` | 40–85% | Public vs private mix | ✅ Direct |
| Per capita THE (SGD) | THE / population | `THE / pop` | SGD 1,000–4,000 | Real resource use | Computed |
| CAGR (expenditure) | Annualised growth rate | `((THE_t / THE_0)^(1/n) - 1)` | 3–8% per annum | Sustainability signal | Computed |
| Volume growth component | Utilisation-driven growth | Decomposition formula | — | Target for demand management | Computed |
| Intensity growth component | Cost-per-case-driven growth | Decomposition formula | — | Technology/complexity driver | Computed |
| Real expenditure growth | Nominal CAGR minus CPI | `nominal_CAGR - CPI` | 0–4% real | Inflation-adjusted trend | Computed |

---

## Feature Engineering Guidance

### Temporal Features
```python
import polars as pl

df = df.with_columns([
    # Year-on-year growth
    ((pl.col('expenditure') - pl.col('expenditure').shift(1)) / pl.col('expenditure').shift(1) * 100)
    .alias('yoy_growth_pct'),

    # CAGR rolling 5-year window
    ((pl.col('expenditure') / pl.col('expenditure').shift(5)) ** (1/5) - 1)
    .alias('cagr_5yr'),

    # Real expenditure (deflated by CPI index if available)
    (pl.col('expenditure') / pl.col('cpi_index'))
    .alias('real_expenditure'),

    # Expenditure per capita
    (pl.col('expenditure') / pl.col('population'))
    .alias('expenditure_per_capita'),
])
```

### Decomposition Features
```python
# Volume-price decomposition: Δ(P × Q) = P₀ × ΔQ + Q₀ × ΔP + ΔP × ΔQ
df = df.with_columns([
    # Volume effect: change in admissions × base cost per case
    (pl.col('admission_change') * pl.col('cost_per_case_base'))
    .alias('volume_effect'),

    # Intensity effect: base admissions × change in cost per case
    (pl.col('admissions_base') * pl.col('cost_per_case_change'))
    .alias('intensity_effect'),

    # Interaction (usually small)
    (pl.col('admission_change') * pl.col('cost_per_case_change'))
    .alias('interaction_effect'),
])
```

### Cross-Domain Correlation Features
- **Expenditure–Utilisation correlation**: Lag admissions by 1 year vs expenditure growth
- **Expenditure–Workforce ratio**: Expenditure per healthcare worker (productivity proxy)
- **Expenditure–Disease burden ratio**: Expenditure per DALY (efficiency of health spending)

### Structural Break Detection
Use Chow test or Bai-Perron breakpoint test to identify policy-induced expenditure shifts:
- 2013: Major MediShield Life reform
- 2015: Pioneer Generation Package
- 2017: Community Health Assist Scheme expansion

---

## Analytical Methodologies

### Expenditure Decomposition Analysis

**Step-by-step approach for Singapore dataset**:
1. Extract `government-health-expenditure.csv` covering 2006–2018
2. Obtain Singapore GDP data from Singstat (external enrichment)
3. Compute per-capita series using Singstat population
4. Decompose growth:
   - **Demographic effect**: Project what spending would have been if only age structure changed
   - **Volume effect**: Residual after removing demographic effect
   - **Price/intensity effect**: Derived from cost per admission (expenditure / admissions)

### Time Series Trend Analysis
Apply the same APC (Annual Percent Change) methodology used in PS-002 disease burden analysis:
- Fit log-linear model: `ln(expenditure) = α + β × year + ε`
- β represents the continuous annual growth rate
- Joinpoint regression identifies statistically significant inflection points

### International Benchmarking
Compare Singapore's expenditure trajectory against:
- **OECD Health Statistics** (annual publication)
- **WHO Global Health Expenditure Database** (https://apps.who.int/nha/database)
- **Typical comparators**: Australia, New Zealand, UK (NHS), South Korea, Japan

Note: External benchmark data must be manually obtained; the Kaggle dataset is Singapore-only.

---

## Common Pitfalls and Best Practices

### Pitfalls to Avoid
- **Nominal vs real growth confusion**: Always deflate expenditure before comparing across years; use Singapore CPI or healthcare-specific deflator
- **Ignoring population growth**: Per capita expenditure more informative than absolute totals
- **Single-driver fallacy**: Healthcare cost growth is always multi-factorial; avoid attributing all growth to one cause
- **Financial year vs calendar year mismatch**: Singapore expenditure data uses financial year (April–March); align with calendar year data from other sources carefully

### Best Practices
- **Decompose before prescribing**: Identify whether growth is driven by volume, price, or demographics before recommending interventions
- **Link to clinical evidence**: Intensity growth may reflect appropriate care improvements (e.g., wider cancer screening); not all cost growth is inefficient
- **International context**: Singapore's THE/GDP ratio is below OECD average — restraint in expenditure is a policy achievement but may create future access risks
- **Sensitivity analysis**: Test conclusions under different inflation assumptions (base case, optimistic, pessimistic)

---

## References and Sources

- **WHO Global Health Expenditure Database**: https://apps.who.int/nha/database — International THE comparisons
- **OECD Health Statistics 2024**: https://www.oecd.org/health/health-statistics.htm — OECD member benchmarks
- **MOH Singapore Annual Report 2023**: https://www.moh.gov.sg/resources-statistics/singapore-health-facts — Singapore-specific context
- **Singapore Singstat**: https://www.singstat.gov.sg — GDP and CPI deflators
- **Papanicolas I, Woskie LR, Jha AK (2018)**: Health Care Spending in the United States and Other High-Income Countries. *JAMA* — Decomposition methodology reference
- **Chernew ME, Rosen AB, Fendrick AM (2007)**: Value-based insurance design. *Health Affairs* — Cost-effectiveness framing

---

## Cross-References

### Related Domain Knowledge Files
- [Healthcare Capacity & Utilization Metrics](healthcare-capacity-utilization-metrics-kpis.md) — Volume drivers of expenditure
- [Healthcare Workforce Metrics & KPIs](healthcare-workforce-metrics-kpis.md) — Labour cost as expenditure component
- [Time Series Forecasting Methods](time-series-forecasting-methods.md) — Projection methodology

### Related Data Dictionary Entries
- [Disease Data Dictionary](../data-dictionary/disease_data.md) — Utilisation tables that drive expenditure
- [External Reference Dictionary](../data-dictionary/external_reference.md) — GDP, CPI, population denominators

---

## Metadata

**Created**: 2026-04-08  
**Last Updated**: 2026-04-08  
**Updated By**: GitHub Copilot (automated generation)  
**Update Reason**: Initial creation to support PS-004 Healthcare Expenditure Drivers user stories  
**Version**: 1.0
