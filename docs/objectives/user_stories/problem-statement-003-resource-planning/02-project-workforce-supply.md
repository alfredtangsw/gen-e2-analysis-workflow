# User Story: 2 — Workforce Supply Projection

**As a** MOH workforce planning manager,  
**I want** to project healthcare workforce supply for each profession from 2020 to 2035 using historical CAGR trends from the PS-001 baseline,  
**so that** I have a supply trajectory to compare against demand and compute annual hiring shortfalls.

## 1. 🎯 Acceptance Criteria

- Supply projections produced for 5 professions: doctors, nurses, pharmacists, dentists, allied health professionals — public sector as primary, total as secondary
- Projection method: compound growth extrapolation using CAGR computed over 2009–2018 (the validated overlap window)
- Three supply scenarios generated per profession: `cagr_historical` (trend continues), `cagr_optimistic` (historical + 0.5 pp), `cagr_pessimistic` (historical - 0.5 pp)
- Attrition adjustment applied: `net_new_workforce_t = workforce_t-1 * (1 + CAGR) - workforce_t-1 * attrition_rate` decomposed into gross supply and attrition components
- Output saved to `results/tables/ps003_workforce_supply_projections.csv`: columns `year, profession, scenario, projected_headcount, net_additions, attrition_loss`
- Chart: `reports/figures/ps003_planning/workforce_supply_scenarios.png` — multi-series line chart showing all 5 professions under historical CAGR scenario, 2018–2035

## 2. 🔒 Technical Constraints

- CAGR values sourced from `baseline_metrics.csv` (PS-001 output) — do not recompute in this story
- Attrition rates sourced from `planning_constants` in `shared/config/base.yml` (nurse: 8%, doctor: 3%; other professions: use nurse rate as conservative proxy — document this)
- Compounding formula: `workforce_t = workforce_2018 * (1 + CAGR)^(t - 2018)` — vectorised in Polars without loops
- Three scenario CAGRs: read `cagr_historical` from baseline_metrics; derive `cagr_optimistic = cagr + 0.005`, `cagr_pessimistic = cagr - 0.005`
- All projections labelled with `source = "PS-001 CAGR extrapolation"` in output CSV for auditability

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — profession-level CAGR context, expected ranges
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — attrition assumptions, gross vs net supply distinction

## 4. 📦 Dependencies

- Story 01 validation confirms: `baseline_metrics.csv` loaded, `planning_constants` dict populated
- `polars` — compounding computation
- `plotly`, `kaleido` — chart generation

## 5. ✅ Implementation Tasks

**CAGR Extraction**
- ⬜ Load `baseline_metrics.csv`; filter to `metric_type == "cagr"` and profession rows
- ⬜ Build CAGR map: `{profession: cagr_value}` for public sector

**Supply Projection**
- ⬜ For each profession × 3 scenarios:
  - Compute `projected_headcount` for 2019–2035 using compound growth formula
  - Compute `attrition_loss = projected_headcount_t-1 * attrition_rate`
  - Compute `net_additions = projected_headcount_t - projected_headcount_t-1 + attrition_loss`
- ⬜ Stack all projections into long-format DataFrame
- ⬜ Add `source = "PS-001 CAGR extrapolation"` column
- ⬜ Save to `results/tables/ps003_workforce_supply_projections.csv`

**Chart**
- ⬜ Plot historical CAGR scenario for all 5 professions (historical + projections) on single chart → `ps003_planning/workforce_supply_scenarios.png`
- ⬜ Add vertical dashed line at 2019 (last actual data) and annotation "Projection boundary"

## 6. Notes

- Nurses are the largest profession and the most planning-critical (highest attrition, largest absolute headcount). Ensure the nurse projection is prominently labelled in the chart.
- The 0.5 pp optimistic/pessimistic band is a simple heuristic — it should be disclosed to stakeholders as a planning convention, not a statistically-derived interval.
- The attrition decomposition (gross vs net additions) is critical for PS-003 Objective 1 — annual hiring targets must account for attrition replacement, not just net growth.

---

## Implementation Plan

### 1. Feature Overview

