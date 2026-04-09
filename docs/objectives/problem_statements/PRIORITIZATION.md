# Problem Statement Prioritization Analysis

**Date**: 2026-04-08  
**Author**: Data Analysis Team  
**Purpose**: Objective prioritization of identified problem statements for Gen-E2 Singapore Health Trends Analysis Project

---

## Prioritization Framework

Each problem statement is scored on three dimensions (1-5 scale):

- **Business Value (BV)**: Alignment with MOH strategic goals, stakeholder impact, decision-enabling power
- **Feasibility (F)**: Data availability, technical complexity, resource requirements, timeline
- **Urgency (U)**: Stakeholder pain points, time sensitivity, policy deadlines, dependencies

**Total Priority Score** = (BV × 0.4) + (F × 0.3) + (U × 0.3)  
*Business Value weighted higher as primary driver*

**Priority Categorization**:
- **P0 (Critical)**: Score ≥ 4.0 - Immediate start, highest resource allocation
- **P1 (High)**: Score 3.0-3.9 - Near-term start, significant resources
- **P2 (Medium)**: Score 2.0-2.9 - Planned start after P0/P1, moderate resources
- **P3 (Low)**: Score < 2.0 - Future consideration, minimal resources

---

## Problem Statement Scoring

### PS-001: Healthcare Workforce Sustainability Analysis (Predictive)

**Business Value: 5/5**
- **Direct alignment** with MOH strategic goal: "Ensure sustainable healthcare system" (business-objectives.md)
- **Critical stakeholder need**: Workforce planning for healthcare sustainability (explicit in project context)
- **High-impact decisions enabled**: 10-year workforce projections inform recruitment, training pipelines, immigration policies
- **Strategic importance**: Workforce shortages have system-wide cascading effects
- **Justification**: Workforce is the #1 healthcare system resource; shortages cannot be quickly remedied

**Feasibility: 4/5**
- **Data availability**: ✅ 7 workforce tables confirmed (2006-2019), 13 years of historical data
- **Data quality**: ✅ 100% complete, official MOH source
- **Technical complexity**: Moderate - Time series forecasting is well-established; Python libraries (statsmodels, Prophet) mature
- **Resource requirements**: Medium - Single analyst with forecasting expertise; 5-7 sprints estimated
- **Known constraints**: Data ends 2019; COVID-19 may have altered workforce trends (mitigation: scenario modeling)
- **Justification**: Standard forecasting problem with good data; -1 for COVID-19 uncertainty

**Urgency: 4/5**
- **Stakeholder urgency**: High - Healthcare workforce shortages are current pain point globally and in Singapore
- **Time sensitivity**: Medium-High - Workforce planning requires 5-10 year lead time for training pipelines
- **Policy deadlines**: No immediate deadline but ongoing need for updated projections
- **Dependencies**: None - can start immediately; may inform capacity planning (PS-003)
- **Justification**: Current pain point with long lead time for interventions = high urgency

**Total Score**: (5 × 0.4) + (4 × 0.3) + (4 × 0.3) = **2.0 + 1.2 + 1.2 = 4.4**  
**Priority Assignment**: **P0 (Critical)**

---

### PS-002: Disease Burden Temporal Trends Analysis (Descriptive)

**Business Value: 4/5**
- **Direct alignment** with MOH goal: "Improve population health outcomes" and disease outbreak detection (business-objectives.md)
- **Stakeholder enabling**: Public health program prioritization; resource allocation to highest-burden diseases
- **Decisions enabled**: Disease control program design, screening guidelines, health promotion focus areas
- **Strategic importance**: Foundation for many public health interventions
- **Justification**: Critical for public health strategy but less urgent than workforce; -1 for being descriptive vs predictive

**Feasibility: 5/5**
- **Data availability**: ✅ 3 mortality tables confirmed (1990-2019), 30 years of data - excellent temporal coverage
- **Data quality**: ✅ 100% complete, age-standardized rates (gold standard for trend analysis)
- **Technical complexity**: Low - Descriptive statistics, trend detection, visualization - straightforward
- **Resource requirements**: Low-Medium - Single analyst; 3-5 sprints estimated
- **Known constraints**: None significant - data is ideal for this analysis type
- **Justification**: Perfect data availability and low technical complexity = maximum feasibility

**Urgency: 3/5**
- **Stakeholder urgency**: Medium - Ongoing need for disease burden assessment but not crisis-level
- **Time sensitivity**: Low-Medium - Public health programs operate on multi-year cycles
- **Policy deadlines**: No immediate deadline; useful for strategic planning cycles
- **Dependencies**: None - standalone analysis; may inform resource allocation discussions
- **Justification**: Important for planning but flexibility in timing

