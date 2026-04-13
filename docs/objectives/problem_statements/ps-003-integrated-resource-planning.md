# PS-003: Integrated Resource Planning & Budget Dashboard

```yaml
problem_statement_id: PS-003
title: "Integrated Resource Planning & Budget Dashboard"
analysis_category: Prescriptive Analytics
priority: P0 (Critical)
platform: Local (development) → HEALIX/Databricks
primary_language: Python (Polars + Plotly)
estimated_sprints: 4-5
status: Initialized
dependencies: PS-001, PS-002
```

---

## STEP 1.5 — Data Reality Check (Applied to this PS)

**Source dataset**: `subhamjain/health-dataset-complete-singapore` (Kaggle, ~3.5 MB, 35 CSV tables)  
**PS-001 outputs**: Workforce baseline, facility baseline, staff-to-bed ratios, utilisation proxy  
**PS-002 outputs**: Admission volume projections (2021–2035, 3 scenarios), disease mortality forecasts

### Data Available for Planning

| Planning Component | Data Source | What It Enables |
|---|---|---|
| Required workforce (future) | PS-002 admission projections + WHO nurse/doctor-to-patient benchmarks | Compute headcount target by applying benchmark ratios to projected admission volumes |
| Required beds (future) | PS-002 admission projections + average length-of-stay assumption | Compute bed requirement: admissions × assumed LOS ÷ days per year × occupancy target |
| Current workforce supply trajectory | PS-001 workforce baseline growth rates → extrapolated forward | Project current supply if growth rate continues unchanged |
| Current bed supply trajectory | PS-001 facility baseline growth rates → extrapolated forward | Project current capacity if construction pace continues |
| Workforce cost estimate | Headcount gap × published MOH/MOM salary benchmarks (external, public) | Workforce cost proxy — not from Kaggle dataset |
| Government expenditure trend | `government-health-expenditure.csv` (2006–2018, total only) | Cost-per-admission trend context — not a full budget model |

### ✅ Feasible Analyses

- Workforce supply projection: extrapolate PS-001 growth rates to 2035 (linear and trend-based)
- Workforce demand projection: apply WHO nurse-to-bed and doctor-to-patient standards to PS-002 admission volumes
- Workforce gap analysis: demand minus supply trajectory, by profession, by year (2021–2035)
- Bed demand projection: PS-002 admissions × assumed LOS ÷ (365 × target occupancy rate)
- Bed supply projection: extrapolate PS-001 facility growth to 2035
- Bed gap analysis: required beds minus projected beds, by year and scenario
- Staff-to-bed alignment check: projected staff ÷ projected beds per year — flag divergence from benchmarks
- Workforce cost estimate: headcount gap × published salary benchmarks (MOH Annual Report / MOM occupational wage data, both public)
- Government expenditure-per-admission contextual trend (2006–2018 only; descriptive, not a cost model)
- Interactive multi-tab dashboard: self-contained HTML, no server

### ❌ Infeasible Analyses (dropped — no data)

- Infrastructure capital cost projection — **no construction cost data in dataset or identified public source**
- Supplies and consumables budget — **zero data on clinical consumables**
- Budget breakdown by category (workforce vs infrastructure vs supplies) — **only total govt expenditure available**
- Facility-level staffing plans — **national aggregates only**
- Ward-type-specific bed plans (acute vs ICU vs step-down) — **beds table does not separate by ward type within acute hospitals**
- Cost savings from care-shift policies (acute → step-down) — **no step-down utilisation data to model the shift**

**Note on budget model scope**: This PS can produce a **workforce cost estimate** (the largest single controllable cost driver) using headcount gap × salary benchmarks. It cannot produce a full system budget. Outputs must be clearly labelled as "workforce cost estimate" — not "total healthcare budget."

---

## Executive Summary

PS-001 established where the system stands today. PS-002 projected where demand is heading. PS-003 answers the operational question: **what concrete actions must MOH take — and what will they cost — to keep workforce and facility supply ahead of projected demand?**

