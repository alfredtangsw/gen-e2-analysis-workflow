# User Story: 1 — Load and Reconcile Planning Inputs

**As a** MOH resource planning lead,  
**I want** to load all PS-001 and PS-002 output artefacts along with four external reference datasets into a unified planning input layer,  
**so that** all subsequent gap calculations and cost estimates draw from a single, validated data foundation.

## 1. 🎯 Acceptance Criteria

- All 5 PS-001 processed outputs loaded and validated (row counts, column names, year bounds): `baseline_metrics.csv`, `benchmark_comparison.csv`, `system_balance_scorecard.csv`, cleaned parquets
- All 3 PS-002 outputs loaded: `admission_volume_projections.csv`, `ps002_demand_projections_export.csv`, `ps002_admission_sensitivity_2035.csv`
- Four external reference tables loaded and validated:
  1. WHO SEARO benchmark densities (hard-coded reference: nurses/10k=22.8, doctors/10k=2.3, beds/10k=21)
  2. MOM Occupational Wages Survey — median monthly gross wages for Registered Nurses and General Practitioners (SGD)
  3. MOH Annual Report — average annual attrition rate for nurses and doctors (%)
  4. Singapore Health Statistics — Average Length of Stay (ALOS) for acute hospitals (days)
- Input reconciliation report generated at `logs/etl/ps003_input_reconciliation.csv`: one row per input file with `file, rows, year_min, year_max, null_count, load_status`
- All inputs available as Polars DataFrames accessible by subsequent stories in the same pipeline

## 2. 🔒 Technical Constraints

- PS-001 and PS-002 outputs are loaded as `pl.read_csv()` or `pl.read_parquet()` — do not regenerate them in this story
- External references loaded as small in-memory dictionaries or single-row DataFrames — they do not require external HTTP calls at runtime; hard-code the values with source citations in comments:
  - ALOS: 5.1 days (MOH Health Statistics 2020)
  - Nurse:bed benchmark: 1 nurse per 4 beds = 0.25 ratio (WHO SEARO)
  - RN median wage: SGD 4,200/month (MOM OWS 2020); GP median wage: SGD 8,500/month (MOM OWS 2020)
  - Nurse attrition: ~8% p.a.; doctor attrition: ~3% p.a. (MOH Annual Report estimates)
- Overhead multiplier: 1.35× (WHO methodology — covers employer CPF, benefits, training)
- All external constants stored in `shared/config/base.yml` under `planning_constants:` key — do not hard-code in Python scripts; read from config YAML

## 3. 📚 Domain Knowledge References

- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — all benchmark values, ALOS formula, overhead methodology

## 4. 📦 Dependencies

- PS-001 `results/` and `data/4_processed/` directories (fully populated)
- PS-002 `models/forecasts/` and `results/exports/` directories (fully populated)
- `polars` — data loading
- `pyyaml` — config loading
- `loguru` — reconciliation logging

## 5. ✅ Implementation Tasks

**PS-001 Inputs**
- ⬜ Load `baseline_metrics.csv`; validate year range 2009–2018 and expected metric names; assert no nulls in `value` column
- ⬜ Load `benchmark_comparison.csv`; validate 8 KPI rows present; assert `gap_pct` column exists
- ⬜ Load `system_balance_scorecard.csv`; validate RAG column present

**PS-002 Inputs**
- ⬜ Load `admission_volume_projections.csv`; validate years 2021–2035 and 3 scenarios
- ⬜ Load `ps002_demand_projections_export.csv`; validate `source_ps == "PS-002"` column present
- ⬜ Load `ps002_admission_sensitivity_2035.csv`; validate 9 rows (3 scenarios × 3 rate assumptions)

**External Constants**
- ⬜ Load `shared/config/base.yml`; extract `planning_constants:` block into a Python dict
- ⬜ Assert all required keys present: `alos_days`, `nurse_bed_ratio_benchmark`, `rn_median_wage_sgd`, `gp_median_wage_sgd`, `nurse_attrition_pct`, `doctor_attrition_pct`, `overhead_multiplier`

**Reconciliation Report**
- ⬜ Assemble one row per input file/source with load metadata
- ⬜ Write `logs/etl/ps003_input_reconciliation.csv`
- ⬜ Log any validation failures at ERROR level; halt with informative message if any critical input fails

## 6. Notes

