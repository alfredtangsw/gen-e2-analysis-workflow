# Time Series Forecasting Methods for Disease Burden Projection

**Domain**: Epidemiological Forecasting & Healthcare Capacity Planning  
**Purpose**: Reference guide for time series forecasting methods, model selection, validation, and uncertainty quantification for disease burden projections  
**Last Updated**: March 13, 2026

---

## Overview

Time series forecasting for disease burden enables proactive healthcare capacity planning by projecting future mortality and morbidity trends. This guide covers forecasting methodologies, implementation patterns, validation approaches, and best practices for epidemiological forecasting.

## Related Problem Statements

- [PS-002: Healthcare Demand Forecasting — Disease Burden & Demographic Projections](../objectives/problem_statements/ps-002-healthcare-demand-forecasting.md)
- [PS-003: Integrated Resource Planning & Budget Dashboard](../objectives/problem_statements/ps-003-integrated-resource-planning.md)

## Related Stakeholders

- **Healthcare Planning Division, MOH**: Infrastructure capacity planning based on projected demand
- **Manpower Planning Unit, MOH**: Clinical workforce sizing for disease-specific specialties
- **Finance & Budget Division, MOH**: Multi-year healthcare budget forecasting
- **Public Health Policy Unit, MOH**: Prevention program scaling decisions
- **Epidemiologists & Data Scientists**: Model development and validation

---

## Key Concepts and Terminology

### Forecast Horizon
**Definition**: The time period into the future for which predictions are made  
**Relevance**: Longer horizons have greater uncertainty; 5-year horizons typical for strategic planning  
**Example**: Forecasting 2025 mortality from 2019 data = 6-year horizon

### Prediction Interval
**Definition**: Range of values within which future observations are expected to fall with specified probability  
**Relevance**: Quantifies forecast uncertainty for risk-based planning  
**Example**: 95% PI [45, 65] means 95% confidence true value falls between 45-65 per 100k

### Stationarity
**Definition**: Time series properties (mean, variance, autocorrelation) remain constant over time  
**Relevance**: Many forecasting methods assume stationarity; non-stationary data requires transformation  
**Example**: Mortality rates with stable long-term average are stationary; exponentially growing rates are not

### Autocorrelation
**Definition**: Correlation of a time series with lagged versions of itself  
**Relevance**: Indicates temporal dependence; informs model selection (AR vs MA components)  
**Example**: High autocorrelation at lag 1 suggests AR(1) model appropriate

### Trend
**Definition**: Long-term increase or decrease in time series level  
**Relevance**: Must be modeled or removed for accurate forecasting  
**Example**: Declining cardiovascular disease mortality from 1990-2019

### Seasonality
**Definition**: Regular periodic fluctuations in time series  
**Relevance**: Less common in annual mortality data but critical for weekly/monthly disease surveillance  
**Example**: Influenza deaths peak in winter months

### Structural Break
**Definition**: Abrupt change in time series behavior (level shift, trend change)  
**Relevance**: COVID-19 represents structural break in mortality patterns; requires special handling  
**Example**: Cancer mortality trend shift in 2005 due to new screening programs

---

## Standard Forecasting Metrics

| Metric Name | Definition | Calculation Formula | Typical Range | Use Case | Interpretation |
|-------------|-----------|---------------------|---------------|----------|----------------|
| **RMSE** (Root Mean Squared Error) | Average magnitude of forecast errors | `√(Σ(y_actual - y_pred)² / n)` | 0 to ∞ (lower better) | Overall accuracy | Penalizes large errors heavily |
| **MAE** (Mean Absolute Error) | Average absolute forecast error | `Σ|y_actual - y_pred| / n` | 0 to ∞ (lower better) | Overall accuracy | Robust to outliers |
| **MAPE** (Mean Absolute % Error) | Average % deviation from actual | `Σ|y_actual - y_pred|/y_actual × 100 / n` | 0-100% (lower better) | Scale-independent comparison | <10% excellent, 10-20% good, >20% poor |
| **MASE** (Mean Absolute Scaled Error) | Error relative to naïve forecast | `MAE / MAE_naive` | <1 better than naïve | Benchmark comparison | <1 beats naïve, >1 worse than naïve |
| **Coverage** | % of actuals within prediction interval | `Count(y_actual ∈ PI) / n × 100` | Should match PI% (e.g., 95%) | Calibration check | 95% PI should contain 95% of actuals |
| **AIC** (Akaike Information Criterion) | Model fit penalized for complexity | `-2log(L) + 2k` | Lower is better | In-sample model selection | Balances accuracy and parsimony |
| **BIC** (Bayesian Information Criterion) | AIC variant with stronger penalty | `-2log(L) + k×log(n)` | Lower is better | In-sample model selection | Prefers simpler models than AIC |

