"""PS-002 Phase 3b: Feature Engineering — lag features, rolling means, YoY, CAGR."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
import numpy as np
from loguru import logger

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
PS_DIR = WS / "problem-statements/ps-002-healthcare-demand-forecasting"
INTERIM = PS_DIR / "data/3_interim"
PROCESSED = PS_DIR / "data/4_processed"
RESULTS = PS_DIR / "results/tables"
LOGS = PS_DIR / "logs"
NB_DIR = PS_DIR / "notebooks"
HANDOFF_DIR = WS / "docs/agent-handoffs/feature-engineering/ps-002-healthcare-demand-forecasting"
HANDOFF_DIR.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"features_{TS}.log"), level="DEBUG")
logger.info("PS-002 feature engineering started")

# ── Load ─────────────────────────────────────────────────────────────────────
cancer = pl.read_parquet(str(INTERIM / "mortality_cancer_clean.parquet"))
ihd    = pl.read_parquet(str(INTERIM / "mortality_ihd_clean.parquet"))
stroke = pl.read_parquet(str(INTERIM / "mortality_stroke_clean.parquet"))
admissions = pl.read_parquet(str(INTERIM / "admissions_by_age_sex_clean.parquet"))
population = pl.read_parquet(str(INTERIM / "population_by_age_clean.parquet"))

mortality_all = pl.concat([cancer, ihd, stroke])
logger.info(f"Mortality combined: {mortality_all.shape}")

# ── Feature 1: ASMR time-series features per disease x sex ──────────────────
# lag_1, lag_2, lag_3, rolling_mean_3, rolling_mean_5, yoy_pct

def add_time_features(df: pl.DataFrame, value_col: str, group_cols: list[str]) -> pl.DataFrame:
    """Add lag, rolling mean, YoY features within each group, sorted by year."""
    results = []
    groups = df.select(group_cols).unique().rows()
    for grp_vals in groups:
        filt = df
        for col, val in zip(group_cols, grp_vals):
            filt = filt.filter(pl.col(col) == val)
        filt = filt.sort("year")
        vals = filt[value_col].to_list()
        n = len(vals)
        lag1  = [None] + vals[:-1]
        lag2  = [None, None] + vals[:-2]
        lag3  = [None, None, None] + vals[:-3]
        rm3   = [None, None] + [np.mean(vals[i-2:i+1]) for i in range(2, n)]
        rm5   = [None, None, None, None] + [np.mean(vals[i-4:i+1]) for i in range(4, n)]
        yoy   = [None] + [((vals[i] - vals[i-1]) / abs(vals[i-1]) * 100) if vals[i-1] != 0 else None
                          for i in range(1, n)]
        tmp = filt.with_columns([
            pl.Series(f"{value_col}_lag1", lag1, dtype=pl.Float64),
            pl.Series(f"{value_col}_lag2", lag2, dtype=pl.Float64),
            pl.Series(f"{value_col}_lag3", lag3, dtype=pl.Float64),
            pl.Series(f"{value_col}_roll3", rm3, dtype=pl.Float64),
            pl.Series(f"{value_col}_roll5", rm5, dtype=pl.Float64),
            pl.Series(f"{value_col}_yoy_pct", yoy, dtype=pl.Float64),
        ])
        results.append(tmp)
    return pl.concat(results).sort(group_cols + ["year"])

logger.info("Building ASMR features …")
mortality_feat = add_time_features(mortality_all.cast({"sex": pl.Utf8, "disease": pl.Utf8}),
                                   "asmr_per_100k", ["disease", "sex"])
logger.info(f"Mortality features: {mortality_feat.shape}")

MORT_FEAT_PATH = PROCESSED / "mortality_features.parquet"
mortality_feat.write_parquet(str(MORT_FEAT_PATH), compression="snappy")
logger.info(f"Saved → {MORT_FEAT_PATH}")

# ── Feature 2: CAGR 1990–2019 per disease x sex ─────────────────────────────
cagr_rows = []
for disease in sorted(mortality_all["disease"].cast(pl.Utf8).unique().to_list()):
    for sex in ["Male", "Female"]:
        subset = (mortality_all
                  .cast({"sex": pl.Utf8, "disease": pl.Utf8})
                  .filter((pl.col("disease") == disease) & (pl.col("sex") == sex))
                  .sort("year"))
        if subset.height < 2:
            continue
        v0 = float(subset["asmr_per_100k"][0])
        vn = float(subset["asmr_per_100k"][-1])
        years = int(subset["year"][-1]) - int(subset["year"][0])
        cagr = ((vn / v0) ** (1 / years) - 1) * 100 if years > 0 and v0 != 0 else None
        cagr_rows.append({"disease": disease, "sex": sex, "year_start": int(subset["year"][0]),
                          "year_end": int(subset["year"][-1]), "cagr_pct": round(cagr, 3) if cagr else None,
                          "pct_change_total": round((vn - v0) / abs(v0) * 100, 1) if v0 != 0 else None})

cagr_df = pl.DataFrame(cagr_rows)
CAGR_PATH = RESULTS / "ps002_cagr_by_disease_sex.csv"
cagr_df.write_csv(str(CAGR_PATH))
logger.info(f"CAGR → {CAGR_PATH}")
print(cagr_df)

# ── Feature 3: Admissions features per age_group x sex ──────────────────────
logger.info("Building admissions features …")
admissions_str = admissions.cast({"sex": pl.Utf8, "age_group": pl.Utf8})
admissions_feat = add_time_features(admissions_str, "admission_rate_per_1000", ["age_group", "sex"])
logger.info(f"Admissions features: {admissions_feat.shape}")

ADM_FEAT_PATH = PROCESSED / "admissions_features.parquet"
admissions_feat.write_parquet(str(ADM_FEAT_PATH), compression="snappy")
logger.info(f"Saved → {ADM_FEAT_PATH}")

# ── Feature 4: Population totals for denominator ─────────────────────────────
pop_annual = (population
              .cast({"age_group": pl.Utf8})
              .group_by("year")
              .agg(pl.col("population").sum().alias("total_population"))
              .sort("year"))
POP_ANNUAL_PATH = PROCESSED / "population_annual.parquet"
pop_annual.write_parquet(str(POP_ANNUAL_PATH), compression="snappy")
logger.info(f"Population annual → {POP_ANNUAL_PATH}")

# ── Notebook ──────────────────────────────────────────────────────────────────
import nbformat
NB_PATH = NB_DIR / "05_feature_engineering.ipynb"
cells_src = [
    f"# PS-002 Feature Engineering\nimport polars as pl\nfrom pathlib import Path\nPS_DIR = Path('{PS_DIR}')\nPROCESSED = PS_DIR / 'data/4_processed'\nprint('Paths set')",
    "mf = pl.read_parquet(str(PROCESSED / 'mortality_features.parquet'))\nprint('Mortality features:', mf.shape)\nprint(mf.columns)\nprint(mf.head(5))",
    "af = pl.read_parquet(str(PROCESSED / 'admissions_features.parquet'))\nprint('Admissions features:', af.shape)\nprint(af.head(5))",
    "cagr = pl.read_csv(str(PS_DIR / 'results/tables/ps002_cagr_by_disease_sex.csv'))\nprint(cagr)",
]
nb = nbformat.v4.new_notebook()
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}
nbformat.write(nb, str(NB_PATH))

# ── Handoff ───────────────────────────────────────────────────────────────────
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
handoff = {
    "agent": "feature-engineer",
    "problem_statement": "ps-002-healthcare-demand-forecasting",
    "status": "success",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "features_created": [
        "asmr_per_100k_lag1, lag2, lag3 — autoregressive features for ARIMA",
        "asmr_per_100k_roll3, roll5 — smoothed baseline for trend comparison",
        "asmr_per_100k_yoy_pct — velocity feature",
        "admission_rate_per_1000_lag1..3, roll3, roll5, yoy_pct — same set for admissions",
        "cagr_pct — per disease x sex (used as model diagnostic)",
    ],
    "train_test_split": {
        "train": "1990–2014 (25 years)", "test": "2015–2019 (5 years)",
        "forecast_horizon": "2020–2030 (exclude 2020 actual due to COVID)",
    },
    "outputs": [
        {"path": str(MORT_FEAT_PATH), "type": "parquet"},
        {"path": str(ADM_FEAT_PATH), "type": "parquet"},
        {"path": str(POP_ANNUAL_PATH), "type": "parquet"},
        {"path": str(CAGR_PATH), "type": "csv"},
        {"path": str(NB_PATH), "type": "notebook"},
    ],
    "next_agent": "model-forecasting",
}
hp = HANDOFF_DIR / f"features_to_forecasting_{TODAY}.json"
hp.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff → {hp}")

print(f"\n{'='*62}")
print(f"  Mortality feature rows   : {mortality_feat.height}")
print(f"  Admissions feature rows  : {admissions_feat.shape}")
print(f"  CAGR rows                : {cagr_df.height}")
print(f"  Population annual rows   : {pop_annual.height}")
print(f"{'='*62}")