- This story is essentially a pre-flight check for PS-003. If any input file is missing or invalid, all downstream gap calculations will be wrong. Fail fast with clear error messages.
- The `planning_constants` in `base.yml` must be added if not already present (they were defined in PS-000 setup). Check before running.
- Hard-coding the external reference values (with source citations) is intentional — it avoids runtime HTTP calls and ensures reproducibility.

---

## Implementation Plan

### 1. Feature Overview

Pre-flight validation of all PS-001 and PS-002 upstream artefacts plus external planning constants. Load config from YAML. Write an input reconciliation CSV. Fail fast with informative errors. Primary user: **MOH resource planning lead**.

---

### 2. Affected Files

```
[CREATE] shared/config/base.yml
  - Adds planning_constants block with all required keys

[CREATE] problem-statements/ps-003-healthcare-capacity/src/planning_loader.py
  - load_planning_constants(config_path) -> dict
  - load_and_validate_ps001_outputs(ps001_dir) -> dict[str, pl.DataFrame]
  - load_and_validate_ps002_outputs(ps002_dir) -> dict[str, pl.DataFrame]
  - build_reconciliation_report(load_results) -> pl.DataFrame

[CREATE] problem-statements/ps-003-healthcare-capacity/scripts/run_planning_setup.py
  - Orchestrates pre-flight; writes reconciliation report; halts on critical failures
```

---

### 3. Code Generation Specifications

#### 3.1 `shared/config/base.yml` (add planning_constants block)

```yaml
# shared/config/base.yml
# Shared constants for PS-003 resource planning
# Update values when authoritative sources are refreshed.

planning_constants:
  # Clinical benchmarks
  alos_days: 5.1                          # Average Length of Stay (MOH Health Statistics 2020)
  occupancy_rate_benchmark: 0.85          # WHO/MOH target occupancy rate
  nurse_bed_ratio_benchmark: 0.25         # 1 nurse per 4 beds (WHO SEARO 2020)
  doctor_bed_ratio_benchmark: 0.10        # 1 doctor per 10 beds (planning proxy — cite MOH AR)
  beds_per_10k_benchmark: 21.0            # WHO SEARO beds per 10,000 population

  # WHO SEARO workforce density benchmarks
  nurses_per_10k_benchmark: 22.8
  doctors_per_10k_benchmark: 2.3

  # Workforce economics (MOM Occupational Wages Survey 2020)
  rn_median_wage_sgd: 4200                # Registered Nurse, median monthly gross
  gp_median_wage_sgd: 8500                # General Practitioner, median monthly gross
  overhead_multiplier: 1.35               # Employer CPF (17%) + benefits + training

  # Workforce dynamics (MOH Annual Report estimates)
  nurse_attrition_pct: 0.08               # 8% annual attrition — Registered Nurses
  doctor_attrition_pct: 0.03              # 3% annual attrition — Medical Practitioners
  # Other professions: use nurse_attrition_pct as conservative proxy

  # Planning horizons
  construction_lead_time_years: 5         # Typical hospital construction lead time
  gap_close_years: 5                      # Target years to close workforce gap

  # RAG thresholds for staff-facility alignment (nurse:bed ratio)
  rag_green_threshold: 0.25               # >= 0.25 = adequate
  rag_amber_threshold: 0.20               # 0.20–0.25 = monitor; < 0.20 = critical
```

#### 3.2 `src/planning_loader.py`

