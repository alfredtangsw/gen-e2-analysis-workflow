# User Story: 6 — System Balance Scorecard

**As a** MOH Deputy Secretary for Planning,  
**I want** a structured system balance scorecard that benchmarks Singapore's workforce density and bed capacity against WHO standards and highlights divergence between workforce and facility growth,  
**so that** I can identify which dimensions are under-resourced heading into the 2020–2035 planning horizon.

## 1. 🎯 Acceptance Criteria

- The scorecard contains 8 headline KPIs as rows: doctors/10k (public + private), nurses/10k (public + private), pharmacists/10k, beds/10k (acute), primary care clinics/10k, nurse:bed ratio (public), CAGR nurses (2009–2018), CAGR beds (2009–2018)
- Each row includes: Singapore 2018 actual, WHO SEARO benchmark (or regional reference where available), gap (absolute and percentage), and a traffic-light RAG status (🔴 >15% below benchmark, 🟡 within 15%, 🟢 at or above)
- A structural divergence section identifies whether workforce and bed growth have been diverging or converging (by comparing respective CAGRs)
- Scorecard exported as `results/tables/system_balance_scorecard.csv`
- Scorecard rendered as an 8-row HTML table with RAG colours in `results/exports/system_balance_scorecard.html`

## 2. 🔒 Technical Constraints

- Scorecard values sourced strictly from `results/tables/baseline_metrics.csv` and `results/tables/benchmark_comparison.csv` — no re-computation in this story
- RAG thresholds: green ≥ 0% gap (at or above benchmark), amber -15% to <0%, red < -15%
- HTML rendering uses `str.replace` / f-string template — no external HTML library required
- All row labels must be human-readable strings (not column codes)
- Score file must include metadata row: `generated_on`, `data_window`, `benchmark_source`

## 3. 📚 Domain Knowledge References

- [Healthcare Workforce Metrics & KPIs](../../../../domain-knowledge/healthcare-workforce-metrics-kpis.md) — benchmark values and interpretation
- [Integrated Resource Planning Guide](../../../../domain-knowledge/integrated-resource-planning-guide.md) — nurse:bed benchmark, overhead ratios

## 4. 📦 Dependencies

- Story 05 outputs: `results/tables/baseline_metrics.csv`, `results/tables/benchmark_comparison.csv`
- `polars` — filtered reads
- Standard library `html` — for safe HTML table rendering

## 5. ✅ Implementation Tasks

**Scorecard Assembly**
- ⬜ Load `benchmark_comparison.csv` using Polars
- ⬜ Filter to 8 KPI rows; map to human-readable labels
- ⬜ Compute `rag_status` column using conditional expression: `gap_pct >= 0 → "green"`, `gap_pct >= -15 → "amber"`, `gap_pct < -15 → "red"`
- ⬜ Add structural divergence flag: compare CAGR nurses vs CAGR beds — if difference > 1 pp, flag as "Diverging"
- ⬜ Save to `results/tables/system_balance_scorecard.csv`

**HTML Export**
- ⬜ Build HTML string: header row + 8 data rows with inline `background-color` for RAG cells
- ⬜ Add metadata footer: generated date, data window 2009–2018, WHO GHO 2020 benchmark source
- ⬜ Save to `results/exports/system_balance_scorecard.html`

**Logging**
- ⬜ Log each KPI row to `logs/etl/ps001_scorecard.log` with: metric name, singapore value, benchmark, gap, rag
- ⬜ Log a final summary line: "X of 8 KPIs are at or above benchmark; Y are in red"

## 6. Notes

- The scorecard is the primary artefact that answers PS-001 Objective 4 (system balance, staff-to-bed ratios vs benchmarks).
- It will also be imported directly as the "Baseline" tab of the PS-003 executive dashboard.
- RAG thresholds should be configurable via `shared/config/base.yml` for future adjustment — add keys `rag_green_threshold: 0.0` and `rag_amber_threshold: -0.15`.

---

## Implementation Plan

### 1. Feature Overview

Assemble the 8-KPI system balance scorecard from Story 05 outputs, apply RAG traffic-light classification, and render a styled HTML report. Primary user: **MOH Deputy Secretary for Planning**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-001-healthcare-system-baseline/src/scorecard.py
  - Function: build_scorecard(benchmark_df, metrics_df, rag_thresholds) -> pl.DataFrame
  - Function: render_html_scorecard(scorecard_df, output_path) -> None

[CREATE] problem-statements/ps-001-healthcare-system-baseline/scripts/run_scorecard.py
[CREATE] problem-statements/ps-001-healthcare-system-baseline/tests/unit/test_scorecard.py
```

---

### 3. Code Generation Specifications

#### 3.1 `src/scorecard.py`

```python
"""System balance scorecard builder for PS-001.

Assembles 8 KPI rows, applies RAG classification, and renders HTML.
All values sourced from Story 05 outputs — no recomputation here.
"""