**Total Score**: (4 × 0.4) + (5 × 0.3) + (3 × 0.3) = **1.6 + 1.5 + 0.9 = 4.0**  
**Priority Assignment**: **P0 (Critical)**

---

### PS-003: Healthcare Capacity & Utilization Optimization (Prescriptive)

**Business Value: 5/5**
- **Direct alignment** with MOH goals: Sustainability AND efficiency (business-objectives.md)
- **High-value decisions enabled**: Multi-billion dollar infrastructure investment decisions (hospital construction, facility expansion)
- **Stakeholder impact**: Finance Ministry, MOH Executive - highest decision-making levels
- **Strategic importance**: Capital investments are irreversible 10-20 year commitments
- **Cost implications**: Prevents wasteful over-capacity or crisis from under-capacity
- **Justification**: Highest financial impact of all problem statements

**Feasibility: 3/5**
- **Data availability**: ✅ Capacity and utilization tables confirmed BUT proxy occupancy rates required (actual occupancy not available)
- **Data quality**: ✅ 100% complete but may lack granularity
- **Technical complexity**: High - Optimization modeling, scenario analysis, multi-objective decision-making
- **Resource requirements**: High - Optimization expertise; potentially 5-7 sprints
- **Known constraints**: Cannot assess regional distribution (national-level only); proxy metrics introduce uncertainty
- **Justification**: Complex analysis with data limitations; -2 for proxy metrics and optimization complexity

**Urgency: 3/5**
- **Stakeholder urgency**: Medium - Infrastructure planning is ongoing but operates on long cycles (5-10 year planning horizons)
- **Time sensitivity**: Medium - Capacity expansion has 3-5 year lead time from planning to operation
- **Policy deadlines**: None immediate but may align with national budget cycles
- **Dependencies**: May benefit from workforce analysis (PS-001) but not blocking
- **Justification**: Important for strategic planning but not time-critical

**Total Score**: (5 × 0.4) + (3 × 0.3) + (3 × 0.3) = **2.0 + 0.9 + 0.9 = 3.8**  
**Priority Assignment**: **P1 (High)**

---

### PS-004: Healthcare Expenditure Drivers & Cost Control (Diagnostic)

**Business Value: 5/5**
- **Direct alignment** with MOH goal: "Ensure sustainable healthcare system" - cost control is pillar of sustainability
- **Critical stakeholder**: Finance Ministry (Budget Office) - national budget impact
- **High-impact decisions**: Cost containment policies with potential hundreds of millions in savings
- **Strategic importance**: Healthcare expenditure is major government budget line; unsustainable growth threatens fiscal position
- **Justification**: Financial sustainability is existential for healthcare system

**Feasibility: 4/5**
- **Data availability**: ✅ Expenditure tables confirmed (2005-2020), 15 years of data
- **Data quality**: ✅ 100% complete, official financial statistics
- **Technical complexity**: Moderate - Decomposition analysis methodologically established; econometric techniques if needed
- **Resource requirements**: Medium - Economist or financial analyst; 4-6 sprints estimated
- **Known constraints**: May lack service-level cost detail (aggregate expenditure only); international benchmarking data needs external sources
- **Justification**: Good data and established methods; -1 for potential granularity limitations

**Urgency: 4/5**
- **Stakeholder urgency**: High - Cost control is persistent concern for MOH and Finance Ministry
- **Time sensitivity**: Medium-High - Budget planning cycles are annual; cost control policies needed
- **Policy deadlines**: Aligns with national budget cycle (ongoing)
- **Dependencies**: None - standalone analysis; may inform capacity investment (PS-003) by quantifying cost implications
- **Justification**: Perennial stakeholder priority with annual budget relevance

**Total Score**: (5 × 0.4) + (4 × 0.3) + (4 × 0.3) = **2.0 + 1.2 + 1.2 = 4.4**  
**Priority Assignment**: **P0 (Critical)**

---

### PS-005: Healthcare Access Equity & Disparities (Diagnostic - Equity)

**Business Value: 3/5**
- **Alignment** with MOH goal: "Improve accessibility" and population health (business-objectives.md)
- **Stakeholder value**: Population health strategists, community health organizations
- **Decisions enabled**: Equity interventions, subsidy targeting, outreach program design
- **Strategic importance**: Moderate - Important for social mission but not system sustainability
- **Justification**: Valuable for equity goals but lower priority than workforce, cost control, capacity; -2 for being important but not critical to system function

