# PM2.5 forecasting: evaluation summary

Generated 2026-10-30T14:01:51+00:00. Models fitted on log1p(PM2.5), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 5 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | SARIMA | 9.71 | 40% | 60% | SARIMA | Naive (last value) (10.50) | yes |
| Bengaluru | Prophet | 9.44 | 20% | 60% | Naive (last value) | Naive (last value) (11.17) | yes |
| Chennai | SARIMA | 7.55 | 60% | 80% | SARIMA | Naive (last value) (8.64) | yes |
| Delhi | SARIMA | 15.73 | 80% | 80% | SARIMA | Seasonal naive (weekly) (22.43) | yes |
| Hyderabad | XGBoost | 4.92 | 20% | 40% | SARIMA | Naive (last value) (5.52) | yes |
| Lucknow | SARIMA | 12.87 | 20% | 60% | XGBoost | Naive (last value) (16.54) | yes |

### Win rate (share of 5 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 20% | 40% | 0% | 0% | 0% | 20% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 20% | 0% | 0% |
| Seasonal naive (annual) | 0% | 0% | 0% | 0% | 0% | 0% |
| ARIMA | 20% | 20% | 20% | 0% | 20% | 20% |
| SARIMA | 40% | 0% | 60% | 80% | 40% | 20% |
| Holt-Winters | 0% | 0% | 0% | 0% | 0% | 0% |
| LSTM | 20% | 0% | 0% | 0% | 20% | 0% |
| XGBoost | 0% | 20% | 0% | 0% | 20% | 40% |
| Prophet | 0% | 20% | 20% | 0% | 0% | 0% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 40% | 40% | 40% | 80% | 20% | 60% |
| SARIMA | 60% | 40% | 80% | 80% | 60% | 60% |
| Holt-Winters | 20% | 20% | 0% | 60% | 20% | 20% |
| LSTM | 60% | 40% | 60% | 80% | 40% | 40% |
| XGBoost | 20% | 60% | 40% | 80% | 40% | 40% |
| Prophet | 20% | 60% | 40% | 60% | 40% | 60% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 10.50 | 11.17 | 8.64 | 24.48 | 5.52 | 16.54 |
| Seasonal naive (weekly) | 15.28 | 13.57 | 10.19 | 22.43 | 9.07 | 19.52 |
| Seasonal naive (annual) | 19.59 | 15.03 | 12.47 | 25.10 | 12.04 | 20.32 |
| ARIMA | 10.06 | 9.61 | 8.70 | 16.21 | 6.09 | 14.31 |
| SARIMA | 9.71 | 12.54 | 7.55 | 15.73 | 5.05 | 12.87 |
| Holt-Winters | 10.74 | 9.92 | 10.03 | 19.49 | 6.35 | 19.17 |
| LSTM | 12.13 | 10.94 | 8.32 | 17.15 | 5.98 | 14.01 |
| XGBoost | 13.83 | 10.82 | 8.61 | 18.30 | 4.92 | 13.65 |
| Prophet | 11.50 | 9.44 | 8.47 | 23.38 | 8.19 | 13.06 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 4.2 | 4.6 | 4.6 | 7.0 | 3.2 | 4.4 |
| Seasonal naive (weekly) | 7.2 | 6.2 | 7.2 | 5.6 | 7.8 | 7.6 |
| Seasonal naive (annual) | 7.6 | 7.8 | 7.2 | 7.6 | 7.8 | 8.2 |
| ARIMA | 3.8 | 4.0 | 4.2 | 3.6 | 4.4 | 3.6 |
| SARIMA | 2.4 | 5.6 | 1.8 | 1.6 | 2.4 | 3.4 |
| Holt-Winters | 4.4 | 4.4 | 6.6 | 5.6 | 4.8 | 6.6 |
| LSTM | 4.0 | 4.8 | 4.2 | 3.8 | 4.8 | 4.2 |
| XGBoost | 6.8 | 4.0 | 5.0 | 4.0 | 4.0 | 3.6 |
| Prophet | 4.6 | 3.6 | 4.2 | 6.2 | 5.8 | 3.4 |

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
| Ahmedabad | 2026-09-30 to 2026-10-29 | SARIMA | 13.40 | 10.42 | 18.2 | Naive (last value) (17.13) | yes |
| Bengaluru | 2026-09-30 to 2026-10-29 | Holt-Winters | 13.87 | 11.70 | 47.0 | Naive (last value) (13.34) | **no** |
| Chennai | 2026-09-30 to 2026-10-29 | Prophet | 12.85 | 10.56 | 46.0 | Seasonal naive (weekly) (13.81) | yes |
| Delhi | 2026-09-30 to 2026-10-29 | SARIMA | 19.50 | 16.93 | 23.6 | Seasonal naive (annual) (42.32) | yes |
| Hyderabad | 2026-09-30 to 2026-10-29 | XGBoost | 4.52 | 3.64 | 9.8 | Naive (last value) (8.42) | yes |
| Lucknow | 2026-09-30 to 2026-10-29 | SARIMA | 14.46 | 10.67 | 26.2 | Naive (last value) (15.09) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 17.13 | 13.34 | 17.34 | 45.73 | 8.42 | 15.09 |
| Seasonal naive (weekly) | 21.24 | 17.32 | 13.81 | 44.03 | 12.79 | 28.60 |
| Seasonal naive (annual) | 33.83 | 21.47 | 28.45 | 42.32 | 8.60 | 35.00 |
| ARIMA | 13.92 | 13.98 | 13.18 | 20.79 | 9.51 | 19.82 |
| SARIMA | 13.40 | 15.49 | 13.18 | 19.50 | 7.92 | 14.46 |
| Holt-Winters | 14.86 | 13.87 | 21.00 | 32.52 | 10.06 | 28.84 |
| LSTM | 14.77 | 16.87 | 14.49 | 23.49 | 10.91 | 17.51 |
| XGBoost | 16.83 | 15.12 | 14.23 | 30.96 | 4.52 | 21.80 |
| Prophet | 15.60 | 16.14 | 12.85 | 48.92 | 13.58 | 14.67 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.14 |
| Bengaluru | 0.46 |
| Chennai | 0.17 |
| Delhi | 0.27 |
| Hyderabad | 1.02 |
| Lucknow | 0.24 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.5820 | 0.043 | 1 | 0.86 | nan (-) | 0.18 / nan |
| Bengaluru | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.1163 | 0.019 | 1 | 0.79 | nan (-) | 0.02 / nan |
| Chennai | 2025-02-19 to 2026-10-29 | 618 | 45 | 0.1264 | 0.046 | 1 | 0.66 | nan (-) | 0.07 / nan |
| Hyderabad | 2025-02-19 to 2026-10-29 | 618 | 44 | 0.0014 | 0.010 | 0 | 0.66 | nan (-) | 0.09 / nan |
| Lucknow | 2025-02-19 to 2026-10-29 | 618 | 42 | 0.2204 | 0.042 | 1 | 0.71 | nan (-) | 0.07 / nan |
| Ahmedabad | 2025-02-19 to 2026-10-29 | 618 | 42 | 0.0085 | 0.084 | 0 | 0.69 | nan (-) | 0.03 / nan |

## Issues log

- Chennai: never beat the baseline in any window: Holt-Winters
