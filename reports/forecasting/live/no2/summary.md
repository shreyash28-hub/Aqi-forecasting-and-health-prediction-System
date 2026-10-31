# NO2 forecasting: evaluation summary

Generated 2026-10-31T09:21:28+00:00. Models fitted on log1p(NO2), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 5 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | LSTM | 6.06 | 20% | 60% | LSTM | Naive (last value) (7.42) | yes |
| Bengaluru | ARIMA | 3.44 | 20% | 60% | Naive (last value) | Seasonal naive (annual) (4.59) | yes |
| Chennai | Prophet | 1.68 | 20% | 60% | ARIMA | Seasonal naive (weekly) (1.86) | yes |
| Delhi | LSTM | 7.03 | 40% | 80% | LSTM | Seasonal naive (weekly) (7.23) | yes |
| Hyderabad | Prophet | 1.35 | 40% | 80% | Prophet | Naive (last value) (1.56) | yes |
| Lucknow | Holt-Winters | 1.73 | 0% | 20% | Naive (last value) | Naive (last value) (1.81) | yes |

### Win rate (share of 5 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 20% | 40% | 20% | 20% | 0% | 60% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 0% | 0% | 0% |
| Seasonal naive (annual) | 0% | 0% | 0% | 0% | 0% | 0% |
| ARIMA | 20% | 20% | 40% | 20% | 0% | 0% |
| SARIMA | 20% | 20% | 0% | 20% | 20% | 0% |
| Holt-Winters | 0% | 0% | 0% | 0% | 20% | 0% |
| LSTM | 20% | 20% | 20% | 40% | 0% | 0% |
| XGBoost | 20% | 0% | 0% | 0% | 20% | 20% |
| Prophet | 0% | 0% | 20% | 0% | 40% | 20% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 80% | 60% | 60% | 40% | 0% | 20% |
| SARIMA | 80% | 60% | 40% | 40% | 20% | 20% |
| Holt-Winters | 20% | 20% | 20% | 20% | 40% | 20% |
| LSTM | 60% | 20% | 60% | 80% | 0% | 20% |
| XGBoost | 60% | 0% | 20% | 40% | 20% | 20% |
| Prophet | 20% | 0% | 60% | 0% | 80% | 40% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 7.42 | 5.28 | 1.98 | 7.99 | 1.56 | 1.81 |
| Seasonal naive (weekly) | 8.60 | 6.20 | 1.86 | 7.23 | 1.83 | 2.25 |
| Seasonal naive (annual) | 9.69 | 4.59 | 2.63 | 9.41 | 3.38 | 3.67 |
| ARIMA | 7.20 | 3.44 | 1.73 | 7.65 | 2.10 | 2.23 |
| SARIMA | 7.21 | 3.49 | 1.88 | 7.90 | 2.05 | 2.24 |
| Holt-Winters | 7.40 | 4.84 | 1.88 | 8.67 | 1.36 | 1.73 |
| LSTM | 6.06 | 3.64 | 1.84 | 7.03 | 2.08 | 2.89 |
| XGBoost | 6.38 | 4.13 | 1.94 | 8.47 | 2.06 | 2.23 |
| Prophet | 9.28 | 5.24 | 1.68 | 8.77 | 1.35 | 2.34 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 5.6 | 3.8 | 5.6 | 6.0 | 3.4 | 2.6 |
| Seasonal naive (weekly) | 6.2 | 8.2 | 5.8 | 4.8 | 4.4 | 4.6 |
| Seasonal naive (annual) | 7.6 | 5.8 | 7.4 | 7.0 | 8.0 | 8.4 |
| ARIMA | 3.0 | 2.6 | 3.2 | 3.4 | 6.2 | 4.8 |
| SARIMA | 3.6 | 3.4 | 4.8 | 4.0 | 5.4 | 5.4 |
| Holt-Winters | 5.6 | 5.8 | 5.2 | 5.8 | 3.0 | 3.4 |
| LSTM | 3.8 | 4.0 | 3.4 | 2.8 | 6.4 | 7.0 |
| XGBoost | 3.0 | 5.8 | 5.6 | 5.2 | 5.6 | 4.2 |
| Prophet | 6.6 | 5.6 | 4.0 | 6.0 | 2.6 | 4.6 |

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
| Ahmedabad | 2026-09-30 to 2026-10-29 | LSTM | 5.19 | 3.96 | 14.9 | Seasonal naive (annual) (10.36) | yes |
| Bengaluru | 2026-09-30 to 2026-10-29 | Prophet | 4.26 | 3.28 | 20.8 | Naive (last value) (4.07) | **no** |
| Chennai | 2026-09-30 to 2026-10-29 | ARIMA | 2.09 | 1.91 | 21.3 | Seasonal naive (weekly) (2.76) | yes |
| Delhi | 2026-09-30 to 2026-10-29 | Holt-Winters | 8.75 | 7.41 | 27.2 | Naive (last value) (5.34) | **no** |
| Hyderabad | 2026-09-30 to 2026-10-29 | XGBoost | 1.17 | 0.82 | 7.6 | Naive (last value) (1.32) | yes |
| Lucknow | 2026-09-30 to 2026-10-29 | XGBoost | 1.27 | 1.15 | 7.1 | Naive (last value) (2.85) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 12.19 | 4.07 | 3.23 | 5.34 | 1.32 | 2.85 |
| Seasonal naive (weekly) | 11.39 | 6.40 | 2.76 | 5.94 | 1.36 | 3.81 |
| Seasonal naive (annual) | 10.36 | 5.13 | 2.88 | 16.54 | 3.76 | 4.31 |
| ARIMA | 8.89 | 5.36 | 2.09 | 11.78 | 2.09 | 1.34 |
| SARIMA | 8.91 | 5.45 | 2.44 | 13.51 | 2.10 | 1.38 |
| Holt-Winters | 11.66 | 6.10 | 2.54 | 8.75 | 1.36 | 1.71 |
| LSTM | 5.19 | 5.05 | 2.30 | 13.68 | 1.58 | 1.45 |
| XGBoost | 7.42 | 5.37 | 2.24 | 14.79 | 1.17 | 1.27 |
| Prophet | 8.52 | 4.26 | 2.65 | 10.00 | 1.28 | 2.08 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.26 |
| Bengaluru | 0.07 |
| Chennai | 0.09 |
| Delhi | 0.34 |
| Hyderabad | 0.08 |
| Lucknow | 0.27 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.5107 | 0.015 | 1 | 0.85 | nan (-) | 0.13 / nan |
| Bengaluru | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.1416 | 0.078 | 1 | 0.86 | nan (-) | 0.15 / nan |
| Chennai | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.3633 | 0.010 | 1 | 0.56 | nan (-) | 0.10 / nan |
| Hyderabad | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.0013 | 0.010 | 0 | 0.59 | nan (-) | 0.05 / nan |
| Lucknow | 2025-02-19 to 2026-10-29 | 618 | 42 | 0.0024 | 0.090 | 0 | 0.80 | nan (-) | 0.02 / nan |
| Ahmedabad | 2025-02-19 to 2026-10-29 | 618 | 42 | 0.0756 | 0.050 | 1 | 0.74 | nan (-) | 0.08 / nan |

## Issues log

- Bengaluru: never beat the baseline in any window: XGBoost, Prophet
- Delhi: never beat the baseline in any window: Prophet
- Hyderabad: never beat the baseline in any window: LSTM, ARIMA
