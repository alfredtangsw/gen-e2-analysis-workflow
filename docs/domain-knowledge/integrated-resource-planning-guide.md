# Domain Knowledge: Healthcare Resource Planning — Workforce, Beds & Cost Benchmarks

## Overview

Integrated resource planning in healthcare requires co-planning three interdependent dimensions: **workforce** (people who deliver care), **facility capacity** (physical infrastructure that enables care), and **cost** (budget required to operate both). Planning any one dimension independently produces incoherent plans — nurses hired for wards not yet built, or wards commissioned without staffing budget.

This guide defines the benchmarks, formulas, and planning conventions used in PS-003 to translate demand projections into year-by-year hiring targets, bed commissioning milestones, and a workforce cost estimate.

## Related Problem Statements

- [PS-001: Healthcare System Baseline](../objectives/problem_statements/ps-001-healthcare-system-baseline.md)
- [PS-002: Healthcare Demand Forecasting](../objectives/problem_statements/ps-002-healthcare-demand-forecasting.md)
- [PS-003: Integrated Resource Planning & Budget Dashboard](../objectives/problem_statements/ps-003-integrated-resource-planning.md)

## Related Stakeholders

- **Workforce Planning Division, MOH**: Consumes annual hiring targets by profession
- **Healthcare Planning Division, MOH**: Consumes bed gap and commissioning milestones
- **Healthcare Financing Division, MOH**: Consumes workforce cost estimate for budget framing
- **Finance Ministry Budget Office**: Multi-year cost trajectory with scenario range

---

## Key Concepts and Terminology

### Bed-to-Population Ratio
**Definition**: Number of hospital beds per 1,000 (or 10,000) resident population  
**Formula**: `(Total beds / Resident population) × 1,000`  
**WHO Benchmark**: ~2.5 beds per 1,000 for high-income countries; Singapore ~2.4 (2020)  
**Use**: Tracks capacity scaling relative to population growth

### Nurse-to-Bed Ratio
**Definition**: Number of registered nurses per inpatient bed (operational measure)  
**WHO Reference**: 1 nurse per 4 beds for acute wards; 1 per 6–8 for step-down  
**Singapore Context**: Apply acute-only ratio (1:4) as national average given lack of ward-type split in dataset  
**Caution**: This is a staffing model input, not an observed value from the dataset

### Doctor-to-Population Ratio
**Definition**: Practising physicians per 10,000 resident population  
**WHO Minimum**: 10 per 10,000; Singapore ~25 per 10,000 (2019)  
**OECD Average**: ~34 per 10,000 (2023)  
**Use**: Demand projection converts population growth into required doctor headcount

### Average Length of Stay (ALOS)
**Definition**: Mean number of inpatient days per hospital admission  
**Formula**: `Total inpatient days / Total discharges`  
**Singapore Acute ALOS**: ~5.0–5.5 days (MOH Health Statistics); OECD average ~5.1 days  
**Use in bed planning**: `Required beds = Annual admissions × ALOS / (365 × target occupancy rate)`

### Target Bed Occupancy Rate
**Definition**: Planned proportion of beds occupied at any time (leaves buffer for surge)  
**Standard Planning Assumption**: 85% for acute hospitals (15% buffer for emergency surges)  
**Use**: `Required beds = (Admissions × ALOS) / (365 × 0.85)`  
**Why not 100%**: Full occupancy leaves no capacity for emergency admissions or infection control isolation

### Workforce Attrition Rate
**Definition**: Proportion of workforce that leaves employment annually (resignation, retirement, death)  
**Typical Range**: 5–10% per year for healthcare workers depending on profession and sector  
**Impact on hiring**: Gross annual hires = Net gap + (Current headcount × attrition rate)  
**Singapore source**: MOH Annual Report (if available); default 5% if not

### Overhead Multiplier
**Definition**: Factor applied to base salary to estimate total employment cost  
**Standard**: 1.35 (base salary × 1.35 = total cost including CPF, leave, training, uniforms)  
**Singapore public sector CPF**: Employer contribution 17% (for workers <55)  
**Other components**: Annual leave cost, training levy, uniforms, medical benefits

---

## Standard Benchmarks Reference Table

| Metric | Benchmark | Source | Notes |
|---|---|---|---|
| Nurse-to-bed ratio (acute) | 1:4 (0.25 nurses per bed) | WHO | National average proxy |
| Doctor-to-population | 25–34 per 10,000 | WHO / OECD | Singapore ~25 (2019) |
| Beds per 1,000 population | 2.5–3.0 | WHO | Singapore ~2.4 (2020) |
| Target bed occupancy | 85% | International standard | 15% surge buffer |
| ALOS (acute) | 5.0–5.5 days | MOH / OECD | Use Singapore Health Stats value first |
| Workforce attrition | 5–8% per year | MOH Annual Report | Default 5% if unavailable |
| CPF overhead (employer) | 17% | CPF Board Singapore | For workers <55 |
| Total overhead multiplier | 1.35 | Standard estimate | Includes CPF, leave, training, uniforms |

---

## Feature Engineering Guidance

### Workforce Supply Projection Features

- **`growth_rate_historical`**: Average YoY growth rate per profession over PS-001 baseline period (2006–2019)
- **`supply_trend_extrap`**: Headcount × (1 + historical growth rate)^n projected forward
- **`supply_flat`**: Headcount held constant (zero net new hires scenario — stress test)