Using the PS-001 workforce and facility baselines, PS-002 admission projections, and publicly available staffing benchmarks and salary data, this PS builds an integrated planning model that computes the workforce and bed gap year by year through 2035, validates that staffing and facility expansion plans are internally consistent (staff hired for beds that exist), and delivers the outputs as a self-contained interactive HTML dashboard for MOH directors.

The budget component is scoped to workforce cost only — the largest controllable cost driver — because no capital or supplies data exists in the verified dataset.

---

## Problem Statement Hypothesis

> We believe that combining PS-001 baseline growth trajectories with PS-002 demand projections into a single workforce-and-bed gap model, validated for internal consistency (staff-to-bed balance) and translated into a workforce cost estimate, will give MOH directors a defensible annual hiring target and bed expansion milestone with an associated budget for the workforce component. We'll know we're successful when MOH directors can read the dashboard and articulate: how many nurses to hire per year, how many beds to commission per year, and what the workforce costs will be — through 2035.

---

## Objectives

**Objective 1 — Workforce Supply Projection (2021–2035)**
- Extrapolate PS-001 historical workforce growth rates for each profession (doctors, nurses, pharmacists, allied health) forward to 2035
- Model two supply assumptions: (a) current trend continues; (b) zero net new hires (status quo headcount)
- This is the supply baseline against which the demand gap is measured

**Objective 2 — Workforce Demand Projection (2021–2035)**
- Apply WHO reference benchmarks (nurses per bed, doctors per 10,000 population, allied health per admission) to PS-002 projected admission volumes and derived bed requirements
- Compute required headcount by profession per year, for each PS-002 demographic scenario (low/medium/high)
- This turns the demand projection into a staffing number

**Objective 3 — Workforce Gap Analysis and Hiring Plan**
- Compute gap: required headcount (Objective 2) minus projected supply (Objective 1), by profession, by year
- Convert gap to annual hiring targets (accounting for workforce attrition: apply publicly available attrition rate estimates by profession)
- Identify which profession-years face the most critical under-supply
- Flag profession-years where hiring would need to materially exceed historical growth — these require policy intervention (training pipeline expansion, immigration, retention programmes)

**Objective 4 — Bed Demand Projection and Capacity Gap**
- Compute required beds: PS-002 projected admission volume × assumed average length of stay (days) ÷ (365 × target occupancy rate)
  - LOS assumption: sourced from Singapore Health Statistics or WHO benchmarks (public)
  - Target occupancy rate: 85% (standard acute hospital benchmark)
- Extrapolate PS-001 bed growth rate to project current trajectory
- Calculate bed gap by year across all scenarios

**Objective 5 — Staff-Facility Alignment Validation**
- For each scenario year: check that projected nurse headcount ÷ projected beds remains within the WHO nurse-to-bed benchmark range
- Flag any year where workforce plan and bed plan diverge — i.e., where planned nurse hiring exceeds what projected beds can absorb, or where beds grow faster than nurses
- This is the core integration check: staff, beds, and admissions must be internally consistent

**Objective 6 — Workforce Cost Estimation**
- Compute annual workforce cost: (current headcount + cumulative new hires) × salary by profession
- Use MOM Occupational Wages Survey or MOH Annual Report salary benchmarks (public)
- Apply overhead multiplier of 1.35 (benefits, training, uniforms — standard public sector estimate)
- Present workforce cost trajectory alongside government expenditure trend from PS-001 for context
- Clearly label outputs as workforce cost only — not total healthcare system budget

---

## Key Questions to Answer

1. How many nurses, doctors, and allied health professionals does MOH need to hire per year through 2035 to keep pace with projected demand?
2. How many additional beds need to be commissioned, and in which five-year windows?
3. Are the annual hiring targets consistent with the bed expansion timeline? (No hiring nurses for wards still years away from opening)
4. Which professions face the most critical supply gaps and require policy-level intervention (training pipeline expansion, immigration schemes)?
5. What is the estimated total workforce cost per year, and how does it compare to the historical government expenditure trajectory?

---

## Stakeholders and Value Proposition

