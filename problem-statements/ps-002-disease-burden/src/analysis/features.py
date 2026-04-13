"""
Feature Engineering Phase — PS-002 Disease Burden Temporal Trends Analysis
Engineers 13 temporal features on the mortality master dataset.
Output: ps-002-mortality-features-{STAMP}.parquet + feature_dictionary CSV.
"""
import polars as pl
import numpy as np
from pathlib import Path
from datetime import date

PS      = Path(__file__).resolve().parents[3]
PROC    = PS / "data/4_processed"
RESULTS = PS / "results/tables"
RESULTS.mkdir(parents=True, exist_ok=True)

STAMP = date.today().strftime("%Y%m%d")

FEATURE_DICT = [
    {"feature": "asmr_lag1",           "description": "ASMR lagged 1 year"},
    {"feature": "asmr_lag2",           "description": "ASMR lagged 2 years"},
    {"feature": "asmr_rolling3_mean",  "description": "3-year rolling mean of ASMR"},
    {"feature": "asmr_rolling5_mean",  "description": "5-year rolling mean of ASMR"},
    {"feature": "asmr_rolling3_std",   "description": "3-year rolling std of ASMR"},
    {"feature": "asmr_rolling5_std",   "description": "5-year rolling std of ASMR"},
    {"feature": "log_asmr",            "description": "Natural log of ASMR"},
    {"feature": "yoy_change_pct",      "description": "Year-over-year % change in ASMR"},
    {"feature": "cumulative_cagr",     "description": "Cumulative CAGR from 1990 baseline"},
    {"feature": "t_index",             "description": "Time index (0=1990, 1=1991, ...)"},
    {"feature": "detrended_residual",  "description": "ASMR minus log-linear trend (residual)"},
    {"feature": "asmr_normalized",     "description": "ASMR / 1990 baseline (relative index)"},
    {"feature": "disease_encoded",     "description": "Ordinal encoding of disease category"},
]

DISEASE_CODES = {"cancer": 0, "ischaemic_heart_disease": 1, "stroke": 2}


def _log_linear_trend(years: list, rates: list) -> list:
    """Fitted log-linear trend values."""
    x = np.array(years, dtype=float) - years[0]
    y = np.log(np.array(rates, dtype=float))
    a, b = np.polyfit(x, y, 1)
    return [round(float(np.exp(b + a * xi)), 3) for xi in x]


def engineer_features(master: pl.DataFrame) -> pl.DataFrame:
    """Build all 13 features per disease, joined back to master."""
    parts = []
    for d in master["disease"].unique().sort().to_list():
        sub = master.filter(pl.col("disease") == d).sort("year")
        years = sub["year"].to_list()
        rates = sub["asmr_per_100k"].to_list()
        n = len(rates)
        base = rates[0]
        trend = _log_linear_trend(years, rates)

        rows = []
        for i, (y, r) in enumerate(zip(years, rates)):
            rows.append({
                "year":               y,
                "disease":            d,
                "asmr_per_100k":      r,
                "asmr_lag1":          rates[i-1] if i >= 1 else None,
                "asmr_lag2":          rates[i-2] if i >= 2 else None,
                "asmr_rolling3_mean": round(float(np.mean(rates[max(0,i-2):i+1])), 3),
                "asmr_rolling5_mean": round(float(np.mean(rates[max(0,i-4):i+1])), 3),
                "asmr_rolling3_std":  round(float(np.std(rates[max(0,i-2):i+1])), 4) if i >= 2 else None,
                "asmr_rolling5_std":  round(float(np.std(rates[max(0,i-4):i+1])), 4) if i >= 4 else None,
                "log_asmr":           round(float(np.log(r)), 4),
                "yoy_change_pct":     round((r / rates[i-1] - 1) * 100, 3) if i >= 1 else None,
                "cumulative_cagr":    round(((r / base) ** (1 / i) - 1) * 100, 4) if i > 0 else 0.0,
                "t_index":            i,
                "detrended_residual": round(r - trend[i], 4),
                "asmr_normalized":    round(r / base, 4),
                "disease_encoded":    DISEASE_CODES.get(d, -1),
            })
        parts.append(pl.DataFrame(rows))

    result = pl.concat(parts).sort(["disease", "year"])
    result.write_parquet(PROC / f"ps-002-mortality-features-{STAMP}.parquet")
    pl.DataFrame(FEATURE_DICT).write_csv(RESULTS / f"feature_dictionary_{STAMP}.csv")
    return result


def run() -> None:
    master = pl.read_parquet(PROC / "mortality_master_clean.parquet")
    feat = engineer_features(master)
    print(f"  Feature matrix: {feat.shape} — {feat.columns}")
    print(f"Feature engineering complete → {PROC}")


if __name__ == "__main__":
    run()