**Feasibility: 2/5**
- **Data availability**: ⚠️ PARTIAL - Age/gender stratification confirmed BUT socioeconomic and ethnic data likely limited/absent
- **Data quality**: ✅ 100% complete for available variables
- **Technical complexity**: Moderate - Disparity metrics and statistical testing established, but interpretation nuanced
- **Resource requirements**: Medium - Equity analysis expertise; 4-5 sprints
- **Known constraints**: ⚠️ **MAJOR LIMITATION** - Cannot fully assess equity without socioeconomic/ethnic stratification; findings will be partial
- **Justification**: Significant data limitations restrict analysis depth; -3 for missing critical equity dimensions

**Urgency: 2/5**
- **Stakeholder urgency**: Medium - Equity is policy priority but not crisis-level
- **Time sensitivity**: Low - Equity initiatives operate on long timelines (multi-year programs)
- **Policy deadlines**: None immediate
- **Dependencies**: None - standalone; could inform resource allocation but not blocking
- **Justification**: Important but flexible timing; -3 for lack of pressing deadline or stakeholder demand

**Total Score**: (3 × 0.4) + (2 × 0.3) + (2 × 0.3) = **1.2 + 0.6 + 0.6 = 2.4**  
**Priority Assignment**: **P2 (Medium)**

---

### PS-006: Five-Year Disease Burden Forecasting and Mortality Projection (Predictive)

**Business Value: 4/5**
- **Direct alignment** with MOH goal: Proactive healthcare capacity planning and future-readiness
- **Stakeholder enabling**: Strategic planners and healthcare capacity planners gain 5-year demand foresight
- **Decisions enabled**: Hospital expansion, clinical service scaling, public health program sizing
- **Strategic importance**: Converts descriptive trend insight (PS-002) into actionable forecasts
- **Justification**: High strategic value for proactive planning; -1 relative to PS-001/PS-004 as it builds on PS-002 output and benefits from sequencing

**Feasibility: 4/5**
- **Data availability**: ✅ 30-year mortality time series confirmed (1990-2019) — excellent for forecasting
- **Data quality**: ✅ 100% complete, age-standardized rates, official source
- **Technical complexity**: Moderate-High - ARIMA/Prophet/SARIMAX + confidence intervals + backtesting; well-established methods
- **Resource requirements**: Medium-High - Forecasting analyst; 5-7 sprints estimated
- **Known constraints**: 7-year data lag (data ends 2019); COVID-19 disruption may affect trend continuity
- **Justification**: Good data for forecasting; -1 for COVID uncertainty and multi-model evaluation overhead

**Urgency: 3/5**
- **Stakeholder urgency**: Medium - Demand forecasts are valuable for planning but capital decisions operate on long cycles
- **Time sensitivity**: Medium - Healthcare planning horizons are 5-10 years; some immediacy but not crisis-driven
- **Policy deadlines**: None immediate; benefits from being scheduled after PS-002 establishes trend baseline
- **Dependencies**: PS-002 recommended input (trend patterns, inflection points) but not blocking
- **Justification**: High-value but sequencing after PS-002 reduces urgency; no hard deadline

**Total Score**: (4 × 0.4) + (4 × 0.3) + (3 × 0.3) = **1.6 + 1.2 + 0.9 = 3.7**  
**Priority Assignment**: **P1 (High)**

---

## Prioritized Problem Statement Portfolio

### P0 (Critical) - Immediate Start Recommended

**1. PS-001: Healthcare Workforce Sustainability (Score: 4.4)**
- **Rationale**: Highest urgency + high business value; workforce shortages are current pain point with long lead time for solutions
- **Recommended Action**: Start immediately; allocate senior analyst with forecasting expertise
- **Resource Allocation**: High priority - dedicate resources for 5-7 sprints
- **Dependencies**: None - can proceed independently

**2. PS-004: Healthcare Expenditure Drivers (Score: 4.4)**  
*(tied with PS-001)*
- **Rationale**: Critical for financial sustainability; aligns with annual budget cycles; Finance Ministry priority
- **Recommended Action**: Start immediately (can run parallel with PS-001)
- **Resource Allocation**: High priority - dedicate economist/financial analyst for 4-6 sprints
- **Dependencies**: None - can proceed independently