import html as html_lib
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl
from loguru import logger

# Human-readable label map
KPI_LABEL_MAP: dict[str, str] = {
    "nurses_per_10k": "Nurses per 10,000 population",
    "doctors_per_10k": "Doctors per 10,000 population",
    "pharmacists_per_10k": "Pharmacists per 10,000 population",
    "beds_per_10k": "Inpatient beds per 10,000 population",
    "nurses_per_bed_public": "Nurse:bed ratio (public sector)",
    "cagr_nurses": "CAGR — Nurses (2009–2018)",
    "cagr_beds": "CAGR — Inpatient beds (2009–2018)",
}

RAG_COLOURS: dict[str, str] = {
    "green": "#27AE60",
    "amber": "#F39C12",
    "red": "#E74C3C",
}


def _classify_rag(
    gap_pct: float,
    green_threshold: float = 0.0,
    amber_threshold: float = -15.0,
) -> str:
    """Return RAG status based on gap percentage.

    Args:
        gap_pct: (singapore - benchmark) / benchmark * 100
        green_threshold: Gap % at or above = green
        amber_threshold: Gap % between amber_threshold and green = amber

    Returns:
        One of "green", "amber", "red"
    """
    if gap_pct >= green_threshold:
        return "green"
    if gap_pct >= amber_threshold:
        return "amber"
    return "red"


def build_scorecard(
    benchmark_df: pl.DataFrame,
    rag_green_threshold: float = 0.0,
    rag_amber_threshold: float = -15.0,
) -> pl.DataFrame:
    """Build the 8-KPI system balance scorecard.

    Args:
        benchmark_df: Output of build_benchmark_comparison() from Story 05
        rag_green_threshold: Gap % at or above = green (default 0.0)
        rag_amber_threshold: Gap % floor for amber (default -15.0)

    Returns:
        Scorecard DataFrame with columns:
        kpi_label, singapore_2018, who_benchmark, gap_pct, rag_status
    """
    rows: list[dict[str, Any]] = []

    for record in benchmark_df.to_dicts():
        metric = record["metric"]
        label = KPI_LABEL_MAP.get(metric, metric.replace("_", " ").title())
        gap_pct = record["gap_pct"]
        rag = _classify_rag(gap_pct, rag_green_threshold, rag_amber_threshold)

        rows.append({
            "kpi_label": label,
            "metric_code": metric,
            "singapore_2018": record["singapore_2018"],
            "who_searo_benchmark": record["who_searo_benchmark"],
            "gap_pct": gap_pct,
            "rag_status": rag,
        })
        logger.info(
            f"KPI: {label} | SG={record['singapore_2018']:.2f} | "
            f"Benchmark={record['who_searo_benchmark']} | "
            f"Gap={gap_pct:.1f}% | {rag.upper()}"
        )

    scorecard = pl.DataFrame(rows)

    green_count = (scorecard["rag_status"] == "green").sum()
    red_count = (scorecard["rag_status"] == "red").sum()
    logger.info(
        f"Scorecard summary: {green_count}/{len(scorecard)} KPIs green, "
        f"{red_count} red"
    )
    return scorecard


def render_html_scorecard(scorecard_df: pl.DataFrame, output_path: Path) -> None:
    """Render the scorecard as a styled, self-contained HTML file.

    Args:
        scorecard_df: Output of build_scorecard()
        output_path: Path to write the HTML file

    Side effect:
        Creates output_path and its parent directories
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    # Build table rows
    row_html_parts: list[str] = []
    for row in scorecard_df.to_dicts():
        rag = row["rag_status"]
        colour = RAG_COLOURS.get(rag, "#FFFFFF")
        label = html_lib.escape(str(row["kpi_label"]))
        sg_val = f"{row['singapore_2018']:.2f}" if row["singapore_2018"] is not None else "N/A"
        bm_val = f"{row['who_searo_benchmark']:.2f}" if row["who_searo_benchmark"] is not None else "—"
        gap = f"{row['gap_pct']:+.1f}%" if row["gap_pct"] is not None else "—"
        rag_label = html_lib.escape(rag.upper())

        row_html_parts.append(f"""
        <tr>
            <td>{label}</td>
            <td style="text-align:right">{sg_val}</td>
            <td style="text-align:right">{bm_val}</td>
            <td style="text-align:right">{gap}</td>
            <td style="text-align:center; background-color:{colour}; color:white; font-weight:bold">
                {rag_label}
            </td>
        </tr>""")

    rows_html = "\n".join(row_html_parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MOH-SG System Balance Scorecard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
    h1 {{ color: #1A5276; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 900px; }}
    th {{ background-color: #1A5276; color: white; padding: 10px; text-align: left; }}
    td {{ padding: 8px 10px; border-bottom: 1px solid #ddd; }}
    tr:hover {{ background-color: #f5f5f5; }}
    .footer {{ margin-top: 20px; font-size: 0.85em; color: #777; }}
  </style>
</head>
<body>
  <h1>[DRAFT] Healthcare System Balance Scorecard — Singapore</h1>
  <table>
    <thead>
      <tr>
        <th>KPI</th>
        <th>Singapore (2018)</th>
        <th>WHO SEARO Benchmark</th>
        <th>Gap %</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
  <div class="footer">
    Generated: {today} &nbsp;|&nbsp;
    Data window: 2009–2018 &nbsp;|&nbsp;
    Benchmark source: WHO Global Health Observatory 2020 (SEARO region) &nbsp;|&nbsp;
    RAG thresholds: Green ≥ 0%, Amber -15% to 0%, Red &lt; -15%
  </div>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    logger.info(f"HTML scorecard saved: {output_path}")
```

#### 3.2 `scripts/run_scorecard.py`

```python
"""PS-001 Story 06 — System Balance Scorecard.