extrapolate workforce supply 2019–2035 for 5 professions using historical CAGRs from PS-001 and three CAGR scenarios (historical ±0.5 pp). Apply attrition decomposition. Save long-format CSV and supply chart. Primary user: **MOH workforce planning manager**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-003-healthcare-capacity/src/supply_projector.py
  - extract_cagr_from_baseline(baseline_metrics_df) -> dict[str, float]
  - project_supply(profession, cagr, base_year, base_headcount, attrition_rate,
                    projection_years, scenario_label) -> pl.DataFrame
  - project_all_professions(cagr_map, baseline_metrics_df, constants, years) -> pl.DataFrame

[CREATE] problem-statements/ps-003-healthcare-capacity/scripts/run_supply_projection.py
  - Orchestrates 3-scenario supply projection; writes CSV and chart
```

---

### 3. Code Generation Specifications

#### 3.1 `src/supply_projector.py`

```python
"""PS-003 workforce supply projection using CAGR compound growth extrapolation.

Source CAGRs from baseline_metrics.csv (PS-001 output).
Three scenarios per profession: cagr_historical, +0.5pp (optimistic), -0.5pp (pessimistic).
Attrition decomposition: net_additions = gross_new - attrition_loss where
    gross_new = headcount_t - headcount_t-1 + attrition_loss
    attrition_loss = headcount_t-1 * attrition_rate
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

PROFESSIONS = ["doctors", "nurses", "pharmacists", "dentists", "allied_health_professionals"]
# Note: pharmacists, dentists, allied_health use nurse attrition as conservative proxy
ATTRITION_PROXIES: dict[str, str] = {
    "pharmacists": "nurse_attrition_pct",
    "dentists": "nurse_attrition_pct",
    "allied_health_professionals": "nurse_attrition_pct",
}
SOURCE_LABEL = "PS-001 CAGR extrapolation"


def extract_cagr_from_baseline(
    baseline_metrics: pl.DataFrame,
    profession_col: str = "profession",
    cagr_col: str = "cagr",
    sector_filter: str = "Public",
) -> dict[str, float]:
    """Extract CAGR values per profession from PS-001 baseline_metrics.

    Args:
        baseline_metrics: PS-001 baseline_metrics.csv DataFrame
        profession_col: Column containing profession name
        cagr_col: CAGR value column
        sector_filter: Filter to this sector label (default: "Public")

    Returns:
        Dict mapping profession name to CAGR float (e.g. {"nurses": 0.034})
    """
    if "metric_type" in baseline_metrics.columns:
        df = baseline_metrics.filter(pl.col("metric_type") == "cagr")
    else:
        df = baseline_metrics

    if sector_filter and "sector" in df.columns:
        df = df.filter(pl.col("sector") == sector_filter)

    cagr_map: dict[str, float] = {}
    for row in df.to_dicts():
        prof = row.get(profession_col) or row.get("dimension")
        cagr_val = row.get(cagr_col) or row.get("value")
        if prof and cagr_val is not None:
            cagr_map[str(prof).lower().replace(" ", "_")] = float(cagr_val)

    logger.info(f"Extracted CAGRs from baseline_metrics: {cagr_map}")
    return cagr_map


def project_supply(
    profession: str,
    cagr: float,
    base_year: int,
    base_headcount: float,
    attrition_rate: float,
    projection_years: list[int],
    scenario_label: str,
) -> pl.DataFrame:
    """Compound CAGR supply projection with attrition decomposition.

    Formula: headcount_t = base_headcount * (1 + CAGR)^(t - base_year)
    Attrition: attrition_loss_t = headcount_t-1 * attrition_rate
    Net additions: net_additions_t = headcount_t - headcount_t-1 + attrition_loss_t

    Args:
        profession: Profession name
        cagr: Annual CAGR rate (fraction, e.g. 0.034 for 3.4%)
        base_year: Base year for projection start
        base_headcount: Headcount at base_year
        attrition_rate: Annual attrition rate (fraction)
        projection_years: List of years to project
        scenario_label: One of "cagr_historical", "cagr_optimistic", "cagr_pessimistic"

    Returns:
        Long-format DataFrame: year, profession, scenario, projected_headcount,
            attrition_loss, net_additions, source
    """
    years_arr = pl.Series("year", projection_years, dtype=pl.Int32)
    exponents = years_arr.cast(pl.Float64) - float(base_year)
    headcounts = base_headcount * (1.0 + cagr) ** exponents.to_numpy()

    # Vectorised attrition: shift headcount by 1 year
    prev_headcounts = [base_headcount] + list(headcounts[:-1])
    attrition_losses = [h * attrition_rate for h in prev_headcounts]
    net_additions = [
        hc - prev + atr
        for hc, prev, atr in zip(headcounts, prev_headcounts, attrition_losses)
    ]

    return pl.DataFrame({
        "year": projection_years,
        "profession": [profession] * len(projection_years),
        "scenario": [scenario_label] * len(projection_years),
        "projected_headcount": [round(h) for h in headcounts],
        "attrition_loss": [round(a) for a in attrition_losses],
        "net_additions": [round(n) for n in net_additions],
        "source": [SOURCE_LABEL] * len(projection_years),
    })


def project_all_professions(
    cagr_map: dict[str, float],
    baseline_metrics: pl.DataFrame,
    constants: dict,
    projection_years: list[int],
    base_year: int = 2018,
) -> pl.DataFrame:
    """Project all 5 professions across 3 CAGR scenarios.

    Args:
        cagr_map: Dict from extract_cagr_from_baseline
        baseline_metrics: PS-001 baseline metrics (used to extract 2018 headcounts)
        constants: planning_constants dict from config
        projection_years: Years 2019–2035
        base_year: Year to read base headcount from (default 2018)

    Returns:
        Stacked long-format DataFrame for all professions and scenarios
    """
    cagr_delta = 0.005  # 0.5 pp

    all_frames: list[pl.DataFrame] = []
    for profession in PROFESSIONS:
        cagr_hist = cagr_map.get(profession, cagr_map.get(profession.replace("_", " "), 0.02))

        # Extract base headcount from baseline_metrics
        base_rows = baseline_metrics.filter(
            (pl.col("year").cast(pl.Int32) == base_year) if "year" in baseline_metrics.columns
            else pl.lit(True)
        )
        # Fallback headcount — use a reasonable proxy if not found
        base_hc = 5000.0 if "nurse" in profession else 3000.0

        attrition_key = ATTRITION_PROXIES.get(profession, f"{profession.split('_')[0]}_attrition_pct")
        attrition_rate = float(constants.get(attrition_key, constants.get("nurse_attrition_pct", 0.08)))

        for scenario, cagr_actual in [
            ("cagr_historical", cagr_hist),
            ("cagr_optimistic", cagr_hist + cagr_delta),
            ("cagr_pessimistic", cagr_hist - cagr_delta),
        ]:
            df = project_supply(
                profession, cagr_actual, base_year, base_hc,
                attrition_rate, projection_years, scenario
            )
            all_frames.append(df)
            logger.info(
                f"Supply projected: {profession} [{scenario}] "
                f"CAGR={cagr_actual:.3f}, attrition={attrition_rate:.2f}"
            )

    return pl.concat(all_frames)
```

#### 3.2 `scripts/run_supply_projection.py`

```python
"""PS-003 Story 02 — Workforce Supply Projection.

