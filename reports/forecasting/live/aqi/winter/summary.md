# AQI forecasting: evaluation summary

Generated 2026-11-12T03:55:32+00:00. Models fitted on log1p(AQI), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 4 30-day test windows per city ending on 2025-11-30, 2025-12-30, 2026-01-29, 2026-02-28 (expanding training window). LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | XGBoost | 35.70 | 50% | 50% | XGBoost | Seasonal naive (weekly) (44.95) | yes |
| Bengaluru | ARIMA | 30.09 | 50% | 75% | ARIMA | Naive (last value) (32.05) | yes |
| Chennai | XGBoost | 46.90 | 0% | 50% | Prophet | Seasonal naive (weekly) (57.53) | yes |
| Delhi | Prophet | 70.35 | 25% | 75% | LSTM | Seasonal naive (weekly) (82.28) | yes |
| Hyderabad | SARIMA | 8.91 | 50% | 50% | SARIMA | Seasonal naive (weekly) (14.07) | yes |
| Lucknow | Prophet | 38.60 | 100% | 100% | Prophet | Seasonal naive (weekly) (60.65) | yes |

### Win rate (share of 4 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 25% | 0% | 25% | 0% | 0% | 0% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 25% | 0% | 0% |
| ARIMA | 0% | 50% | 0% | 0% | 0% | 0% |
| SARIMA | 0% | 25% | 0% | 25% | 50% | 0% |
| Holt-Winters | 0% | 0% | 0% | 0% | 0% | 0% |
| LSTM | 0% | 0% | 25% | 25% | 0% | 0% |
| XGBoost | 50% | 0% | 0% | 0% | 25% | 0% |
| Prophet | 25% | 25% | 50% | 25% | 25% | 100% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 25% | 75% | 75% | 50% | 50% | 100% |
| SARIMA | 25% | 75% | 75% | 50% | 50% | 100% |
| Holt-Winters | 0% | 50% | 25% | 25% | 25% | 0% |
| LSTM | 25% | 25% | 50% | 50% | 50% | 75% |
| XGBoost | 50% | 25% | 50% | 75% | 50% | 75% |
| Prophet | 50% | 50% | 50% | 75% | 25% | 100% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 45.00 | 32.05 | 69.57 | 92.11 | 14.24 | 73.76 |
| Seasonal naive (weekly) | 44.95 | 34.32 | 57.53 | 82.28 | 14.07 | 60.65 |
| ARIMA | 39.52 | 30.09 | 52.80 | 88.49 | 10.02 | 43.70 |
| SARIMA | 39.51 | 30.40 | 52.02 | 88.28 | 8.91 | 44.70 |
| Holt-Winters | 48.18 | 33.32 | 67.74 | 88.16 | 13.46 | 71.48 |
| LSTM | 41.06 | 33.27 | 47.19 | 88.92 | 12.10 | 48.98 |
| XGBoost | 35.70 | 39.24 | 46.90 | 72.39 | 10.07 | 57.76 |
| Prophet | 38.34 | 38.41 | 51.67 | 70.35 | 18.01 | 38.60 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 3.5 | 4.5 | 5.5 | 6.0 | 5.8 | 7.0 |
| Seasonal naive (weekly) | 4.2 | 5.0 | 6.5 | 4.8 | 5.2 | 6.2 |
| ARIMA | 5.2 | 2.2 | 4.2 | 4.5 | 3.5 | 2.8 |
| SARIMA | 5.8 | 2.8 | 3.8 | 4.0 | 2.8 | 3.2 |
| Holt-Winters | 4.8 | 4.8 | 5.0 | 5.5 | 5.5 | 7.0 |
| LSTM | 5.5 | 5.0 | 4.0 | 4.2 | 4.2 | 4.2 |
| XGBoost | 3.0 | 6.8 | 3.2 | 4.5 | 3.2 | 4.5 |
| Prophet | 4.0 | 5.0 | 3.8 | 2.5 | 5.8 | 1.0 |

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
| Ahmedabad | 2026-01-30 to 2026-02-28 | Prophet | 27.53 | 22.22 | 15.4 | Naive (last value) (32.10) | yes |
| Bengaluru | 2026-01-30 to 2026-02-28 | SARIMA | 16.62 | 13.94 | 15.8 | Naive (last value) (26.87) | yes |
| Chennai | 2026-01-30 to 2026-02-28 | Prophet | 36.50 | 29.04 | 31.3 | Naive (last value) (43.19) | yes |
| Delhi | 2026-01-30 to 2026-02-28 | LSTM | 32.59 | 27.26 | 10.5 | Naive (last value) (65.23) | yes |
| Hyderabad | 2026-01-30 to 2026-02-28 | Prophet | 7.71 | 6.53 | 6.8 | Seasonal naive (weekly) (8.81) | yes |
| Lucknow | 2026-01-30 to 2026-02-28 | Prophet | 27.28 | 22.64 | 28.8 | Naive (last value) (40.60) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 32.10 | 26.87 | 43.19 | 65.23 | 12.78 | 40.60 |
| Seasonal naive (weekly) | 36.82 | 28.96 | 46.41 | 76.17 | 8.81 | 45.95 |
| ARIMA | 50.12 | 16.63 | 42.83 | 46.66 | 10.94 | 32.76 |
| SARIMA | 49.98 | 16.62 | 42.80 | 46.60 | 10.92 | 34.92 |
| Holt-Winters | 42.56 | 25.91 | 39.83 | 38.51 | 11.67 | 41.75 |
| LSTM | 36.73 | 20.67 | 40.01 | 32.59 | 10.34 | 45.53 |
| XGBoost | 32.44 | 24.10 | 45.40 | 41.00 | 10.41 | 39.35 |
| Prophet | 27.53 | 23.14 | 36.50 | 37.96 | 7.71 | 27.28 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 1.62 |
| Bengaluru | 1.27 |
| Chennai | 1.27 |
| Delhi | 0.81 |
| Hyderabad | 0.23 |
| Lucknow | 1.32 |

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
- Ahmedabad: never beat the baseline in any window: Holt-Winters
- Lucknow: never beat the baseline in any window: Holt-Winters
