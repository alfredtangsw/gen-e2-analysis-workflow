# Diagnose Access Barriers & Systemic Inequities (Lifecycle Stage: Advanced Analysis)

**Story ID**: PS-005-US-07  
**Epic**: Healthcare Access Equity & Demographic Disparities Analysis  
**Priority**: P1 (High)  
**Effort Estimate**: M (5 days)  
**Created**: March 11, 2026

---

## 📝 User Story Description

As a **Population Health Strategist designing equity interventions**,  
I want **to diagnose potential root causes of observed disparities including access barriers, social determinants, and systemic inequities**,  
So that **I can recommend targeted interventions addressing root causes rather than just symptoms of health inequity**.

---

## 🎯 Acceptance Criteria

1. **Barrier hypotheses developed**
   - Geographic access barriers (if geospatial data available)
   - Financial barriers (relevant to different demographics)
   - Cultural/language barriers
   - Health literacy barriers

2. **Disparity patterns analyzed for root causes**
   - Utilization-outcome mismatches: quality vs access issues
   - Demographic-specific patterns suggest specific barriers
   - Comparison with other datasets (if available): social determinants

3. **Systemic inequity indicators**
   - Persistent disparities despite policy efforts
   - Widening gaps suggesting structural issues
   - Intersection of multiple disadvantages (age + other factors)

4. **Deliverables**
   - Output: `results/tables/equity_barrier_diagnosis.csv`
   - Report: Root cause analysis and intervention recommendations
   - Figures: Diagnostic charts

---

## 🔒 Technical Constraints

- **Platform**: Databricks Runtime 13.3.x, Python 3.9
- **Primary Library**: Polars 0.20+
- **Analysis**: Qualitative synthesis + quantitative patterns
- **Logging**: loguru
- **Testing**: pytest ≥80% coverage

---

## 📚 Domain Knowledge References