**Primary Stakeholders**:
- Workforce Planning Division, MOH — primary consumer: annual hiring targets by profession
- Healthcare Planning Division, MOH — bed gap and commissioning timeline
- Healthcare Financing Division, MOH — workforce cost trajectory for budget framing
- Finance Ministry Budget Office — multi-year workforce cost estimate with scenario range

**Business Value**:
- **Decision enabled**: Specific, year-by-year hiring targets and bed commissioning milestones — not vague ranges
- **Risk reduction**: Staff-facility alignment check prevents the failure mode of hiring staff for facilities that don't yet exist (or building facilities without staff)
- **Efficiency gain**: Single dashboard replaces multi-division manual reconciliation
- **Transparency**: Confidence intervals from PS-002 propagate into the planning model — directors see best/base/worst case, not a false point estimate

---

## Data Requirements

**From PS-001 outputs** (no re-extraction needed):

| Input | File | Use |
|---|---|---|
| Workforce baseline | `results/tables/workforce_baseline.csv` | Historical growth rates for supply projection |
| Facility baseline | `results/tables/facility_baseline.csv` | Historical bed growth for capacity projection |
| System balance scorecard | `results/metrics/system_balance_scorecard.csv` | Current staff-to-bed starting ratios |

**From PS-002 outputs** (no re-extraction needed):

| Input | File | Use |
|---|---|---|
| Admission volume projections | `results/exports/demand_projections_for_planning.csv` | Demand-side driver for all planning calculations |

**External references required (all publicly available)**:

| Source | Data | Use |
|---|---|---|
| WHO Global Health Observatory | Nurse-to-bed ratio benchmark; doctor-to-population benchmark | Convert admission volumes to headcount requirements |
| MOM Occupational Wages Survey (public) | Median annual salary by healthcare occupation | Workforce cost estimation |
| Singapore Health Statistics (MOH, public) | Average length of stay in acute hospitals | Bed requirement calculation |
| MOH Annual Report (public) | Healthcare workforce attrition rates | Hiring target calculation (gross hires = net gap + attrition) |

**No additional Kaggle extraction required for this PS** — all inputs come from PS-001 and PS-002 processed outputs plus external references.

**Known data limitations**:
- LOS assumption is a national average — no ward-type or diagnosis-specific breakdown available
- Salary benchmarks are proxies; actual MOH internal scales may differ but are not publicly available
- Infrastructure capital costs are completely absent — the budget model covers workforce cost only
- Attrition rates from public sources may lag actual current rates; this uncertainty must be disclosed

---

## Analytical Approach

**Planning model**:
- All calculations in Polars — tabular, row-by-row computations on year × profession × scenario combinations
- Workforce and bed projections are additive forward projections from PS-001 baselines plus PS-002 demand scaling

**Dashboard**:
- Built with Plotly — exported as a self-contained HTML file (all JS/CSS bundled inline)
- Six tabs as described below
- No server, no login — opens in any browser and can be emailed as a single file

**Platform**: Local Python (Polars + Plotly). Compute requirements are minimal.

---

## Expected Outcomes and Deliverables

**Stakeholder Outcomes**:
- Annual hiring targets by profession through 2035 across three scenarios
- Bed gap milestones by five-year planning window
- Staff-facility alignment validation — confirmed consistent or flagged for policy attention
- Workforce cost trajectory for Finance Ministry budget submissions

**Concrete Deliverables**:
- 📋 `results/metrics/workforce_gap_analysis.csv` — required vs projected headcount by profession, year, scenario; annual hiring target
- 📋 `results/metrics/bed_gap_analysis.csv` — required vs projected beds by year, scenario
- 📋 `results/tables/staff_facility_alignment.csv` — staff-to-bed ratio by year, scenario; benchmark comparison; alignment flags
- 📋 `results/exports/workforce_cost_estimate.xlsx` — workforce cost by profession, year, scenario (clearly labelled as workforce cost only)
- 📊 `reports/dashboards/moh_resource_planning_dashboard.html` — self-contained interactive dashboard (6 tabs)