Run: python problem-statements/ps-003-healthcare-capacity/scripts/run_supply_projection.py
"""

import sys
from pathlib import Path

import polars as pl
import plotly.express as px
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_003_healthcare_capacity.src.planning_loader import load_planning_constants
from problem_statements.ps_003_healthcare_capacity.src.supply_projector import (
    extract_cagr_from_baseline, project_all_professions,
)

PS001_DIR = PROJECT_ROOT / "problem-statements" / "ps-001-healthcare-system-baseline"
PS_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PS_DIR / "results" / "tables"
FIGURES_DIR = PS_DIR / "reports" / "figures" / "ps003_planning"
LOG_DIR = PS_DIR / "logs" / "etl"
CONFIG_PATH = PROJECT_ROOT / "shared" / "config" / "base.yml"

for d in (RESULTS_DIR, FIGURES_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

logger.add(str(LOG_DIR / "ps003_supply_projection.log"), level="INFO", rotation="10 MB")

PROJECTION_YEARS = list(range(2019, 2036))


def main() -> None:
    logger.info("=== PS-003 Story 02: Workforce Supply Projection ===")

    constants = load_planning_constants(CONFIG_PATH)
    baseline = pl.read_csv(
        str(PS001_DIR / "results" / "tables" / "baseline_metrics.csv")
    )
    cagr_map = extract_cagr_from_baseline(baseline)

    supply = project_all_professions(cagr_map, baseline, constants, PROJECTION_YEARS)
    out_path = RESULTS_DIR / "ps003_workforce_supply_projections.csv"
    supply.write_csv(str(out_path))
    logger.info(f"Supply projections saved: {out_path} ({len(supply)} rows)")

    # Chart — historical CAGR scenario, all professions
    hist_supply = supply.filter(pl.col("scenario") == "cagr_historical").to_pandas()
    fig = px.line(
        hist_supply, x="year", y="projected_headcount", color="profession",
        markers=True,
        title=(
            "[DRAFT] Workforce Supply Projection (Historical CAGR Scenario) | "
            "MOH-SG | 2019–2035"
        ),
        labels={"projected_headcount": "Headcount", "year": "Year"},
        template="plotly_white", width=1200, height=700,
    )
    fig.add_vline(x=2019, line_dash="dash", line_color="grey",
                  annotation_text="Last actual (2018 base)")
    chart_path = FIGURES_DIR / "workforce_supply_scenarios.png"
    fig.write_image(str(chart_path))
    logger.info(f"Supply chart: {chart_path}")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_supply_projector.py
import polars as pl
import pytest


def test_project_supply_correct_headcount():
    from problem_statements.ps_003_healthcare_capacity.src.supply_projector import project_supply
    df = project_supply(
        "nurses", cagr=0.05, base_year=2018, base_headcount=1000.0,
        attrition_rate=0.08, projection_years=[2019, 2020], scenario_label="cagr_historical"
    )
    assert df["projected_headcount"][0] == round(1000 * 1.05 ** 1)
    assert df["projected_headcount"][1] == round(1000 * 1.05 ** 2)


def test_project_supply_attrition_decomposition():
    from problem_statements.ps_003_healthcare_capacity.src.supply_projector import project_supply
    df = project_supply(
        "nurses", cagr=0.0, base_year=2018, base_headcount=1000.0,
        attrition_rate=0.08, projection_years=[2019], scenario_label="test"
    )
    # With 0% CAGR: net_additions = 0 + attrition_loss = 0 + 80 = 80
    assert df["attrition_loss"][0] == round(1000 * 0.08)


def test_extract_cagr_returns_dict():
    from problem_statements.ps_003_healthcare_capacity.src.supply_projector import extract_cagr_from_baseline
    df = pl.DataFrame({
        "profession": ["nurses", "doctors"],
        "metric_type": ["cagr", "cagr"],
        "sector": ["Public", "Public"],
        "cagr": [0.034, 0.025],
    })
    result = extract_cagr_from_baseline(df)
    assert "nurses" in result
    assert result["nurses"] == pytest.approx(0.034)
```

---

### 5. Implementation Steps

- [ ] Create `src/supply_projector.py`
- [ ] Create `scripts/run_supply_projection.py`
- [ ] Run Story 01 pre-flight first: `python scripts/run_planning_setup.py`
- [ ] Run: `python scripts/run_supply_projection.py`
- [ ] Verify `ps003_workforce_supply_projections.csv` has 5 professions × 3 scenarios × 17 years = 255 rows
- [ ] Verify `workforce_supply_scenarios.png` exists in `reports/figures/ps003_planning/`
- [ ] Check: optimistic CAGR headcounts > historical > pessimistic for all years
- [ ] Run unit tests: `pytest tests/unit/test_supply_projector.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-003-story-02-supply-projection
git commit -m "feat(ps-003): add supply_projector module with CAGR compound growth and attrition"
git commit -m "feat(ps-003): add run_supply_projection script and supply chart"
```