---

## Forecasting Methodologies

### 1. Naïve Forecasting (Baseline)

**Description**: Use last observed value as forecast for all future periods

**Formula**:
```
ŷ_(t+h) = y_t  for all h > 0
```

**When to Use**: 
- Baseline benchmark for model comparison
- Random walk processes (stock prices, exchange rates)

**Polars Implementation**:
```python
import polars as pl

# Last observation carried forward
last_value = df.filter(pl.col('year') == df['year'].max())['ASMR'][0]

forecast_df = pl.DataFrame({
    'year': list(range(2020, 2026)),
    'forecast': [last_value] * 6,
    'method': ['Naive'] * 6
})
```

**Pros**: Simple, interpretable, no parameters  
**Cons**: Ignores trends and patterns; poor for trending data

---

### 2. Simple Exponential Smoothing (SES)

**Description**: Weighted average of past observations with exponentially decaying weights

**Formula**:
```
ŷ_(t+1) = α×y_t + (1-α)×ŷ_t
```
where α = smoothing parameter (0-1)

**When to Use**:
- Data with no trend or seasonality
- Short-term forecasting (1-2 periods ahead)

**Python Implementation** (statsmodels):
```python
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

model = SimpleExpSmoothing(mortality_rates)
fitted = model.fit(smoothing_level=0.6, optimized=True)
forecast = fitted.forecast(steps=5)
```

**Pros**: Simple, computationally efficient  
**Cons**: Cannot handle trends or seasonality

---

### 3. Holt's Linear Trend Method

**Description**: Extends SES to capture linear trends

**Formula**:
```
Level:    l_t = α×y_t + (1-α)×(l_(t-1) + b_(t-1))
Trend:    b_t = β×(l_t - l_(t-1)) + (1-β)×b_(t-1)
Forecast: ŷ_(t+h) = l_t + h×b_t
```

**When to Use**:
- Data with linear trend but no seasonality
- Medium-term forecasting (3-5 years)

**Python Implementation**:
```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

model = ExponentialSmoothing(
    mortality_rates,
    trend='add',  # or 'mul' for multiplicative
    seasonal=None
)
fitted = model.fit()
forecast = fitted.forecast(steps=5)
```

**Pros**: Captures trends, simple interpretation  
**Cons**: Assumes linear trend continues indefinitely

---

### 4. Holt-Winters Seasonal Method

**Description**: Extends Holt's method to include seasonality

**Formula**:
```
Level:    l_t = α×(y_t - s_(t-m)) + (1-α)×(l_(t-1) + b_(t-1))
Trend:    b_t = β×(l_t - l_(t-1)) + (1-β)×b_(t-1)
Seasonal: s_t = γ×(y_t - l_t) + (1-γ)×s_(t-m)
Forecast: ŷ_(t+h) = l_t + h×b_t + s_(t+h-m)
```

**When to Use**:
- Data with trend AND seasonality
- Monthly/quarterly disease surveillance data

**Python Implementation**:
```python
model = ExponentialSmoothing(
    monthly_cases,
    trend='add',
    seasonal='add',
    seasonal_periods=12  # monthly data
)
fitted = model.fit()
forecast = fitted.forecast(steps=24)  # 2 years ahead
```

**Pros**: Handles trend and seasonality  
**Cons**: Requires complete seasonal cycles; many parameters

---

### 5. ARIMA (AutoRegressive Integrated Moving Average)

**Description**: Combines autoregression, differencing, and moving average

**Model Notation**: ARIMA(p, d, q)
- **p**: Autoregressive order (lags of dependent variable)
- **d**: Differencing order (to achieve stationarity)
- **q**: Moving average order (lags of forecast errors)

**Formula**:
```
ARIMA(p,d,q): (1-ϕ₁B-...-ϕₚBᵖ)(1-B)ᵈy_t = (1+θ₁B+...+θₑBᵍ)ε_t
```

**When to Use**:
- Data with complex autocorrelation structures
- Non-seasonal annual data  
- Short- to medium-term forecasts