```python
"""PS-003 planning input loader and pre-flight validator.

All load functions return (data, load_status). load_status = "OK" | "WARN" | "ERROR".
The orchestration script halts on any "ERROR" status.
"""

import sys
from pathlib import Path
from typing import Any

import polars as pl
import yaml
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_PLANNING_CONSTANTS = [
    "alos_days", "occupancy_rate_benchmark", "nurse_bed_ratio_benchmark",
    "doctor_bed_ratio_benchmark", "rn_median_wage_sgd", "gp_median_wage_sgd",
    "overhead_multiplier", "nurse_attrition_pct", "doctor_attrition_pct",
    "construction_lead_time_years", "gap_close_years",
    "rag_green_threshold", "rag_amber_threshold",
]


def load_planning_constants(config_path: Path) -> dict[str, Any]:
    """Load and validate planning constants from shared/config/base.yml.

    Args:
        config_path: Absolute path to base.yml

    Returns:
        Dict of planning constant values

    Raises:
        FileNotFoundError: If config file not found
        KeyError: If required constant is missing
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    constants = config.get("planning_constants", {})
    missing = [k for k in REQUIRED_PLANNING_CONSTANTS if k not in constants]
    if missing:
        raise KeyError(f"Missing planning_constants keys: {missing}")

    logger.info(f"Planning constants loaded: {len(constants)} keys from {config_path.name}")
    return constants


def load_and_validate_ps001_outputs(ps001_dir: Path) -> dict[str, Any]:
    """Load and validate all required PS-001 output files.

    Args:
        ps001_dir: Root directory of PS-001 (ps-001-healthcare-system-baseline)

    Returns:
        Dict mapping output name to (DataFrame, load_status)
    """
    results: dict[str, Any] = {}
    required_files = {
        "baseline_metrics": ps001_dir / "results" / "tables" / "baseline_metrics.csv",
        "benchmark_comparison": ps001_dir / "results" / "tables" / "benchmark_comparison.csv",
        "system_balance_scorecard": ps001_dir / "results" / "tables" / "system_balance_scorecard.csv",
    }

    for name, path in required_files.items():
        if not path.exists():
            logger.error(f"PS-001 output missing: {path}")
            results[name] = (None, "ERROR")
            continue

        df = pl.read_csv(str(path))
        status = "OK"

        if name == "baseline_metrics":
            if "year" in df.columns:
                yr_range = (int(df["year"].min()), int(df["year"].max()))
                if yr_range[0] > 2009 or yr_range[1] < 2018:
                    logger.warning(f"baseline_metrics year range {yr_range} — expected 2009–2018")
                    status = "WARN"
            if "value" in df.columns and df["value"].null_count() > 0:
                logger.warning(f"Nulls in baseline_metrics.value: {df['value'].null_count()}")
                status = "WARN"

        elif name == "benchmark_comparison":
            if "gap_pct" not in df.columns:
                logger.error("benchmark_comparison missing gap_pct column")
                status = "ERROR"

        logger.info(f"PS-001 [{name}]: {df.shape}, status={status}")
        results[name] = (df, status)

    return results


def load_and_validate_ps002_outputs(ps002_dir: Path) -> dict[str, Any]:
    """Load and validate all required PS-002 output files.

    Args:
        ps002_dir: Root directory of PS-002 (ps-002-disease-burden)

    Returns:
        Dict mapping output name to (DataFrame, load_status)
    """
    results: dict[str, Any] = {}
    required_files = {
        "admission_volume_projections": (
            ps002_dir / "models" / "forecasts" / "admission_volume_projections.csv"
        ),
        "demand_projections_export": (
            ps002_dir / "results" / "exports" / "ps002_demand_projections_export.csv"
        ),
        "admission_sensitivity_2035": (
            ps002_dir / "results" / "tables" / "ps002_admission_sensitivity_2035.csv"
        ),
    }

    for name, path in required_files.items():
        if not path.exists():
            logger.error(f"PS-002 output missing: {path}")
            results[name] = (None, "ERROR")
            continue

        df = pl.read_csv(str(path))
        status = "OK"

        if name == "admission_volume_projections":
            if "scenario" in df.columns:
                scenarios = set(df["scenario"].unique().to_list())
                if not {"principal", "high", "low"}.issubset(scenarios):
                    logger.warning(f"Not all 3 scenarios found: {scenarios}")
                    status = "WARN"

        elif name == "demand_projections_export":
            if "source_ps" in df.columns:
                if not all(v == "PS-002" for v in df["source_ps"].to_list() if v):
                    logger.warning("source_ps column has non-PS-002 values")

        elif name == "admission_sensitivity_2035":
            if len(df) != 9:
                logger.warning(f"Sensitivity table has {len(df)} rows; expected 9")
                status = "WARN"

        logger.info(f"PS-002 [{name}]: {df.shape}, status={status}")
        results[name] = (df, status)

    return results


def build_reconciliation_report(
    load_results: dict[str, tuple[pl.DataFrame | None, str]]
) -> pl.DataFrame:
    """Assemble one-row-per-file reconciliation report.

    Args:
        load_results: Dict from load_and_validate_* functions

    Returns:
        Polars DataFrame for writing to CSV
    """
    rows: list[dict] = []
    for name, (df, status) in load_results.items():
        rows.append({
            "file": name,
            "rows": len(df) if df is not None else 0,
            "year_min": None,
            "year_max": None,
            "null_count": int(sum(df[c].null_count() for c in df.columns)) if df is not None else -1,
            "load_status": status,
        })
    return pl.DataFrame(rows)
```

