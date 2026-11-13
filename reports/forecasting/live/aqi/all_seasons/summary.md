# AQI forecasting: evaluation summary

Generated 2026-11-13T13:11:12+00:00. Models fitted on log1p(AQI), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 10 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. The windows ending on 2025-11-30, 2025-12-30, 2026-01-29, 2026-02-28 are added so the comparison includes winter. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | ARIMA | 32.32 | 10% | 30% | Naive (last value) | Naive (last value) (33.43) | yes |
| Bengaluru | ARIMA | 29.21 | 30% | 50% | ARIMA | Seasonal naive (weekly) (30.79) | yes |
| Chennai | XGBoost | 33.32 | 10% | 30% | LSTM | Seasonal naive (weekly) (39.71) | yes |
| Delhi | XGBoost | 62.11 | 10% | 70% | SARIMA | Naive (last value) (86.46) | yes |
| Hyderabad | XGBoost | 12.59 | 10% | 40% | Holt-Winters | Naive (last value) (13.68) | yes |
| Lucknow | ARIMA | 34.73 | 0% | 90% | Prophet | Seasonal naive (weekly) (49.79) | yes |

### Win rate (share of 10 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 40% | 10% | 10% | 10% | 0% | 0% |
| Seasonal naive (weekly) | 0% | 10% | 0% | 10% | 0% | 0% |
| Seasonal naive (annual) | 0% | 10% | 0% | 0% | 10% | 0% |
| ARIMA | 10% | 30% | 20% | 10% | 0% | 0% |
| SARIMA | 0% | 20% | 0% | 20% | 30% | 0% |
| Holt-Winters | 10% | 10% | 20% | 10% | 30% | 10% |
| LSTM | 0% | 0% | 20% | 10% | 0% | 0% |
| XGBoost | 20% | 0% | 10% | 10% | 10% | 30% |
| Prophet | 20% | 10% | 20% | 20% | 20% | 60% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 30% | 50% | 80% | 70% | 30% | 90% |
| SARIMA | 30% | 40% | 50% | 70% | 30% | 90% |
| Holt-Winters | 20% | 30% | 50% | 20% | 50% | 20% |
| LSTM | 20% | 20% | 30% | 70% | 20% | 70% |
| XGBoost | 30% | 20% | 30% | 70% | 40% | 80% |
| Prophet | 50% | 40% | 30% | 60% | 40% | 70% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 33.43 | 31.46 | 45.12 | 86.46 | 13.68 | 51.83 |
| Seasonal naive (weekly) | 38.72 | 30.79 | 39.71 | 88.50 | 14.42 | 49.79 |
| Seasonal naive (annual) | 44.42 | 32.36 | 30.59 | 67.19 | 20.57 | 38.13 |
| ARIMA | 32.32 | 29.21 | 34.92 | 65.11 | 12.65 | 34.73 |
| SARIMA | 32.34 | 29.69 | 35.98 | 65.16 | 13.32 | 35.22 |
| Holt-Winters | 37.67 | 31.06 | 44.03 | 84.00 | 13.06 | 51.76 |
| LSTM | 34.20 | 31.94 | 34.62 | 68.70 | 14.54 | 37.78 |
| XGBoost | 36.31 | 34.23 | 33.32 | 62.11 | 12.59 | 40.60 |
| Prophet | 34.74 | 31.66 | 40.39 | 64.85 | 15.03 | 35.17 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 3.1 | 4.5 | 5.2 | 6.1 | 4.8 | 6.1 |
| Seasonal naive (weekly) | 5.7 | 4.1 | 5.4 | 6.4 | 5.7 | 7.1 |
| Seasonal naive (annual) | 8.5 | 6.8 | 7.2 | 6.5 | 7.3 | 6.7 |
| ARIMA | 4.1 | 3.5 | 3.2 | 3.1 | 4.2 | 2.8 |
| SARIMA | 4.5 | 4.1 | 4.4 | 2.9 | 3.9 | 3.0 |
| Holt-Winters | 4.5 | 4.6 | 4.3 | 6.2 | 3.9 | 6.8 |
| LSTM | 5.2 | 5.8 | 4.5 | 4.3 | 5.6 | 4.2 |
| XGBoost | 5.4 | 6.4 | 4.4 | 4.3 | 3.9 | 3.8 |
| Prophet | 3.8 | 4.3 | 5.7 | 4.2 | 5.0 | 3.6 |

### Test windows