### Workforce Demand Features

- **`required_nurses`**: `projected_beds × (1 / nurse_to_bed_ratio)`
- **`required_doctors`**: `projected_population × (doctor_per_10k / 10000)`
- **`required_allied_health`**: `projected_admissions × allied_health_per_admission_benchmark`

### Gap and Hiring Features

- **`workforce_gap`**: `required_headcount - supply_trend_extrap` (by profession, year, scenario)
- **`gross_annual_hires`**: `max(workforce_gap_delta, 0) + (current_headcount × attrition_rate)` — minimum hires just to maintain headcount
- **`policy_action_flag`**: Boolean — True if `gross_annual_hires > historical_max_annual_hires × 1.5` (requires policy intervention)

### Bed Planning Features

- **`required_beds`**: `projected_admissions × ALOS / (365 × 0.85)`
- **`bed_supply_extrap`**: Beds × (1 + historical bed growth rate)^n
- **`bed_gap`**: `required_beds - bed_supply_extrap`
- **`commissioning_window`**: 5-year intervals where cumulative bed gap exceeds a threshold (e.g., 200 beds)

### Cost Features

- **`annual_workforce_cost`**: `headcount_by_profession × median_salary_by_profession × overhead_multiplier`
- **`cumulative_10yr_cost`**: Sum of annual workforce cost over projection horizon
- **`cost_per_admission`**: `total_govt_expenditure / estimated_total_admissions` (contextual trend, not a forecast)

---

## Data Quality Considerations

### Salary Benchmarks
- MOM Occupational Wages Survey is published annually — use latest available year
- Values are median gross monthly wages; annualise by × 12
- Apply overhead multiplier of 1.35 to get total employment cost

### ALOS Assumption
- Singapore Health Statistics publishes ALOS annually in MOH's Health Facts
- If not downloadable, use OECD acute ALOS (5.1 days) with explicit disclosure in outputs
- Document the source and date of the ALOS value used in all deliverables

### Attrition Rate
- MOH Annual Report section on manpower may contain profession-specific rates
- If unavailable, apply a uniform 5% and disclose this assumption clearly
- Sensitivity test: run at 3%, 5%, and 8% to show impact on hiring targets

### Demographic Scenario Alignment
- PS-002 produces 3 scenarios (low/medium/high ageing)
- PS-003 must run all planning models for all 3 scenarios
- All gap and cost outputs should carry a scenario label — never mix scenarios within a single output row

---

## Analytical Methodologies

### Workforce Projection (Supply Side)
- **Method**: Linear extrapolation of historical CAGR from PS-001 baseline
- **CAGR formula**: `((headcount_2019 / headcount_2006) ^ (1/13)) - 1`
- **Apply to**: Each profession separately (doctors, nurses, pharmacists, dentists, allied health)
- **Implementation**: `supply_year_n = supply_2019 × (1 + CAGR)^n`

### Workforce Projection (Demand Side)
- **Method**: Benchmark ratio × PS-002 projection
- **Nurses**: `required = projected_beds_year_n × nurse_per_bed`
- **Doctors**: `required = projected_population_year_n × doctor_per_10k / 10000`
- **Complexity**: Run per scenario from PS-002; output is a 3-scenario × profession × year matrix

### Bed Requirement Projection
- **Formula**: `beds = (admissions × ALOS) / (365 × 0.85)`
- Admissions from PS-002 admission volume projection
- Run for all 3 PS-002 scenarios
- Compare against extrapolated bed supply from PS-001 facility growth rate

### Staff-Facility Alignment Validation
- **Check**: `projected_nurses_year_n / projected_beds_year_n` vs. nurse-to-bed benchmark (0.25)
- **Flag**: If ratio < 0.20 (under-staffed relative to beds) or > 0.35 (over-staffed relative to beds)
- **Output**: Traffic-light heatmap by profession-year-scenario

---

## Common Pitfalls

- **Mixing scenarios**: Never average across demographic scenarios — always report low/medium/high separately
- **Ignoring attrition**: Gross hires ≠ net gap. A 500-person gap + 5% attrition on 20,000 workforce = 1,500 gross hires needed, not 500
- **Planning beds without staff**: Always validate that bed commissioning milestones are preceded by hiring milestones (given training lead times)
- **Presenting workforce cost as total budget**: The model covers workforce cost only — explicitly label output columns as `workforce_cost_only`

---

## References and Sources

- **WHO Global Health Observatory**: Nurse-to-bed ratios, doctor-to-population benchmarks — https://www.who.int/data/gho
- **OECD Health Statistics**: ALOS, bed ratios, physician density — https://stats.oecd.org/
- **MOM Occupational Wages Survey**: Singapore salary benchmarks by occupation — https://www.mom.gov.sg/
- **MOH Health Facts Singapore**: Annual ALOS, bed statistics — https://www.moh.gov.sg/resources-statistics/singapore-health-facts
- **CPF Board**: Employer CPF contribution rates — https://www.cpf.gov.sg/

## Metadata

**Created**: 2026-04-13  
**Last Updated**: 2026-04-13  
**Related PS**: PS-001, PS-002, PS-003
