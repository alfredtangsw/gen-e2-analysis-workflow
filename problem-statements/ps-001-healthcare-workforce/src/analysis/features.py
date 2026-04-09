"""PS-001 Phase 3b: Feature engineering — lags, rolling stats, log transforms, external demand features."""

import json
from pathlib import Path

import numpy as np
import polars as pl

BASE = Path(__file__).resolve().parents[5]
PS_DIR  = BASE / "problem-statements/ps-001-healthcare-workforce"
PROC    = PS_DIR / "data/4_processed"
INTERIM = PS_DIR / "data/3_interim"
RESULTS = PS_DIR / "results/tables"
HANDOFF_DIR = BASE / "docs/agent-handoffs/feature-engineering/ps-001-healthcare-workforce"

FEATURE_DICT = [
    {"feature": "year",                   "type": "temporal",    "description": "Calendar year"},
    {"feature": "profession",             "type": "categorical", "description": "Healthcare profession category"},
    {"feature": "headcount",              "type": "target",      "description": "Total workforce headcount"},
    {"feature": "total_population",       "type": "external",    "description": "Singapore total population"},
    {"feature": "density_per_10k_pop",    "type": "derived",     "description": "Workers per 10,000 population"},
    {"feature": "yoy_growth_pct",         "type": "growth",      "description": "Year-over-year headcount growth %"},
    {"feature": "lag1_headcount",         "type": "lag",         "description": "Headcount lagged 1 year"},
    {"feature": "lag2_headcount",         "type": "lag",         "description": "Headcount lagged 2 years"},
    {"feature": "roll3_mean",             "type": "rolling",     "description": "3-year rolling mean headcount"},
    {"feature": "roll3_std",              "type": "rolling",     "description": "3-year rolling std headcount"},
    {"feature": "cagr_cumulative_pct",    "type": "growth",      "description": "Cumulative CAGR from baseline %"},
    {"feature": "t_index",                "type": "temporal",    "description": "Years since first observation (0-based)"},
    {"feature": "log_headcount",          "type": "derived",     "description": "Natural log of headcount for log-linear models"},
    {"feature": "elderly_admission_rate", "type": "external",    "description": "Mean admission rate/1000 for 65+ (demand proxy)"},
    {"feature": "total_facilities",       "type": "external",    "description": "Total healthcare facility count"},
]


def _make_dirs() -> None:
    for d in [INTERIM, RESULTS, HANDOFF_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def engineer_features(master: pl.DataFrame, hosp_adm: pl.DataFrame, fac: pl.DataFrame) -> pl.DataFrame:
    professions = master["profession"].unique().sort().to_list()
    frames = []

    aging_demand = (
        hosp_adm.filter(pl.col("age_group").is_in(["65-74", "75-84", "85+"]))
        .group_by("year")
        .agg(pl.col("admission_rate_per_1000").mean().alias("elderly_admission_rate"))
        .sort("year")
    )
    facility_count = (
        fac.group_by("year")
        .agg(pl.col("facility_count").sum().alias("total_facilities"))
        .sort("year")
    )

    for prof in professions:
        sub = master.filter(pl.col("profession") == prof).sort("year")
        counts = sub["headcount"].to_numpy().astype(float)
        n = len(counts)

        yoy    = np.concatenate([[np.nan], np.diff(counts) / counts[:-1] * 100])
        lag1   = np.concatenate([[np.nan], counts[:-1]])
        lag2   = np.concatenate([[np.nan, np.nan], counts[:-2]])
        roll3  = np.array([np.mean(counts[max(0, i - 2):i + 1]) for i in range(n)])
        roll3s = np.array([np.std(counts[max(0, i - 2):i + 1]) for i in range(n)])
        cagr   = np.array([(counts[i] / counts[0]) ** (1 / max(1, i)) - 1 if i > 0 else 0.0 for i in range(n)])

        sub_feat = sub.with_columns([
            pl.Series("yoy_growth_pct",     yoy),
            pl.Series("lag1_headcount",      lag1),
            pl.Series("lag2_headcount",      lag2),
            pl.Series("roll3_mean",          roll3),
            pl.Series("roll3_std",           roll3s),
            pl.Series("cagr_cumulative_pct", cagr * 100),
            pl.Series("t_index",             np.arange(n, dtype=float)),
            pl.Series("log_headcount",       np.log(counts)),
        ])
        frames.append(sub_feat)

    features = pl.concat(frames).sort(["profession", "year"])
    features = features.join(aging_demand, on="year", how="left")
    features = features.join(facility_count, on="year", how="left")
    return features


def run() -> None:
    _make_dirs()

    master   = pl.read_parquet(PROC / "workforce_master_clean.parquet")
    hosp_adm = pl.read_parquet(PROC / "hospital_admissions_clean.parquet")
    fac      = pl.read_parquet(PROC / "facilities_clean.parquet")

    features = engineer_features(master, hosp_adm, fac)

    features.write_parquet(PROC / "ps-001-workforce-features-20260409.parquet")
    features.write_csv(INTERIM / "ps-001-workforce-features-20260409.csv")

    feat_dict_df = pl.DataFrame(FEATURE_DICT)
    feat_dict_df.write_csv(RESULTS / "feature_dictionary_20260409.csv")

    print(f"Feature dataset: {features.shape}")
    print(f"Columns: {features.columns}")

    handoff = {
        "agent": "feature-engineer",
        "problem_statement": "ps-001-healthcare-workforce-sustainability",
        "timestamp": "2026-04-09",
        "status": "completed",
        "feature_dataset": str(PROC / "ps-001-workforce-features-20260409.parquet"),
        "feature_count": len(FEATURE_DICT),
        "feature_categories": ["temporal", "lag", "rolling", "growth", "derived", "external"],
        "files_created": [
            str(PROC / "ps-001-workforce-features-20260409.parquet"),
            str(INTERIM / "ps-001-workforce-features-20260409.csv"),
            str(RESULTS / "feature_dictionary_20260409.csv"),
        ],
        "next_agent": "model-forecasting",
    }
    with open(HANDOFF_DIR / "features_to_forecasting_20260409.json", "w") as f:
        json.dump(handoff, f, indent=2)

    print("Feature engineering complete.")


if __name__ == "__main__":
    run()