**3. PS-002: Disease Burden Temporal Trends (Score: 4.0)**
- **Rationale**: Excellent feasibility (perfect data, low complexity) + solid business value; foundational for public health strategy
- **Recommended Action**: Start in Sprint 1-2 (after PS-001 and PS-004 initiated if resource-constrained)
- **Resource Allocation**: Medium priority - can assign mid-level analyst
- **Dependencies**: None - can proceed independently; feeds PS-006

### P1 (High) - Near-Term Start (Within 3-6 Months)

**4. PS-003: Healthcare Capacity Optimization (Score: 3.8)**
- **Rationale**: Highest business value (infrastructure investment impact) but lower urgency (long planning cycles) and moderate feasibility (data limitations, optimization complexity)
- **Recommended Action**: Start after P0 problem statements underway; requires optimization expertise
- **Resource Allocation**: Medium-High priority - allocate experienced analyst with operations research skills
- **Dependencies**: May benefit from PS-001 findings (workforce constraints affect capacity planning) but not blocking

**5. PS-006: Disease Burden Forecasting (Score: 3.7)**
- **Rationale**: High value predictive extension of PS-002; moderate-high technical lift; benefits from PS-002 trend insights
- **Recommended Action**: Start after PS-002 completes or in parallel if staffing allows
- **Resource Allocation**: Medium priority - allocate forecasting analyst for 5-7 sprints
- **Dependencies**: PS-002 recommended as input (not blocking)

### P2 (Medium) - Planned Start (6-12 Months)

**6. PS-005: Healthcare Access Equity (Score: 2.4)**
- **Rationale**: Important for social mission but constrained by data limitations (missing socioeconomic/ethnic variables); lower urgency (no pressing deadlines)
- **Recommended Action**: Defer until P0/P1 problem statements completed; consider data enhancement efforts first
- **Resource Allocation**: Low-Medium priority - assign when resources available
- **Dependencies**: None technical, but may benefit from first obtaining richer demographic data
- **Enhancement Opportunity**: **Recommend engaging MOH to obtain ethnicity and socioeconomic stratification data before starting** - would significantly increase feasibility and value

---

## Execution Roadmap

### Phase 1 (Sprint 1-3): P0 Critical Analyses - Parallel Execution
- **PS-001 (Workforce)**: Start immediately - Workforce planner + forecasting analyst
- **PS-004 (Expenditure)**: Start immediately - Financial analyst/economist
- **PS-002 (Disease Burden)**: Start Sprint 2 - Public health analyst (if resources permit parallel work)

### Phase 2 (Sprint 4-8): P1 High-Priority Analysis
- **PS-003 (Capacity)**: Start after PS-001/PS-004 initiated - Operations research analyst
- Continue/complete P0 analyses

### Phase 3 (Sprint 9-12): P2 Medium-Priority Analysis
- **PS-005 (Equity)**: Start when resources available; ideally after data enhancement
- Complete P1 analyses

### Parallel Execution Strategy
**PS-001, PS-002, PS-004 can run in parallel** (no dependencies):
- If resources available (3+ analysts), start all three simultaneously for maximum velocity
- If resource-constrained (1-2 analysts), prioritize PS-001 and PS-004 first (both score 4.4)

**PS-003 can start while P0 analyses are in progress** (no blocking dependencies):
- May benefit from PS-001 findings but not required
- Can proceed independently if optimization expertise available

**PS-005 should start last**:
- Lower priority and data limitations suggest deferral
- Recommend data enhancement efforts before starting

---

## Recommendations

**Immediate Actions**:
1. **Initiate PS-001 and PS-004** as P0 Critical analyses - highest combined business value and urgency
2. **Allocate dedicated resources**: Senior analyst/forecaster for PS-001; Economist for PS-004
3. **Start PS-002 in Sprint 2** if resources permit - excellent feasibility makes it quick win

**Near-Term Planning**:
4. **Prepare for PS-003** (Capacity Optimization) - identify analyst with operations research skills; schedule for Sprint 4-5 start
5. **Socialize prioritization** with MOH stakeholders - validate priority assignments

**Future Enhancements**:
6. **For PS-005 (Equity)**: Engage MOH to request ethnicity and socioeconomic stratification data - would increase feasibility from 2/5 to 4/5 and business value from 3/5 to 4/5 (projected new score: 3.4 - P1 High)
7. **Monitor emerging priorities**: Healthcare landscape may change; reassess priorities quarterly

---

**Reviewed By**: _[Pending Stakeholder Review]_  
**Approved By**: _[Pending MOH Approval]_  
**Next Review Date**: 2026-06-11 (Quarterly reassessment)