Run: python problem-statements/ps-001-healthcare-system-baseline/scripts/run_scorecard.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.scorecard import (
    build_scorecard,
    render_html_scorecard,
)

PS_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PS_DIR / "results" / "tables"
EXPORTS_DIR = PS_DIR / "results" / "exports"
LOG_PATH = PS_DIR / "logs" / "etl" / "scorecard.log"


def main() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.add(str(LOG_PATH), level="INFO", rotation="10 MB")
    logger.info("=== PS-001 Story 06: System Balance Scorecard ===")

    benchmark_df = pl.read_csv(str(RESULTS_DIR / "benchmark_comparison.csv"))
    scorecard_df = build_scorecard(
        benchmark_df,
        rag_green_threshold=0.0,
        rag_amber_threshold=-15.0,
    )

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    scorecard_df.write_csv(str(RESULTS_DIR / "system_balance_scorecard.csv"))
    logger.info(f"Scorecard CSV: {RESULTS_DIR / 'system_balance_scorecard.csv'}")

    render_html_scorecard(scorecard_df, EXPORTS_DIR / "system_balance_scorecard.html")
    logger.info("=== Scorecard complete ===")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_scorecard.py

import sys
from pathlib import Path
import polars as pl
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_001_healthcare_system_baseline.src.scorecard import (
    _classify_rag,
    build_scorecard,
    render_html_scorecard,
)


def test_rag_green() -> None:
    assert _classify_rag(5.0) == "green"
    assert _classify_rag(0.0) == "green"


def test_rag_amber() -> None:
    assert _classify_rag(-5.0) == "amber"
    assert _classify_rag(-15.0) == "amber"


def test_rag_red() -> None:
    assert _classify_rag(-16.0) == "red"
    assert _classify_rag(-50.0) == "red"


def test_build_scorecard_columns() -> None:
    benchmark_df = pl.DataFrame({
        "metric": ["nurses_per_10k", "doctors_per_10k"],
        "singapore_2018": [18.0, 2.5],
        "who_searo_benchmark": [22.8, 2.3],
        "gap_pct": [-21.0, 8.7],
        "above_below_benchmark": ["below", "above"],
    })
    scorecard = build_scorecard(benchmark_df)
    assert set(scorecard.columns) >= {"kpi_label", "rag_status", "gap_pct"}
    assert scorecard["rag_status"][0] == "red"   # -21% < -15%
    assert scorecard["rag_status"][1] == "green"  # +8.7%


def test_html_render_creates_file(tmp_path: Path) -> None:
    scorecard = pl.DataFrame({
        "kpi_label": ["Nurses per 10k"],
        "metric_code": ["nurses_per_10k"],
        "singapore_2018": [18.0],
        "who_searo_benchmark": [22.8],
        "gap_pct": [-21.0],
        "rag_status": ["red"],
    })
    output = tmp_path / "scorecard.html"
    render_html_scorecard(scorecard, output)
    assert output.exists()
    content = output.read_text()
    assert "[DRAFT]" in content
    assert "WHO Global Health Observatory" in content
```

---

### 5. Implementation Steps

- [ ] Create `src/scorecard.py`
- [ ] Create `scripts/run_scorecard.py`
- [ ] Run `pytest tests/unit/test_scorecard.py -v` — all 5 tests must pass
- [ ] Run `python scripts/run_scorecard.py`
- [ ] Verify `system_balance_scorecard.csv` has expected columns and ≥ 3 rows
- [ ] Open `results/exports/system_balance_scorecard.html` in browser — confirm RAG colours render

---

### 6. Version Control

```bash
git checkout -b feat/ps-001-story-06-scorecard
git commit -m "feat(ps-001): add scorecard builder and HTML renderer"
git commit -m "feat(ps-001): add run_scorecard orchestration script"
git commit -m "test(ps-001): add scorecard unit tests"
```
