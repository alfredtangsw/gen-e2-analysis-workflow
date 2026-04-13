"""
Forecasting Phase — PS-002 Disease Burden Temporal Trends Analysis
Models: Log-linear OLS (primary), Linear OLS, Holt Double ETS.
Best model selected by RMSE. Forecast horizon: 2020-2030.
Outputs: mortality_forecasts_2020_2030.parquet + scenario and priority CSVs.
"""
import polars as pl
import numpy as np
from pathlib import Path
from scipy import stats
from scipy.optimize import minimize_scalar

PS      = Path(__file__).resolve().parents[3]
PROC    = PS / "data/4_processed"
RESULTS = PS / "results/tables"
METRICS = PS / "results/metrics"
METRICS.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)

DISEASES = ["cancer", "stroke", "ischaemic_heart_disease"]
FCST_YEARS = list(range(2020, 2031))
HIST_YEARS = list(range(1990, 2020))


# ── Model functions ───────────────────────────────────────────────────────────

def _loglinear(x_hist: np.ndarray, y_hist: np.ndarray, x_pred: np.ndarray):
    slope, intercept, r, _, _ = stats.linregress(x_hist, np.log(y_hist))
    y_fit  = np.exp(intercept + slope * x_hist)
    rmse   = float(np.sqrt(np.mean((y_hist - y_fit) ** 2)))
    r2     = float(r ** 2)
    y_pred = np.exp(intercept + slope * x_pred)
    # 95% CI via prediction interval on log scale
    n      = len(x_hist)
    se     = np.std(np.log(y_hist) - (intercept + slope * x_hist), ddof=2)
    x_mean = np.mean(x_hist)
    margin = 1.96 * se * np.sqrt(1 + 1/n + (x_pred - x_mean)**2 / np.sum((x_hist - x_mean)**2))
    lower  = np.exp(np.log(y_pred) - margin)
    upper  = np.exp(np.log(y_pred) + margin)
    return y_pred, lower, upper, rmse, r2


def _linear(x_hist: np.ndarray, y_hist: np.ndarray, x_pred: np.ndarray):
    slope, intercept, _, _, _ = stats.linregress(x_hist, y_hist)
    y_fit  = intercept + slope * x_hist
    rmse   = float(np.sqrt(np.mean((y_hist - y_fit) ** 2)))
    y_pred = intercept + slope * x_pred
    return y_pred, rmse


def _holt_ets(y_hist: np.ndarray, n_steps: int):
    """Holt double exponential smoothing with optimised alpha/beta."""
    def _sse(params):
        a, b = params
        level, trend = y_hist[0], y_hist[1] - y_hist[0]
        sse = 0.0
        for obs in y_hist[1:]:
            level_p, trend_p = level, trend
            level = a * obs + (1 - a) * (level_p + trend_p)
            trend = b * (level - level_p) + (1 - b) * trend_p
            sse += (obs - (level_p + trend_p)) ** 2
        return sse

    from scipy.optimize import minimize
    res = minimize(_sse, [0.3, 0.1], bounds=[(0.01, 0.99), (0.01, 0.99)], method="L-BFGS-B")
    a, b = res.x
    level, trend = y_hist[0], y_hist[1] - y_hist[0]
    for obs in y_hist[1:]:
        l_p, t_p = level, trend
        level = a * obs + (1 - a) * (l_p + t_p)
        trend = b * (level - l_p) + (1 - b) * t_p
    preds = [level + (i + 1) * trend for i in range(n_steps)]
    # RMSE on in-sample
    level, trend = y_hist[0], y_hist[1] - y_hist[0]
    fits = []
    for obs in y_hist[1:]:
        fits.append(level + trend)
        l_p, t_p = level, trend
        level = a * obs + (1 - a) * (l_p + t_p)
        trend = b * (level - l_p) + (1 - b) * t_p
    rmse = float(np.sqrt(np.mean((y_hist[1:] - np.array(fits)) ** 2)))
    return np.array(preds), rmse


# ── Main forecast loop ────────────────────────────────────────────────────────

