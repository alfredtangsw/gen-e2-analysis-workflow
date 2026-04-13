# User Story: 1 — Extract and Profile Forecasting Source Data

**As a** healthcare demand forecasting analyst,  
**I want** to extract the mortality, hospital admissions, and LTC data along with Singapore's official demographic projections,  
**so that** I have verified, profiled inputs before building any forecasting models.

## 1. 🎯 Acceptance Criteria

- Mortality series extracted for all 3 target diseases: cancer, stroke, IHD — with year range, null counts, and record counts confirmed
- Hospital admissions by age group and sex loaded and row-counts confirmed (2006–2020)
- SingStat demographic projections downloaded and saved to `shared/data/2_external/population/` (principal, high-growth, low-growth scenarios)
- Data profile report generated to `logs/etl/ps002_data_profile.csv` — one row per table with: table name, rows, cols, year_min, year_max, null_count, data_source
- Admission rate denominator (per 1,000 or per 10,000 resident population) confirmed and recorded in profile report
- Any year gaps or discontinuities flagged explicitly in the profile report

## 2. 🔒 Technical Constraints

- All Kaggle data loaded via `kagglehub` cache — do not re-download if already present from PS-001
- SingStat projections: primary URL `https://www.singstat.gov.sg/find-data/search-by-theme/population/population-and-population-growth/latest-data`; if unavailable, use UN WPP 2022 as fallback (document which was used)
- Profile report written with Polars to CSV — one `pl.LazyFrame` scan per table fed into a single summary frame
- Use `loguru` for all extraction log messages; write to `logs/etl/ps002_extraction.log`
- Do NOT load PS-001 cleaned parquets in this story — load from raw source to confirm independence of data supply

## 3. 📚 Domain Knowledge References

- [Disease Burden Feature Engineering Guide](../../../../domain-knowledge/disease-burden-feature-engineering-guide.md) — mortality series notes, ICD code mapping context
- [Time-Series Forecasting Methods](../../../../domain-knowledge/time-series-forecasting-methods.md) — data length requirements per method (ARIMA min ~15 obs, Prophet min ~10)

## 4. 📦 Dependencies

- `kagglehub` — Kaggle data access
- `polars` — profiling
- `loguru` — logging
- `requests` or browser — SingStat population download
- PS-001 Story 01 must be complete (kagglehub cache populated)

## 5. ✅ Implementation Tasks

**Mortality Data**
- ⬜ Load cancer mortality CSV; confirm years 1990–2019; check for nulls; record profile row
- ⬜ Load stroke mortality CSV; confirm years and record count; profile
- ⬜ Load IHD mortality CSV; confirm years and record count; profile

**Admissions Data**
- ⬜ Load hospital admissions by age/sex; confirm 2006–2020 coverage; profile
- ⬜ Confirm denominator: check column headers/notes for "per 1,000" or "per 10,000" — record in profile

**LTC Data**
- ⬜ Load LTC admissions; record count and year range; note sparsity in profile

**SingStat Population Projections**
- ⬜ Attempt SingStat download; save to `shared/data/2_external/population/singstat_projections.csv`
- ⬜ If unavailable, use UN WPP 2022 CSV; document in profile report under `data_source` column

**Profile Report**
- ⬜ Assemble all profile rows into single frame; write to `logs/etl/ps002_data_profile.csv`
- ⬜ Log extraction completion with row count per table to `logs/etl/ps002_extraction.log`

## 6. Notes

- Mortality series extends back to 1990 for cancer and 1992 for stroke/IHD — 25–30 years of data — sufficient for ARIMA and Prophet. This long history is a strength.
- SingStat provides three projection scenarios (principal, high, low) needed for PS-002 Objective 3 (scenario-based admission volume projections). Ensure all three are captured.
- The denominator confirmation in admissions data is critical: using wrong base (1,000 vs 10,000) would produce a 10× error in estimated admission volumes.

---

## Implementation Plan

### 1. Feature Overview

Extract mortality (cancer, stroke, IHD), hospital admissions, and LTC data from the shared Kaggle cache. Download SingStat population projections (or UN WPP fallback). Profile all tables into a single CSV report. Primary user: **PS-002 forecasting analyst**.

---

### 2. Affected Files