**Python Implementation**:
```python
from statsmodels.tsa.arima.model import ARIMA

# Fit ARIMA(1,1,1)
model = ARIMA(mortality_rates, order=(1, 1, 1))
fitted = model.fit()

# Forecast with confidence intervals
forecast_obj = fitted.get_forecast(steps=5)
forecast_mean = forecast_obj.predicted_mean
forecast_ci = forecast_obj.conf_int(alpha=0.05)  # 95% CI
```

**Model Selection**:
```python
import itertools
import pandas as pd

# Grid search for best (p,d,q)
p_range = range(0, 3)
d_range = range(0, 2)
q_range = range(0, 3)

best_aic = float('inf')
best_order = None

for p, d, q in itertools.product(p_range, d_range, q_range):
    try:
        model = ARIMA(mortality_rates, order=(p, d, q))
        fitted = model.fit()
        if fitted.aic < best_aic:
            best_aic = fitted.aic
            best_order = (p, d, q)
    except:
        continue

print(f"Best ARIMA order: {best_order}, AIC: {best_aic}")
```

**Pros**: Flexible, handles many patterns, well-established theory  
**Cons**: Requires stationarity, manual parameter tuning, complex

---

### 6. SARIMA (Seasonal ARIMA)

**Description**: ARIMA extended for seasonal patterns

**Model Notation**: SARIMA(p,d,q)(P,D,Q)_m
- **(p,d,q)**: Non-seasonal components
- **(P,D,Q)**: Seasonal components
- **m**: Seasonal period (e.g., 12 for monthly, 4 for quarterly)

**When to Use**:
- Monthly/quarterly disease surveillance with seasonality
- Influenza, dengue, respiratory disease forecasting

**Python Implementation**:
```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

# SARIMA(1,1,1)(1,1,1,12) for monthly data
model = SARIMAX(
    monthly_mortality,
    order=(1, 1, 1),
    seasonal_order=(1, 1, 1, 12),
    enforce_stationarity=False
)
fitted = model.fit(disp=False)
forecast = fitted.get_forecast(steps=24)
```

**Pros**: Captures seasonal patterns, flexible  
**Cons**: Computationally intensive, many parameters

---

### 7. Prophet (Facebook)

**Description**: Additive regression model with trend, seasonality, and holidays

**Model**:
```
y(t) = g(t) + s(t) + h(t) + ε_t
```
- **g(t)**: Piecewise linear or logistic growth trend
- **s(t)**: Seasonal component (Fourier series)
- **h(t)**: Holiday effects
- **ε**: Error term

**When to Use**:
- Data with multiple seasonalities
- Trend changepoints (automatic detection)
- Missing data, outliers
- Business time series (non-technical stakeholders)

**Python Implementation**:
```python
from prophet import Prophet
import pandas as pd

# Prepare data (Prophet requires 'ds' and 'y' columns)
df_prophet = pd.DataFrame({
    'ds': pd.to_datetime(df['year'], format='%Y'),
    'y': df['ASMR'].tolist()
})

# Initialize and fit model
model = Prophet(
    growth='linear',  # or 'logistic'
    yearly_seasonality=False,  # annual data has no seasonality
    weekly_seasonality=False,
    daily_seasonality=False,
    changepoint_prior_scale=0.05  # flexibility of trend changes
)

# Add custom seasonality if needed
# model.add_seasonality(name='monthly', period=30.5, fourier_order=5)

model.fit(df_prophet)

# Create future dataframe and forecast
future = model.make_future_dataframe(periods=5, freq='Y')
forecast = model.predict(future)

# Extract forecast components
forecast_df = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
```

**Visualization**:
```python
from prophet.plot import plot_plotly, plot_components_plotly

# Interactive forecast plot
fig1 = plot_plotly(model, forecast)
fig1.show()

# Decomposition (trend, seasonality)
fig2 = plot_components_plotly(model, forecast)
fig2.show()
```

**Pros**: Automatic changepoint detection, handles missing data, interpretable, fast  
**Cons**: Less flexible than ARIMA for complex patterns, can overfit

---

### 8. Ensemble Methods

**Description**: Combine multiple models to improve accuracy and robustness

**Simple Average**:
```python
forecast_ensemble = (forecast_arima + forecast_prophet + forecast_holt) / 3
```

**Weighted Average**:
```python
# Weights based on historical performance (e.g., inverse RMSE)
w1, w2, w3 = 0.4, 0.35, 0.25  # sum to 1
forecast_ensemble = w1*forecast_arima + w2*forecast_prophet + w3*forecast_holt
```

