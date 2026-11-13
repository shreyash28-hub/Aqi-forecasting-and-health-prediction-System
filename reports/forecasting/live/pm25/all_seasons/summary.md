# PM2.5 forecasting: evaluation summary

Generated 2026-11-13T13:17:29+00:00. Models fitted on log1p(PM2.5), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 10 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. The windows ending on 2025-11-30, 2025-12-30, 2026-01-29, 2026-02-28 are added so the comparison includes winter. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | ARIMA | 14.39 | 20% | 50% | XGBoost | Naive (last value) (18.72) | yes |
| Bengaluru | Prophet | 13.88 | 10% | 40% | Seasonal naive (weekly) | Seasonal naive (weekly) (15.70) | yes |
| Chennai | XGBoost | 16.24 | 20% | 60% | Naive (last value) | Seasonal naive (weekly) (21.28) | yes |
| Delhi | XGBoost | 41.91 | 20% | 80% | ARIMA | Seasonal naive (weekly) (58.91) | yes |
| Hyderabad | Holt-Winters | 7.83 | 10% | 30% | LSTM | Naive (last value) (8.21) | yes |
| Lucknow | Prophet | 16.82 | 40% | 90% | Prophet | Seasonal naive (weekly) (23.01) | yes |

### Win rate (share of 10 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 20% | 20% | 30% | 0% | 10% | 0% |
| Seasonal naive (weekly) | 10% | 20% | 0% | 0% | 10% | 0% |
| Seasonal naive (annual) | 0% | 0% | 0% | 0% | 10% | 0% |
| ARIMA | 20% | 10% | 20% | 20% | 10% | 30% |
| SARIMA | 0% | 0% | 0% | 10% | 10% | 0% |
| Holt-Winters | 20% | 10% | 10% | 20% | 10% | 0% |
| LSTM | 0% | 10% | 0% | 20% | 20% | 20% |
| XGBoost | 30% | 20% | 20% | 20% | 10% | 10% |
| Prophet | 0% | 10% | 20% | 10% | 10% | 40% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 50% | 30% | 50% | 70% | 30% | 90% |
| SARIMA | 50% | 20% | 50% | 60% | 40% | 90% |
| Holt-Winters | 30% | 30% | 10% | 50% | 30% | 10% |
| LSTM | 50% | 20% | 50% | 60% | 30% | 80% |
| XGBoost | 50% | 40% | 60% | 80% | 30% | 70% |
| Prophet | 40% | 40% | 40% | 70% | 20% | 90% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 18.72 | 16.97 | 24.65 | 59.13 | 8.21 | 26.01 |
| Seasonal naive (weekly) | 19.61 | 15.70 | 21.28 | 58.91 | 8.84 | 23.01 |
| Seasonal naive (annual) | 20.41 | 16.29 | 13.57 | 31.91 | 12.84 | 19.98 |
| ARIMA | 14.39 | 14.95 | 16.74 | 42.85 | 8.28 | 18.27 |
| SARIMA | 14.53 | 16.12 | 16.66 | 43.18 | 8.20 | 18.29 |
| Holt-Winters | 19.79 | 16.35 | 25.19 | 47.97 | 7.83 | 25.44 |
| LSTM | 15.83 | 16.14 | 16.55 | 44.74 | 9.98 | 20.08 |
| XGBoost | 18.78 | 14.69 | 16.24 | 41.91 | 8.22 | 18.96 |
| Prophet | 16.49 | 13.88 | 16.83 | 44.70 | 8.95 | 16.82 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 4.4 | 5.0 | 5.0 | 6.4 | 4.8 | 6.9 |
| Seasonal naive (weekly) | 6.0 | 4.3 | 6.2 | 6.6 | 5.3 | 6.3 |
| Seasonal naive (annual) | 8.7 | 7.5 | 6.3 | 6.7 | 7.5 | 7.0 |
| ARIMA | 3.5 | 3.7 | 4.6 | 2.7 | 4.2 | 2.5 |
| SARIMA | 3.2 | 5.2 | 4.4 | 3.7 | 3.4 | 2.9 |
| Holt-Winters | 4.8 | 4.2 | 5.8 | 4.6 | 4.2 | 6.8 |
| LSTM | 5.0 | 5.6 | 4.3 | 4.5 | 4.3 | 3.9 |
| XGBoost | 4.5 | 4.9 | 3.2 | 3.8 | 5.4 | 4.8 |
| Prophet | 4.8 | 4.0 | 4.1 | 5.1 | 5.3 | 3.1 |

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
| Ahmedabad | 2026-10-14 to 2026-11-12 | XGBoost | 20.82 | 14.53 | 24.0 | Naive (last value) (23.53) | yes |
| Bengaluru | 2026-10-14 to 2026-11-12 | Prophet | 19.54 | 16.62 | 63.1 | Seasonal naive (weekly) (19.38) | **no** |
| Chennai | 2026-10-14 to 2026-11-12 | Prophet | 24.51 | 19.13 | 81.5 | Seasonal naive (weekly) (26.99) | yes |
| Delhi | 2026-10-14 to 2026-11-12 | ARIMA | 56.49 | 46.33 | 45.5 | Seasonal naive (annual) (72.78) | yes |
| Hyderabad | 2026-10-14 to 2026-11-12 | LSTM | 11.73 | 8.10 | 22.0 | Seasonal naive (annual) (11.46) | **no** |
| Lucknow | 2026-10-14 to 2026-11-12 | ARIMA | 28.79 | 19.19 | 82.7 | Seasonal naive (annual) (35.29) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 23.53 | 26.08 | 30.32 | 105.77 | 12.23 | 40.60 |
| Seasonal naive (weekly) | 29.47 | 19.38 | 26.99 | 121.30 | 14.42 | 44.82 |
| Seasonal naive (annual) | 31.96 | 20.57 | 31.76 | 72.78 | 11.46 | 35.29 |
| ARIMA | 20.98 | 20.73 | 27.30 | 56.49 | 12.21 | 28.79 |
| SARIMA | 20.98 | 21.70 | 27.30 | 56.96 | 12.05 | 28.82 |
| Holt-Winters | 21.49 | 31.48 | 32.78 | 66.81 | 12.41 | 31.09 |
| LSTM | 21.31 | 19.98 | 24.72 | 67.52 | 11.73 | 29.83 |
| XGBoost | 20.82 | 21.87 | 26.59 | 75.40 | 12.95 | 32.15 |
| Prophet | 22.95 | 19.54 | 24.51 | 69.27 | 12.13 | 29.06 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.61 |
| Bengaluru | 0.36 |
| Chennai | 0.37 |
| Delhi | 0.81 |
| Hyderabad | 0.23 |
| Lucknow | 0.52 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-19 to 2026-11-12 | 632 | 44 | 0.5473 | 0.049 | 1 | 0.86 | nan (-) | 0.18 / nan |
| Bengaluru | 2025-02-19 to 2026-11-12 | 632 | 44 | 0.1274 | 0.018 | 1 | 0.79 | nan (-) | 0.01 / nan |
| Chennai | 2025-02-19 to 2026-11-12 | 632 | 46 | 0.1281 | 0.060 | 1 | 0.66 | nan (-) | 0.08 / nan |
| Hyderabad | 2025-02-19 to 2026-11-12 | 632 | 45 | 0.0183 | 0.010 | 0 | 0.67 | nan (-) | 0.10 / nan |
| Lucknow | 2025-02-19 to 2026-11-12 | 632 | 43 | 0.1764 | 0.039 | 1 | 0.71 | nan (-) | 0.05 / nan |
| Ahmedabad | 2025-02-19 to 2026-11-12 | 632 | 43 | 0.0073 | 0.100 | 0 | 0.69 | nan (-) | 0.06 / nan |

## Issues log

- **Ahmedabad / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Bengaluru / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Chennai / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Delhi / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Hyderabad / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 6 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Lucknow / window 7 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 8 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 9 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
