"""PS-001 Phase 4: Log-linear, linear OLS, and Holt ETS forecasting with 95% CI and demand-gap analysis."""

import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

BASE = Path(__file__).resolve().parents[5]
PS_DIR  = BASE / "problem-statements/ps-001-healthcare-workforce"
PROC    = PS_DIR / "data/4_processed"
RESULTS = PS_DIR / "results"
HANDOFF_DIR = BASE / "docs/agent-handoffs/model-forecasting/ps-001-healthcare-workforce"

FORECAST_YEARS = list(range(2020, 2031))
DEMAND_GROWTH_FACTOR = 1.18  # ~18% demand uplift from population aging 2019-2030


def _make_dirs() -> None:
    for d in [PROC, RESULTS / "tables", RESULTS / "metrics", HANDOFF_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def _holt_linear(series: np.ndarray, n_forecast: int, alpha: float = 0.3, beta: float = 0.2) -> tuple[np.ndarray, np.ndarray]:
    s = series.astype(float)
    L, T = s[0], s[1] - s[0]
    fitted = [L]
    for i in range(1, len(s)):
        L_prev, T_prev = L, T
        L = alpha * s[i] + (1 - alpha) * (L_prev + T_prev)
        T = beta * (L - L_prev) + (1 - beta) * T_prev
        fitted.append(L)
    forecasts = [L + h * T for h in range(1, n_forecast + 1)]
    return np.array(fitted), np.array(forecasts)


def _linear_ols(years: np.ndarray, counts: np.ndarray, forecast_years: list[int]) -> tuple[np.ndarray, float, float, float, float]:
    slope, intercept, r, _, _ = stats.linregress(years, counts)
    fitted    = slope * years + intercept
    forecast  = slope * np.array(forecast_years) + intercept
    rmse      = np.sqrt(np.mean((counts - fitted) ** 2))
    return forecast, slope, intercept, rmse, r ** 2


def _log_linear(years: np.ndarray, counts: np.ndarray, forecast_years: list[int]) -> tuple[np.ndarray, float, float, float, float]:
    log_counts = np.log(counts)
    slope, intercept, r, _, _ = stats.linregress(years, log_counts)
    fitted    = np.exp(slope * years + intercept)
    forecast  = np.exp(slope * np.array(forecast_years) + intercept)
    rmse      = np.sqrt(np.mean((counts - fitted) ** 2))
    return forecast, slope * 100, np.exp(intercept), rmse, r ** 2


def build_forecasts(features: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    professions = features["profession"].unique().sort().to_list()
    forecast_rows, metrics_rows = [], []

    for prof in professions:
        sub = features.filter(pl.col("profession") == prof).sort("year")
        years_arr  = sub["year"].to_numpy()
        counts_arr = sub["headcount"].to_numpy().astype(float)

        lin_fc, _, _, lin_rmse, lin_r2     = _linear_ols(years_arr, counts_arr, FORECAST_YEARS)
        log_fc, _, _, log_rmse, log_r2     = _log_linear(years_arr, counts_arr, FORECAST_YEARS)
        _, holt_fc = _holt_linear(counts_arr, len(FORECAST_YEARS))
        holt_rmse  = np.sqrt(np.mean((counts_arr - _holt_linear(counts_arr, 0)[0]) ** 2))

        best_name, best_rmse = min(
            [("linear", lin_rmse), ("log_linear", log_rmse), ("holt_ets", holt_rmse)],
            key=lambda x: x[1],
        )
        best_fc = {"linear": lin_fc, "log_linear": log_fc, "holt_ets": holt_fc}[best_name]
        recent_std = np.std(counts_arr[-4:]) * 1.5

        for i, yr in enumerate(FORECAST_YEARS):
            width = recent_std * np.sqrt(i + 1)
            forecast_rows.append({
                "profession":      prof,
                "year":            yr,
                "forecast_linear": round(lin_fc[i]),
                "forecast_loglin": round(log_fc[i]),
                "forecast_holt":   round(holt_fc[i]),
                "forecast_best":   round(best_fc[i]),
                "best_model":      best_name,
                "ci95_lower":      round(max(0, best_fc[i] - 1.96 * width)),
                "ci95_upper":      round(best_fc[i] + 1.96 * width),
            })

        metrics_rows.append({
            "profession":     prof,
            "linear_rmse":    round(lin_rmse, 1),
            "linear_r2":      round(lin_r2, 4),
            "loglinear_rmse": round(log_rmse, 1),
            "loglinear_r2":   round(log_r2, 4),
            "holt_rmse":      round(holt_rmse, 1),
            "best_model":     best_name,
            "best_rmse":      round(best_rmse, 1),
        })

        print(f"  {prof}: best={best_name} RMSE={best_rmse:.0f}")

    return pl.DataFrame(forecast_rows), pl.DataFrame(metrics_rows)


def build_gap_analysis(forecast_df: pl.DataFrame, features: pl.DataFrame, pop_2019: int) -> pl.DataFrame:
    pop_2030 = int(pop_2019 * (1.008 ** 11))
    professions = forecast_df["profession"].unique().sort().to_list()
    rows = []
    for prof in professions:
        supply_2030 = forecast_df.filter(
            (pl.col("profession") == prof) & (pl.col("year") == 2030)
        )["forecast_best"][0]
        density_2019 = features.filter(
            (pl.col("profession") == prof) & (pl.col("year") == 2019)
        )["density_per_10k_pop"][0]
        demand_2030 = int(density_2019 / 10000 * pop_2030 * DEMAND_GROWTH_FACTOR)
        gap = supply_2030 - demand_2030
        rows.append({
            "profession":   prof,
            "supply_2030":  supply_2030,
            "demand_2030":  demand_2030,
            "gap_2030":     gap,
            "gap_severity": "CRITICAL" if gap < -3000 else "HIGH" if gap < -1000 else "MODERATE" if gap < 0 else "SURPLUS",
        })
    return pl.DataFrame(rows).sort("gap_2030")


def build_scenario_analysis(forecast_df: pl.DataFrame, gap_df: pl.DataFrame) -> pl.DataFrame:
    doc_2030   = forecast_df.filter((pl.col("profession") == "doctors") & (pl.col("year") == 2030))["forecast_best"][0]
    doc_demand = gap_df.filter(pl.col("profession") == "doctors")["demand_2030"][0]
    scenarios = {
        "Baseline (current trajectory)":          doc_2030,
        "Accelerated training (+10% intakes)":     int(doc_2030 * 1.08),
        "International recruitment (+5%/yr)":      int(doc_2030 * 1.12),
        "Combined intervention":                   int(doc_2030 * 1.18),
    }
    return pl.DataFrame([
        {"scenario": k, "doctors_2030": v, "demand_2030": doc_demand, "gap": v - doc_demand}
        for k, v in scenarios.items()
    ])


def run() -> None:
    _make_dirs()

    features = pl.read_parquet(PROC / "ps-001-workforce-features-20260409.parquet")
    pop_tot  = pl.read_parquet(PROC / "population_totals_clean.parquet")
    pop_2019 = pop_tot.filter(pl.col("year") == 2019)["total_population"][0]

    print("Building forecasts...")
    forecast_df, metrics_df = build_forecasts(features)

    print("Building demand-gap analysis...")
    gap_df = build_gap_analysis(forecast_df, features, pop_2019)

    print("Building scenario analysis...")
    scenario_df = build_scenario_analysis(forecast_df, gap_df)

    forecast_df.write_parquet(PROC / "workforce_forecasts_2020_2030.parquet")
    forecast_df.write_csv(RESULTS / "tables/workforce_forecasts_2020_2030.csv")
    metrics_df.write_csv(RESULTS / "metrics/model_evaluation_metrics.csv")
    gap_df.write_csv(RESULTS / "tables/demand_gap_analysis_2030.csv")
    scenario_df.write_csv(RESULTS / "tables/scenario_analysis_doctors.csv")

    print("\nForecast 2030:")
    print(forecast_df.filter(pl.col("year") == 2030).select(["profession", "forecast_best", "ci95_lower", "ci95_upper"]))
    print("\nDemand gap:")
    print(gap_df)

    handoff = {
        "agent": "model-forecasting",
        "problem_statement": "ps-001-healthcare-workforce-sustainability",
        "timestamp": "2026-04-09",
        "status": "completed",
        "models_built": ["Linear OLS", "Log-linear", "Holt Double ETS"],
        "best_models": {r["profession"]: r["best_model"] for r in metrics_df.to_dicts()},
        "forecast_file": str(PROC / "workforce_forecasts_2020_2030.parquet"),
        "files_created": [
            str(PROC / "workforce_forecasts_2020_2030.parquet"),
            str(RESULTS / "tables/workforce_forecasts_2020_2030.csv"),
            str(RESULTS / "metrics/model_evaluation_metrics.csv"),
            str(RESULTS / "tables/demand_gap_analysis_2030.csv"),
            str(RESULTS / "tables/scenario_analysis_doctors.csv"),
        ],
        "next_agent": "dashboard-visualization",
    }
    with open(HANDOFF_DIR / "forecasting_to_dashboard_20260409.json", "w") as f:
        json.dump(handoff, f, indent=2)

    print("Forecasting complete.")


if __name__ == "__main__":
    run()