- [Domain Knowledge Research](../../../problem_statements/DOMAIN_KNOWLEDGE_RESEARCH.md#health-equity-barriers)
- [Problem Statement PS-005](../../../problem_statements/ps-005-healthcare-equity-disparities.md#objective-4)

---

## 📦 Dependencies

### External Packages
- `polars>=0.20.0`, `matplotlib>=3.8.0`, `loguru>=0.7.0`

### Internal Dependencies
- **Upstream**: PS-005-US-03, PS-005-US-04, PS-005-US-06 (All disparity analyses - BLOCKING)
- **Data Sources**: All PS-005 analysis outputs

---

## ✅ Implementation Tasks

### Barrier Hypothesis Development
- [ ] Identify demographic groups with low utilization + poor outcomes
- [ ] Map to likely barriers (geographic, financial, cultural)
- [ ] Literature review: known barriers for identified demographics

### Pattern Analysis
- [ ] Utilization-outcome mismatch patterns
- [ ] Temporal pattern analysis: persistent vs emerging barriers
- [ ] Cross-demographic comparison

### Systemic Indicator Assessment
- [ ] Persistent disparities despite interventions
- [ ] Widening gaps identification
- [ ] Intersectionality analysis (multiple disadvantages)

### Recommendation Development
- [ ] Barrier-specific interventions
- [ ] Systemic change recommendations
- [ ] Priority populations for intervention

### Testing & Documentation
- [ ] Validate barrier hypotheses against domain knowledge
- [ ] Docstrings
- [ ] Root cause report

---

## 📌 Notes

**Common Barriers**:
- **Geographic**: Distance to facilities
- **Financial**: Cost, insurance gaps
- **Cultural**: Language, mistrust
- **Informational**: Health literacy, awareness
- **Systemic**: Discrimination, implicit bias

**Intervention Map**:
- Geographic barriers → Mobile clinics, telemedicine
- Financial barriers → Subsidies, insurance expansion
- Cultural barriers → Culturally tailored programs, language services
- Systemic barriers → Policy change, workforce diversity

---

## Implementation Plan

### 1. Feature Overview

Synthesize all upstream disparity findings (US-03 through US-06) to diagnose potential root causes of observed healthcare access barriers and systemic inequities. Classify each demographic group's disparity pattern into a barrier typology, cross-reference with domain literature, and produce structured intervention hypotheses.

**Primary User Role**: Population Health Strategist designing equity interventions

**Key Deliverable**: `results/tables/equity_barrier_diagnosis.csv` mapping demographic groups to barrier typologies and recommended interventions, plus a diagnostic narrative report.

**Important constraint**: Data limitations (age and sex only, no SES/geography) mean root cause attributions are hypothesis-level, not causally confirmed. This must be documented explicitly.

---

### 2. Component Analysis & Reuse Strategy

| Component | Action | Justification |
|-----------|--------|---------------|
| All PS-005 results tables | Reuse | `results/tables/utilization_disparity_analysis.csv`, `outcome_disparity_analysis.csv`, `equity_temporal_trends.csv` |
| `equity_analysis_integrated.parquet` | Reuse | For pattern-matching logic |
| `access_barrier_diagnosis.py` | **Create** | Pattern classification, barrier hypothesis engine |
| `test_access_barrier_diagnosis.py` | **Create** | ≥80% coverage |

---

### 3. ML Model Evaluation & Selection

Not applicable — this is a qualitative synthesis + pattern-matching analysis story. No predictive modelling.

---

### 4. Affected Files

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/src/access_barrier_diagnosis.py`**
  - Functions: `classify_barrier_typology(util_ratio: float, outcome_ratio: float, trend: str) -> dict[str, str]`, `build_barrier_diagnosis_table(disparity_df: pl.DataFrame, trend_df: pl.DataFrame) -> pl.DataFrame`, `run_barrier_diagnosis(results_dir: Path, output_dir: Path) -> pl.DataFrame`
  - Dependencies: `polars`, `loguru`, `pathlib`
  - Logging: `logs/analysis/barrier_diagnosis_{timestamp}.log`

- **[CREATE] `problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_access_barrier_diagnosis.py`**

---

### 5. Data Pipeline

**Inputs**:
- `results/tables/utilization_disparity_analysis.csv` — mean_rate_ratio per group (from US-03)
- `results/tables/outcome_disparity_analysis.csv` — mortality ratios (from US-04)
- `results/tables/equity_temporal_trends.csv` — convergence_status per group (from US-06)

**Processing**:
1. Load and join all tables on `demographic_group`
2. Apply barrier typology classifier per group:
   - Low utilisation + Poor outcomes + Stable/Diverging trend → **Access barrier (high priority)**
   - High utilisation + Poor outcomes → **Quality concern**
   - Low utilisation + Good outcomes → **Possibly healthy population or preventive care gap**
   - Widening disparity regardless of quadrant → **Systemic/structural concern**
3. Map barrier typology to hypothesis set from domain knowledge
4. Score urgency: widening = high, stable high-disparity = medium, converging = low
5. Output: `results/tables/equity_barrier_diagnosis.csv`

---

### 6. Code Generation Specifications

#### 6.1 Complete Function Implementations

```python
# problem-statements/ps-005-healthcare-equity-disparities/src/access_barrier_diagnosis.py

from pathlib import Path
from datetime import datetime

import polars as pl
from loguru import logger


# ── Barrier typology definitions ────────────────────────────────────────────
BARRIER_HYPOTHESES: dict[str, dict[str, str]] = {
    "Access barrier": {
        "description": "Low utilisation with poor outcomes suggests unmet need",
        "likely_causes": "Geographic distance, financial cost, cultural/language barriers, health literacy",
        "interventions": "Mobile clinics, subsidies, culturally-tailored outreach, health literacy programs",
    },
    "Quality concern": {
        "description": "High utilisation but poor outcomes suggests care quality issues",
        "likely_causes": "Inadequate care quality, delayed treatment, comorbidity complexity",
        "interventions": "Care quality audits, specialist referral pathways, disease management programs",
    },
    "Healthy/preventive gap": {
        "description": "Low utilisation with good outcomes — may reflect healthy population or preventive care gap",
        "likely_causes": "Good baseline health, low perceived need, possible under-screening",
        "interventions": "Preventive screening campaigns, health promotion",
    },
    "Effective care": {
        "description": "High utilisation with good outcomes — care is reaching and helping this group",
        "likely_causes": "Established care pathways, appropriate utilisation",
        "interventions": "Maintain and replicate successful care models",
    },
    "Systemic inequity": {
        "description": "Disparity widening despite overall system improvement — structural barrier",
        "likely_causes": "Structural disadvantage, differential policy impact, cumulative disadvantage",
        "interventions": "Targeted equity policies, differential subsidy scaling, workforce diversity",
    },
}


def _setup_logging(log_dir: str = "logs/analysis") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(
        Path(log_dir) / f"barrier_diagnosis_{ts}.log",
        rotation="10 MB",
        level="INFO",
    )


def classify_barrier_typology(
    util_ratio: float,
    outcome_ratio: float | None,
    convergence_status: str,
) -> dict[str, str]:
    """
    Classify a demographic group's barrier typology based on disparity patterns.

    Args:
        util_ratio: Mean utilisation rate ratio vs reference (>1=high, <1=low).
        outcome_ratio: Mean mortality/outcome rate ratio vs reference. None if unavailable.
        convergence_status: Trend classification from US-06
            (e.g. 'Converging', 'Diverging', 'Stable').

    Returns:
        Dict with keys: barrier_type, urgency, description, likely_causes, interventions.
    """
    # Systemic check takes priority regardless of quadrant
    if "Diverging" in convergence_status:
        typology_key = "Systemic inequity"
        urgency = "HIGH"
    elif outcome_ratio is None:
        # Without outcome data, classify by utilisation only
        if util_ratio < 0.8:
            typology_key = "Access barrier"
            urgency = "HIGH" if util_ratio < 0.67 else "MEDIUM"
        elif util_ratio > 1.5:
            typology_key = "Quality concern"
            urgency = "MEDIUM"
        else:
            typology_key = "Effective care"
            urgency = "LOW"
    else:
        # Full 2x2 matrix classification
        high_util = util_ratio > 1.0
        poor_outcome = outcome_ratio > 1.0
        if not high_util and poor_outcome:
            typology_key = "Access barrier"
            urgency = "HIGH"
        elif high_util and poor_outcome:
            typology_key = "Quality concern"
            urgency = "MEDIUM"
        elif not high_util and not poor_outcome:
            typology_key = "Healthy/preventive gap"
            urgency = "LOW"
        else:
            typology_key = "Effective care"
            urgency = "LOW"

    hypothesis = BARRIER_HYPOTHESES[typology_key]
    return {
        "barrier_type": typology_key,
        "urgency": urgency,
        "description": hypothesis["description"],
        "likely_causes": hypothesis["likely_causes"],
        "recommended_interventions": hypothesis["interventions"],
    }


def build_barrier_diagnosis_table(
    disparity_df: pl.DataFrame,
    trend_df: pl.DataFrame,
) -> pl.DataFrame:
    """
    Build the full barrier diagnosis table by joining disparity and trend data.

    Args:
        disparity_df: From utilization_disparity_analysis.csv; needs
            [demographic_group, mean_rate_ratio].
        trend_df: From equity_temporal_trends.csv; needs
            [demographic_group, convergence_status].

    Returns:
        Barrier diagnosis DataFrame with typology, urgency, and interventions.
    """
    merged = disparity_df.join(
        trend_df.select(["demographic_group", "convergence_status"]),
        on="demographic_group",
        how="left",
    )
    merged = merged.with_columns(
        pl.col("convergence_status").fill_null("Unknown")
    )

    diagnosis_rows = []
    for row in merged.iter_rows(named=True):
        group = row["demographic_group"]
        util_ratio = float(row.get("mean_rate_ratio", 1.0))
        outcome_ratio = row.get("mean_mortality_ratio")  # may be None
        convergence = str(row.get("convergence_status", "Unknown"))

        typology = classify_barrier_typology(util_ratio, outcome_ratio, convergence)
        typology["demographic_group"] = group
        typology["util_rate_ratio"] = round(util_ratio, 4)
        typology["outcome_rate_ratio"] = outcome_ratio
        typology["convergence_status"] = convergence
        typology["data_limitations"] = (
            "National aggregate only; no SES, ethnicity, or geographic breakdown available. "
            "Root cause attributions are hypothesis-level only."
        )
        diagnosis_rows.append(typology)

    result = pl.DataFrame(diagnosis_rows).sort(["urgency", "barrier_type"])
    logger.info(
        f"Barrier diagnosis complete: {result.shape[0]} groups classified; "
        f"HIGH urgency={result.filter(pl.col('urgency') == 'HIGH').shape[0]}"
    )
    return result


def run_barrier_diagnosis(results_dir: Path, output_dir: Path) -> pl.DataFrame:
    """
    Orchestrate the access barrier diagnosis pipeline.

    Args:
        results_dir: Directory containing upstream results CSVs.
        output_dir: Directory for barrier diagnosis outputs.

    Returns:
        Barrier diagnosis DataFrame.
    """
    _setup_logging()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load upstream results
    disparity_path = results_dir / "tables" / "utilization_disparity_analysis.csv"
    trend_path = results_dir / "tables" / "equity_temporal_trends.csv"

    if not disparity_path.exists():
        raise FileNotFoundError(
            f"Disparity analysis not found: {disparity_path}. Run US-03 first."
        )

    disparity_df = pl.read_csv(disparity_path)
    logger.info(f"Loaded disparity data: {disparity_df.shape[0]} groups")

    if trend_path.exists():
        trend_df = pl.read_csv(trend_path)
        logger.info(f"Loaded trend data: {trend_df.shape[0]} groups")
    else:
        logger.warning("Trend data not found; classification will use utilisation data only")
        trend_df = pl.DataFrame(
            {"demographic_group": disparity_df["demographic_group"].to_list(),
             "convergence_status": ["Unknown"] * disparity_df.shape[0]}
        )

    diagnosis_df = build_barrier_diagnosis_table(disparity_df, trend_df)

    output_path = output_dir / "tables" / "equity_barrier_diagnosis.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    diagnosis_df.write_csv(output_path)
    logger.info(f"Barrier diagnosis saved: {output_path}")
    return diagnosis_df
```

---

### 7. Domain-Driven Feature Engineering

**Step 1 — Domain knowledge**: Barrier typology from `health-equity-metrics-kpis.md` and `ps-005` problem statement

**Step 2 — Data availability**:
| Feature | Available | Source |
|---------|-----------|--------|
| Utilisation rate ratio | ✅ | US-03 output |
| Trend convergence | ✅ | US-06 output |
| Outcome ratio | ⚠️ Limited | US-04 (mortality only, limited sex breakdown) |
| SES barriers | ❌ | Not in dataset — hypothesis only |
| Geographic barriers | ❌ | Not in dataset — hypothesis only |

All root-cause attributions are clearly flagged as hypothesis-level in the `data_limitations` column.

---

### 10. Testing Strategy

```python
# problem-statements/ps-005-healthcare-equity-disparities/tests/unit/test_access_barrier_diagnosis.py

import polars as pl
import pytest
from problem_statements.ps_005.src.access_barrier_diagnosis import (
    classify_barrier_typology,
    build_barrier_diagnosis_table,
)


def test_classify_access_barrier():
    result = classify_barrier_typology(
        util_ratio=0.5, outcome_ratio=1.8, convergence_status="Stable"
    )
    assert result["barrier_type"] == "Access barrier"
    assert result["urgency"] == "HIGH"


def test_classify_systemic_inequity_diverging():
    result = classify_barrier_typology(
        util_ratio=1.2, outcome_ratio=1.0, convergence_status="Diverging (equity worsening)"
    )
    assert result["barrier_type"] == "Systemic inequity"
    assert result["urgency"] == "HIGH"


def test_classify_effective_care():
    result = classify_barrier_typology(
        util_ratio=1.3, outcome_ratio=0.8, convergence_status="Converging (equity improving)"
    )
    assert result["barrier_type"] == "Effective care"


def test_build_barrier_table_output_shape():
    disp_df = pl.DataFrame({
        "demographic_group": ["25-44 years", "65+ years"],
        "mean_rate_ratio": [1.0, 5.0],
    })
    trend_df = pl.DataFrame({
        "demographic_group": ["25-44 years", "65+ years"],
        "convergence_status": ["Stable (persistent gap)", "Diverging (equity worsening)"],
    })
    result = build_barrier_diagnosis_table(disp_df, trend_df)
    assert result.shape[0] == 2
    assert "barrier_type" in result.columns
    assert "data_limitations" in result.columns
```

---

### 11. Implementation Steps

**Phase 1 — Load & Validate Inputs**
- [ ] Confirm `results/tables/utilization_disparity_analysis.csv` exists (US-03 must be complete)
- [ ] Confirm `results/tables/equity_temporal_trends.csv` exists (US-06 must be complete)
- [ ] Load both files and inspect column names; adjust join key if column naming differs

**Phase 2 — Classification**
- [ ] Run `build_barrier_diagnosis_table()` on loaded data
- [ ] Review output: expect elderly groups classified as either `"Access barrier"` or `"Quality concern"`
- [ ] Manually validate 2–3 entries against raw disparity values

**Phase 3 — Output**
- [ ] Write `results/tables/equity_barrier_diagnosis.csv`
- [ ] Review HIGH urgency groups — prepare narrative summary for notebook

**Phase 4 — Testing**
- [ ] Run pytest with ≥80% coverage on `access_barrier_diagnosis.py`

---

### 12. Adaptive Implementation Strategy

- If outcome ratio not available (no sex/age breakdown in mortality) → `classify_barrier_typology()` gracefully handles `None` for `outcome_ratio` using utilisation-only classification
- If column names in upstream CSVs differ from expected → add rename step at load time
- If ALL groups classified as `"Effective care"` → check that reference group is correctly set (reference group itself always presents ratio ≈ 1.0; exclude from interpretation)

---

### 14. Data Quality & Validation

| Check | Expected | Action |
|-------|----------|--------|
| All groups from US-03 present in output | Same count | Log any missing groups |
| Urgency values | Only HIGH/MEDIUM/LOW | Raise if other value found |
| `data_limitations` column populated | 100% | Assert non-null |
| Output CSV row count | ≥ 1 | Raise if empty |

---

### 20. Security & Privacy

Aggregated data only. Results in `results/` (git-ignored).

---

### 21. Version Control

- Branch: `feature/ps-005-access-barrier-diagnosis`
- Commits:
  - `feat(ps-005): add barrier typology classifier and diagnosis pipeline`
  - `test(ps-005): add unit tests for classify_barrier_typology and build_barrier_table`