```
[CREATE] problem-statements/ps-002-disease-burden/scripts/run_extraction_ps002.py
  - Loads data from shared Kaggle cache (no re-download)
  - Downloads SingStat projections to shared/data/2_external/population/
  - Writes data profile report to logs/etl/ps002_data_profile.csv

[CREATE] problem-statements/ps-002-disease-burden/src/forecasting_connector.py
  - load_mortality_table(disease) -> pl.DataFrame
  - load_admissions_table() -> pl.DataFrame
  - load_ltc_table() -> pl.DataFrame
  - download_singstat_projections(dest_dir) -> Path
  - profile_table(df, table_name, data_source) -> dict
```

---

### 3. Code Generation Specifications

#### 3.1 `src/forecasting_connector.py`

```python
"""PS-002 forecasting data connector.

Loads Kaggle-cached CSVs and external population projections for demand forecasting.
Do NOT import this from PS-001 — PS-002 must load raw to confirm data independence.
"""

import sys
from pathlib import Path

import polars as pl
import requests
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

RAW_DIR = PROJECT_ROOT / "shared" / "data" / "1_raw"
EXTERNAL_POP_DIR = PROJECT_ROOT / "shared" / "data" / "2_external" / "population"

MORTALITY_FILE_MAP: dict[str, str] = {
    "cancer": "principal-causes-of-death/cancer.csv",
    "stroke": "principal-causes-of-death/stroke.csv",
    "ihd": "principal-causes-of-death/ischaemic-heart-diseases.csv",
}
ADMISSIONS_FILE = "admissions-and-beds/hospital-admissions-by-sex-and-age-group.csv"
LTC_FILE = "admissions-and-beds/long-term-care-admissions.csv"

SINGSTAT_CSV_URL = (
    "https://tablebuilder.singstat.gov.sg/api/table/tabledata/M830001"
    "?seriesNoORrowNo=1"
)
UN_WPP_FALLBACK_URL = (
    "https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/"
    "WPP2022_TotalPopulationBySex.csv"
)


def load_mortality_table(disease: str) -> pl.DataFrame:
    """Load a mortality CSV for a target disease from the shared Kaggle cache.

    Args:
        disease: One of "cancer", "stroke", "ihd"

    Returns:
        Raw mortality DataFrame with at minimum a year and rate column

    Raises:
        KeyError: If disease is not in MORTALITY_FILE_MAP
        FileNotFoundError: If the CSV is not present in the shared cache
    """
    if disease not in MORTALITY_FILE_MAP:
        raise KeyError(f"Unknown disease '{disease}'. Valid: {list(MORTALITY_FILE_MAP)}")

    path = RAW_DIR / MORTALITY_FILE_MAP[disease]
    if not path.exists():
        raise FileNotFoundError(
            f"Mortality CSV not found: {path}. Run PS-001 extraction first."
        )
    df = pl.read_csv(str(path), infer_schema_length=500)
    logger.debug(f"Loaded {disease} mortality: {df.shape} from {path.name}")
    return df


def load_admissions_table() -> pl.DataFrame:
    """Load hospital admissions by sex and age group from shared cache."""
    path = RAW_DIR / ADMISSIONS_FILE
    if not path.exists():
        raise FileNotFoundError(f"Admissions CSV not found: {path}")
    df = pl.read_csv(str(path), infer_schema_length=500)
    logger.debug(f"Loaded admissions: {df.shape}")
    return df


def load_ltc_table() -> pl.DataFrame:
    """Load long-term care admissions from shared cache."""
    path = RAW_DIR / LTC_FILE
    if not path.exists():
        raise FileNotFoundError(f"LTC CSV not found: {path}")
    df = pl.read_csv(str(path), infer_schema_length=500)
    logger.debug(f"Loaded LTC: {df.shape}")
    return df


def download_singstat_projections(dest_dir: Path) -> Path:
    """Download SingStat population projections (principal/high/low scenarios).

    Falls back to UN WPP 2022 if the SingStat API is unavailable.

    Args:
        dest_dir: Directory to save the CSV file

    Returns:
        Path to the saved projections CSV
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / "singstat_projections.csv"

    if out_path.exists():
        logger.info(f"SingStat projections already exist at {out_path} — skipping download.")
        return out_path

    try:
        logger.info(f"Downloading SingStat projections from {SINGSTAT_CSV_URL}")
        resp = requests.get(SINGSTAT_CSV_URL, timeout=30)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)
        logger.info(f"SingStat projections saved: {out_path}")
        return out_path
    except requests.RequestException as exc:
        logger.warning(f"SingStat download failed ({exc}); falling back to UN WPP 2022.")

    un_path = dest_dir / "un_wpp2022_singapore.csv"
    logger.info(f"Downloading UN WPP 2022 Singapore data from {UN_WPP_FALLBACK_URL}")
    resp = requests.get(UN_WPP_FALLBACK_URL, timeout=60, stream=True)
    resp.raise_for_status()

    chunks: list[bytes] = []
    for chunk in resp.iter_content(chunk_size=65536):
        chunks.append(chunk)
    raw_csv = b"".join(chunks)

    # Filter to Singapore rows only (LocID 702) to reduce file size
    lines = raw_csv.decode("utf-8", errors="replace").splitlines()
    header = lines[0]
    sg_lines = [l for l in lines[1:] if ",702," in l or l.startswith("702,")]
    filtered = "\n".join([header] + sg_lines)
    un_path.write_text(filtered, encoding="utf-8")
    logger.info(f"UN WPP 2022 Singapore subset saved: {un_path} — data_source=UN_WPP_2022")
    return un_path


def profile_table(
    df: pl.DataFrame,
    table_name: str,
    data_source: str,
    year_col: str | None = None,
) -> dict:
    """Profile a single DataFrame for the extraction report.

    Args:
        df: DataFrame to profile
        table_name: Human-readable table identifier
        data_source: Source tag (e.g. "kaggle_cache", "singstat", "un_wpp")
        year_col: Optional year column name; if None, auto-detected

    Returns:
        Dict with: table_name, rows, cols, year_min, year_max, null_count, data_source
    """
    rows, cols = df.shape

    if year_col is None:
        candidates = [c for c in df.columns if "year" in c.lower()]
        year_col = candidates[0] if candidates else None

    year_min = year_max = None
    if year_col and year_col in df.columns:
        year_series = df[year_col].cast(pl.Utf8).str.extract(r"(\d{4})", 1)
        valid = year_series.drop_nulls().cast(pl.Int32)
        if len(valid) > 0:
            year_min = int(valid.min())
            year_max = int(valid.max())

    null_count = sum(df[c].null_count() for c in df.columns)

    return {
        "table_name": table_name,
        "rows": rows,
        "cols": cols,
        "year_min": year_min,
        "year_max": year_max,
        "null_count": null_count,
        "data_source": data_source,
    }
```