**Stacking** (Model Combination):
```python
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import LinearRegression

# Use forecasts from base models as features
X_train = np.column_stack([pred_arima_train, pred_prophet_train, pred_holt_train])
y_train = actual_values

meta_model = LinearRegression()
meta_model.fit(X_train, y_train)

# Final forecast
X_test = np.column_stack([pred_arima_test, pred_prophet_test, pred_holt_test])
forecast_final = meta_model.predict(X_test)
```

**Pros**: Reduces forecast variance, robust to model misspecification  
**Cons**: More complex, requires model diversity

---

## Model Validation & Selection

### Time Series Cross-Validation (Rolling Origin)

**Approach**: Incrementally expand training window, forecast h steps ahead

```python
import numpy as np

n_folds = 5
h = 5  # forecast horizon

rmse_scores = []

for i in range(n_folds):
    # Expanding window
    train_end = len(mortality_rates) - (n_folds - i) * h
    train = mortality_rates[:train_end]
    test = mortality_rates[train_end:train_end + h]
    
    # Fit model
    model = ARIMA(train, order=(1, 1, 1))
    fitted = model.fit()
    
    # Forecast and evaluate
    forecast = fitted.forecast(steps=len(test))
    rmse = np.sqrt(np.mean((test - forecast) ** 2))
    rmse_scores.append(rmse)

avg_rmse = np.mean(rmse_scores)
print(f"Cross-validated RMSE: {avg_rmse:.2f}")
```

### Backtesting (Out-of-Sample Validation)

```python
# Withhold last 5 years for testing
train_data = mortality_rates[:-5]
test_data = mortality_rates[-5:]

# Fit on training data
model = ARIMA(train_data, order=(1, 1, 1))
fitted = model.fit()

# Forecast test period
forecast = fitted.get_forecast(steps=5)
forecast_mean = forecast.predicted_mean
forecast_ci = forecast.conf_int()

# Evaluate
from sklearn.metrics import mean_absolute_percentage_error

mape = mean_absolute_percentage_error(test_data, forecast_mean)
print(f"Backtest MAPE: {mape:.2%}")

# Check prediction interval coverage
coverage = ((test_data >= forecast_ci.iloc[:, 0]) & 
            (test_data <= forecast_ci.iloc[:, 1])).mean()
print(f"95% PI Coverage: {coverage:.2%}")  # Should be ~95%
```

---

## Scenario Modeling

### Baseline Scenario (Trend Continuation)

```python
# Standard forecast assuming historical trends continue
model = ARIMA(mortality_rates, order=best_order)
fitted = model.fit()
baseline_forecast = fitted.get_forecast(steps=5).predicted_mean
```

### Optimistic Scenario (Enhanced Interventions)

```python
# Assume accelerated improvement (e.g., 20% faster decline)
intervention_effect = 1.20  # 20% enhancement

# Apply to trend component
optimistic_forecast = baseline_forecast * (1 - 0.05 * intervention_effect)
```

### Pessimistic Scenario (Trend Reversal)

```python
# Model worsening trends (e.g., aging population, lifestyle changes)
risk_factor = 1.10  # 10% increase

pessimistic_forecast = baseline_forecast * risk_factor
```

### Monte Carlo Simulation (Uncertainty Quantification)

```python
import numpy as np

n_simulations = 1000
forecast_horizon = 5

# Extract model residuals
residuals = fitted.resid
residual_std = residuals.std()

# Simulate future paths
simulations = np.zeros((n_simulations, forecast_horizon))

for i in range(n_simulations):
    # Add random shocks
    shocks = np.random.normal(0, residual_std, forecast_horizon)
    simulations[i, :] = baseline_forecast + np.cumsum(shocks)

# Calculate percentiles
p05 = np.percentile(simulations, 5, axis=0)  # 90% PI lower
p50 = np.percentile(simulations, 50, axis=0)  # median
p95 = np.percentile(simulations, 95, axis=0)  # 90% PI upper
```

---

## Domain-Specific Considerations

### Handling COVID-19 Structural Break

**Challenge**: 2020-2022 data contaminated by pandemic effects

**Approach 1**: Exclude outbreak years
```python
# Train only on pre-COVID data
pre_covid_data = mortality_rates[mortality_rates['year'] < 2020]
model = ARIMA(pre_covid_data['ASMR'], order=(1,1,1))
```

**Approach 2**: Add COVID dummy variable
```python
covid_indicator = (mortality_rates['year'] >= 2020) & (mortality_rates['year'] <= 2022)

from statsmodels.tsa.statespace.sarimax import SARIMAX
model = SARIMAX(
    mortality_rates['ASMR'],
    exog=covid_indicator.astype(int),
    order=(1, 1, 1)
)
```

