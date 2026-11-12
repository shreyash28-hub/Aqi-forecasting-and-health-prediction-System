# AQI forecasting: evaluation summary

Generated 2026-11-12T04:02:11+00:00. Models fitted on log1p(AQI), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 4 30-day test windows per city ending on 2025-11-30, 2025-12-30, 2026-01-29, 2026-02-28 (expanding training window). LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py).

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | ARIMA | 37.25 | 25% | 50% | SARIMA | Seasonal naive (weekly) (44.95) | yes |
| Bengaluru | ARIMA | 29.39 | 25% | 50% | XGBoost | Naive (last value) (32.05) | yes |
| Chennai | LSTM | 48.95 | 25% | 50% | Prophet | Seasonal naive (weekly) (57.53) | yes |
| Delhi | ARIMA | 79.45 | 25% | 75% | ARIMA | Seasonal naive (weekly) (82.28) | yes |
| Hyderabad | XGBoost | 11.15 | 25% | 25% | Prophet | Seasonal naive (weekly) (14.07) | yes |
| Lucknow | ARIMA | 52.05 | 25% | 75% | ARIMA | Seasonal naive (weekly) (60.65) | yes |

### Win rate (share of 4 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 25% | 0% | 25% | 0% | 25% | 0% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 25% | 0% | 25% |
| ARIMA | 25% | 25% | 0% | 25% | 0% | 25% |
| SARIMA | 25% | 25% | 25% | 0% | 25% | 25% |
| Holt-Winters | 0% | 0% | 0% | 0% | 0% | 0% |
| LSTM | 25% | 0% | 25% | 25% | 0% | 0% |
| XGBoost | 0% | 50% | 0% | 25% | 25% | 25% |
| Prophet | 0% | 0% | 25% | 0% | 25% | 0% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 50% | 50% | 50% | 75% | 25% | 75% |
| SARIMA | 25% | 50% | 25% | 25% | 25% | 50% |
| Holt-Winters | 0% | 50% | 0% | 0% | 25% | 25% |
| LSTM | 25% | 25% | 50% | 25% | 25% | 50% |
| XGBoost | 75% | 75% | 25% | 75% | 25% | 75% |
| Prophet | 0% | 25% | 50% | 25% | 25% | 50% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 45.00 | 32.05 | 69.57 | 92.11 | 14.24 | 73.76 |
| Seasonal naive (weekly) | 44.95 | 34.32 | 57.53 | 82.28 | 14.07 | 60.65 |
| ARIMA | 37.25 | 29.39 | 50.99 | 79.45 | 14.73 | 52.05 |
| SARIMA | 61.63 | 54.67 | 52.06 | 120.82 | 17.45 | 64.26 |
| Holt-Winters | 46.64 | 33.81 | 66.26 | 105.09 | 13.98 | 72.30 |
| LSTM | 46.39 | 37.16 | 48.95 | 139.80 | 17.18 | 58.83 |
| XGBoost | 39.80 | 30.13 | 50.44 | 81.06 | 11.15 | 57.87 |
| Prophet | 354967.81 | 236738.97 | 67.67 | 225.40 | 8955724303423.47 | 92.63 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 4.0 | 4.2 | 5.0 | 4.8 | 3.8 | 6.0 |
| Seasonal naive (weekly) | 4.5 | 4.8 | 5.2 | 4.2 | 4.0 | 4.5 |
| ARIMA | 2.8 | 3.0 | 3.8 | 2.2 | 4.8 | 2.2 |
| SARIMA | 5.2 | 4.5 | 5.0 | 4.8 | 5.2 | 4.2 |
| Holt-Winters | 5.0 | 4.0 | 5.0 | 6.0 | 3.8 | 5.8 |
| LSTM | 4.5 | 5.2 | 3.2 | 5.0 | 5.5 | 3.8 |
| XGBoost | 2.2 | 3.5 | 4.2 | 2.5 | 2.8 | 3.0 |
| Prophet | 7.8 | 6.8 | 4.5 | 6.5 | 6.2 | 6.5 |

