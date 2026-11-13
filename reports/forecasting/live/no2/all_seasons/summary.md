# NO2 forecasting: evaluation summary

Generated 2026-11-13T13:24:52+00:00. Models fitted on log1p(NO2), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 10 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. The windows ending on 2025-11-30, 2025-12-30, 2026-01-29, 2026-02-28 are added so the comparison includes winter. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | XGBoost | 11.17 | 30% | 40% | XGBoost | Naive (last value) (12.01) | yes |
| Bengaluru | Holt-Winters | 5.60 | 0% | 40% | LSTM | Naive (last value) (4.78) | **no** |
| Chennai | ARIMA | 1.54 | 10% | 60% | Naive (last value) | Naive (last value) (1.68) | yes |
| Delhi | ARIMA | 7.69 | 0% | 40% | Naive (last value) | Naive (last value) (9.37) | yes |
| Hyderabad | Prophet | 1.79 | 40% | 60% | Prophet | Naive (last value) (1.97) | yes |
| Lucknow | ARIMA | 2.13 | 30% | 60% | Naive (last value) | Naive (last value) (2.46) | yes |

### Win rate (share of 10 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 20% | 30% | 30% | 40% | 30% | 30% |
| Seasonal naive (weekly) | 10% | 0% | 10% | 0% | 0% | 10% |
| Seasonal naive (annual) | 0% | 10% | 0% | 0% | 0% | 0% |
| ARIMA | 10% | 0% | 10% | 0% | 10% | 30% |
| SARIMA | 0% | 10% | 20% | 30% | 0% | 10% |
| Holt-Winters | 0% | 0% | 0% | 0% | 10% | 0% |
| LSTM | 20% | 30% | 20% | 10% | 0% | 0% |
| XGBoost | 30% | 0% | 0% | 20% | 10% | 20% |
| Prophet | 10% | 20% | 10% | 0% | 40% | 0% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 30% | 50% | 60% | 40% | 20% | 60% |
| SARIMA | 30% | 50% | 60% | 50% | 20% | 60% |
| Holt-Winters | 30% | 40% | 30% | 10% | 40% | 20% |
| LSTM | 40% | 30% | 50% | 60% | 20% | 30% |
| XGBoost | 40% | 10% | 40% | 60% | 20% | 50% |
| Prophet | 10% | 40% | 50% | 40% | 60% | 10% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 12.01 | 4.78 | 1.68 | 9.37 | 1.97 | 2.46 |
| Seasonal naive (weekly) | 12.80 | 5.88 | 1.78 | 9.66 | 2.02 | 2.52 |
| Seasonal naive (annual) | 10.56 | 5.17 | 2.92 | 9.96 | 5.27 | 3.57 |
| ARIMA | 12.75 | 5.68 | 1.54 | 7.69 | 2.43 | 2.13 |
| SARIMA | 12.74 | 5.75 | 1.61 | 7.80 | 2.39 | 2.13 |
| Holt-Winters | 12.91 | 5.60 | 1.73 | 9.61 | 2.17 | 2.37 |
| LSTM | 12.45 | 6.57 | 1.92 | 7.79 | 2.58 | 3.91 |
| XGBoost | 11.17 | 5.86 | 1.94 | 8.56 | 2.39 | 2.16 |
| Prophet | 15.71 | 6.73 | 1.64 | 8.97 | 1.79 | 3.16 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 3.5 | 3.5 | 4.8 | 4.2 | 3.8 | 4.2 |
| Seasonal naive (weekly) | 4.9 | 5.7 | 4.8 | 5.6 | 4.3 | 4.5 |
| Seasonal naive (annual) | 8.5 | 6.3 | 8.7 | 6.8 | 8.7 | 7.5 |
| ARIMA | 4.3 | 4.3 | 3.4 | 3.7 | 5.3 | 3.2 |
| SARIMA | 4.5 | 3.9 | 3.9 | 3.8 | 4.6 | 3.8 |
| Holt-Winters | 4.6 | 4.7 | 5.3 | 5.9 | 4.7 | 4.4 |
| LSTM | 4.7 | 4.7 | 4.1 | 3.8 | 5.5 | 6.5 |
| XGBoost | 3.2 | 5.5 | 5.7 | 4.9 | 5.2 | 3.8 |
| Prophet | 6.6 | 5.3 | 4.2 | 5.4 | 2.8 | 6.5 |

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
| Ahmedabad | 2026-10-14 to 2026-11-12 | XGBoost | 6.87 | 5.83 | 19.4 | Naive (last value) (6.30) | **no** |
| Bengaluru | 2026-10-14 to 2026-11-12 | XGBoost | 5.37 | 4.59 | 29.1 | Seasonal naive (annual) (4.84) | **no** |
| Chennai | 2026-10-14 to 2026-11-12 | SARIMA | 1.80 | 1.59 | 15.8 | Seasonal naive (weekly) (2.04) | yes |
| Delhi | 2026-10-14 to 2026-11-12 | Holt-Winters | 6.28 | 5.39 | 18.9 | Naive (last value) (5.51) | **no** |
| Hyderabad | 2026-10-14 to 2026-11-12 | XGBoost | 1.79 | 1.29 | 13.9 | Seasonal naive (weekly) (2.56) | yes |
| Lucknow | 2026-10-14 to 2026-11-12 | Prophet | 0.89 | 0.77 | 4.6 | Naive (last value) (0.53) | **no** |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 6.30 | 5.54 | 2.04 | 5.51 | 3.38 | 0.53 |
| Seasonal naive (weekly) | 8.38 | 5.63 | 2.04 | 8.04 | 2.56 | 0.76 |
| Seasonal naive (annual) | 11.44 | 4.84 | 3.68 | 19.79 | 4.13 | 5.33 |
| ARIMA | 8.90 | 5.67 | 1.84 | 12.22 | 2.18 | 2.45 |
| SARIMA | 8.90 | 5.52 | 1.80 | 16.79 | 2.18 | 2.45 |
| Holt-Winters | 7.44 | 5.83 | 2.02 | 6.28 | 3.03 | 1.63 |
| LSTM | 7.65 | 6.40 | 3.58 | 17.10 | 2.16 | 2.54 |
| XGBoost | 6.87 | 5.37 | 1.99 | 16.48 | 1.79 | 1.56 |
| Prophet | 11.37 | 5.99 | 2.27 | 11.82 | 2.32 | 0.89 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.77 |
| Bengaluru | 0.27 |
| Chennai | 0.04 |
| Delhi | 0.22 |
| Hyderabad | 0.18 |
| Lucknow | 0.34 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-19 to 2026-11-12 | 632 | 44 | 0.4886 | 0.013 | 1 | 0.84 | nan (-) | 0.11 / nan |
| Bengaluru | 2025-02-19 to 2026-11-12 | 632 | 44 | 0.1298 | 0.091 | 1 | 0.86 | nan (-) | 0.14 / nan |
| Chennai | 2025-02-19 to 2026-11-12 | 632 | 44 | 0.1231 | 0.010 | 1 | 0.56 | nan (-) | 0.09 / nan |
| Hyderabad | 2025-02-19 to 2026-11-12 | 632 | 44 | 0.0015 | 0.010 | 0 | 0.59 | nan (-) | 0.05 / nan |
| Lucknow | 2025-02-19 to 2026-11-12 | 632 | 43 | 0.0011 | 0.087 | 0 | 0.80 | nan (-) | 0.00 / nan |
| Ahmedabad | 2025-02-19 to 2026-11-12 | 632 | 43 | 0.0900 | 0.054 | 1 | 0.74 | nan (-) | 0.10 / nan |

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