**Approach 3**: Model pre-COVID then adjust
```python
# Forecast "counterfactual" (no COVID scenario)
# Then add COVID impact estimates from literature
covid_excess_mortality = 15  # % increase from studies

counterfactual_forecast = baseline_forecast
covid_adjusted_forecast = counterfactual_forecast * (1 + covid_excess_mortality/100)
```

### Long-Term vs Short-Term Forecasting

| Horizon | Approach | Key Considerations |
|---------|----------|-------------------|
| **1-2 years** | ARIMA, SES | High accuracy possible; use recent data heavily |
| **3-5 years** | ARIMA, Prophet, Holt | Moderate uncertainty; account for trends |
| **5-10 years** | Structural models, scenario analysis | High uncertainty; use multiple scenarios |
| **10+ years** | Cohort models, external projections | Extreme uncertainty; focus on scenarios not point forecasts |

### Incorporating External Factors

**Demographic Projections**:
```python
# Adjust for population aging
population_growth_rate = 0.01  # 1% annual growth
aged_population_share_increase = 0.02  # 2pp per year

demographic_adjustment = (1 + population_growth_rate) ** np.arange(1, 6)
forecast_adjusted = baseline_forecast * demographic_adjustment
```

**Risk Factor Trends** (e.g., obesity, smoking):
```python
# Incorporate obesity trend impact on diabetes mortality
obesity_rate_change = 0.05  # 5pp increase projected
diabetes_impact_factor = 1.15  # 15% increase per obesity prevalence increase

diabetes_forecast = baseline_forecast * (1 + obesity_rate_change * diabetes_impact_factor)
```

---

## Common Pitfalls and Best Practices

### Pitfalls to Avoid

1. **Overfitting to Historical Data**
   - **Problem**: Complex models fit noise, poor out-of-sample performance
   - **Solution**: Use cross-validation, penalize complexity (AIC/BIC), prefer simpler models

2. **Ignoring Structural Breaks**
   - **Problem**: COVID-19, policy changes invalidate historical patterns
   - **Solution**: Use dummy variables, train on relevant periods only, scenario modeling

3. **Extrapolating Far Beyond Data**
   - **Problem**: 30-year forecast from 5 years of data = extreme uncertainty
   - **Solution**: Forecast horizon ≤ 1/3 of data history; widen prediction intervals

4. **Misinterpreting Prediction Intervals**
   - **Problem**: Stakeholders treat PI as deterministic range
   - **Solution**: Extensive training, visualize uncertainty, scenario narratives

5. **Point Forecasts Only (No Uncertainty)**
   - **Problem**: Decision-makers unaware of forecast reliability
   - **Solution**: Always provide 80% and 95% PIs, probabilistic language

6. **Assuming Stationarity Without Testing**
   - **Problem**: ARIMA on non-stationary data = biased forecasts
   - **Solution**: ADF test, KPSS test; difference if needed

### Best Practices

1. **Start Simple, Add Complexity Only If Needed**
   - Baseline: Naïve → SES → Holt → ARIMA → Ensemble
   - Compare each model; stop when improvement plateaus

2. **Use Multiple Models (Ensemble)**
   - No single "best" model; ensemble reduces risk
   - Combine ARIMA (captures autocorrelation) + Prophet (captures changepoints)

3. **Validate Rigorously**
   - Out-of-sample testing mandatory
   - Check residual diagnostics (Ljung-Box test, ACF plots)
   - Evaluate prediction interval coverage

4. **Communicate Uncertainty Transparently**
   - Show prediction intervals in all visualizations
   - Use probabilistic language ("likely", "95% confidence")
   - Present multiple scenarios (baseline, optimistic, pessimistic)

5. **Update Forecasts Regularly**
   - Annual retraining with new data
   - Monitor forecast vs actual, trigger retraining if drift detected
   - Adaptive learning from forecast errors

6. **Document Assumptions and Limitations**
   - State forecast validity period
   - Identify factors not captured (e.g., future policy changes)
   - Clearly communicate COVID-19 impact uncertainty

---

## Practical Workflow Example

### End-to-End Forecasting Pipeline

