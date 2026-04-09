# User Stories: PS-005 Healthcare Access Equity & Disparities

**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Problem Statement**: [ps-005-healthcare-equity-disparities.md](../../problem_statements/ps-005-healthcare-equity-disparities.md)  
**Analysis Category**: Diagnostic Analytics (Equity Focus)  
**Priority**: P2 (Medium)

---

## Overview

This epic decomposes the health equity analysis into 9 sprint-ready user stories. These stories enable population health strategists to identify underserved populations and reduce health outcome disparities.

---

## User Story Index

### Stage 1-2: Data Extraction & Understanding
1. **[01-extract-demographic-health-data.md](01-extract-demographic-health-data.md)** - Extract utilization and outcome data with demographic stratification (S - 2 days, P0)
2. **[02-prepare-equity-analysis-data.md](02-prepare-equity-analysis-data.md)** - Integrate and standardize demographic health datasets (M - 4 days, P0)

### Stage 3-4: Disparity Analysis
3. **[03-analyze-utilization-disparities.md](03-analyze-utilization-disparities.md)** - Quantify healthcare utilization disparities by demographics (M - 5 days, P0)
4. **[04-analyze-outcome-disparities.md](04-analyze-outcome-disparities.md)** - Assess health outcome inequities (mortality, disease burden) (M - 5 days, P0)

### Stage 5: Advanced Equity Metrics
5. **[05-calculate-disparity-metrics.md](05-calculate-disparity-metrics.md)** - Calculate disparity ratios, concentration indices (M - 4-5 days, P0)
6. **[06-temporal-equity-trends.md](06-temporal-equity-trends.md)** - Analyze equity trends: are disparities widening or narrowing? (M - 4 days, P0)

### Stage 5-6: Root Cause & Recommendations
7. **[07-diagnose-access-barriers.md](07-diagnose-access-barriers.md)** - Diagnose potential access barriers and systemic inequities (M - 5 days, P1)
8. **[08-prioritize-vulnerable-populations.md](08-prioritize-vulnerable-populations.md)** - Identify and prioritize vulnerable demographic segments (M - 4 days, P0)

### Stage 7: Visualization
9. **[09-create-equity-dashboard.md](09-create-equity-dashboard.md)** - Build health equity monitor dashboard (L - 7-8 days, P0)

---

## Summary Statistics
- **Total User Stories**: 9
- **Total Effort**: ~44-50 days (9-10 sprint weeks)
- **P0 Stories**: 7 | **P1 Stories**: 2

---

## Expected Deliverables
1. **Curated Dataset**: `shared/data/4_processed/equity_analysis_2005_2020.parquet`
2. **Analytical Report**: Singapore Healthcare Equity Assessment (PDF, 30-40 pages)
3. **Interactive Dashboard**: Health Equity Monitor Dashboard
4. **Policy Brief**: Health Equity Action Plan 2026-2030 (8-12 pages)

---

## Domain Knowledge References

- [Health Equity Metrics & KPIs](../../../../domain-knowledge/health-equity-metrics-kpis.md) — Disparity ratio, absolute disparity, age-standardisation, concentration index. **Key data constraint documented**: SES and ethnicity data not available in current dataset.
- [Disease Burden Feature Engineering Guide](../../../../domain-knowledge/disease-burden-feature-engineering-guide.md) — Mortality rate methodology for outcome disparity analysis
- [Healthcare Capacity & Utilization Metrics](../../../../domain-knowledge/healthcare-capacity-utilization-metrics-kpis.md) — Utilisation metrics for access equity analysis

---

**Last Updated**: 2026-04-08