#### 3.2 `scripts/run_extraction_ps002.py`

```python
"""PS-002 Story 01 — Forecasting Data Extraction.

Run: python problem-statements/ps-002-disease-burden/scripts/run_extraction_ps002.py
"""

import sys
from pathlib import Path

import polars as pl
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from problem_statements.ps_002_disease_burden.src.forecasting_connector import (
    download_singstat_projections,
    load_admissions_table,
    load_ltc_table,
    load_mortality_table,
    profile_table,
)

PS_DIR = Path(__file__).resolve().parent.parent
EXTERNAL_POP_DIR = PROJECT_ROOT / "shared" / "data" / "2_external" / "population"
LOG_DIR = PS_DIR / "logs" / "etl"
LOG_PATH = LOG_DIR / "ps002_extraction.log"
PROFILE_PATH = LOG_DIR / "ps002_data_profile.csv"

DISEASES = ["cancer", "stroke", "ihd"]


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.add(str(LOG_PATH), level="INFO", rotation="10 MB")
    logger.info("=== PS-002 Story 01: Forecasting Data Extraction ===")

    profile_rows: list[dict] = []

    # Mortality tables
    for disease in DISEASES:
        df = load_mortality_table(disease)
        profile_rows.append(
            profile_table(df, f"mortality_{disease}", "kaggle_cache")
        )
        logger.info(f"Mortality [{disease}]: {df.shape[0]} rows, "
                    f"cols={df.columns}")

    # Admissions by age/sex
    adm = load_admissions_table()
    profile_rows.append(
        profile_table(adm, "hospital_admissions_by_age_sex", "kaggle_cache")
    )

    # Confirm rate denominator — look for "1,000" or "10,000" in column names/notes
    denom_hint = [c for c in adm.columns if "1000" in c or "10000" in c or "per" in c.lower()]
    logger.info(f"Admissions rate denominator candidates: {denom_hint}")
    logger.info(f"Admissions: {adm.shape[0]} rows; head columns={adm.columns[:6]}")

    # LTC
    ltc = load_ltc_table()
    profile_rows.append(profile_table(ltc, "ltc_admissions", "kaggle_cache"))
    logger.info(f"LTC: {ltc.shape[0]} rows (sparsity check: {ltc.shape[0] < 50})")

    # SingStat population projections
    proj_path = download_singstat_projections(EXTERNAL_POP_DIR)
    proj = pl.read_csv(str(proj_path), infer_schema_length=200)
    data_source = "un_wpp_2022" if "un_wpp" in str(proj_path) else "singstat"
    profile_rows.append(
        profile_table(proj, "population_projections", data_source)
    )
    logger.info(f"Population projections: {proj.shape}, source={data_source}")

    # Write profile report
    profile_df = pl.DataFrame(profile_rows)
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    profile_df.write_csv(str(PROFILE_PATH))
    logger.info(f"Profile report: {PROFILE_PATH} ({len(profile_rows)} tables)")

    # Year gap check  
    for row in profile_rows:
        y_min, y_max = row.get("year_min"), row.get("year_max")
        if y_min and y_max:
            expected = y_max - y_min + 1
            actual = row["rows"]
            if actual < expected * 0.7:
                logger.warning(
                    f"Possible year gaps in {row['table_name']}: "
                    f"expected ~{expected} rows, got {actual}"
                )

    logger.info("Extraction complete.")


if __name__ == "__main__":
    main()
```