def build_forecasts(master: pl.DataFrame):
    x_hist = np.array(HIST_YEARS, dtype=float) - 1990
    x_pred = np.array(FCST_YEARS, dtype=float) - 1990
    all_rows, met_rows = [], []

    for d in DISEASES:
        rates = master.filter(pl.col("disease") == d).sort("year")["asmr_per_100k"].to_numpy()

        ll_pred, ll_lo, ll_hi, ll_rmse, ll_r2 = _loglinear(x_hist, rates, x_pred)
        lin_pred, lin_rmse = _linear(x_hist, rates, x_pred)
        holt_pred, holt_rmse = _holt_ets(rates, len(FCST_YEARS))

        rmse_map = {"loglinear": ll_rmse, "linear": lin_rmse, "holt": holt_rmse}
        best_model = min(rmse_map, key=rmse_map.get)
        best_pred  = {"loglinear": ll_pred, "linear": lin_pred, "holt": holt_pred}[best_model]

        for i, yr in enumerate(FCST_YEARS):
            all_rows.append({
                "disease":         d,
                "year":            yr,
                "forecast_best":   round(float(best_pred[i]), 2),
                "forecast_loglin": round(float(ll_pred[i]), 2),
                "forecast_linear": round(float(lin_pred[i]), 2),
                "forecast_holt":   round(float(holt_pred[i]), 2),
                "ci95_lower":      round(float(ll_lo[i]), 2),
                "ci95_upper":      round(float(ll_hi[i]), 2),
                "best_model":      best_model,
            })
        apc = (np.exp(np.polyfit(x_hist, np.log(rates), 1)[0]) - 1) * 100
        met_rows.append({
            "disease":        d,
            "apc_pct":        round(float(apc), 4),
            "loglinear_rmse": round(ll_rmse, 4),
            "loglinear_r2":   round(ll_r2, 4),
            "linear_rmse":    round(lin_rmse, 4),
            "linear_r2":      round(float(np.corrcoef(rates, lin_pred[:len(rates)] if False else np.polyval(np.polyfit(x_hist, rates, 1), x_hist))[0, 1] ** 2), 4),
            "holt_rmse":      round(holt_rmse, 4),
            "best_model":     best_model,
            "best_rmse":      round(rmse_map[best_model], 4),
        })

    fc_df  = pl.DataFrame(all_rows).sort(["disease", "year"])
    met_df = pl.DataFrame(met_rows)
    fc_df.write_parquet(PROC  / "mortality_forecasts_2020_2030.parquet")
    fc_df.write_csv(RESULTS   / "mortality_forecasts_2020_2030.csv")
    met_df.write_csv(METRICS  / "model_evaluation_metrics.csv")
    return fc_df, met_df


def build_scenario_analysis(master: pl.DataFrame, met_df: pl.DataFrame) -> pl.DataFrame:
    """Pessimistic / baseline / optimistic APC scenarios to 2030."""
    rows = []
    x_hist = np.array(HIST_YEARS, dtype=float) - 1990
    for d in DISEASES:
        rates  = master.filter(pl.col("disease") == d).sort("year")["asmr_per_100k"].to_numpy()
        apc    = float(met_df.filter(pl.col("disease") == d)["apc_pct"][0]) / 100
        base19 = rates[-1]
        for label, factor in [("Baseline (current trend)", 1.0),
                               ("Accelerated improvement (-20% APC)", 1.2),
                               ("Deterioration (+20% worse APC)", 0.8)]:
            apc_adj = apc * factor
            asmr30  = base19 * (1 + apc_adj) ** 11
            rows.append({
                "disease":              d,
                "scenario":             label,
                "asmr_2030":            round(asmr30, 1),
                "asmr_2019_baseline":   round(base19, 1),
            })
    df = pl.DataFrame(rows)
    df.write_csv(RESULTS / "scenario_analysis_2030.csv")
    return df


def build_priority_matrix(master: pl.DataFrame, met_df: pl.DataFrame) -> pl.DataFrame:
    """Rank diseases by remaining burden × rate of change."""
    rows = []
    for d in DISEASES:
        rates = master.filter(pl.col("disease") == d).sort("year")["asmr_per_100k"].to_numpy()
        apc   = float(met_df.filter(pl.col("disease") == d)["apc_pct"][0])
        burden_score = round(float(rates[-1]) / 10, 1)          # normalised residual burden
        urgency      = round(abs(apc) < 2.0, 0)                 # 1=slow progress (high urgency)
        rows.append({"disease": d, "asmr_2019": round(float(rates[-1]), 1),
                     "apc_pct": round(apc, 3),
                     "burden_score": burden_score,
                     "urgency_flag": int(urgency),
                     "priority_rank": 0})   # filled after sort
    df = (pl.DataFrame(rows)
          .sort(["urgency_flag", "burden_score"], descending=[True, True])
          .with_row_index("priority_rank", offset=1))
    df.write_csv(RESULTS / "disease_priority_matrix.csv")
    return df


def run() -> None:
    master = pl.read_parquet(PROC / "mortality_master_clean.parquet")
    fc_df, met_df = build_forecasts(master)
    print(f"  Forecasts: {fc_df.shape}")
    sc = build_scenario_analysis(master, met_df)
    print(f"  Scenarios: {sc.shape}")
    pm = build_priority_matrix(master, met_df)
    print(f"  Priority matrix: {pm}")
    print(f"Forecasting phase complete → {PROC}")


if __name__ == "__main__":
    run()
