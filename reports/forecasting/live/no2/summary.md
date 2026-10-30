# NO2 forecasting: evaluation summary

Generated 2026-10-30T14:05:08+00:00. Models fitted on log1p(NO2), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 5 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | SARIMA | 5.56 | 20% | 80% | Prophet | Naive (last value) (7.42) | yes |
| Bengaluru | LSTM | 3.65 | 20% | 20% | ARIMA | Seasonal naive (annual) (4.59) | yes |
| Chennai | LSTM | 1.79 | 40% | 60% | LSTM | Seasonal naive (weekly) (1.86) | yes |
| Delhi | Prophet | 6.32 | 0% | 40% | Naive (last value) | Seasonal naive (weekly) (7.23) | yes |
| Hyderabad | SARIMA | 1.40 | 20% | 40% | Holt-Winters | Naive (last value) (1.56) | yes |
| Lucknow | XGBoost | 2.61 | 20% | 20% | Holt-Winters | Naive (last value) (1.81) | **no** |

### Win rate (share of 5 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 20% | 20% | 20% | 20% | 0% | 20% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 0% | 0% | 20% |
| Seasonal naive (annual) | 0% | 0% | 0% | 0% | 0% | 0% |
| ARIMA | 0% | 40% | 20% | 20% | 0% | 0% |
| SARIMA | 20% | 0% | 20% | 20% | 20% | 0% |
| Holt-Winters | 0% | 0% | 0% | 0% | 40% | 40% |
| LSTM | 0% | 20% | 40% | 20% | 0% | 0% |
| XGBoost | 0% | 20% | 0% | 20% | 20% | 20% |
| Prophet | 60% | 0% | 0% | 0% | 20% | 0% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 40% | 40% | 40% | 40% | 20% | 20% |
| SARIMA | 80% | 40% | 60% | 20% | 40% | 0% |
| Holt-Winters | 20% | 20% | 0% | 20% | 40% | 40% |
| LSTM | 0% | 20% | 60% | 60% | 0% | 0% |
| XGBoost | 20% | 20% | 0% | 40% | 20% | 20% |
| Prophet | 80% | 40% | 0% | 40% | 40% | 20% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 7.42 | 5.28 | 1.98 | 7.99 | 1.56 | 1.81 |
| Seasonal naive (weekly) | 8.60 | 6.20 | 1.86 | 7.23 | 1.83 | 2.25 |
| Seasonal naive (annual) | 9.69 | 4.59 | 2.63 | 9.41 | 3.38 | 3.67 |
| ARIMA | 8.87 | 4.02 | 2.19 | 7.77 | 1.78 | 3.39 |
| SARIMA | 5.56 | 4.20 | 1.86 | 7.11 | 1.40 | 2.84 |
| Holt-Winters | 8.73 | 4.81 | 2.35 | 8.86 | 1.61 | 3.22 |
| LSTM | 10.24 | 3.65 | 1.79 | 7.25 | 2.50 | 3.47 |
| XGBoost | 8.30 | 4.05 | 2.54 | 8.23 | 1.99 | 2.61 |
| Prophet | 6.05 | 4.35 | 2.58 | 6.32 | 1.63 | 2.75 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 4.8 | 4.2 | 4.0 | 6.0 | 3.8 | 2.2 |
| Seasonal naive (weekly) | 5.4 | 8.0 | 4.2 | 4.8 | 4.8 | 3.8 |
| Seasonal naive (annual) | 6.8 | 6.2 | 6.4 | 7.4 | 8.0 | 7.0 |
| ARIMA | 5.4 | 3.0 | 4.2 | 3.8 | 4.8 | 5.4 |
| SARIMA | 2.4 | 4.6 | 3.2 | 4.8 | 2.6 | 5.8 |
| Holt-Winters | 6.4 | 5.4 | 6.2 | 6.6 | 4.2 | 4.4 |
| LSTM | 7.2 | 4.4 | 3.0 | 3.6 | 6.8 | 6.2 |
| XGBoost | 4.8 | 4.8 | 7.2 | 4.6 | 5.4 | 4.2 |
| Prophet | 1.8 | 4.4 | 6.6 | 3.4 | 4.6 | 6.0 |

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
| Ahmedabad | 2026-09-30 to 2026-10-29 | SARIMA | 4.52 | 3.42 | 11.9 | Seasonal naive (annual) (10.36) | yes |
| Bengaluru | 2026-09-30 to 2026-10-29 | XGBoost | 3.72 | 2.65 | 14.4 | Naive (last value) (4.07) | yes |
| Chennai | 2026-09-30 to 2026-10-29 | LSTM | 1.42 | 1.10 | 11.3 | Seasonal naive (weekly) (2.76) | yes |
| Delhi | 2026-09-30 to 2026-10-29 | Prophet | 5.81 | 4.70 | 17.6 | Naive (last value) (5.34) | **no** |
| Hyderabad | 2026-09-30 to 2026-10-29 | XGBoost | 1.19 | 0.92 | 8.7 | Naive (last value) (1.32) | yes |
| Lucknow | 2026-09-30 to 2026-10-29 | XGBoost | 2.65 | 1.98 | 12.0 | Naive (last value) (2.85) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 12.19 | 4.07 | 3.23 | 5.34 | 1.32 | 2.85 |
| Seasonal naive (weekly) | 11.39 | 6.40 | 2.76 | 5.94 | 1.36 | 3.81 |
| Seasonal naive (annual) | 10.36 | 5.13 | 2.88 | 16.54 | 3.76 | 4.31 |
| ARIMA | 8.21 | 4.87 | 4.57 | 12.23 | 1.28 | 6.73 |
| SARIMA | 4.52 | 5.02 | 1.78 | 8.29 | 1.36 | 3.30 |
| Holt-Winters | 10.85 | 5.82 | 4.30 | 9.12 | 1.50 | 6.29 |
| LSTM | 18.31 | 4.75 | 1.42 | 14.04 | 2.39 | 6.09 |
| XGBoost | 7.48 | 3.72 | 4.92 | 14.85 | 1.19 | 2.65 |
| Prophet | 8.71 | 4.98 | 3.43 | 5.81 | 1.51 | 2.84 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.44 |
| Bengaluru | 0.07 |
| Chennai | 0.03 |
| Delhi | 0.28 |
| Hyderabad | 0.13 |
| Lucknow | 0.52 |

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

- Ahmedabad: never beat the baseline in any window: LSTM
- Chennai: never beat the baseline in any window: Holt-Winters, XGBoost, Prophet
- Hyderabad: never beat the baseline in any window: LSTM
- Lucknow: never beat the baseline in any window: SARIMA, LSTM