#### 3.3 `scripts/run_planning_setup.py`

```python
"""PS-003 Story 01 — Planning Input Pre-flight.

Run: python problem-statements/ps-003-healthcare-capacity/scripts/run_planning_setup.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_003_healthcare_capacity.src.planning_loader import (
    build_reconciliation_report,
    load_and_validate_ps001_outputs,
    load_and_validate_ps002_outputs,
    load_planning_constants,
)

PS_DIR = Path(__file__).resolve().parent.parent
PS001_DIR = PROJECT_ROOT / "problem-statements" / "ps-001-healthcare-system-baseline"
PS002_DIR = PROJECT_ROOT / "problem-statements" / "ps-002-disease-burden"
CONFIG_PATH = PROJECT_ROOT / "shared" / "config" / "base.yml"
LOG_DIR = PS_DIR / "logs" / "etl"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.add(str(LOG_DIR / "ps003_setup.log"), level="INFO", rotation="10 MB")


def main() -> None:
    logger.info("=== PS-003 Story 01: Planning Input Pre-flight ===")

    # Load constants
    constants = load_planning_constants(CONFIG_PATH)
    logger.info(f"Constants: ALOS={constants['alos_days']}, "
                f"Occupancy={constants['occupancy_rate_benchmark']}, "
                f"Gap close years={constants['gap_close_years']}")

    # Validate PS-001 and PS-002 outputs
    ps001 = load_and_validate_ps001_outputs(PS001_DIR)
    ps002 = load_and_validate_ps002_outputs(PS002_DIR)
    all_results = {**ps001, **ps002}

    # Build reconciliation report
    report = build_reconciliation_report(all_results)
    report_path = LOG_DIR / "ps003_input_reconciliation.csv"
    report.write_csv(str(report_path))
    logger.info(f"Reconciliation report: {report_path}")

    # Halt on any ERROR
    errors = [name for name, (_, status) in all_results.items() if status == "ERROR"]
    if errors:
        logger.error(
            f"Pre-flight FAILED — {len(errors)} critical input(s) missing: {errors}\n"
            "Resolve missing files before running PS-003 analysis scripts."
        )
        raise SystemExit(1)

    logger.info("Pre-flight PASSED — all inputs valid. PS-003 analysis may proceed.")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_planning_loader.py
import polars as pl
import pytest
from pathlib import Path


def test_load_planning_constants_raises_on_missing_file(tmp_path):
    from problem_statements.ps_003_healthcare_capacity.src.planning_loader import load_planning_constants
    with pytest.raises(FileNotFoundError):
        load_planning_constants(tmp_path / "nonexistent.yml")


def test_load_planning_constants_raises_on_missing_key(tmp_path):
    from problem_statements.ps_003_healthcare_capacity.src.planning_loader import load_planning_constants
    config = tmp_path / "base.yml"
    config.write_text("planning_constants:\n  alos_days: 5.1\n", encoding="utf-8")
    with pytest.raises(KeyError, match="Missing"):
        load_planning_constants(config)


def test_build_reconciliation_report_shape():
    from problem_statements.ps_003_healthcare_capacity.src.planning_loader import build_reconciliation_report
    df_ok = pl.DataFrame({"a": [1, 2]})
    results = {"table_a": (df_ok, "OK"), "table_b": (None, "ERROR")}
    report = build_reconciliation_report(results)
    assert len(report) == 2
    assert "load_status" in report.columns
```

---

### 5. Implementation Steps

- [ ] Create `shared/config/base.yml` with `planning_constants:` block
- [ ] Create `problem-statements/ps-003-healthcare-capacity/src/__init__.py` (empty)
- [ ] Create `src/planning_loader.py`
- [ ] Create `scripts/run_planning_setup.py`
- [ ] Run: `python scripts/run_planning_setup.py`
- [ ] Check log: confirm "Pre-flight PASSED" or resolve listed errors
- [ ] Verify `logs/etl/ps003_input_reconciliation.csv` written
- [ ] Run unit tests: `pytest tests/unit/test_planning_loader.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-003-story-01-planning-setup
git commit -m "feat(shared): add planning_constants block to shared/config/base.yml"
git commit -m "feat(ps-003): add planning_loader and run_planning_setup pre-flight script"
```