| City | Window 0 | Window 1 | Window 2 | Window 3 | Window 4 | Window 5 | Window 6 | Window 7 | Window 8 | Window 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Ahmedabad | w0: 2026-10-14 to 2026-11-12 | w1: 2026-08-30 to 2026-09-28 | w2: 2026-07-16 to 2026-08-14 | w3: 2026-06-01 to 2026-06-30 | w4: 2026-04-17 to 2026-05-16 | w5: 2026-03-03 to 2026-04-01 | w6: 2026-01-30 to 2026-02-28 | w7: 2025-12-31 to 2026-01-29 | w8: 2025-12-01 to 2025-12-30 | w9: 2025-11-01 to 2025-11-30 |
| Bengaluru | w0: 2026-10-14 to 2026-11-12 | w1: 2026-08-30 to 2026-09-28 | w2: 2026-07-16 to 2026-08-14 | w3: 2026-06-01 to 2026-06-30 | w4: 2026-04-17 to 2026-05-16 | w5: 2026-03-03 to 2026-04-01 | w6: 2026-01-30 to 2026-02-28 | w7: 2025-12-31 to 2026-01-29 | w8: 2025-12-01 to 2025-12-30 | w9: 2025-11-01 to 2025-11-30 |
| Chennai | w0: 2026-10-14 to 2026-11-12 | w1: 2026-08-30 to 2026-09-28 | w2: 2026-07-16 to 2026-08-14 | w3: 2026-06-01 to 2026-06-30 | w4: 2026-04-17 to 2026-05-16 | w5: 2026-03-03 to 2026-04-01 | w6: 2026-01-30 to 2026-02-28 | w7: 2025-12-31 to 2026-01-29 | w8: 2025-12-01 to 2025-12-30 | w9: 2025-11-01 to 2025-11-30 |
| Delhi | w0: 2026-10-14 to 2026-11-12 | w1: 2026-08-30 to 2026-09-28 | w2: 2026-07-16 to 2026-08-14 | w3: 2026-06-01 to 2026-06-30 | w4: 2026-04-17 to 2026-05-16 | w5: 2026-03-03 to 2026-04-01 | w6: 2026-01-30 to 2026-02-28 | w7: 2025-12-31 to 2026-01-29 | w8: 2025-12-01 to 2025-12-30 | w9: 2025-11-01 to 2025-11-30 |
| Hyderabad | w0: 2026-10-14 to 2026-11-12 | w1: 2026-08-30 to 2026-09-28 | w2: 2026-07-16 to 2026-08-14 | w3: 2026-06-01 to 2026-06-30 | w4: 2026-04-17 to 2026-05-16 | w5: 2026-03-03 to 2026-04-01 | w6: 2026-01-30 to 2026-02-28 | w7: 2025-12-31 to 2026-01-29 | w8: 2025-12-01 to 2025-12-30 | w9: 2025-11-01 to 2025-11-30 |
| Lucknow | w0: 2026-10-14 to 2026-11-12 | w1: 2026-08-30 to 2026-09-28 | w2: 2026-07-16 to 2026-08-14 | w3: 2026-06-01 to 2026-06-30 | w4: 2026-04-17 to 2026-05-16 | w5: 2026-03-03 to 2026-04-01 | w6: 2026-01-30 to 2026-02-28 | w7: 2025-12-31 to 2026-01-29 | w8: 2025-12-01 to 2025-12-30 | w9: 2025-11-01 to 2025-11-30 |

## Final 30-day hold-out only (window 0, kept for comparison)

| City | Window | Best model | RMSE | MAE | MAPE % | Best baseline (RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | 2026-10-14 to 2026-11-12 | SARIMA | 45.06 | 27.87 | 18.0 | Naive (last value) (43.55) | **no** |
| Bengaluru | 2026-10-14 to 2026-11-12 | Prophet | 40.87 | 33.06 | 40.0 | Seasonal naive (annual) (36.43) | **no** |
| Chennai | 2026-10-14 to 2026-11-12 | LSTM | 50.98 | 36.35 | 44.9 | Seasonal naive (weekly) (53.42) | yes |
| Delhi | 2026-10-14 to 2026-11-12 | ARIMA | 82.68 | 56.43 | 34.2 | Seasonal naive (annual) (99.42) | yes |
| Hyderabad | 2026-10-14 to 2026-11-12 | Holt-Winters | 24.13 | 15.96 | 20.6 | Naive (last value) (24.22) | yes |
| Lucknow | 2026-10-14 to 2026-11-12 | XGBoost | 59.09 | 47.96 | 48.2 | Seasonal naive (annual) (80.71) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 43.55 | 49.44 | 53.44 | 181.56 | 24.22 | 86.88 |
| Seasonal naive (weekly) | 56.09 | 43.51 | 53.42 | 185.85 | 25.90 | 93.26 |
| Seasonal naive (annual) | 78.70 | 36.43 | 67.99 | 99.42 | 26.81 | 80.71 |
| ARIMA | 45.92 | 44.65 | 52.45 | 82.68 | 25.46 | 60.35 |
| SARIMA | 45.06 | 44.59 | 53.08 | 83.42 | 25.32 | 60.48 |
| Holt-Winters | 45.63 | 49.05 | 59.62 | 140.75 | 24.13 | 72.26 |
| LSTM | 46.17 | 43.85 | 50.98 | 93.14 | 24.63 | 62.90 |
| XGBoost | 52.80 | 45.24 | 54.33 | 86.16 | 25.67 | 59.09 |
| Prophet | 50.44 | 40.87 | 57.69 | 103.07 | 25.86 | 63.21 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 1.26 |
| Bengaluru | 0.85 |
| Chennai | 1.59 |
| Delhi | 1.15 |
| Hyderabad | 0.92 |
| Lucknow | 0.84 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-20 to 2026-11-12 | 631 | 46 | 0.3933 | 0.049 | 1 | 0.85 | nan (-) | 0.04 / nan |
| Bengaluru | 2025-02-20 to 2026-11-12 | 631 | 47 | 0.0303 | 0.035 | 0 | 0.74 | nan (-) | 0.02 / nan |
| Chennai | 2025-02-20 to 2026-11-12 | 631 | 46 | 0.0223 | 0.100 | 0 | 0.61 | nan (-) | 0.12 / nan |
| Hyderabad | 2025-02-20 to 2026-11-12 | 631 | 46 | 0.0827 | 0.010 | 1 | 0.82 | nan (-) | 0.09 / nan |
| Lucknow | 2025-02-20 to 2026-11-12 | 631 | 45 | 0.1801 | 0.069 | 1 | 0.69 | nan (-) | 0.00 / nan |
| Ahmedabad | 2025-02-20 to 2026-11-12 | 631 | 45 | 0.0174 | 0.075 | 0 | 0.64 | nan (-) | 0.04 / nan |

## Issues log

- **Ahmedabad / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Bengaluru / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Chennai / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Delhi / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Hyderabad / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 9 but size of corresponding boolean axis is 30`
- **Lucknow / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
