# AQI forecasting: evaluation summary

Generated 2026-10-30T13:58:26+00:00. Models fitted on log1p(AQI), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 5 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | SARIMA | 19.88 | 0% | 40% | ARIMA | Naive (last value) (22.35) | yes |
| Bengaluru | Prophet | 19.36 | 20% | 60% | Holt-Winters | Naive (last value) (27.04) | yes |
| Chennai | ARIMA | 18.79 | 40% | 40% | ARIMA | Naive (last value) (19.50) | yes |
| Delhi | ARIMA | 46.93 | 20% | 80% | SARIMA | Seasonal naive (weekly) (59.61) | yes |
| Hyderabad | ARIMA | 7.68 | 20% | 60% | Naive (last value) | Naive (last value) (10.28) | yes |
| Lucknow | SARIMA | 24.97 | 0% | 40% | Naive (last value) | Naive (last value) (27.82) | yes |

### Win rate (share of 5 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 20% | 20% | 20% | 0% | 40% | 40% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 0% | 0% | 0% |
| Seasonal naive (annual) | 0% | 0% | 20% | 0% | 0% | 0% |
| ARIMA | 40% | 20% | 40% | 20% | 20% | 20% |
| SARIMA | 0% | 0% | 0% | 40% | 0% | 0% |
| Holt-Winters | 0% | 20% | 20% | 20% | 20% | 0% |
| LSTM | 20% | 0% | 0% | 20% | 20% | 0% |
| XGBoost | 0% | 20% | 0% | 0% | 0% | 20% |
| Prophet | 20% | 20% | 0% | 0% | 0% | 20% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 40% | 40% | 40% | 80% | 60% | 40% |
| SARIMA | 40% | 40% | 20% | 60% | 20% | 40% |
| Holt-Winters | 40% | 20% | 20% | 40% | 40% | 20% |
| LSTM | 40% | 40% | 0% | 80% | 40% | 60% |
| XGBoost | 0% | 20% | 20% | 40% | 60% | 40% |
| Prophet | 40% | 60% | 0% | 40% | 0% | 20% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 22.35 | 27.04 | 19.50 | 63.13 | 10.28 | 27.82 |
| Seasonal naive (weekly) | 27.58 | 27.16 | 21.04 | 59.61 | 15.51 | 32.68 |
| Seasonal naive (annual) | 45.43 | 29.68 | 29.43 | 61.75 | 18.80 | 38.23 |
| ARIMA | 20.12 | 21.26 | 18.79 | 46.93 | 7.68 | 28.34 |
| SARIMA | 19.88 | 23.37 | 26.84 | 47.59 | 12.48 | 24.97 |
| Holt-Winters | 20.49 | 23.26 | 20.82 | 58.29 | 8.13 | 30.13 |
| LSTM | 22.70 | 23.84 | 21.20 | 48.48 | 10.04 | 26.95 |
| XGBoost | 36.22 | 27.95 | 19.14 | 51.67 | 9.02 | 26.51 |
| Prophet | 22.42 | 19.36 | 21.47 | 55.54 | 15.79 | 29.01 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 3.2 | 4.4 | 4.2 | 5.2 | 3.4 | 4.4 |
| Seasonal naive (weekly) | 6.4 | 5.2 | 5.2 | 6.0 | 7.4 | 6.6 |
| Seasonal naive (annual) | 8.6 | 7.6 | 7.0 | 8.0 | 7.8 | 7.6 |
| ARIMA | 2.8 | 3.6 | 4.0 | 2.8 | 2.6 | 4.8 |
| SARIMA | 3.2 | 4.8 | 5.2 | 3.6 | 5.6 | 3.4 |
| Holt-Winters | 3.8 | 4.0 | 4.8 | 5.0 | 2.4 | 6.0 |
| LSTM | 4.8 | 5.4 | 4.6 | 3.2 | 4.6 | 3.6 |
| XGBoost | 7.8 | 6.2 | 4.4 | 4.8 | 3.6 | 4.0 |
| Prophet | 4.4 | 3.8 | 5.6 | 6.4 | 7.6 | 4.6 |

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
| Ahmedabad | 2026-09-30 to 2026-10-29 | ARIMA | 21.07 | 14.91 | 10.7 | Seasonal naive (weekly) (38.91) | yes |
| Bengaluru | 2026-09-30 to 2026-10-29 | Holt-Winters | 24.66 | 21.86 | 27.9 | Naive (last value) (26.30) | yes |
| Chennai | 2026-09-30 to 2026-10-29 | ARIMA | 21.79 | 17.66 | 23.9 | Seasonal naive (weekly) (22.47) | yes |
| Delhi | 2026-09-30 to 2026-10-29 | SARIMA | 48.22 | 41.60 | 25.8 | Seasonal naive (annual) (70.99) | yes |
| Hyderabad | 2026-09-30 to 2026-10-29 | LSTM | 12.57 | 10.23 | 13.1 | Seasonal naive (annual) (16.35) | yes |
| Lucknow | 2026-09-30 to 2026-10-29 | SARIMA | 25.65 | 23.40 | 31.7 | Naive (last value) (24.27) | **no** |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 43.81 | 26.30 | 24.79 | 129.50 | 18.44 | 24.27 |
| Seasonal naive (weekly) | 38.91 | 35.10 | 22.47 | 93.96 | 27.31 | 39.11 |
| Seasonal naive (annual) | 76.65 | 37.07 | 56.00 | 70.99 | 16.35 | 70.84 |
| ARIMA | 21.07 | 27.58 | 21.79 | 54.41 | 13.14 | 36.14 |
| SARIMA | 23.26 | 27.88 | 23.01 | 48.22 | 18.47 | 25.65 |
| Holt-Winters | 23.77 | 24.66 | 26.57 | 104.47 | 13.37 | 36.70 |
| LSTM | 22.87 | 29.76 | 23.50 | 53.11 | 12.57 | 30.33 |
| XGBoost | 58.24 | 28.34 | 24.60 | 66.43 | 14.66 | 41.63 |
| Prophet | 29.29 | 30.98 | 29.71 | 66.69 | 23.58 | 34.65 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.99 |
| Bengaluru | 0.65 |
| Chennai | 2.34 |
| Delhi | 0.81 |
| Hyderabad | 0.24 |
| Lucknow | 0.86 |

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

- Ahmedabad: never beat the baseline in any window: XGBoost
- Chennai: never beat the baseline in any window: LSTM, Prophet
- Hyderabad: never beat the baseline in any window: Prophet
