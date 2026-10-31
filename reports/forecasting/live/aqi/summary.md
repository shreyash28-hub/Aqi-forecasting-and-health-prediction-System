# AQI forecasting: evaluation summary

Generated 2026-10-31T09:15:10+00:00. Models fitted on log1p(AQI), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 5 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | Holt-Winters | 20.71 | 20% | 60% | SARIMA | Naive (last value) (22.35) | yes |
| Bengaluru | Holt-Winters | 22.67 | 0% | 40% | XGBoost | Naive (last value) (27.04) | yes |
| Chennai | XGBoost | 19.46 | 0% | 20% | SARIMA | Naive (last value) (19.50) | yes |
| Delhi | ARIMA | 51.12 | 40% | 60% | ARIMA | Seasonal naive (weekly) (59.61) | yes |
| Hyderabad | Holt-Winters | 9.07 | 20% | 60% | SARIMA | Naive (last value) (10.28) | yes |
| Lucknow | SARIMA | 25.19 | 20% | 40% | XGBoost | Naive (last value) (27.82) | yes |

### Win rate (share of 5 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 20% | 20% | 20% | 20% | 0% | 20% |
| Seasonal naive (weekly) | 0% | 20% | 0% | 0% | 0% | 0% |
| Seasonal naive (annual) | 0% | 0% | 20% | 0% | 0% | 0% |
| ARIMA | 0% | 20% | 20% | 40% | 0% | 0% |
| SARIMA | 20% | 0% | 20% | 0% | 40% | 20% |
| Holt-Winters | 20% | 0% | 20% | 20% | 20% | 0% |
| LSTM | 20% | 0% | 0% | 20% | 0% | 0% |
| XGBoost | 0% | 20% | 0% | 0% | 20% | 40% |
| Prophet | 20% | 20% | 0% | 0% | 20% | 20% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 40% | 40% | 40% | 60% | 60% | 40% |
| SARIMA | 40% | 40% | 20% | 60% | 60% | 40% |
| Holt-Winters | 60% | 40% | 20% | 20% | 60% | 40% |
| LSTM | 40% | 40% | 20% | 60% | 20% | 40% |
| XGBoost | 40% | 40% | 20% | 0% | 40% | 60% |
| Prophet | 60% | 20% | 0% | 20% | 20% | 60% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 22.35 | 27.04 | 19.50 | 63.13 | 10.28 | 27.82 |
| Seasonal naive (weekly) | 27.58 | 27.16 | 21.04 | 59.61 | 15.51 | 32.68 |
| Seasonal naive (annual) | 45.43 | 29.68 | 29.43 | 61.75 | 18.80 | 38.23 |
| ARIMA | 21.96 | 23.84 | 20.03 | 51.12 | 11.02 | 25.22 |
| SARIMA | 21.54 | 24.09 | 20.55 | 51.22 | 10.97 | 25.19 |
| Holt-Winters | 20.71 | 22.67 | 21.62 | 57.21 | 9.07 | 27.05 |
| LSTM | 24.22 | 25.15 | 19.52 | 53.87 | 15.23 | 26.87 |
| XGBoost | 28.45 | 30.21 | 19.46 | 55.77 | 12.15 | 26.59 |
| Prophet | 23.66 | 23.52 | 26.42 | 62.39 | 11.69 | 27.63 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 4.0 | 4.4 | 4.0 | 4.4 | 3.8 | 4.8 |
| Seasonal naive (weekly) | 6.0 | 4.8 | 5.2 | 5.4 | 7.0 | 7.6 |
| Seasonal naive (annual) | 8.6 | 7.0 | 7.2 | 7.2 | 8.0 | 7.2 |
| ARIMA | 4.2 | 4.0 | 3.8 | 2.8 | 3.0 | 4.0 |
| SARIMA | 3.6 | 4.6 | 4.2 | 3.4 | 3.2 | 3.4 |
| Holt-Winters | 3.0 | 3.8 | 5.0 | 5.4 | 3.2 | 4.2 |
| LSTM | 5.4 | 5.4 | 4.6 | 4.6 | 6.8 | 5.2 |
| XGBoost | 5.8 | 6.2 | 4.6 | 5.8 | 4.8 | 4.0 |
| Prophet | 4.4 | 4.8 | 6.4 | 6.0 | 5.2 | 4.6 |

### Test windows

| City | Window 0 | Window 1 | Window 2 | Window 3 | Window 4 |
|---|---|---|---|---|---|
| Ahmedabad | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Bengaluru | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Chennai | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Delhi | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Hyderabad | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Lucknow | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |

## Final 30-day hold-out only (window 0, kept for comparison)

| City | Window | Best model | RMSE | MAE | MAPE % | Best baseline (RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | 2026-09-30 to 2026-10-29 | SARIMA | 21.71 | 15.98 | 11.5 | Seasonal naive (weekly) (38.91) | yes |
| Bengaluru | 2026-09-30 to 2026-10-29 | XGBoost | 24.30 | 21.09 | 27.3 | Naive (last value) (26.30) | yes |
| Chennai | 2026-09-30 to 2026-10-29 | SARIMA | 20.76 | 16.85 | 22.5 | Seasonal naive (weekly) (22.47) | yes |
| Delhi | 2026-09-30 to 2026-10-29 | ARIMA | 63.86 | 51.84 | 36.4 | Seasonal naive (annual) (70.99) | yes |
| Hyderabad | 2026-09-30 to 2026-10-29 | SARIMA | 12.53 | 10.11 | 13.0 | Seasonal naive (annual) (16.35) | yes |
| Lucknow | 2026-09-30 to 2026-10-29 | Prophet | 22.60 | 19.40 | 26.0 | Naive (last value) (24.27) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 43.81 | 26.30 | 24.79 | 129.50 | 18.44 | 24.27 |
| Seasonal naive (weekly) | 38.91 | 35.10 | 22.47 | 93.96 | 27.31 | 39.11 |
| Seasonal naive (annual) | 76.65 | 37.07 | 56.00 | 70.99 | 16.35 | 70.84 |
| ARIMA | 24.18 | 28.28 | 21.30 | 63.86 | 12.88 | 26.10 |
| SARIMA | 21.71 | 28.40 | 20.76 | 64.17 | 12.53 | 25.74 |
| Holt-Winters | 22.49 | 24.66 | 28.35 | 94.85 | 15.46 | 23.00 |
| LSTM | 22.09 | 29.27 | 23.16 | 64.85 | 15.80 | 25.46 |
| XGBoost | 32.02 | 24.30 | 22.77 | 75.22 | 14.59 | 37.28 |
| Prophet | 32.34 | 26.72 | 39.12 | 103.72 | 23.35 | 22.60 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.98 |
| Bengaluru | 0.38 |
| Chennai | 1.35 |
| Delhi | 0.84 |
| Hyderabad | 0.87 |
| Lucknow | 0.46 |

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

- Chennai: never beat the baseline in any window: Prophet
- Delhi: never beat the baseline in any window: XGBoost
