# PM2.5 forecasting: evaluation summary

Generated 2026-10-31T09:18:11+00:00. Models fitted on log1p(PM2.5), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 5 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | ARIMA | 10.39 | 20% | 40% | Naive (last value) | Naive (last value) (10.50) | yes |
| Bengaluru | ARIMA | 9.99 | 20% | 40% | Naive (last value) | Naive (last value) (11.17) | yes |
| Chennai | LSTM | 8.53 | 0% | 20% | ARIMA | Naive (last value) (8.64) | yes |
| Delhi | Holt-Winters | 18.84 | 20% | 60% | Holt-Winters | Seasonal naive (weekly) (22.43) | yes |
| Hyderabad | Holt-Winters | 5.24 | 0% | 60% | XGBoost | Naive (last value) (5.52) | yes |
| Lucknow | XGBoost | 12.57 | 40% | 60% | XGBoost | Naive (last value) (16.54) | yes |

### Win rate (share of 5 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 40% | 20% | 20% | 0% | 40% | 20% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 20% | 0% | 0% |
| Seasonal naive (annual) | 0% | 0% | 0% | 0% | 0% | 0% |
| ARIMA | 20% | 20% | 40% | 20% | 0% | 20% |
| SARIMA | 20% | 20% | 0% | 0% | 0% | 0% |
| Holt-Winters | 0% | 20% | 0% | 20% | 0% | 20% |
| LSTM | 20% | 0% | 0% | 20% | 0% | 0% |
| XGBoost | 0% | 0% | 40% | 0% | 40% | 40% |
| Prophet | 0% | 20% | 0% | 20% | 20% | 0% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 40% | 40% | 40% | 80% | 60% | 60% |
| SARIMA | 40% | 40% | 40% | 80% | 60% | 60% |
| Holt-Winters | 20% | 40% | 0% | 60% | 60% | 20% |
| LSTM | 60% | 40% | 20% | 60% | 40% | 60% |
| XGBoost | 0% | 40% | 40% | 60% | 60% | 60% |
| Prophet | 40% | 40% | 0% | 60% | 20% | 60% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 10.50 | 11.17 | 8.64 | 24.48 | 5.52 | 16.54 |
| Seasonal naive (weekly) | 15.28 | 13.57 | 10.19 | 22.43 | 9.07 | 19.52 |
| Seasonal naive (annual) | 19.59 | 15.03 | 12.47 | 25.10 | 12.04 | 20.32 |
| ARIMA | 10.39 | 9.99 | 8.99 | 19.13 | 7.15 | 13.23 |
| SARIMA | 10.40 | 11.56 | 9.02 | 19.78 | 7.05 | 13.19 |
| Holt-Winters | 11.34 | 10.19 | 10.72 | 18.84 | 5.24 | 16.38 |
| LSTM | 12.71 | 12.06 | 8.53 | 19.50 | 9.48 | 13.38 |
| XGBoost | 14.78 | 11.62 | 8.59 | 23.17 | 6.07 | 12.57 |
| Prophet | 11.55 | 10.33 | 9.97 | 25.77 | 6.89 | 14.01 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 3.8 | 4.4 | 3.6 | 6.8 | 4.0 | 4.8 |
| Seasonal naive (weekly) | 6.8 | 5.8 | 6.2 | 5.2 | 7.4 | 7.8 |
| Seasonal naive (annual) | 7.2 | 7.8 | 6.4 | 6.8 | 7.6 | 8.2 |
| ARIMA | 3.2 | 3.0 | 4.0 | 3.2 | 4.6 | 3.0 |
| SARIMA | 3.0 | 4.4 | 4.6 | 4.4 | 4.0 | 3.2 |
| Holt-Winters | 4.4 | 4.8 | 6.0 | 4.0 | 2.8 | 6.0 |
| LSTM | 4.8 | 6.0 | 4.4 | 4.4 | 6.2 | 3.6 |
| XGBoost | 6.8 | 4.8 | 4.0 | 4.6 | 3.6 | 3.4 |
| Prophet | 5.0 | 4.0 | 5.8 | 5.6 | 4.8 | 5.0 |

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
| Ahmedabad | 2026-09-30 to 2026-10-29 | SARIMA | 13.81 | 10.38 | 17.4 | Naive (last value) (17.13) | yes |
| Bengaluru | 2026-09-30 to 2026-10-29 | ARIMA | 13.81 | 11.96 | 44.7 | Naive (last value) (13.34) | **no** |
| Chennai | 2026-09-30 to 2026-10-29 | ARIMA | 13.13 | 10.29 | 46.8 | Seasonal naive (weekly) (13.81) | yes |
| Delhi | 2026-09-30 to 2026-10-29 | Holt-Winters | 27.12 | 23.16 | 30.2 | Seasonal naive (annual) (42.32) | yes |
| Hyderabad | 2026-09-30 to 2026-10-29 | XGBoost | 6.93 | 5.52 | 14.8 | Naive (last value) (8.42) | yes |
| Lucknow | 2026-09-30 to 2026-10-29 | XGBoost | 13.91 | 11.61 | 31.5 | Naive (last value) (15.09) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 17.13 | 13.34 | 17.34 | 45.73 | 8.42 | 15.09 |
| Seasonal naive (weekly) | 21.24 | 17.32 | 13.81 | 44.03 | 12.79 | 28.60 |
| Seasonal naive (annual) | 33.83 | 21.47 | 28.45 | 42.32 | 8.60 | 35.00 |
| ARIMA | 13.83 | 13.81 | 13.13 | 31.55 | 7.43 | 14.36 |
| SARIMA | 13.81 | 14.65 | 13.19 | 33.37 | 7.10 | 14.04 |
| Holt-Winters | 15.95 | 16.76 | 23.18 | 27.12 | 8.25 | 16.20 |
| LSTM | 14.65 | 16.89 | 14.32 | 30.75 | 7.29 | 14.90 |
| XGBoost | 18.37 | 15.01 | 15.10 | 49.32 | 6.93 | 13.91 |
| Prophet | 14.87 | 14.46 | 14.30 | 61.81 | 11.37 | 14.18 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.17 |
| Bengaluru | 0.32 |
| Chennai | 0.14 |
| Delhi | 1.44 |
| Hyderabad | 0.60 |
| Lucknow | 0.27 |

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

- Ahmedabad: never beat the baseline in any window: XGBoost
- Chennai: never beat the baseline in any window: Prophet, Holt-Winters