### Test windows

| City | Window 0 | Window 1 | Window 2 | Window 3 |
|---|---|---|---|---|
| Ahmedabad | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Bengaluru | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Chennai | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Delhi | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Hyderabad | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Lucknow | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |

## Final 30-day hold-out only (window 0, kept for comparison)

| City | Window | Best model | RMSE | MAE | MAPE % | Best baseline (RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | 2026-01-30 to 2026-02-28 | SARIMA | 24.60 | 18.05 | 11.8 | Naive (last value) (32.10) | yes |
| Bengaluru | 2026-01-30 to 2026-02-28 | ARIMA | 16.68 | 13.87 | 15.3 | Naive (last value) (26.87) | yes |
| Chennai | 2026-01-30 to 2026-02-28 | Prophet | 36.96 | 30.16 | 34.1 | Naive (last value) (43.19) | yes |
| Delhi | 2026-01-30 to 2026-02-28 | ARIMA | 60.07 | 48.78 | 20.7 | Naive (last value) (65.23) | yes |
| Hyderabad | 2026-01-30 to 2026-02-28 | Prophet | 8.56 | 6.60 | 6.8 | Seasonal naive (weekly) (8.81) | yes |
| Lucknow | 2026-01-30 to 2026-02-28 | ARIMA | 16.99 | 13.01 | 14.5 | Naive (last value) (40.60) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 32.10 | 26.87 | 43.19 | 65.23 | 12.78 | 40.60 |
| Seasonal naive (weekly) | 36.82 | 28.96 | 46.41 | 76.17 | 8.81 | 45.95 |
| ARIMA | 33.99 | 16.68 | 38.68 | 60.07 | 12.92 | 16.99 |
| SARIMA | 24.60 | 16.72 | 47.36 | 76.10 | 14.48 | 18.30 |
| Holt-Winters | 37.25 | 35.88 | 43.26 | 82.31 | 11.13 | 35.92 |
| LSTM | 32.72 | 18.40 | 45.04 | 67.95 | 12.37 | 34.80 |
| XGBoost | 26.55 | 18.78 | 49.04 | 64.24 | 10.00 | 36.78 |
| Prophet | 58.25 | 18.43 | 36.96 | 62.98 | 8.56 | 39.22 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 1.22 |
| Bengaluru | 0.70 |
| Chennai | 2.33 |
| Delhi | 5.94 |
| Hyderabad | 1.82 |
| Lucknow | 3.83 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-20 to 2026-10-29 | 617 | 45 | 0.4460 | 0.044 | 1 | 0.85 | nan (-) | 0.06 / nan |
| Bengaluru | 2025-02-20 to 2026-10-29 | 617 | 46 | 0.0231 | 0.038 | 0 | 0.74 | nan (-) | 0.03 / nan |
| Chennai | 2025-02-20 to 2026-10-29 | 617 | 45 | 0.0265 | 0.100 | 0 | 0.61 | nan (-) | 0.12 / nan |
| Hyderabad | 2025-02-20 to 2026-10-29 | 617 | 45 | 0.1367 | 0.010 | 1 | 0.81 | nan (-) | 0.10 / nan |
| Lucknow | 2025-02-20 to 2026-10-29 | 617 | 44 | 0.2135 | 0.080 | 1 | 0.70 | nan (-) | 0.00 / nan |
| Ahmedabad | 2025-02-20 to 2026-10-29 | 617 | 44 | 0.0155 | 0.075 | 0 | 0.64 | nan (-) | 0.03 / nan |

## Issues log

- **Ahmedabad / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Bengaluru / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Chennai / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Delhi / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Hyderabad / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Lucknow / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- Ahmedabad: never beat the baseline in any window: Holt-Winters, Prophet
- Chennai: never beat the baseline in any window: Holt-Winters
- Delhi: never beat the baseline in any window: Holt-Winters