### Dashboard Design (6 Tabs)

| Tab | Content | Data Source |
|---|---|---|
| **1. Executive Summary** | KPI cards: nurse hiring gap (year 1, year 5, year 10), bed gap (year 5, year 10), workforce cost total (10-year), largest profession gap | All PS-003 outputs |
| **2. Workforce Plan** | Line chart: required vs projected headcount by profession; bar chart: annual hiring targets; highlight profession-years requiring policy action | `workforce_gap_analysis.csv` |
| **3. Facility Capacity Plan** | Line chart: required vs projected beds by year and scenario; milestone table for 5-year commissioning windows | `bed_gap_analysis.csv` |
| **4. Staff-Facility Alignment** | Heatmap: nurse-to-bed ratio by year and scenario vs benchmark; traffic-light flags for misaligned years | `staff_facility_alignment.csv` |
| **5. Workforce Cost Estimate** | Area chart: workforce cost by profession per year; line: cumulative cost; expenditure-per-admission trend from PS-001 for context | `workforce_cost_estimate.xlsx` |
| **6. Scenario Comparison** | Toggle between low/medium/high demographic scenarios; show impact on nurse gap, bed gap, and cost across all scenarios in one view | All outputs |

---

## Dependencies and Assumptions

**Depends on**: PS-001 (outputs required as inputs), PS-002 (demand projections required as inputs)  
**Blocks**: None — this is the final deliverable  
**Related to**: PS-001, PS-002

**Key Assumptions**:
- WHO nurse-to-bed benchmark: 1 nurse per 4 acute beds (standard acute ward); 1 nurse per 8 beds (step-down/community) — applied as a national average given lack of ward-type split
- Average length of stay: sourced from Singapore Health Statistics on first extraction; if unavailable, WHO OECD average of 5.1 days for acute hospitals will be used with explicit disclosure
- Target occupancy rate: 85% (standard planning assumption for acute hospitals)
- Attrition rate: applied uniformly across professions unless profession-specific data is available from MOH Annual Report
- Overhead multiplier: 1.35 (35% above base salary for benefits, training, uniforms) — standard Singapore public sector estimate

---

## Risks and Open Questions

- **Risk**: If LOS and attrition data cannot be sourced from public Singapore government reports, WHO/OECD proxies will be used — results must be clearly flagged as estimate-dependent
- **Risk**: WHO nurse-to-bed benchmarks are international; Singapore's actual operational ratios may differ. The dashboard should show the benchmark threshold alongside Singapore's current PS-001 ratio so the gap is interpretable
- **Risk**: Dashboard complexity — six tabs with interactive Plotly charts may result in a large HTML file; test file size before finalising
- **Open question**: Should the dashboard include a "data explorer" tab with the raw projection table (filterable)? Useful for Finance Ministry but adds development effort — decision to be made in sprint planning
- **Open question**: Should the scenario comparison tab allow the user to select custom assumptions (e.g., change the occupancy rate or LOS assumption)? If yes, this requires Plotly Dash (server) or pre-computed scenario grid — to be decided in planning

---

## Problem Statement Readiness Checklist

- [x] All data inputs verified: PS-001 and PS-002 outputs (no new extraction) + four external public references
- [x] All infeasible analyses explicitly dropped (infrastructure cost, supplies, ward-type split)
- [x] Budget scope clearly bounded: workforce cost only — not total system budget
- [x] Platform and technical feasibility confirmed (local Python/Polars/Plotly, self-contained HTML)
- [x] Problem statement can be decomposed into 5–10 user stories
- [x] Six-tab dashboard design specified with data source per tab
- [x] Dependencies on PS-001 and PS-002 documented; no downstream blockers

---

## Priority Scoring

| Dimension | Score (1–5) | Rationale |
|---|---|---|
| Business Value | 5 | This is the direct decision-support tool MOH directors will use |
| Feasibility | 4 | Inputs are verified; 4 external references needed but all public |
| Urgency | 5 | Final deliverable — determines whether the project achieves its business objective |
| **Total** | **14/15** | |