```python
import polars as pl
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
import pandas as pd

# 1. Load and prepare data
df = pl.read_csv('data/1_raw/age-standardised-mortality-rate-for-cancer.csv')
ts_data = df.select(['year', 'ASMR']).sort('year')

# 2. Train-test split
train = ts_data.filter(pl.col('year') < 2015)
test = ts_data.filter(pl.col('year') >= 2015)

# 3. Fit ARIMA
arima_model = ARIMA(train['ASMR'], order=(1, 1, 1))
arima_fitted = arima_model.fit()

# 4. Fit Prophet
prophet_df = pd.DataFrame({
    'ds': pd.to_datetime(train['year'], format='%Y'),
    'y': train['ASMR'].to_list()
})
prophet_model = Prophet(yearly_seasonality=False)
prophet_model.fit(prophet_df)

# 5. Generate forecasts
arima_forecast = arima_fitted.get_forecast(steps=5)
arima_mean = arima_forecast.predicted_mean
arima_ci = arima_forecast.conf_int()

prophet_future = prophet_model.make_future_dataframe(periods=5, freq='Y')
prophet_forecast = prophet_model.predict(prophet_future)
prophet_mean = prophet_forecast['yhat'].tail(5)

# 6. Ensemble
ensemble_forecast = (arima_mean.values + prophet_mean.values) / 2

# 7. Evaluate on test set
from sklearn.metrics import mean_absolute_percentage_error
test_actual = test['ASMR'].to_numpy()

mape_arima = mean_absolute_percentage_error(test_actual, arima_mean)
mape_prophet = mean_absolute_percentage_error(test_actual, prophet_mean.values)
mape_ensemble = mean_absolute_percentage_error(test_actual, ensemble_forecast)

print(f"ARIMA MAPE: {mape_arima:.2%}")
print(f"Prophet MAPE: {mape_prophet:.2%}")
print(f"Ensemble MAPE: {mape_ensemble:.2%}")

# 8. Retrain on full data for production forecast
full_arima = ARIMA(ts_data['ASMR'], order=(1, 1, 1)).fit()
production_forecast = full_arima.get_forecast(steps=5)

# 9. Save results
forecast_df = pl.DataFrame({
    'year': list(range(2020, 2025)),
    'forecast': production_forecast.predicted_mean.values,
    'lower_95': production_forecast.conf_int().iloc[:, 0].values,
    'upper_95': production_forecast.conf_int().iloc[:, 1].values
})

forecast_df.write_csv('data/4_processed/cancer_mortality_forecast_2020-2025.csv')
```

---

## Authoritative Sources

### Academic & Research

1. **Hyndman, R.J., & Athanasopoulos, G. (2021).** *Forecasting: Principles and Practice (3rd ed.)*  
   URL: https://otexts.com/fpp3/  
   Content: Comprehensive forecasting textbook; industry-standard methods

2. **Box, G.E.P., et al. (2015).** *Time Series Analysis: Forecasting and Control (5th ed.)*  
   Content: ARIMA methodology bible

3. **Taylor, S.J., & Letham, B. (2018).** "Forecasting at Scale." *The American Statistician*, 72(1), 37-45.  
   Content: Prophet methodology and applications

### Public Health Applications

4. **IHME COVID-19 Forecasting Team (2020-2023).** COVID-19 Mortality Projections  
   URL: https://covid19.healthdata.org/  
   Content: Forecasting methods for disease burden under uncertainty

5. **CDC FluSight.** Influenza Forecasting  
   URL: https://www.cdc.gov/flu/weekly/flusight/  
   Content: Ensemble forecasting for seasonal disease surveillance

6. **Reich, N.G., et al. (2019).** "A collaborative multiyear, multimodel assessment of seasonal influenza forecasting in the United States." *PNAS*, 116(8), 3146-3154.  
   Content: Benchmark evaluation of epidemiological forecasting methods

### Software Documentation

7. **Statsmodels Time Series Documentation**  
   URL: https://www.statsmodels.org/stable/tsa.html  
   Content: ARIMA, SARIMA, state space models in Python

8. **Prophet Documentation**  
   URL: https://facebook.github.io/prophet/  
   Content: Installation, tutorials, best practices

---

## Metadata

**Created**: 2026-03-13  
**Last Updated**: 2026-03-13  
**Updated By**: GitHub Copilot  
**Update Reason**: Initial creation for PS-006 forecasting support  
**Version**: 1.0

## Notes

- This guide focuses on univariate time series forecasting suitable for annual mortality data
- For multivariate modeling (incorporating covariates), see Vector Autoregression (VAR) or SARIMAX with exogenous variables
- Prophet particularly useful for stakeholders without deep statistical training due to interpretable decomposition
- Always validate forecast assumptions with domain experts (epidemiologists, clinicians)