---

### 4. Testing Strategy

```python
# tests/unit/test_forecasting_connector.py
import polars as pl
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_load_mortality_raises_on_unknown_disease(tmp_path):
    """Unknown disease names raise KeyError."""
    from problem_statements.ps_002_disease_burden.src.forecasting_connector import (
        load_mortality_table,
    )
    with pytest.raises(KeyError, match="Unknown disease"):
        load_mortality_table("tuberculosis")


def test_profile_table_returns_expected_keys():
    """profile_table dict has required top-level keys."""
    from problem_statements.ps_002_disease_burden.src.forecasting_connector import (
        profile_table,
    )
    df = pl.DataFrame({"year": [2010, 2011, 2012], "rate": [1.1, 1.2, None]})
    result = profile_table(df, "test_table", "test_source", year_col="year")
    for key in ("table_name", "rows", "cols", "year_min", "year_max", "null_count", "data_source"):
        assert key in result
    assert result["year_min"] == 2010
    assert result["year_max"] == 2012
    assert result["null_count"] == 1


def test_profile_table_no_year_col():
    """profile_table handles DataFrames with no year column gracefully."""
    from problem_statements.ps_002_disease_burden.src.forecasting_connector import (
        profile_table,
    )
    df = pl.DataFrame({"value": [1, 2, 3]})
    result = profile_table(df, "no_year", "test")
    assert result["year_min"] is None
    assert result["year_max"] is None
```

---

### 5. Implementation Steps

- [ ] Create `problem-statements/ps-002-disease-burden/src/__init__.py` (empty)
- [ ] Create `src/forecasting_connector.py`
- [ ] Create `scripts/run_extraction_ps002.py`
- [ ] Run: `python scripts/run_extraction_ps002.py`
- [ ] Verify `logs/etl/ps002_data_profile.csv` has 5 rows (cancer, stroke, IHD, admissions, LTC)
- [ ] Inspect admissions rate denominator candidates logged — record in config comment
- [ ] Verify SingStat or UN WPP file exists in `shared/data/2_external/population/`
- [ ] Run unit tests: `pytest tests/unit/test_forecasting_connector.py -v`

---

### 6. Version Control

```bash
git checkout -b feat/ps-002-story-01-forecasting-extraction
git commit -m "feat(ps-002): add forecasting_connector and run_extraction_ps002 script"
```
